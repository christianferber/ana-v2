"""Änderung 2.040: Bestehender deaktivierter Statistikbereich mit eigenem Anzeigezustand."""
import os
import pandas as pd
import plotly.graph_objects as go
from nicegui import ui


class StatistikOberflaeche:
    # Änderung: Gemeinsame Abnehmerdaten und Abrechnungspfade auf der Anwendung belassen.
    def __init__(self, anwendung):
        self.anwendung = anwendung

    def abnehmer_auslesen(self):
        # Änderung 2.040: Bisherigen Statistikablauf über Ansicht und Anwendung ausführen.
        abnehmer_liste = []
        for row in self.anwendung.abnehmer_db:
            abnehmer_kurz_row = row["Ident"] + " | " + row["Name"] + " " + row["Vorname"]
            abnehmer_liste.append(abnehmer_kurz_row)
        return abnehmer_liste

    def dropdown_vergleichswerte_update(self):
        # Änderung 2.040: Bisherigen Statistikablauf über Ansicht und Anwendung ausführen.
        vergleichswerte_mapping = {
            "Abrechnung": ["Mindestvertragssume", "Mindestvertragsleistung", "verbrauchte kWh"],
        }
        self.dropdown_vergleichswerte.set_options(vergleichswerte_mapping.get(self.dropdown_bereich.value, []))
        self.anwendung.lade_diagramm()

    def lade_diagramm(self):
        # Änderung 2.040: Bisherigen Statistikablauf über Ansicht und Anwendung ausführen.
        if not self.dropdown_abnehmer.value or not self.dropdown_vergleichswerte.value:
            return

        ident = self.dropdown_abnehmer.value.split(" | ")[0]  # Nur die Ident extrahieren
        spalten_name = self.dropdown_vergleichswerte.value

        jahre = []
        werte = []

        for eintrag in os.listdir(self.anwendung.ordner_abrechnungen):
            if eintrag.startswith("Abrechnung-"):
                jahr = eintrag.split("-")[1]
                csv_datei = os.path.join(self.anwendung.ordner_abrechnungen, eintrag, f"Abrechnung-{jahr}.csv")

                if os.path.isfile(csv_datei):
                    df = pd.read_csv(csv_datei, sep=';', encoding='cp1252')

                    row = df[df["Ident"] == ident]
                    if not row.empty and spalten_name in df.columns:
                        jahre.append(int(jahr))
                        werte.append(row[spalten_name].iloc[0])

        self.anwendung.zeichne_diagramm(jahre, werte)

    def zeichne_diagramm(self, jahre, werte):
        # Änderung 2.040: Bisherigen Statistikablauf über Ansicht und Anwendung ausführen.
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=jahre, y=werte, mode='lines+markers', name='Wertentwicklung'))
        fig.update_layout(xaxis_title="Jahre", yaxis_title="Wert", title="Abrechnungsstatistik")
        self.plot.update()

    def statistik_ui(self):
        # Änderung 2.040: Bisherigen Statistikablauf über Ansicht und Anwendung ausführen.

        with ui.row():
            self.dropdown_abnehmer = ui.select(
                self.anwendung.abnehmer_auslesen(),
                label='Anschlussnehmer',
                on_change=lambda _: self.anwendung.lade_diagramm()
            ).classes('w-64')

        with ui.row():
            self.dropdown_bereich = ui.select(
                ['Abrechnung'],
                label='Bereich',
                on_change=self.anwendung.dropdown_vergleichswerte_update
            ).classes('w-48')

        with ui.row():
            self.dropdown_vergleichswerte = ui.select(
                [],
                label='Vergleichswert',
                on_change=lambda _: self.anwendung.lade_diagramm()
            ).classes('w-64')
            self.anwendung.dropdown_vergleichswerte_update()  # initiale Befüllung

        with ui.row():
            self.plot = ui.plotly(go.Figure())
