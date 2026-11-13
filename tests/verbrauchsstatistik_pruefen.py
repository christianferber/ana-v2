"""Änderung nach 2.049: Statistik nur lokal gegen gespeicherte Abrechnungen prüfen."""
import csv
from decimal import Decimal
import hashlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from nicegui import ui

from anwendung.datenhaltung import datei_oeffnen
from anwendung.einstellungen import ini_datei_lesen
from anwendung.verbrauchsstatistik import Verbrauchsstatistik, verbrauchswerte_lesen
from anwendung.kostenstatistik import kostenwerte_lesen, kostenmatrix_lesen


def pruefen():
    # Änderung: Unabhängige Referenz aus allen Original-Jahresdateien, ohne Inhalte auszugeben.
    basis = Path(__file__).resolve().parents[1]
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner'])
    bestand = {p: hashlib.sha256(p.read_bytes()).digest() for p in daten.rglob('*') if p.is_file()}
    ordner = daten / 'Abrechnungen'
    # Änderung: Kosten aller lokalen Jahresabrechnungen unabhängig vergleichen, keine Inhalte ausgeben.
    for datei in ordner.glob('Abrechnung-*/Abrechnung-*.csv'):
        with datei.open(encoding='cp1252', newline='') as quelle:
            original = list(csv.DictReader(quelle, delimiter=';'))
        erwartet = sorted(original, key=lambda z: Decimal(z['Wärmekosten tats Verbrauch'].replace(',', '.'))
                          - Decimal(z['Mindestvertragssumme'].replace(',', '.')))
        zeilen, fehler = kostenwerte_lesen(datei)
        assert fehler == 0 and len(zeilen) == len(erwartet)
        for zeile, referenzzeile in zip(zeilen, erwartet):
            differenz = (Decimal(referenzzeile['Wärmekosten tats Verbrauch'].replace(',', '.'))
                         - Decimal(referenzzeile['Mindestvertragssumme'].replace(',', '.')))
            assert zeile['ident'] == referenzzeile['Ident']
            assert zeile['differenz'] == f'{differenz:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
            assert zeile['farbe'] == ('text-green-800 bg-green-50' if differenz > 0
                                     else 'text-red-800 bg-red-50' if differenz < 0 else '')
    with TemporaryDirectory(dir=basis / '.lokal') as tmp:
        datei = Path(tmp) / 'kosten.csv'
        datei.write_text('Ident;Name;Vorname;Wärmekosten tats Verbrauch;Mindestvertragssumme\n'
                         '1;Test;A;1000;0\n2;Test;B;0;2\n3;Test;C;2;2\n4;Test;D;NaN;2\n'
                         '5;Test;E;10,25;10,10\n', encoding='utf-8')
        zeilen, fehler = kostenwerte_lesen(datei)
        assert fehler == 1
        assert [z['ident'] for z in zeilen] == ['2', '3', '5', '1', '4']
        assert [z['differenz'] for z in zeilen] == ['-2,00', '0,00', '0,15', '1.000,00', '–']
        assert kostenwerte_lesen(Path(tmp) / 'fehlt') == ([], 1)
        # Änderung: Jahre über Text-Ident verbinden, Namenswechsel und Lücken erhalten.
        alt = Path(tmp) / 'alt.csv'
        alt.write_text('Ident;Name;Vorname;Wärmekosten tats Verbrauch;Mindestvertragssumme\n'
                       '007;Alt;A;12;2\n008;Nur alt;B;0;2\n009;Doppelt;C;1;2\n009;Doppelt;C;3;2\n', encoding='utf-8')
        neu = Path(tmp) / 'neu.csv'
        neu.write_text('Ident;Name;Vorname;Wärmekosten tats Verbrauch;Mindestvertragssumme\n'
                       '007;Neu;A;1;2\n010;Nur neu;D;2;2\n', encoding='utf-8')
        matrix, fehler = kostenmatrix_lesen({2024: alt, 2025: neu})
        assert fehler == 1 and len(matrix) == 4
        assert [z['ident'] for z in matrix] == ['007', '010', '008', '009']
        zeile = matrix[0]
        assert zeile['name'] == 'Neu' and zeile['jahr_2024'] == '10,00' and zeile['jahr_2025'] == '-1,00'
        assert zeile['sort_2024'] == 1000 and zeile['sort_2025'] == -100
        assert matrix[-1]['jahr_2024'] == '–'
        assert kostenmatrix_lesen({}) == ([], 0)
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
        # Änderung: Zwei Bereiche statt Statistik-Dropdown; Einzelansichten zunächst leer.
        assert not hasattr(ansicht, 'dropdown_statistik')
        assert ansicht.kostenstatistik.tabelle.rows == []
        assert ansicht.allgemeine_kostenstatistik.tabelle.rows
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
        # Änderung: Nullbeginn und alle Tabellenwerte unabhängig mit lokalen Jahreswerten vergleichen.
        assert fig.layout.yaxis.autorangeoptions.minallowed == 0
        def formatiert(zahl, stellen=0):
            # Änderung: Ganze kWh unabhängig prüfen; Prozentdarstellung mit zwei Stellen erhalten.
            return f'{zahl:,.{stellen}f}'.replace(',', '_').replace('.', ',').replace('_', '.')
        # Änderung: Einheiten nur an Werten; Kennzahlen bleiben ohne Einheitenzeichen.
        assert [z['kennzahl'] for z in ansicht.tabelle.rows] == [
            'Tatsächlicher Verbrauch', 'Mindestabnahme', 'Abweichung absolut', 'Abweichung prozentual']
        assert fig.layout.yaxis.ticksuffix == ' kWh' and 'kWh' not in fig.layout.yaxis.title.text
        assert fig.layout.yaxis.tickformat == ',.0f'
        # Änderung: Dieselben Zahlen in den gedrehten Tabellenzellen prüfen.
        assert [s['label'] for s in ansicht.tabelle.columns][1:] == [str(j) for j in fig.data[0].x]
        for jahr, (wert, minimum) in referenz[ident].items():
            assert [z[f'jahr_{jahr}'] for z in ansicht.tabelle.rows] == [
                formatiert(wert) + ' kWh', formatiert(minimum) + ' kWh', formatiert(wert - minimum) + ' kWh',
                formatiert((wert - minimum) * 100 / minimum, 2) + ' %' if minimum else '–']
        # Änderung: Nullbasis und fehlende Jahre auch über die echte Tabelle prüfen.
        with TemporaryDirectory(dir=basis / '.lokal') as tmp:
            for jahr, inhalt in [(2023, '007;0;100'), (2024, '008;1;2'), (2025, '007;12,5;0')]:
                ziel = Path(tmp) / f'Abrechnung-{jahr}'
                ziel.mkdir()
                (ziel / f'{ziel.name}.csv').write_text(
                    'Ident;verbrauchte kWh;Mindestvertragsleistung\n' + inhalt + '\n', encoding='utf-8')
            app.ordner_abrechnungen = tmp
            ansicht.dropdown_abnehmer.set_options({'007': 'Testabnehmer'}, value='007')
            ansicht.lade_diagramm()
            assert [ansicht.tabelle.rows[2][f'jahr_{j}'] for j in (2023, 2024, 2025)] == ['-100 kWh', '–', '12 kWh']
            assert list(ansicht.plot.figure.data[0].y) == [0, None, 12.5]
            assert [ansicht.tabelle.rows[3][f'jahr_{j}'] for j in (2023, 2024, 2025)] == ['-100,00 %', '–', '–']
        app.abnehmer_db = []
        ansicht.aktualisieren()
        assert ansicht.dropdown_abnehmer.value is None and len(ansicht.plot.figure.data) == 0
        assert ansicht.tabelle.rows == []
        assert ansicht.kostenstatistik.tabelle.rows == []
        # Änderung: Jahresmatrix und alle Differenzzellen mit lokalen Jahresdateien vergleichen.
        app.ordner_abrechnungen = str(ordner)
        ansicht.aktualisieren()
        kostenansicht = ansicht.allgemeine_kostenstatistik
        assert not hasattr(kostenansicht, 'jahr')
        assert [s['label'] for s in kostenansicht.tabelle.columns][3:] == [
            str(jahr) for jahr in sorted(kostenansicht.dateien)]
        matrix = {z['ident']: z for z in kostenansicht.tabelle.rows}
        alle_ident = set()
        for jahr, datei in kostenansicht.dateien.items():
            zeilen, fehler = kostenwerte_lesen(datei)
            assert fehler == 0
            vorhanden = {z['ident'] for z in zeilen}
            alle_ident.update(vorhanden)
            for z in zeilen:
                assert matrix[z['ident']][f'jahr_{jahr}'] == z['differenz']
                assert matrix[z['ident']]['farben'][f'jahr_{jahr}'] == z['farbe']
            for ident in matrix.keys() - vorhanden:
                assert matrix[ident][f'jahr_{jahr}'] == '–'
        assert set(matrix) == alle_ident
        # Änderung: Jeder verfügbare Verbraucher erhält ausschließlich seine eigene Kostenzeile.
        app.abnehmer_db = datei_oeffnen(daten / 'Datenbank/db_abnehmer.csv')
        ansicht.aktualisieren()
        for ident in ansicht.dropdown_abnehmer.options:
            ansicht.dropdown_abnehmer.value = ident
            ansicht.lade_diagramm()
            assert ansicht.kostenstatistik.tabelle.rows == ([matrix[ident]] if ident in matrix else [])
            # Änderung: Einzelkosten nur mit Jahresspalten, allgemeine Identitätsfelder bleiben erhalten.
            assert all(s['name'].startswith('jahr_') for s in ansicht.kostenstatistik.tabelle.columns)
            assert [s['name'] for s in kostenansicht.tabelle.columns][:3] == ['ident', 'name', 'vorname']
        ansicht.dropdown_abnehmer.value = None
        ansicht.lade_diagramm()
        assert ansicht.kostenstatistik.tabelle.rows == [] and ansicht.tabelle.rows == []
        assert ansicht.allgemeine_kostenstatistik.tabelle.rows == list(matrix.values())
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
