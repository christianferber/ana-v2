"""Änderung: Abschlagsansicht mit lokalen Beispieldaten gegen Original prüfen."""
import ast
import contextlib
import copy
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

from anwendung.abschlag_ui import AbschlagOberflaeche
from anwendung.datenhaltung import datei_oeffnen, datei_speichern, import_csv_inhalt
from anwendung.einstellungen import ini_datei_lesen


# Änderung: Fachvergleich isoliert Zusatzprotokoll; echte Protokolle separat prüfen.
@patch('anwendung.aenderungsprotokoll.protokolliere', lambda *args: None)
def pruefen():
    basis = Path(__file__).resolve().parents[1]
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
    quelle = daten / 'Datenbank' / 'db_abschlag.csv'
    originalbytes = quelle.read_bytes()
    zeilen = datei_oeffnen(quelle)
    assert zeilen
    baum = ast.parse((basis.parent / '_Vorlagen' / 'ana' / 'ana.py').read_text(encoding='utf-8-sig'))
    namen = {'abschlag_columns_erstellen', 'abschlag_tabelle_on_change', 'abschlag_speichern', 'abschlag_upload', 'string_in_dict'}
    funktionen = [n for n in baum.body if isinstance(n, ast.FunctionDef) and n.name in namen]
    ui = Mock()
    alt = dict(ui=ui, events=SimpleNamespace(UploadEventArguments=object), StringIO=io.StringIO,
               import_csv_inhalt=import_csv_inhalt, abschlag_db=copy.deepcopy(zeilen),
               abschlag_button_speichern=Mock(), abschlag_grid_ui=Mock(),
               change_log=Mock(), db_sichern=Mock(), col_cell_mod='test', db_abschlag='db_abschlag.csv')
    exec(compile(ast.Module(body=funktionen, type_ignores=[]), 'original_abschlag', 'exec'), alt)
    app = SimpleNamespace(abschlag_db=copy.deepcopy(zeilen), col_cell_mod='test',
                          change_log=Mock(), db_sichern=Mock(), abschlag_grid_ui=Mock(),
                          string_in_dict=alt['string_in_dict'], db_abschlag='db_abschlag.csv')
    ansicht = AbschlagOberflaeche(app)
    ansicht.abschlag_button_speichern = Mock()
    with patch('anwendung.abschlag_ui.ui', ui):
        # Änderung: Spaltendefinitionen und Bearbeiten auf denselben echten Daten vergleichen.
        assert ansicht.abschlag_columns_erstellen(app.abschlag_db) == alt['abschlag_columns_erstellen'](alt['abschlag_db'])
        spalte = next(k for k in zeilen[0] if 'Abschlag-' in k)
        for wert in (None, 123.45):
            event = dict(newValue=wert, rowId='0', colId=spalte)
            alt['abschlag_tabelle_on_change'](event)
            ansicht.abschlag_tabelle_on_change(event)
            assert app.abschlag_db == alt['abschlag_db']
        assert app.change_log.call_args_list == alt['change_log'].call_args_list
        # Änderung: CSV-Speicherung ausschließlich in zwei lokalen Testdateien vergleichen.
        with tempfile.TemporaryDirectory(dir=basis / '.lokal') as tmp:
            alt['db_datei_speichern'] = lambda name, rows: datei_speichern(Path(tmp) / 'alt.csv', rows)
            app.db_datei_speichern = lambda name, rows: datei_speichern(Path(tmp) / 'neu.csv', rows)
            alt['abschlag_speichern']()
            ansicht.abschlag_speichern()
            assert (Path(tmp) / 'alt.csv').read_bytes() == (Path(tmp) / 'neu.csv').read_bytes()
        # Änderung: Erfolgreichen Upload und Formatabweisung mit identischen Eingaben prüfen.
        for inhalt in (originalbytes, b'Falsche-Spalte;Wert\n1;2\n'):
            alt['abschlag_upload'](SimpleNamespace(content=io.BytesIO(inhalt)))
            ansicht.abschlag_upload(SimpleNamespace(content=io.BytesIO(inhalt)))
            assert app.abschlag_db == alt['abschlag_db']
        assert app.db_sichern.call_args_list == alt['db_sichern'].call_args_list
        assert ansicht.abschlag_button_speichern.method_calls == alt['abschlag_button_speichern'].method_calls
    assert quelle.read_bytes() == originalbytes


if __name__ == '__main__':
    try:
        # Änderung: Keine Beispieldaten oder Tracebacks in Werkzeugausgaben ausgeben.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Abschlagsansicht: Spalten, Bearbeiten, Speichern und Upload gegen Original bestanden.')
    except Exception as fehler:
        print('Abschlagsprüfung nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)
