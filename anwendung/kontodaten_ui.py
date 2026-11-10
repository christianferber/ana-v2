"""Änderung 2.036: Kontodatenoberfläche mit eigenem Tabellen- und Bedienzustand."""
# Änderung: Änderungsprotokoll ergänzen; vorhandene Fachlogik unverändert ausführen.
from anwendung.aenderungsprotokoll import aenderungen_protokollieren
from io import StringIO
from nicegui import events, ui
from schwifty import IBAN
from anwendung.datenhaltung import import_csv_inhalt


class KontodatenOberflaeche:
    # Änderung: Gemeinsame Daten und Exportauswahl über die Anwendung lesen.
    def __init__(self, anwendung):
        self.anwendung = anwendung

    def konto_label_ui(self, label):
        # Änderung 2.036: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        ui.label(label).style('font-size:100%')

    def konto_upload(self, e: events.UploadEventArguments):
        # Änderung: Tatsächliche Daten-/Dateiänderungen zusätzlich protokollieren.
        with aenderungen_protokollieren(
            self.anwendung, 'KONTODATEN', 'Kontodaten importieren',
            daten=lambda: {'Kontodaten': self.anwendung.konto_db},
        ):
            # Änderung 2.036: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
            with StringIO(e.content.read().decode('iso-8859-1', errors='ignore')) as f:
                self.anwendung.konto_db = import_csv_inhalt(f)
            templist = []
            for row in self.anwendung.konto_db:
                temprow = {}
                for key,value in row.items():
                    if key == "Ident":
                        temprow[key] = int(value)
                    elif key == "Name" or key == "Vorname" or key == "Zahlungspflichtiger":
                        temprow[key] = str(value)
                    elif key == "IBAN des Zahlungspflichtigen":
                        temprow["IBAN"] = IBAN(str(value)).formatted
                    elif key == "BIC":
                        temprow["BIC"] = str(value)
                    elif key == "Bei Kreditinstitut":
                        temprow["Bank"] = str(value)
                    elif key == "Unterschrieben am":
                        temprow["Datum SEPA-Auftrag"] = str(value)
                iban = IBAN(temprow["IBAN"])
                temprow["BIC"] = iban.bic
                temprow["Bank"] = iban.bank_name
                templist.append(temprow)
            self.anwendung.konto_db = templist
            self.anwendung.konto_db = sorted(self.anwendung.konto_db, key=lambda k: k['Ident'])
            self.anwendung.konto_grid_ui.refresh()

    def db_konto_speichern(self):
        # Änderung 2.036: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        self.anwendung.db_datei_speichern(self.anwendung.db_konto, self.anwendung.konto_db)
        self.button_konto_speichern.disable()
        ui.notify("Kontodaten gespeichert.", type="positive")

    def konto_aus_db(self):
        # Änderung 2.036: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        self.anwendung.konto_db = self.anwendung.db_datei_oeffnen(self.anwendung.db_konto)
        self.anwendung.konto_grid_ui.refresh()

    def konto_columns_erstellen(self, table):
        # Änderung 2.036: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
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
                    column_element["minWidth"] = 200

                if key in ("Ident", "Name", "Vorname"):
                    column_element["pinned"] = 'left'

                column_element["filter"] = 'agTextColumnFilter'
                column_element["floatingFilter"] = True

                if key in ("Zahlungspflichtiger", "IBAN", "Datum SEPA-Auftrag"):
                    column_element["editable"] = True
                    column_element["cellStyle"] = {'backgroundColor': self.anwendung.col_cell_mod}
                    column_element["cellEditor"] = 'agStringCellEditor'

                columns.append(column_element)

        return columns

    def konto_grid_ui(self):
        # Änderung 2.036: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        self.konto_grid = ui.aggrid({
            'defaultColDef': {
                'editable': False,
                'resizable': True,
                'wrapHeaderText': True,
                'autoHeaderHeight': True,
            },
            'columnDefs': self.anwendung.konto_columns_erstellen(self.anwendung.konto_db),
            'rowData': self.anwendung.konto_db,
            'domLayout': 'autoHeight',
            'pagination': True,
            'paginationPageSize': self.anwendung.pagination
        }).on(
            'cellValueChanged',
            lambda event: self.anwendung.buchung_tabelle_on_change(event.args)
        ).style('height: 100%')

    def buchung_tabelle_on_change(self, event):
        # Änderung: Tatsächliche Daten-/Dateiänderungen zusätzlich protokollieren.
        with aenderungen_protokollieren(
            self.anwendung, 'KONTODATEN', 'Kontodaten bearbeiten',
            daten=lambda: {'Kontodaten': self.anwendung.konto_db},
        ):
            # Änderung 2.036: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
            if event["newValue"] == None:
                return
            # IBAN wird geprüft und nur bei ok eingesetzt. Dazu wird sie mit Leerzeichen formatiert
            if event["colId"] == "IBAN":
                if IBAN(str(event["newValue"]).replace(" ",""), allow_invalid=True).is_valid:
                    iban = IBAN(event["newValue"])
                    self.anwendung.konto_db[int(event["rowId"])][event["colId"]] = iban.formatted
                    self.anwendung.konto_db[int(event["rowId"])]["BIC"] = iban.bic
                    self.anwendung.konto_db[int(event["rowId"])]["Bank"] = iban.bank_name
                    self.anwendung.konto_grid_ui.refresh()
                else:
                    ui.notify('IBAN ist nicht korrekt. Änderung nicht gespeichert.', type="negative")
                    self.anwendung.konto_grid_ui.refresh()
                    return
            else:
                self.anwendung.konto_db[int(event["rowId"])][event["colId"]] = event["newValue"]
            self.button_konto_speichern.enable()
            self.anwendung.change_log("KONTODATEN", event)

    def buchung_ui(self):
        # Änderung 2.036: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        self.anwendung.konto_label_ui('')
        with ui.row():
            ui.upload(label='Upload Lastschriftvorlage',on_upload=self.anwendung.konto_upload, auto_upload=True, max_files=1).props("accept=.csv").classes('max-w-full')
            self.button_konto_speichern = ui.button('Speichern', icon='save', on_click=lambda: (self.anwendung.db_konto_speichern())).props('color=' + self.anwendung.speichernbutton)
            self.button_konto_speichern.disable()
        self.anwendung.konto_grid_ui()
        ui.label('Betreiber Name: ' + self.anwendung.betreiber_name)
        ui.label('Betreiber IBAN: ' + self.anwendung.betreiber_iban)
        ui.label('Betreiber Mandatsreferenz: ' + self.anwendung.betreiber_glaeubigerid)
        with ui.row():
            ui.button('CSV Grundgebühr erzeugen', icon='save_alt', on_click=lambda: (self.anwendung.csv_grundgebuehr_speichern()))
        with ui.row():
            self.anwendung.abschlagsjahr_dropdown = ui.select([], label='Jahr Abschlag').classes('w-48')
            self.anwendung.quartal_dropdown = ui.select(['Q1','Q2','Q3','Q4'], label='Quartal').classes('w-48')
        with ui.row():
            ui.button('CSV Abschlag erzeugen', icon='save_alt', on_click=lambda: (self.anwendung.csv_abschlag_speichern()))
        with ui.row():
            self.anwendung.vonnetto_switch = ui.switch("Abrechnungsbeträge von Netto erzeugen", value=True)
        with ui.row():
            self.anwendung.abrechnungsjahr_dropdown = ui.select([], label='Jahr Abrechnung').classes('w-48')
    #   with ui.row():
    #       ui.button('CSV Lexware Rechnungen für Jahresabrechnung erzeugen', icon='euro').props('color=red-5')
        with ui.row():
            ui.button('CSV Lastschriften für Jahresabrechnung erzeugen', icon='save_alt', on_click=lambda: (self.anwendung.csv_abrechnung_lastschrift_speichern()))
            ui.button('CSV Überweisungen für Jahresabrechnung erzeugen', icon='save_alt', on_click=lambda: (self.anwendung.csv_abrechnung_ueberweisung_speichern()))
        with ui.row():
            self.anwendung.rueckvjahr_dropdown = ui.select([], label='Jahr Rückvergütung').classes('w-48')
    #   with ui.row():
    #       ui.button('CSV Lexware Rechnungskorrekturen für Rückvergütung erzeugen', icon='euro').props('color=red-5')
        with ui.row():
            ui.button('CSV Überweisungen für Rückvergütung erzeugen', icon='save_alt', on_click=lambda: (self.anwendung.csv_rueckv_speichern()))
        if self.anwendung.db_datei_oeffnen(self.anwendung.db_konto)[0] == "file not found":
            self.anwendung.konto_label_ui.refresh('Keine Kontodaten in Datenbank! Upload Kontodaten per CSV-Datei möglich.')
        else:
            self.anwendung.db_konto_found = 1
            self.anwendung.konto_label_ui.refresh('Kontodaten wurden aus DB geladen. Daten aus Datenbank können über einen neuen Upload überschrieben werden.')
            self.anwendung.konto_aus_db()
