"""Änderung 2.033: Zähleroberfläche mit eigenem Tabellen- und Dialogzustand.
Gemeinsame Daten und Dateihilfen bleiben auf der übergebenen Anwendung.
"""
from collections import Counter
from io import StringIO
from pathlib import Path
from nicegui import events, ui
from anwendung.berechnungen import datum_in_string, datum_in_punkt, datum_tage_vorher


class ZaehlerOberflaeche:
    # Änderung: Gemeinsame Daten stets aktuell über die Anwendung lesen.
    def __init__(self, anwendung):
        self.anwendung = anwendung

    def zaehler_label_ui(self, label):
        # Änderung 2.033: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        ui.label(label).style('font-size:100%')

    def import_zaehler_liste(self, zaehler_liste):
        # Änderung 2.033: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        zaehler_liste_temp = []
        basis_liste = []

        # Prüfung, ob Zähler vom Monatsende importiert werden, da Zählerdaten an anderen Tagen nicht unterstützt werden.

        zaehler_ok = True
        for key in zaehler_liste[0].keys():
            if "Ident" not in key and "wechsel" not in key and key[4:8] not in ['0131','0228','0229','0331','0430','0531','0630','0731','0831','0930','1031','1130','1231']:
                zaehler_ok = False
        if zaehler_ok == False:
            ui.notify('Nur Import von Zählerdaten zum Monatsende erlaubt.', type="warning")
            return self.anwendung.zaehler_db

        # Wenn eine Datenbank gefunden wird, wird diese als Basis genommen, wenn nicht, dann die Abnehmer DB
        if self.anwendung.db_zaehler_found == 1:
            print("DB Zähler vorhanden")
            basis_liste = self.anwendung.zaehler_db 
        else:
            print("DB Zähler nicht gefunden")
            basis_liste = self.anwendung.abnehmer_db

        # Alle Zahlen als INT darstellen

        for row in basis_liste:
            for key,value in row.items():
                if "Ident" in key or ("-zaehler" in key and "datum" not in key):
                    row[key] = int(value)
        for row in zaehler_liste:
            for key,value in row.items():
                if "Ident" in key or ("-zaehler" in key and "datum" not in key):
                    row[key] = int(value)

        # Es wird eine temporäre Liste erzeugt, die die Basisliste und die neu eingelesene Zählerliste kombiniert
        for row in basis_liste:
            zaehler_liste_row_temp = {}
            for key,value in row.items():
                if key == "Ident" or key == "Name" or key == "Vorname" or "-zaehler" in key or key == "Kommentar":
                    zaehler_liste_row_temp[key] = value
                    if key == "Kommentar" and self.anwendung.db_zaehler_found != 1:
                        zaehler_liste_row_temp[key] = ""
            for zaehler_liste_row in zaehler_liste:
                if zaehler_liste_row["Ident"] == row["Ident"]:
                    for key,value in zaehler_liste_row.items():
                        # Ein bestehender Wert wird nur überschrieben, wenn der Schalter auf "on" ist
                        if ((self.upload_overwrite_switch.value == False) and "-zaehler" in key and key not in row) or (self.upload_overwrite_switch.value == True and "-zaehler" in key):
                            zaehler_liste_row_temp[key] = value
            zaehler_liste_temp.append(zaehler_liste_row_temp)

    # Keys, die nicht vorhanden sind, werden erzeugt
        keylist = []
        for row in zaehler_liste_temp:
            for key in row.keys():
                if key not in keylist:
                    keylist.append(key)
        for row in zaehler_liste_temp:
            for keys in keylist:
                if key not in row.keys():
                    row[key] = "-1"
        return zaehler_liste_temp

    def import_zaehlerdaten_visu(self, csvinput):
        # Änderung 2.033: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        imported_file = csvinput.split("\n")
        import_file_listdict = []
        abnehmer_dict = {}
        tabelle_zaehler_erg = []
        double_node= []
        node_found = ""
        # gewünschtes Ablesedatum auslesen
        for row in imported_file:
            if "Tag von" in row:
                zaehler_von_temp = row.split(";")
                zaehler_von = zaehler_von_temp[1][:-1]
            if "Tag bis" in row:
                zaehler_bis_temp = row.split(";")
                zaehler_bis = zaehler_bis_temp[1][:-1]
        del imported_file[0:6]
        del imported_file[-1]
        del imported_file[-1]
        import_file_listdict=self.anwendung.listcsv_to_dict(imported_file)
        # Erkennt, ob es für Zeilen 2 Werte gibt (für Zählerwechsel) und schreibt die gefundenen "node nummern" in eine Liste
        for row in import_file_listdict:
            if row["0"] == node_found:
                double_node.append(row["0"])
                node_found = ""
            else:
                node_found = row["0"]
        erste_zeile = 1
        for row in import_file_listdict:
            abnehmer_dict["Ident"] = row["0"]
            # geht mehrzeilige Einträge (Zählerwechsel) durch
            # Verarbeitung erste Zeile (vor Zählerwechsel)
            if row["0"] in double_node and erste_zeile == 1:
                abnehmer_dict[self.anwendung.jahr_in_datum(row["TAG BIS"]) + "-zaehlerwechsel-alt"] = row["Zaehlerstand BIS(kWh)"].replace(".",",")
                erste_zeile = 0
            # Verarbeitung zweite Zeile (nach Zählerwechsel)
            elif row["0"] in double_node and erste_zeile == 0:
                abnehmer_dict[self.anwendung.jahr_in_datum(row["TAG VON"]) + "-zaehlerwechsel-neu"] = row["Zaehlerstand VON(kWh)"].replace(".",",")
                if datum_tage_vorher(row["TAG BIS"],1) == zaehler_bis or row["TAG BIS"] == zaehler_bis:
                    abnehmer_dict[datum_in_string(zaehler_bis) + "-zaehler"] = row["Zaehlerstand BIS(kWh)"].replace(".",",")
                else:
                    abnehmer_dict[datum_in_string(zaehler_bis) + "-zaehler"] = "-1"
                abnehmer_dict[self.anwendung.jahr_in_datum(row["TAG VON"]) + "-datum-zaehlerwechsel"] = datum_in_punkt(row["TAG VON"])
                erste_zeile = 1
                tabelle_zaehler_erg.append(abnehmer_dict)
                abnehmer_dict = {}
            else:
                if double_node != []:
                    abnehmer_dict[self.anwendung.jahr_in_datum(row["TAG VON"]) + "-zaehlerwechsel-neu"] = "-1"
                    abnehmer_dict[self.anwendung.jahr_in_datum(row["TAG VON"]) + "-zaehlerwechsel-alt"] = "-1"
                    abnehmer_dict[self.anwendung.jahr_in_datum(row["TAG VON"]) + "-datum-zaehlerwechsel"] = "NICHT_VORHANDEN"
                # if row["TAG VON"] == zaehler_von:
                #     abnehmer_dict[datum_tage_vorher(zaehler_von,1).replace("-","") + "-zaehler"] = row["Zaehlerstand VON(kWh)"].replace(".",",")
                # else:
                #     abnehmer_dict[datum_tage_vorher(zaehler_von,1).replace("-","") + "-zaehler"] = "-1"
                if datum_tage_vorher(row["TAG BIS"],1) == zaehler_bis or row["TAG BIS"] == zaehler_bis:  
                    abnehmer_dict[datum_in_string(zaehler_bis) + "-zaehler"] = row["Zaehlerstand BIS(kWh)"].replace(".",",")
                else:
                    abnehmer_dict[datum_in_string(zaehler_bis) + "-zaehler"] = "-1"
                tabelle_zaehler_erg.append(abnehmer_dict)
                abnehmer_dict = {}
        return tabelle_zaehler_erg

    def zaehler_aus_db(self):
        # Änderung 2.033: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        print("Zähler werden aus DB importiert")
        self.anwendung.zaehler_db = self.anwendung.db_datei_oeffnen(self.anwendung.db_zaehler)
        self.anwendung.zaehler_db = self.anwendung.tablefields_to_int(self.anwendung.zaehler_db)
        self.zaehler_sortieren()
        self.anwendung.zaehler_label_ui.refresh('Zähler-Datenbank gefunden!')  
        self.anwendung.zaehler_grid_ui.refresh()
        self.zaehler_button_check.enable()
        self.anwendung.db_zaehler_found = 1

    def zaehler_liste_upload(self, e: events.UploadEventArguments):
        # Änderung 2.033: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        jahre_in_zaehler = []
        if self.anwendung.db_zaehler_found == 1:
            for key,value in self.anwendung.zaehler_db[0].items():
                if "-zaehler" in key:
                    jahre_in_zaehler.append(int(key[:4]))

            # Abrechnung des letzten erfassten Jahres muss erstellt sein - außer die Jahresenddaten sind nicht vorhanden

            datei_abrechnung = self.anwendung.ordner_abrechnungen + "\\" + "Abrechnung-" + str(max(jahre_in_zaehler)) + "\\" + "Abrechnung-" + str(max(jahre_in_zaehler)) + ".csv"
            if Path(datei_abrechnung).is_file() or (str(max(jahre_in_zaehler)) + "1231-zaehler") not in self.anwendung.zaehler_db[0].keys():
                print("Abrechnung für letzten Zählerstand gefunden oder Jahresendstand des letzten, erfassten Zählerjahres nicht gefunden.") 
            else:
                ui.notify("Bitte erstellen Sie die Abrechnung des letzten Jahres zuerst.", type="info")
                return          
        csv_import = StringIO(e.content.read().decode('iso-8859-1', errors='ignore'))
        csv_import_list = csv_import.getvalue().split("\n")
        if "Verbrauch Gesamt" in csv_import_list[0]:
            print("Zählerdatei korrekt")
        else:
            ui.notify('Importdaten entsprechen nicht dem erforderlichen Format. Bitte Zählerexport aus Visualisierung importieren.', type="warning")
            return
        self.anwendung.zaehler_db = self.import_zaehler_liste(self.import_zaehlerdaten_visu(csv_import.getvalue()))
        print("Zählerliste importiert")
        for row in self.anwendung.zaehler_db:
            for key,value in row.items():
                if "Ident" in key or ("-zaehler" in key and "datum" not in key):
                    row[key] = int(value)
        self.zaehler_sortieren()
        self.anwendung.db_sichern("Upload Zählerdaten")
        self.anwendung.zaehler_grid_ui.refresh()

    def zaehler_sortieren(self):
        # Änderung 2.033: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        zaehler_keys_temp = []
        zaehler_keys = []
        zaehlerkeys_sortiert = []
        zaehler_db_temp = []
        temprow = {}
        for key in self.anwendung.zaehler_db[0].keys():
            if key != "Ident" and key != "Name" and key != "Vorname" and key != "Kommentar":
                zaehler_keys_temp.append(key[:4])
        zaehler_keys_temp.sort(reverse=True)
        # zaehler_keys_temp enthält nur die Jahreszahlen
        keyscounter = Counter(zaehler_keys_temp)

        ### doppelte Einträge werden ermittelt

        zaehler_keys = []
        gefunden = set()
        for item in zaehler_keys_temp:
            if item not in gefunden:
                zaehler_keys.append(item)
                gefunden.add(item)
        jahre_kleiner_4 = []
        for jahr in zaehler_keys:
            # Es wird aufgrund der Anzahl der Jahre ermittelt, ob es sich um ein Zählerwechseljahr (bei 4 Einträgen) handelt
            if keyscounter[jahr] < 4 or keyscounter[jahr] > 4:
                for key in self.anwendung.zaehler_db[0].keys():
                    if jahr in key:
                        jahre_kleiner_4.append(key)
                        jahre_kleiner_4.sort()
                for element in jahre_kleiner_4:
                    zaehlerkeys_sortiert.append(element)
                jahre_kleiner_4 = []
            elif keyscounter[jahr] == 4:                   
                zaehlerkeys_sortiert.append(str(jahr) + '-zaehlerwechsel-alt')
                zaehlerkeys_sortiert.append(str(jahr) + '-zaehlerwechsel-neu')
                zaehlerkeys_sortiert.append(str(jahr) + '-datum-zaehlerwechsel')
                # wenn der key mit einer 8-stelligen Zahl beginnt (z.B. 20251130)
                for key in self.anwendung.zaehler_db[0].keys():
                    if jahr in key and key[:8].isdigit():
                        zaehlerkeys_sortiert.append(key)

        for row in self.anwendung.zaehler_db:
            temprow = {}
            temprow["Ident"] = row["Ident"]
            temprow["Name"] = row["Name"]
            temprow["Vorname"] = row["Vorname"]
            temprow["Kommentar"] = row["Kommentar"]
            for element in zaehlerkeys_sortiert:
                if element not in row.keys():
                    temprow[element] = "-1"
                else: 
                    temprow[element] = row[element]
            zaehler_db_temp.append(temprow)
        self.anwendung.zaehler_db = zaehler_db_temp

    def check_zaehlerdaten(self):
        # Änderung 2.033: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        index = -1
        na_found = 0
        number_na_found = 0
        self.zaehler_input_values = {}
        for row in self.anwendung.zaehler_db:
            if -1 in row.values() or "NICHT_VORHANDEN" in row.values():
                number_na_found = number_na_found + 1
        if number_na_found > 0:
            for row in self.anwendung.zaehler_db:
                index = index + 1
                for key,value in row.items():
                    if ("zaehler" in key) and ("datum" not in key) and (value == -1):
                        na_found = 1
                        self.zaehler_dialog_check_label01.set_text("Bitte Zählerstand manuell eintragen")
                        self.zaehler_dialog_check_label02.set_text(row["Name"] + " " + row["Vorname"] + " " + key)
                        self.zaehler_dialog_check_input01.label = "Zählerstand"
                        self.zaehler_dialog_check_input01.value = ""
                        self.zaehler_input_values["listid"] = index
                        self.zaehler_input_values["Key"] = key
                        self.zaehler_input_values["Type"] = "NUMBER"
                    if "datum" in key and (value == "NICHT_VORHANDEN"):
                        na_found = 1
                        self.zaehler_dialog_check_label01.set_text("Bitte Datum manuell eintragen")
                        self.zaehler_dialog_check_label02.set_text(row["Name"] + " " + row["Vorname"] + " " + key)
                        self.zaehler_dialog_check_input01.label = "Datum Zählerwechsel"
                        self.zaehler_dialog_check_input01.value = ""
                        self.zaehler_input_values["listid"] = index
                        self.zaehler_input_values["Key"] = key
                        self.zaehler_input_values["Type"] = "TEXT"
                    if na_found == 1:
                        self.dialog_zaehler_check.open()
                        break
        else:
            ui.notify("Zählerdaten geprüft - keine Fehler gefunden", type="positive")

    def zaehler_speichern(self):
        # Änderung 2.033: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        for row in self.anwendung.zaehler_db:
            if -1 in row.values() or "NICHT_VORHANDEN" in row.values():
                ui.notify("Fehler in der Tabelle gefunden. Bitte Daten vor Speichern überprüfen und korrigieren.", type="warning")
                return
        self.anwendung.db_datei_speichern(self.anwendung.db_zaehler, self.anwendung.zaehler_db)
        ui.notify('Zählerdaten gespeichert', type="positive")
        self.zaehler_button_speichern.disable()

    def dialog_zaehlerstand_uebernehmen(self):
        # Änderung 2.033: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        log_daten = str(self.anwendung.zaehler_db[self.zaehler_input_values["listid"]]["Ident"]) + " " + str(self.anwendung.zaehler_db[self.zaehler_input_values["listid"]]["Name"]) + " " + str(self.anwendung.zaehler_db[self.zaehler_input_values["listid"]]["Vorname"]) + " ::: " + str(self.zaehler_input_values["Key"]) + " ::: " + str(self.anwendung.zaehler_db[self.zaehler_input_values["listid"]][self.zaehler_input_values["Key"]]) + " ===> " + str(self.zaehler_dialog_check_input01.value)
        self.anwendung.change_log_info("ZÄHLER", log_daten)
        if self.zaehler_input_values["Type"] == "NUMBER":
            self.anwendung.zaehler_db[self.zaehler_input_values["listid"]][self.zaehler_input_values["Key"]] = int(self.zaehler_dialog_check_input01.value)
        else:
            self.anwendung.zaehler_db[self.zaehler_input_values["listid"]][self.zaehler_input_values["Key"]] = str(self.zaehler_dialog_check_input01.value)
        self.anwendung.zaehler_grid_ui.refresh()
        self.zaehler_button_speichern.enable()
        ui.notify("Zählerstand aktualisiert", type="positive")
        self.dialog_zaehler_check.close()

    def zaehler_tabelle_on_change(self, event):
        # Änderung 2.033: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        if event["newValue"] == None or event["newValue"] == -1:
             return
        self.anwendung.zaehler_db[int(event["rowId"])][event["colId"]] = event["newValue"]
        self.zaehler_button_speichern.enable()
        self.anwendung.change_log("ZÄHLER", event)
        ui.notify("Daten aktualisiert", type="positive")

    def zaehler_columns_erstellen(self, table):
        # Änderung 2.033: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        columns = []
        if table != []:
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
                if key == "Name" or key == "Vorname":
                    column_element["pinned"] = 'left'
                column_element["filter"] = 'agTextColumnFilter'
                column_element["floatingFilter"] = 'True'
                if key == "Kommentar" or "datum-zaehlerwechsel" in key:
                    column_element["editable"] = True
                    column_element["cellStyle"] = {'backgroundColor': self.anwendung.col_cell_mod}
                    column_element["cellEditor"] = 'agStringCellEditor'
                if "-zaehler" in key and "datum" not in key:
                    column_element["filter"] = 'agNumberColumnFilter'
                    column_element["editable"] = True
                    column_element["cellStyle"] = {'backgroundColor': self.anwendung.col_cell_mod}
                    column_element["cellEditor"] = 'agNumberCellEditor'
                    column_element["cellEditorParams"]= {"min": -1,"step": 1}
                columns.append(column_element)

        return columns   

    def zaehler_grid_ui(self):
        # Änderung 2.033: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        self.zaehler_grid = ui.aggrid({
            'defaultColDef': {
                'editable': False,
                'resizable': True,
                'wrapHeaderText': True,
                'autoHeaderHeight': True,
            },
            'columnDefs': self.zaehler_columns_erstellen(self.anwendung.zaehler_db),
            'rowData': self.anwendung.zaehler_db,
            'domLayout': 'autoHeight',
            'pagination': True,
            'paginationPageSize': self.anwendung.pagination
        }).on(
            'cellValueChanged',
            lambda event: self.zaehler_tabelle_on_change(event.args)
        ).style('height: 100%')

    def zaehlerdaten_ui(self):
        # Änderung 2.033: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        with ui.dialog() as self.dialog_zaehler_check, ui.card():
            self.zaehler_dialog_check_label01 = ui.label("Bitte Zählerstand manuell eintragen")
            self.zaehler_dialog_check_label02 = ui.label("")
            self.zaehler_dialog_check_input01 = ui.input("Zählerstand")
            with ui.row():
                ui.button("Übernehmen", on_click=lambda: self.dialog_zaehlerstand_uebernehmen())
                ui.button("Abbrechen", on_click=self.dialog_zaehler_check.close)
        self.anwendung.zaehler_label_ui("")
        with ui.row():
            ui.upload(label='Zählerdaten aus Visualisierungs-Export hochladen', on_upload=self.zaehler_liste_upload, auto_upload=True, max_files=1).props("accept=.csv").classes('max-w-full')
            self.upload_overwrite_switch = ui.switch('Daten bei Upload überschreiben')
            self.zaehler_button_check = ui.button("Daten überprüfen", icon='task_alt', on_click=lambda: (self.check_zaehlerdaten()))
            self.zaehler_button_check.disable()
            self.zaehler_button_speichern = ui.button('Speichern', icon='save', on_click=lambda: (self.zaehler_speichern())).props('color=' + self.anwendung.speichernbutton)
            self.zaehler_button_speichern.disable()    
        self.anwendung.zaehler_grid_ui()
        if self.anwendung.db_datei_oeffnen(self.anwendung.db_zaehler)[0] == "file not found":
            self.anwendung.zaehler_label_ui.refresh('Keine Zählerdaten in Datenbank. Upload CSV-Datei mit Zählerdaten.')
        else:
            self.anwendung.db_zaehler_found = 1
            self.zaehler_aus_db()    
