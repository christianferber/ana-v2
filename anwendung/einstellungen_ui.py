"""Änderung 2.038: Einstellungsoberfläche mit eigenem Eingabe- und Dialogzustand."""
# Änderung: Änderungsprotokoll ergänzen; vorhandene Fachlogik unverändert ausführen.
from anwendung.aenderungsprotokoll import aenderungen_protokollieren
import configparser
from pathlib import Path
from nicegui import app, ui
import webview
from anwendung.einstellungen import ini_datei_schreiben


class EinstellungenOberflaeche:
    # Änderung: Aktuelle Konfiguration und Ladehilfe auf der Anwendung belassen.
    def __init__(self, anwendung):
        self.anwendung = anwendung

    def einstellungen_ui(self):
        # Änderung 2.038: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        self.anwendung.ini_einlesen()
        with ui.dialog() as self.dialog_einstellungen, ui.card():
            ui.label('Betreiberdaten').style('font-size: 120%')
            self.ini_betreiber_name = ui.input(label='Betreiber Name', value=self.anwendung.betreiber_name).props("size=60")
            self.ini_glaeubiger_id = ui.input(label='Gläubiger ID', value=self.anwendung.betreiber_glaeubigerid).props("size=60")
            self.ini_betreiber_iban = ui.input(label='Betreiber IBAN', value=self.anwendung.betreiber_iban).props("size=60")
            self.ini_arbeitspreis = ui.input(label='Wärmepreis (Ct/kWh)', value=self.anwendung.arbeitspreis).props("size=60")
            self.ini_grundgebuehr = ui.input(label='Grundgebühr (€ pro Monat)', value=self.anwendung.grundgebuehr).props("size=60")
            ui.label('')
            ui.label('Programmkonfiguration').style('font-size: 120%')
            self.ini_farbe_spezial = ui.input(label='Farbe für besondere Hervorhebungen (Farbe als Text)', value=self.anwendung.col_special).props("size=60")
            self.ini_farbe_tabelle_edit = ui.input(label='Farbe für editierbare Tabellenzellen (#ABCDEF)', value=self.anwendung.col_cell_mod).props("size=60")
            self.ini_tabelle_pagination = ui.input(label='Anzahl Zeilen pro Tabellenseite', value=self.anwendung.pagination).props("size=60")
            ui.label('Arbeitsordner:')
            with ui.row():
                ui.button("auswählen", icon='folder', on_click=lambda: (self.anwendung.ordner_auswaehlen()))
                ui.button("Auf standard zurücksetzen", icon='folder_special', on_click=lambda: (self.anwendung.ordner_standard()))
            self.ini_arbeitsordner = ui.label(self.anwendung.arbeitsordner)
            with ui.row():
                ui.button("Speichern", icon='save', on_click=lambda: (self.anwendung.ini_speichern())).props('color=' + self.anwendung.speichernbutton)
                ui.button("Abbrechen", icon='close', on_click=self.dialog_einstellungen.close)
        with ui.dialog() as self.dialog_neustart, ui.card():
            ui.label('Der Arbeitsordner wurde geändert. Das Programm wird jetzt automatisch geschlossen. Beim nächsten Programmstart wird die neue Arbeitsordnereinstellung verwendet.')
            ui.button("OK", on_click=app.shutdown)
        self.dialog_einstellungen.open()

    def ordner_standard(self):
        # Änderung 2.038: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        self.ini_arbeitsordner.set_text('')

    async def ordner_auswaehlen(self):
        # Änderung 2.038: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        ordner_pfad = await app.native.main_window.create_file_dialog(webview.FOLDER_DIALOG)
        ordner_pfad = str(ordner_pfad).replace("(","")
        ordner_pfad = str(ordner_pfad).replace(")","")
        ordner_pfad = str(ordner_pfad).replace(",","")
        ordner_pfad = str(ordner_pfad).replace("'","")
        ordner_pfad = str(ordner_pfad).replace("\\\\","\\")
        self.ini_arbeitsordner.set_text(ordner_pfad)

    def ini_speichern(self):
        # Änderung: Tatsächliche Daten-/Dateiänderungen zusätzlich protokollieren.
        with aenderungen_protokollieren(
            self.anwendung, 'EINSTELLUNGEN', 'Einstellungen speichern',
            daten=lambda: {},
            dateien=lambda: (self.anwendung.ini, Path(self.anwendung.arbeitsordner) / self.anwendung.ini_betreiber),
        ):
            # Änderung 2.038: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
            config = configparser.ConfigParser()
            config['Anwendung'] = { 'FarbeSpezial' : self.ini_farbe_spezial.value,
                                    'FarbeTabelleEdit' : self.ini_farbe_tabelle_edit.value,
                                    'TabellenZeilenProSeite' : self.ini_tabelle_pagination.value,
                                    'Arbeitsordner' : self.ini_arbeitsordner.text}
            # Änderung für v2: Nur der Dateizugriff ist ausgelagert; Dialogablauf bleibt bestehen.
            ini_datei_schreiben(self.anwendung.ini, config)
            if self.anwendung.arbeitsordner != self.ini_arbeitsordner.text:
                self.dialog_neustart.open()
            self.dialog_einstellungen.close()

            config_betreiber = configparser.ConfigParser()
            inibetreiberfile = Path(str(self.anwendung.arbeitsordner) + "\\" + self.anwendung.ini_betreiber)

            config_betreiber['Betreiber'] = { 'BetreiberName' : self.ini_betreiber_name.value,
                                    'GlaeubigerID' : self.ini_glaeubiger_id.value,
                                    'BetreiberIBAN' : self.ini_betreiber_iban.value,
                                    'Waermepreis' : self.ini_arbeitspreis.value,
                                    'Grundgebuehr' : self.ini_grundgebuehr.value}

            # Änderung für v2: Betreiberdaten wie bisher nach dem Dialogabschluss speichern.
            ini_datei_schreiben(inibetreiberfile, config_betreiber)

            self.anwendung.ini_einlesen()
