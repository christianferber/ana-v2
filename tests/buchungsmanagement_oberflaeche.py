"""Änderung nach 2.06.00: Buchungsmanagement im regulären lokalen Praxislauf bedienen."""
import json
from collections import Counter
from pathlib import Path

from anwendung.buchungsmanagement import (
    kontoauszuege_lesen, betreff_schluessel, rechnungen_pruefen,
    ausblendungen_laden, AUSBLENDUNGEN_DATEINAME,
    ist_ausgeblendet,
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
    knopf('Kontoumsätze verwalten')
    warten('Boolean(' + dialog + ')')
    warten(dialog + ".innerText.includes('62 Einträge angezeigt.')")
    # Änderung: Betreff entfällt, die bestätigten Datum-/Betragsspalten bleiben erhalten.
    assert js(dialog + ".querySelector('thead').innerText.includes('Datum') && " + dialog + ".querySelector('thead').innerText.includes('Betrag (EUR)')")
    assert not js(dialog + ".querySelector('thead').innerText.includes('Betreff vereinfacht')")
    tabellenkopf_pruefen(js, warten, dialog + ".querySelector('.q-table__middle')", dialog + ".querySelector('thead th')")
    configdatei = kopie / 'buchungsmanagement.json'
    # Änderung: Ausschlüsse müssen in der neuen CSV-Datenbank liegen, nicht mehr in JSON.
    db_datei = kopie / 'Datenbank' / AUSBLENDUNGEN_DATEINAME
    assert db_datei.is_file() and ausblendungen_laden(db_datei) == []
    config = json.loads(configdatei.read_text(encoding='utf-8'))
    assert 'ausgeblendet' not in config
    buchungen = kontoauszuege_lesen(config['kontoordner'])
    # Änderung: Reales wiederholtes Paar auswählen und die sofortige Gruppenausblendung prüfen.
    paare = Counter((betreff_schluessel(b['empfaenger']), betreff_schluessel(b['zweck'])) for b in buchungen)
    ziel = next(b for b in buchungen if paare[(betreff_schluessel(b['empfaenger']), betreff_schluessel(b['zweck']))] > 1)
    assert js(dialog + ".innerText.includes('Empfänger / Auftraggeber') && " + dialog + ".innerText.includes('Zweck')")
    suchen(ziel['id'])
    warten(dialog + '.querySelector("tbody")?.innerText.includes(' + json.dumps(ziel['id']) + ')')
    klicken("Array.from((" + dialog + ").querySelectorAll('tbody tr')).find(r=>Array.from(r.cells).some(c=>c.textContent.trim()==="
            + json.dumps(ziel['id']) + ")).querySelector('.q-checkbox')")
    knopf('Auswahl ausblenden', dialog)
    warten("(()=>{const d=" + dialog + ";return d && !d.innerText.includes('62 Einträge angezeigt.')})()")
    ausgeblendet = ausblendungen_laden(db_datei)
    assert ausgeblendet and all(len(r) == 3 for r in ausgeblendet)
    assert 'ausgeblendet' not in json.loads(configdatei.read_text(encoding='utf-8'))
    erwartete = sum(not ist_ausgeblendet(b, ausgeblendet) for b in buchungen)
    assert erwartete <= len(buchungen) - 2
    assert js(dialog + '.innerText.includes(' + json.dumps(str(erwartete) + ' Einträge angezeigt.') + ')')
    # Änderung: Ausgeblendete sichtbar machen und Betreff-Regel wieder aufheben.
    klicken(dialog + ".querySelector('.q-toggle')")
    warten(dialog + ".innerText.includes('62 Einträge angezeigt.')")
    klicken("Array.from((" + dialog + ").querySelectorAll('tbody tr')).find(r=>r.innerText.includes('Ausgeblendet')).querySelector('.q-checkbox')")
    knopf('Auswahl aktivieren', dialog)
    warten('!(' + dialog + ").querySelector('tbody')?.innerText.includes('Ausgeblendet')")
    assert ausblendungen_laden(db_datei) == []
    suchen('')
    knopf('Schließen', dialog)
    warten('!(' + dialog + ')')
    # Änderung: Tatsächliche Fortschrittsanzeige beobachten, ohne Dateiinhalte zu erfassen.
    js("window.anaKontoMessung=[];window.anaKontoTimer=setInterval(()=>{const d=document.querySelector('.ana-kontomanager-fortschritt');if(d){window.anaKontoMessung.push({phase:d.querySelector('.ana-konto-phase').textContent,wert:Number(d.querySelector('.q-linear-progress').getAttribute('aria-valuenow'))})}},50)")
    knopf('Rechnungen überprüfen')
    warten("Boolean(document.querySelector('.ana-kontomanager-fortschritt'))")
    # Änderung: Lokale OCR benötigt beim ersten Lesen zusätzliche Zeit; Ergebnis lokal abgleichen.
    warten('Boolean(' + dialog + ')', 120)
    messungen = js('clearInterval(window.anaKontoTimer);window.anaKontoMessung')
    assert len(messungen) >= 2 and any(0 <= m['wert'] < 1 for m in messungen)
    assert messungen[-1]['wert'] == 1
    for phase in {m['phase'] for m in messungen}:
        werte = [m['wert'] for m in messungen if m['phase'] == phase]
        assert werte == sorted(werte)
    assert js("!document.querySelector('.ana-kontomanager-fortschritt')")
    prueffaelle = rechnungen_pruefen(buchungen, config['rechnungsordner'], set(), vollstaendig=True)
    anzahltext = str(len(prueffaelle)) + ' Einträge angezeigt.'
    warten(dialog + '.innerText.includes(' + json.dumps(anzahltext) + ')')
    # Änderung: Kurznamen sind jetzt gültig; verbliebene Zuordnungsfälle sichtbar halten.
    assert js(dialog + ".innerText.includes('Rechnung ohne Buchung') && " + dialog + ".innerText.includes('Rechnung fehlt')")
    # Änderung: Grüne Zuordnung und Betragsstatus sowie beide reinen Anzeigefilter prüfen.
    assert js(dialog + ".querySelector('thead').innerText.includes('Betrag OK')")
    assert js(dialog + ".querySelectorAll('.q-badge.bg-green').length>0")
    csv_vorher = db_datei.read_bytes()
    for modus, erwartet in [
        ('Status OK ausblenden', sum(r['status'] != 'OK' for r in prueffaelle)),
        ('Status OK und Betrag OK ausblenden', sum(not (r['status'] == 'OK' and r['betrag_status'] == 'OK') for r in prueffaelle)),
        ('Alle anzeigen', len(prueffaelle)),
    ]:
        auswahl('Prüfergebnisse anzeigen', modus)
        warten(dialog + '.innerText.includes(' + json.dumps(str(erwartet) + ' Einträge angezeigt.') + ')')
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
    suchen('')
    warten(dialog + ".querySelector('tbody')?.innerText.includes('Rechnung fehlt')")
    klicken("Array.from((" + dialog + ").querySelectorAll('tbody tr')).find(r=>r.innerText.includes('Rechnung fehlt')).querySelector('.q-checkbox')")
    knopf('Auswahl ausblenden', dialog)
    warten("!document.querySelector('.ana-kontomanager-fortschritt')", 120)
    assert ausblendungen_laden(db_datei)
    knopf('Schließen', dialog)
    warten('!(' + dialog + ')')
    knopf('Kontoumsätze verwalten')
    warten('Boolean(' + dialog + ')')
    assert not js(dialog + ".innerText.includes('62 Einträge angezeigt.')")
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
    knopf('Kontoumsätze verwalten')
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
    vorher = js('(' + kopf + ').getBoundingClientRect().top')
    js('(' + scroller + ').scrollTop=120')
    warten('(' + scroller + ').scrollTop>0')
    nachher = js('(' + kopf + ').getBoundingClientRect().top')
    assert abs(nachher - vorher) <= 1
    js('(' + scroller + ').scrollTop=0')
    if alt is None:
        js('(' + scroller + ").removeAttribute('style')")
    else:
        js('(' + scroller + ').setAttribute("style",' + json.dumps(alt) + ')')
