"""Änderung 2.044: Ergebnisse, Mutationen und Fehler lokal gegen Original prüfen."""
import ast
import contextlib
import copy
import hashlib
import io
from pathlib import Path
from anwendung import datenaufbereitung
from anwendung.datenhaltung import datei_oeffnen
from anwendung.einstellungen import ini_datei_lesen


def pruefen():
    # Änderung: Original ohne GUI-Start laden; Beispieldaten bleiben ausschließlich lokal.
    basis = Path(__file__).resolve().parents[1]
    namen = {'string_in_dict', 'listcsv_to_dict', 'jahr_in_datum',
             'tablefields_to_dotfloat', 'tablefields_to_int'}
    baum = ast.parse((basis.parent / '_Vorlagen/ana/ana.py').read_text(encoding='utf-8-sig'))
    funktionen = [k for k in baum.body if isinstance(k, ast.FunctionDef) and k.name in namen]
    alt = {}
    exec(compile(ast.Module(body=funktionen, type_ignores=[]), 'original_aufbereitung', 'exec'), alt)
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen/ana Beispieldaten').resolve()
    bestand = {p: hashlib.sha256(p.read_bytes()).digest() for p in daten.rglob('*') if p.is_file()}

    def vergleichen(name, *args):
        # Änderung: Auch Eingabemutation, Rückgabeidentität und bisherige Fehler vergleichen.
        ergebnisse = []
        for funktion in (alt[name], getattr(datenaufbereitung, name)):
            eingaben = copy.deepcopy(args)
            try:
                wert = funktion(*eingaben)
                ergebnis = (wert, None, wert is eingaben[0])
            except Exception as fehler:
                ergebnis = (None, (type(fehler), str(fehler)), False)
            ergebnisse.append((ergebnis, eingaben))
        assert ergebnisse[0] == ergebnisse[1]

    for datei in (daten / 'Datenbank').glob('*.csv'):
        tabelle = datei_oeffnen(datei)
        for name in ('tablefields_to_dotfloat', 'tablefields_to_int'):
            vergleichen(name, tabelle)
        if tabelle:
            for suchwert in ('Ident', 'Name', 'nicht_vorhanden'):
                vergleichen('string_in_dict', tabelle[0], suchwert)
        vergleichen('listcsv_to_dict', datei.read_text().splitlines())
    # Änderung: Sonderwerte und unpassende Eingaben mit bisherigen Seiteneffekten erhalten.
    for tabelle in ([], [{}], [{'Ident': '001', 'Name': 'Lokal', 'Vorname': 'Test',
                              'Kommentar': '1,2', 'Datum': '01.01.2026', 'datum': '2026-01-01',
                              'a': None, 'b': '', 'c': '1,25', 'd': '1.234,56', 'e': '-2',
                              'f': '12', 'g': 'abc', 'h': 1.5}]):
        for name in ('tablefields_to_dotfloat', 'tablefields_to_int'):
            vergleichen(name, tabelle)
    for eingabe in ([], ['A;B;'], ['A;B;', '1;2;'], ['A;B;', '1;'], ['A;B', '1;2']):
        vergleichen('listcsv_to_dict', eingabe)
    for datum in ('08.11.2026', '2026-11-08', '', 'ungültig', None):
        vergleichen('jahr_in_datum', datum)
    for obj in ({}, {'Ident': 1}, {'MeineIdentSpalte': 2}, {1: 'wert'}):
        vergleichen('string_in_dict', obj, 'Ident')
    assert bestand == {p: hashlib.sha256(p.read_bytes()).digest() for p in daten.rglob('*') if p.is_file()}


if __name__ == '__main__':
    try:
        # Änderung: Datenhaltige Fehlerdetails ausschließlich lokal halten.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Datenaufbereitung: Ergebnisse, Mutationen und Fehler gegen Original bestanden.')
    except Exception as fehler:
        print('Datenaufbereitung nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)
