"""Änderung nach 2.049: Lesende Verbrauchsübersicht über gespeicherte Jahresabrechnungen."""
import csv
import math
from pathlib import Path
import re

import plotly.graph_objects as go
from nicegui import ui


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
        self.lade_diagramm()

    def lade_diagramm(self):
        # Änderung: Beide Größen aus derselben Jahresdatei gemeinsam in kWh darstellen.
        ident = self.dropdown_abnehmer.value
        fig = go.Figure()
        hinweis = 'Bitte einen Abnehmer auswählen.'
        if ident is not None:
            jahre, verbrauch, minimum, fehler = verbrauchswerte_lesen(
                self.anwendung.ordner_abrechnungen, ident)
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
                          yaxis_title='Verbrauch / Mindestabnahme (kWh)', template='plotly_white',
                          margin={'l': 65, 'r': 20, 't': 60, 'b': 95},
                          legend={'orientation': 'h', 'y': -0.25}, separators=',.')
        self.plot.figure = fig
        self.plot.update()
        self.hinweis.set_text(hinweis)

    def aufbauen(self):
        # Änderung: Zwei Dropdowns oben; Diagramm passt sich an verfügbare Breite an.
        with ui.column().classes('w-full ana-statistik'):
            ui.label('Statistik').classes('text-h5')
            with ui.row().classes('w-full gap-4 items-end'):
                self.dropdown_statistik = ui.select(['Verbrauchsübersicht'], value='Verbrauchsübersicht',
                                                   label='Statistik', on_change=lambda _: self.lade_diagramm()).classes('w-72 max-w-full')
                self.dropdown_abnehmer = ui.select({}, label='Abnehmer (Ident | Name Vorname)',
                                                  on_change=lambda _: self.lade_diagramm(),
                                                  with_input=True).classes('w-96 max-w-full')
            self.hinweis = ui.label('').classes('text-sm text-slate-600')
            self.plot = ui.plotly(go.Figure()).classes('w-full').style('height: 480px')
        self.aktualisieren()
