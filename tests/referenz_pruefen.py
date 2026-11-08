# Änderung für v2: In tests/ eingeordnet; Modul- und Dateipfade angepasst.
"""Änderung für v2: Berechnungsreferenzen ausschließlich lokal erzeugen und prüfen.

Aufruf: python -m tests.referenz_pruefen erstellen | pruefen
Es werden keine Dateninhalte, Dateinamen aus Beispieldaten oder Fehlerwerte ausgegeben.
Die Anwendung und ihre Speicherfunktionen werden nicht gestartet.
"""

import ast
import contextlib
import copy
# Änderung für v2: Referenzlauf verwendet jetzt die tatsächlich ausgelagerte Leseroutine.
from anwendung.datenhaltung import datei_oeffnen
# Änderung für v2: Die ausgelagerte Pfadbildung im Berechnungslauf verwenden.
from anwendung.einstellungen import pfade_erstellen, ini_datei_lesen
from datetime import datetime, timedelta
import hashlib
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace
# Änderung für v2: Tatsächliche GUI-unabhängige Berechnung im Referenzlauf verwenden.
from anwendung import berechnungen
BASIS = Path(__file__).resolve().parents[1]
REFERENZ = BASIS / '.lokal' / 'berechnungsreferenz.json'
# Änderung für v2: Nur feste Prüfschrittnamen zur datensparsamen Fehlerdiagnose verwenden.
PRUEFSCHRITT = 'Vorbereitung'


class Anzeige:
    # Änderung für v2: Anzeigen im Prüflauf ersetzen, ohne die Berechnung zu ändern.
    def __init__(self, value=None):
        self.value = value

    def refresh(self, *args):
        pass

    def enable(self):
        pass

    def set_text(self, text):
        pass


def csv_lesen(pfad):
    # Änderung für v2: Auch die neue Modulgrenze in die Referenzprüfung einbeziehen.
    return datei_oeffnen(pfad)


def funktionen_laden():
    # Änderung für v2: Originalfunktionen laden; keine Imports, GUI oder Startaktionen ausführen.
    namen = {
        'tablefields_to_int', 'tablefields_to_dotfloat',
    }
    # Änderung 2.044: Die tatsächlich importierten Hilfen statt kopierter Funktionskörper prüfen.
    from anwendung import datenaufbereitung
    baum = ast.parse((BASIS / 'anwendung' / 'datenaufbereitung.py').read_text(encoding='utf-8-sig'))
    funktionen = [knoten for knoten in baum.body
                  if isinstance(knoten, ast.FunctionDef) and knoten.name in namen]
    if {knoten.name for knoten in funktionen} != namen:
        raise RuntimeError('Funktionen fehlen')
    for knoten in funktionen:
        knoten.decorator_list = []
    umgebung = {'datetime': datetime, 'timedelta': timedelta}
    # Änderung für v2: Dieselben importierten Funktionen wie in ANA bereitstellen.
    umgebung.update({name: getattr(berechnungen, name) for name in (
        'abrechnung_berechnen', 'abnehmer_aus_daten', 'mwst_berechnen',
        'datum_in_string', 'datum_in_punkt', 'datum_tage_vorher')})
    umgebung['mindestabnahme_berechnen'] = berechnungen.letzte_mindestabnahme
    umgebung.update({name: getattr(datenaufbereitung, name) for name in namen})
    # Änderung 2.03: Echte Instanzmethoden ausführen. Die bestehende Prüfoberfläche
    # als Wörterbuch beibehalten, damit der unabhängige Originalvergleich weiterläuft.
    from anwendung import abrechnung_ui
    from unittest.mock import patch
    ansicht = abrechnung_ui.AbrechnungOberflaeche(SimpleNamespace())
    def abrechnung_erstellen():
        for name in ('abrechnung', 'jahre_dropdown', 'mwst_jahr', 'za_switch', 'za_datum',
                     'za_mwst', 'abr_button_speichern', 'abr_button_download',
                     'abrechnung_grid_ui', 'label_umsatz'):
            setattr(ansicht, name, umgebung[name])
        for name in ('abnehmer_db', 'zaehler_db', 'abschlag_db', 'arbeitspreis', 'grundgebuehr'):
            setattr(ansicht.anwendung, name, umgebung[name])
        with patch.object(abrechnung_ui, 'ui', umgebung['ui']):
            ansicht.abrechnung_erstellen_gui()
        umgebung['abrechnung'] = ansicht.abrechnung
    umgebung['abrechnung_erstellen_gui'] = abrechnung_erstellen
    return umgebung


