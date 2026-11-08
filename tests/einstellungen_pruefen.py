"""Änderung 2.038: Einstellungen mit lokalen Konfigurationskopien gegen Original prüfen."""
import ast
import asyncio
import configparser
import contextlib
import copy
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
import anwendung.einstellungen_ui as modul
from anwendung.einstellungen import ini_datei_lesen


class Textfeld:
    # Änderung: Textänderung des Anzeigeelements ohne echten Dialog nachvollziehen.
    def __init__(self, text):
        self.text = text

    def set_text(self, text):
        self.text = text


def pruefen():
    basis = Path(__file__).resolve().parents[1]
    config = ini_datei_lesen(basis / 'ana.ini')
    daten = Path(config['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
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
