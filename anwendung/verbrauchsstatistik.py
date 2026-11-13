"""Änderung nach 2.049: Lesende Verbrauchsübersicht über gespeicherte Jahresabrechnungen."""
import csv
import math
from pathlib import Path
import re

import plotly.graph_objects as go
from nicegui import ui
# Änderung nach 2.049: Kostenvergleich allgemein und verbraucherspezifisch anbieten.
from anwendung.kostenstatistik import Kostenstatistik


def verbrauchswerte_lesen(ordner, ident):
    # Änderung: Jahresdateien sortiert lesen; fehlende Werte niemals als Null darstellen.
    jahre, verbrauch, mindestabnahme = [], [], []
    fehler = 0
    basis = Path(ordner)
    if not basis.is_dir():
        return jahre, verbrauch, mindestabnahme, fehler
    dateien = []
    for verzeichnis in basis.iterdir():
        treffer = re.fullmatch(r'Abrechnung-(\d{4})', verzeichnis.name)
        if verzeichnis.is_dir() and treffer:
            datei = verzeichnis / (verzeichnis.name + '.csv')
            if datei.is_file():
                dateien.append((int(treffer[1]), datei))
    for jahr, datei in sorted(dateien):
        jahre.append(jahr)
        verbrauch.append(None)
        mindestabnahme.append(None)
        try:
            # Änderung: Sowohl UTF-8 als auch bisherige Windows-Dateien unterstützen.
            try:
                inhalt = datei.read_text(encoding='utf-8-sig')
            except UnicodeDecodeError:
                inhalt = datei.read_text(encoding='cp1252')
            zeilen = csv.DictReader(inhalt.splitlines(), delimiter=';')
            if not {'Ident', 'verbrauchte kWh', 'Mindestvertragsleistung'} <= set(zeilen.fieldnames or []):
                fehler += 1
                continue
            treffer = [z for z in zeilen if str(z.get('Ident', '')).strip() == str(ident).strip()]
            if not treffer:
                continue
            if len(treffer) != 1:
                fehler += 1
                continue
            for spalte, ziel in (('verbrauchte kWh', verbrauch), ('Mindestvertragsleistung', mindestabnahme)):
                try:
                    zahl = float(treffer[0][spalte].strip().replace(',', '.'))
                    if not math.isfinite(zahl):
                        raise ValueError('Kein endlicher Wert')
                    ziel[-1] = zahl
                except (ValueError, TypeError, AttributeError):
                    fehler += 1
        except (OSError, UnicodeError, csv.Error):
            # Änderung: Fehlerhafte Jahresdateien dürfen die übrige Übersicht nicht verhindern.
            fehler += 1
    return jahre, verbrauch, mindestabnahme, fehler


