"""Änderung 2.040: Deaktivierte Statistik mit ausschließlich lokalen Beispieldaten vergleichen."""
import ast
import contextlib
import copy
import hashlib
import io
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import pandas as pd
import plotly.graph_objects as go
import anwendung.statistik_ui as modul
from anwendung.datenhaltung import datei_oeffnen
from anwendung.einstellungen import ini_datei_lesen


def pruefen():
    basis = Path(__file__).resolve().parents[1]
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
    abrechnungen = daten / 'Abrechnungen'
    dateien = list(abrechnungen.rglob('*.csv'))
    assert dateien
    bestand = {p: hashlib.sha256(p.read_bytes()).digest() for p in dateien}
    baum = ast.parse((basis.parent / '_Vorlagen' / 'ana' / 'ana.py').read_text(encoding='utf-8-sig'))
    namen = {'abnehmer_auslesen', 'dropdown_vergleichswerte_update', 'lade_diagramm', 'zeichne_diagramm'}
    fs = [copy.deepcopy(n) for n in baum.body if isinstance(n, ast.FunctionDef) and n.name in namen]
    alt = dict(os=os, pd=pd, go=go)
    exec(compile(ast.Module(body=fs, type_ignores=[]), 'original_statistik', 'exec'), alt)
    zeilen = datei_oeffnen(daten / 'Datenbank' / 'db_abnehmer.csv')
    app = SimpleNamespace(abnehmer_db=copy.deepcopy(zeilen), ordner_abrechnungen=str(abrechnungen))
    ansicht = modul.StatistikOberflaeche(app)
    alt['abnehmer_db'], alt['ordner_abrechnungen'] = copy.deepcopy(zeilen), str(abrechnungen)
    assert alt['abnehmer_auslesen']() == ansicht.abnehmer_auslesen()
    auswahl = ansicht.abnehmer_auslesen()
    assert auswahl
    for name in ('dropdown_abnehmer', 'dropdown_bereich', 'dropdown_vergleichswerte', 'plot'):
        alt[name] = Mock(value=None)
        setattr(ansicht, name, Mock(value=None))
    # Änderung: Vergleichswertoptionen und anschließenden Ladeaufruf gegen Original prüfen.
    laden_alt = alt['lade_diagramm']
    alt['lade_diagramm'], app.lade_diagramm = Mock(), Mock()
    for bereich in ('Abrechnung', 'Unbekannt', None):
        alt['dropdown_bereich'].value = ansicht.dropdown_bereich.value = bereich
        alt['dropdown_vergleichswerte_update']()
        ansicht.dropdown_vergleichswerte_update()
        assert alt['dropdown_vergleichswerte'].method_calls == ansicht.dropdown_vergleichswerte.method_calls
    assert alt['lade_diagramm'].call_count == app.lade_diagramm.call_count == 3
    alt['lade_diagramm'] = laden_alt
    alt['zeichne_diagramm'], app.zeichne_diagramm = Mock(), Mock()
    # Änderung: Reale lokale CSV-Leseabläufe und bisherige Typbehandlung unverändert vergleichen.
    for abnehmer in (None, auswahl[0], 'nicht-vorhanden | Test'):
        for spalte in (None, 'Mindestvertragssume', 'Mindestvertragsleistung', 'verbrauchte kWh', 'Unbekannt'):
            alt['dropdown_abnehmer'].value = ansicht.dropdown_abnehmer.value = abnehmer
            alt['dropdown_vergleichswerte'].value = ansicht.dropdown_vergleichswerte.value = spalte
            alt['lade_diagramm']()
            ansicht.lade_diagramm()
            assert alt['zeichne_diagramm'].call_args_list == app.zeichne_diagramm.call_args_list
    # Änderung: Zusätzlich Text-Identen aus denselben lokalen Daten verwenden,
    # um den vorhandenen Zweig für gefundene Werte unabhängig von Pandas-Typinferenz zu prüfen.
    lesen = pd.read_csv
    def als_text(*args, **kwargs):
        frame = lesen(*args, **kwargs)
        frame['Ident'] = frame['Ident'].astype(str)
        return frame
    referenz = next(abrechnungen.glob('Abrechnung-*/Abrechnung-*.csv'))
    frame = als_text(referenz, sep=';', encoding='cp1252')
    ident = str(frame['Ident'].iloc[0])
    spalte = next(k for k in frame.columns if k != 'Ident')
    alt['dropdown_abnehmer'].value = ansicht.dropdown_abnehmer.value = ident + ' | lokaler Test'
    alt['dropdown_vergleichswerte'].value = ansicht.dropdown_vergleichswerte.value = spalte
    with patch.object(pd, 'read_csv', side_effect=als_text):
        alt['lade_diagramm']()
        ansicht.lade_diagramm()
    assert alt['zeichne_diagramm'].call_args_list == app.zeichne_diagramm.call_args_list
    assert app.zeichne_diagramm.call_args.args[0]
    # Änderung: Echte Plotly-Figuren erzeugen und Inhalte vergleichen, ohne Diagramme auszugeben.
    zeichnen = next(n for n in fs if n.name == 'zeichne_diagramm')
    exec(compile(ast.Module(body=[zeichnen], type_ignores=[]), 'original_diagramm', 'exec'), alt)
    figuren = []
    def figur():
        ergebnis = go.Figure()
        figuren.append(ergebnis)
        return ergebnis
    ersatz = SimpleNamespace(Figure=figur, Scatter=go.Scatter)
    alt['go'] = ersatz
    with patch.object(modul, 'go', ersatz):
        for jahre, werte in (([], []), ([2024, 2025], [1.5, 2.5])):
            alt['zeichne_diagramm'](jahre, werte)
            ansicht.zeichne_diagramm(jahre, werte)
            assert figuren[-2].to_json() == figuren[-1].to_json()
            assert alt['plot'].method_calls == ansicht.plot.method_calls
    # Änderung: Statistikregister darf durch die Auslagerung nicht aktiviert werden.
    haupt = ast.parse((basis / 'anwendung' / 'oberflaeche.py').read_text(encoding='utf-8'))
    main = next(n for n in haupt.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'statistik_ui' for n in ast.walk(main))
    assert bestand == {p: hashlib.sha256(p.read_bytes()).digest() for p in dateien}


if __name__ == '__main__':
    try:
        # Änderung: Beispieldaten, Diagramminhalte und Tracebacks nicht ausgeben.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Statistik: Auswahl, Vergleichswerte, lokale Abrechnungen, Diagramme und deaktivierter Zustand gegen Original bestanden.')
    except Exception as fehler:
        print('Statistikprüfung nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)
