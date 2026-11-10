"""Änderung 2.047: Namenaktualisierung und Speicher-/Ladereihenfolge nur lokal vergleichen."""
import ast
import contextlib
import copy
import io
from itertools import product
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from anwendung.datenhaltung import DatenbankZugriff, datei_oeffnen, dictlist_to_csv, check_ordner_exists
from anwendung.einstellungen import ini_datei_lesen
from tests.datenbank_pruefen import bestand


# Änderung: Fachvergleich isoliert Zusatzprotokoll; echte Protokolle separat prüfen.
@patch('anwendung.aenderungsprotokoll.protokolliere', lambda *args: None)
def pruefen():
    basis = Path(__file__).resolve().parents[1]
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen/ana Beispieldaten').resolve()
    vorher = bestand(daten)
    baum = ast.parse((basis.parent / '_Vorlagen/ana/ana.py').read_text(encoding='utf-8-sig'))
    original = next(n for n in baum.body if isinstance(n, ast.FunctionDef) and n.name == 'dbs_mitglieder_aktualisieren')
    alt = {}
    exec(compile(ast.Module(body=[original], type_ignores=[]), 'original_mitgliederaktualisierung', 'exec'), alt)
    haupt = ast.parse((basis / 'anwendung/oberflaeche.py').read_text(encoding='utf-8'))
    adapter = next(n for n in haupt.body if isinstance(n, ast.FunctionDef) and n.name == original.name)
    app = SimpleNamespace(dictlist_to_csv=dictlist_to_csv, check_ordner_exists=check_ordner_exists)
    hilfe = DatenbankZugriff(app)
    neu = {'datenhaltung_hilfe': hilfe}
    exec(compile(ast.Module(body=[adapter], type_ignores=[]), 'adapter_mitgliederaktualisierung', 'exec'), neu)
    namen = ('abnehmer', 'zaehler', 'abschlag', 'konto')
    dateien = ('db_abnehmer.csv', 'db_zaehler.csv', 'db_abschlag.csv', 'db_kontodaten.csv')
    beispiele = {name + '_db': datei_oeffnen(daten / 'Datenbank' / datei) for name, datei in zip(namen, dateien)}
    beispiele['mitglieder_db'] = datei_oeffnen(daten / 'Datenbank/db_mitglieder.csv')
    assert beispiele['mitglieder_db']
    # Änderung: Doppelte Identen, Typunterschiede und fehlende Treffer unverändert behandeln.
    sonderfall = {name + '_db': [{'Ident': 'x', 'Name': 'alt', 'Vorname': 'alt'},
                                {'Ident': 'fehlt', 'Name': 'bleibt', 'Vorname': 'bleibt'},
                                {'Ident': 1, 'Name': 'alt', 'Vorname': 'alt'}] for name in namen}
    sonderfall['mitglieder_db'] = [{'Ident': 'x', 'Name': 'erster', 'Vorname': 'A'},
                                  {'Ident': 'x', 'Name': 'letzter', 'Vorname': 'B'},
                                  {'Ident': '1', 'Name': 'Text', 'Vorname': 'C'}]
    leer = {name: [] for name in beispiele}
    def run(eingabe, flags, ziel, umgebung, aktualisieren, fehler=None, laden_aendert=False):
        # Änderung: Echte CSV-Schreibzugriffe ausschließlich in temporären Datenordnern ausführen.
        umgebung.update(copy.deepcopy(eingabe))
        umgebung.update({name: str(ziel / ordner) for name, ordner in (
            ('ordner_abrechnungen', 'Abrechnungen'), ('ordner_rueckv', 'Rueckverguetung'),
            ('ordner_logs', 'Logs'), ('ordner_datenbank', 'Datenbank'),
            ('ordner_sicherungen', 'Sicherungen'), ('ordner_downloads', 'Downloads'))})
        protokoll = []
        referenzen = [umgebung[n + '_db'] for n in namen]
        schreiber = DatenbankZugriff(SimpleNamespace(**umgebung, dictlist_to_csv=dictlist_to_csv,
                                                   check_ordner_exists=check_ordner_exists))
        def schreiben(datei, tabelle):
            protokoll.append(('speichern', datei, copy.deepcopy(tabelle)))
            if fehler == ('speichern', datei):
                raise OSError('Lokaler Testfehler')
            schreiber.db_datei_speichern(datei, tabelle)
        umgebung['db_datei_speichern'] = schreiben
        for name, datei, flag in zip(namen, dateien, flags):
            umgebung['db_' + name] = datei
            umgebung['db_' + name + '_found'] = flag
            def laden(name=name, datei=datei):
                protokoll.append(('laden', datei))
                if fehler == ('laden', datei):
                    raise OSError('Lokaler Testfehler')
                umgebung[name + '_db'] = schreiber.db_datei_oeffnen(datei)
                if laden_aendert:
                    # Änderung: Spätere Bereiche müssen aktuelle, beim Laden geänderte Mitglieder lesen.
                    umgebung['mitglieder_db'] = list(reversed(umgebung['mitglieder_db']))
            umgebung[name + '_aus_db'] = laden
        ausnahme = None
        try:
            rueckgabe = aktualisieren()
            assert rueckgabe is None
        except Exception as exc:
            ausnahme = type(exc)
        return (ausnahme, protokoll, {n: umgebung[n] for n in eingabe}, referenzen,
                [umgebung[n + '_db'] is ref for n, ref in zip(namen, referenzen)], bestand(ziel))

    # Änderung: Alle Kombinationen der vier Dateistatuswerte und erneute Aufrufe derselben Hilfe prüfen.
    with tempfile.TemporaryDirectory(dir=basis / '.lokal') as tmp:
        faelle = [(datenfall, flags, None, False) for datenfall in (beispiele, sonderfall, leer)
                  for flags in product((0, 1), repeat=4)]
        faelle += [(sonderfall, (1, 1, 1, 1), (aktion, datei), False)
                   for aktion in ('speichern', 'laden') for datei in dateien]
        faelle += [(sonderfall, (1, 1, 1, 1), None, True)]
        kaputt = copy.deepcopy(sonderfall)
        kaputt['zaehler_db'][0].pop('Ident')
        faelle += [(kaputt, (1, 1, 1, 1), None, False)]
        for index, (eingabe, flags, fehler, laden_aendert) in enumerate(faelle):
            ergebnisse = []
            for seite, umgebung, aktualisieren in (('alt', alt, alt[original.name]),
                                                   ('neu', vars(app), neu[original.name])):
                ziel = Path(tmp) / (str(index) + seite)
                ziel.mkdir()
                # Änderung: Nur Datenwerte überschreiben, die gemeinsame Hilfsinstanz bleibt bestehen.
                for key in ('dictlist_to_csv', 'check_ordner_exists'):
                    umgebung.pop(key, None)
                ergebnisse.append(run(eingabe, flags, ziel, umgebung, aktualisieren, fehler, laden_aendert))
            assert ergebnisse[0] == ergebnisse[1]
            if eingabe is sonderfall and flags == (1, 1, 1, 1) and fehler is None and not laden_aendert:
                assert ergebnisse[0][2]['abnehmer_db'][0]['Name'] == 'letzter'
                assert ergebnisse[0][2]['abnehmer_db'][1]['Name'] == 'bleibt'
    assert bestand(daten) == vorher


if __name__ == '__main__':
    try:
        # Änderung: Beispieldaten und mögliche Fehlerdetails bleiben ausschließlich lokal.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Mitgliederaktualisierung: Daten, CSV, Reihenfolge, Neuladen und Fehler gegen Original bestanden.')
    except Exception as fehler:
        print('Mitgliederaktualisierung nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)
