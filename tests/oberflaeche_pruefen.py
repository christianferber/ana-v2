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
    ana.ini = str(ordner / 'ana.ini')
    original_run = ana.ui.run
    def test_run(**kwargs):
        kwargs.update(host='127.0.0.1', port=int((ordner / 'port.txt').read_text()))
        return original_run(**kwargs)
    ana.ui.run = test_run
    ana.main()


def bestand(daten):
    # Änderung für v2: Originaldateien lokal auf unveränderte Inhalte kontrollieren.
    return {str(p.relative_to(daten)): hashlib.sha256(p.read_bytes()).digest()
            for p in daten.rglob('*') if p.is_file()}


def testen(rueckverguetung=False):
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
    ini_datei_schreiben(run / 'ana.ini', config)
    port = freier_port()
    (run / 'port.txt').write_text(str(port))
    log = (run / 'app.log').open('w', encoding='utf-8')
    # Änderung für v2: Paketstart erhält den Projektordner im Python-Suchpfad.
    app = subprocess.Popen([sys.executable, '-m', 'tests.oberflaeche_pruefen', '--app', str(run)],
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
        browser = subprocess.Popen([
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            '--headless=new', '--remote-debugging-port=0', '--user-data-dir=' + str(profil),
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
                suche = ("Array.from(" + scope + ".querySelectorAll('button')).find(e=>"
                         "e.getClientRects().length && e.textContent.trim().endsWith(" + json.dumps(text) + "))")
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
            SCHRITT = 'Testseite laden'
            cdp('Page.navigate', {'url': url})
            if rueckverguetung:
                # Änderung für v2: Rückvergütung vollständig über die echte Oberfläche prüfen.
                SCHRITT = 'Rückvergütungsregister laden'
                warten("Boolean(Array.from(document.querySelectorAll('.q-tab')).find(e=>e.textContent.trim()==='Rückvergütung'))")
                js("Array.from(document.querySelectorAll('.q-tab')).find(e=>e.textContent.trim()==='Rückvergütung').click()")
                time.sleep(1)
                auswahl('Jahr der Rückvergütung', jahr)
                SCHRITT = 'Rückvergütungssatz und Beschlussdatum eingeben'
                eingabe('Rückergütung in %', fall['satz'])
                eingabe('Datum Beschluss', fall['datum'])
                SCHRITT = 'Rückvergütung berechnen'
                knopf('Erstellung Rückvergütung')
                warten("Array.from(document.querySelectorAll('button')).some(e=>e.getClientRects().length && e.textContent.trim().endsWith('Speichern') && !e.disabled)")
                assert js("Array.from(document.querySelectorAll('.ag-root')).some(e=>e.getClientRects().length && e.querySelectorAll('.ag-center-cols-container .ag-row').length>0)")
                print('Rückvergütung berechnet, Tabelle und Schaltflächen: bestanden.', flush=True)
                SCHRITT = 'Rückvergütung speichern'
                knopf('Speichern')
                dialog = "Array.from(document.querySelectorAll('.q-dialog')).find(e=>e.getClientRects().length && e.textContent.includes('Rückvergütung wirklich speichern'))"
                warten('Boolean(' + dialog + ')')
                js("(" + dialog + ").querySelectorAll('.q-checkbox').forEach(e=>{if(e.getClientRects().length && e.getAttribute('aria-checked')!=='true')e.click()})")
                knopf('Ja', '(' + dialog + ')')
                warten("Array.from(document.querySelectorAll('button')).some(e=>e.getClientRects().length && e.textContent.trim().endsWith('Word/PDF-Rückvergütungen erzeugen') && !e.disabled)")
                gespeichert = kopie / 'Rückvergütungen' / ('Rückvergütung-' + jahr) / ('Rückvergütung-' + jahr + '.csv')
                assert gespeichert.read_text() == erwartete_csv
                print('Rückvergütung gespeichert und mit Referenz verglichen: bestanden.', flush=True)
                SCHRITT = 'Rückvergütungsdokumente erzeugen'
                knopf('Word/PDF-Rückvergütungen erzeugen')
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
                warten("Boolean(Array.from(document.querySelectorAll('.q-tab')).find(e=>e.textContent.trim()==='Abrechnungen'))")
                js("Array.from(document.querySelectorAll('.q-tab')).find(e=>e.textContent.trim()==='Abrechnungen').click()")
                time.sleep(1)
                SCHRITT = 'Jahr und Mehrwertsteuer auswählen'
                auswahl('Abrechnungsjahr', jahr)
                auswahl('Mehrwertsteuer in %', mwst)
                SCHRITT = 'Berechnen und Anzeige prüfen'
                knopf('Erstellung Jahresabrechnung')
                warten("Array.from(document.querySelectorAll('button')).some(e=>e.getClientRects().length && e.textContent.trim().endsWith('Speichern') && !e.disabled)")
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
                    bereit = js("Array.from(document.querySelectorAll('button')).some(e=>e.getClientRects().length && e.textContent.trim().endsWith('Word/PDF-Abrechnungen erzeugen') && !e.disabled)")
                    if bereit and not js("Array.from(document.querySelectorAll('.q-dialog')).some(e=>e.getClientRects().length)"):
                        break
                    time.sleep(.5)
                gespeichert = kopie / 'Abrechnungen' / ('Abrechnung-' + jahr) / ('Abrechnung-' + jahr + '.csv')
                assert gespeichert.read_text() == erwartete_csv
                print('Speichern und Vergleich mit Referenzergebnis: bestanden.', flush=True)
                SCHRITT = 'Word und PDF aus Oberfläche erzeugen'
                knopf('Word/PDF-Abrechnungen erzeugen')
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
        assert bestand(daten) == originalbestand
        erfolgreich = True
        print('Original-Beispieldaten unverändert. Oberflächentest bestanden.', flush=True)
        print('Lokale Testausgabe: ' + str(run), flush=True)
    finally:
        if browser is not None:
            browser.terminate()
        # Änderung für v2: Erfolgreich getestete Anwendung für die lokale Ansicht geöffnet lassen.
        if not erfolgreich:
            app.terminate()
        log.close()


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--app':
        app_starten(Path(sys.argv[2]))
    else:
        try:
            testen(sys.argv[1:] == ['--rueckverguetung'])
        except Exception as fehler:
            print('Oberflächentest nicht abgeschlossen. Schritt: ' + SCHRITT
                  + '. Fehlertyp: ' + type(fehler).__name__, flush=True)
            raise SystemExit(1)
