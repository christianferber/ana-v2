"""Änderung 2.03: Abrechnungsoberfläche mit eigenem Bereichszustand.

Dialoge und Abläufe bleiben erhalten. Gemeinsame Datenbanken und Einstellungen
werden weiterhin aus der übergebenen Anwendung gelesen und dort aktualisiert.
"""
import os
from pathlib import Path
import threading

from nicegui import ui
from anwendung.datenhaltung import datei_oeffnen, datei_speichern
from anwendung.berechnungen import abrechnung_berechnen
from anwendung.berechnungen import letzte_mindestabnahme as mindestabnahme_berechnen
from anwendung.dokumente import abrechnung_word_schreiben, abrechnung_pdf_konvertieren
from anwendung.dokumentfelder import mapping_wordfelder


class AbrechnungOberflaeche:
    # Änderung 2.03: Bedien- und Tabellenzustand gehört zu dieser Ansicht.
    def __init__(self, anwendung):
        self.anwendung = anwendung
        # Änderung 2.03: Vorheriger globaler Anfangswert bleibt erhalten.
        self.abrechnung = []
        self.abrechnung_fuer_pdf = []

    def jahre_abrechnung(self):
        # Änderung 2.03: Zustand über die Ansicht bzw. gemeinsame Anwendung verwenden.
        jahrliste = []
        self.jahrliste_erstellbar = []
        self.jahrliste_einlesbar = []
        self.anwendung.zaehler_aus_db()
        if self.anwendung.zaehler_db == []:
            ui.notify("Zählerdatenbank nicht gefüllt!", type="warning")
            return
        if self.anwendung.abschlag_db == []:
            ui.notify("Abschlag-Datenbank nicht gefüllt", type="warning")
            return
        for key in self.anwendung.zaehler_db[0]:
            if "1231" in key:
                if (str(int(key[0:4]) - 1) + "1231-zaehler") in self.anwendung.zaehler_db[0].keys():
                    if ("Abschlag-" + str(int(key[0:4]))) in self.anwendung.abschlag_db[0].keys():
                        if ("Mindest-Vertragsleistung-" + str(int(key[0:4]))) in self.anwendung.abnehmer_db[0].keys():
                            if ("Mindest-Vertragsleistung-" + str(int(key[0:4]) - 1)) in self.anwendung.abnehmer_db[0].keys():
                                jahrliste.append(key[0:4])
                                self.jahrliste_erstellbar.append(key[0:4])
                            else:
                                ui.notify("Für Jahr " + str(int(key[0:4]) - 1) + " (Vorjahr von " + str(key[0:4]) + ") ist keine Mindest-Vertragsleistung hinterlegt.", type="warning")
                        else:
                            ui.notify("Für Jahr " + str(key[0:4]) + " ist keine Mindest-Vertragsleistung hinterlegt.", type="warning")
                    else:
                        ui.notify("Für Jahr " + str(key[0:4]) + " ist kein Abschlag hinterlegt.", type="warning")
        pfad_ordner_abrechnungen = Path(self.anwendung.ordner_abrechnungen)
        for item in pfad_ordner_abrechnungen.iterdir():
            if item.is_dir():
                if item.name[:-4] == 'Abrechnung-':
                    datei_abrechnung = self.anwendung.ordner_abrechnungen + "\\" + item.name + "\\" + "Abrechnung-" + item.name[-4:] + ".csv"
                    if Path(datei_abrechnung).is_file():
                        self.jahrliste_einlesbar.append(item.name[-4:])
                        if item.name[-4:] not in jahrliste:
                            jahrliste.append(item.name[-4:])
        jahrliste.sort()
        self.jahre_dropdown.set_options(jahrliste)
        self.reset_abrechnung()

    # Buttons ein/ausblenden in Abhängigkeit davon, ob Abrechnung gespeichert wurde bzw. ob alle Daten vorliegen, um Abrechnung zu erstellen

    def reset_abrechnung(self):
        # Änderung 2.03: Zustand über die Ansicht bzw. gemeinsame Anwendung verwenden.
        self.abr_button_erstellen.disable()
        self.abr_button_einlesen.disable()
        if self.jahre_dropdown.value in self.jahrliste_einlesbar:
            self.abr_button_einlesen.enable()
            self.mwst_jahr.disable()
        if self.jahre_dropdown.value in self.jahrliste_erstellbar:
            self.abr_button_erstellen.enable()
            self.mwst_jahr.enable()
        self.abr_button_download.disable()
        self.abr_button_plausibel.disable()
        self.abr_button_pdf.disable()
        self.abrechnung = []
        self.za_switch.value = False
        self.abrechnung_grid_ui.refresh()
        self.label_umsatz.set_text("")


    async def abr_speichern(self):
        # Speichert die Abrechnung als CSV, hinterlegt die neuen Abschläge und passt ggf. die Mindestabnahme an.
        # Änderung 2.03: Zustand über die Ansicht bzw. gemeinsame Anwendung verwenden.

        # Überprüft, ob die Mindestabnahme für das neue Jahr erneut ausgesetzt werden soll. Sonst wird die Mindestabnahme des letzen Jahres, wo sie gesetzt war übernommen

        async def mindestabnahme_pruefen(jahr):
            def mv_aussetzen():
                dialog_mv.close()
                row["Mindest-Vertragsleistung-" + str(int(jahr) + 1)] = 0

            def mv_nicht_aussetzen():
                dialog_mv.close()
                row["Mindest-Vertragsleistung-" + str(int(jahr) + 1)] = self.letzte_mindestabnahme(row["Ident"])

            with ui.dialog().style("width: 800px, max-width: none") as dialog_mv:
                with ui.card().style("width: 800px"):
                    with ui.row():
                        label_mv = ui.label("hallo")
                    with ui.row():
                        ui.label("Möchten Sie die Mindestabnahme auch im folgenden Jahr aussetzen?")
                    with ui.row():
                        button_ja = ui.button("Ja", on_click=mv_aussetzen)
                        button_nein = ui.button("Nein", on_click=mv_nicht_aussetzen)

            # Es werden alle Abnehmer durchgegangen. Wenn die Mindestvertragsleistung im Vorjahr 0 war, wird gefragt, ob dies wieder übernommen werden soll oder nicht.

            for row in self.anwendung.abnehmer_db:
                if row["Mindest-Vertragsleistung-" + str(int(jahr))] == 0:
                    label_mv.set_text("Für den Abnehmer " + row["Name"] + " " + row["Vorname"] + " mit der Anschluss-Nr. " + row["Ident"] + " wurde im Abrechnungsjahr die Mindestabnahme ausgesetzt.")
                    dialog_mv.open()
                    await dialog_mv
                else:
                    row["Mindest-Vertragsleistung-" + str(int(jahr) + 1)] = self.letzte_mindestabnahme(row["Ident"])

        def mindestabnahme_speichern(jahr):
            # Änderung 2.03: Zustand über die Ansicht bzw. gemeinsame Anwendung verwenden.
            self.anwendung.db_datei_speichern(self.anwendung.db_abnehmer, self.anwendung.abnehmer_db)
            ui.notify("Mindestabnahmen aktualisiert", type="positive")
            self.anwendung.abnehmer_aus_db()


        def abrechnung_speichern_exec():
            # Speichert neuen Abschlag und Abrechnung
            for abrechnung_row in self.abrechnung:
                for abschlag_row in self.anwendung.abschlag_db:
                    if abrechnung_row["Ident"] == abschlag_row["Ident"]:
                        abschlag_row["Abschlag-"+ str(abrechnung_row["Folgejahr"])] = abrechnung_row["neuer Abschlag"]
            self.anwendung.db_datei_speichern(self.anwendung.db_abschlag, self.anwendung.abschlag_db)
            self.anwendung.abschlag_aus_db()
            datei_speichern(self.datei_abrechnung_aktuell, self.abrechnung)
            ui.notify(self.text_bestaetigung, type="positive")
            self.abr_button_download.enable()
            self.abr_button_plausibel.enable()
            self.abr_button_pdf.enable()
            self.abr_button_speichern.disable()

        # Überprüft, ob Vorhandensein der Abrechnung erkannt wurde und blendet dann zusätzlich Checkbox für das Überschreiben ein

        def abrechnung_speichern_check():
            # Änderung 2.03: Zustand über die Ansicht bzw. gemeinsame Anwendung verwenden.
            self.text_bestaetigung = ""
            if self.checkbox_ueberschreiben.visible == True and self.checkbox_ueberschreiben.value == True:
                    self.checkbox_ueberschreiben.set_value(False)
                    self.text_bestaetigung = "Bestehende Abrechnungs-Datei und/oder Abschläge überschrieben"
                    abrechnung_speichern_exec()
                    self.dialog_abr_bestaetigung.close()
            elif self.checkbox_ueberschreiben.visible == False:
                    self.text_bestaetigung = "Abschläge und Abrechnungs-Datei gespeichert"
                    abrechnung_speichern_exec()
                    self.dialog_abr_bestaetigung.close()
            else:
                return

        def speichern_abbrechen():
            # Änderung 2.03: Zustand über die Ansicht bzw. gemeinsame Anwendung verwenden.
            self.speichern_abbruch = 1
            self.dialog_abr_bestaetigung.close()

        async def dialog_abfrage_speichern():
            # Änderung 2.03: Zustand über die Ansicht bzw. gemeinsame Anwendung verwenden.
            with ui.dialog() as self.dialog_abr_bestaetigung, ui.card():
                dialog_abr_label01 = ui.label('Möchten Sie die Abrechnungsdaten wirklich speichern?')
                self.checkbox_ueberschreiben = ui.checkbox('bestehende Daten überschreiben')
                if ueberschr == 1:
                    self.checkbox_ueberschreiben.set_visibility(visible=True)
                else:
                    self.checkbox_ueberschreiben.set_visibility(visible=False)
                with ui.row():
                    ui.button('Ja', on_click=abrechnung_speichern_check)
                    ui.button('Nein', on_click=speichern_abbrechen)
            self.dialog_abr_bestaetigung.open()
            await self.dialog_abr_bestaetigung


        # Prüft, ob die Verzeichnisse vorhanden sind und ob bereits eine Abrechnung besteht
        ueberschr = 0
        if self.abrechnung == []:
            ui.notify("Bitte erst Abrechnung erstellen, dann speichern.", type="info")
            return
        ordner_abrechnung_aktuell = self.anwendung.ordner_abrechnungen + "\\" + "Abrechnung-" + str(self.jahre_dropdown.value)
        pfad_ordner_abrechnung_aktuell = Path(ordner_abrechnung_aktuell)
        if not pfad_ordner_abrechnung_aktuell.exists():
            pfad_ordner_abrechnung_aktuell.mkdir()
        self.datei_abrechnung_aktuell = ordner_abrechnung_aktuell + "\\" + "Abrechnung-" + str(self.jahre_dropdown.value) + ".csv"
        if ("Abschlag-" + str((int(self.jahre_dropdown.value) + 1))) in self.anwendung.abschlag_db[0].keys() or Path(self.datei_abrechnung_aktuell).exists():
            ueberschr = 1
        self.speichern_abbruch = 0
        await dialog_abfrage_speichern()
        if self.speichern_abbruch == 0:
            await mindestabnahme_pruefen(self.jahre_dropdown.value)
            mindestabnahme_speichern(self.jahre_dropdown.value)
        self.abr_button_plausibel.enable()




    def umsatz_berechnen(self):
        abschlag_netto = 0
        for row in self.abrechnung:
            abschlag_netto=round(abschlag_netto + float(row["Zahlung Abschläge Netto"]) + float(row["Jahresabrechnung Netto"]),2)
        self.label_umsatz.set_text(str(abschlag_netto) + " €")

    def abrechnung_von_db(self):
        # Änderung 2.03: Zustand über die Ansicht bzw. gemeinsame Anwendung verwenden.
        datei_abrechnung = self.anwendung.ordner_abrechnungen + "\\" + "Abrechnung-" + str(self.jahre_dropdown.value) + "\\" + "Abrechnung-" + str(self.jahre_dropdown.value) + ".csv"
        self.abrechnung = datei_oeffnen(datei_abrechnung)
        self.abrechnung_grid_ui.refresh()
        self.abr_button_speichern.disable()
        self.abr_button_download.enable()
        self.abr_button_plausibel.enable()
        self.abr_button_pdf.enable()
        self.umsatz_berechnen()


    def zwischenablesung(self):
        if self.za_switch.value == True:
            self.za_mwst.visible = True
            self.za_datum.visible = True
            self.za_datum_auslesen()
        else:
            self.za_mwst.visible = False
            self.za_datum.visible = False
            return

    def za_datum_auslesen(self):
        # Änderung 2.03: Zustand über die Ansicht bzw. gemeinsame Anwendung verwenden.
        za_datum_list = []
        abrechnungsjahr = self.jahre_dropdown.value
        if abrechnungsjahr == None:
            ui.notify('Bitte zuerst Abrechnungsjahr auswählen.', type="info")
            return
        za_found = False
        for key in self.anwendung.zaehler_db[0].keys():
            if str(abrechnungsjahr) in key and "wechsel" not in key and (str(abrechnungsjahr) + "1231") not in key and (str(abrechnungsjahr) + "0101") not in key:
                print(abrechnungsjahr + " zw found")
                za_datum_list.append(key)
                za_found = True
        za_datum_list_format = []
        for element in za_datum_list:
            element_datum = element[6:8] + "." + element[4:6] + "." + element[0:4]
            za_datum_list_format.append(element_datum)
        if za_datum_list_format == []:
            self.za_switch.value = False
            ui.notify('Abrechnungsjahr ' + abrechnungsjahr + ' hat keine Zwischenablesung.', type="info")
        self.za_datum.set_options(za_datum_list_format)

    # Prüfung, ob Verbrauch zum Vorjahr abweicht

    def abrechnung_plausibel(self):

        if (str(int(self.jahre_dropdown.value) - 1)) not in self.jahrliste_einlesbar:
            ui.notify("Abrechnung Vorjahr ist nicht vorhanden.", type='warning')
            return

        def plausibel_verbrauch_grid_update():
            columns = [
                {"haederName": "Ident", "field": "Ident", "maxWidth": "150"},
                {"headerName": "Name", "field": "Name"},
                {"headerName": "Vorname", "field": "Vorname"},
                {"headerName": "Abweichung zum Vorjahr kWh", "field": "Abweichung zum Vorjahr kWh",'cellClassRules': {
                'bg-red-300': 'x > 3000 || x < -3000',
                'bg-green-300': 'x > -3000 && x < 3000',
            }}
            ]

            self.plausibel_verbrauch_grid.options['columnDefs'] = columns
            self.plausibel_verbrauch_grid.options['rowData'] = self.pruef_erg_verbrauch
            self.plausibel_verbrauch_grid.options['rowSelection'] = 'multiple'
            self.plausibel_verbrauch_grid.options['pagination'] = 'false'
            self.plausibel_verbrauch_grid.options['paginationPageSize'] = '15'
            self.plausibel_verbrauch_grid.options['alwaysShowHorizontalScroll'] = 'true'
            self.plausibel_verbrauch_grid.options['fullWidthCellRenderer'] = 'fullWidthCellRenderer'
            self.plausibel_verbrauch_grid.update()

        def plausibel_mindestabnahme_grid_update():
            columns = []
            column_element = {}
            if self.pruef_erg_mindestabnahme != []:
                for key in self.pruef_erg_mindestabnahme[0].keys():
                    column_element = {}
                    column_element['headername'] = key
                    column_element["field"] = key
                    columns.append(column_element)

                self.plausibel_mindestabnahme_grid.options['columnDefs'] = columns
                self.plausibel_mindestabnahme_grid.options['rowData'] = self.pruef_erg_mindestabnahme
                self.plausibel_mindestabnahme_grid.options['rowSelection'] = 'multiple'
                self.plausibel_mindestabnahme_grid.options['pagination'] = 'false'
                self.plausibel_mindestabnahme_grid.options['paginationPageSize'] = '15'
                self.plausibel_mindestabnahme_grid.options['alwaysShowHorizontalScroll'] = 'true'
                self.plausibel_mindestabnahme_grid.options['fullWidthCellRenderer'] = 'fullWidthCellRenderer'
                self.plausibel_mindestabnahme_grid.update()

        def pruefung_verbrauch():
            # Änderung 2.03: Zustand über die Ansicht bzw. gemeinsame Anwendung verwenden.
            # Aktuelle Abrechnung wird mit Abrechnung von Vorjahr verglichen
            datei_vorjahr = self.anwendung.ordner_abrechnungen + "\\" + "Abrechnung-" + str(int(self.jahre_dropdown.value)-1) + "\\" + "Abrechnung-" + str(int(self.jahre_dropdown.value)-1) + ".csv"
            abrechnung_vorjahr = datei_oeffnen(datei_vorjahr)
            ergebnis = []
            for anschluss in self.abrechnung:
                ergebnis_row = {}
                ergebnis_row["Ident"] = anschluss["Ident"]
                ergebnis_row["Name"] = anschluss["Name"]
                ergebnis_row["Vorname"] = anschluss["Vorname"]
                for anschluss_vorjahr in abrechnung_vorjahr:
                    if anschluss["Ident"] == anschluss_vorjahr["Ident"]:
                        abweichung_real = float(anschluss["verbrauchte kWh"]) - float(anschluss_vorjahr["verbrauchte kWh"])
                        abweichung = abs(abweichung_real)
                        ergebnis_row["Abweichung zum Vorjahr kWh"] = abweichung_real
                        ergebnis_row["Abw absolut"] = abweichung
                ergebnis.append(ergebnis_row)
            ergebnis_temp = ergebnis
            self.pruef_erg_verbrauch = sorted(ergebnis_temp, key=lambda x: x["Abw absolut"], reverse=True)

        def pruefung_mindestabnahme():
            # Änderung 2.03: Zustand über die Ansicht bzw. gemeinsame Anwendung verwenden.
            ergebnis = []
            for anschluss in self.abrechnung:
                ergebnis_row = {}
                for anschluss_abnehmer in self.anwendung.abnehmer_db:
                    if anschluss["Ident"] == anschluss_abnehmer["Ident"]:
                        if str(anschluss["Mindestvertragsleistung"]) != str(anschluss_abnehmer["Mindest-Vertragsleistung-" + str(int(anschluss["Abrechnungsjahr"])+1)]):
                            ergebnis_row["Ident"] = anschluss["Ident"]
                            ergebnis_row["Name"] = anschluss["Name"]
                            ergebnis_row["Vorname"] = anschluss["Vorname"]
                            ergebnis_row["Mindestabnahme-" + anschluss["Abrechnungsjahr"]] = anschluss["Mindestvertragsleistung"]
                            ergebnis_row["Mindestabnahme-" + str(int(anschluss["Abrechnungsjahr"])+1)] = anschluss_abnehmer["Mindest-Vertragsleistung-" + str(int(anschluss["Abrechnungsjahr"])+1)]
                            ergebnis.append(ergebnis_row)
            self.pruef_erg_mindestabnahme = ergebnis

        with ui.dialog().style("width: 800px; max-width: none") as dialog_plausibel:
            # Änderung 2.03: Zustand über die Ansicht bzw. gemeinsame Anwendung verwenden.
            with ui.card().style("width: 800px"):
                ui.button('', icon='close', on_click=dialog_plausibel.close).classes('absolute top-3 right-3')
                with ui.row():
                    ui.label('Plausibilitätsprüfung').style("font-size: 24px; font-weight: bold;")
                with ui.row():
                    ui.label('Aufstellung Veränderung der verbrauchten kWh zum Vorjahr. Es werden alle Abweichungen (positiv wie negativ) größer als 3000 kWh in "Rot" angezeigt.')
                    columns = []
                    table = []
                    self.plausibel_verbrauch_grid = ui.aggrid({
                        'defaultColDef': {'flex': 1, 'editable': False, 'resizable': True, 'wrapHeaderText': True, 'autoHeaderHeight': True, 'wrapText': True, 'autoHeight': True},
                        'columnDefs': columns,
                        'rowData': table,
                        'domLayout': 'normal',
                    }).style('height: 300px; width: 500px')
                with ui.row():
                    ui.label('Veränderungen bei Mindestabnahme')
                    columns = []
                    table = []
                    self.plausibel_mindestabnahme_grid = ui.aggrid({
                        'defaultColDef': {'flex': 1, 'editable': False, 'resizable': True, 'wrapHeaderText': True, 'autoHeaderHeight': True, 'wrapText': True, 'autoHeight': True},
                        'columnDefs': columns,
                        'rowData': table,
                        'domLayout': 'normal',
                    }).style('height: 300px; width: 500px')

        dialog_plausibel.open()
        pruefung_verbrauch()
        plausibel_verbrauch_grid_update()
        pruefung_mindestabnahme()
        plausibel_mindestabnahme_grid_update()


    def abrechnung_columns_erstellen(self, table):
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

                columns.append(column_element)

        return columns


    @ui.refreshable
    def abrechnung_grid_ui(self):
        # Änderung 2.03: Zustand über die Ansicht bzw. gemeinsame Anwendung verwenden.
        self.abrechnung_grid = ui.aggrid({
            'defaultColDef': {
                'editable': False,
                'resizable': True,
                'wrapHeaderText': True,
                'autoHeaderHeight': True,
            },
            'columnDefs': self.abrechnung_columns_erstellen(self.abrechnung),
            'rowData': self.abrechnung,
            'domLayout': 'autoHeight',
            'pagination': True,
            'paginationPageSize': self.anwendung.pagination
        }).style('height: 100%')



    def abrechnung_ui(self):
        # Änderung 2.03: Zustand über die Ansicht bzw. gemeinsame Anwendung verwenden.
        ui.label('Jahresabrechnung Wärmelieferung').classes("text-2xl font-bold")
        with ui.row():
            self.jahre_dropdown = ui.select([], label='Abrechnungsjahr', on_change=self.reset_abrechnung).classes('w-48')
            self.mwst_jahr = ui.select(['7','19'], label='Mehrwertsteuer in %').classes('w-48')
            self.za_switch = ui.switch("Zwischenablesung", on_change=self.zwischenablesung)
            self.za_datum = ui.select([], label='Datum Zwischenabl.').classes('w-48').props('visible=false')
            self.za_datum.visible = False
            self.za_mwst = ui.select(['7','19'], label='MwSt. % bis Zwischenabl.').classes('w-48')
            self.za_mwst.visible = False
            self.abr_button_speichern = ui.button('Speichern', icon='save', on_click=self.abr_speichern).props('color=' + self.anwendung.speichernbutton)
            self.abr_button_speichern.disable()

        with ui.row():
            self.abr_button_erstellen = ui.button('Erstellung Jahresabrechnung', icon='calculate', on_click=self.abrechnung_erstellen_gui)
            self.abr_button_einlesen = ui.button('Jahresabrechnung von DB einlesen', icon='file_open', on_click=self.abrechnung_von_db)
            self.abr_button_erstellen.disable()
            self.abr_button_einlesen.disable()
            self.abr_button_download = ui.button('CSV mit Kommas herunterladen', icon='file_download', on_click=self.csv_komma_abrechnung_download)
            self.abr_button_download.disable()
            self.abr_button_plausibel = ui.button("Plausibilitätsprüfung", icon="check_circle", on_click=self.abrechnung_plausibel)
            self.abr_button_plausibel.disable()
            self.abr_button_pdf = ui.button('Word/PDF-Abrechnungen erzeugen', icon='picture_as_pdf', on_click=self.abrechnungen_dateien_erstellen).props('color=red-5')
            self.abr_button_pdf.disable()
            self.abr_progress_pdf = ui.circular_progress(min=0, max=100, color="black").classes('invisible')
            ui.label('Gesamtumsatz netto: ')
            self.label_umsatz = ui.label("")
        self.abrechnung_grid_ui()


    async def csv_komma_abrechnung_download(self):
        filename = "Abrechnung " + self.jahre_dropdown.value + ".csv"
        await self.anwendung.komma_datei_speichern(self.abrechnung, filename)

    def abrechnung_erstellen_gui(self):
        # Änderung 2.03: Zustand über die Ansicht bzw. gemeinsame Anwendung verwenden.
        for row in self.anwendung.zaehler_db:
            if "-1" in row.values():
                ui.notify("Es sind ungültige Zählerdaten vorhanden. Bitte Zählerdaten überprüfen.", type="negative")
                return
        if self.jahre_dropdown.value == None or self.mwst_jahr.value == None:
            ui.notify("Bitte Jahr und Mwst-Satz auswählen.", type="info")
            return
        # Änderung für v2: Rechnen ohne Oberfläche; Meldungen und Anzeige bleiben hier.
        self.abrechnung = abrechnung_berechnen(
            self.anwendung.abnehmer_db, self.anwendung.zaehler_db, self.anwendung.abschlag_db, self.anwendung.arbeitspreis, self.anwendung.grundgebuehr,
            self.jahre_dropdown.value, self.mwst_jahr.value, self.za_switch.value, self.za_datum.value,
            self.za_mwst != [], self.za_mwst.value if self.za_mwst != [] else None)

        self.abrechnung_grid_ui.refresh()
        self.abr_button_speichern.enable()
        self.abr_button_download.enable()
        self.umsatz_berechnen()

    #### Letzte Mindestabhnahme, die nicht 0 ist ermitteln. Wenn keine vorhanden, dann Original-Mindestabnahme


    def letzte_mindestabnahme(self, Ident):
        # Änderung für v2: Bestehende Aufrufe behalten; Daten explizit an das Rechenmodul übergeben.
        return mindestabnahme_berechnen(Ident, self.anwendung.abnehmer_db)


    def abrechnungen_dateien_erstellen(self):
        self.abrechnungen_word_erstellen()
        self.abrechnungen_pdf_erstellen()

    def abrechnungen_word_erstellen(self):
        # Änderung 2.03: Zustand über die Ansicht bzw. gemeinsame Anwendung verwenden.
        self.ordner_abrechnungen_word = self.anwendung.ordner_abrechnungen + "\\" + "Abrechnung-" + self.jahre_dropdown.value + "\\word"
        pfad_ordner_abrechnungen_word = Path(self.ordner_abrechnungen_word)
        if not pfad_ordner_abrechnungen_word.exists():
            pfad_ordner_abrechnungen_word.mkdir()
        self.anwendung.dateien_in_ordner_loeschen(self.ordner_abrechnungen_word)
        ordner_abrechnung_jahr = self.anwendung.ordner_abrechnungen + "\\" + "Abrechnung-" + str(self.jahre_dropdown.value)
        datei_abrechnung =  ordner_abrechnung_jahr + "\\" + "Abrechnung-" + str(self.jahre_dropdown.value) + ".csv"
        pfad_datei_abrechnung = Path(datei_abrechnung)
        if not pfad_datei_abrechnung.exists():
            ui.notify("Bitte erst Abrechnung für Jahr " + self.jahre_dropdown.value + " abspeichern.", type="info")
            return
        dateiname_vorlage = "Vorlage-Abrechnung-" + str(self.jahre_dropdown.value) + ".docx"
        datei_vorlage_abrechnung = self.anwendung.ordner_vorlagen + "\\" + dateiname_vorlage
        pfad_datei_vorlage_abrechnung = Path(datei_vorlage_abrechnung)
        if not pfad_datei_vorlage_abrechnung.exists():
            ui.notify("Bitte Datei " + dateiname_vorlage + " in Ordner " + self.anwendung.ordner_vorlagen + " ablegen.", type="info")
            return
        self.abrechnung_fuer_pdf = datei_oeffnen(datei_abrechnung)
        # Änderung für v2: Vorprüfungen bleiben hier; die Serienschleife liegt im Dokumentmodul.
        abrechnung_word_schreiben(self.abrechnung_fuer_pdf, datei_vorlage_abrechnung,
                                 self.ordner_abrechnungen_word, self.jahre_dropdown.value,
                                 mapping_wordfelder)

    def abrechnungen_pdf_erstellen(self):
        # Änderung 2.03: Zustand über die Ansicht bzw. gemeinsame Anwendung verwenden.
        docx_files_found = 0
        self.ordner_abrechnungen_pdf = self.anwendung.ordner_abrechnungen + "\\" + "Abrechnung-" + self.jahre_dropdown.value + "\\pdf"
        pfad_ordner_abrechnungen_pdf = Path(self.ordner_abrechnungen_pdf)
        if not pfad_ordner_abrechnungen_pdf.exists():
            pfad_ordner_abrechnungen_pdf.mkdir()
        word_ordner = os.listdir(self.ordner_abrechnungen_word)
        for datei in word_ordner:
                if datei.endswith('docx'):
                    docx_files_found = 1
        if docx_files_found == 0:
            return
        self.anwendung.dateien_in_ordner_loeschen(self.ordner_abrechnungen_pdf)
        self.abrechnung_pdf_background = threading.Thread(target=self.abr_pdf_process)
    #    pdf_stop_flag = threading.Event()
        self.abrechnung_pdf_background.start()
        self.abr_progress_pdf.classes(remove='invisible')


    # PDF Verarbeitung Performance-optimiert

    def abr_pdf_process(self):
        # Änderung für v2: Hintergrund-Thread und Fortschrittsanzeige bleiben an dieser Schnittstelle.
        abrechnung_pdf_konvertieren(self.ordner_abrechnungen_word, self.ordner_abrechnungen_pdf,
                                   self.abr_progress_pdf.set_value)
