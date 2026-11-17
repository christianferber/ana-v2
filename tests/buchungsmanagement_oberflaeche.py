"""Änderung nach 2.06.00: Buchungsmanagement im regulären lokalen Praxislauf bedienen."""
import json
from pathlib import Path

from anwendung.buchungsmanagement import (
    kontoauszuege_lesen, betreff_schluessel, rechnungen_pruefen,
    ausblendungen_laden, AUSBLENDUNGEN_DATEINAME,
    ist_ausgeblendet, auswahl_regeln_aendern, buchungs_pruef_ids,
)


def vorbereiten(basis, kopie):
    # Änderung: Ausschließlich Einstellungen der isolierten App-Kopie vorbereiten.
    # Änderung: CSV nur in der Testkopie zurücksetzen, damit Neuanlage unabhängig vom Original geprüft wird.
    db_datei = kopie / 'Datenbank' / AUSBLENDUNGEN_DATEINAME
    if db_datei.exists():
        db_datei.unlink()
    vorlagen = basis.parent / '_Vorlagen'
    config = {'kontoordner': str(vorlagen / 'Kontoauszüge Beispieldaten'),
              'rechnungsordner': str(vorlagen / 'Rechnungen Beispieldaten'), 'ausgeblendet': []}
    (kopie / 'buchungsmanagement.json').write_text(json.dumps(config), encoding='utf-8')


