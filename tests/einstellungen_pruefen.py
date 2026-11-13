"""Änderung 2.038: Einstellungen mit lokalen Konfigurationskopien gegen Original prüfen."""
import ast
import asyncio
import configparser
import contextlib
import copy
import io
from pathlib import Path
import tempfile
import hashlib
import shutil
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
import anwendung.einstellungen_ui as modul
from anwendung.einstellungen import ini_datei_lesen, ini_datei_schreiben, datenordner_anlegen, pfade_erstellen


def ordneranlage_pruefen(basis, beispieldaten):
    # Änderung nach 2.06.00: Externe, relative und leere INI-Pfade mit lokalen Daten prüfen.
    with tempfile.TemporaryDirectory(dir=basis / '.lokal') as tmp:
        wurzel = Path(tmp)
        programm = wurzel / 'programm'
        programm.mkdir()
        ini = programm / 'ana.ini'
        daten = wurzel / 'vorhandene-daten'
        shutil.copytree(beispieldaten, daten)
        namen = [Path(p).name for k, p in pfade_erstellen(str(daten)).items() if k != 'arbeitsordner']
        for name in namen:
            (daten / name).mkdir(exist_ok=True)
        vorher = {p.relative_to(daten): hashlib.sha256(p.read_bytes()).digest()
                  for p in daten.rglob('*') if p.is_file()}
        config = configparser.ConfigParser()
        def pfad_setzen(wert):
            config['Anwendung'] = {'Arbeitsordner': wert}
            ini_datei_schreiben(ini, config)
        pfad_setzen(str(daten))
        # Änderung: Vorhandene Ordner dürfen keine mkdir-Aufrufe und keine Programmordner erzeugen.
        with patch.object(Path, 'mkdir', side_effect=AssertionError('Vorhandener Ordner erneut angelegt')):
            datenordner_anlegen(ini, programm)
        assert not any((programm / name).exists() for name in namen)
        assert vorher == {p.relative_to(daten): hashlib.sha256(p.read_bytes()).digest()
                          for p in daten.rglob('*') if p.is_file()}
        # Änderung: Bei teilweise vorhandenem Ziel nur die Lücken ergänzen.
        teilweise = wurzel / 'teilweise'
        (teilweise / 'Datenbank').mkdir(parents=True)
        marker = teilweise / 'Datenbank/bestand.txt'
        marker.write_text('Lokaler Testbestand', encoding='utf-8')
        zeit = marker.parent.stat().st_mtime_ns
        pfad_setzen(str(teilweise))
        datenordner_anlegen(ini, programm)
        assert all((teilweise / name).is_dir() for name in namen)
        assert marker.read_text(encoding='utf-8') == 'Lokaler Testbestand'
        assert marker.parent.stat().st_mtime_ns == zeit
        assert not any((programm / name).exists() for name in namen)
        # Änderung: Auch einen fehlenden konfigurierten Basispfad am richtigen Ort erstellen.
        neu = wurzel / 'neuer-pfad/arbeitsdaten'
        pfad_setzen(str(neu))
        inhalt = ini.read_bytes()
        datenordner_anlegen(ini, programm)
        assert all((neu / name).is_dir() for name in namen)
        assert ini.read_bytes() == inhalt
        assert not any((programm / name).exists() for name in namen)
        # Änderung: Relative INI-Pfade beziehen sich auf den Programmordner.
        pfad_setzen('../teilweise')
        with patch.object(Path, 'mkdir', side_effect=AssertionError('Relativer Bestand erneut angelegt')):
            datenordner_anlegen(ini, programm)
        # Änderung: Leerer oder fehlender INI-Pfad verwendet ausschließlich den Programmordner.
        pfad_setzen('')
        datenordner_anlegen(ini, programm)
        assert all((programm / name).is_dir() for name in namen)
        ini.unlink()
        with patch.object(Path, 'mkdir', side_effect=AssertionError('Programmordner erneut angelegt')):
            datenordner_anlegen(ini, programm)


class Textfeld:
    # Änderung: Textänderung des Anzeigeelements ohne echten Dialog nachvollziehen.
    def __init__(self, text):
        self.text = text

    def set_text(self, text):
        self.text = text


