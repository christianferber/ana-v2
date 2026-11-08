"""Änderung 2.036: Kontodatenmethoden mit ausschließlich lokalen Beispieldaten vergleichen."""
import ast
import contextlib
import copy
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

from anwendung.kontodaten_ui import KontodatenOberflaeche
from anwendung.datenhaltung import datei_oeffnen, datei_speichern, import_csv_inhalt
from anwendung.einstellungen import ini_datei_lesen
from schwifty import IBAN


def pruefen():
    basis = Path(__file__).resolve().parents[1]
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
    quelle = daten / 'Datenbank' / 'db_kontodaten.csv'
    originalbytes = quelle.read_bytes()
    zeilen = datei_oeffnen(quelle)
    assert zeilen
    baum = ast.parse((basis.parent / '_Vorlagen' / 'ana' / 'ana.py').read_text(encoding='utf-8-sig'))
    namen = {'konto_columns_erstellen', 'buchung_tabelle_on_change', 'db_konto_speichern', 'konto_aus_db', 'konto_upload'}
    funktionen = [copy.deepcopy(n) for n in baum.body if isinstance(n, ast.FunctionDef) and n.name in namen]
    ui = Mock()
    alt = dict(ui=ui, events=SimpleNamespace(UploadEventArguments=object), StringIO=io.StringIO,
               IBAN=IBAN, import_csv_inhalt=import_csv_inhalt, konto_db=copy.deepcopy(zeilen),
               button_konto_speichern=Mock(), konto_grid_ui=Mock(), change_log=Mock(),
               col_cell_mod='test', db_konto='db_kontodaten.csv')
    exec(compile(ast.Module(body=funktionen, type_ignores=[]), 'original_kontodaten', 'exec'), alt)
    app = SimpleNamespace(konto_db=copy.deepcopy(zeilen), col_cell_mod='test',
                          change_log=Mock(), konto_grid_ui=Mock(), db_konto='db_kontodaten.csv')
    ansicht = KontodatenOberflaeche(app)
    ansicht.button_konto_speichern = Mock()
    with patch('anwendung.kontodaten_ui.ui', ui):
        assert ansicht.konto_columns_erstellen(app.konto_db) == alt['konto_columns_erstellen'](alt['konto_db'])
        # Änderung: Leere Eingabe, Freitext sowie gültige und ungültige IBAN vergleichen.
        iban = next(str(row['IBAN']) for row in zeilen if IBAN(str(row['IBAN']), allow_invalid=True).is_valid)
        for spalte, wert in (('Zahlungspflichtiger', None), ('Zahlungspflichtiger', 'Lokaler Test'),
                             ('Datum SEPA-Auftrag', '01.01.2027'), ('IBAN', 'ungueltig'), ('IBAN', iban)):
            event = dict(newValue=wert, rowId='0', colId=spalte)
            alt['buchung_tabelle_on_change'](event)
            ansicht.buchung_tabelle_on_change(event)
            assert app.konto_db == alt['konto_db']
        assert app.change_log.call_args_list == alt['change_log'].call_args_list
        # Änderung: Bytegleichen CSV-Inhalt nur in lokalen temporären Dateien prüfen.
        with tempfile.TemporaryDirectory(dir=basis / '.lokal') as tmp:
            alt['db_datei_speichern'] = lambda name, rows: datei_speichern(Path(tmp) / 'alt.csv', rows)
            app.db_datei_speichern = lambda name, rows: datei_speichern(Path(tmp) / 'neu.csv', rows)
            alt['db_konto_speichern']()
            ansicht.db_konto_speichern()
            assert (Path(tmp) / 'alt.csv').read_bytes() == (Path(tmp) / 'neu.csv').read_bytes()
        alt['db_datei_oeffnen'] = lambda name: datei_oeffnen(quelle)
        app.db_datei_oeffnen = alt['db_datei_oeffnen']
        alt['konto_aus_db']()
        ansicht.konto_aus_db()
        assert app.konto_db == alt['konto_db']
        # Änderung: Bestehende Kontodaten lokal in das bisherige Uploadformat übertragen.
        import csv
        inhalt = io.StringIO()
        writer = csv.DictWriter(inhalt, delimiter=';', fieldnames=['Ident', 'Name', 'Vorname',
            'Zahlungspflichtiger', 'IBAN des Zahlungspflichtigen', 'BIC', 'Bei Kreditinstitut', 'Unterschrieben am'])
        writer.writeheader()
        for row in zeilen:
            if not IBAN(str(row['IBAN']), allow_invalid=True).is_valid:
                continue
            writer.writerow({**{k: row.get(k, '') for k in ('Ident', 'Name', 'Vorname', 'Zahlungspflichtiger', 'BIC')},
                'IBAN des Zahlungspflichtigen': row['IBAN'], 'Bei Kreditinstitut': row.get('Bank', ''),
                'Unterschrieben am': row.get('Datum SEPA-Auftrag', '')})
        for wert in (inhalt.getvalue().encode('iso-8859-1', errors='ignore'), b'Falsche-Spalte;Wert\n1;2\n'):
            # Änderung: Auch bisherige Fehler bei ungeeignetem Format unverändert bestätigen.
            fehler = []
            for aufruf in (alt['konto_upload'], ansicht.konto_upload):
                try:
                    aufruf(SimpleNamespace(content=io.BytesIO(wert)))
                    fehler.append(None)
                except Exception as ausnahme:
                    fehler.append((type(ausnahme), ausnahme.args))
            assert fehler[0] == fehler[1]
            if wert.startswith(b'Ident'):
                assert fehler[0] is None
            assert app.konto_db == alt['konto_db']
        assert ansicht.button_konto_speichern.method_calls == alt['button_konto_speichern'].method_calls
        assert app.konto_grid_ui.method_calls == alt['konto_grid_ui'].method_calls
    assert quelle.read_bytes() == originalbytes


if __name__ == '__main__':
    try:
        # Änderung: Beispieldaten und Fehlerdetails niemals in Werkzeugausgaben ausgeben.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Kontodatenansicht: Spalten, Bearbeitung, IBAN, Laden, Speichern und Upload gegen Original bestanden.')
    except Exception as fehler:
        print('Kontodatenprüfung nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)
