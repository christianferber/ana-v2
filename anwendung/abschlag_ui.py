"""Änderung: Abschlagsoberfläche mit eigenem Tabellen- und Bedienzustand.
Gemeinsame Abschlagsdaten bleiben auf der übergebenen Anwendung.
"""
# Änderung: Änderungsprotokoll ergänzen; vorhandene Fachlogik unverändert ausführen.
from anwendung.aenderungsprotokoll import aenderungen_protokollieren
from io import StringIO
from nicegui import events, ui
from anwendung.datenhaltung import import_csv_inhalt


class AbschlagOberflaeche:
    # Änderung: Gemeinsame Daten und Hilfen stets über die Anwendung lesen.
    def __init__(self, anwendung):
        self.anwendung = anwendung

    def abschlag_label_ui(self, label):
        # Änderung: Bisherigen Ablauf mit Ansichts- und Anwendungszustand ausführen.
        ui.label(label).style('font-size:100%')

    def abschlag_aus_db(self):
        # Änderung: Bisherigen Ablauf mit Ansichts- und Anwendungszustand ausführen.
        print("Abschläge werden aus DB importiert")
        self.anwendung.abschlag_db = self.anwendung.db_datei_oeffnen(self.anwendung.db_abschlag)
        self.anwendung.abschlag_db = self.anwendung.tablefields_to_dotfloat(self.anwendung.abschlag_db)
        self.anwendung.abschlag_label_ui.refresh('Abschlags-Datenbank gefunden! Daten wurden geladen und können über einen neuen Upload überschrieben werden.')
        self.anwendung.abschlag_grid_ui.refresh()
        self.anwendung.db_abschlag_found = 1

    def abschlag_upload(self, e: events.UploadEventArguments):
        # Änderung: Tatsächliche Daten-/Dateiänderungen zusätzlich protokollieren.
        with aenderungen_protokollieren(
            self.anwendung, 'ABSCHLAG', 'Abschläge importieren',
            daten=lambda: {'Abschläge': self.anwendung.abschlag_db},
        ):
            # Änderung: Bisherigen Ablauf mit Ansichts- und Anwendungszustand ausführen.
            with StringIO(e.content.read().decode('iso-8859-1', errors='ignore')) as f:
                abschlag_import = import_csv_inhalt(f)
            if self.anwendung.string_in_dict(abschlag_import[0], 'Ident') == True and self.anwendung.string_in_dict(abschlag_import[0], 'Name') == True and self.anwendung.string_in_dict(abschlag_import[0], 'Vorname') == True and self.anwendung.string_in_dict(abschlag_import[0], 'Abschlag') == True:
                self.anwendung.abschlag_db = abschlag_import
            else:
                ui.notify('Importdaten entsprechen nicht dem erforderlichen Format. Es müssen Tabellenspalten für Ident, Name, Vorname und Abschlag-<Jahr> enthalten sein.', type="warning")
                return
            self.anwendung.db_sichern("Upload Abschlagsdaten")
            self.anwendung.abschlag_grid_ui.refresh()
            self.abschlag_button_speichern.enable()

    def abschlag_speichern(self):
        # Änderung: Bisherigen Ablauf mit Ansichts- und Anwendungszustand ausführen.
        self.anwendung.db_datei_speichern(self.anwendung.db_abschlag, self.anwendung.abschlag_db)
        ui.notify('Abschlagsdaten gespeichert', type="positive")
        self.abschlag_button_speichern.disable()

    def abschlag_tabelle_on_change(self, event):
        # Änderung: Tatsächliche Daten-/Dateiänderungen zusätzlich protokollieren.
        with aenderungen_protokollieren(
            self.anwendung, 'ABSCHLAG', 'Abschläge bearbeiten',
            daten=lambda: {'Abschläge': self.anwendung.abschlag_db},
        ):
            # Änderung: Bisherigen Ablauf mit Ansichts- und Anwendungszustand ausführen.
            if event["newValue"] == None:
                return
            self.anwendung.abschlag_db[int(event["rowId"])][event["colId"]] = event["newValue"]
            self.anwendung.change_log("ABSCHLAG", event)
            self.abschlag_button_speichern.enable()

    def abschlag_columns_erstellen(self, table):
        # Änderung: Bisherigen Ablauf mit Ansichts- und Anwendungszustand ausführen.
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
                    column_element["pinned"] = "left"
                else:
                    column_element["flex"] = 1
                    column_element["minWidth"] = 160

                if key in ("Ident", "Name", "Vorname"):
                    column_element["pinned"] = 'left'

                column_element["filter"] = 'agTextColumnFilter'
                column_element["floatingFilter"] = True

                if key == "Kommentar":
                    column_element["editable"] = True
                    column_element["cellStyle"] = {'backgroundColor': self.anwendung.col_cell_mod}
                    column_element["cellEditor"]='agStringCellEditor'
                if "Abschlag-" in key:
                    column_element["editable"] = True
                    column_element["cellStyle"] = {'backgroundColor': self.anwendung.col_cell_mod}
                    column_element["cellEditor"]='agNumberCellEditor'
                columns.append(column_element)

        return columns

    def abschlag_grid_ui(self):
        # Änderung: Bisherigen Ablauf mit Ansichts- und Anwendungszustand ausführen.
        self.abschlag_grid = ui.aggrid({
            'defaultColDef': {
                'editable': False,
                'resizable': True,
                'wrapHeaderText': True,
                'autoHeaderHeight': True,
            },
            'columnDefs': self.abschlag_columns_erstellen(self.anwendung.abschlag_db),
            'rowData': self.anwendung.abschlag_db,
            'domLayout': 'autoHeight',
            'pagination': True,
            'paginationPageSize': self.anwendung.pagination
        }).on(
            'cellValueChanged',
            lambda event: self.abschlag_tabelle_on_change(event.args)
        ).style('height: 100%')

    def abschlag_ui(self):
        # Änderung: Bisherigen Ablauf mit Ansichts- und Anwendungszustand ausführen.
        self.anwendung.abschlag_label_ui("")
        with ui.row():
            ui.upload(on_upload=self.abschlag_upload, auto_upload=True, max_files=1).props("accept=.csv").classes('max-w-full')
            self.abschlag_button_speichern = ui.button('Speichern', icon='save', on_click=lambda: self.abschlag_speichern()).props('color=' + self.anwendung.speichernbutton)
            self.abschlag_button_speichern.disable()
        self.anwendung.abschlag_grid_ui()

        if self.anwendung.db_datei_oeffnen(self.anwendung.db_abschlag)[0] == "file not found":
            self.anwendung.abschlag_label_ui.refresh('Keine Abschlagsdaten in Datenbank! Upload Abschlag per CSV-Datei möglich.')
        else:
            self.anwendung.db_abschlag_found = 1
            self.anwendung.abschlag_label_ui.refresh('Abschlagsdaten gefunden! Daten wurden geladen. Daten aus Datenbank können über einen neuen Upload überschrieben und ergänzt werden.')
            self.abschlag_aus_db()
