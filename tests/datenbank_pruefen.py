"""Änderung 2.045: Datenbankzugriffe mit lokalen Kopien gegen Original vergleichen."""
import ast
import contextlib
import copy
import csv
import hashlib
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace

from anwendung.datenhaltung import DatenbankZugriff, check_ordner_exists, dictlist_to_csv
from anwendung.einstellungen import ini_datei_lesen


def bestand(ordner):
    # Änderung: Nur Prüfsummen im Arbeitsspeicher halten; keine Dateninhalte ausgeben.
    return {str(p.relative_to(ordner)): None if p.is_dir() else hashlib.sha256(p.read_bytes()).digest()
            for p in ordner.rglob('*')}


def pruefen():
    basis = Path(__file__).resolve().parents[1]
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen/ana Beispieldaten').resolve()
    originalbestand = bestand(daten)
    baum = ast.parse((basis.parent / '_Vorlagen/ana/ana.py').read_text(encoding='utf-8-sig'))
    namen = {'db_datei_oeffnen', 'db_datei_speichern'}
    funktionen = [k for k in baum.body if isinstance(k, ast.FunctionDef) and k.name in namen]
    alt = dict(Path=Path, csv=csv, dictlist_to_csv=dictlist_to_csv)
    exec(compile(ast.Module(body=funktionen, type_ignores=[]), 'original_datenbank', 'exec'), alt)
    app = SimpleNamespace(dictlist_to_csv=dictlist_to_csv)
    hilfe = DatenbankZugriff(app)
    ordnernamen = ('Abrechnungen', 'Rueckverguetung', 'Logs', 'Datenbank', 'Sicherungen', 'Downloads')
    pfadnamen = ('ordner_abrechnungen', 'ordner_rueckv', 'ordner_logs', 'ordner_datenbank',
                 'ordner_sicherungen', 'ordner_downloads')
    with tempfile.TemporaryDirectory(dir=basis / '.lokal') as tmp:
        # Änderung: Dieselbe Hilfsinstanz muss auch nach einem Arbeitsordnerwechsel funktionieren.
        for wechsel in range(2):
            links, rechts = [Path(tmp) / (str(wechsel) + seite) for seite in ('alt', 'neu')]
            for ziel, umgebung in ((links, alt), (rechts, vars(app))):
                ziel.mkdir()
                for name, ordner in zip(pfadnamen, ordnernamen):
                    umgebung[name] = str(ziel / ordner)
            assert alt['db_datei_oeffnen']('fehlt.csv') == hilfe.db_datei_oeffnen('fehlt.csv') == ['file not found']
            # Änderung: Tatsächliche Ordneranlage samt Reihenfolge mitprotokollieren.
            protokolle = [[], []]
            for index, (ziel, umgebung) in enumerate(((links, alt), (rechts, vars(app)))):
                def anlegen(pfad, index=index, ziel=ziel):
                    protokolle[index].append(str(Path(pfad).relative_to(ziel)))
                    check_ordner_exists(pfad)
                umgebung['check_ordner_exists'] = anlegen
            for datei in (daten / 'Datenbank').glob('*.csv'):
                from anwendung.datenhaltung import datei_oeffnen
                tabelle = datei_oeffnen(datei)
                if not tabelle:
                    continue
                a, b = copy.deepcopy(tabelle), copy.deepcopy(tabelle)
                alt['db_datei_speichern']('vergleich.csv', a)
                hilfe.db_datei_speichern('vergleich.csv', b)
                assert a == b
                assert bestand(links) == bestand(rechts)
                assert alt['db_datei_oeffnen']('vergleich.csv') == hilfe.db_datei_oeffnen('vergleich.csv')
            assert protokolle[0] == protokolle[1]
            assert protokolle[0][:6] == list(ordnernamen)
            # Änderung: Leere Datei, leere Tabelle und falscher Zieltyp behalten ihr Fehlerverhalten.
            for ziel in (links, rechts):
                (ziel / 'Datenbank/leer.csv').write_bytes(b'')
                (ziel / 'Datenbank/ordner.csv').mkdir()
            assert alt['db_datei_oeffnen']('leer.csv') == hilfe.db_datei_oeffnen('leer.csv') == []
            for dateiname, tabelle in (('vergleich.csv', []), ('ordner.csv', [{'a': 'b'}])):
                fehler = []
                for speichern in (alt['db_datei_speichern'], hilfe.db_datei_speichern):
                    try:
                        speichern(dateiname, copy.deepcopy(tabelle))
                        fehler.append(None)
                    except Exception as exc:
                        fehler.append(type(exc))
                assert fehler[0] == fehler[1] and fehler[0] is not None
                assert bestand(links) == bestand(rechts)
    assert bestand(daten) == originalbestand


if __name__ == '__main__':
    try:
        # Änderung: Datenhaltige Fehlerdetails ausschließlich lokal halten.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Datenbankzugriffe: Lesen, Schreiben, Ordnerfolge, Pfadwechsel und Fehler bestanden.')
    except Exception as fehler:
        print('Datenbankprüfung nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)
