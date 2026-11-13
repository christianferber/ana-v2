# Änderung für v2: In tests/ eingeordnet; Modul- und Dateipfade angepasst.
"""Änderung für v2: Echter lokaler Oberflächentest mit isolierter Beispieldatenkopie.

Keine Screenshots, Dateninhalte oder Browserprotokolle werden ausgegeben.
Die Benutzeroberfläche wird über einen lokalen Chrome-Testprozess bedient.
"""

import contextlib
import copy
import csv
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

from websockets.sync.client import connect

from anwendung.datenhaltung import datei_oeffnen, dictlist_to_csv
from anwendung.einstellungen import ini_datei_lesen, ini_datei_schreiben
from tests.referenz_pruefen import ergebnisse_berechnen
# Änderung: Ein Testlauf besitzt alle gestarteten Prozesse einschließlich Fenster.
from tests.testprozesse import TestProzesse

BASIS = Path(__file__).resolve().parents[1]
SCHRITT = 'Vorbereitung'


def freier_port():
    # Änderung für v2: Testserver nur auf einer freien lokalen Adresse starten.
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def app_starten(ordner):
    # Änderung für v2: Originaloberfläche mit separater Konfiguration starten.
    from anwendung import oberflaeche as ana
    # Änderung: Optional einen Hintergrundfehler auslösen; der nächste Versuch läuft regulär.
    if (ordner / 'exportfehler.txt').exists():
        from anwendung import abrechnung_ui, rueckverguetung_ui
        for modul, name in ((abrechnung_ui, 'abrechnung_pdf_konvertieren'),
                            (rueckverguetung_ui, 'rueckverguetung_pdf_konvertieren')):
            def fehler_einmal(original):
                erster_aufruf = True
                def konvertieren(*args, **kwargs):
                    nonlocal erster_aufruf
                    if erster_aufruf:
                        erster_aufruf = False
                        raise OSError('Lokaler simulierter Exportfehler')
                    return original(*args, **kwargs)
                return konvertieren
            setattr(modul, name, fehler_einmal(getattr(modul, name)))
    ana.ini = str(ordner / 'ana.ini')
    original_run = ana.ui.run
    def test_run(**kwargs):
        kwargs.update(host='127.0.0.1', port=int((ordner / 'port.txt').read_text()))
        return original_run(**kwargs)
    ana.ui.run = test_run
    # Änderung: Den echten Programmeinstieg samt Startanzeige mit isolierter INI prüfen.
    import ana as programm
    original_anzeige = programm.Startanzeige
    def anzeige_anlegen():
        anzeige = original_anzeige()
        fenster = anzeige._fenster
        def fenster_pruefen():
            fenster()
            (ordner / 'startanzeige-geschlossen.txt').write_text('1')
        anzeige._fenster = fenster_pruefen
        return anzeige
    programm.Startanzeige = anzeige_anlegen
    programm.main()


def bestand(daten):
    # Änderung für v2: Originaldateien lokal auf unveränderte Inhalte kontrollieren.
    return {str(p.relative_to(daten)): hashlib.sha256(p.read_bytes()).digest()
            for p in daten.rglob('*') if p.is_file()}


def testen(rueckverguetung=False):
    # Änderung: Sperre und vollständiges Aufräumen gelten auch bei Fehlern und Abbruch.
    with TestProzesse(BASIS) as prozesse:
        _testen(prozesse, rueckverguetung)
    print('Test-App, Fenster und Testbrowser vollständig beendet.', flush=True)


