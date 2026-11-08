"""Änderung 2.034: Abnehmeroberfläche mit eigenem Tabellen- und Bedienzustand."""
from io import StringIO
from nicegui import events, ui
from anwendung.datenhaltung import import_csv_inhalt


class AbnehmerOberflaeche:
    # Änderung: Gemeinsame Daten stets über die Anwendung lesen.
    def __init__(self, anwendung):
        self.anwendung = anwendung

    def abnehmer_label_ui(self, label):
        # Änderung 2.034: Bisherigen Ablauf mit Ansichts- und Anwendungszustand ausführen.
        ui.label(label).style('font-size:100%')

    def abnehmer_upload(self, e: events.UploadEventArguments):
        # Änderung 2.034: Bisherigen Ablauf mit Ansichts- und Anwendungszustand ausführen.
        if self.anwendung.mitglieder_db == []:
            ui.notify('Mitglieder sind noch nicht erfasst. Bitte vorher Mitgliederliste anlegen.', type="info")
            return
        with StringIO(e.content.read().decode('iso-8859-1', errors='ignore')) as f:
            abnehmer_import = import_csv_inhalt(f)
        if self.anwendung.string_in_dict(abnehmer_import[0], 'Ident') == True and self.anwendung.string_in_dict(abnehmer_import[0], 'Name') == True and self.anwendung.string_in_dict(abnehmer_import[0], 'Vorname') == True and self.anwendung.string_in_dict(abnehmer_import[0], 'Original-Vertragsleistung') == True and self.anwendung.string_in_dict(abnehmer_import[0], 'Mindest-Vertragsleistung') == True:
            for mrow in self.anwendung.mitglieder_db:
                ident_found = 0
                temprow = {}
                for row in abnehmer_import:
                    if mrow["Ident"] == row["Ident"]:
                        for key,value in row.items():
                            if key == "Ident" or key == "Name" or key == "Vorname":
                                temprow[key] = mrow[key]
                            else:
                                temprow[key] = row[key]
                        self.anwendung.abnehmer_db.append(temprow)
                        ident_found = 1
                if ident_found != 1 and mrow["Ident"] != "":
                    temprow = {}
                    temprow["Ident"] = mrow["Ident"]
                    temprow["Name"] = mrow["Name"]
                    temprow["Voranme"] = mrow["Vorname"]
                    ui.notify("Ident " + mrow["Ident"] + " nicht gefunden.", type="warning")
                    self.anwendung.abnehmer_db.append(temprow)
        else:
            ui.notify('Importdaten entsprechen nicht dem erforderlichen Format. Es müssen Tabellenspalten für Ident, Name, Vorname, Original-Vertragsleistung und Mindest-Vertragsleistung-<Jahr> enthalten sein.', type="Warning")
            return
        self.anwendung.abnehmer_db = sorted(self.anwendung.abnehmer_db, key=lambda x: int(x["Ident"]))  
        for row in self.anwendung.abnehmer_db:
            for key,value in row.items():
                if "Ident" in key or "Vertragsleistung" in key:
                    row[key] = int(value)
        self.anwendung.db_sichern("Upload Abnehmerdaten")
        self.button_abnehmer_speichern.enable()
        self.anwendung.abnehmer_grid_ui.refresh()

    def abnehmer_aus_db(self):
        # Änderung 2.034: Bisherigen Ablauf mit Ansichts- und Anwendungszustand ausführen.
        self.anwendung.abnehmer_db = self.anwendung.db_datei_oeffnen(self.anwendung.db_abnehmer)
        self.anwendung.abnehmer_db = self.anwendung.tablefields_to_int(self.anwendung.abnehmer_db)
        self.anwendung.abnehmer_grid_ui.refresh()
        self.button_abnehmer_speichern.disable()

    def abnehmerdaten_speichern(self):
        # Änderung 2.034: Bisherigen Ablauf mit Ansichts- und Anwendungszustand ausführen.
        self.anwendung.db_datei_speichern(self.anwendung.db_abnehmer, self.anwendung.abnehmer_db)
        self.anwendung.abschlag_speichern()
        self.anwendung.abschlag_grid_ui.refresh()
        self.button_abnehmer_speichern.disable()
        ui.notify("Abnehmerdaten gespeichert", type='positive')

    def abnehmer_tabelle_on_change(self, event):
        # Änderung 2.034: Bisherigen Ablauf mit Ansichts- und Anwendungszustand ausführen.
        if event["newValue"] == None:
            return
        self.anwendung.abnehmer_db[int(event["rowId"])][event["colId"]] = event["newValue"]
        if "Mindest" in event["colId"]:
            abschlag_db_wert_alt = self.anwendung.abschlag_db[int(event["rowId"])]["Abschlag-" + str(event["colId"])[-4:]]
            if event["newValue"] != 0:
                self.anwendung.abschlag_db[int(event["rowId"])]["Abschlag-" + str(event["colId"])[-4:]] = round((event["newValue"] / 100 * self.anwendung.arbeitspreis / 4),2)
            abschlag_db_wert_neu = self.anwendung.abschlag_db[int(event["rowId"])]["Abschlag-" + str(event["colId"])[-4:]]
            log_daten = event["data"]["Ident"] + " " + event["data"]["Name"] + " " + event["data"]["Vorname"] + " ::: " + "Abschlag-" + str(event["colId"])[-4:] + " ::: " + str(abschlag_db_wert_alt) + " ===> " + str(abschlag_db_wert_neu)
            self.anwendung.change_log_info("ABSCHLAG", log_daten)
        self.anwendung.change_log("ABNEHMER", event)
        self.button_abnehmer_speichern.enable()

    def abnehmer_columns_erstellen(self, table):
        # Änderung 2.034: Bisherigen Ablauf mit Ansichts- und Anwendungszustand ausführen.
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
                if "Mindest-" in key:
                    column_element["editable"] = True
                    column_element["cellStyle"] = {'backgroundColor': self.anwendung.col_cell_mod}
                    column_element["cellEditor"]='agNumberCellEditor'

                columns.append(column_element)
        return columns

    def abnehmer_grid_ui(self):
        # Änderung 2.034: Bisherigen Ablauf mit Ansichts- und Anwendungszustand ausführen.
        self.abnehmer_grid = ui.aggrid({
            'defaultColDef': {
                'editable': False,
                'resizable': True,
                'wrapHeaderText': True,
                'autoHeaderHeight': True,
            },
            'columnDefs': self.anwendung.abnehmer_columns_erstellen(self.anwendung.abnehmer_db),
            'rowData': self.anwendung.abnehmer_db,
            'domLayout': 'autoHeight',
            'pagination': True,
            'paginationPageSize': self.anwendung.pagination
        }).on(
            'cellValueChanged',
            lambda event: self.anwendung.abnehmer_tabelle_on_change(event.args)
        ).style('height: 100%')

    def abnehmer_ui(self):
        # Änderung 2.034: Bisherigen Ablauf mit Ansichts- und Anwendungszustand ausführen.

        self.anwendung.abnehmer_label_ui('')
        with ui.row():
            ui.upload(label='Upload Vorlage Abnehmerdaten',on_upload=self.anwendung.abnehmer_upload, auto_upload=True, max_files=1).props("accept=.csv").classes('max-w-full')
            self.button_abnehmer_speichern = ui.button('Speichern', icon='save', on_click=lambda: (self.anwendung.abnehmerdaten_speichern())).props('color=' + self.anwendung.speichernbutton)
            self.button_abnehmer_speichern.disable()
        self.anwendung.abnehmer_grid_ui()
        if self.anwendung.db_datei_oeffnen(self.anwendung.db_abnehmer)[0] == "file not found":
            self.anwendung.abnehmer_label_ui.refresh('Keine Abnehmerdaten in Datenbank. Upload CSV-Datei mit Basisdaten der Abnehmer.')
        else:
            self.anwendung.db_abnehmer_found = 1
            self.anwendung.abnehmer_label_ui.refresh('Abnehmer-Datenbank gefunden! Daten wurden geladen und können über einen neuen Upload überschrieben und ergänzt werden.')
            self.anwendung.abnehmer_aus_db()   
