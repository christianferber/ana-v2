"""Änderung 2.043: Sicherungen mit lokalen Datenkopien gegen Original vergleichen."""
import ast
import contextlib
import hashlib
import io
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from anwendung.einstellungen import ini_datei_lesen
from anwendung.sicherung import Sicherung
from tests.changelog_pruefen import FesteZeit


def bestand(pfad):
    # Änderung: Inhalte und copy2-Metadaten prüfen, ohne Daten auszugeben.
    return {str(p.relative_to(pfad)): (p.is_dir(), None if p.is_dir() else
            (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns))
            for p in pfad.rglob('*')}


def pruefen():
    basis = Path(__file__).resolve().parents[1]
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen/ana Beispieldaten').resolve()
    originalbestand = bestand(daten)
    baum = ast.parse((basis.parent / '_Vorlagen/ana/ana.py').read_text(encoding='utf-8-sig'))
    funktionen = [k for k in baum.body if isinstance(k, ast.FunctionDef)
                  and k.name in {'db_sichern', 'max_anzahl_ordner'}]
    alt = dict(os=os, shutil=shutil, Path=Path, datetime=FesteZeit)
    exec(compile(ast.Module(body=funktionen, type_ignores=[]), 'original_sicherung', 'exec'), alt)
    app = SimpleNamespace()
    hilfe = Sicherung(app)
    app.max_anzahl_ordner = hilfe.max_anzahl_ordner
    with tempfile.TemporaryDirectory(dir=basis / '.lokal') as tmp:
        wurzel = Path(tmp)
        # Änderung: Fehlende/leere Datenbank, echte Beispieldaten, Unterordner,
        # volle Aufbewahrung und Kollision bei identischem Zeitstempel vergleichen.
        for fall in ('fehlt', 'leer', 'beispieldaten', 'unterordner', 'voll', 'kollision'):
            links, rechts = wurzel / (fall + '-alt'), wurzel / (fall + '-neu')
            # Änderung: Künstliche Dateien erhalten gleiche Zeiten für den Metadatenvergleich.
            for ziel in (links, rechts):
                ziel.mkdir()
                (ziel / 'Sicherungen').mkdir()
                if fall != 'fehlt':
                    if fall == 'leer':
                        (ziel / 'Datenbank').mkdir()
                    else:
                        shutil.copytree(daten / 'Datenbank', ziel / 'Datenbank')
                if fall in ('unterordner', 'kollision'):
                    (ziel / 'Datenbank/Unterordner').mkdir()
                    (ziel / 'Datenbank/Unterordner/test.txt').write_text('lokaler Test', encoding='utf-8')
                    os.utime(ziel / 'Datenbank/Unterordner/test.txt', (1000, 1000))
                if fall == 'voll':
                    for n in range(12):
                        p = ziel / 'Sicherungen' / str(n)
                        p.mkdir()
                        (p / 'test.txt').write_text(str(n), encoding='utf-8')
                        os.utime(p / 'test.txt', (1000, 1000))
                        os.utime(p, (1000 + n, 1000 + n))
            alt.update(ordner_datenbank=str(links / 'Datenbank'), ordner_sicherungen=str(links / 'Sicherungen'))
            app.ordner_datenbank, app.ordner_sicherungen = str(rechts / 'Datenbank'), str(rechts / 'Sicherungen')
            for versuch in range(2 if fall == 'kollision' else 1):
                fehler = []
                for aufruf in (alt['db_sichern'], hilfe.db_sichern):
                    try:
                        with patch('anwendung.sicherung.datetime', FesteZeit):
                            aufruf('Pruefung')
                        fehler.append(None)
                    except Exception as exc:
                        fehler.append(type(exc))
                assert fehler[0] == fehler[1]
                assert fehler[0] is (FileExistsError if fall == 'kollision' and versuch == 1 else None)
                assert bestand(links) == bestand(rechts)
            if fall == 'voll':
                assert len(list((rechts / 'Sicherungen').iterdir())) == 9
                assert all(not (rechts / 'Sicherungen' / str(n)).exists() for n in range(4))
        # Änderung: Abweichende Höchstzahl und fremde Dateien unverändert behandeln.
        for ziel in (links, rechts):
            (ziel / 'Sicherungen/fremde-datei.txt').write_text('erhalten', encoding='utf-8')
            os.utime(ziel / 'Sicherungen/fremde-datei.txt', (1000, 1000))
        alt['max_anzahl_ordner'](str(links / 'Sicherungen'), 0)
        hilfe.max_anzahl_ordner(str(rechts / 'Sicherungen'), 0)
        assert bestand(links) == bestand(rechts)
        assert (rechts / 'Sicherungen/fremde-datei.txt').exists()
    assert bestand(daten) == originalbestand


if __name__ == '__main__':
    try:
        # Änderung: Beispieldaten und Fehlerdetails ausschließlich lokal halten.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Sicherung: Alle lokalen Inhalts-, Aufbewahrungs- und Fehlervergleiche bestanden.')
    except Exception as fehler:
        print('Sicherungsprüfung nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)