def _testen(prozesse, rueckverguetung=False):
    global SCHRITT
    config = ini_datei_lesen(BASIS / 'ana.ini')
    daten = Path(config['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (BASIS.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
    originalbestand = bestand(daten)
    # Änderung für v2: Rückvergütung mit der vor dem Umbau gesicherten lokalen Referenz prüfen.
    if rueckverguetung:
        faelle = json.loads((BASIS / '.lokal' / 'rueckverguetungsreferenz.json').read_text(encoding='utf-8'))
        fall = next(f for f in reversed(faelle)
                    if (daten / 'Vorlagen' / ('Vorlage-Rückvergütung-' + f['jahr'] + '.docx')).is_file())
    else:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            faelle = ergebnisse_berechnen()
        # Änderung für v2: Vorhandenen Fall mit passender Vorlage auswählen, keine Testdaten erfinden.
        fall = next(f for f in reversed(faelle) if not f['zwischenablesung']
                    and (daten / 'Vorlagen' / ('Vorlage-Abrechnung-' + f['jahr'] + '.docx')).is_file())
    jahr = fall['jahr']
    mwst = str(fall['ergebnis'][0].get('MwSt-Satz', ''))
    erwartete_csv = dictlist_to_csv(__import__('copy').deepcopy(fall['ergebnis']))
    run = BASIS / '.lokal' / ('oberflaechentest-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    run.mkdir(parents=True)
    # Änderung: Fehlersimulation bleibt auf die isolierte Test-App begrenzt.
    exportfehler = '--exportfehler' in sys.argv
    if exportfehler:
        (run / 'exportfehler.txt').write_text('1')
    kopie = run / 'daten'
    shutil.copytree(daten, kopie)
    if rueckverguetung:
        # Änderung für v2: Praxistest auf einen vorhandenen Datensatz begrenzen.
        # Vollständige Berechnung und Neuberechnung werden separat für alle Beispiele verglichen.
        # Ausschließlich die isolierte Kopie verändern; Originaldateien bleiben unverändert.
        jahresdatei = kopie / 'Abrechnungen' / ('Abrechnung-' + jahr) / ('Abrechnung-' + jahr + '.csv')
        zeilen = datei_oeffnen(jahresdatei)
        with jahresdatei.open('w', newline='') as datei:
            schreiber = csv.DictWriter(datei, fieldnames=list(zeilen[0]), delimiter=';')
            schreiber.writeheader()
            schreiber.writerow(zeilen[0])
        fall = copy.deepcopy(fall)
        fall['ergebnis'] = fall['ergebnis'][:1]
        erwartete_csv = dictlist_to_csv(copy.deepcopy(fall['ergebnis']))
    config['Anwendung']['Arbeitsordner'] = str(kopie)
    # Änderung: Testkopie mit definierten Optionen starten, unabhängig von Benutzer-Sicherungszielen.
    config['Sicherung'] = dict(Ordner='', BeiProgrammende='nein', Aufraeumen='nein',
                              AufbewahrungWochen='12')
    ini_datei_schreiben(run / 'ana.ini', config)
    port = freier_port()
    (run / 'port.txt').write_text(str(port))
    log = (run / 'app.log').open('w', encoding='utf-8')
    # Änderung für v2: Paketstart erhält den Projektordner im Python-Suchpfad.
    app = prozesse.starten([sys.executable, '-m', 'tests.oberflaeche_pruefen', '--app', str(run)],
                           cwd=BASIS, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW)
    (run / 'app.pid').write_text(str(app.pid))
    browser = None
    erfolgreich = False
    try:
        SCHRITT = 'Oberfläche starten'
        url = 'http://127.0.0.1:' + str(port)
        for _ in range(60):
            try:
                with urllib.request.urlopen(url, timeout=2) as antwort:
                    if antwort.status == 200:
                        break
            except Exception:
                if app.poll() is not None:
                    raise RuntimeError('Start fehlgeschlagen')
                time.sleep(1)
        else:
            raise TimeoutError()
        print('Oberfläche mit neuem Code und Datenkopie gestartet.', flush=True)
        SCHRITT = 'Lokalen Testbrowser starten'
        profil = run / 'chrome'
        browser = prozesse.starten([
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            # Änderung 2.049: Desktop-Oberfläche mit realistischer Fensterbreite bedienen.
            '--headless=new', '--window-size=1440,1000', '--remote-debugging-port=0', '--user-data-dir=' + str(profil),
            '--disable-background-networking', '--disable-extensions', '--no-first-run',
            '--no-default-browser-check', 'about:blank'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(30):
            if (profil / 'DevToolsActivePort').exists():
                break
            time.sleep(1)
        debugport = (profil / 'DevToolsActivePort').read_text().splitlines()[0]
        with urllib.request.urlopen('http://127.0.0.1:' + debugport + '/json/list') as antwort:
            seiten = json.load(antwort)
        ziel = next(s for s in seiten if s['type'] == 'page')
        SCHRITT = 'Lokale Browsersteuerung verbinden'
        with connect(ziel['webSocketDebuggerUrl'], max_size=16 * 1024 * 1024) as ws:
            nummer = 0
            def cdp(methode, parameter):
                nonlocal nummer
                nummer += 1
                ws.send(json.dumps({'id': nummer, 'method': methode, 'params': parameter}))
                while True:
                    antwort = json.loads(ws.recv(timeout=30))
                    if antwort.get('id') == nummer:
                        if 'error' in antwort:
                            raise RuntimeError('Browserbefehl fehlgeschlagen')
                        return antwort.get('result', {})
            def js(code):
                ergebnis = cdp('Runtime.evaluate', {'expression': code, 'returnByValue': True})
                if 'exceptionDetails' in ergebnis:
                    raise RuntimeError('Browserausdruck fehlgeschlagen')
                return ergebnis.get('result', {}).get('value')
            def klicken(code):
                # Änderung für v2: Echte Mausereignisse auslösen, auch für Quasar-Auswahlfelder.
                # Änderung: Nach Scrollen erst das stabile Layout für Mauskoordinaten verwenden.
                js('(' + code + ").scrollIntoView({block:'center',behavior:'instant'})")
                time.sleep(.2)
                punkt = js("(()=>{const e=(" + code + ");e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()")
                cdp('Input.dispatchMouseEvent', {'type': 'mousePressed', 'button': 'left',
                                                'clickCount': 1, **punkt})
                cdp('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'button': 'left',
                                                'clickCount': 1, **punkt})
            def warten(code, sekunden=20):
                for _ in range(sekunden * 2):
                    if js(code):
                        return
                    time.sleep(.5)
                # Änderung für v2: Ausschließlich feste technische Ladeindikatoren melden.
                print('Browserdiagnose: ' + json.dumps(js("({geladen:document.readyState==='complete', tabs:document.querySelectorAll('.q-tab').length, layout:document.querySelectorAll('.q-layout').length, vue:typeof Vue!=='undefined', quasar:typeof Quasar!=='undefined', fehlerseite:document.body.innerText.includes('Internal Server Error')})")), flush=True)
                raise TimeoutError()
            def knopf(text, scope='document'):
                # Änderung nach 2.049: Beschriftung unabhängig von der zusätzlichen Prozentzahl finden.
                suche = ("Array.from(" + scope + ".querySelectorAll('button')).find(e=>"
                         "e.getClientRects().length && (e.querySelector('.q-btn__content > .block')?.textContent || e.textContent).trim().endsWith(" + json.dumps(text) + "))")
                warten('Boolean(' + suche + ' && !(' + suche + ').disabled)')
                klicken(suche)
                time.sleep(.6)
            def auswahl(label, wert):
                global SCHRITT
                SCHRITT = 'Auswahlfeld öffnen: ' + label
                feld = ("Array.from(document.querySelectorAll('.q-field')).find(e=>"
                        "e.getClientRects().length && e.querySelector('.q-field__label')?.textContent==="
                        + json.dumps(label) + ')')
                warten('Boolean(' + feld + ')')
                klicken('(' + feld + ").querySelector('.q-field__control')")
                SCHRITT = 'Auswahloption finden: ' + label
                option = ("Array.from(document.querySelectorAll('.q-menu .q-item')).find(e=>"
                          'e.textContent.trim()===' + json.dumps(wert) + ')')
                warten('Boolean(' + option + ')')
                klicken(option)
                time.sleep(.6)
            def eingabe(label, wert):
                # Änderung für v2: Vorhandene Referenzwerte über echte Eingabefeld-Ereignisse setzen.
                feld = ("Array.from(document.querySelectorAll('.q-field')).find(e=>"
                        "e.getClientRects().length && e.querySelector('.q-field__label')?.textContent==="
                        + json.dumps(label) + ')')
                warten('Boolean(' + feld + ')')
                js("(()=>{const e=(" + feld + ").querySelector('input');"
                   "Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(e,"
                   + json.dumps(str(wert)) + ");e.dispatchEvent(new Event('input',{bubbles:true}));"
                   "e.dispatchEvent(new Event('change',{bubbles:true}));e.blur()})()")
                time.sleep(1)
            def einstellungstab(name):
                # Änderung nach 2.05.00: Echte Tabklicks auch in schmaler Einstellungsansicht.
                tab = ("Array.from(document.querySelectorAll('.ana-settings-tabs .q-tab')).find(e=>"
                       "e.querySelector('.q-tab__label')?.textContent.trim()===" + json.dumps(name) + ')')
                warten('Boolean(' + tab + ')')
                klicken(tab)
                warten('(' + tab + ").getAttribute('aria-selected')==='true'")
                time.sleep(.4)
            def export_starten(text):
                # Änderung nach 2.049: Fortschrittskomponente muss direkt im PDF-Button liegen.
                assert js("Array.from(document.querySelectorAll('button')).some(e=>e.getClientRects().length && (e.querySelector('.q-btn__content > .block')?.textContent || e.textContent).trim().endsWith("
                          + json.dumps(text) + ") && e.querySelector('.ana-button-progress'))")
                # Änderung: Optional Fehlermeldung und wieder freigegebenen Knopf prüfen.
                knopf(text)
                if exportfehler:
                    warten("document.body.innerText.includes('Der Export konnte nicht vollständig erstellt werden.')")
                    warten("Array.from(document.querySelectorAll('button')).some(e=>(e.querySelector('.q-btn__content > .block')?.textContent || e.textContent).trim().endsWith("
                           + json.dumps(text) + ") && !e.disabled)")
                    print('Exportfehler sichtbar und erneuter Start möglich: bestanden.', flush=True)
                    knopf(text)
            SCHRITT = 'Testseite laden'
            cdp('Page.navigate', {'url': url})
            # Änderung nach 2.049: Neue Statistik mit zwei lokalen Abnehmern im Browser bedienen.
            if not rueckverguetung:
                SCHRITT = 'Statistikregister laden'
                statistik_tab = "Array.from(document.querySelectorAll('.q-tab')).find(e=>e.querySelector('.q-tab__label')?.textContent.trim()==='Statistik')"
                warten('Boolean(' + statistik_tab + ')')
                js('(' + statistik_tab + ').click()')
                warten("Boolean(document.querySelector('.ana-statistik'))")
                # Änderung: Getrennte Bereiche bedienen; Verbraucherfilter steht vor beiden Einzelstatistiken.
                def statistikbereich(name):
                    js("Array.from(document.querySelectorAll('.ana-statistik .q-tab')).find(e=>e.querySelector('.q-tab__label')?.textContent.trim()===" + json.dumps(name) + ").click()")
                    time.sleep(.6)
                statistikbereich('Verbraucherspezifisch')
                warten("Boolean(document.querySelector('.ana-verbraucherstatistik')?.getClientRects().length)")
                assert js("document.querySelector('.ana-verbraucherstatistik .q-select').getBoundingClientRect().top < document.querySelector('.ana-verbraucherstatistik .js-plotly-plot').getBoundingClientRect().top")
                from anwendung.verbrauchsstatistik import verbrauchswerte_lesen
                from anwendung.kostenstatistik import kostenmatrix_lesen
                dateien = sorted((kopie / 'Abrechnungen').glob('Abrechnung-*/Abrechnung-*.csv'))
                jahresdateien = {int(p.stem.removeprefix('Abrechnung-')): p for p in dateien}
                kostenmatrix, fehler = kostenmatrix_lesen(jahresdateien)
                assert fehler == 0
                einzelkosten = "document.querySelector('.ana-verbraucherstatistik .ana-kostenstatistik .q-table tbody')"
                for abnehmer in datei_oeffnen(kopie / 'Datenbank/db_abnehmer.csv')[:2]:
                    auswahl('Verbraucher (Ident | Name Vorname)',
                            abnehmer['Ident'] + ' | ' + abnehmer['Name'] + ' ' + abnehmer['Vorname'])
                    jahre, verbrauch, minimum, fehler = verbrauchswerte_lesen(kopie / 'Abrechnungen', abnehmer['Ident'])
                    plot = "document.querySelector('.ana-statistik .js-plotly-plot')"
                    warten('Boolean(' + plot + '?.data?.length===2)')
                    assert json.loads(js('JSON.stringify(' + plot + '.data.map(s=>s.y))')) == [verbrauch, minimum]
                    assert json.loads(js('JSON.stringify(' + plot + '.data[0].x)')) == jahre
                    assert fehler == 0
                    # Änderung: Tatsächlichen Nullbeginn und sichtbare Jahrestabelle im Browser prüfen.
                    assert js(plot + '._fullLayout.yaxis.range[0]===0')
                    # Änderung: Vier Kennzahlzeilen und eine Spalte je Jahr statt Jahreszeilen prüfen.
                    assert js("document.querySelectorAll('.ana-statistik-tabelle tbody tr').length") == 4
                    assert json.loads(js("JSON.stringify(Array.from(document.querySelectorAll('.ana-statistik-tabelle thead th')).slice(1).map(e=>e.innerText.trim()))")) == [str(j) for j in jahre]
                    for spalte, (wert, mindestwert) in enumerate(zip(verbrauch, minimum), start=1):
                        differenz = wert - mindestwert if wert is not None and mindestwert is not None else None
                        prozent = differenz / mindestwert * 100 if differenz is not None and mindestwert != 0 else None
                        for zeilennummer, zahl in enumerate((wert, mindestwert, differenz, prozent)):
                            # Änderung: Einheiten in jeder gültigen Tabellenzelle mitprüfen.
                            # Änderung: kWh ohne Nachkommastellen, Prozent mit zwei Stellen prüfen.
                            stellen = 2 if zeilennummer == 3 else 0
                            textwert = '–' if zahl is None else f'{zahl:,.{stellen}f}'.replace(',', '_').replace('.', ',').replace('_', '.') + (' %' if zeilennummer == 3 else ' kWh')
                            assert js(f"document.querySelectorAll('.ana-statistik-tabelle tbody tr')[{zeilennummer}].querySelectorAll('td')[{spalte}].innerText.trim()") == textwert
                    assert js("document.querySelector('.ana-statistik-tabelle').innerText.includes('Abweichung prozentual')")
                    # Änderung: Die zweite Einzelstatistik zeigt zeitgleich nur diesen Verbraucher.
                    erwartet_einzel = [z for z in kostenmatrix if z['ident'] == abnehmer['Ident']]
                    assert js(einzelkosten + '.querySelectorAll("tr").length') == len(erwartet_einzel)
                    if erwartet_einzel:
                        zellen = einzelkosten + '.querySelectorAll("tr")[0].querySelectorAll("td")'
                        assert js(zellen + '.length') == len(jahresdateien)
                        for spalte, spaltenjahr in enumerate(sorted(jahresdateien)):
                            werttext = erwartet_einzel[0][f'jahr_{spaltenjahr}']
                            assert js(zellen + f'[{spalte}].innerText.trim()') == (werttext + ' €' if werttext != '–' else '–')
                for breite in (1440, 800):
                    cdp('Emulation.setDeviceMetricsOverride', {'width': breite, 'height': 1000,
                        'deviceScaleFactor': 1, 'mobile': False})
                    time.sleep(1)
                    assert js("document.querySelector('.ana-statistik').getBoundingClientRect().width <= window.innerWidth")
                print('Verbraucherspezifisch: gemeinsamer Filter, beide Statistiken, Verbraucherwechsel und Layout bestanden.', flush=True)
                # Änderung: Zweite Statistik als Jahresmatrix mit Beträgen, Reihenfolge und Farben prüfen.
                cdp('Emulation.setDeviceMetricsOverride', {'width': 1440, 'height': 1000,
                    'deviceScaleFactor': 1, 'mobile': False})
                time.sleep(1)
                statistikbereich('Allgemein')
                # Änderung: Asynchronen Statistikwechsel vor der Matrixprüfung abwarten.
                warten("Boolean(document.querySelector('.ana-allgemeine-statistik .ana-kostenstatistik')?.getClientRects().length)")
                from anwendung.kostenstatistik import kostenmatrix_lesen
                dateien = sorted((kopie / 'Abrechnungen').glob('Abrechnung-*/Abrechnung-*.csv'))
                jahresdateien = {int(p.stem.removeprefix('Abrechnung-')): p for p in dateien}
                erwartet, fehler = kostenmatrix_lesen(jahresdateien)
                assert fehler == 0
                # Änderung: Die Tabellen-Seitenlängenauswahl ist keine Jahresauswahl.
                assert js("!Array.from(document.querySelectorAll('.ana-kostenstatistik .q-select')).some(e=>!e.closest('.q-table__container'))")
                tabelle = "document.querySelector('.ana-allgemeine-statistik .q-table tbody')"
                warten('Boolean(' + tabelle + ')')
                assert js(tabelle + '.querySelectorAll("tr").length') == len(erwartet)
                # Änderung: Sortierpfeile dürfen zusätzlich zum Jahr in den Spaltenköpfen stehen.
                koepfe = json.loads(js("JSON.stringify(Array.from(document.querySelectorAll('.ana-allgemeine-statistik thead th')).slice(3).map(e=>e.innerText.trim()))"))
                assert len(koepfe) == len(jahresdateien)
                assert all(str(jahr) in kopf and '€' not in kopf for kopf, jahr in zip(koepfe, sorted(jahresdateien)))
                for index, zeile in enumerate(erwartet):
                    zelle = tabelle + '.querySelectorAll("tr")[' + str(index) + '].querySelectorAll("td")'
                    assert js(zelle + '[0].innerText.trim()') == zeile['ident']
                    # Änderung: Das Abrechnungsjahr des folgenden Praxislaufs nicht überschreiben.
                    for spalte, spaltenjahr in enumerate(sorted(jahresdateien), start=3):
                        feld = f'jahr_{spaltenjahr}'
                        assert js(zelle + f'[{spalte}].innerText.trim()') == (zeile[feld] + ' €' if zeile[feld] != '–' else '–')
                        assert js(zelle + f'[{spalte}].className.includes("bg-green-50")') == ('bg-green-50' in zeile['farben'].get(feld, ''))
                        assert js(zelle + f'[{spalte}].className.includes("bg-red-50")') == ('bg-red-50' in zeile['farben'].get(feld, ''))
                # Änderung: Eine andere Jahresspalte muss numerisch sortieren, fehlende Werte zuletzt.
                klicken("document.querySelectorAll('.ana-allgemeine-statistik thead th')[3]")
                time.sleep(.6)
                feld = f'sort_{min(jahresdateien)}'
                sortiert = sorted(erwartet, key=lambda z: (z[feld] is None, z[feld] or 0))
                assert json.loads(js('JSON.stringify(Array.from(' + tabelle + '.querySelectorAll("tr")).map(e=>e.querySelector("td").innerText.trim()))')) == [z['ident'] for z in sortiert]
                statistikbereich('Verbraucherspezifisch')
                print('Kostenvergleich: Jahresmatrix, alle Abnehmer, Spaltensortierung und Farben bestanden.', flush=True)
            # Änderung nach 2.049: Einstellungen mit echten Dialogelementen prüfen, ohne zu speichern.
            if not rueckverguetung:
                SCHRITT = 'Einstellungsdialog prüfen'
                warten("Boolean(document.querySelector('.ana-settings'))")
                menue = "document.querySelector('button[aria-label=\"Navigation ein-/ausblenden\"]')"
                navigation_offen = js("document.querySelector('.q-drawer').getBoundingClientRect().right > 0")
                if not navigation_offen:
                    klicken(menue)
                    time.sleep(1)
                ini_vorher = (run / 'ana.ini').read_bytes()
                knopf('Einstellungen')
                warten("Boolean(document.querySelector('.ana-settings-dialog'))")
                # Änderung: Vier getrennte Tabs, bestehende Eingaben und gemeinsame Aktionsleiste.
                einstellungstabs = ['Betreiber und Preise', 'Arbeitsordner', 'Datensicherung', 'Darstellung']
                assert json.loads(js("JSON.stringify(Array.from(document.querySelectorAll('.ana-settings-tabs .q-tab__label')).map(e=>e.textContent.trim()))")) == einstellungstabs
                assert js("document.querySelectorAll('.ana-settings-operator .q-field').length === 5")
                einstellungstab('Datensicherung')
                assert js("document.querySelector('.ana-backup-settings').innerText.includes('Jetzt sichern')")
                assert js("document.querySelector('.ana-backup-settings').innerText.includes('Bei Programmbeendigung sichern')")
                assert js("document.querySelector('.ana-backup-retention').getClientRects().length === 0")
                klicken("document.querySelectorAll('.ana-backup-settings .q-checkbox')[1]")
                warten("document.querySelector('.ana-backup-retention').getClientRects().length > 0")
                eingabe('Aufbewahrung in Wochen', 6)
                klicken("document.querySelectorAll('.ana-backup-settings .q-checkbox')[1]")
                warten("document.querySelector('.ana-backup-retention').getClientRects().length === 0")
                klicken("document.querySelectorAll('.ana-backup-settings .q-checkbox')[1]")
                warten("document.querySelector('.ana-backup-retention').getClientRects().length > 0")
                assert js("document.querySelector('.ana-backup-retention input').value") == '6'
                einstellungstab('Darstellung')
                assert js("document.querySelectorAll('.ana-settings-appearance .q-field').length === 3")
                eingabe('Hervorhebungsfarbe', 'teal')
                # Änderung: Dialog, Tabs und Aktionsleiste dürfen beim Tabwechsel nicht wandern.
                for breite, hoehe in ((1440, 900), (800, 900), (400, 900), (800, 600)):
                    cdp('Emulation.setDeviceMetricsOverride', {'width': breite, 'height': hoehe,
                        'deviceScaleFactor': 1, 'mobile': False})
                    time.sleep(1)
                    vorher = None
                    for name in einstellungstabs:
                        einstellungstab(name)
                        assert js("(()=>{const r=document.querySelector('.ana-settings-dialog').getBoundingClientRect();const f=document.querySelector('.ana-settings-footer').getBoundingClientRect();const t=document.querySelector('.ana-settings-tabs').getBoundingClientRect();return r.left>=0 && r.right<=window.innerWidth+1 && f.bottom<=window.innerHeight+1 && t.top>=r.top && t.bottom<f.top})()")
                        position = js("(()=>{const r=document.querySelector('.ana-settings-dialog').getBoundingClientRect();const t=document.querySelector('.ana-settings-tabs').getBoundingClientRect();const f=document.querySelector('.ana-settings-footer').getBoundingClientRect();return [r.top,r.height,t.top,f.top]})()")
                        if vorher is not None:
                            assert all(abs(a - b) <= 1 for a, b in zip(position, vorher))
                        vorher = position
                assert js("document.querySelector('.ana-settings-appearance input').value") == 'teal'
                cdp('Emulation.clearDeviceMetricsOverride', {})
                time.sleep(1)
                knopf('Abbrechen', "document.querySelector('.ana-settings-dialog')")
                warten("!document.querySelector('.ana-settings-dialog')")
                assert (run / 'ana.ini').read_bytes() == ini_vorher
                if not navigation_offen:
                    klicken(menue)
                    time.sleep(1)
                print('Einstellungen: vier Tabs, Werterhalt, bedingte Aufbewahrung, Abbrechen und stabile Dialog-/Tabposition bei 1440/800/400 sowie 600 Pixel Höhe bestanden.', flush=True)
            # Änderung 2.049: Register anhand ihrer Beschriftung finden; Navigationsicons nicht mitlesen.
            if rueckverguetung:
                # Änderung für v2: Rückvergütung vollständig über die echte Oberfläche prüfen.
                SCHRITT = 'Rückvergütungsregister laden'
                warten("Boolean(Array.from(document.querySelectorAll('.q-tab')).find(e=>e.querySelector('.q-tab__label')?.textContent.trim()==='Rückvergütung'))")
                js("Array.from(document.querySelectorAll('.q-tab')).find(e=>e.querySelector('.q-tab__label')?.textContent.trim()==='Rückvergütung').click()")
                time.sleep(1)
                auswahl('Jahr der Rückvergütung', jahr)
                SCHRITT = 'Rückvergütungssatz und Beschlussdatum eingeben'
                eingabe('Rückergütung in %', fall['satz'])
                eingabe('Datum Beschluss', fall['datum'])
                SCHRITT = 'Rückvergütung berechnen'
                knopf('Berechnen')
                warten("Array.from(document.querySelectorAll('button')).some(e=>e.getClientRects().length && (e.querySelector('.q-btn__content > .block')?.textContent || e.textContent).trim().endsWith('Speichern') && !e.disabled)")
                assert js("Array.from(document.querySelectorAll('.ag-root')).some(e=>e.getClientRects().length && e.querySelectorAll('.ag-center-cols-container .ag-row').length>0)")
                print('Rückvergütung berechnet, Tabelle und Schaltflächen: bestanden.', flush=True)
                SCHRITT = 'Rückvergütung speichern'
                knopf('Speichern')
                dialog = "Array.from(document.querySelectorAll('.q-dialog')).find(e=>e.getClientRects().length && e.textContent.includes('Rückvergütung wirklich speichern'))"
                warten('Boolean(' + dialog + ')')
                js("(" + dialog + ").querySelectorAll('.q-checkbox').forEach(e=>{if(e.getClientRects().length && e.getAttribute('aria-checked')!=='true')e.click()})")
                knopf('Ja', '(' + dialog + ')')
                warten("Array.from(document.querySelectorAll('button')).some(e=>e.getClientRects().length && (e.querySelector('.q-btn__content > .block')?.textContent || e.textContent).trim().endsWith('Word/PDF erstellen') && !e.disabled)")
                gespeichert = kopie / 'Rückvergütungen' / ('Rückvergütung-' + jahr) / ('Rückvergütung-' + jahr + '.csv')
                assert gespeichert.read_text() == erwartete_csv
                print('Rückvergütung gespeichert und mit Referenz verglichen: bestanden.', flush=True)
                SCHRITT = 'Rückvergütungsdokumente erzeugen'
                export_starten('Word/PDF erstellen')
                zielordner = gespeichert.parent
                for _ in range(300):
                    docs = list((zielordner / 'word').glob('*.docx'))
                    pdfs = list((zielordner / 'pdf').glob('*.pdf'))
                    if len(docs) == len(fall['ergebnis']) and len(pdfs) == len(docs) and all(p.stat().st_size for p in pdfs):
                        break
                    time.sleep(1)
                else:
                    raise TimeoutError()
                from pypdf import PdfReader
                assert all(len(PdfReader(p).pages) > 0 for p in pdfs)
                # Änderung für v2: Kopierte Altdokumente dürfen keinen erfolgreichen Test vortäuschen.
                assert all(p.stat().st_mtime >= (run / 'app.pid').stat().st_mtime for p in docs + pdfs)
                print('Rückvergütung: Echte Word-/PDF-Erstellung bestanden.', flush=True)
            else:
                SCHRITT = 'Abrechnungsregister laden'
                # Änderung für v2: Textinhalt verwenden; CSS-Großschreibung verändert innerText.
                warten("Boolean(Array.from(document.querySelectorAll('.q-tab')).find(e=>e.querySelector('.q-tab__label')?.textContent.trim()==='Abrechnungen'))")
                js("Array.from(document.querySelectorAll('.q-tab')).find(e=>e.querySelector('.q-tab__label')?.textContent.trim()==='Abrechnungen').click()")
                time.sleep(1)
                # Änderung 2.049: Desktop- und schmale Ansicht sowie Einklappen wirklich prüfen.
                for breite in (1440, 800):
                    cdp('Emulation.setDeviceMetricsOverride', {'width': breite, 'height': 1000,
                        'deviceScaleFactor': 1, 'mobile': False})
                    time.sleep(1)
                    menue = "document.querySelector('button[aria-label=\"Navigation ein-/ausblenden\"]')"
                    assert js('Boolean(' + menue + ')')
                    vorher = js("document.querySelector('.q-drawer').getBoundingClientRect().right")
                    klicken(menue)
                    time.sleep(1)
                    nachher = js("document.querySelector('.q-drawer').getBoundingClientRect().right")
                    assert abs(vorher - nachher) > 100
                    # Bei schmalem Fenster die überlagernde Navigation geschlossen lassen.
                    if nachher > 0:
                        klicken(menue)
                        time.sleep(1)
                    assert js("document.documentElement.scrollWidth <= window.innerWidth + 1")
                # Änderung 2.049: Für native Mausklicks anschließend die echte Fenstergröße verwenden.
                cdp('Emulation.clearDeviceMetricsOverride', {})
                time.sleep(1)
                # Änderung 2.049: Der Größenwechsel kann die mobile Navigation erneut öffnen.
                # Vor der Fachbedienung die überlagernde Leiste über den echten Menüknopf schließen.
                if js("document.querySelector('.q-drawer').getBoundingClientRect().right > 0"):
                    klicken(menue)
                    time.sleep(1)
                print('Navigation ein-/ausklappen und Layout bei 1440/800 Pixeln: bestanden.', flush=True)
                SCHRITT = 'Jahr und Mehrwertsteuer auswählen'
                auswahl('Abrechnungsjahr', jahr)
                auswahl('Mehrwertsteuer in %', mwst)
                SCHRITT = 'Berechnen und Anzeige prüfen'
                # Änderung nach 2.049: Kurze Beschriftung der kompakten Aktionsleiste bedienen.
                assert js("document.querySelectorAll('.ana-compact-toolbar button').length === 6")
                assert js("document.querySelectorAll('.ana-compact-toolbar .ana-button-group').length === 2")
                # Änderung nach 2.049: Umsatz gehört zu den Eingaben, keine sichtbare Extra-Ergebniszeile.
                assert js("Boolean(document.querySelector('.ana-input-row .ana-inline-summary'))")
                assert js("document.querySelector('.ana-action-row').classList.contains('hidden')")
                knopf('Berechnen')
                warten("Array.from(document.querySelectorAll('button')).some(e=>e.getClientRects().length && (e.querySelector('.q-btn__content > .block')?.textContent || e.textContent).trim().endsWith('Speichern') && !e.disabled)")
                assert js("document.querySelectorAll('.ag-center-cols-container .ag-row').length > 0")
                print('Berechnung, Tabellenanzeige und Speichern-Schaltfläche: bestanden.', flush=True)
                SCHRITT = 'Speicherdialog bestätigen'
                knopf('Speichern')
                warten("Array.from(document.querySelectorAll('.q-dialog')).some(e=>e.innerText.includes('Abrechnungsdaten wirklich speichern'))")
                js("Array.from(document.querySelectorAll('.q-dialog .q-checkbox')).filter(e=>e.getClientRects().length && e.getAttribute('aria-checked')!=='true').forEach(e=>e.click())")
                knopf('Ja', "Array.from(document.querySelectorAll('.q-dialog')).find(e=>e.innerText.includes('Abrechnungsdaten wirklich speichern'))")
                # Änderung für v2: Nachfragen zur Folgejahres-Mindestabnahme nur in der Datenkopie beantworten.
                for _ in range(120):
                    dialog = "Array.from(document.querySelectorAll('.q-dialog')).find(e=>e.getClientRects().length && e.innerText.includes('Mindestabnahme auch im folgenden Jahr aussetzen'))"
                    if js('Boolean(' + dialog + ')'):
                        knopf('Nein', '(' + dialog + ')')
                    bereit = js("Array.from(document.querySelectorAll('button')).some(e=>e.getClientRects().length && (e.querySelector('.q-btn__content > .block')?.textContent || e.textContent).trim().endsWith('Word/PDF erstellen') && !e.disabled)")
                    if bereit and not js("Array.from(document.querySelectorAll('.q-dialog')).some(e=>e.getClientRects().length)"):
                        break
                    time.sleep(.5)
                gespeichert = kopie / 'Abrechnungen' / ('Abrechnung-' + jahr) / ('Abrechnung-' + jahr + '.csv')
                assert gespeichert.read_text() == erwartete_csv
                print('Speichern und Vergleich mit Referenzergebnis: bestanden.', flush=True)
                SCHRITT = 'Word und PDF aus Oberfläche erzeugen'
                export_starten('Word/PDF erstellen')
                # Änderung: Während des tatsächlichen Stapels muss der Knopf gesperrt sein.
                warten("Array.from(document.querySelectorAll('button')).some(e=>(e.querySelector('.q-btn__content > .block')?.textContent || e.textContent).trim().endsWith('Word/PDF erstellen') && e.disabled)")
                zielordner = gespeichert.parent
                for _ in range(240):
                    docs = list((zielordner / 'word').glob('*.docx'))
                    pdfs = list((zielordner / 'pdf').glob('*.pdf'))
                    if len(docs) == len(fall['ergebnis']) and len(pdfs) == len(docs) and all(p.stat().st_size for p in pdfs):
                        break
                    time.sleep(1)
                else:
                    raise TimeoutError()
                from pypdf import PdfReader
                assert all(len(PdfReader(p).pages) > 0 for p in pdfs)
                print('Echte Word-/PDF-Erstellung über die Oberfläche: bestanden.', flush=True)
            # Änderung: Abschluss des Threads und UI-Timers vor Testende abwarten.
            # Änderung nach 2.049: Gemeinsame kompakte Beschriftung in beiden Ansichten.
            exporttext = 'Word/PDF erstellen'
            warten("Array.from(document.querySelectorAll('button')).some(e=>(e.querySelector('.q-btn__content > .block')?.textContent || e.textContent).trim().endsWith("
                   + json.dumps(exporttext) + ") && !e.disabled)")
            # Änderung nach 2.049: Quasar meldet den Balkenmaßstab über aria-valuemax (0 bis 1).
            assert js("Array.from(document.querySelectorAll('button')).some(e=>{const p=e.querySelector('.ana-button-progress');return e.getClientRects().length && (e.querySelector('.q-btn__content > .block')?.textContent || e.textContent).trim().endsWith('Word/PDF erstellen') && p && Number(p.getAttribute('aria-valuemax'))>0 && Number(p.getAttribute('aria-valuenow'))===Number(p.getAttribute('aria-valuemax'))})")
            # Änderung nach 2.049: Prozentzahl muss im sichtbaren Exportbutton erscheinen.
            assert js("Array.from(document.querySelectorAll('button')).some(e=>e.getClientRects().length && e.querySelector('.ana-button-percent')?.textContent.trim()==='100 %' && !e.querySelector('.ana-button-percent').classList.contains('invisible'))")
            if not rueckverguetung:
                # Änderung nach 2.05.00: Echte Backup-Bedienung nach vollständigem Dokumentlauf prüfen.
                SCHRITT = 'Vollsicherung über Einstellungen'
                if not js("document.querySelector('.q-drawer').getBoundingClientRect().right > 0"):
                    klicken("document.querySelector('button[aria-label=\"Navigation ein-/ausblenden\"]')")
                    time.sleep(1)
                knopf('Einstellungen')
                einstellungstab('Datensicherung')
                warten("Boolean(document.querySelector('.ana-backup-settings input'))")
                assert js("document.querySelector('.ana-backup-retention').getClientRects().length === 0")
                sicherungsziel = run / 'vollsicherungen'
                js("(()=>{const e=document.querySelector('.ana-backup-settings input');e.value="
                   + json.dumps(str(sicherungsziel)) + ";e.dispatchEvent(new Event('input',{bubbles:true}))})()")
                time.sleep(1)
                # Änderung: Beide Optionen sowie Wochen einstellen und tatsächlich in INI speichern.
                klicken("document.querySelectorAll('.ana-backup-settings .q-checkbox')[0]")
                klicken("document.querySelectorAll('.ana-backup-settings .q-checkbox')[1]")
                warten("document.querySelector('.ana-backup-retention').getClientRects().length > 0")
                js("(()=>{const e=document.querySelector('.ana-backup-settings input[type=number]');e.value='8';e.dispatchEvent(new Event('input',{bubbles:true}))})()")
                time.sleep(1)
                knopf('Speichern', "document.querySelector('.ana-settings-dialog')")
                warten("!document.querySelector('.ana-settings-dialog')")
                sicherungsconfig = ini_datei_lesen(run / 'ana.ini')['Sicherung']
                assert sicherungsconfig['Ordner'] == str(sicherungsziel)
                assert sicherungsconfig['BeiProgrammende'] == sicherungsconfig['Aufraeumen'] == 'ja'
                assert sicherungsconfig['AufbewahrungWochen'] == '8'
                knopf('Einstellungen')
                einstellungstab('Datensicherung')
                warten("Boolean(document.querySelector('.ana-backup-settings input'))")
                assert js("document.querySelector('.ana-backup-settings input').value") == str(sicherungsziel)
                assert js("Array.from(document.querySelectorAll('.ana-backup-settings .q-checkbox')).every(e=>e.getAttribute('aria-checked')==='true')")
                assert js("document.querySelector('.ana-backup-settings input[type=number]').value") == '8'
                assert js("document.querySelector('.ana-backup-retention').getClientRects().length > 0")
                # Änderung: Nach der normalen Öffnungsanimation Größe/Position und Balkeninhalt
                # während des Laufs lokal messen; der Dialogeffekt ist keine Inhaltsänderung.
                js("window.anaBackupMessung=[];window.anaBackupStart=null;window.anaBackupTimer=setInterval(()=>{const d=document.querySelector('.ana-backup-progress');if(!d)return;if(window.anaBackupStart===null)window.anaBackupStart=performance.now();if(performance.now()-window.anaBackupStart<400)return;const b=d.querySelector('.ana-backup-total');const k=d.querySelector('button');const r=d.getBoundingClientRect();const br=b.getBoundingClientRect();window.anaBackupMessung.push({rahmen:[r.x,r.y,r.width,r.height,br.y,k.getBoundingClientRect().y],wert:Number(b.getAttribute('aria-valuenow')),text:b.textContent.trim(),gesperrt:k.disabled})},50)")
                knopf('Jetzt sichern')
                warten("Boolean(document.querySelector('.ana-backup-progress .q-linear-progress'))")
                # Änderung: Genau ein Gesamtbalken für Komprimieren und Sichern.
                assert js("document.querySelectorAll('.ana-backup-progress .q-linear-progress').length === 1")
                assert js("document.querySelector('.ana-backup-progress .ana-backup-total').getAttribute('aria-label')") == 'Gesamtfortschritt Komprimieren und Sichern'
                warten("document.querySelector('.ana-backup-progress')?.innerText.includes('Sicherung gespeichert:')", 120)
                assert js("document.querySelector('.ana-backup-progress').innerText.includes('100 %')")
                time.sleep(.2)
                messungen = js('clearInterval(window.anaBackupTimer);window.anaBackupMessung')
                assert len(messungen) >= 2 and any(m['gesperrt'] for m in messungen)
                assert not messungen[-1]['gesperrt'] and messungen[-1]['wert'] == 1
                assert all(m['text'] == '' for m in messungen)
                assert all(all(abs(a - b) <= 1 for a, b in zip(m['rahmen'], messungen[0]['rahmen'])) for m in messungen)
                assert [m['wert'] for m in messungen] == sorted(m['wert'] for m in messungen)
                # Änderung: Auch lange Abschlusspfade dürfen auf schmalen Fenstern nichts verschieben.
                for breite in (400, 800, 1440):
                    cdp('Emulation.setDeviceMetricsOverride', {'width': breite, 'height': 900,
                        'deviceScaleFactor': 1, 'mobile': False})
                    time.sleep(.5)
                    assert js("(()=>{const d=document.querySelector('.ana-backup-progress');const r=d.getBoundingClientRect();const b=d.querySelector('button').getBoundingClientRect();return r.left>=0 && r.right<=innerWidth+1 && r.bottom<=innerHeight+1 && b.bottom<=r.bottom && d.scrollHeight<=d.clientHeight+1})()")
                cdp('Emulation.clearDeviceMetricsOverride', {})
                time.sleep(.5)
                knopf('Schließen', "document.querySelector('.ana-backup-progress')")
                warten("!document.querySelector('.ana-backup-progress')")
                knopf('Abbrechen', "document.querySelector('.ana-settings-dialog')")
                warten("!document.querySelector('.ana-settings-dialog')")
                assert len(list(sicherungsziel.glob('ANA-Vollsicherung-*.zip'))) == 1
                print('Vollsicherung: gespeicherte Optionen, ZIP-Lauf, stabiler Dialog, textfreier Balken und monotoner Gesamtfortschritt bestanden.', flush=True)

                # Änderung: Natives Fenster-X auslösen; reale automatische Sicherung abwarten.
                SCHRITT = 'Vollsicherung bei nativem Fenster-X'
                import win32con
                import win32gui
                import win32process
                from tests.testprozesse import prozessliste
                pids = {p['ProcessId'] for p in prozessliste() if p['ParentProcessId'] == app.pid}
                fenster = []
                def suchen(hwnd, _):
                    if win32process.GetWindowThreadProcessId(hwnd)[1] in pids and win32gui.GetWindowText(hwnd) == 'ANA':
                        fenster.append(hwnd)
                win32gui.EnumWindows(suchen, None)
                assert len(fenster) == 1
                win32gui.PostMessage(fenster[0], win32con.WM_CLOSE, 0, 0)
                anzeige_gesehen = False
                anzeige_pids = {app.pid}
                for _ in range(600):
                    # Änderung: Eigenständigen Anzeigeprozess einbeziehen und echte Sichtbarkeit prüfen.
                    if not anzeige_gesehen:
                        anzeige_pids.update(p['ProcessId'] for p in prozessliste() if p['ParentProcessId'] == app.pid)
                    sichtbar = []
                    def anzeige_suchen(hwnd, _):
                        if (win32process.GetWindowThreadProcessId(hwnd)[1] in anzeige_pids
                                and win32gui.GetWindowText(hwnd) == 'ANA – Sicherung beim Beenden'
                                and win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd)):
                            sichtbar.append(hwnd)
                    win32gui.EnumWindows(anzeige_suchen, None)
                    anzeige_gesehen = anzeige_gesehen or bool(sichtbar)
                    if app.poll() is not None:
                        break
                    time.sleep(.1)
                else:
                    raise TimeoutError('Automatische Sicherung oder Programmende nicht abgeschlossen')
                assert anzeige_gesehen
                assert len(list(sicherungsziel.glob('ANA-Vollsicherung-*.zip'))) == 2
                from zipfile import ZipFile
                jetzt = bestand(kopie)
                for archiv in sicherungsziel.glob('ANA-Vollsicherung-*.zip'):
                    with ZipFile(archiv) as zipdatei:
                        assert zipdatei.testzip() is None
                        gesichert = {n.removeprefix('Arbeitsordner/').replace('/', '\\'): hashlib.sha256(zipdatei.read(n)).digest()
                                     for n in zipdatei.namelist() if n.startswith('Arbeitsordner/') and not n.endswith('/')}
                        assert gesichert == jetzt
                        assert zipdatei.read('Programmeinstellungen/ana.ini') == (run / 'ana.ini').read_bytes()
                print('Fenster-X: native Fortschrittsanzeige, automatische ZIP-Sicherung und vollständige Daten/INI bestanden.', flush=True)
        assert bestand(daten) == originalbestand
        # Änderung: Das Startfenster muss sich nach Verbindung selbständig geschlossen haben.
        assert (run / 'startanzeige-geschlossen.txt').is_file()
        erfolgreich = True
        print('Original-Beispieldaten unverändert. Oberflächentest bestanden.', flush=True)
        print('Lokale Testausgabe: ' + str(run), flush=True)
    finally:
        # Änderung: Der äußere TestProzesse-Kontext beendet immer den gesamten Prozessbaum.
        log.close()


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--app':
        app_starten(Path(sys.argv[2]))
    else:
        try:
            testen('--rueckverguetung' in sys.argv[1:])
        except Exception as fehler:
            # Änderung: Fehlerstelle ausschließlich lokal sichern, ohne Beispieldaten auszugeben.
            (BASIS / '.lokal/oberflaechentest-fehler.txt').write_text(
                __import__('traceback').format_exc(), encoding='utf-8')
            print('Oberflächentest nicht abgeschlossen. Schritt: ' + SCHRITT
                  + '. Fehlertyp: ' + type(fehler).__name__, flush=True)
            raise SystemExit(1)