def pruefen(kopie, js, klicken, warten, knopf, cdp, auswahl):
    # Änderung: Echte Tab-/Tabellenereignisse nutzen, keine Dateninhalte ausgeben.
    tab = lambda name: "Array.from(document.querySelectorAll('.q-tab')).find(e=>e.querySelector('.q-tab__label')?.textContent.trim()===" + json.dumps(name) + ')'
    klicken(tab('Tools'))
    warten('Boolean(' + tab('PDF-Zusammenführung') + ')')
    assert js('(' + tab('PDF-Zusammenführung') + ").getAttribute('aria-selected')==='true'")
    klicken(tab('Buchungsmanagement'))
    warten("Boolean(document.querySelector('.ana-buchungsmanagement')?.getClientRects().length)")
    dialog = "document.querySelector('.ana-kontomanager-dialog')"
    def suchen(text):
        # Änderung: Suche auch zur Auswahl eines real wiederholten Empfänger-/Zweck-Paares nutzen.
        js("(()=>{const e=(" + dialog + ").querySelector('.q-field input');"
           "Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(e," + json.dumps(text) + ");"
           "e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));e.blur()})()")
    # Änderung 16.11.2026: Alle Umsatzaktionen sind ausschließlich in der Rechnungsprüfung erreichbar.
    assert not js("Array.from(document.querySelectorAll('button')).some(e=>e.textContent.includes('Kontoumsätze verwalten'))")
    configdatei = kopie / 'buchungsmanagement.json'
    db_datei = kopie / 'Datenbank' / AUSBLENDUNGEN_DATEINAME
    config = json.loads(configdatei.read_text(encoding='utf-8'))
    buchungen = kontoauszuege_lesen(config['kontoordner'])
    assert db_datei.is_file() and ausblendungen_laden(db_datei) == []
    # Änderung: Tatsächliche Fortschrittsanzeige beobachten, ohne Dateiinhalte zu erfassen.
    js("window.anaKontoMessung=[];window.anaKontoTimer=setInterval(()=>{const d=document.querySelector('.ana-kontomanager-fortschritt');if(d){window.anaKontoMessung.push({phase:d.querySelector('.ana-konto-phase').textContent,wert:Number(d.querySelector('.q-linear-progress').getAttribute('aria-valuenow'))})}},50)")
    knopf('Rechnungen überprüfen')
    warten("Boolean(document.querySelector('.ana-kontomanager-fortschritt'))")
    # Änderung: Lokale OCR benötigt beim ersten Lesen zusätzliche Zeit; Ergebnis lokal abgleichen.
    warten('Boolean(' + dialog + ')', 120)
    messungen = js('clearInterval(window.anaKontoTimer);window.anaKontoMessung')
    assert len(messungen) >= 2 and any(0 <= m['wert'] < 1 for m in messungen)
    assert messungen[-1]['wert'] == 1
    # Änderung 16.11.2026: Kein Rücksprung des linearen Balkens beim Phasenwechsel.
    werte = [m['wert'] for m in messungen]
    assert werte == sorted(werte)
    assert js("!document.querySelector('.ana-kontomanager-fortschritt')")
    prueffaelle = rechnungen_pruefen(buchungen, config['rechnungsordner'], set(), vollstaendig=True)
    anzahltext = str(len(prueffaelle)) + ' Einträge angezeigt.'
    warten(dialog + '.innerText.includes(' + json.dumps(anzahltext) + ')')
    # Änderung: Aktivierung, kompakte Schrift und auf zwei Zeilen begrenzte Hinweise im echten Dialog prüfen.
    # Änderung: Aktiv-Symbole und deutsches Datum mit durchgehend absteigender Sortierung prüfen.
    assert js(dialog + ".querySelector('thead').innerText.includes('Aktiv')")
    assert js(dialog + ".querySelector('tbody [aria-label=Aktiv]') !== null")
    # Änderung: Aktiv zeigt einen Haken; Datumszellen sind vollständig und einzeilig.
    assert js(dialog + ".querySelector('tbody [aria-label=Aktiv]').textContent.includes('check')")
    for breite in (1440, 800, 400):
        cdp('Emulation.setDeviceMetricsOverride', {'width': breite, 'height': 1000,
                                                'deviceScaleFactor': 1, 'mobile': False})
        warten("Array.from((" + dialog + ").querySelectorAll('.ana-konto-datum span')).every(e=>e.getBoundingClientRect().height<=parseFloat(getComputedStyle(e).lineHeight)+1 && e.scrollWidth<=e.clientWidth+1)")
    cdp('Emulation.clearDeviceMetricsOverride', {})
    assert js("(()=>{const d=" + dialog + ";const i=Array.from(d.querySelectorAll('thead th')).findIndex(e=>e.textContent.trim()==='Datum');const a=Array.from(d.querySelectorAll('tbody tr')).map(r=>r.cells[i]?.textContent.trim()).filter(x=>x&&x!=='—');return a.every(x=>/^\\d{2}\\.\\d{2}\\.\\d{4}$/.test(x))&&a.map(x=>x.split('.').reverse().join('')).every((x,i,b)=>!i||b[i-1]>=x)})()")
    assert js("parseFloat(getComputedStyle((" + dialog + ").querySelector('tbody td')).fontSize)<=12")
    assert js("Array.from((" + dialog + ").querySelectorAll('.ana-konto-kurztext')).every(e=>e.getBoundingClientRect().height<=33)")
    tabellenkopf_pruefen(js, warten, dialog + ".querySelector('.q-table__middle')", dialog + ".querySelector('thead th')")
    # Änderung: Kurznamen sind jetzt gültig; verbliebene Zuordnungsfälle sichtbar halten.
    # Änderung: Nicht zugeordnete Rechnungen stehen ohne Buchungsdatum am Ende; gezielt suchen.
    suchen('Rechnung ohne Buchung')
    warten(dialog + ".querySelector('tbody')?.innerText.includes('Rechnung ohne Buchung')")
    suchen('')
    # Änderung: Grüne Zuordnung und Betragsstatus sowie beide reinen Anzeigefilter prüfen.
    assert js(dialog + ".querySelector('thead').innerText.includes('Betrag OK')")
    # Änderung: Nach Datumsortierung können erfolgreiche Fälle auf späteren Seiten stehen.
    suchen('OK')
    warten(dialog + ".querySelectorAll('.q-badge.bg-green').length>0")
    assert js(dialog + ".querySelectorAll('.q-badge.bg-green').length>0")
    suchen('')
    csv_vorher = db_datei.read_bytes()
    # Änderung 16.11.2026: Übersicht zählt alle aktiven Ergebnisse; Klick setzt den passenden Filter.
    for gruppe, erwartet in [
        ('OK', sum(r['status'] == 'OK' and r['betrag_status'] == 'OK' for r in prueffaelle)),
        ('Betrag prüfen', sum(r['status'] == 'OK' and r['betrag_status'] != 'OK' for r in prueffaelle)),
        ('Fehlerhaft', sum(r['status'] != 'OK' for r in prueffaelle)),
    ]:
        knopf(gruppe + ': ' + str(erwartet), dialog)
        warten(dialog + '.innerText.includes(' + json.dumps(str(erwartet) + ' Einträge angezeigt.') + ')')
        assert db_datei.read_bytes() == csv_vorher
        # Änderung: Symbole und Gesamtstatus bleiben unabhängig von der ausgewählten Gruppe sichtbar.
        assert js(dialog + ".querySelector('.ana-rechnung-gesamtstatus').innerText.includes('Fehlerhafte Rechnungen vorhanden')")
        assert js(dialog + ".querySelector('.ana-rechnung-gesamtstatus .text-red') !== null")
    # Änderung: Kein Dropdown; aktiven Button erneut klicken setzt den Gruppenfilter zurück.
    # Änderung: Die unveränderte Seitengrößenauswahl der Tabelle ist weiterhin zulässig.
    assert js("Array.from((" + dialog + ").querySelectorAll('.q-select')).every(e=>e.closest('.q-table__bottom'))")
    knopf('Fehlerhaft: ' + str(sum(r['status'] != 'OK' for r in prueffaelle)), dialog)
    warten(dialog + '.innerText.includes(' + json.dumps(str(len(prueffaelle)) + ' Einträge angezeigt.') + ')')
    assert db_datei.read_bytes() == csv_vorher
    # Änderung: Neue Betragsfälle im echten Dialog suchen und beide Vergleichsbeträge kontrollieren.
    suchen('Betrag abweichend')
    warten(dialog + ".querySelector('tbody')?.innerText.includes('Betrag abweichend')")
    abweichend = next(p for p in prueffaelle if p['betrag_status'] == 'Betrag abweichend')
    assert abweichend['status'] == 'OK'
    for feld in ('betrag', 'rechnungsbetrag'):
        assert js(dialog + ".querySelector('tbody').innerText.includes(" + json.dumps(abweichend[feld].replace('.', ',')) + ')')
    suchen('Betrag nicht prüfbar')
    warten(dialog + ".querySelector('tbody')?.innerText.includes('Betrag nicht prüfbar')")
    suchen('Rechnung fehlt')
    warten(dialog + ".querySelector('tbody')?.innerText.includes('Rechnung fehlt')")
    klicken("Array.from((" + dialog + ").querySelectorAll('tbody tr')).find(r=>r.innerText.includes('Rechnung fehlt')).querySelector('.q-checkbox')")
    knopf('Auswahl ausblenden', dialog)
    warten("!document.querySelector('.ana-kontomanager-fortschritt')", 120)
    assert ausblendungen_laden(db_datei)
    # Änderung: Auch nach Ausblenden im Rechnungsfenster zeigt jede sichtbare aktive Zeile ihre neue ID.
    regeln = ausblendungen_laden(db_datei)
    neue_ids = buchungs_pruef_ids(buchungen, regeln)
    id_zeilen = js('Array.from((' + dialog + ").querySelectorAll('.ana-buchungs-id[data-ursprung]')).map(e=>({ursprung:e.dataset.ursprung,wert:e.textContent.trim()}))")
    assert id_zeilen and all(z['wert'] == neue_ids[z['ursprung']] for z in id_zeilen if z['ursprung'] in neue_ids)
    knopf('Schließen', dialog)
    warten('!(' + dialog + ')')
    knopf('Rechnungen überprüfen')
    warten('Boolean(' + dialog + ')')
    # Änderung 16.11.2026: Deaktivierte Buchungen sind in derselben Prüfung erkennbar und reaktivierbar.
    klicken(dialog + ".querySelector('.q-toggle')")
    suchen('Ausgeblendet')
    warten(dialog + ".querySelector('tbody')?.innerText.includes('Ausgeblendet')")
    assert js(dialog + ".querySelector('tbody [aria-label=Inaktiv]') !== null")
    klicken("Array.from((" + dialog + ").querySelectorAll('tbody tr')).find(r=>r.innerText.includes('Ausgeblendet')).querySelector('.q-checkbox')")
    knopf('Auswahl aktivieren', dialog)
    warten("!document.querySelector('.ana-kontomanager-fortschritt')", 120)
    assert ausblendungen_laden(db_datei) == []
    suchen('')
    knopf('Schließen', dialog)
    warten('!(' + dialog + ')')
    # Änderung: Nach einem echten Lesefehler müssen Fortschrittsfenster und Startsperre frei sein.
    gespeichert = configdatei.read_text(encoding='utf-8')
    fehlerordner = kopie.parent / 'ungueltiger-kontoauszug'
    fehlerordner.mkdir()
    (fehlerordner / 'ungueltig.pdf').write_bytes(b'Kein PDF - lokaler Fehlerfall')
    config = json.loads(gespeichert)
    config['kontoordner'] = str(fehlerordner)
    configdatei.write_text(json.dumps(config), encoding='utf-8')
    try:
        knopf('Rechnungen überprüfen')
        warten("document.querySelector('.ana-buchungsmanagement').innerText.includes('Vorgang abgebrochen; kein vollständiges Prüfergebnis.')")
        warten("!document.querySelector('.ana-kontomanager-fortschritt')")
        assert js('!(' + dialog + ')')
    finally:
        configdatei.write_text(gespeichert, encoding='utf-8')
    knopf('Rechnungen überprüfen')
    warten('Boolean(' + dialog + ')')
    knopf('Schließen', dialog)
    warten('!(' + dialog + ')')
    # Änderung: Navigation bei zwei Desktopbreiten auf Umbruch und Abschneiden prüfen.
    for breite in (1000, 1440):
        cdp('Emulation.setDeviceMetricsOverride', {'width': breite, 'height': 1000,
                                                'deviceScaleFactor': 1, 'mobile': False})
        warten("Array.from(document.querySelectorAll('.ana-nav .q-tab__label')).every(e=>e.getBoundingClientRect().height<=parseFloat(getComputedStyle(e).lineHeight)+1 && e.scrollWidth<=e.clientWidth+1)")
    klicken(tab('PDF-Zusammenführung'))
    # Änderung: Tabwechsel wird asynchron gerendert; sichtbaren PDF-Bereich abwarten.
    warten("Array.from(document.querySelectorAll('button')).some(e=>e.textContent.includes('PDF erstellen') && e.getClientRects().length)")
    print('Tools-Praxisprüfung: CSV-Datenbank für Ausschlüsse, Migration, Reaktivierung/Persistenz, optionale Namen, Fortschritt, PDF-Betragsvergleich und Navigation bestanden.', flush=True)


def tabellenkopf_pruefen(js, warten, scroller, kopf):
    # Änderung: Einen echten vertikalen Scrollvorgang ausführen und die Kopfposition vergleichen.
    alt = js('(' + scroller + ").getAttribute('style')")
    js('(' + scroller + ").style.setProperty('max-height','160px','important');(" + scroller + ").style.setProperty('height','160px','important')")
    # Änderung: Dialogbewegungen ausklammern; der Kopf muss relativ zu seinem Scrollbereich stehen bleiben.
    vorher = js('(' + kopf + ').getBoundingClientRect().top - (' + scroller + ').getBoundingClientRect().top')
    js('(' + scroller + ').scrollTop=120')
    warten('(' + scroller + ').scrollTop>0')
    nachher = js('(' + kopf + ').getBoundingClientRect().top - (' + scroller + ').getBoundingClientRect().top')
    assert abs(nachher - vorher) <= 1
    js('(' + scroller + ').scrollTop=0')
    if alt is None:
        js('(' + scroller + ").removeAttribute('style')")
    else:
        js('(' + scroller + ').setAttribute("style",' + json.dumps(alt) + ')')
