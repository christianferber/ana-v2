"""Änderung 2.035: Mitgliederoberfläche mit eigenem Tabellen- und Dialogzustand."""
# Änderung: Änderungsprotokoll ergänzen; vorhandene Fachlogik unverändert ausführen.
from anwendung.aenderungsprotokoll import aenderungen_protokollieren
from anwendung.datenhaltung import import_csv_inhalt, check_ordner_exists, datei_speichern
from nicegui import events, ui
# Änderung: Listenexporte sperren und Fehler über den UI-Kontext zurückmelden.
from anwendung.exportsteuerung import export_start_absichern, export_hintergrund_absichern
import threading
import time
from io import StringIO
import re
import os
from pathlib import Path
from datetime import datetime
from mailmerge import MailMerge
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT
from docx.shared import Inches
from docx.shared import Pt
from docx.oxml import OxmlElement
import pythoncom


class MitgliederOberflaeche:
    # Änderung: Gemeinsame Daten stets über die Anwendung lesen.
    def __init__(self, anwendung):
        self.anwendung = anwendung
        self.mitglieder_changes = []

    def mitglieder_label_ui(self, label):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        ui.label(label).style('font-size:100%')

    def dialog_wartung(self):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        # Wartungsdaten werden in einem Dictlist bespeichert. Zeile 1 enthält die Ident-Nr. 0-99. Bei Ident-Nr. 0 steht das Datum für den Eintrag. Bei den anderen Ident-Nr. die Einträge für den jeweiligen Anschluss
        columns = []
        table = []
        row_data = self.anwendung.mitglieder_selected_row

        if not row_data:
            ui.notify("Bitte Zeile in Tabelle selektieren.", type="info")
            return

        if row_data["Ident"] == "":
            ui.notify(
                "Bitte Zeile mit bestehender Ident/Anschluss-Nr. auswählen.",
                type="info"
            )
            return

        if self.anwendung.db_datei_oeffnen(self.anwendung.db_wartung)[0] != 'file not found':
            self.anwendung.wartung_db = self.anwendung.db_datei_oeffnen(self.anwendung.db_wartung)
        else:
            self.anwendung.wartung_db.append({})
            for ident in range(0,99):
                self.anwendung.wartung_db[0][str(ident)] = ""
            self.anwendung.db_datei_speichern(self.anwendung.db_wartung, self.anwendung.wartung_db)

        def ist_datum_format(string):
            try:
                # Versuch, den String ins gewünschte Format zu parsen
                datetime.strptime(string, "%d.%m.%Y")
                return True
            except ValueError:
                # Falls ein Fehler auftritt, ist es kein gültiges Datum im Format
                return False

        def wartung_grid_update():
            temp_wartung = []
            for row in self.anwendung.wartung_db:
                temp_wartung_row = {}
                if ist_datum_format(row["0"]) and str(row[row_data["Ident"]]) != "" and str(row[row_data["Ident"]]) != "None":
                    temp_wartung_row['Datum'] = row["0"]
                    temp_wartung_row['Wartungseintrag'] = row[row_data["Ident"]].replace("\\n", "\n")
                    temp_wartung.append(temp_wartung_row)
            temp_wartung.sort(key=lambda x: datetime.strptime(x["Datum"], "%d.%m.%Y"), reverse=True)
            columns = [
                {"haederName": "Datum", "field": "Datum", "maxWidth": "150"},
                {"headerName": "Wartungseintrag", "field": "Wartungseintrag", 'cellStyle': {'whiteSpace': 'pre-wrap'}}
            ] 
            self.wartung_grid.options['columnDefs'] = columns
            self.wartung_grid.options['rowData'] = temp_wartung
            self.wartung_grid.options['rowSelection'] = 'multiple'
            self.wartung_grid.options['pagination'] = 'true'
            self.wartung_grid.options['paginationPageSize'] = self.anwendung.pagination
            self.wartung_grid.options['alwaysShowHorizontalScroll'] = 'true'
            self.wartung_grid.options['fullWidthCellRenderer'] = 'fullWidthCellRenderer'
            self.wartung_grid.update()


        def wartung_eintrag_neu_speichern(datum, eintrag):
            wartung_neu = {}
            datum_gefunden = 0
            # Überprüfen, ob Datumsformat passt
            if ist_datum_format(datum):
                for item in self.anwendung.wartung_db:
                    # Überprüfen, ob Datum schon vorhanden ist
                    if item["0"] == datum:
                        datum_gefunden = 1
                        # Überprüfen, ob Eintrag für Ident leer ist
                        if item[row_data["Ident"]] == "":
                            item[row_data["Ident"]] = eintrag
                        else:
                            ui.notify("Eintrag für dieses Datum bereits vorhanden. Bitte Änderung durchführen.", type="info")
                # Neuer Eintrag, wenn Datum nicht vorhanden
                if datum_gefunden == 0:
                    wartung_neu["0"] = datum
                    # Einträge mit leer befüllen statt None, es muss aber zuerst mit leer befüllt werden, dann mit dem Wert, da sonst die Reihenfolge nicht passt
                    for ident in range(0,99):
                        if str(ident) != "0":
                            wartung_neu[str(ident)] = ""
                    wartung_neu[row_data["Ident"]] = eintrag
                if wartung_neu != {}:
                    self.anwendung.wartung_db.append(wartung_neu)
                loginfo = 'Ident: ' + str(row_data["Ident"]) + ' ' + row_data["Name"] + ' ' + row_data["Vorname"] + ' ::: Datum ' + str(datum) + ' ===> neuer Eintrag: ' + eintrag.replace("\n","\\n")
                self.anwendung.change_log_info('WARTUNG', loginfo)
                self.anwendung.db_datei_speichern(self.anwendung.db_wartung, self.anwendung.wartung_db)
                wartung_grid_update()
                self.dialog_wartung_neu.close()
            else:
                ui.notify('Bitte Datum im Format DD.MM.YYYY eingeben.', type="info")

        def wartung_eintrag_geaendert_speichern(eintrag):
            for item in self.anwendung.wartung_db:
                if item["0"] == self.anwendung.wartung_selected_row["Datum"]:
                    item[row_data["Ident"]] = eintrag
            loginfo = 'Ident: ' + str(row_data["Ident"]) + ' ' + row_data["Name"] + ' ' + row_data["Vorname"] + ' ::: Datum ' + str(self.anwendung.wartung_selected_row["Datum"]) + ' ===> Eintrag geändert: ' + eintrag.replace("\n","\\n")
            self.anwendung.change_log_info('WARTUNG', loginfo)
            self.anwendung.db_datei_speichern(self.anwendung.db_wartung, self.anwendung.wartung_db)
            wartung_grid_update()
            self.dialog_wartung_aendern.close()

        def wartung_eintrag_neu():

            datum_aktuell = datetime.now().strftime("%d.%m.%Y")

            def update_datum(e):
                # Datum in das gewünschte Format konvertieren
                self.datum_auswahl = datetime.strptime(e.value, '%Y-%m-%d').strftime('%d.%m.%Y')
                input_datum.value = self.datum_auswahl  # Eingabefeld aktualisieren


            with ui.dialog() as self.dialog_wartung_neu:
                with ui.card().style("width: 100%; height: 400px;"):
                    ui.button('', icon='close', on_click=self.dialog_wartung_neu.close).classes('absolute top-3 right-3')
                    with ui.row():
    #                    input_datum = ui.input("Datum").style('width: 200px')
                        with ui.input('Datum', value=datum_aktuell).style("width: 250px;") as input_datum:
                            with input_datum.add_slot('append'):
                                ui.icon('edit_calendar').on('click', lambda: date_menu.open()).classes('cursor-pointer')

                            # Menü mit Kalenderauswahl
                            with ui.menu() as date_menu:
                                ui.date(
                                    value=datetime.now().strftime('%d.%m.%Y'),  # ISO-Format für ui.date
                                    on_change=update_datum  # Callback für Änderungen
                                ).props(f"min-date={datetime.now().strftime('%Y-%m-%d')}")  # Nur zukünftige Daten erlauben  
                    with ui.row():
                        input_wartung = ui.textarea(label='Wartungsdaten').style('width: 400px')
                    with ui.row():
                        ui.button("Speichern", icon='save', on_click=lambda: wartung_eintrag_neu_speichern(input_datum.value, input_wartung.value)).props('color=' + self.anwendung.speichernbutton)
            self.dialog_wartung_neu.open()      

        def wartung_eintrag_aendern():

            if not self.anwendung.wartung_selected_row:
                ui.notify("Bitte Wartungseintrag auswählen", type="info")
                return

            wartung_data = self.anwendung.wartung_selected_row
            with ui.dialog() as self.dialog_wartung_aendern:
                with ui.card().style("width: 100%; height: 400px;"):
                    ui.button('', icon='close', on_click=self.dialog_wartung_aendern.close).classes('absolute top-3 right-3')
                    with ui.row():
                        ui.label("Datum: " + wartung_data["Datum"])
                    with ui.row():
                        input_wartung = ui.textarea(label='Wartungsdaten',value=wartung_data["Wartungseintrag"]).style('width: 400px')
                    with ui.row():
                        ui.button("Speichern", icon='save', on_click=lambda: wartung_eintrag_geaendert_speichern(input_wartung.value)).props('color=' + self.anwendung.speichernbutton)
            self.dialog_wartung_aendern.open()



        def loeschen_bestaetigen(wartung_data, dialog):
            """
        Löscht den ausgewählten Wartungseintrag für die aktuelle Ident.
        
        Parameters:
            wartung_data: dict
                Die aktuell ausgewählte Zeile im Wartungs-Grid.
            dialog: ui.dialog
                Referenz auf den geöffneten Dialog, damit er geschlossen werden kann.
        """

            ident = self.anwendung.mitglieder_selected_row["Ident"]  # aktuelle Mitglieds-ID

            # Wartungseintrag löschen
            for item in self.anwendung.wartung_db:
                if item["0"] == wartung_data["Datum"]:
                    item[ident] = ""

            # Log-Eintrag erstellen
            loginfo = (
                f"Ident: {ident} "
                f"{self.anwendung.mitglieder_selected_row['Name']} {self.anwendung.mitglieder_selected_row['Vorname']} "
                f"::: Datum {wartung_data['Datum']} ===> Eintrag gelöscht: "
                f"{wartung_data.get('Wartungseintrag', '').replace(chr(10),'\\n')}"
            )
            self.anwendung.change_log_info('WARTUNG', loginfo)

            # Daten speichern
            self.anwendung.db_datei_speichern(self.anwendung.db_wartung, self.anwendung.wartung_db)

            # Grid aktualisieren
            wartung_grid_update()

            # Dialog schließen
            dialog.close()


        def wartung_eintrag_loeschen():

            if not self.anwendung.wartung_selected_row:
                ui.notify("Bitte Wartungseintrag auswählen", type="info")
                return

            wartung_data = self.anwendung.wartung_selected_row

            with ui.dialog() as dialog_wartung_loeschen:
                with ui.card():
                    ui.label(
                        f"Möchten Sie den Eintrag vom {wartung_data['Datum']} wirklich löschen?"
                    )
                    with ui.row():
                        ui.button(
                            "Ja",
                            on_click=lambda: loeschen_bestaetigen(wartung_data, dialog_wartung_loeschen)
                        ).props('color=negative')
                        ui.button("Nein", on_click=dialog_wartung_loeschen.close)
            dialog_wartung_loeschen.open()


        def wartung_row_selected(event):
            self.anwendung.wartung_selected_row = event.args['data']

        # Hauptteil bei Wartung

        if row_data == None:
            ui.notify("Bitte Zeile in Tabelle selektieren.", type="info")
            return

        with ui.dialog().style("width: 800px; max-width: none") as dialog:
            with ui.card().style("width: 800px"):

                ui.button('', icon='close', on_click=dialog.close).classes('absolute top-3 right-3')
                with ui.row():
                    ui.label('Wartungsprotokoll').style("font-size: 24px; font-weight: bold;")
                with ui.row():
                    ui.label("Anschluss Nr. " + row_data["Ident"])
                with ui.row():
                    ui.label("aktueller Anschlussnehmer: " + row_data["Name"] + " " + row_data["Vorname"])
                with ui.row():
                    ui.button("Neu", icon='add_circle', on_click=wartung_eintrag_neu)
                    ui.button("Ändern", icon='edit', on_click=wartung_eintrag_aendern)
                    ui.button("Löschen", icon='delete', on_click=wartung_eintrag_loeschen)
                with ui.row():
                    self.wartung_grid = ui.aggrid({
                        'defaultColDef': {'flex': 1, 'editable': False, 'resizable': True, 'wrapHeaderText': True, 'autoHeaderHeight': True, 'wrapText': True, 'autoHeight': True},
                        'columnDefs': columns,
                        'rowData': table,
                        'domLayout': 'autoHeight', 
                    }).on('cellClicked', wartung_row_selected).style('height: 100%; width: 500px')                
                wartung_grid_update()

        if row_data["Ident"] != "":
            dialog.open()
        else:
            ui.notify("Bitte Zeile mit bestehender Ident/Anschluss-Nr. auswählen.", type="info")

    def anschluss_aendern(self):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.

        row_auswahl = self.anwendung.mitglieder_selected_row

        if not row_auswahl:
            ui.notify("Bitte zuerst einen Eintrag auswählen.", type="info")
            return

        if row_auswahl["Ident"] == "":
            ui.notify(
                "Bitte Zeile mit bestehender Ident/Anschluss-Nr. auswählen.",
                type="info"
            )
            return

        def aenderung_speichern():
            # Änderung: Tatsächliche Daten-/Dateiänderungen zusätzlich protokollieren.
            with aenderungen_protokollieren(
                self.anwendung, 'MITGLIEDER', 'Anschlussnehmer wechseln',
                daten=lambda: {'Mitglieder': self.anwendung.mitglieder_db},
            ):
                neuer_anschluss_lnr = (
                    neuer_anschlussnehmer.value.split('|')[0].strip()
                )

                keylist = [
                    "MAC-Adresse LAN Modul Dezimal",
                    "MAC-Adresse LAN Modul Hex",
                    "Zählernummer",
                    "MAC Adresse ONU",
                    "F-Nr.",
                    "Berechnete Leistung (KW)",
                    "Leistung Übergabestation (KW)"
                ]

                anschluss_valide = False
                neuer_name = ""
                neuer_vorname = ""

                # Neuer Anschlussnehmer
                for row in self.anwendung.mitglieder_db:
                    if str(row["Laufende Nummer"]) == str(neuer_anschluss_lnr):
                        if row["Ident"] == "":
                            row["Ident"] = row_auswahl["Ident"]
                            for key in keylist:
                                row[key] = row_auswahl[key]
                            neuer_name = row["Name"]
                            neuer_vorname = row["Vorname"]
                            anschluss_valide = True
                        break

                # Alter Anschlussnehmer
                if anschluss_valide:
                    for row in self.anwendung.mitglieder_db:
                        if str(row["Laufende Nummer"]) == str(row_auswahl["Laufende Nummer"]):
                            row["Ident"] = ""
                            for key in keylist:
                                row[key] = ""
                            break

                    loginfo = (
                        f"Lfd-Nr. {row_auswahl['Laufende Nummer']} ::: "
                        f"Anschlussnehmer {row_auswahl['Name']} "
                        f"{row_auswahl['Vorname']} ===> "
                        f"Anschlussnehmer {neuer_anschluss_lnr} "
                        f"{neuer_name} {neuer_vorname}"
                    )
                    self.mitglieder_changes.append(loginfo)

                    self.anwendung.mitglieder_grid_update()
                    dialog.close()
                else:
                    ui.notify("Ausgewählter Anschlussnehmer ist nicht valide.", type="warning")

        with ui.dialog() as dialog:
            with ui.card().style("width: 600px; height: 400px;"):
                ui.button(
                    '', icon='close', on_click=dialog.close
                ).classes('absolute top-3 right-3')

                with ui.row():
                    ui.label(
                        'Anschlussnehmer ändern'
                    ).style("font-size: 24px; font-weight: bold;")

                with ui.row():
                    ui.label(f"Anschluss Nr. {row_auswahl['Ident']}")

                with ui.row():
                    ui.label(
                        f"aktueller Anschlussnehmer: "
                        f"{row_auswahl['Name']} {row_auswahl['Vorname']}"
                    )

                anschlussnehmer = [
                    f"{row['Laufende Nummer']} | {row['Name']} {row['Vorname']}"
                    for row in self.anwendung.mitglieder_db
                    if row["Ident"] == "" and row["Ident"] != row_auswahl["Ident"]
                ]

                with ui.row():
                    neuer_anschlussnehmer = ui.select(
                        options=anschlussnehmer,
                        label='Neuen Anschlussnehmer auswählen'
                    ).style("min-width: 300px;")

                with ui.row():
                    ui.button(
                        "Übernehmen",
                        icon='save',
                        on_click=aenderung_speichern
                    )

        dialog.open()

    def mitglieder_neu(self):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        def aenderung_speichern():
            # Änderung: Tatsächliche Daten-/Dateiänderungen zusätzlich protokollieren.
            with aenderungen_protokollieren(
                self.anwendung, 'MITGLIEDER', 'Mitglied anlegen',
                daten=lambda: {'Mitglieder': self.anwendung.mitglieder_db},
            ):
                neuer_eintrag = {}
                neuer_eintrag["Laufende Nummer"] = neue_lnr
                neuer_eintrag["Ident"] = ""
                neuer_eintrag["Name"] = input_name.value
                neuer_eintrag["Vorname"] = input_vorname.value
                for key in self.anwendung.mitglieder_db[0]:
                    if key not in ["Laufende Nummer","Ident","Name","Vorname"]:
                        neuer_eintrag[key] = ""
                self.anwendung.mitglieder_db.append(neuer_eintrag)
                ui.notify('Eintrag ' + input_name.value + " " + input_vorname.value + " wurde mit der Nummer " + str(neue_lnr) + " angelegt.", type="positive")
                loginfo = 'Lfd-Nr. ' + str(neue_lnr) + ' ::: Neuanlage ' + neuer_eintrag["Name"] + ' ' + neuer_eintrag["Vorname"]
                self.mitglieder_changes.append(loginfo)
                self.anwendung.mitglieder_grid_update()
                dialog.close()

        with ui.dialog() as dialog:
            with ui.card().style("width: 600px; height: 400px;"):
                ui.button('', icon='close', on_click=dialog.close).classes('absolute top-3 right-3')
                with ui.row():
                    ui.label('Neuen Eintrag anlegen').style("font-size: 24px; font-weight: bold;")
                with ui.row():
                    neue_lnr = max(int(x["Laufende Nummer"]) for x in self.anwendung.mitglieder_db) + 1
                    input_name = ui.input(label='Name').style('width: 200px')
                with ui.row():
                    input_vorname = ui.input(label='Vorname').style('width: 200px')
                with ui.row():
                    ui.button("Übernehmen", icon='save', on_click=aenderung_speichern)
        dialog.open()

    def dialog_mitglieder_editieren(self):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.

        if not self.anwendung.mitglieder_selected_row:
            ui.notify('Bitte zuerst einen Eintrag auswählen')
            return

        row_data = self.anwendung.mitglieder_selected_row

        with ui.dialog() as dialog:
            fields = {}
            with ui.card().classes('w-200'):
                ui.button('', icon='close', on_click=dialog.close)\
                  .classes('absolute top-3 right-3')

                for col_name, value in row_data.items():
                    if col_name == "ehrenamtlich aktiv":
                        fields[col_name] = ui.checkbox(col_name, value=value)\
                            .style("min-width: 400px")
                    elif col_name in ("Laufende Nummer", "Ident"):
                        ui.label(f"{col_name}: {value}")\
                            .style("color: #a0a0a0; min-width: 400px")
                    else:
                        fields[col_name] = ui.input(col_name, value=str(value))\
                            .style("min-width: 400px")

                def save_changes():
                    # Änderung: Tatsächliche Daten-/Dateiänderungen zusätzlich protokollieren.
                    with aenderungen_protokollieren(
                        self.anwendung, 'MITGLIEDER', 'Mitglied bearbeiten',
                        daten=lambda: {'Mitglieder': self.anwendung.mitglieder_db},
                    ):
                        # Das gesamte `rowData`-Array holen
                        row_data_list = self.mitglieder_grid.options['rowData']
                
                        # Aktuelle Zeile anhand der Referenz suchen und aktualisieren
                        for row in row_data_list:
                            if row['Laufende Nummer'] == row_data['Laufende Nummer']:  # Eindeutiges Feld zum Identifizieren
                                for col_name, input_field in fields.items():
                                    row[col_name] = input_field.value  # Checkbox-Wert
                                row_neu = row
                                break
                        # Grid-Daten explizit neu setzen und aktualisieren
                        self.mitglieder_grid.options['rowData'] = row_data_list
                        self.anwendung.mitglieder_db = row_data_list
                        self.anwendung.mitglieder_grid_update()
                        loginfo = 'Lfd-Nr. ' + str(row_data["Laufende Nummer"]) + ' ::: Anschlussdaten geändert für  ' + row_data["Name"] + ' ' + row_data["Vorname"]
                        self.mitglieder_changes.append(loginfo)
                        loginfo = 'Lfd-Nr. ' + str(row_data["Laufende Nummer"]) + ' ::: ALT: ' + str(row_data)
                        self.mitglieder_changes.append(loginfo)
                        loginfo = 'Lfd-Nr. ' + str(row_data["Laufende Nummer"]) + ' ::: NEU: ' + str(row_neu)
                        self.mitglieder_changes.append(loginfo)
                        dialog.close()

                with ui.row():
                    ui.button('Übernehmen', icon='save', on_click=save_changes)
                    ui.button('Abbrechen', icon='close', on_click=dialog.close)

        dialog.open()

    def dialog_mitglieder_loeschen(self):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.

        row_auswahl = self.anwendung.mitglieder_selected_row

        if not row_auswahl:
            ui.notify('Bitte zuerst einen Eintrag auswählen')
            return

        def loeschen_ja():
            # Änderung: Tatsächliche Daten-/Dateiänderungen zusätzlich protokollieren.
            with aenderungen_protokollieren(
                self.anwendung, 'MITGLIEDER', 'Mitglied löschen',
                daten=lambda: {'Mitglieder': self.anwendung.mitglieder_db},
            ):
                for row in self.anwendung.mitglieder_db[:]:
                    if row["Laufende Nummer"] == row_auswahl["Laufende Nummer"]:
                        self.anwendung.mitglieder_db.remove(row)

                        self.button_edit.disable()
                        self.button_loeschen.disable()

                        loginfo = (
                            f"Lfd-Nr. {row_auswahl['Laufende Nummer']} ::: "
                            f"Anschlussnehmer {row_auswahl['Name']} "
                            f"{row_auswahl['Vorname']} gelöscht."
                        )
                        self.mitglieder_changes.append(loginfo)

                        self.anwendung.mitglieder_grid_update()
                        break

                dialog.close()

        with ui.dialog() as dialog:
            with ui.card():
                ui.label(
                    f"Möchten Sie den Eintrag "
                    f"{row_auswahl['Laufende Nummer']} "
                    f"{row_auswahl['Name']} "
                    f"{row_auswahl['Vorname']} löschen?"
                )
                with ui.row():
                    ui.button(
                        "Ja",
                        on_click=loeschen_ja
                    ).props('color=negative')

                    ui.button(
                        "Nein",
                        on_click=dialog.close
                    ).props('color=primary')

        dialog.open()

    def duplikate_zusammensetzen(self, mitglieder_tabelle):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        # Dictionary zur Nachverfolgung von Name + Vorname
        verarbeitet = {}

        # Neue Liste für die resultierenden Einträge
        neue_tabelle = []

        for eintrag in mitglieder_tabelle:
            schluessel = (eintrag["Name"], eintrag["Vorname"])  # Schlüssel aus Name und Vorname
            if schluessel in verarbeitet:
                # Ident-Wert des Duplikats anhängen
                verarbeitet[schluessel]["Laufende Nummer"] += "," + eintrag["Laufende Nummer"]
                verarbeitet[schluessel]["Ident"] += "," + eintrag["Ident"]
            else:
                # Erstelle eine Kopie des Eintrags und füge ihn der neuen Liste hinzu
                verarbeitet[schluessel] = eintrag
                neue_tabelle.append(eintrag)
    
        return neue_tabelle

    def mitglieder_grid_update(self):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        check_ordner_exists(self.anwendung.ordner_downloads)
        check_ordner_exists(self.anwendung.ordner_vorlagen)
        # Fortschrittsanzeige ausblenden
        self.mgl_progress.classes('invisible')

        columns = []
        for row in self.anwendung.mitglieder_db:

            # Daten werden auf True oder False (binär) harmonisiert

            if row["ehrenamtlich aktiv"] == 'True' or row["ehrenamtlich aktiv"] == 'False':
                row["ehrenamtlich aktiv"] = row["ehrenamtlich aktiv"] == 'True'
            elif row["ehrenamtlich aktiv"] == True or row["ehrenamtlich aktiv"] == False:
                row["ehrenamtlich aktiv"] = row["ehrenamtlich aktiv"] == True           
            else:   
                row["ehrenamtlich aktiv"] = row["ehrenamtlich aktiv"] == 'x'

        # notwendig für den Fall, dass die Tabellendaten editiert werden
        self.mitglieder_tabelle = self.anwendung.mitglieder_db
        # Nur ausführen, wenn Editiermodus ausgeschalten ist
        if self.edit_switch.value != True:
            self.button_word_export.disable()
            self.mitglieder_tabelle = []

            # Filtert Daten in Abhängigkeit von Dropdown Auswahl. Es wird lediglich die Anzeige angepasst. Gespeicherte Daten werden nicht verändert
            # Sortierung wandelt String in Int um, um nicht 10 nach 1 zu erhalten
            mitglieder_tabelle_temp_row = {}
            mitglieder_tabelle_temp = []        

            if self.mitglieder_filter_dropdown.value == 'kein Filter':
                self.radio_filter.enable()
                self.button_serienbrief.enable()
                self.mitglieder_tabelle = self.anwendung.mitglieder_db
            elif self.mitglieder_filter_dropdown.value == 'Verbraucheranschlüsse':
                self.radio_filter.enable()
                self.button_serienbrief.enable()
                for mitglied in self.anwendung.mitglieder_db:
                    if str(mitglied['Ident']) != '':
                        self.mitglieder_tabelle.append(mitglied)
            elif self.mitglieder_filter_dropdown.value == 'Aktive Helfer':
                self.radio_filter.enable()
                self.button_serienbrief.enable()
                for mitglied in self.anwendung.mitglieder_db:
                    mitglieder_tabelle_row = {}
                    for key,value in mitglied.items():
                        if key in ['Name','Vorname','Geburtsdatum','Straße','Hausnummer','Festnetz','Mobil','E-Mail 1','E-Mail 2','Postleitzahl','Wohnort','Anrede-Adressat','Anrede-Geschlecht','Anrede-Formel','Anrede-Name']:
                            mitglieder_tabelle_row[key] = value
                    if mitglied["ehrenamtlich aktiv"] == True:
                        self.mitglieder_tabelle.append(mitglied)
            elif self.mitglieder_filter_dropdown.value == 'Mitgliederliste (Jahresabschluss)':
                self.button_word_export.enable()
                self.button_serienbrief.disable()
                self.radio_filter.set_value("Name")
                self.radio_filter.disable()
                for mitglied in self.anwendung.mitglieder_db:
                    mitglieder_tabelle_temp_row = {}
                    for key,value in mitglied.items():
                        if key in ['Laufende Nummer','Ident','Name','Vorname','Straße','Hausnummer','Postleitzahl','Wohnort']:
                            mitglieder_tabelle_temp_row[key] = value
                    if str(mitglied["Ident"]) != '':
                        mitglieder_tabelle_temp.append(mitglieder_tabelle_temp_row)
                self.mitglieder_tabelle = self.anwendung.duplikate_zusammensetzen(mitglieder_tabelle_temp)
            elif self.mitglieder_filter_dropdown.value == 'Mitgliederliste (Generalversammlung)':
                self.button_word_export.enable()
                self.button_serienbrief.disable()
                self.radio_filter.set_value("Name")
                self.radio_filter.disable()
                for mitglied in self.anwendung.mitglieder_db:
                    mitglieder_tabelle_temp_row = {}
                    for key,value in mitglied.items():
                        if key in ['Laufende Nummer','Ident','Name','Vorname']:
                            mitglieder_tabelle_temp_row[key] = value
                    if str(mitglied["Ident"]) != '':
                        mitglieder_tabelle_temp.append(mitglieder_tabelle_temp_row)
                self.mitglieder_tabelle = self.anwendung.duplikate_zusammensetzen(mitglieder_tabelle_temp)
            elif self.mitglieder_filter_dropdown.value == 'Verbraucher mit Wartungsdaten':
                self.button_word_export.disable()
                self.button_serienbrief.disable()
                self.radio_filter.set_value("Ident")
                self.radio_filter.disable()
                # db_wartung wird eingelesen
                if self.anwendung.db_datei_oeffnen(self.anwendung.db_wartung)[0] != 'file not found':
                    self.anwendung.wartung_db = self.anwendung.db_datei_oeffnen(self.anwendung.db_wartung)
                else:
                    return
                for mitglied in self.anwendung.mitglieder_db:
                    mitglieder_tabelle_temp_row = {}
                    datum_wartung = []
                    # nur Mitglieder mit Anschluss berücksichtigen
                    if mitglied["Ident"] == "":
                        continue
                    # Anzahl der Tage mit Wartungseintrag ermitteln
                    for zeile in self.anwendung.wartung_db:
                        if zeile[mitglied["Ident"]] != "":
                            datum_wartung.append(zeile["0"])
                    datum_wartung.sort(key=lambda x: datetime.strptime(x, "%d.%m.%Y"), reverse=True)
                    # nur die letzten 3 aktuellesten Datum berücksichtigen
                    if len(datum_wartung) > 3:
                        datum_wartung = datum_wartung[:3]
                    zaehler = 0
                
                    # ermitteln, ob Anschluss einen Eintrag bei den 3 Datum hat
                    for datum in datum_wartung:
                        zaehler += 1
                        for zeile in self.anwendung.wartung_db:
                            if zeile["0"] == datum:
                                mitglieder_tabelle_temp_row["Ident"] = mitglied["Ident"]
                                mitglieder_tabelle_temp_row["Name"] = mitglied["Name"]
                                mitglieder_tabelle_temp_row["Vorname"] = mitglied["Vorname"]
                                mitglieder_tabelle_temp_row["Eintrag " + str(zaehler)] = datum + ": " + zeile[mitglied["Ident"]]
                    if zaehler == 1:
                        mitglieder_tabelle_temp_row["Eintrag " + str(zaehler + 1)] = ""
                        mitglieder_tabelle_temp_row["Eintrag " + str(zaehler + 2)] = ""
                    if zaehler == 2:
                        mitglieder_tabelle_temp_row["Eintrag " + str(zaehler + 1)] = ""
                    if mitglieder_tabelle_temp_row != []:
                        mitglieder_tabelle_temp.append(mitglieder_tabelle_temp_row)
                self.mitglieder_tabelle = mitglieder_tabelle_temp

        # Radio Filter wird ausgewertet    
        if self.radio_filter.value == "Laufende Nummer":
            self.mitglieder_tabelle = sorted(self.mitglieder_tabelle, key=lambda x: int(x["Laufende Nummer"]))
        elif self.radio_filter.value == "Ident":
            # Wenn kein Wert in Spalte, soll die Zeile hinten angestellt werden
            self.mitglieder_tabelle = sorted(self.mitglieder_tabelle, key=lambda x: (not x.get("Ident") or not x["Ident"].isdigit(), int(x["Ident"]) if x.get("Ident") and x["Ident"].isdigit() else 0))
        elif self.radio_filter.value == "Name":
            self.mitglieder_tabelle = sorted(self.mitglieder_tabelle,key=lambda x: (x["Name"], x["Vorname"]))
        elif self.radio_filter.value == "Straße":
            self.mitglieder_tabelle = sorted(self.mitglieder_tabelle, key=lambda x: (not x.get("Reihenfolge Straße") or not x["Reihenfolge Straße"].isdigit(), int(x["Reihenfolge Straße"]) if x.get("Reihenfolge Straße") and x["Reihenfolge Straße"].isdigit() else 0))

        if self.mitglieder_tabelle != []:
            for key in self.mitglieder_tabelle[0].keys():
                column_element = {}
                column_element["minWidth"] = 160
                column_element["headerName"] = key
                column_element["field"] = key
                column_element["filter"] = 'agTextColumnFilter'
                column_element["floatingFilter"] = 'True'
                if key == "ehrenamtlich aktiv":
                    column_element["cellRenderer"] = 'agCheckboxCellRenderer'
                    column_element["editable"] = False
                if key == "Geburtsdatum":
                    column_element["cellEditor"] = 'agDateCellEditor'
                    column_element["filterParams"]= {"browserDatePicker": True}  # Enable browser's native date picker in the filter
                    column_element["cellEditorParams"] = {"dateFormat": "DD.MM.YYYY"}   
                columns.append(column_element)
        self.mitglieder_grid.options['columnDefs'] = columns
        self.mitglieder_grid.options['rowData'] = self.mitglieder_tabelle
        self.mitglieder_grid.options['rowSelection'] = 'multiple'
        self.mitglieder_grid.options['pagination'] = 'true'
        self.mitglieder_grid.options['paginationPageSize'] = self.anwendung.pagination
        self.mitglieder_grid.options['alwaysShowHorizontalScroll'] = 'true'
        self.mitglieder_grid.options['fullWidthCellRenderer'] = 'fullWidthCellRenderer'
        self.mitglieder_grid.update()

    async def editiermodus_aendern(self):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.

        async def confirm_save():
            # Funktion zum Anzeigen des Bestätigungsdialogs
            with ui.dialog() as dialog:
                with ui.card():
                    ui.label("Möchten Sie Ihre Änderungen speichern?")
                    with ui.row():
                        # "Ja" ruft die Funktion auf und schließt den Dialog
                        ui.button("Ja", on_click=lambda: (self.anwendung.mitglieder_speichern(), dialog.close()))
                        # "Nein" schließt nur den Dialog
                        ui.button("Nein", on_click=lambda: (nicht_speichern(),dialog.close()))

            dialog.open()

        def nicht_speichern():
            # Änderung: Tatsächliche Daten-/Dateiänderungen zusätzlich protokollieren.
            with aenderungen_protokollieren(
                self.anwendung, 'MITGLIEDER', 'Mitgliederänderungen verwerfen',
                daten=lambda: {'Mitglieder': self.anwendung.mitglieder_db},
            ):
                self.anwendung.mitglieder_aus_db()

        def apply_switch_off_state():
            # Status setzen, wenn der Switch ausgeschaltet wird
            self.button_edit.disable()
            self.button_anschluss.disable()
            self.button_neu.disable()
            self.button_loeschen.disable()
            self.mitglieder_filter_dropdown.enable()
            self.button_csv_export.enable()
            self.button_serienbrief.enable()
            self.button_email.enable()
            self.anwendung.mitglieder_grid_update()

        # Logik bei Statuswechsel
        if self.edit_switch.value == True:
            # Switch wird eingeschaltet -> direkter Wechsel
            self.button_edit.disable()
            self.button_anschluss.disable()
            self.button_neu.enable()
            self.button_loeschen.disable()
            self.mitglieder_filter_dropdown.disable()
            self.button_csv_export.disable()
            self.button_word_export.disable()
            self.button_serienbrief.disable()
            self.button_email.disable()
    #        mitglieder_aus_db()
        else:
            # Switch wird ausgeschaltet
            await confirm_save()  # Zeigt den Dialog an
            apply_switch_off_state()  # Setzt den "ausgeschalteten" Zustand immer

    def edit_aktivieren(self, event):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        self.anwendung.mitglieder_selected_row = event.args['data']

        if not self.edit_switch.value:
            return

        if not self.anwendung.mitglieder_selected_row:
            self.button_edit.disable()
            self.button_anschluss.disable()
            return

        self.button_edit.enable()

        if self.anwendung.mitglieder_selected_row.get("Ident", "") == "":
            self.button_anschluss.disable()
            self.button_loeschen.enable()
        else:
            self.button_anschluss.enable()
            self.button_loeschen.disable()

    def mitglieder_upload(self, e: events.UploadEventArguments):
        # Änderung: Tatsächliche Daten-/Dateiänderungen zusätzlich protokollieren.
        with aenderungen_protokollieren(
            self.anwendung, 'MITGLIEDER', 'Mitglieder importieren',
            daten=lambda: {'Mitglieder': self.anwendung.mitglieder_db},
        ):
            # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
            with StringIO(e.content.read().decode('iso-8859-1', errors='ignore')) as f:
                mitglieder_import = import_csv_inhalt(f)
            if self.anwendung.string_in_dict(mitglieder_import[0], 'Ident') == True and self.anwendung.string_in_dict(mitglieder_import[0], 'Name') == True and self.anwendung.string_in_dict(mitglieder_import[0], 'Vorname') == True:
                self.anwendung.mitglieder_db = mitglieder_import
            else:
                ui.notify('Importdaten entsprechen nicht dem erforderlichen Format. Es müssen mindestens Tabellenspalten für Ident, Name, Vorname enthalten sein.', type="warning")
                return
            self.anwendung.db_sichern("Upload Mitgliederdaten")
            self.button_mitglieder_pruefen.enable()
            self.button_mitglieder_speichern.enable()
            self.anwendung.mitglieder_grid_update()

    def mitglieder_aus_db(self):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        self.anwendung.mitglieder_db = self.anwendung.db_datei_oeffnen(self.anwendung.db_mitglieder)
        self.anwendung.mitglieder_grid_update()

    def mitglieder_speichern(self):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        if self.mitglieder_changes != []:
            for eintrag in self.mitglieder_changes:
                self.anwendung.change_log_info("MITGLIEDER", eintrag)
        self.anwendung.db_sichern("Mitglieder gespeichert")
        self.anwendung.db_datei_speichern(self.anwendung.db_mitglieder, self.anwendung.mitglieder_db)
        ui.notify('Mitgliederdaten gespeichert', type="positive")
        self.anwendung.mitglieder_aus_db()
        self.button_mitglieder_speichern.disable()
        self.anwendung.dbs_mitglieder_aktualisieren()

    def mitglieder_pruefen(self):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        mitglieder_ok = 1
        if self.anwendung.abnehmer_db != []:
            for row in self.anwendung.abnehmer_db:
                for mitglied in self.anwendung.mitglieder_db:
                    if row["Ident"] == mitglied["Ident"]:
                        if row["Name"] != mitglied["Name"]:
                            ui.notify("Mitglied Nr. " + row["Ident"] + ": Name in ABNEHMER DB stimmt nicht überein: " + mitglied["Name"] + " |vs| " + row["Name"], type="warning")
                            mitglieder_ok = 0
                        if row["Vorname"] != mitglied["Vorname"]:
                            ui.notify("Mitglied Nr. " + row["Ident"] + ": Vorname in ABNEHMER DB stimmt nicht überein: " + mitglied["Vorname"] + " |vs| " + row["Vorname"], type="warning")
                            mitglieder_ok = 0
        if self.anwendung.zaehler_db != []:
            for row in self.anwendung.zaehler_db:
                for mitglied in self.anwendung.mitglieder_db:
                    if row["Ident"] == mitglied["Ident"]:
                        if row["Name"] != mitglied["Name"]:
                            ui.notify("Mitglied Nr. " + row["Ident"] + ": Name in ZÄHLER-DB stimmt nicht überein: " + mitglied["Name"] + " |vs| " + row["Name"], type="warning")
                            mitglieder_ok = 0
                        if row["Vorname"] != mitglied["Vorname"]:
                            ui.notify("Mitglied Nr. " + row["Ident"] + ": Vorname in ZÄHLER-DB stimmt nicht überein: " + mitglied["Vorname"] + " |vs| " + row["Vorname"], type="warning")
                            mitglieder_ok = 0
        if self.anwendung.abschlag_db != []:
            for row in self.anwendung.abschlag_db:
                for mitglied in self.anwendung.mitglieder_db:
                    if row["Ident"] == mitglied["Ident"]:
                        if row["Name"] != mitglied["Name"]:
                            ui.notify("Mitglied Nr. " + row["Ident"] + ": Name in ABSCHLAG-DB stimmt nicht überein: " + mitglied["Name"] + " |vs| " + row["Name"], type="warning")
                            mitglieder_ok = 0
                        if row["Vorname"] != mitglied["Vorname"]:
                            ui.notify("Mitglied Nr. " + row["Ident"] + ": Vorname in ABSCHLAG-DB stimmt nicht überein:" + mitglied["Vorname"] + " |vs| " + row["Vorname"], type="warning")
                            mitglieder_ok = 0
        if self.anwendung.konto_db != []:
            for row in self.anwendung.konto_db:
                for mitglied in self.anwendung.mitglieder_db:
                    if row["Ident"] == mitglied["Ident"]:
                        if row["Name"] != mitglied["Name"]:
                            ui.notify("Mitglied Nr. " + row["Ident"] + ": Name in KONTO-DB stimmt nicht überein: " + mitglied["Name"] + " |vs| " + row["Name"], type="warning")
                            mitglieder_ok = 0
                        if row["Vorname"] != mitglied["Vorname"]:
                            ui.notify("Mitglied Nr. " + row["Ident"] + ": Vorname in KONTO-DB stimmt nicht überein:" + mitglied["Vorname"] + " |vs| " + row["Vorname"], type="warning")
                            mitglieder_ok = 0
        if mitglieder_ok == 1:
            ui.notify('Mitglieder wurden erfolgreich geprüft.', type="positive")

    def disable_row_splitting(self, table):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        """Verhindert das Teilen aller Zeilen einer Tabelle zwischen Seiten."""
        for row in table.rows:
            tr = row._tr  # Zugriff auf die zugrunde liegende XML-Struktur der Zeile
            trPr = tr.get_or_add_trPr()  # Zeilen-Eigenschaften hinzufügen/abrufen
            cant_split = OxmlElement('w:cantSplit')  # Keine Teilung zulassen
            trPr.append(cant_split)

    @export_hintergrund_absichern
    def mitglieder_ja_word_erstellen(self, dateiname):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        # Neues Word-Dokument erstellen für Jahresabschluss
        pythoncom.CoInitialize()
        self.mgl_progress.set_value(0)
        self.button_word_export.disable()
        doc = Document()

        section = doc.sections[0]
        section.orientation = WD_ORIENT.LANDSCAPE

        # # # Seitenrand oben verkleinern (z. B. auf 1 Zoll = 2.54 cm)
        section.top_margin = Inches(0.5)  # 0.5 Zoll = 1.27 cm

        # # # A4-Seitengröße setzen (Breite: 29.7 cm, Höhe: 21.0 cm)
        section.page_width = Inches(11.69)  # 29.7 cm in Zoll
        section.page_height = Inches(8.27)  # 21.0 cm in Zoll

        # # Überschrift hinzufügen
        heading=doc.add_heading('Mitgliederliste', level=1)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER  # Zentrieren
        doc.add_paragraph('')
        heading2=doc.add_heading('Nahwärme Sulzdorf eG', level=2)
        heading2.alignment = WD_ALIGN_PARAGRAPH.CENTER  # Zentrieren
        doc.add_paragraph('')
        self.mgl_progress.set_value(4)

        #  # Tabelle erstellen
        table = doc.add_table(rows=len(self.mitglieder_tabelle)+1, cols=len(self.mitglieder_tabelle[0]), style='Table Grid')
        self.mgl_progress.set_value(8)

        # # Tabelle Spaltenüberschriften
        column = 0
        for key in self.mitglieder_tabelle[0].keys():
            cell = table.cell(0, column)
            paragraph = cell.add_paragraph()
            run = paragraph.add_run(key)
            run.bold = True
            run.font.size = Pt(10)
            column = column + 1
        self.mgl_progress.set_value(10)

        progress_step = 89 / len(self.mitglieder_tabelle)
        progress_akt = 10 + progress_step
        row = 1
        for element in self.mitglieder_tabelle:
            column = 0
            for value in element.values():
                cell = table.cell(row, column)
                paragraph = cell.add_paragraph()
                run = paragraph.add_run(value)
                run.font.size = Pt(10)  # Kleinere Schriftgröße (z. B. 8 pt) für die Zelleninhalte
                column += 1
            row += 1
            self.mgl_progress.set_value(int(progress_akt))
            progress_akt = progress_akt + progress_step
        self.anwendung.disable_row_splitting(table)

        doc.save(self.anwendung.ordner_downloads + '\\' + dateiname)
        self.mgl_progress.set_value(100)
        self.button_word_export.enable()

    @export_hintergrund_absichern
    def mitglieder_gv_word_erstellen(self, dateiname, datum, ort):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        # Neues Word-Dokument erstellen für Generalversammlung
        pythoncom.CoInitialize()
        self.mgl_progress.set_value(0)
        self.button_word_export.disable()
        doc = Document()

        section = doc.sections[0]
        # # # Seitenrand oben verkleinern (z. B. auf 1 Zoll = 2.54 cm)
        section.top_margin = Inches(0.5)  # 0.5 Zoll = 1.27 cm
        column_widths = [1, 1, 1,1,4,1]

        # # Überschrift hinzufügen
        heading=doc.add_heading('Generalversammlung der Nahwärme Sulzdorf eG\nam ' + datum, level=1)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER  # Zentrieren
        heading2=doc.add_heading('Anwesenheitsliste', level=2)
        heading2.alignment = WD_ALIGN_PARAGRAPH.CENTER  # Zentrieren
        heading3=doc.add_heading('Ort: '+ ort, level=3)
        heading3.alignment = WD_ALIGN_PARAGRAPH.CENTER  # Zentrieren
        doc.add_paragraph('')
        self.mgl_progress.set_value(4)

        #  # Tabelle erstellen
        table = doc.add_table(rows=len(self.mitglieder_tabelle)+1, cols=len(self.mitglieder_tabelle[0])+2, style='Table Grid')
        self.mgl_progress.set_value(8)

        # # Tabelle Spaltenüberschriften
        column = 0
        for key in self.mitglieder_tabelle[0].keys():
            cell = table.cell(0, column)
            cell.width = Inches(column_widths[column])
            paragraph = cell.add_paragraph()
            run = paragraph.add_run(key)
            run.bold = True
            run.font.size = Pt(10)
            column = column + 1
        cell = table.cell(0,column)
        cell.width = Inches(column_widths[column])
        paragraph = cell.add_paragraph()
        run = paragraph.add_run("Unterschrift")
        run.bold = True
        run.font.size = Pt(10)
        cell = table.cell(0,column+1)
        cell.width = Inches(column_widths[column+1])
        paragraph = cell.add_paragraph()
        run = paragraph.add_run("Vollmacht liegt vor")
        run.bold = True
        run.font.size = Pt(10)

        self.mgl_progress.set_value(10)

        progress_step = 89 / len(self.mitglieder_tabelle)
        progress_akt = 10 + progress_step
        row = 1
        for element in self.mitglieder_tabelle:
            column = 0
            for value in element.values():
                cell = table.cell(row, column)
                paragraph = cell.add_paragraph()
                run = paragraph.add_run(value)
                run.font.size = Pt(10)  # Kleinere Schriftgröße (z. B. 8 pt) für die Zelleninhalte
                column += 1
            row += 1
            self.mgl_progress.set_value(int(progress_akt))
            progress_akt = progress_akt + progress_step
        self.anwendung.disable_row_splitting(table)

        doc.save(self.anwendung.ordner_downloads + '\\' + dateiname)
        self.mgl_progress.set_value(100)
        self.button_word_export.enable()

    @export_start_absichern('button_word_export', 'word_erstellung_background')
    def mitglieder_word_process(self, quelle, dateiname, datum, ort):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        # eigene Funktion für die Tabellen erstellung, da resourcenhungrig und in eigenem Thread
        # Komma hinter Dateiname, da sonst die Zeichen des Strings einzeln übergeben werden
        self.mgl_progress.set_value(0)
        self.mgl_progress.classes(remove='invisible')
        if quelle == "ja":
            self.word_erstellung_background = threading.Thread(target=self.anwendung.mitglieder_ja_word_erstellen, args=(dateiname,))
        elif quelle == "gv":
            self.word_erstellung_background = threading.Thread(target=self.anwendung.mitglieder_gv_word_erstellen, args=(dateiname,datum,ort,))
        self.word_erstellung_background.start()

    async def mitglieder_word_download(self):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        async def gv_dialog():

            def word_ja_start():
                ui.notify("Datei " + dateiname + " wird im Ordner " + self.anwendung.ordner_downloads + " abgelegt.", type="info")
                dialog.close()
                self.anwendung.mitglieder_word_process("gv", dateiname, self.selected_date, self.ort_input.value)
      
            # Dialog erstellen
            # Funktion für das aktuelle Datum
            current_date = datetime.now().strftime('%d.%m.%Y')
            self.selected_date = current_date
 
            def update_datum(e):
                # Datum in das gewünschte Format konvertieren
                self.selected_date = datetime.strptime(e.value, '%Y-%m-%d').strftime('%d.%m.%Y')
                date_input.value = self.selected_date  # Eingabefeld aktualisieren



            with ui.dialog().style("width: 800px; max-width: none") as dialog:
                with ui.card().style("width: 800px"):
                    ui.button('', icon='close', on_click=dialog.close).classes('absolute top-3 right-3')
                    with ui.row():
                        ui.label("Daten Generalversammlung").style("font-size: 24px;")
                    with ui.row():
                        with ui.input('Datum', value=current_date).style("width: 250px;") as date_input:
                            with date_input.add_slot('append'):
                                ui.icon('edit_calendar').on('click', lambda: date_menu.open()).classes('cursor-pointer')

                            # Menü mit Kalenderauswahl
                            with ui.menu() as date_menu:
                                ui.date(
                                    value=datetime.now().strftime('%Y-%m-%d'),  # ISO-Format für ui.date
                                    on_change=update_datum  # Callback für Änderungen
                                ).props(f"min-date={datetime.now().strftime('%Y-%m-%d')}")  # Nur zukünftige Daten erlauben
                    #    datum_input = ui.input('Datum')
                    with ui.row():
                        self.ort_input = ui.input("Ort").style("width: 250px;")
                    with ui.row():
                        ui.button("Word export", icon='file_download', on_click=word_ja_start)
        
            dialog.open()

        current_datetime = datetime.now().strftime("%Y-%m-%d")
        dateiname = self.mitglieder_filter_dropdown.value.replace(" ","-") + '-' + current_datetime + '.docx'
        if "Jahresabschluss" in self.mitglieder_filter_dropdown.value:
            ui.notify("Datei " + dateiname + " wird im Ordner " + self.anwendung.ordner_downloads + " abgelegt.", type="info")
            self.anwendung.mitglieder_word_process("ja", dateiname,"","")
        elif "Generalversammlung" in self.mitglieder_filter_dropdown.value:
            await gv_dialog()

    def mitglieder_csv_download(self):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        self.mgl_progress.set_value(0)
        time.sleep(1)
        self.mgl_progress.classes(remove='invisible')
        self.mgl_progress.set_value(1)
        current_datetime = datetime.now().strftime("%Y-%m-%d")
        dateiname = 'Mitglieder-' + self.mitglieder_filter_dropdown.value.replace(" ","-") + '-' + current_datetime + '.csv'
        dateipfad = self.anwendung.ordner_downloads + '\\' + dateiname
        datei_speichern(dateipfad,self.mitglieder_tabelle)
        self.mgl_progress.set_value(100)
        ui.notify("Datei " + dateiname + " wurde unter " + self.anwendung.ordner_downloads + " abgelegt.", type="positive")

    def serienbrief_dialog(self):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        datum_aktuell = datetime.now().strftime("%d.%m.%Y")

        def update_datum(e):
            # Datum in das gewünschte Format konvertieren
            self.datum_auswahl = datetime.strptime(e.value, '%Y-%m-%d').strftime('%d.%m.%Y')
            date_input.value = self.datum_auswahl  # Eingabefeld aktualisieren

        def ersetze_variablen(serientext: str, mitglieddetails: dict) -> str:
            """
        Ersetzt Variablen im Format %[KEY]% im serientext durch die Werte aus mitglieddetails.
        """
        
            # Regex findet %[irgendwas]%
            pattern = r"%\[(.+?)\]%"
        
            def replacer(match):
                key = match.group(1)
                # Wenn key existiert, ersetze – sonst Original stehen lassen
                return str(mitglieddetails.get(key, match.group(0)))
        
            return re.sub(pattern, replacer, serientext)

        def serienbrief_erstellen(betreff, text):
            mergestring = {}
            progress_akt = 0
            time.sleep(1)
            progress_step = 100/len(self.mitglieder_tabelle)
            self.mgl_progress.classes(remove='invisible')

            # Vorhandensein Vorlage prüfen
            serienbrief_daten = {}
            serienbrief_vorlage = self.anwendung.ordner_vorlagen + "\\" + "Vorlage-Serienbrief.docx"
            pfad_serienbrief_vorlage = Path(serienbrief_vorlage)
            if not pfad_serienbrief_vorlage.exists(): 
                ui.notify('Bitte Serienbrief-Vorlage ' + serienbrief_vorlage + ' ablegen.', type="info")
                return

            # Datum für Brief mit Punkten
            datum_brief = datetime.now().strftime("%d.%m.%Y")
            pfad_ordner_serienbrief = Path(self.ordner_serienbrief)
            if not pfad_ordner_serienbrief.exists():
    #            pfad_ordner_serienbrief.mkdir()
                os.makedirs(self.ordner_serienbrief)
            else:
                self.anwendung.dateien_in_ordner_loeschen(self.ordner_serienbrief)
            for mitglied in self.mitglieder_tabelle:
                serienbrief_felder = ["Ident","Name", "Vorname", "Straße", "Hausnummer", "Postleitzahl", "Wohnort", "Anrede-Geschlecht", "Anrede-Formal", "Anrede-Name"]
                for key,value in self.mitglieder_tabelle[0].items():
                    if key in serienbrief_felder:
                        serienbrief_daten[key] = value
                if len(serienbrief_daten) != len(serienbrief_felder):
                    ui.notify("Die Filterliste enthält nicht alle notwendigen Felder für den Serienbrief.", type="info")
                    return
            
                # Ersetzt Variablen im Text, die mit %[Variable]% identifiziert werden. Es kann da bei jedes Tabellenfeld verwendet werden. 
                # Wenn eine Variable nicht einem Tabellenfeld entspricht, wird sie nicht ersetzt

                text_variablen_ersetzt = ersetze_variablen(text, mitglied)
                betreff_variablen_ersetzt = ersetze_variablen(betreff, mitglied)

                # Es werden alle Felder der Tabelle im Word evaluiert + zusätzlich die Felder Datum, Betreff und Text ergänzt
                mergestring = {
                    "Datum": datum_brief,
                    "Betreff": betreff_variablen_ersetzt,
                    "Text": text_variablen_ersetzt
                }
                for key,value in mitglied.items():
                    mergestring[key] = value

                document = MailMerge(serienbrief_vorlage)
                docmergelist = mergestring
                document.merge(**docmergelist)
                if self.radio_filter.value == "Laufende Nummer":
                    prefix = "lnr" + mitglied["Laufende Nummer"] + "-"
                elif self.radio_filter.value == "Ident":
                    prefix = "id" + mitglied["Ident"] + "-"
                elif self.radio_filter.value == "Name":
                    prefix = ""
                elif self.radio_filter.value == "Straße":
                    prefix = "str" + mitglied["Reihenfolge Straße"] + "-"
                datei_serienbrief = prefix + "Brief-" + mitglied["Name"].replace(" ","-") + "-" + mitglied["Vorname"] + ".docx"            
                document.write(self.ordner_serienbrief + "\\" + datei_serienbrief)
                progress_akt += progress_step
                self.mgl_progress.set_value(int(progress_akt))


        def serienbrief_process(betreff,text):
            # Datum für Ordner und Datei mit Strichen
            datum_aktuell = datetime.now().strftime("%Y-%m-%d")
            self.ordner_serienbrief = self.anwendung.ordner_downloads + "\\" + "Serienbrief-" + datum_aktuell + "-" + betreff.replace(" ","-") + "\\word"
            ui.notify("Serienbriefe werden unter " + self.ordner_serienbrief + " abgelegt.", type="info")
            dialog.close()
            self.mgl_progress.set_value(0)
            self.mgl_progress.classes(remove='invisible')
            serienbrief_background = threading.Thread(target=serienbrief_erstellen, args=(betreff,text,))
            serienbrief_background.start()


        with ui.dialog().style("width: 800px; height: 600px; max-width: none") as dialog:
            with ui.card().style("width: 800px"):
                ui.button('', icon='close', on_click=dialog.close).classes('absolute top-3 right-3')
                with ui.row():
                    ui.label("Daten für Serienbrief").style("font-size: 24px;")
                with ui.row():
                    with ui.input('Datum', value=datum_aktuell).style("width: 250px;") as date_input:
                        with date_input.add_slot('append'):
                            ui.icon('edit_calendar').on('click', lambda: date_menu.open()).classes('cursor-pointer')

                        # Menü mit Kalenderauswahl
                        with ui.menu() as date_menu:
                            ui.date(
                                value=datetime.now().strftime('%d.%m.%Y'),  # ISO-Format für ui.date
                                on_change=update_datum  # Callback für Änderungen
                            ).props(f"min-date={datetime.now().strftime('%Y-%m-%d')}")  # Nur zukünftige Daten erlauben
                with ui.row():
                    ui.label("In Betreff und Text können Spaltennamen aus der Mitgliedertabelle im Format %[Feldname]% verwendet werden. Diese werden dynamisch durch den Wert des Mitglieds ersetzt.")
                    input_betreff = ui.input("Betreff").style("width: 500px;")
                with ui.row():
                    input_text = ui.textarea(label='Brieftext').style('width: 400px')
                with ui.row():
                    ui.button("Serienbrief erstellen", icon='keyboard', on_click=lambda: serienbrief_process(input_betreff.value, input_text.value))
        dialog.open()

    def mitglieder_ui(self):
        # Änderung 2.035: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        columns = []
        table = []
        self.anwendung.mitglieder_label_ui('')
        with ui.row():
            button_wartung = ui.button('Wartung', icon='engineering', on_click=self.anwendung.dialog_wartung).props('color=accent')
        ui.separator().style("height: 2px; background-color: black")
        with ui.row():
            self.mitglieder_filter_dropdown = ui.select(options=['kein Filter','Verbraucheranschlüsse','Aktive Helfer','Mitgliederliste (Jahresabschluss)','Mitgliederliste (Generalversammlung)', 'Verbraucher mit Wartungsdaten'], label='Filtervorlagen', value='kein Filter',on_change=self.anwendung.mitglieder_grid_update).classes('w-96')
            ui.label("Sortierung:")
            self.radio_filter = ui.radio(["Laufende Nummer", "Ident", "Name", "Straße"], value="Laufende Nummer", on_change=self.anwendung.mitglieder_grid_update).props('inline')
        with ui.row():
            self.button_csv_export = ui.button('CSV Export', icon='file_download', on_click=self.anwendung.mitglieder_csv_download)
            self.button_word_export = ui.button('Word Export', icon='file_download', on_click=self.anwendung.mitglieder_word_download)
            self.button_word_export.disable()
            self.button_serienbrief = ui.button('Serienbrief', icon='keyboard', on_click=self.anwendung.serienbrief_dialog)
            self.button_email = ui.button('E-Mail', icon='email')
            self.button_email.disable()
            self.mgl_progress = ui.circular_progress(min=0, max=100, color="black").classes('invisible')
        ui.separator().style("height: 2px; background-color: black")
        with ui.row():
            self.edit_switch = ui.switch('Editiermodus', on_change=self.anwendung.editiermodus_aendern)
            self.button_neu = ui.button('Eintrag neu', icon='add_circle', on_click=self.anwendung.mitglieder_neu)
            self.button_neu.disable()
            self.button_edit = ui.button('Eintrag editieren', icon='edit',on_click=self.anwendung.dialog_mitglieder_editieren)
            self.button_edit.disable()
            self.button_loeschen = ui.button('Eintrag löschen',icon='delete', on_click=self.anwendung.dialog_mitglieder_loeschen)
            self.button_loeschen.disable()
            self.button_anschluss = ui.button('Anschlussnehmer ändern',icon='change_circle', on_click=self.anwendung.anschluss_aendern)
            self.button_anschluss.disable()
        self.mitglieder_grid = ui.aggrid({
            'defaultColDef': {'flex': 1, 'editable': True, 'resizable': True, 'wrapHeaderText': True, 'autoHeaderHeight': True},
            'columnDefs': columns,
            'rowData': table,
            'domLayout': 'autoHeight',
        }).on('cellClicked', self.anwendung.edit_aktivieren).style('height: 100%')
        ui.separator().style("height: 2px; background-color: black")
        with ui.row():
            ui.upload(label='Upload Vorlage Mitgliederdaten',on_upload=self.anwendung.mitglieder_upload, auto_upload=True, max_files=1).props("accept=.csv").classes('max-w-full')
            self.button_mitglieder_pruefen = ui.button("Prüfen", icon='task_alt', on_click=self.anwendung.mitglieder_pruefen)
            self.button_mitglieder_speichern = ui.button('Speichern', icon='save', on_click=lambda: (self.anwendung.mitglieder_speichern())).props('color=' + self.anwendung.speichernbutton)
            self.button_mitglieder_pruefen.disable()
            self.button_mitglieder_speichern.disable()

        if self.anwendung.db_datei_oeffnen(self.anwendung.db_mitglieder)[0] == "file not found":
            self.anwendung.mitglieder_label_ui.refresh('Keine Mitgliederdaten in Datenbank. Upload CSV-Datei mit Basisdaten der Mitglieder.')
            self.anwendung.db_mitglieder_found = 0
        else:
            self.anwendung.db_mitglieder_found = 1
            self.anwendung.mitglieder_label_ui.refresh('Mitglieder-Datenbank wurde gefunden! Daten wurden geladen und können über einen neuen Upload überschrieben und ergänzt werden.')
            self.anwendung.mitglieder_aus_db() 