class Verbrauchsstatistik:
    # Änderung: Eigener Anzeigezustand; keine Änderung an Abrechnung oder Datenbank.
    def __init__(self, anwendung):
        self.anwendung = anwendung

    def aktualisieren(self):
        # Änderung: Beim Öffnen aktuelle Abnehmer und inzwischen gespeicherte Jahre übernehmen.
        optionen = {str(z['Ident']): f"{z['Ident']} | {z['Name']} {z['Vorname']}"
                    for z in self.anwendung.abnehmer_db}
        bisher = self.dropdown_abnehmer.value
        self.dropdown_abnehmer.set_options(optionen, value=bisher if bisher in optionen else None)
        # Änderung: Allgemeine Übersicht unabhängig von der Verbraucherauswahl aktualisieren.
        self.allgemeine_kostenstatistik.aktualisieren()
        self.lade_diagramm()

    def lade_diagramm(self):
        # Änderung: Beide Einzelstatistiken stets mit derselben Verbraucherauswahl aktualisieren.
        self.kostenstatistik.aktualisieren(self.dropdown_abnehmer.value)
        # Änderung: Beide Größen aus derselben Jahresdatei gemeinsam in kWh darstellen.
        ident = self.dropdown_abnehmer.value
        fig = go.Figure()
        # Änderung nach 2.049: Jahrestabelle aus denselben unveränderten Diagrammwerten aufbauen.
        zeilen = []
        # Änderung: Jahre auch für die verbraucherspezifische Tabelle als Spalten verwenden.
        jahre = []
        hinweis = 'Bitte oben einen Verbraucher auswählen.'
        if ident is not None:
            jahre, verbrauch, minimum, fehler = verbrauchswerte_lesen(
                self.anwendung.ordner_abrechnungen, ident)
            for jahr, wert, mindestwert in zip(jahre, verbrauch, minimum):
                abweichung = wert - mindestwert if wert is not None and mindestwert is not None else None
                prozent = abweichung / mindestwert * 100 if abweichung is not None and mindestwert != 0 else None
                def anzeigen(zahl, nachkommastellen=0):
                    # Änderung: kWh ohne Nachkommastellen anzeigen; nur Prozent behält zwei Stellen.
                    return '–' if zahl is None else f'{zahl:,.{nachkommastellen}f}'.replace(',', '_').replace('.', ',').replace('_', '.')
                zeilen.append({'jahr': jahr, 'verbrauch': anzeigen(wert), 'minimum': anzeigen(mindestwert),
                               'abweichung': anzeigen(abweichung), 'prozent': anzeigen(prozent, 2)})
            for name, werte, farbe in (('Tatsächlicher Verbrauch', verbrauch, '#1761a0'),
                                       ('Mindestabnahme', minimum, '#d97706')):
                fig.add_trace(go.Scatter(x=jahre, y=werte, name=name, mode='lines+markers',
                                        connectgaps=False, line={'color': farbe},
                                        hovertemplate='%{x}: %{y:,.0f} kWh<extra>%{fullData.name}</extra>'))
            vorhanden = any(w is not None for w in verbrauch + minimum)
            hinweis = ('Gespeicherte Jahreswerte; fehlende Werte erscheinen als Lücken.' if vorhanden
                       else 'Für diesen Abnehmer sind keine Verbrauchswerte in den gespeicherten Jahresabrechnungen verfügbar.')
            if fehler:
                hinweis += ' Einige Jahreswerte konnten nicht gelesen werden.'
            fig.update_xaxes(tickmode='array', tickvals=jahre)
        fig.update_layout(title='Verbrauchsübersicht', xaxis_title='Abrechnungsjahr',
                          yaxis_title='Verbrauch / Mindestabnahme', template='plotly_white',
                          margin={'l': 65, 'r': 20, 't': 60, 'b': 95},
                          legend={'orientation': 'h', 'y': -0.25}, separators=',.')
        # Änderung nach 2.049: Null als festen unteren Achsenwert verwenden.
        # Änderung: Einheit direkt an den Achsenwerten statt im Achsentitel anzeigen.
        # Änderung: Auch die kWh-Achsenwerte stets ohne Nachkommastellen darstellen.
        fig.update_yaxes(rangemode='tozero', autorange=True, autorangeoptions={'minallowed': 0}, ticksuffix=' kWh', tickformat=',.0f')
        # Änderung: Unveränderte Jahreswerte drehen: Kennzahlen als Zeilen, Jahre als Spalten.
        self.tabelle.columns = [{'name': 'kennzahl', 'label': 'Kennzahl', 'field': 'kennzahl', 'align': 'left'}]
        self.tabelle.columns += [
            {'name': f'jahr_{jahr}', 'label': str(jahr), 'field': f'jahr_{jahr}', 'align': 'right'}
            for jahr in jahre]
        self.tabelle.rows = [
            # Änderung: Einheiten an vorhandene Werte anhängen; fehlende Werte bleiben ein Strich.
            {'kennzahl': titel, **{f"jahr_{z['jahr']}": z[feld] + einheit if z[feld] != '–' else '–' for z in zeilen}}
            for feld, titel, einheit in [('verbrauch', 'Tatsächlicher Verbrauch', ' kWh'),
                                         ('minimum', 'Mindestabnahme', ' kWh'),
                                         ('abweichung', 'Abweichung absolut', ' kWh'),
                                         ('prozent', 'Abweichung prozentual', ' %')]
        ] if zeilen else []
        self.tabelle.update()
        self.plot.figure = fig
        self.plot.update()
        self.hinweis.set_text(hinweis)

    def aufbauen(self):
        # Änderung: Zwei Bereiche; Verbraucherauswahl über beiden zugehörigen Statistiken.
        with ui.column().classes('w-full ana-statistik'):
            ui.label('Statistik').classes('text-h5')
            with ui.tabs().classes('w-full') as self.bereichsauswahl:
                allgemein = ui.tab('Allgemein')
                verbraucher = ui.tab('Verbraucherspezifisch')
            with ui.tab_panels(self.bereichsauswahl, value=allgemein).classes('w-full'):
                with ui.tab_panel(allgemein).classes('ana-allgemeine-statistik'):
                    self.allgemeine_kostenstatistik = Kostenstatistik(self.anwendung)
                    self.allgemeine_kostenstatistik.aufbauen()
                with ui.tab_panel(verbraucher).classes('ana-verbraucherstatistik'):
                    self.verbraucherbereich_aufbauen()
        self.aktualisieren()

    def verbraucherbereich_aufbauen(self):
        # Änderung: Gemeinsamer Verbraucherfilter vor Verbrauchsübersicht und Kostenvergleich.
        with ui.column().classes('w-full'):
            self.dropdown_abnehmer = ui.select({}, label='Verbraucher (Ident | Name Vorname)',
                                                  on_change=lambda _: self.lade_diagramm(),
                                                  with_input=True).classes('w-96 max-w-full')
            ui.label('Verbrauchsübersicht').classes('text-h6')
            self.hinweis = ui.label('').classes('text-sm text-slate-600')
            self.plot = ui.plotly(go.Figure()).classes('w-full').style('height: 480px')
            # Änderung nach 2.049: Alle Jahreswerte unter dem Graphen ohne Seitenwechsel anzeigen.
            # Änderung: Spalten werden aus den vorhandenen Jahren erstellt; Zeilenschlüssel ist die Kennzahl.
            self.tabelle = ui.table(columns=[], rows=[], row_key='kennzahl',
                                    pagination={'rowsPerPage': 0}).classes('w-full ana-statistik-tabelle')
            self.erklaerung = ui.label('Abweichung = Verbrauch − Mindestabnahme; Prozent bezogen auf die Mindestabnahme. '
                     '„–“ bedeutet fehlender Wert oder Prozentwert bei Mindestabnahme 0.').classes('text-sm text-slate-600')
            # Änderung: Zweite Statistik unter demselben Verbraucherfilter anzeigen.
            self.kostenstatistik = Kostenstatistik(self.anwendung, verbraucherspezifisch=True)
            self.kostenstatistik.aufbauen()
