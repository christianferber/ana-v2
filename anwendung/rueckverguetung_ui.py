"""Änderung 2.02: Rückvergütungsoberfläche mit eigenem Bereichszustand.

Berechnungen und Abläufe bleiben erhalten. Gemeinsame Pfade, Einstellungen
und Hilfsfunktionen werden über die übergebene Anwendung gelesen.
"""
# Änderung: Änderungsprotokoll ergänzen; vorhandene Fachlogik unverändert ausführen.
from anwendung.aenderungsprotokoll import aenderungen_protokollieren
import os
from pathlib import Path
import threading

from nicegui import ui
# Änderung: Doppelstarts verhindern und Hintergrundfehler in der Oberfläche melden.
from anwendung.exportsteuerung import export_start_absichern, export_hintergrund_absichern
from anwendung.datenhaltung import datei_oeffnen, datei_speichern
from anwendung.berechnungen import rueckverguetung_vorbereiten, rueckverguetung_berechnen
from anwendung.dokumente import rueckverguetung_word_schreiben, rueckverguetung_pdf_konvertieren
from anwendung.dokumentfelder import mapping_wordfelder


class RueckverguetungOberflaeche:
    # Änderung 2.02: Tabellen und Bedienelemente gehören zu dieser Ansicht.
    def __init__(self, anwendung):
        self.anwendung = anwendung

    def rueckv_jahre_einlesen(self):
        # Änderung 2.02: Bereichszustand liegt auf self.
        self.rueckv_button_einlesen.disable()
        rueckv_jahr_liste = []
        self.rueckv_jahre_erstellbar = []
        self.rueckv_jahre_einlesbar = []
        pfad_ordner_abrechnungen = Path(self.anwendung.ordner_abrechnungen)
        for item in pfad_ordner_abrechnungen.iterdir():
            if item.is_dir():
                if item.name[:-4] == 'Abrechnung-':
                    datei_abrechnung = self.anwendung.ordner_abrechnungen + "\\" + item.name + "\\" + "Abrechnung-" + item.name[-4:] + ".csv"
                    if Path(datei_abrechnung).is_file():
                        rueckv_jahr_liste.append(item.name[-4:])
                        self.rueckv_jahre_erstellbar.append(item.name[-4:])
        pfad_ordner_rueckv = Path(self.anwendung.ordner_rueckv)
        for item in pfad_ordner_rueckv.iterdir():
            if item.is_dir():
                if item.name[:-4] == "Rückvergütung-":
                    datei_rueckv = self.anwendung.ordner_rueckv + "\\" + item.name + "\\" + "Rückvergütung-" + item.name[-4:] + ".csv"
                    if Path(datei_rueckv).is_file():
                        self.rueckv_jahre_einlesbar.append(item.name[-4:])
                        if item.name[-4:] not in rueckv_jahr_liste:
                            rueckv_jahr_liste.append(item.name[-4:])
        rueckv_jahr_liste.sort()
        self.rueckv_jahre_dropdown.set_options(rueckv_jahr_liste)


    def reset_rueckv(self):
        self.rueckv_prozent.value = 0.00
        self.rueckv_datum_beschluss.value = ""
        self.rueckv_button_erstellen.disable()
        self.rueckv_button_einlesen.disable()
        if self.rueckv_jahre_dropdown.value in self.rueckv_jahre_einlesbar:
            self.rueckv_button_einlesen.enable()
            self.rueckv_prozent.disable()
            self.rueckv_datum_beschluss.disable()
            self.rueckv_button_speichern.disable()
        else:
            self.rueckv_button_einlesen.disable()
        if self.rueckv_jahre_dropdown.value in self.rueckv_jahre_erstellbar:
            self.rueckv_button_erstellen.enable()
            self.rueckv_prozent.enable()
            self.rueckv_datum_beschluss.enable()
            self.rueckv_button_speichern.disable()
        self.rueckv_button_download.disable()
        self.rueckv_button_pdf.disable()
        self.rueckv_grid_ui.refresh()



    ###### Muss Abrechnungs-File, nicht Abschlag überprüfen

    def rueckv_tabelle_erstellen(self):
        # Änderung 2.02: Bereichszustand liegt auf self.

        rueckv_tabelle = []
        if self.rueckv_jahre_dropdown.value == None:
            return
        abrechnung_datei = []
        abrechnung_datei = datei_oeffnen(self.anwendung.ordner_abrechnungen + "\\" + "Abrechnung-" + str(self.rueckv_jahre_dropdown.value) + "\\" + "Abrechnung-" + str(self.rueckv_jahre_dropdown.value) + ".csv")
        # Änderung für v2: Reinen Tabellenaufbau ins Berechnungsmodul verlagern.
        rueckv_tabelle = rueckverguetung_vorbereiten(abrechnung_datei, self.rueckv_jahre_dropdown.value)
        # Änderung für v2: Wie bisher gelten anschließend die Steuersätze der letzten Zeile.
        if abrechnung_datei:
            self.rueckv_mwst = abrechnung_datei[-1]["MwSt-Satz"]
            if "Abrechnung ab ZA" in abrechnung_datei[0].keys():
                self.rueckv_mwst2 = abrechnung_datei[-1]["ZA MwSt"]
        rueckv_tabelle = self.rueckv_tabelle_berechnen(rueckv_tabelle)
        self.rueckv_button_speichern.enable()
        self.rueckv_button_download.enable()
        return rueckv_tabelle

    def rueckv_tabelle_berechnen(self, table):
        # Änderung für v2: Leere Tabellen weiterhin ohne Zugriff auf Eingabefelder zurückgeben.
        if table == []:
            return table
        # Änderung für v2: Steuerwerte explizit übergeben; vorhandene Tabellen weiter direkt ändern.
        return rueckverguetung_berechnen(
            table, self.rueckv_prozent.value, self.rueckv_datum_beschluss.value, self.rueckv_mwst,
            self.rueckv_mwst2 if "MwSt bis ZA" in table[0].keys() else None)

    def rueckv_tabelle_on_change(self, event):
        # Änderung: Tatsächliche Daten-/Dateiänderungen zusätzlich protokollieren.
        with aenderungen_protokollieren(
            self.anwendung, 'RÜCKVERGÜTUNG', 'Rückvergütung bearbeiten',
            daten=lambda: {'Rückvergütung': self.rueckv_table},
        ):
            # Änderung 2.02: Bereichszustand liegt auf self.
            if event["newValue"] == None:
                return
            self.anwendung.change_log("RÜCKVERGÜTUNG " + str(self.rueckv_jahre_dropdown.value), event)
            self.rueckv_table[int(event["rowId"])][event["colId"]] = event["newValue"]
            self.rueckv_table = self.rueckv_tabelle_berechnen(self.rueckv_table)

    def rueckv_erstellen(self):
        # Änderung 2.02: Bereichszustand liegt auf self.
        if self.rueckv_jahre_dropdown.value == None or self.rueckv_prozent.value == None or self.rueckv_datum_beschluss.value == "":
            ui.notify("Bitte Jahr, Mwst., Rückvergütungssatz und Beschlussdatum spezifiziern.", type="info")
            return
        self.rueckv_table = self.rueckv_tabelle_erstellen()
        self.rueckv_grid_ui.refresh()
        self.rueckv_button_speichern.enable()

    def rueckv_speichern(self):
        # Änderung 2.02: Bereichszustand liegt auf self.
        self.rueckv_checkbox_ueberschreiben.set_visibility(visible=False)
        if self.rueckv_table == []:
            ui.notify("Bitte erst Rückvergütung erstellen, dann speichern.", type="info")
            return
        ordner_rueckv_aktuell = self.anwendung.ordner_rueckv + "\\" + "Rückvergütung-" + str(self.rueckv_jahre_dropdown.value)
        self.datei_rueckv_aktuell = ordner_rueckv_aktuell + "\\" + "Rückvergütung-" + str(self.rueckv_jahre_dropdown.value) + ".csv"
        pfad_ordner_rueckv_aktuell = Path(ordner_rueckv_aktuell)
        if not pfad_ordner_rueckv_aktuell.exists():
            pfad_ordner_rueckv_aktuell.mkdir()
        if Path(self.datei_rueckv_aktuell).exists():
            self.rueckv_checkbox_ueberschreiben.set_visibility(visible=True)
        self.dialog_rueckv_bestaetigung.open()

    def rueckv_speichern_ja(self):
        # Änderung: Tatsächliche Daten-/Dateiänderungen zusätzlich protokollieren.
        with aenderungen_protokollieren(
            self.anwendung, 'RÜCKVERGÜTUNG', 'Rückvergütung speichern',
            daten=lambda: {},
            dateien=lambda: (self.datei_rueckv_aktuell,),
        ):
            # Änderung 2.02: Bereichszustand liegt auf self.
            if self.rueckv_checkbox_ueberschreiben.visible == True:
                if self.rueckv_checkbox_ueberschreiben.value == True:
                    ui.notify("Bestehende Rückvergütungsdatei überschrieben.", type="info")
                    datei_speichern(self.datei_rueckv_aktuell, self.rueckv_table)
                    self.rueckv_von_db()
                    self.dialog_rueckv_bestaetigung.close()
            else:
                    ui.notify("Rückvergütungsdatei gespeichert.", type="positive")
                    datei_speichern(self.datei_rueckv_aktuell, self.rueckv_table)
                    self.rueckv_von_db()
                    self.dialog_rueckv_bestaetigung.close()


    def rueckv_von_db(self):
        # Änderung 2.02: Bereichszustand liegt auf self.
        datei_rueckv = self.anwendung.ordner_rueckv + "\\" + "Rückvergütung-" + str(self.rueckv_jahre_dropdown.value) + "\\" + "Rückvergütung-" + str(self.rueckv_jahre_dropdown.value) + ".csv"
        self.rueckv_table = datei_oeffnen(datei_rueckv)
        self.rueckv_table = self.anwendung.tablefields_to_dotfloat(self.rueckv_table)
        self.rueckv_grid_ui.refresh()
        self.rueckv_button_speichern.enable()
        self.rueckv_button_download.enable()
        self.rueckv_button_pdf.enable()

    async def csv_komma_rueckv_download(self):
        filename = "Rückvergütung " + self.rueckv_jahre_dropdown.value + ".csv"
        await self.anwendung.komma_datei_speichern(self.rueckv_table, filename)

    def rueckv_columns_erstellen(self, table):
        columns = []

        if table:
            for key in table[0].keys():
                column_element = {}
                column_element["headerName"] = key
                column_element["field"] = key

                # Ident-Spalte schmal machen
                if key == "Ident":
                    column_element["width"] = 90          # feste Breite
                    column_element["minWidth"] = 90
                    column_element["maxWidth"] = 90
                    column_element["flex"] = 0            # darf nicht wachsen
                    column_element["resizable"] = False
                else:
                    column_element["flex"] = 1
                    column_element["minWidth"] = 160

                if key in ("Ident", "Name", "Vorname"):
                    column_element["pinned"] = 'left'

                column_element["filter"] = 'agTextColumnFilter'
                column_element["floatingFilter"] = True
                if key == "Materialumsatz":
                    column_element["editable"] = True
                    column_element["cellStyle"] = {'backgroundColor': self.anwendung.col_cell_mod}
                    column_element["cellEditor"]='agNumberCellEditor'

                columns.append(column_element)

        return columns


    @ui.refreshable
    def rueckv_grid_ui(self):
        # Änderung 2.02: Bereichszustand liegt auf self.
        self.rueckv_grid = ui.aggrid({
            'defaultColDef': {
                'editable': False,
                'resizable': True,
                'wrapHeaderText': True,
                'autoHeaderHeight': True,
            },
            'columnDefs': self.rueckv_columns_erstellen(self.rueckv_table),
            'rowData': self.rueckv_table,
            'domLayout': 'autoHeight',
            'pagination': True,
            'paginationPageSize': self.anwendung.pagination
        }).on(
            'cellValueChanged',
            lambda event: self.rueckv_tabelle_on_change(event.args)
        ).style('height: 100%')


    def rueckverguetung_ui(self):
        # Änderung 2.02: Bereichszustand liegt auf self.
        self.rueckv_table = []
        ui.label('Rückvergütung').classes("text-2xl font-bold")
        with ui.row():
            self.rueckv_jahre_dropdown = ui.select([], label='Jahr der Rückvergütung', on_change=self.reset_rueckv).classes('w-48')
            self.rueckv_prozent = ui.number(label='Rückergütung in %', format='%.2f')
            with ui.input('Datum Beschluss') as date:
                with date.add_slot('append'):
                    ui.icon('edit_calendar').on('click', lambda: menu.open()).classes('cursor-pointer')
                with ui.menu() as menu:
                    self.rueckv_datum_beschluss = ui.date({'from':'2024-01-01', 'to':'2024-12-31'},mask='DD.MM.YYYY').bind_value(date).props('range')
            self.rueckv_button_speichern = ui.button('Speichern', icon='save', on_click=self.rueckv_speichern).props('color=' + self.anwendung.speichernbutton)
            self.rueckv_button_speichern.disable()
        with ui.row():
            self.rueckv_button_erstellen = ui.button('Erstellung Rückvergütung', icon='calculate', on_click=self.rueckv_erstellen)
            self.rueckv_button_erstellen.disable()
            self.rueckv_button_einlesen = ui.button('Rückvergütung von DB einlesen', icon='file_open', on_click=self.rueckv_von_db)
            self.rueckv_button_einlesen.disable()
            self.rueckv_button_download = ui.button('CSV mit Kommas herunterladen', icon='file_download', on_click=self.csv_komma_rueckv_download)
            self.rueckv_button_download.disable()
            self.rueckv_button_pdf = ui.button('Word/PDF-Rückvergütungen erzeugen', icon='picture_as_pdf', on_click=self.rueckv_dateien_erstellen).props('color=red-5')
            self.rueckv_button_pdf.disable()
            self.rueckv_progress_pdf = ui.circular_progress(min=0, max=100, color="black").classes('invisible')
        with ui.dialog() as self.dialog_rueckv_bestaetigung, ui.card():
            self.dialog_rueckv_label01 = ui.label('Möchten Sie die Rückvergütung wirklich speichern?')
            self.rueckv_checkbox_ueberschreiben = ui.checkbox('bestehende Daten überschreiben')
            with ui.row():
                ui.button('Ja', on_click=self.rueckv_speichern_ja)
                ui.button('Nein', on_click=self.dialog_rueckv_bestaetigung.close)
        self.rueckv_grid_ui()

    @export_start_absichern('rueckv_button_pdf', 'rueckv_pdf_background')
    def rueckv_dateien_erstellen(self):
        self.rueckv_word_erstellen()
        self.rueckv_pdf_erstellen()

    def rueckv_word_erstellen(self):
        # Änderung 2.02: Bereichszustand liegt auf self.
        self.ordner_rueckv_word = self.anwendung.ordner_rueckv + "\\" + "Rückvergütung-" + self.rueckv_jahre_dropdown.value + "\\word"
        pfad_ordner_rueckv_word = Path(self.ordner_rueckv_word)
        if not pfad_ordner_rueckv_word.exists():
            pfad_ordner_rueckv_word.mkdir()
        self.anwendung.dateien_in_ordner_loeschen(self.ordner_rueckv_word)
        ordner_rueckv_jahr = self.anwendung.ordner_rueckv + "\\" + "Rückvergütung-" + str(self.rueckv_jahre_dropdown.value)
        datei_rueckv =  ordner_rueckv_jahr + "\\" + "Rückvergütung-" + str(self.rueckv_jahre_dropdown.value) + ".csv"
        pfad_datei_rueckv = Path(datei_rueckv)
        if not pfad_datei_rueckv.exists():
            ui.notify("Bitte erst Rückvergütung für Jahr " + self.rueckv_jahre_dropdown.value + " abspeichern.", type="info")
            return
        dateiname_vorlage = "Vorlage-Rückvergütung-" + str(self.rueckv_jahre_dropdown.value) + ".docx"
        datei_vorlage_rueckv = self.anwendung.ordner_vorlagen + "\\" + dateiname_vorlage
        pfad_datei_vorlage_rueckv = Path(datei_vorlage_rueckv)
        if not pfad_datei_vorlage_rueckv.exists():
            ui.notify("Bitte Datei " + dateiname_vorlage + " in Ordner " + self.anwendung.ordner_vorlagen + " ablegen.", type="info")
            return
        self.rueckv_fuer_pdf = datei_oeffnen(datei_rueckv)
        # Änderung für v2: Vorprüfungen bleiben in der Oberfläche, Serienschleife auslagern.
        rueckverguetung_word_schreiben(self.rueckv_fuer_pdf, datei_vorlage_rueckv,
                                      self.ordner_rueckv_word, self.rueckv_jahre_dropdown.value,
                                      mapping_wordfelder)

    def rueckv_pdf_erstellen(self):
        # Änderung 2.02: Bereichszustand liegt auf self.
        docx_files_found = 0
        self.ordner_rueckv_pdf = self.anwendung.ordner_rueckv + "\\" + "Rückvergütung-" + self.rueckv_jahre_dropdown.value + "\\pdf"
        pfad_ordner_rueckv_pdf = Path(self.ordner_rueckv_pdf)
        if not pfad_ordner_rueckv_pdf.exists():
            pfad_ordner_rueckv_pdf.mkdir()
        word_ordner = os.listdir(self.ordner_rueckv_word)
        for datei in word_ordner:
                if datei.endswith('docx'):
                    docx_files_found = 1
        if docx_files_found == 0:
            return
        self.anwendung.dateien_in_ordner_loeschen(self.ordner_rueckv_pdf)
        self.rueckv_pdf_background = threading.Thread(target=self.rueckv_pdf_process)
        self.rueckv_pdf_background.start()
        self.rueckv_progress_pdf.classes(remove='invisible')

    # PDF-Erzeugung Performance-optimiert (Word wird nur 1x gestartet)

    @export_hintergrund_absichern
    def rueckv_pdf_process(self):
        # Änderung 2.02: Bereichszustand liegt auf self.

        # Änderung für v2: Bestehenden Thread an die ausgelagerte Konvertierung anbinden.
        rueckverguetung_pdf_konvertieren(self.ordner_rueckv_word, self.ordner_rueckv_pdf,
                                        self.rueckv_progress_pdf.set_value)
