"""Änderung 2.046: CSV-Speicherung ausschließlich mit lokalen Beispieldaten prüfen."""
import ast
import asyncio
import contextlib
import copy
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from anwendung.exporthilfe import ExportHilfe
from anwendung.datenhaltung import datei_oeffnen, dictlist_to_csv
from anwendung.einstellungen import ini_datei_lesen
from tests.datenbank_pruefen import bestand


def pruefen():
    basis = Path(__file__).resolve().parents[1]
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen/ana Beispieldaten').resolve()
    vorher = bestand(daten)
    original = ast.parse((basis.parent / '_Vorlagen/ana/ana.py').read_text(encoding='utf-8-sig'))
    alt = next(n for n in original.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'komma_datei_speichern')
    haupt = ast.parse((basis / 'anwendung/oberflaeche.py').read_text(encoding='utf-8'))
    modul = ast.parse((basis / 'anwendung/exporthilfe.py').read_text(encoding='utf-8'))
    klasse = next(n for n in modul.body if isinstance(n, ast.ClassDef))
    neu = next(n for n in klasse.body if isinstance(n, ast.AsyncFunctionDef))

    # Änderung: Vollständigen Funktionskörper nach Rückführung der Anwendungszugriffe vergleichen.
    class Zugriffe(ast.NodeTransformer):
        def visit_Attribute(self, n):
            if (isinstance(n.value, ast.Attribute) and n.value.attr == 'anwendung'
                    and isinstance(n.value.value, ast.Name) and n.value.value.id == 'self'):
                return ast.copy_location(ast.Name(id=n.attr, ctx=n.ctx), n)
            return self.generic_visit(n)

    vergleich = Zugriffe().visit(copy.deepcopy(neu))
    assert vergleich.args.args.pop(0).arg == 'self'
    assert ast.dump(vergleich) == ast.dump(alt)
    adapter = next(n for n in haupt.body if isinstance(n, ast.AsyncFunctionDef) and n.name == alt.name)
    erwartet = copy.deepcopy(alt)
    erwartet.body = ast.parse('async def f():\n    return await exporthilfe.komma_datei_speichern(dictlist, dateiname)').body[0].body
    assert ast.dump(adapter) == ast.dump(erwartet)
    assert any(isinstance(n, ast.ImportFrom) and n.module == 'anwendung.exporthilfe'
               and [(a.name, a.asname) for a in n.names] == [('ExportHilfe', None)] for n in haupt.body)
    initialisierung = ast.parse('exporthilfe = ExportHilfe(sys.modules[__name__])').body[0]
    assert any(ast.dump(n) == ast.dump(initialisierung) for n in haupt.body)

    # Änderung: Echte Beispieldaten ergänzen Grenzfälle der bisherigen Punktumwandlung.
    faelle = [datei_oeffnen(p) for p in (daten / 'Datenbank').glob('*.csv')]
    faelle += [[{'Zahl': 12.34, 'Text': 'a.b', 'Mehrere': 'a.b.c', 'Leer': '',
                 'Null': None, 'Ganzzahl': 12, 'Komma': '1,23', 'Zeilen': 'a;\nb'}], []]
    app = SimpleNamespace(dictlist_to_csv=dictlist_to_csv)
    hilfe = ExportHilfe(app)
    umgebung = {}
    exec(compile(ast.Module(body=[alt], type_ignores=[]), 'original_csv_speicherung', 'exec'), umgebung)

    async def vergleichen():
        with tempfile.TemporaryDirectory(dir=basis / '.lokal') as tmp:
            ziel = Path(tmp) / 'vergleich.csv'
            for tabelle in faelle:
                # Änderung: Speichern, Abbruch, falscher Zieltyp und Dialogfehler gleich behandeln.
                for modus in ('speichern', 'abbruch', 'ordner', 'dialogfehler'):
                    ergebnisse = []
                    for speichern in (umgebung['komma_datei_speichern'], hilfe.komma_datei_speichern):
                        if ziel.exists():
                            ziel.unlink()
                        rueckgabe = {'speichern': str(ziel), 'abbruch': None,
                                     'ordner': tmp, 'dialogfehler': None}[modus]
                        dialog = AsyncMock(return_value=rueckgabe)
                        if modus == 'dialogfehler':
                            dialog.side_effect = RuntimeError('Lokaler Testfehler')
                        werte = dict(dictlist_to_csv=Mock(wraps=dictlist_to_csv), ui=Mock(),
                                     app=SimpleNamespace(native=SimpleNamespace(main_window=SimpleNamespace(create_file_dialog=dialog))),
                                     webview=SimpleNamespace(SAVE_DIALOG=30))
                        umgebung.update(werte)
                        vars(app).update(werte)
                        eingabe = copy.deepcopy(tabelle)
                        try:
                            ergebnis = await speichern(eingabe, 'vorgabe.csv')
                            fehler = None
                        except Exception as exc:
                            ergebnis, fehler = None, type(exc)
                        assert eingabe == tabelle
                        ergebnisse.append((ergebnis, fehler, ziel.read_bytes() if ziel.exists() else None,
                                           dialog.call_args_list, werte['ui'].notify.call_args_list,
                                           werte['dictlist_to_csv'].call_args_list))
                    assert ergebnisse[0] == ergebnisse[1]
                    if tabelle:
                        assert ergebnisse[0][3] == [((30,), dict(directory='%USERPROFILE\\Downloads', allow_multiple=False, save_filename='vorgabe.csv'))]
    asyncio.run(vergleichen())
    assert bestand(daten) == vorher


if __name__ == '__main__':
    try:
        # Änderung: Dateninhalte und Fehlerdetails bleiben außerhalb der Werkzeugausgabe.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('CSV-Speicherhilfe: Struktur, Dateiinhalte, Dialoge, Abbruch und Fehler bestanden.')
    except Exception as fehler:
        print('CSV-Speicherprüfung nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)
