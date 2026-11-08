"""Änderung 2.041: Jahresauswahl und Speicherdialoge für Buchungsexporte."""
from datetime import datetime
from pathlib import Path
from nicegui import app, ui
import webview


class BuchungsexportOberflaeche:
    # Änderung: Auswahlfelder, Exportfunktionen und Daten bleiben gemeinsam verfügbar.
    def __init__(self, anwendung):
        self.anwendung = anwendung

    async def buchung_datei_speichern(self, content, dateiprefix):
        # Änderung 2.041: Bisherigen Bedienablauf über die aktuelle Anwendung ausführen.
        current_datetime = datetime.now().strftime("%Y-%m-%d")
        dateiname = str(dateiprefix) + "-" + current_datetime + ".csv"
        datei = await app.native.main_window.create_file_dialog(webview.SAVE_DIALOG, directory="%USERPROFILE\\Downloads", allow_multiple=False, save_filename=dateiname)
        if datei != None:
            with open(datei,'w') as f: 
                f.write(content)
                ui.notify(datei + " wurde gespeichert.", type="positive")
        else:
            return

    async def csv_grundgebuehr_speichern(self):
        # Änderung 2.041: Bisherigen Bedienablauf über die aktuelle Anwendung ausführen.
        await self.anwendung.buchung_datei_speichern(self.anwendung.csv_grundgebuehr(),'csv_grundgebuehr')

    async def csv_abschlag_speichern(self):
        # Änderung 2.041: Bisherigen Bedienablauf über die aktuelle Anwendung ausführen.
        if self.anwendung.abschlagsjahr_dropdown.value == None or self.anwendung.quartal_dropdown.value == None:
            ui.notify('Bitte Abschlagsjahr und Quartal auswählen.', type="info")
            return 
        await self.anwendung.buchung_datei_speichern(self.anwendung.csv_abschlag(), "csv_abschlag_" + self.anwendung.quartal_dropdown.value + "_" + self.anwendung.abschlagsjahr_dropdown.value)

    async def csv_abrechnung_lastschrift_speichern(self):
        # Änderung 2.041: Bisherigen Bedienablauf über die aktuelle Anwendung ausführen.
        if self.anwendung.abrechnungsjahr_dropdown.value == None:
            ui.notify('Bitte Abrechnungsjahr auswählen.', type="info")
            return 
        await self.anwendung.buchung_datei_speichern(self.anwendung.csv_abrechnung_lastschrift(), "csv_abrechnung_ls_" + self.anwendung.abrechnungsjahr_dropdown.value)

    async def csv_abrechnung_ueberweisung_speichern(self):
        # Änderung 2.041: Bisherigen Bedienablauf über die aktuelle Anwendung ausführen.
        if self.anwendung.abrechnungsjahr_dropdown.value == None:
            ui.notify('Bitte Abrechnungsjahr auswählen.', type="info")
            return 
        await self.anwendung.buchung_datei_speichern(self.anwendung.csv_abrechnung_ueberweisung(), "csv_abrechnung_üw_" + self.anwendung.abrechnungsjahr_dropdown.value)

    async def csv_rueckv_speichern(self):
        # Änderung 2.041: Bisherigen Bedienablauf über die aktuelle Anwendung ausführen.
        if self.anwendung.rueckvjahr_dropdown.value == None:
            ui.notify('Bitte Rückvergütungsjahr auswählen.', type="info")
            return 
        await self.anwendung.buchung_datei_speichern(self.anwendung.csv_rueckv(), "csv_rückvergütung_" + self.anwendung.rueckvjahr_dropdown.value)

    def dropdowns_einlesen(self):
        # Änderung 2.041: Bisherigen Bedienablauf über die aktuelle Anwendung ausführen.
        jahrliste = []
        if self.anwendung.abschlag_db != []:
            for key in self.anwendung.abschlag_db[0].keys():
                if "Abschlag-" in key:
                    jahrliste.append(key[-4:])
            jahrliste.sort()
            self.anwendung.abschlagsjahr_dropdown.set_options(jahrliste)
        else:
            ui.notify("Abschlag-Datenbank nicht gefüllt.", type="info")
    
        jahrliste = []
        pfad_ordner_abrechnungen = Path(self.anwendung.ordner_abrechnungen)
        for item in pfad_ordner_abrechnungen.iterdir():
            if item.is_dir():
                if item.name[:-4] == 'Abrechnung-':
                    datei_abrechnung = self.anwendung.ordner_abrechnungen + "\\" + item.name + "\\" + "Abrechnung-" + item.name[-4:] + ".csv"
                    if Path(datei_abrechnung).is_file():
                        jahrliste.append(item.name[-4:])
        jahrliste.sort()
        if len(jahrliste) == 0:
            ui.notify("Keine Abrechnungen abgespeichert.", type="info")
        self.anwendung.abrechnungsjahr_dropdown.set_options(jahrliste)

        jahrliste = []
        pfad_ordner_rueckv = Path(self.anwendung.ordner_rueckv)
        for item in pfad_ordner_rueckv.iterdir():
            if item.is_dir():
                if item.name[:-4] == "Rückvergütung-":
                    datei_rueckv = self.anwendung.ordner_rueckv + "\\" + item.name + "\\" + "Rückvergütung-" + item.name[-4:] + ".csv"
                    if Path(datei_rueckv).is_file():
                        jahrliste.append(item.name[-4:])
        jahrliste.sort()
        if len(jahrliste) == 0:
            ui.notify("Keine Rückvergütungen gespeichert.", type="info")
        self.anwendung.rueckvjahr_dropdown.set_options(jahrliste)
