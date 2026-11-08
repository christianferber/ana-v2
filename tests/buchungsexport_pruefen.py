"""Änderung 2.041: Exportbedienung ausschließlich lokal gegen Original vergleichen."""
import ast
import asyncio
import contextlib
import copy
from datetime import datetime
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
import anwendung.buchungsexport_ui as modul
from anwendung.datenhaltung import datei_oeffnen
from anwendung.einstellungen import ini_datei_lesen


class FesteZeit:
    # Änderung: Gleiche Dateinamensvorgabe unabhängig vom Ausführungszeitpunkt prüfen.
    @staticmethod
    def now():
        return datetime(2026, 11, 8, 12, 0, 0)


def pruefen():
    basis = Path(__file__).resolve().parents[1]
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
    baum = ast.parse((basis.parent / '_Vorlagen' / 'ana' / 'ana.py').read_text(encoding='utf-8-sig'))
    namen = {n for n in vars(modul.BuchungsexportOberflaeche) if not n.startswith('__')}
    fs = [copy.deepcopy(n) for n in baum.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in namen]
    alt = dict(Path=Path, datetime=FesteZeit, webview=modul.webview)
    exec(compile(ast.Module(body=fs, type_ignores=[]), 'original_exportbedienung', 'exec'), alt)
    app = SimpleNamespace(ordner_abrechnungen=str(daten / 'Abrechnungen'), ordner_rueckv=str(daten / 'Rückvergütungen'),
                          abschlag_db=datei_oeffnen(daten / 'Datenbank' / 'db_abschlag.csv'))
    ansicht = modul.BuchungsexportOberflaeche(app)
    alt.update(vars(app))
    for name in ('abschlagsjahr_dropdown', 'abrechnungsjahr_dropdown', 'rueckvjahr_dropdown', 'quartal_dropdown'):
        alt[name] = Mock(value=None)
        setattr(app, name, Mock(value=None))
    ui_alt, ui_neu = Mock(), Mock()
    alt['ui'] = ui_alt
    with patch.object(modul, 'ui', ui_neu):
        # Änderung: Jahreslisten aus tatsächlichen lokalen Beispielordnern vergleichen.
        alt['dropdowns_einlesen']()
        ansicht.dropdowns_einlesen()
        for name in ('abschlagsjahr_dropdown', 'abrechnungsjahr_dropdown', 'rueckvjahr_dropdown'):
            assert alt[name].method_calls == getattr(app, name).method_calls
        assert ui_alt.notify.call_args_list == ui_neu.notify.call_args_list
        # Änderung: Fehlende und vollständige Auswahlen für jede Exportart vergleichen.
        async def auswahl():
            speichern_alt, speichern_neu = AsyncMock(), AsyncMock()
            alt['buchung_datei_speichern'], app.buchung_datei_speichern = speichern_alt, speichern_neu
            for name in ('csv_grundgebuehr', 'csv_abschlag', 'csv_abrechnung_lastschrift', 'csv_abrechnung_ueberweisung', 'csv_rueckv'):
                alt[name] = Mock(return_value='lokaler CSV-Test')
                setattr(app, name, Mock(return_value='lokaler CSV-Test'))
                for jahr, quartal in ((None, None), ('2026', None), (None, 'Q1'), ('2026', 'Q1')):
                    for feld in ('abschlagsjahr_dropdown', 'abrechnungsjahr_dropdown', 'rueckvjahr_dropdown'):
                        alt[feld].value = getattr(app, feld).value = jahr
                    alt['quartal_dropdown'].value = app.quartal_dropdown.value = quartal
                    await alt[name + '_speichern']()
                    await getattr(ansicht, name + '_speichern')()
                    assert speichern_alt.call_args_list == speichern_neu.call_args_list
                    assert ui_alt.notify.call_args_list == ui_neu.notify.call_args_list
                    assert alt[name].call_args_list == getattr(app, name).call_args_list
        asyncio.run(auswahl())
    # Änderung: Echten CSV-Inhalt aus lokalen Beispieldaten nur in temporären Zielen speichern.
    from tests.buchungsvorlagen_pruefen import umgebung_laden
    umgebung = umgebung_laden(False, daten)
    inhalt = umgebung['csv_grundgebuehr']()
    async def dialoge():
        with tempfile.TemporaryDirectory(dir=basis / '.lokal') as tmp:
            datei = Path(tmp) / 'export.csv'
            for rueckgabe in (None, str(datei)):
                links = SimpleNamespace(native=SimpleNamespace(main_window=SimpleNamespace(create_file_dialog=AsyncMock(return_value=rueckgabe))))
                rechts = SimpleNamespace(native=SimpleNamespace(main_window=SimpleNamespace(create_file_dialog=AsyncMock(return_value=rueckgabe))))
                alt['app'] = links
                alt['ui'] = Mock()
                ui_neu = Mock()
                # Änderung: Die Original-Speicherfunktion nach dem Auswahltest erneut laden.
                funktion = next(n for n in fs if n.name == 'buchung_datei_speichern')
                exec(compile(ast.Module(body=[funktion], type_ignores=[]), 'original_speicherdialog', 'exec'), alt)
                await alt['buchung_datei_speichern'](inhalt, 'csv_grundgebuehr')
                vorher = datei.read_bytes() if datei.exists() else None
                with patch.object(modul, 'app', rechts), patch.object(modul, 'ui', ui_neu), patch.object(modul, 'datetime', FesteZeit):
                    await ansicht.buchung_datei_speichern(inhalt, 'csv_grundgebuehr')
                assert vorher == (datei.read_bytes() if datei.exists() else None)
                assert links.native.main_window.create_file_dialog.call_args_list == rechts.native.main_window.create_file_dialog.call_args_list
                assert alt['ui'].notify.call_args_list == ui_neu.notify.call_args_list
    asyncio.run(dialoge())


if __name__ == '__main__':
    try:
        # Änderung: Keine Exportinhalte, Kontodaten oder Tracebacks ausgeben.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Exportbedienung: Jahreslisten, Auswahlprüfungen, Dateinamen, Speichern und Abbruch gegen Original bestanden.')
    except Exception as fehler:
        print('Exportbedienungsprüfung nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)
