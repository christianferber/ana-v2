# Änderung für v2: In tests/ eingeordnet; Modul- und Dateipfade angepasst.
"""Änderung für v2: Rückvergütungen lokal sichern und mit der Vorlage vergleichen.

Beispieldaten werden nur gelesen. Ergebnisse bleiben unter .lokal; Ausgaben
enthalten ausschließlich feste Statusmeldungen und keine Dateninhalte.
"""

import ast
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace

from anwendung.datenhaltung import datei_oeffnen
from anwendung.einstellungen import ini_datei_lesen

BASIS = Path(__file__).resolve().parents[1]
REFERENZ = BASIS / '.lokal' / 'rueckverguetungsreferenz.json'


class Knopf:
    # Änderung für v2: Oberflächenaufrufe lokal protokollieren, ohne GUI zu starten.
    def __init__(self):
        self.aktiv = False

    def enable(self):
        self.aktiv = True


def funktionen_laden(original):
    # Änderung 2.02: Neue Referenzprüfung führt die tatsächlichen gebundenen
    # Methoden aus; der alte Referenzcode bleibt als unabhängiger Vergleich bestehen.
    if not original:
        from anwendung.rueckverguetung_ui import RueckverguetungOberflaeche
        ansicht = RueckverguetungOberflaeche(SimpleNamespace())
        return {'ansicht': ansicht,
                'rueckv_tabelle_erstellen': ansicht.rueckv_tabelle_erstellen,
                'rueckv_tabelle_berechnen': ansicht.rueckv_tabelle_berechnen}
    # Änderung 2.02: Nach dem frühen Rücksprung nur noch den Originalcode laden.
    quelle = BASIS.parent / '_Vorlagen' / 'ana' / 'ana.py'
    baum = ast.parse(quelle.read_text(encoding='utf-8-sig'))
    namen = {'rueckv_tabelle_erstellen', 'rueckv_tabelle_berechnen', 'rueckv_erstellen'}
    namen.add('mwst_berechnen')
    funktionen = [k for k in baum.body if isinstance(k, ast.FunctionDef) and k.name in namen]
    assert {k.name for k in funktionen} == namen
    umgebung = {'datei_oeffnen': datei_oeffnen}
    exec(compile(ast.Module(body=funktionen, type_ignores=[]), 'rueckverguetung', 'exec'), umgebung)
    return umgebung


def ergebnisse(original):
    daten = Path(ini_datei_lesen(BASIS / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (BASIS.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
    umgebung = funktionen_laden(original)
    faelle = []
    for datei in sorted((daten / 'Rückvergütungen').glob('Rückvergütung-*/Rückvergütung-*.csv')):
        gespeichert = datei_oeffnen(datei)
        if not gespeichert:
            continue
        jahr = datei.parent.name.removeprefix('Rückvergütung-')
        satz = gespeichert[0]['Rückvergütungssatz']
        datum = gespeichert[0]['Datum Beschluss']
        assert all(row['Rückvergütungssatz'] == satz and row['Datum Beschluss'] == datum
                   for row in gespeichert)
        umgebung.update({
            'ordner_abrechnungen': str(daten / 'Abrechnungen'),
            'rueckv_jahre_dropdown': SimpleNamespace(value=jahr),
            'rueckv_prozent': SimpleNamespace(value=satz),
            'rueckv_datum_beschluss': SimpleNamespace(value=datum),
            'rueckv_button_speichern': Knopf(), 'rueckv_button_download': Knopf(),
        })
        # Änderung 2.02: Referenzwerte auf die Instanz statt globale Variablen setzen.
        if not original:
            ansicht = umgebung['ansicht']
            ansicht.anwendung.ordner_abrechnungen = umgebung['ordner_abrechnungen']
            for name in ('rueckv_jahre_dropdown', 'rueckv_prozent', 'rueckv_datum_beschluss',
                         'rueckv_button_speichern', 'rueckv_button_download'):
                setattr(ansicht, name, umgebung[name])
        tabelle = umgebung['rueckv_tabelle_erstellen']()
        assert umgebung['rueckv_button_speichern'].aktiv and umgebung['rueckv_button_download'].aktiv
        # Änderung für v2: Neuberechnung bestehender Tabellen inklusive Materialumsatz prüfen.
        neu_berechnet = umgebung['rueckv_tabelle_berechnen'](copy.deepcopy(gespeichert))
        faelle.append({'jahr': jahr, 'satz': satz, 'datum': datum,
                      'ergebnis': tabelle, 'neuberechnet': neu_berechnet})
        # Änderung für v2: Kein Jahr und leere Tabellen behalten das bisherige Verhalten.
        umgebung['rueckv_jahre_dropdown'].value = None
        assert umgebung['rueckv_tabelle_erstellen']() is None
        assert umgebung['rueckv_tabelle_berechnen']([]) == []
    assert faelle
    return faelle


def main():
    if sys.argv[1:] not in (['erstellen'], ['pruefen']):
        print('Aufruf: python -m tests.rueckverguetung_pruefen erstellen | pruefen')
        return 2
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            vorher = ergebnisse(True)
            if sys.argv[1] == 'erstellen':
                assert not REFERENZ.exists()
                REFERENZ.parent.mkdir(exist_ok=True)
                REFERENZ.write_text(json.dumps(vorher, ensure_ascii=False, indent=2), encoding='utf-8')
            else:
                nachher = ergebnisse(False)
                assert nachher == vorher == json.loads(REFERENZ.read_text(encoding='utf-8'))
        print('Rückvergütungsreferenz lokal erstellt.' if sys.argv[1] == 'erstellen'
              else 'Rückvergütung: Referenzvergleich und Neuberechnung bestanden.')
        return 0
    except Exception as fehler:
        print('Rückvergütungsprüfung nicht abgeschlossen. Fehlertyp: ' + type(fehler).__name__)
        return 1


if __name__ == '__main__':
    sys.exit(main())
