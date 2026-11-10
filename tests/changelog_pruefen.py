"""Änderung 2.039: Changelog-Anzeige und Protokollierung ausschließlich lokal vergleichen."""
import ast
import contextlib
import copy
from datetime import datetime
import io
import locale
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch
import anwendung.changelog_ui as modul
from anwendung.protokollierung import Protokollierung
from anwendung.einstellungen import ini_datei_lesen


class FesteZeit:
    # Änderung: Identische Zeitstempel für den bytegenauen Schreibvergleich verwenden.
    @staticmethod
    def now():
        return datetime(2026, 11, 8, 12, 0, 0)


def pruefen():
    basis = Path(__file__).resolve().parents[1]
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
    logs = list(daten.rglob('ana-change.log'))
    original = {p: p.read_bytes() for p in logs}
    # Änderung: Fehlt ein Beispielprotokoll, lokale Prüfeinträge aus Beispieldaten ableiten.
    from anwendung.datenhaltung import datei_oeffnen
    mitglied = datei_oeffnen(daten / 'Datenbank' / 'db_mitglieder.csv')[0]
    # Änderung: Zusätzliche Änderungsbereiche mit realer Filteranzeige prüfen.
    module = ('MITGLIEDER', 'WARTUNG', 'ABNEHMER', 'ZÄHLER', 'ABSCHLAG', 'RÜCKVERGÜTUNG', 'KONTODATEN', 'ABRECHNUNG', 'EINSTELLUNGEN', 'DATENBANK')
    beispielinhalt = ''.join('08.11.2026 12:00:00 | ' + name + ' | ' + str(mitglied['Ident']) + ' ' + mitglied['Name'] + ' ' + mitglied['Vorname'] + '\n' for name in module).encode(locale.getpreferredencoding(False))

    altbaum = ast.parse((basis.parent / '_Vorlagen' / 'ana' / 'ana.py').read_text(encoding='utf-8-sig'))
    neubaum = ast.parse((basis / 'anwendung' / 'oberflaeche.py').read_text(encoding='utf-8'))
    namen = {'changelog_markdown_ui_refresh', 'change_log', 'change_log_info'}
    alt = dict(Path=Path, datetime=FesteZeit)
    fs = [copy.deepcopy(n) for n in altbaum.body if isinstance(n, ast.FunctionDef) and n.name in namen]
    exec(compile(ast.Module(body=fs, type_ignores=[]), 'original_changelog', 'exec'), alt)
    neu = dict(Path=Path, datetime=FesteZeit)
    fs = [copy.deepcopy(n) for n in neubaum.body if isinstance(n, ast.FunctionDef) and n.name in {'change_log', 'change_log_info'}]
    exec(compile(ast.Module(body=fs, type_ignores=[]), 'aktuelle_protokollierung', 'exec'), neu)
    app = SimpleNamespace(changelog='ana-change.log')
    # Änderung 2.043: Echte ausgelagerte Schreibmethoden über die bisherigen Adapter prüfen.
    neu['protokollierung_hilfe'] = Protokollierung(app)
    ansicht = modul.ChangelogOberflaeche(app)
    alt['changelog'] = neu['changelog'] = app.changelog
    alt['changelog_markdown'] = Mock()
    ansicht.changelog_markdown = Mock()
    alt['filter_toggle'] = SimpleNamespace(value='ALLE')
    ansicht.filter_toggle = SimpleNamespace(value='ALLE')
    neu['changelog_markdown_ui_refresh'] = ansicht.changelog_markdown_ui_refresh
    app.changelog_markdown_ui_refresh = ansicht.changelog_markdown_ui_refresh
    with tempfile.TemporaryDirectory(dir=basis / '.lokal') as tmp:
        a, b = Path(tmp) / 'alt', Path(tmp) / 'neu'
        a.mkdir()
        b.mkdir()
        alt['ordner_logs'], neu['ordner_logs'], app.ordner_logs = str(a), str(b), str(b)
        # Änderung: Fehlende und leere Protokolle sowie echte lokale Inhalte vergleichen.
        for inhalt in (None, b'', beispielinhalt, *original.values()):
            for ordner in (a, b):
                pfad = ordner / app.changelog
                if inhalt is None:
                    pfad.unlink(missing_ok=True)
                else:
                    pfad.write_bytes(inhalt)
            for filterwert in ('ALLE', *module, 'NICHT-VORHANDEN'):
                alt['filter_toggle'].value = ansicht.filter_toggle.value = filterwert
                alt['changelog_markdown_ui_refresh']()
                ansicht.changelog_markdown_ui_refresh()
                assert alt['changelog_markdown'].method_calls == ansicht.changelog_markdown.method_calls
                if inhalt == beispielinhalt and filterwert in module:
                    assert filterwert in ansicht.changelog_markdown.set_content.call_args.args[0]
        # Änderung: Beide unveränderten Schreibfunktionen mit anschließender echter Anzeige prüfen.
        alt['filter_toggle'].value = ansicht.filter_toggle.value = 'ALLE'
        event = dict(data=dict(Ident='1', Name='Test', Vorname='Lokal'), colId='Kommentar', oldValue='alt', newValue='neu')
        for name, args in (('change_log', ('MITGLIEDER', event)), ('change_log_info', ('WARTUNG', 'Lokaler Vergleich'))):
            alt[name](*args)
            # Änderung 2.043: Zeitstempel im neuen Modul identisch festlegen.
            with patch('anwendung.protokollierung.datetime', FesteZeit):
                neu[name](*args)
            assert (a / app.changelog).read_bytes() == (b / app.changelog).read_bytes()
            assert alt['changelog_markdown'].method_calls == ansicht.changelog_markdown.method_calls
    assert original == {p: p.read_bytes() for p in original}


if __name__ == '__main__':
    try:
        # Änderung: Protokollinhalte und Tracebacks ausschließlich lokal halten.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Changelog: Alle Filter, fehlende/leere Dateien, Anzeige und Protokollierung gegen Original bestanden.')
    except Exception as fehler:
        print('Changelog-Prüfung nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)
