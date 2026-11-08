"""Änderung 2.035: Gebundene Mitgliederabläufe ausschließlich lokal vergleichen."""
import ast
import contextlib
import copy
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch
from zipfile import ZipFile

import anwendung.mitglieder_ui as modul
from anwendung.datenhaltung import datei_oeffnen, datei_speichern
from anwendung.einstellungen import ini_datei_lesen


def pruefen():
    basis = Path(__file__).resolve().parents[1]
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
    quelle = daten / 'Datenbank' / 'db_mitglieder.csv'
    originalbytes = quelle.read_bytes()
    baum = ast.parse((basis.parent / '_Vorlagen' / 'ana' / 'ana.py').read_text(encoding='utf-8-sig'))
    namen = {n for n in vars(modul.MitgliederOberflaeche) if not n.startswith('__')}
    funktionen = [copy.deepcopy(n) for n in baum.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in namen]
    for n in funktionen:
        n.decorator_list = []
    alt = dict(vars(modul))
    exec(compile(ast.Module(body=funktionen, type_ignores=[]), 'original_mitglieder', 'exec'), alt)
    app = SimpleNamespace()
    ansicht = modul.MitgliederOberflaeche(app)
    # Änderung: Gemeinsam genutzte Daten nur aus lokalen Beispieldateien lesen.
    for name in ('mitglieder', 'wartung', 'abnehmer', 'zaehler', 'abschlag'):
        wert = datei_oeffnen(daten / 'Datenbank' / ('db_' + name + '.csv'))
        alt[name + '_db'] = copy.deepcopy(wert)
        setattr(app, name + '_db', copy.deepcopy(wert))
    alt['konto_db'] = []
    app.konto_db = []
    alt['mitglieder_changes'] = []
    for name in ('db_mitglieder', 'db_wartung'):
        alt[name] = name + '.csv'
        setattr(app, name, alt[name])
    for name in ('pagination',):
        alt[name] = 20
        setattr(app, name, 20)
    # Änderung: Anzeigeelemente und Nebenwirkungen auf beiden Seiten gleich isolieren.
    for name in ('button_mitglieder_pruefen', 'button_mitglieder_speichern', 'button_word_export',
                 'button_serienbrief', 'button_edit', 'button_anschluss', 'button_neu',
                 'button_loeschen', 'button_csv_export', 'button_email', 'mgl_progress'):
        alt[name] = Mock()
        setattr(ansicht, name, Mock())
    alt['mitglieder_grid'] = Mock(options={})
    ansicht.mitglieder_grid = Mock(options={})
    for name in ('mitglieder_filter_dropdown', 'radio_filter', 'edit_switch'):
        alt[name] = Mock()
        setattr(ansicht, name, Mock())
    for name in ('db_sichern', 'change_log_info', 'dbs_mitglieder_aktualisieren'):
        alt[name] = Mock()
        setattr(app, name, Mock())
    # Änderung: Originalhilfe unabhängig laden; bestehende Suchlogik unverändert ausführen.
    helper = next(n for n in baum.body if isinstance(n, ast.FunctionDef) and n.name == 'string_in_dict')
    exec(compile(ast.Module(body=[helper], type_ignores=[]), 'original_suche', 'exec'), alt)
    app.string_in_dict = alt['string_in_dict']
    for name in namen:
        setattr(app, name, getattr(ansicht, name))
    ui = Mock()
    with tempfile.TemporaryDirectory(dir=basis / '.lokal') as tmp, patch.object(modul, 'ui', ui), patch.object(modul.time, 'sleep'):
        alt['ui'] = ui
        for name in ('ordner_downloads', 'ordner_vorlagen'):
            alt[name] = str(Path(tmp) / ('alt-' + name))
            setattr(app, name, str(Path(tmp) / ('neu-' + name)))
        for name in ('db_datei_speichern',):
            alt[name] = lambda datei, rows: datei_speichern(Path(tmp) / 'alt.csv', rows)
            setattr(app, name, lambda datei, rows: datei_speichern(Path(tmp) / 'neu.csv', rows))
        alt['db_datei_oeffnen'] = lambda datei: datei_oeffnen(quelle)
        app.db_datei_oeffnen = alt['db_datei_oeffnen']
        # Änderung: Alle Filter und Sortierungen mit echten Zeilen vergleichen.
        filterwerte = ['kein Filter', 'Verbraucheranschlüsse', 'Aktive Helfer',
                      'Mitgliederliste (Jahresabschluss)', 'Mitgliederliste (Generalversammlung)',
                      'Verbraucher mit Wartungsdaten']
        for filterwert in filterwerte:
            for sortierung in ('Laufende Nummer', 'Ident', 'Name', 'Straße'):
                alt['mitglieder_filter_dropdown'].value = ansicht.mitglieder_filter_dropdown.value = filterwert
                alt['radio_filter'].value = ansicht.radio_filter.value = sortierung
                alt['edit_switch'].value = ansicht.edit_switch.value = False
                # Änderung: Vorhandene Fehler bei lückenhaften Wartungsspalten ebenfalls vergleichen.
                fehler = []
                for aufruf in (alt['mitglieder_grid_update'], ansicht.mitglieder_grid_update):
                    try:
                        aufruf()
                        fehler.append(None)
                    except Exception as ausnahme:
                        fehler.append((type(ausnahme), ausnahme.args))
                assert fehler[0] == fehler[1]
                if fehler[0] is not None:
                    continue
                assert alt['mitglieder_tabelle'] == ansicht.mitglieder_tabelle
                assert alt['mitglieder_grid'].options == ansicht.mitglieder_grid.options
        alt['mitglieder_filter_dropdown'].value = ansicht.mitglieder_filter_dropdown.value = 'kein Filter'
        # Änderung: Auswahl und Bearbeitungsschaltflächen in beiden Modi prüfen.
        for modus in (False, True):
            alt['edit_switch'].value = ansicht.edit_switch.value = modus
            for row in ({}, {'Ident': ''}, {'Ident': '1'}):
                event = SimpleNamespace(args={'data': row})
                alt['edit_aktivieren'](event)
                ansicht.edit_aktivieren(event)
                assert alt['mitglieder_selected_row'] == app.mitglieder_selected_row
        # Änderung: Laden, Upload/Formatabweisung und Speichern gegen Original vergleichen.
        alt['edit_switch'].value = ansicht.edit_switch.value = False
        for inhalt in (originalbytes, b'Falsch;Wert\n1;2\n'):
            alt['mitglieder_upload'](SimpleNamespace(content=io.BytesIO(inhalt)))
            ansicht.mitglieder_upload(SimpleNamespace(content=io.BytesIO(inhalt)))
            assert alt['mitglieder_db'] == app.mitglieder_db
        alt['mitglieder_speichern']()
        ansicht.mitglieder_speichern()
        assert (Path(tmp) / 'alt.csv').read_bytes() == (Path(tmp) / 'neu.csv').read_bytes()
        assert alt['db_sichern'].call_args_list == app.db_sichern.call_args_list
        assert alt['dbs_mitglieder_aktualisieren'].call_args_list == app.dbs_mitglieder_aktualisieren.call_args_list
        # Änderung: Beide Word-Listen in lokalen Zielordnern inhaltlich vergleichen.
        for filterwert, methode, args in (
            ('Mitgliederliste (Jahresabschluss)', 'mitglieder_ja_word_erstellen', ('liste.docx',)),
            ('Mitgliederliste (Generalversammlung)', 'mitglieder_gv_word_erstellen', ('liste.docx', '01.01.2027', 'Testort'))):
            alt['mitglieder_filter_dropdown'].value = ansicht.mitglieder_filter_dropdown.value = filterwert
            alt['radio_filter'].value = ansicht.radio_filter.value = 'Laufende Nummer'
            alt['mitglieder_grid_update']()
            ansicht.mitglieder_grid_update()
            alt[methode](*args)
            getattr(ansicht, methode)(*args)
            with ZipFile(Path(alt['ordner_downloads']) / 'liste.docx') as links, ZipFile(Path(app.ordner_downloads) / 'liste.docx') as rechts:
                assert links.namelist() == rechts.namelist()
                assert all(links.read(n) == rechts.read(n) for n in links.namelist())
        # Änderung: CSV-Export einschließlich Dateiname und Inhalt vergleichen.
        alt['mitglieder_csv_download']()
        ansicht.mitglieder_csv_download()
        links = list(Path(alt['ordner_downloads']).glob('*.csv'))
        rechts = list(Path(app.ordner_downloads).glob('*.csv'))
        assert len(links) == len(rechts) == 1
        assert links[0].name == rechts[0].name and links[0].read_bytes() == rechts[0].read_bytes()
    assert quelle.read_bytes() == originalbytes


if __name__ == '__main__':
    try:
        # Änderung: Beispieldaten und Tracebacks ausschließlich lokal halten.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Mitgliederansicht: Filter, Sortierung, Auswahl, Upload, Speicherung und Word-Listen gegen Original bestanden.')
    except Exception as fehler:
        print('Mitgliederprüfung nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)
