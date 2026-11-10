"""Änderung: Abnehmeransicht mit lokalen Beispieldaten gegen Original prüfen."""
import ast
import contextlib
import copy
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

from anwendung.abnehmer_ui import AbnehmerOberflaeche
from anwendung.datenhaltung import datei_oeffnen, datei_speichern, import_csv_inhalt
from anwendung.einstellungen import ini_datei_lesen


# Änderung: Fachvergleich isoliert Zusatzprotokoll; echte Protokolle separat prüfen.
@patch('anwendung.aenderungsprotokoll.protokolliere', lambda *args: None)
def pruefen():
    basis = Path(__file__).resolve().parents[1]
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
    quelle = daten / 'Datenbank' / 'db_abnehmer.csv'
    originalbytes = quelle.read_bytes()
    zeilen = datei_oeffnen(quelle)
    assert zeilen
    # Änderung 2.034: Gemeinsame Abschlagsdaten und Mitgliederdaten lokal bereitstellen.
    mitglieder = datei_oeffnen(daten / 'Datenbank' / 'db_mitglieder.csv')
    abschlaege = datei_oeffnen(daten / 'Datenbank' / 'db_abschlag.csv')
    baum = ast.parse((basis.parent / '_Vorlagen' / 'ana' / 'ana.py').read_text(encoding='utf-8-sig'))
    namen = {'abnehmer_columns_erstellen', 'abnehmer_tabelle_on_change', 'abnehmerdaten_speichern', 'abnehmer_upload', 'string_in_dict'}
    funktionen = [n for n in baum.body if isinstance(n, ast.FunctionDef) and n.name in namen]
    ui = Mock()
    alt = dict(ui=ui, events=SimpleNamespace(UploadEventArguments=object), StringIO=io.StringIO,
               import_csv_inhalt=import_csv_inhalt, abnehmer_db=copy.deepcopy(zeilen),
               button_abnehmer_speichern=Mock(), abnehmer_grid_ui=Mock(),
               change_log=Mock(), db_sichern=Mock(), col_cell_mod='test', db_abnehmer='db_abnehmer.csv')
    exec(compile(ast.Module(body=funktionen, type_ignores=[]), 'original_abnehmer', 'exec'), alt)
    app = SimpleNamespace(abnehmer_db=copy.deepcopy(zeilen), col_cell_mod='test',
                          change_log=Mock(), db_sichern=Mock(), abnehmer_grid_ui=Mock(),
                          string_in_dict=alt['string_in_dict'], db_abnehmer='db_abnehmer.csv')
    alt.update(mitglieder_db=copy.deepcopy(mitglieder), abschlag_db=copy.deepcopy(abschlaege), arbeitspreis=12.34, abschlag_speichern=Mock(), abschlag_grid_ui=Mock(), change_log_info=Mock())
    for name in ('mitglieder_db', 'abschlag_db', 'arbeitspreis', 'abschlag_speichern', 'abschlag_grid_ui', 'change_log_info'):
        setattr(app, name, copy.deepcopy(alt[name]))
    ansicht = AbnehmerOberflaeche(app)
    ansicht.button_abnehmer_speichern = Mock()
    with patch('anwendung.abnehmer_ui.ui', ui):
        # Änderung: Spaltendefinitionen und Bearbeiten auf denselben echten Daten vergleichen.
        assert ansicht.abnehmer_columns_erstellen(app.abnehmer_db) == alt['abnehmer_columns_erstellen'](alt['abnehmer_db'])
        spalte = next(k for k in zeilen[0] if 'Mindest-' in k and 'Abschlag-' + k[-4:] in abschlaege[0])
        for wert in (None, 0, 12345):
            event = dict(newValue=wert, rowId='0', colId=spalte, data={k: str(v) for k,v in zeilen[0].items()})
            alt['abnehmer_tabelle_on_change'](event)
            ansicht.abnehmer_tabelle_on_change(event)
            assert app.abnehmer_db == alt['abnehmer_db']
            assert app.abschlag_db == alt['abschlag_db']
        assert app.change_log.call_args_list == alt['change_log'].call_args_list
        # Änderung: CSV-Speicherung ausschließlich in zwei lokalen Testdateien vergleichen.
        with tempfile.TemporaryDirectory(dir=basis / '.lokal') as tmp:
            alt['db_datei_speichern'] = lambda name, rows: datei_speichern(Path(tmp) / 'alt.csv', rows)
            app.db_datei_speichern = lambda name, rows: datei_speichern(Path(tmp) / 'neu.csv', rows)
            alt['abnehmerdaten_speichern']()
            ansicht.abnehmerdaten_speichern()
            assert (Path(tmp) / 'alt.csv').read_bytes() == (Path(tmp) / 'neu.csv').read_bytes()
        # Änderung: Erfolgreichen Upload und Formatabweisung mit identischen Eingaben prüfen.
        for inhalt in (originalbytes, b'Falsche-Spalte;Wert\n1;2\n'):
            alt['abnehmer_upload'](SimpleNamespace(content=io.BytesIO(inhalt)))
            ansicht.abnehmer_upload(SimpleNamespace(content=io.BytesIO(inhalt)))
            assert app.abnehmer_db == alt['abnehmer_db']
            assert app.abschlag_db == alt['abschlag_db']
        assert app.db_sichern.call_args_list == alt['db_sichern'].call_args_list
        assert ansicht.button_abnehmer_speichern.method_calls == alt['button_abnehmer_speichern'].method_calls
    assert quelle.read_bytes() == originalbytes


if __name__ == '__main__':
    try:
        # Änderung: Keine Beispieldaten oder Tracebacks in Werkzeugausgaben ausgeben.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Abnehmeransicht: Spalten, Bearbeiten, Speichern und Upload gegen Original bestanden.')
    except Exception as fehler:
        print('Abnehmerprüfung nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)