# Änderung: Fachvergleich isoliert Zusatzprotokoll; echte Protokolle separat prüfen.
@patch('anwendung.aenderungsprotokoll.protokolliere', lambda *args: None)
def pruefen():
    basis = Path(__file__).resolve().parents[1]
    config = ini_datei_lesen(basis / 'ana.ini')
    daten = Path(config['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
    ordneranlage_pruefen(basis, daten)
    original = {p: p.read_bytes() for p in (basis / 'ana.ini', daten / 'ana-betreiber.ini')}
    betreiber = ini_datei_lesen(daten / 'ana-betreiber.ini')['Betreiber']
    baum = ast.parse((basis.parent / '_Vorlagen' / 'ana' / 'ana.py').read_text(encoding='utf-8-sig'))
    namen = {'ini_speichern', 'ordner_standard', 'ordner_auswaehlen'}
    fs = [copy.deepcopy(n) for n in baum.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in namen]
    alt = dict(configparser=configparser, Path=Path, webview=modul.webview)
    exec(compile(ast.Module(body=fs, type_ignores=[]), 'original_einstellungen', 'exec'), alt)
    app = SimpleNamespace()
    ansicht = modul.EinstellungenOberflaeche(app)
    # Änderung: Echte lokale Werte verwenden, aber ausschließlich temporäre Ziele beschreiben.
    felder = {'ini_betreiber_name': betreiber['BetreiberName'], 'ini_glaeubiger_id': betreiber['GlaeubigerID'],
              'ini_betreiber_iban': betreiber['BetreiberIBAN'], 'ini_arbeitspreis': betreiber['Waermepreis'],
              'ini_grundgebuehr': betreiber['Grundgebuehr'], 'ini_farbe_spezial': config['Anwendung']['FarbeSpezial'],
              'ini_farbe_tabelle_edit': config['Anwendung']['FarbeTabelleEdit'],
              'ini_tabelle_pagination': config['Anwendung']['TabellenZeilenProSeite']}
    for name, wert in felder.items():
        alt[name] = SimpleNamespace(value=wert)
        setattr(ansicht, name, SimpleNamespace(value=wert))
    with tempfile.TemporaryDirectory(dir=basis / '.lokal') as tmp:
        wurzel = Path(tmp)
        alt['ini'], app.ini = str(wurzel / 'ana.ini'), str(wurzel / 'ana.ini')
        alt['ini_betreiber'] = app.ini_betreiber = 'ana-betreiber.ini'
        alt['arbeitsordner'] = app.arbeitsordner = str(wurzel)
        for ausgewaehlt in (str(wurzel), str(wurzel / 'neuer-ordner'), ''):
            alt['ini_arbeitsordner'] = Textfeld(ausgewaehlt)
            ansicht.ini_arbeitsordner = Textfeld(ausgewaehlt)
            for name in ('dialog_neustart', 'dialog_einstellungen'):
                alt[name] = Mock()
                setattr(ansicht, name, Mock())
            alt['ini_einlesen'], app.ini_einlesen = Mock(), Mock()
            alt['ini_speichern']()
            vorher = {p.name: p.read_bytes() for p in wurzel.glob('*.ini')}
            ansicht.ini_speichern()
            assert vorher == {p.name: p.read_bytes() for p in wurzel.glob('*.ini')}
            assert alt['dialog_neustart'].method_calls == ansicht.dialog_neustart.method_calls
            assert ansicht.dialog_neustart.open.call_count == int(ausgewaehlt != str(wurzel))
            assert alt['dialog_einstellungen'].method_calls == ansicht.dialog_einstellungen.method_calls
            assert app.ini_einlesen.call_count == alt['ini_einlesen'].call_count == 1
            assert not (wurzel / 'neuer-ordner').exists()
        alt['ordner_standard']()
        ansicht.ordner_standard()
        assert alt['ini_arbeitsordner'].text == ansicht.ini_arbeitsordner.text == ''
        # Änderung: Native Ordnerwahl einschließlich bisheriger Abbruchbehandlung vergleichen.
        async def dialoge():
            for wert in ((str(wurzel),), None, ()):
                links = SimpleNamespace(native=SimpleNamespace(main_window=SimpleNamespace(create_file_dialog=AsyncMock(return_value=wert))))
                rechts = SimpleNamespace(native=SimpleNamespace(main_window=SimpleNamespace(create_file_dialog=AsyncMock(return_value=wert))))
                alt['app'] = links
                with patch.object(modul, 'app', rechts):
                    await alt['ordner_auswaehlen']()
                    await ansicht.ordner_auswaehlen()
                assert alt['ini_arbeitsordner'].text == ansicht.ini_arbeitsordner.text
                assert links.native.main_window.create_file_dialog.call_args_list == rechts.native.main_window.create_file_dialog.call_args_list
        asyncio.run(dialoge())
    assert original == {p: p.read_bytes() for p in original}


if __name__ == '__main__':
    try:
        # Änderung: Keine Konfigurationsinhalte oder Tracebacks weitergeben.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Einstellungen: INI-Inhalte, Arbeitsordnerwechsel, Dialoge, Standard und Ordnerwahl gegen Original bestanden.')
    except Exception as fehler:
        print('Einstellungsprüfung nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)
