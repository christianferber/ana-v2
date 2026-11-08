"""Änderung 2.037: Werkzeuge mit ausschließlich lokalen PDF-Beispieldaten vergleichen."""
import ast
import asyncio
import contextlib
import copy
import io
from pathlib import Path
import re
import os
import shutil
import tempfile
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from pypdf import PdfReader, PdfWriter
import anwendung.werkzeuge_ui as modul
from anwendung.einstellungen import ini_datei_lesen


def pruefen():
    basis = Path(__file__).resolve().parents[1]
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
    pdfs = sorted(daten.rglob('*.pdf'))
    assert len(pdfs) >= 2
    import hashlib
    bestand = {p: hashlib.sha256(p.read_bytes()).digest() for p in pdfs}
    baum = ast.parse((basis.parent / '_Vorlagen' / 'ana' / 'ana.py').read_text(encoding='utf-8-sig'))
    namen = {'extract_numbers', 'pdfjoin', 'pdfordner1_auswaehlen', 'pdfordner2_auswaehlen', 'ausgabeordner_auswaehlern'}
    funktionen = [copy.deepcopy(n) for n in baum.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in namen]
    alt = dict(re=re, os=os, PdfReader=PdfReader, PdfWriter=PdfWriter, webview=modul.webview)
    exec(compile(ast.Module(body=funktionen, type_ignores=[]), 'original_werkzeuge', 'exec'), alt)
    app = SimpleNamespace(pdfordner1_pfad='', pdfordner2_pfad='', ausgabeordner_pfad='')
    ansicht = modul.WerkzeugeOberflaeche(app)
    app.extract_numbers = ansicht.extract_numbers
    for name in ('label_ordner1', 'label_ordner2', 'label_ausgabe', 'log_feld'):
        alt[name] = SimpleNamespace(text='', value='')
        setattr(ansicht, name, SimpleNamespace(text='', value=''))
    for datei in ('a-12-b.pdf', 'a-12-b-34-c.pdf', 'ohne-id.pdf', 'a-123-b.pdf', 'a-1-b.PDF'):
        assert alt['extract_numbers'](datei) == ansicht.extract_numbers(datei)
    # Änderung: Ordnerwahl und Abbruch ohne native Fenster über echte Async-Methoden prüfen.
    async def dialoge():
        for methode, pfad, label in (
            ('pdfordner1_auswaehlen', 'pdfordner1_pfad', 'label_ordner1'),
            ('pdfordner2_auswaehlen', 'pdfordner2_pfad', 'label_ordner2'),
            ('ausgabeordner_auswaehlern', 'ausgabeordner_pfad', 'label_ausgabe')):
            alt[pfad] = ''
            for wert in (None, [], [str(basis / '.lokal')]):
                links = SimpleNamespace(native=SimpleNamespace(main_window=SimpleNamespace(create_file_dialog=AsyncMock(return_value=wert))))
                rechts = SimpleNamespace(native=SimpleNamespace(main_window=SimpleNamespace(create_file_dialog=AsyncMock(return_value=wert))))
                alt['app'] = links
                with patch.object(modul, 'app', rechts):
                    await alt[methode]()
                    await getattr(ansicht, methode)()
                assert alt[pfad] == getattr(app, pfad)
                assert alt[label].text == getattr(ansicht, label).text
                assert links.native.main_window.create_file_dialog.call_args_list == rechts.native.main_window.create_file_dialog.call_args_list
    asyncio.run(dialoge())
    with tempfile.TemporaryDirectory(dir=basis / '.lokal') as tmp:
        wurzel = Path(tmp)
        eins, zwei, links, rechts = [wurzel / n for n in ('eins', 'zwei', 'alt', 'neu')]
        for ordner in (eins, zwei, links, rechts):
            ordner.mkdir()
        # Änderung: Echte PDFs nur lokal unter neutralen Dateinamen kopieren.
        for name in ('a-12-b.pdf', 'mehr-12-b-34-c.pdf', 'ohne-id.pdf', 'kein-99-pendant.pdf'):
            shutil.copyfile(pdfs[0], eins / name)
        for name in ('b-12-c.pdf', 'zweites-12-c.pdf', 'mehr-12-b-34-c.pdf'):
            shutil.copyfile(pdfs[1], zwei / name)
        def lauf(ordner1, ordner2):
            for name, wert in (('pdfordner1_pfad', str(ordner1)), ('pdfordner2_pfad', str(ordner2))):
                alt[name] = wert
                setattr(app, name, wert)
            alt['ausgabeordner_pfad'], app.ausgabeordner_pfad = str(links), str(rechts)
            ui_alt, ui_neu = Mock(), Mock()
            alt['ui'] = ui_alt
            fortschritt_alt, fortschritt_neu = Mock(value=0), Mock(value=0)
            with patch.object(modul, 'ui', ui_neu):
                alt['pdfjoin'](fortschritt_alt)
                ansicht.pdfjoin(fortschritt_neu)
            assert alt['log_feld'].value == ansicht.log_feld.value
            assert fortschritt_alt.value == fortschritt_neu.value
            assert fortschritt_alt.method_calls == fortschritt_neu.method_calls
            assert ui_alt.notify.call_args_list == ui_neu.notify.call_args_list
        lauf('', '')
        lauf(eins, zwei)
        assert sorted(p.name for p in links.iterdir()) == sorted(p.name for p in rechts.iterdir()) == ['a-12-b-komplett.pdf']
        a, b = links / 'a-12-b-komplett.pdf', rechts / 'a-12-b-komplett.pdf'
        assert a.read_bytes() == b.read_bytes()
        reader = PdfReader(b)
        erwartet = list(PdfReader(pdfs[0]).pages) + list(PdfReader(pdfs[1]).pages)
        assert len(reader.pages) == len(erwartet)
        assert [p.extract_text() for p in reader.pages] == [p.extract_text() for p in erwartet]
        assert '[WARN]' in ansicht.log_feld.value and '[INFO]' in ansicht.log_feld.value
        leer = wurzel / 'leer'
        leer.mkdir()
        lauf(leer, zwei)
    assert bestand == {p: hashlib.sha256(p.read_bytes()).digest() for p in pdfs}


if __name__ == '__main__':
    try:
        # Änderung: Keine PDF-Inhalte, Beispieldaten oder Tracebacks ausgeben.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Werkzeuge: Ordnerwahl, Abbruch, Zuordnung, PDF-Inhalte und Fortschritt gegen Original bestanden.')
    except Exception as fehler:
        print('Werkzeugeprüfung nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)
