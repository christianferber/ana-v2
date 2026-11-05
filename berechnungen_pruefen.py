"""Änderung für v2: Alten und neuen Abrechnungsablauf ausschließlich lokal vergleichen."""

import ast
import contextlib
import copy
from datetime import datetime, timedelta
import io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import referenz_pruefen


def pruefen():
    # Änderung für v2: Alte Funktionen aus der unveränderten Vorlage ohne Programmstart laden.
    basis = Path(__file__).resolve().parent
    original = basis.parent / '_Vorlagen' / 'ana' / 'ana.py'
    baum = ast.parse(original.read_text(encoding='utf-8-sig'))
    namen = {'tablefields_to_int', 'tablefields_to_dotfloat', 'abnehmer_aus_daten',
             'mwst_berechnen', 'datum_in_string', 'datum_in_punkt', 'datum_tage_vorher',
             'letzte_mindestabnahme', 'abrechnung_erstellen_gui', 'umsatz_berechnen'}
    funktionen = [k for k in baum.body if isinstance(k, ast.FunctionDef) and k.name in namen]
    assert {k.name for k in funktionen} == namen
    alt = {'datetime': datetime, 'timedelta': timedelta}
    exec(compile(ast.Module(body=funktionen, type_ignores=[]), 'original_berechnung', 'exec'), alt)
    neu = referenz_pruefen.funktionen_laden()

    # Änderung für v2: Alle vorhandenen Beispielfälle mit beiden Implementierungen berechnen.
    ergebnisse = []
    for umgebung in (alt, neu):
        with patch.object(referenz_pruefen, 'funktionen_laden', return_value=umgebung):
            ergebnisse.append(referenz_pruefen.ergebnisse_berechnen())
    assert ergebnisse[0] == ergebnisse[1]

    # Änderung für v2: Abbruchbedingungen anhand lokaler Kopien vorhandener Eingaben prüfen.
    for fall in ('jahr_fehlt', 'steuersatz_fehlt', 'zaehler_ungueltig'):
        protokolle = []
        for umgebung in (alt, neu):
            sicherung = {name: copy.deepcopy(umgebung[name]) for name in (
                'zaehler_db', 'abrechnung', 'jahre_dropdown', 'mwst_jahr')}
            vorher = copy.deepcopy(umgebung['abrechnung'])
            protokoll = []
            umgebung['ui'] = SimpleNamespace(notify=lambda *args, **kwargs: protokoll.append((args, kwargs)))
            if fall == 'jahr_fehlt':
                umgebung['jahre_dropdown'].value = None
            elif fall == 'steuersatz_fehlt':
                umgebung['mwst_jahr'].value = None
            else:
                # Bestehende Daten nur im Arbeitsspeicher als ungültig markieren.
                umgebung['zaehler_db'] = copy.deepcopy(umgebung['zaehler_db'])
                umgebung['zaehler_db'][0]['Pruefwert'] = '-1'
            umgebung['abrechnung_erstellen_gui']()
            assert umgebung['abrechnung'] == vorher
            assert len(protokoll) == 1
            protokolle.append(protokoll)
            umgebung.update(sicherung)
        assert protokolle[0] == protokolle[1]


if __name__ == '__main__':
    try:
        # Änderung für v2: Dateninhalte und datenhaltige Fehler bleiben aus den Ausgaben ausgeschlossen.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Berechnungsvergleich und Abbruchbedingungen: bestanden.')
    except Exception as fehler:
        print('Berechnungsprüfung nicht abgeschlossen. Fehlertyp: ' + type(fehler).__name__)
        raise SystemExit(1)
