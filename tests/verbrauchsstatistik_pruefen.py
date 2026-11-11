"""Änderung nach 2.049: Statistik nur lokal gegen gespeicherte Abrechnungen prüfen."""
import csv
import hashlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from nicegui import ui

from anwendung.datenhaltung import datei_oeffnen
from anwendung.einstellungen import ini_datei_lesen
from anwendung.verbrauchsstatistik import Verbrauchsstatistik, verbrauchswerte_lesen


def pruefen():
    # Änderung: Unabhängige Referenz aus allen Original-Jahresdateien, ohne Inhalte auszugeben.
    basis = Path(__file__).resolve().parents[1]
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner'])
    bestand = {p: hashlib.sha256(p.read_bytes()).digest() for p in daten.rglob('*') if p.is_file()}
    ordner = daten / 'Abrechnungen'
    referenz = {}
    for datei in ordner.glob('Abrechnung-*/Abrechnung-*.csv'):
        jahr = int(datei.stem.removeprefix('Abrechnung-'))
        with datei.open(encoding='cp1252', newline='') as quelle:
            for zeile in csv.DictReader(quelle, delimiter=';'):
                if not {'verbrauchte kWh', 'Mindestvertragsleistung'} <= zeile.keys():
                    continue
                ident = zeile['Ident']
                referenz.setdefault(ident, {})[jahr] = (
                    float(zeile['verbrauchte kWh'].replace(',', '.')),
                    float(zeile['Mindestvertragsleistung'].replace(',', '.')))
    assert referenz
    for ident, erwartet in referenz.items():
        jahre, verbrauch, minimum, fehler = verbrauchswerte_lesen(ordner, ident)
        assert jahre == sorted(set(jahre)) and fehler == 0
        for jahr, werte in erwartet.items():
            index = jahre.index(jahr)
            assert (verbrauch[index], minimum[index]) == werte
    # Änderung: Sortierung, Text-Ident, echte Nullwerte, Lücken und Fehler getrennt prüfen.
    with TemporaryDirectory(dir=basis / '.lokal') as tmp:
        def schreiben(jahr, inhalt):
            ziel = Path(tmp) / ('Abrechnung-' + str(jahr))
            ziel.mkdir()
            (ziel / (ziel.name + '.csv')).write_text(inhalt, encoding='utf-8')
        kopf = 'Ident;verbrauchte kWh;Mindestvertragsleistung\n'
        schreiben(2025, kopf + '007;12,5;0\n')
        schreiben(2023, kopf + '007;0;100\n')
        schreiben(2024, kopf + '008;99;100\n')
        assert verbrauchswerte_lesen(tmp, '007') == ([2023, 2024, 2025], [0, None, 12.5], [100, None, 0], 0)
        schreiben(2026, kopf + '007;NaN;100\n')
        schreiben(2027, 'Falsche;Spalten\n1;2\n')
        schreiben(2028, kopf + '007;1;2\n007;3;4\n')
        jahre, v, m, fehler = verbrauchswerte_lesen(tmp, '007')
        assert fehler == 3 and v[-3:] == [None, None, None] and m[-3:] == [100, None, None]
        assert verbrauchswerte_lesen(Path(tmp) / 'fehlt', '007') == ([], [], [], 0)
    # Änderung: Echte NiceGUI-Komponenten und beide Plotly-Reihen ohne Browserdatenexport prüfen.
    app = SimpleNamespace(abnehmer_db=datei_oeffnen(daten / 'Datenbank/db_abnehmer.csv'),
                          ordner_abrechnungen=str(ordner))
    with ui.column():
        ansicht = Verbrauchsstatistik(app)
        ansicht.aufbauen()
        assert ansicht.dropdown_statistik.value == 'Verbrauchsübersicht'
        assert ansicht.dropdown_abnehmer.value is None
        ident = next(i for i in referenz if i in ansicht.dropdown_abnehmer.options)
        ansicht.dropdown_abnehmer.value = ident
        ansicht.lade_diagramm()
        fig = ansicht.plot.figure
        assert [s.name for s in fig.data] == ['Tatsächlicher Verbrauch', 'Mindestabnahme']
        for jahr, werte in referenz[ident].items():
            index = list(fig.data[0].x).index(jahr)
            assert (fig.data[0].y[index], fig.data[1].y[index]) == werte
        assert all(s.connectgaps is False for s in fig.data)
        app.abnehmer_db = []
        ansicht.aktualisieren()
        assert ansicht.dropdown_abnehmer.value is None and len(ansicht.plot.figure.data) == 0
    assert bestand == {p: hashlib.sha256(p.read_bytes()).digest() for p in daten.rglob('*') if p.is_file()}


if __name__ == '__main__':
    # Änderung: Keine Daten oder Tracebacks mit Beispieldaten an die Werkzeugausgabe geben.
    try:
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Verbrauchsstatistik: Jahreswerte, Auswahl, Diagramme, Lücken und Originalbestand bestanden.')
    except Exception as fehler:
        Path('.lokal/verbrauchsstatistik-fehler.txt').write_text(__import__('traceback').format_exc(), encoding='utf-8')
        print('Verbrauchsstatistik nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)