def ergebnisse_berechnen():
    global PRUEFSCHRITT
    # Änderung für v2: Nur den ausdrücklich freigegebenen Beispielordner zulassen.
    # Änderung für v2: Tatsächliche INI-Leseroutine auch im Referenzlauf verwenden.
    einstellungen = ini_datei_lesen(BASIS / 'ana.ini')
    daten = Path(einstellungen['Anwendung']['arbeitsordner']).resolve()
    erlaubt = (BASIS.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
    if daten != erlaubt or not daten.is_dir():
        raise RuntimeError('Beispielpfad nicht freigegeben')
    # Änderung für v2: Beispieldaten über dieselben Pfade wie die Anwendung laden.
    pfade = pfade_erstellen(str(daten))
    datenbank = Path(pfade['ordner_datenbank'])

    PRUEFSCHRITT = 'Betreibereinstellungen'
    betreiber = ini_datei_lesen(daten / 'ana-betreiber.ini')
    PRUEFSCHRITT = 'Datenbanken laden'
    umgebung = funktionen_laden()
    abnehmer = umgebung['tablefields_to_int'](csv_lesen(datenbank / 'db_abnehmer.csv'))
    zaehler = umgebung['tablefields_to_int'](csv_lesen(datenbank / 'db_zaehler.csv'))
    abschlag = umgebung['tablefields_to_dotfloat'](csv_lesen(datenbank / 'db_abschlag.csv'))
    ergebnisse = []

    # Änderung für v2: Jahr und Steuerparameter aus vorhandenen Beispielabrechnungen übernehmen.
    for pfad in sorted(Path(pfade['ordner_abrechnungen']).glob('Abrechnung-*/Abrechnung-*.csv')):
        PRUEFSCHRITT = 'Parameter vorhandener Abrechnungen'
        gespeichert = csv_lesen(pfad)
        if not gespeichert:
            continue
        erste = gespeichert[0]
        # Änderung für v2: Ältere Exporte enthalten das Jahr nur im Ordnernamen.
        jahr = str(erste.get('Abrechnungsjahr', pfad.parent.name.removeprefix('Abrechnung-')))
        if len(jahr) != 4 or not jahr.isdigit():
            raise RuntimeError('Abrechnungsjahr nicht eindeutig')
        mwst = erste['MwSt-Satz']
        zwischen = 'Abrechnung ab ZA' in erste
        datum = erste.get('Datum Zwischenablesung') if zwischen else None
        mwst_vorher = erste.get('ZA MwSt') if zwischen else None
        for zeile in gespeichert:
            if (str(zeile.get('Abrechnungsjahr', jahr)), zeile['MwSt-Satz'],
                    zeile.get('Datum Zwischenablesung'), zeile.get('ZA MwSt')) != (
                    jahr, mwst, erste.get('Datum Zwischenablesung'), erste.get('ZA MwSt')):
                raise RuntimeError('Uneinheitliche Parameter')

        meldungen = []
        PRUEFSCHRITT = 'Berechnungsumgebung'
        umgebung.update({
            'abnehmer_db': copy.deepcopy(abnehmer), 'zaehler_db': copy.deepcopy(zaehler),
            'abschlag_db': copy.deepcopy(abschlag), 'abrechnung': [],
            'arbeitspreis': float(betreiber['Betreiber']['Waermepreis']),
            'grundgebuehr': float(betreiber['Betreiber']['Grundgebuehr']),
            'jahre_dropdown': Anzeige(jahr), 'mwst_jahr': Anzeige(mwst),
            'za_switch': Anzeige(zwischen), 'za_datum': Anzeige(datum),
            'za_mwst': Anzeige(mwst_vorher),
            'abr_button_speichern': Anzeige(), 'abr_button_download': Anzeige(),
            'abrechnung_grid_ui': Anzeige(), 'label_umsatz': Anzeige(),
            'ui': SimpleNamespace(notify=lambda *args, **kwargs: meldungen.append(True)),
        })
        PRUEFSCHRITT = 'Originalberechnung'
        umgebung['abrechnung_erstellen_gui']()
        if meldungen or not umgebung['abrechnung']:
            raise RuntimeError('Berechnung nicht abgeschlossen')
        ergebnisse.append({'jahr': jahr, 'zwischenablesung': zwischen,
                           'ergebnis': umgebung['abrechnung']})
    if not ergebnisse:
        raise RuntimeError('Keine geeigneten Beispielabrechnungen')
    return ergebnisse


def main():
    # Änderung für v2: Fehler und Programmausgaben dürfen keine Beispieldaten offenlegen.
    if sys.argv[1:] not in (['erstellen'], ['pruefen']):
        print('Aufruf: python -m tests.referenz_pruefen erstellen | pruefen')
        return 2
    try:
        if sys.argv[1] == 'erstellen' and REFERENZ.exists():
            print('Nicht erstellt: Eine Referenz ist bereits vorhanden.')
            return 1
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            ergebnisse = ergebnisse_berechnen()
        if sys.argv[1] == 'erstellen':
            REFERENZ.parent.mkdir(exist_ok=True)
            inhalt = {
                'quellcode_sha256': hashlib.sha256((BASIS / 'anwendung' / 'oberflaeche.py').read_bytes()).hexdigest(),
                'ergebnisse': ergebnisse,
            }
            REFERENZ.write_text(json.dumps(inhalt, ensure_ascii=False, indent=2), encoding='utf-8')
            print('Referenz lokal erstellt. Dateninhalte werden nicht ausgegeben.')
        else:
            referenz = json.loads(REFERENZ.read_text(encoding='utf-8'))
            if referenz['ergebnisse'] != ergebnisse:
                print('Referenzprüfung: nicht bestanden.')
                return 1
            print('Referenzprüfung: bestanden.')
        return 0
    except Exception as fehler:
        # Änderung für v2: Nur den Fehlertyp melden, niemals datenhaltige Fehlermeldungen.
        print('Prüfung nicht abgeschlossen. Schritt: ' + PRUEFSCHRITT
              + '. Fehlertyp: ' + type(fehler).__name__)
        return 1


if __name__ == '__main__':
    sys.exit(main())
