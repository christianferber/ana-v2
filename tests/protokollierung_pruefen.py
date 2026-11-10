"""Änderung: Echte lokale Änderungsprotokolle und unveränderte Beispieldaten prüfen."""
import ast
import contextlib
import copy
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch
import warnings

from anwendung.aenderungsprotokoll import aenderungen_protokollieren
from anwendung.protokollierung import Protokollierung
from anwendung.datenhaltung import DatenbankZugriff, dictlist_to_csv, check_ordner_exists
from anwendung.einstellungen_ui import EinstellungenOberflaeche
from anwendung.kontodaten_ui import KontodatenOberflaeche
from anwendung.datenhaltung import datei_oeffnen
from anwendung.einstellungen import ini_datei_lesen
from anwendung import mitglieder_ui


def pruefen():
    basis = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(dir=basis / '.lokal') as tmp:
        root = Path(tmp)
        app = SimpleNamespace(ordner_logs=str(root), changelog='aenderungen.log',
                              changelog_markdown_ui_refresh=Mock())
        app.change_log_info = Protokollierung(app).change_log_info
        log = root / app.changelog
        daten = [{'Ident': '1', 'Wert': 'alt'}]
        with aenderungen_protokollieren(app, 'TEST', 'Ohne Änderung', daten=lambda: {'Testbestand': daten}):
            pass
        assert not log.exists()
        # Änderung: Unlesbare Beobachtungsdateien dürfen die bestehende Aktion nicht verhindern.
        with patch('anwendung.aenderungsprotokoll.dateistand', side_effect=OSError()), warnings.catch_warnings(record=True) as meldungen:
            warnings.simplefilter('always')
            with aenderungen_protokollieren(app, 'TEST', 'Nicht lesbar'):
                ausgefuehrt = True
            assert ausgefuehrt and len(meldungen) == 1
        with aenderungen_protokollieren(app, 'TEST', 'Bearbeiten', daten=lambda: {'Testbestand': daten}):
            daten[0]['Wert'] = 'neu'
        assert 'Bearbeiten' in log.read_text()
        assert 'Arbeitsspeicher: Testbestand' in log.read_text()
        vorher = log.read_bytes()
        try:
            with aenderungen_protokollieren(app, 'TEST', 'Fehler ohne Änderung', daten=lambda: {'Testbestand': daten}):
                raise ValueError('synthetisch')
        except ValueError:
            pass
        assert log.read_bytes() == vorher
        try:
            with aenderungen_protokollieren(app, 'TEST', 'Teiländerung', daten=lambda: {'Testbestand': daten}):
                daten.append({'Ident': '2'})
                raise ValueError('synthetisch')
        except ValueError:
            pass
        assert 'Aktion abgebrochen; bereits ausgeführte Teiländerung' in log.read_text()
        # Änderung: Protokollfehler dürfen ursprüngliche Ausnahmen und Daten nicht verändern.
        with patch('anwendung.aenderungsprotokoll.protokolliere', side_effect=OSError()), warnings.catch_warnings(record=True) as meldungen:
            warnings.simplefilter('always')
            try:
                with aenderungen_protokollieren(app, 'TEST', 'Protokollfehler', daten=lambda: {'Testbestand': daten}):
                    daten.append({'Ident': '3'})
                    raise LookupError('ursprünglich')
            except LookupError:
                pass
            else:
                raise AssertionError('Ursprünglicher Fehler verloren')
            assert len(meldungen) == 1
        # Änderung: Datenbankdateien erst nach tatsächlicher Änderung protokollieren.
        for name in ('ordner_abrechnungen','ordner_rueckv','ordner_datenbank','ordner_sicherungen','ordner_downloads'):
            setattr(app, name, str(root))
        app.check_ordner_exists = check_ordner_exists
        app.dictlist_to_csv = dictlist_to_csv
        db = DatenbankZugriff(app)
        db.db_datei_speichern('test.csv', [{'Ident':'1','Name':'Test'}])
        assert 'Datei geändert: test.csv' in log.read_text()
        vorher = log.read_bytes()
        db.db_datei_speichern('test.csv', [{'Ident':'1','Name':'Test'}])
        assert log.read_bytes() == vorher
        # Änderung: Mitgliederanlage ist vor dem späteren Speichern bereits protokolliert.
        app.mitglieder_db = [{'Laufende Nummer':'1','Ident':'1','Name':'Test','Vorname':'A'}]
        app.mitglieder_grid_update = Mock()
        view = mitglieder_ui.MitgliederOberflaeche(app)
        tree = ast.parse((basis/'anwendung/mitglieder_ui.py').read_text(encoding='utf-8'))
        typ = next(n for n in tree.body if isinstance(n,ast.ClassDef))
        neu = next(n for n in typ.body if isinstance(n,ast.FunctionDef) and n.name=='mitglieder_neu')
        callback = next(n for n in neu.body if isinstance(n,ast.FunctionDef))
        env = dict(vars(mitglieder_ui), self=view, neue_lnr=2,
                   input_name=SimpleNamespace(value='Test'), input_vorname=SimpleNamespace(value='B'),
                   dialog=Mock(), ui=Mock())
        exec(compile(ast.Module(body=[callback],type_ignores=[]),'<Mitglieder-Callback>','exec'),env)
        env[callback.name]()
        assert len(app.mitglieder_db) == 2 and 'Mitglied anlegen' in log.read_text()
        # Änderung: Fehlerhafter Kontoimport bleibt fachlich unverändert, wird als Teiländerung erfasst.
        app.konto_db = [{'Ident':9}]
        app.konto_grid_ui = Mock()
        konto = KontodatenOberflaeche(app)
        try:
            konto.konto_upload(SimpleNamespace(content=io.BytesIO(b'Falsch;Spalte\n1;2\n')))
        except KeyError:
            pass
        else:
            raise AssertionError('Bisheriger Importfehler verändert')
        assert app.konto_db == [{'Falsch':'1','Spalte':'2'}]
        assert 'Kontodaten importieren ::: Aktion abgebrochen' in log.read_text()
        # Änderung: Beide Einstellungsdateien werden beobachtet, unverändertes Speichern nicht neu geloggt.
        app.ini = str(root/'ana.ini')
        app.arbeitsordner = str(root)
        app.ini_betreiber = 'betreiber.ini'
        app.ini_einlesen = Mock()
        view = EinstellungenOberflaeche(app)
        for name, value in dict(ini_farbe_spezial='red',ini_farbe_tabelle_edit='#000000',
                                ini_tabelle_pagination='20',ini_betreiber_name='Test',
                                ini_glaeubiger_id='Test',ini_betreiber_iban='Test',
                                ini_arbeitspreis='10',ini_grundgebuehr='20').items():
            setattr(view,name,SimpleNamespace(value=value))
        view.ini_arbeitsordner=SimpleNamespace(text=str(root))
        view.dialog_neustart=Mock()
        view.dialog_einstellungen=Mock()
        view.ini_speichern()
        assert 'Einstellungen speichern' in log.read_text()
        vorher=log.read_bytes()
        view.ini_speichern()
        assert log.read_bytes()==vorher
        # Änderung: Echte lokale Beispieldatenkopie bearbeiten; Quelle und Inhalte nie ausgeben.
        quelle = Path(ini_datei_lesen(basis/'ana.ini')['Anwendung']['Arbeitsordner'])/'Datenbank'/'db_kontodaten.csv'
        original = quelle.read_bytes()
        app.konto_db = copy.deepcopy(datei_oeffnen(quelle))
        assert app.konto_db
        with aenderungen_protokollieren(app,'KONTODATEN','Lokaler Beispielvergleich',daten=lambda:{'Kontodaten':app.konto_db}):
            app.konto_db[0]['Name'] = 'Lokaler Test'
        assert 'Lokaler Beispielvergleich' in log.read_text()
        assert quelle.read_bytes()==original
        assert all(' | ' in zeile for zeile in log.read_text().splitlines())
    print('Änderungsprotokoll: Daten, Dateien, Einstellungen, Teilfehler und lokale Beispieldaten bestanden.')


if __name__ == '__main__':
    pruefen()
