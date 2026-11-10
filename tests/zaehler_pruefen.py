"""Änderung 2.033: Echte Zählermethoden lokal gegen den bisherigen Ablauf prüfen."""
import ast
from collections import Counter
import contextlib
import copy
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

from anwendung.zaehler_ui import ZaehlerOberflaeche
from anwendung.datenhaltung import datei_oeffnen, datei_speichern
from anwendung.einstellungen import ini_datei_lesen
from anwendung.berechnungen import datum_in_string, datum_in_punkt, datum_tage_vorher


# Änderung: Fachvergleich isoliert Zusatzprotokoll; echte Protokolle separat prüfen.
@patch('anwendung.aenderungsprotokoll.protokolliere', lambda *args: None)
def pruefen():
    # Änderung: Beispieldaten nur lokal lesen und ausschließlich Testkopien bearbeiten.
    basis = Path(__file__).resolve().parents[1]
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
    quelle = daten / 'Datenbank' / 'db_zaehler.csv'
    vorher = quelle.read_bytes()
    zeilen = datei_oeffnen(quelle)
    baum = ast.parse((basis.parent / '_Vorlagen' / 'ana' / 'ana.py').read_text(encoding='utf-8-sig'))
    namen = {k for k in vars(ZaehlerOberflaeche) if not k.startswith('__')}
    namen.update({'listcsv_to_dict', 'jahr_in_datum'})
    funktionen = [copy.deepcopy(n) for n in baum.body if isinstance(n, ast.FunctionDef) and n.name in namen]
    for f in funktionen:
        f.decorator_list = []
    alt = dict(ui=Mock(), events=SimpleNamespace(UploadEventArguments=object),
               Counter=Counter, StringIO=io.StringIO, Path=Path,
               datum_in_string=datum_in_string, datum_in_punkt=datum_in_punkt,
               datum_tage_vorher=datum_tage_vorher)
    exec(compile(ast.Module(body=funktionen, type_ignores=[]), 'original_zaehler', 'exec'), alt)
    gemeinsame = dict(zaehler_db=copy.deepcopy(zeilen), db_zaehler_found=1,
                       db_zaehler='db_zaehler.csv', col_cell_mod='test',
                       change_log=Mock(), change_log_info=Mock(), db_sichern=Mock(),
                       zaehler_grid_ui=Mock(), zaehler_label_ui=Mock())
    alt.update(copy.deepcopy(gemeinsame))
    app = SimpleNamespace(**gemeinsame)
    app.listcsv_to_dict = alt['listcsv_to_dict']
    app.jahr_in_datum = alt['jahr_in_datum']
    ansicht = ZaehlerOberflaeche(app)
    bedienung = ('zaehler_button_speichern', 'zaehler_button_check',
                 'zaehler_dialog_check_label01', 'zaehler_dialog_check_label02',
                 'zaehler_dialog_check_input01', 'dialog_zaehler_check', 'upload_overwrite_switch')
    for name in bedienung:
        alt[name] = Mock()
        setattr(ansicht, name, Mock())
    with patch('anwendung.zaehler_ui.ui', alt['ui']):
        # Änderung: Visualisierungsformat mit Zählerwechsel und fehlendem Endstand prüfen.
        visu = '\n'.join(['Verbrauch Gesamt', 'Tag von;2099-01-01;',
                          'Tag bis;2099-12-31;', '', '', '',
                          '0;TAG VON;TAG BIS;Zaehlerstand VON(kWh);Zaehlerstand BIS(kWh);',
                          '1;2099-01-01;2099-06-01;0;100;',
                          '1;2099-06-01;2100-01-01;0;200;',
                          '2;2099-01-01;2099-08-01;0;300;', '', ''])
        assert ansicht.import_zaehlerdaten_visu(visu) == alt['import_zaehlerdaten_visu'](visu)
        assert ansicht.zaehler_columns_erstellen(app.zaehler_db) == alt['zaehler_columns_erstellen'](alt['zaehler_db'])
        ansicht.zaehler_sortieren()
        alt['zaehler_sortieren']()
        assert app.zaehler_db == alt['zaehler_db']
        assert list(app.zaehler_db[0]) == list(alt['zaehler_db'][0])
        spalte = next(k for k in zeilen[0] if '-zaehler' in k and 'datum' not in k)
        for wert in (None, -1, 12345):
            event = dict(newValue=wert, rowId='0', colId=spalte)
            ansicht.zaehler_tabelle_on_change(event)
            alt['zaehler_tabelle_on_change'](event)
            assert app.zaehler_db == alt['zaehler_db']
        # Änderung: Monatsende, Überschreiben und unerlaubtes Datum vergleichen.
        for overwrite in (False, True):
            ansicht.upload_overwrite_switch.value = overwrite
            alt['upload_overwrite_switch'].value = overwrite
            for key in (spalte, '20991231-zaehler', '20991230-zaehler'):
                eingabe = [{'Ident': zeilen[0]['Ident'], key: '45678'}]
                assert ansicht.import_zaehler_liste(copy.deepcopy(eingabe)) == alt['import_zaehler_liste'](copy.deepcopy(eingabe))
                assert app.zaehler_db == alt['zaehler_db']
        # Änderung: Zahlen- und Datumsdialog sowie Übernahme auf identischen Kopien prüfen.
        for key, leer, eingabe in ((spalte, -1, '12345'), ('2099-datum-zaehlerwechsel', 'NICHT_VORHANDEN', '01.01.2099')):
            app.zaehler_db = copy.deepcopy(zeilen[:1])
            alt['zaehler_db'] = copy.deepcopy(zeilen[:1])
            app.zaehler_db[0][key] = leer
            alt['zaehler_db'][0][key] = leer
            ansicht.check_zaehlerdaten()
            alt['check_zaehlerdaten']()
            assert ansicht.zaehler_input_values == alt['zaehler_input_values']
            ansicht.zaehler_dialog_check_input01.value = eingabe
            alt['zaehler_dialog_check_input01'].value = eingabe
            ansicht.dialog_zaehlerstand_uebernehmen()
            alt['dialog_zaehlerstand_uebernehmen']()
            assert app.zaehler_db == alt['zaehler_db']
        with tempfile.TemporaryDirectory(dir=basis / '.lokal') as tmp:
            app.db_datei_speichern = lambda name, rows: datei_speichern(Path(tmp) / 'neu.csv', rows)
            alt['db_datei_speichern'] = lambda name, rows: datei_speichern(Path(tmp) / 'alt.csv', rows)
            app.zaehler_db = copy.deepcopy(zeilen)
            alt['zaehler_db'] = copy.deepcopy(zeilen)
            ansicht.zaehler_speichern()
            alt['zaehler_speichern']()
            assert (Path(tmp) / 'neu.csv').read_bytes() == (Path(tmp) / 'alt.csv').read_bytes()
            app.zaehler_db[0][spalte] = -1
            alt['zaehler_db'][0][spalte] = -1
            gespeichert = (Path(tmp) / 'neu.csv').read_bytes()
            ansicht.zaehler_speichern()
            alt['zaehler_speichern']()
            assert (Path(tmp) / 'neu.csv').read_bytes() == gespeichert
        for name in bedienung:
            assert getattr(ansicht, name).method_calls == alt[name].method_calls
        assert app.change_log.call_args_list == alt['change_log'].call_args_list
        assert app.change_log_info.call_args_list == alt['change_log_info'].call_args_list
        # Änderung: Upload samt Formatabweisung auf isolierten Ausgangsdaten prüfen.
        app.db_zaehler_found = alt['db_zaehler_found'] = 0
        app.abnehmer_db = copy.deepcopy(zeilen[:1])
        alt['abnehmer_db'] = copy.deepcopy(zeilen[:1])
        visu = visu.replace('\n1;', '\n' + str(zeilen[0]['Ident']) + ';')
        for inhalt in (b'Falsches Format\n', visu.encode('iso-8859-1')):
            ansicht.zaehler_liste_upload(SimpleNamespace(content=io.BytesIO(inhalt)))
            alt['zaehler_liste_upload'](SimpleNamespace(content=io.BytesIO(inhalt)))
            assert app.zaehler_db == alt['zaehler_db']
        assert app.db_sichern.call_args_list == alt['db_sichern'].call_args_list
    assert quelle.read_bytes() == vorher


if __name__ == '__main__':
    try:
        # Änderung: Datenhaltige Ausgaben ausschließlich im lokalen Speicher halten.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Zähleransicht: Originalvergleich mit lokalen Beispieldaten bestanden.')
    except Exception as fehler:
        print('Zählerprüfung nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)
