
# Mail bei Mitglieder implementieren
# Serienbrief PDF implementieren
# Diagramme für Auswertung implementieren
# Weitere Felder für Anreden bei Serienbrief implementieren

# Änderung für v2: Dateihilfen zentral aus datenhaltung laden; Aufrufe bleiben gleich.
from datenhaltung import (check_ordner_exists, datei_oeffnen, datei_speichern,
                         dictlist_to_csv, import_file, import_csv_inhalt)
# Änderung für v2: Arbeitsordnerpfade unabhängig von der Oberfläche erzeugen.
from einstellungen import pfade_erstellen, ini_datei_lesen, ini_datei_schreiben
# Änderung für v2: Dokumentverarbeitung erhält Daten, Pfade und Fortschrittsrückruf explizit.
from dokumente import abrechnung_word_schreiben, abrechnung_pdf_konvertieren
# Änderung für v2: Auch die Rückvergütungsdokumente über das Dokumentmodul verarbeiten.
from dokumente import rueckverguetung_word_schreiben, rueckverguetung_pdf_konvertieren
# Änderung für v2: Dokumentfeldformatierung ohne GUI- und Word-Abhängigkeiten laden.
from dokumentfelder import (format_fuer_serienbrief, form_betrag, form_zaehler,
                            form_mwst, form_rvsatz, mapping_wordfelder)

# Änderung für v2: Berechnung und gemeinsame Hilfen ohne GUI-Abhängigkeit laden.
from berechnungen import (abrechnung_berechnen, abnehmer_aus_daten, mwst_berechnen,
                           datum_in_string, datum_in_punkt, datum_tage_vorher)
from berechnungen import letzte_mindestabnahme as mindestabnahme_berechnen

# Änderung für v2: Rückvergütung ohne Oberfläche berechnen.
from berechnungen import rueckverguetung_vorbereiten, rueckverguetung_berechnen

# Änderung für v2: CSV-Inhalte ohne Oberfläche erzeugen; Speicher- und Eingabedialoge bleiben hier.
from buchungsvorlagen import (grundgebuehr_csv, abschlag_csv, abrechnung_lastschrift_csv,
                             abrechnung_ueberweisung_csv, rueckverguetung_csv)
from berechnungen import round_half_up

from nicegui import events,app,native,ui
import threading                                                    # Zur Ausführung von Hintergrund-Tasks (z.B. PDF-Generierung)

import time    
time.sleep(0.5)
import csv
from io import StringIO
import re                                                           # für PDF Merger
from pypdf import PdfReader, PdfWriter                              # für PDF Merger
import os
from pathlib import Path
import shutil
from datetime import datetime, timedelta, date
from mailmerge import MailMerge
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT
from docx.shared import Inches
from docx.shared import Pt                                          # Für Fontgrößen
from docx.oxml import OxmlElement                                   # Benötigt, um Tabellenzeilen bei Seitenübergang nicht zu trennen
from docx2pdf import convert
from win32com.client import Dispatch                                # PDF Konvertierung, Word nur 1x eröffnen
import pythoncom                                                    # Benötigt, damit threading nach Kompilierung funktioniert
from schwifty import IBAN
import webview                                                      # Für Datei speichern dialog
from collections import Counter
import configparser                                                 # Für INI-Dateien
import plotly.graph_objects as go                                   # Für Diagramme / Statistiken
from decimal import Decimal, ROUND_HALF_UP                          # Für Schulrundung (bei 5 aufrunden)
import re                                                           # ersetzt Variablen für Serienbrief
import pandas as pd

### Settings

db_mitglieder = 'db_mitglieder.csv'
db_wartung = 'db_wartung.csv'
db_abnehmer = 'db_abnehmer.csv'
db_abschlag = 'db_abschlag.csv'
db_zaehler = 'db_zaehler.csv'
db_konto = 'db_kontodaten.csv'
changelog = 'ana-change.log'

ini = 'ana.ini'
ini_betreiber = 'ana-betreiber.ini'
# Änderung für v2: Erste freigegebene Version gemäß AGENTS.md.
version = 2.00
zaehler_liste = []
abrechnung = []
abrechnung_fuer_pdf = []
mitglieder_db = []
wartung_db = []
abnehmer_db = []
zaehler_db = []
abschlag_db = []
konto_db = []
db_abnehmer_found = 0
db_zaehler_found = 0
db_abschlag_found = 0
db_konto_found = 0
naechstes_jahr = ""
mitglieder_selected_row = None
wartung_selected_row = None
speichernbutton = "dark"

arbeitsordner = ""

pdfordner1_pfad = ""
pdfordner2_pfad = ""
ausgabeordner_pfad = ""
label_ordner1 = None
label_ordner2 = None
label_ausgabe = None
log_feld = None

###########################################################################################################################
### ANFANG EINSTELLUNGEN
###########################################################################################################################

def pfade_setzen():
    # Wird beim Einlesen der ini ausgeführt
    global ordner_abrechnungen, ordner_rueckv, ordner_logs, ordner_datenbank, ordner_sicherungen, ordner_downloads, ordner_vorlagen, arbeitsordner
    # Änderung für v2: Pfadbildung auslagern; bestehende globale Werte weiter bereitstellen.
    pfade = pfade_erstellen(arbeitsordner)
    arbeitsordner = pfade['arbeitsordner']
    ordner_abrechnungen = pfade['ordner_abrechnungen']
    ordner_rueckv = pfade['ordner_rueckv']
    ordner_logs = pfade['ordner_logs']
    ordner_datenbank = pfade['ordner_datenbank']
    ordner_sicherungen = pfade['ordner_sicherungen']
    ordner_downloads = pfade['ordner_downloads']
    ordner_vorlagen = pfade['ordner_vorlagen']

def ini_einlesen():
    global betreiber_name 
    global betreiber_glaeubigerid 
    global betreiber_iban 
    global arbeitspreis
    global grundgebuehr
    global col_special
    global col_cell_mod
    global pagination
    global arbeitsordner
    config = configparser.ConfigParser()
    inifile = Path(ini)
    if inifile.is_file():
        # Änderung für v2: INI-Dateizugriff über das Einstellungsmodul ausführen.
        config = ini_datei_lesen(ini)
        col_special = config['Anwendung']['FarbeSpezial']
        col_cell_mod = config['Anwendung']['FarbeTabelleEdit']
        pagination = config['Anwendung']['TabellenZeilenProSeite']
        arbeitsordner = config['Anwendung']['Arbeitsordner']
    else:
        col_special = 'light-blue-10'
        pagination = 12
        arbeitsordner = ""
        config['Anwendung'] = { 'FarbeSpezial' : col_special,
                                'FarbeTabelleEdit' : col_cell_mod,
                                'TabellenZeilenProSeite' : pagination,
                                'Arbeitsordner': arbeitsordner}
        # Änderung für v2: Schreibzugriff ausgelagert; Zeitpunkt bleibt unverändert.
        ini_datei_schreiben(ini, config)
        with ui.dialog() as dialog_inierstellt, ui.card():
            ui.label('ana.ini war nicht vorhanden und wurde mit Standardwerten erstellt. Die Einstellungen können über das Zahnradsymbol angepasst werden')
            ui.button("OK", icon='check_circle', on_click=dialog_inierstellt.close)
        dialog_inierstellt.open()
    if not Path(arbeitsordner).exists():
        arbeitsordner = ""
        config['Anwendung']["Arbeitsordner"] = arbeitsordner
        # Änderung für v2: Korrigierten Arbeitsordner wie bisher sofort speichern.
        ini_datei_schreiben(ini, config)

    # INI Betreiberdatei wird einlesesen oder angelegt
            
    if arbeitsordner != "":
        inibetreiberfile = Path(str(arbeitsordner) + "\\" + ini_betreiber)
    else:
        inibetreiberfile = Path(ini_betreiber)
    config_betreiber = configparser.ConfigParser()
    if inibetreiberfile.is_file():
        # Änderung für v2: Auch Betreibereinstellungen zentral lesen.
        config_betreiber = ini_datei_lesen(inibetreiberfile)
        betreiber_name = config_betreiber['Betreiber']['BetreiberName']
        betreiber_glaeubigerid = config_betreiber['Betreiber']['GlaeubigerID']
        betreiber_iban = config_betreiber['Betreiber']['BetreiberIBAN']

        arbeitspreis = float(config_betreiber['Betreiber']['Waermepreis'])
        grundgebuehr = float(config_betreiber['Betreiber']['Grundgebuehr'])
    else:
        betreiber_name = 'leer'
        betreiber_glaeubigerid = 'leer'
        betreiber_iban = 'leer'
        arbeitspreis = 6.5
        grundgebuehr = 12       
        config_betreiber = configparser.ConfigParser()
        config_betreiber['Betreiber'] = { 'BetreiberName' : betreiber_name,
                                'GlaeubigerID' : betreiber_glaeubigerid,
                                'BetreiberIBAN' : betreiber_iban,
                                'Waermepreis' : arbeitspreis,
                                'Grundgebuehr' : grundgebuehr}
        # Änderung für v2: Bisherige Standardwerte über das Einstellungsmodul schreiben.
        ini_datei_schreiben(inibetreiberfile, config_betreiber)

    pfade_setzen()
    

def einstellungen_ui():
    global ini_betreiber_name, ini_glaeubiger_id, ini_betreiber_iban, ini_arbeitspreis, ini_grundgebuehr, ini_farbe_spezial, ini_farbe_tabelle_edit, ini_tabelle_pagination, ini_arbeitsordner, dialog_einstellungen, dialog_neustart
    ini_einlesen()
    with ui.dialog() as dialog_einstellungen, ui.card():
        ui.label('Betreiberdaten').style('font-size: 120%')
        ini_betreiber_name = ui.input(label='Betreiber Name', value=betreiber_name).props("size=60")
        ini_glaeubiger_id = ui.input(label='Gläubiger ID', value=betreiber_glaeubigerid).props("size=60")
        ini_betreiber_iban = ui.input(label='Betreiber IBAN', value=betreiber_iban).props("size=60")
        ini_arbeitspreis = ui.input(label='Wärmepreis (Ct/kWh)', value=arbeitspreis).props("size=60")
        ini_grundgebuehr = ui.input(label='Grundgebühr (€ pro Monat)', value=grundgebuehr).props("size=60")
        ui.label('')
        ui.label('Programmkonfiguration').style('font-size: 120%')
        ini_farbe_spezial = ui.input(label='Farbe für besondere Hervorhebungen (Farbe als Text)', value=col_special).props("size=60")
        ini_farbe_tabelle_edit = ui.input(label='Farbe für editierbare Tabellenzellen (#ABCDEF)', value=col_cell_mod).props("size=60")
        ini_tabelle_pagination = ui.input(label='Anzahl Zeilen pro Tabellenseite', value=pagination).props("size=60")
        ui.label('Arbeitsordner:')
        with ui.row():
            ui.button("auswählen", icon='folder', on_click=lambda: (ordner_auswaehlen()))
            ui.button("Auf standard zurücksetzen", icon='folder_special', on_click=lambda: (ordner_standard()))
        ini_arbeitsordner = ui.label(arbeitsordner)
        with ui.row():
            ui.button("Speichern", icon='save', on_click=lambda: (ini_speichern())).props('color=' + speichernbutton)
            ui.button("Abbrechen", icon='close', on_click=dialog_einstellungen.close)
    with ui.dialog() as dialog_neustart, ui.card():
        ui.label('Der Arbeitsordner wurde geändert. Das Programm wird jetzt automatisch geschlossen. Beim nächsten Programmstart wird die neue Arbeitsordnereinstellung verwendet.')
        ui.button("OK", on_click=app.shutdown)
    dialog_einstellungen.open()

def ordner_standard():
    global ini_arbeitsordner
    ini_arbeitsordner.set_text('')

async def ordner_auswaehlen():
    global ini_arbeitsordner
    ordner_pfad = await app.native.main_window.create_file_dialog(webview.FOLDER_DIALOG)
    ordner_pfad = str(ordner_pfad).replace("(","")
    ordner_pfad = str(ordner_pfad).replace(")","")
    ordner_pfad = str(ordner_pfad).replace(",","")
    ordner_pfad = str(ordner_pfad).replace("'","")
    ordner_pfad = str(ordner_pfad).replace("\\\\","\\")
    ini_arbeitsordner.set_text(ordner_pfad)

def ini_speichern():
    global dialog_einstellungen
    config = configparser.ConfigParser()
    config['Anwendung'] = { 'FarbeSpezial' : ini_farbe_spezial.value,
                            'FarbeTabelleEdit' : ini_farbe_tabelle_edit.value,
                            'TabellenZeilenProSeite' : ini_tabelle_pagination.value,
                            'Arbeitsordner' : ini_arbeitsordner.text}
    # Änderung für v2: Nur der Dateizugriff ist ausgelagert; Dialogablauf bleibt bestehen.
    ini_datei_schreiben(ini, config)
    if arbeitsordner != ini_arbeitsordner.text:
        dialog_neustart.open()
    dialog_einstellungen.close()

    config_betreiber = configparser.ConfigParser()
    inibetreiberfile = Path(str(arbeitsordner) + "\\" + ini_betreiber)

    config_betreiber['Betreiber'] = { 'BetreiberName' : ini_betreiber_name.value,
                            'GlaeubigerID' : ini_glaeubiger_id.value,
                            'BetreiberIBAN' : ini_betreiber_iban.value,
                            'Waermepreis' : ini_arbeitspreis.value,
                            'Grundgebuehr' : ini_grundgebuehr.value}

    # Änderung für v2: Betreiberdaten wie bisher nach dem Dialogabschluss speichern.
    ini_datei_schreiben(inibetreiberfile, config_betreiber)

    ini_einlesen()


###########################################################################################################################
### ENDE EINSTELLUNGEN
###########################################################################################################################


###########################################################################################################################
### ANFANG HILFSFUNKTIONEN
###########################################################################################################################

# rundet bei 5 auf (nicht ab, wie python default)

# Änderung für v2: round_half_up unverändert aus berechnungen importieren.

### Prüft, ob db-Datei existiert und öffnet diese als CSV und gibt sie als dictionary aus

# Änderung für v2: check_ordner_exists ist unverändert in datenhaltung.py ausgelagert.

def db_datei_oeffnen(dbfile):
    dbfilepath = Path(ordner_datenbank + "\\" + dbfile)
    dictionary_temp_list = []
    if dbfilepath.is_file():
        with open(ordner_datenbank + "\\" + dbfile) as csvdatei:
            csv_reader_object = csv.DictReader(csvdatei, delimiter=';')
            for row in csv_reader_object:
                dictionary_temp_list.append(row)
    else:
        dictionary_temp_list.append("file not found")
    return dictionary_temp_list

# Änderung für v2: datei_oeffnen ist unverändert in datenhaltung.py ausgelagert.

def db_datei_speichern(dbfile, csvdict):
    # Überprüfen, ob die Unterordner vorhanden sind und anlegen, wenn nicht
    check_ordner_exists(ordner_abrechnungen)
    check_ordner_exists(ordner_rueckv)
    check_ordner_exists(ordner_logs)
    check_ordner_exists(ordner_datenbank)
    check_ordner_exists(ordner_sicherungen)
    check_ordner_exists(ordner_downloads)
    csvstring = dictlist_to_csv(csvdict)
    dbfile = ordner_datenbank + "\\" + dbfile
    dbfileobject = open(dbfile, "w")
    dbfileobject.write(csvstring)
    dbfileobject.close()


# Änderung für v2: datei_speichern ist unverändert in datenhaltung.py ausgelagert.

def string_in_dict(my_dict, my_string):
    for key in my_dict:
        if my_string in key:
            return True
    return False

# Änderung für v2: dictlist_to_csv ist unverändert in datenhaltung.py ausgelagert.

def textarea_to_string(textarea):
    string = str(textarea).replace("\n", " | ")
    return string

def string_to_textarea(string):
    textarea = string.replace(" | ", "\n")
    return textarea

def dateien_in_ordner_loeschen(ordner):
    dateien = os.listdir(ordner)
    for datei in dateien:
        datei_pfad = os.path.join(ordner,datei)
        try:
            if os.path.isfile(datei_pfad):
                os.remove(datei_pfad)
                print(f"Datei gelöscht: {datei_pfad}")
            else:
                print(f"Übersprungen: {datei_pfad}")
        except Exception as e:
            print(f"Fehler beim Löschen {datei_pfad}: {e}")

def listcsv_to_dict(listcsv):
    dictrow = {}
    vardict = []
    dictkeys = listcsv[0].split(";")
    del dictkeys[-1]
    del listcsv[0]
    for row in listcsv:
        dictvalues = row.split(";")
        del dictvalues[-1]
        for x in range(len(dictkeys)):
            dictrow[dictkeys[x]] = dictvalues[x]
        vardict.append(dictrow)
        dictrow = {}
    return vardict


# Änderung für v2: import_file ist unverändert in datenhaltung.py ausgelagert.

# Änderung für v2: import_csv_inhalt ist unverändert in datenhaltung.py ausgelagert.


### Wandelt Format dd.mm.yyyy um in yyyymmdd

def datum_mit_strich(datum):
    if "." in datum:
        datum_split = datum.split(".")
        datum_string = datum_split[2] + "-" + datum_split[1] + "-" + datum_split[0]
    elif "-" in datum:
        datum_string = datum_in_string
    else:
        print("Datum ist nicht im Format DD.MM.YYYY oder YYYY-MM-DD.")
        return
    return datum_string

# Änderung für v2: datum_in_string unverändert aus berechnungen importiert.

### Wandelt Datum JJJJ-MM-TT und in TT.MM.JJJJ

# Änderung für v2: datum_in_punkt unverändert aus berechnungen importiert.

### Liest Jahr aus Datumsstring aus

def jahr_in_datum(datum):
    if "." in datum:
        datum_split = datum.split(".")
        jahr = datum_split[2]
    elif "-" in datum:
        datum_split = datum.split("-")
        jahr = datum_split[0]
    return jahr


### Zieht Tage x von Datum ab und speichert Datum im Format YYYY-MM-DD

# Änderung für v2: datum_tage_vorher unverändert aus berechnungen importiert.


def dbs_mitglieder_aktualisieren():
    global abnehmer_db
    global zaehler_db
    global abschlag_db
    global konto_db
    global db_abnehmer
    global db_zaehler
    global db_abschlag
    global db_konto
    if abnehmer_db != []:
        for row in abnehmer_db:
            for mitglied in mitglieder_db:
                if row["Ident"] == mitglied["Ident"]:
                    row["Name"] = mitglied["Name"]
                    row["Vorname"] = mitglied["Vorname"]
    if (db_abnehmer_found == 1):
        db_datei_speichern(db_abnehmer, abnehmer_db)
        abnehmer_aus_db()
    if zaehler_db != []:
        for row in zaehler_db:
            for mitglied in mitglieder_db:
                if row["Ident"] == mitglied["Ident"]:
                    row["Name"] = mitglied["Name"]
                    row["Vorname"] = mitglied["Vorname"]
    if (db_zaehler_found == 1):
        db_datei_speichern(db_zaehler, zaehler_db)
        zaehler_aus_db()
    if abschlag_db != []:
        for row in abschlag_db:
            for mitglied in mitglieder_db:
                if row["Ident"] == mitglied["Ident"]:
                    row["Name"] = mitglied["Name"]
                    row["Vorname"] = mitglied["Vorname"]
    if (db_abschlag_found == 1):
        db_datei_speichern(db_abschlag, abschlag_db)
        abschlag_aus_db()
    if konto_db != []:
        for row in konto_db:
            for mitglied in mitglieder_db:
                if row["Ident"] == mitglied["Ident"]:
                    row["Name"] = mitglied["Name"]
                    row["Vorname"] = mitglied["Vorname"]
    if (db_konto_found == 1):
        db_datei_speichern(db_konto, konto_db)
        konto_aus_db()


# Tabellenfelder werden als floats markiert, wenn Zahlen enthalten sind. Ansonsten kann man Tabellenzellen im Grid nicht mit numerischen Werten anpassen

def tablefields_to_dotfloat(table):
    for row in table:
        for key,value in row.items():
            if key != "Ident" and key != "Name" and key != "Vorname" and key != "Kommentar" and "Datum" not in key:
                modifiedvalue = str(value).replace(".","")
                modifiedvalue = modifiedvalue.replace(",","")
                if modifiedvalue.isnumeric() and modifiedvalue != None:
                    row[key] = float(str(value).replace(",","."))
    return table

def tablefields_to_int(table):
    table_new = []

    for row in table:
        row_new = {}
        for key, value in row.items():
            if (
                key not in ("Ident", "Name", "Vorname", "Kommentar") and "datum" not in key):
                if value is None or value == "":
                    row_new[key] = None
                else:
                    try:
                        row_new[key] = int(value)
                    except (TypeError, ValueError):
                        row_new[key] = None
            else:
                row_new[key] = value

        table_new.append(row_new)

    return table_new


def tablefield_to_int(table, field):
    for row in table:
        for key,value in row.items():
            if key == field:
                if value.isnumeric() and value != None:
                    row[key] = int(value)
    return table

# Änderung für v2: Die sechs unveränderten Formatierungsfunktionen liegen in dokumentfelder.py.


async def komma_datei_speichern(dictlist, dateiname):
    kommacsv = []
    kommacsvrow = {}
    for row in dictlist:
        for key,value in row.items():
            if str(value).count('.') == 1:
                kommacsvrow[key] = str(value).replace(".",",")
            else:
                kommacsvrow[key] = value
        kommacsv.append(kommacsvrow)
        kommacsvrow = {}
    content = dictlist_to_csv(kommacsv)
    datei = await app.native.main_window.create_file_dialog(webview.SAVE_DIALOG, directory="%USERPROFILE\\Downloads", allow_multiple=False, save_filename=dateiname)
    if datei != None:
        with open(datei,'w') as f: 
            f.write(content)
            ui.notify(datei + " wurde gespeichert.", type="positive")
    else:
        return
    
# Änderung für v2: mwst_berechnen unverändert aus berechnungen importiert.
    

###########################################################################################################################
### ENDE HILFSFUNKTIONEN
###########################################################################################################################



###########################################################################################################################
### ANFANG MITGLIEDER
###########################################################################################################################

@ui.refreshable
def mitglieder_label_ui(label):
    ui.label(label).style('font-size:100%')


######################
# Funktion für Wartung
######################

def dialog_wartung():
    # Wartungsdaten werden in einem Dictlist bespeichert. Zeile 1 enthält die Ident-Nr. 0-99. Bei Ident-Nr. 0 steht das Datum für den Eintrag. Bei den anderen Ident-Nr. die Einträge für den jeweiligen Anschluss
    global wartung_db, mitglieder_selected_row
    columns = []
    table = []
    row_data = mitglieder_selected_row

    if not row_data:
        ui.notify("Bitte Zeile in Tabelle selektieren.", type="info")
        return

    if row_data["Ident"] == "":
        ui.notify(
            "Bitte Zeile mit bestehender Ident/Anschluss-Nr. auswählen.",
            type="info"
        )
        return

    if db_datei_oeffnen(db_wartung)[0] != 'file not found':
        wartung_db = db_datei_oeffnen(db_wartung)
    else:
        wartung_db.append({})
        for ident in range(0,99):
            wartung_db[0][str(ident)] = ""
        db_datei_speichern(db_wartung, wartung_db)

    def ist_datum_format(string):
        try:
            # Versuch, den String ins gewünschte Format zu parsen
            datetime.strptime(string, "%d.%m.%Y")
            return True
        except ValueError:
            # Falls ein Fehler auftritt, ist es kein gültiges Datum im Format
            return False

    def wartung_grid_update():
        global wartung_grid
        temp_wartung = []
        for row in wartung_db:
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
        wartung_grid.options['columnDefs'] = columns
        wartung_grid.options['rowData'] = temp_wartung
        wartung_grid.options['rowSelection'] = 'multiple'
        wartung_grid.options['pagination'] = 'true'
        wartung_grid.options['paginationPageSize'] = pagination
        wartung_grid.options['alwaysShowHorizontalScroll'] = 'true'
        wartung_grid.options['fullWidthCellRenderer'] = 'fullWidthCellRenderer'
        wartung_grid.update()


    def wartung_eintrag_neu_speichern(datum, eintrag):
        wartung_neu = {}
        datum_gefunden = 0
        # Überprüfen, ob Datumsformat passt
        if ist_datum_format(datum):
            for item in wartung_db:
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
                wartung_db.append(wartung_neu)
            loginfo = 'Ident: ' + str(row_data["Ident"]) + ' ' + row_data["Name"] + ' ' + row_data["Vorname"] + ' ::: Datum ' + str(datum) + ' ===> neuer Eintrag: ' + eintrag.replace("\n","\\n")
            change_log_info('WARTUNG', loginfo)
            db_datei_speichern(db_wartung, wartung_db)
            wartung_grid_update()
            dialog_wartung_neu.close()
        else:
            ui.notify('Bitte Datum im Format DD.MM.YYYY eingeben.', type="info")

    def wartung_eintrag_geaendert_speichern(eintrag):
        for item in wartung_db:
            if item["0"] == wartung_selected_row["Datum"]:
                item[row_data["Ident"]] = eintrag
        loginfo = 'Ident: ' + str(row_data["Ident"]) + ' ' + row_data["Name"] + ' ' + row_data["Vorname"] + ' ::: Datum ' + str(wartung_selected_row["Datum"]) + ' ===> Eintrag geändert: ' + eintrag.replace("\n","\\n")
        change_log_info('WARTUNG', loginfo)
        db_datei_speichern(db_wartung, wartung_db)
        wartung_grid_update()
        dialog_wartung_aendern.close()

    def wartung_eintrag_neu():
        global dialog_wartung_neu

        datum_aktuell = datetime.now().strftime("%d.%m.%Y")

        def update_datum(e):
            global datum_auswahl
            # Datum in das gewünschte Format konvertieren
            datum_auswahl = datetime.strptime(e.value, '%Y-%m-%d').strftime('%d.%m.%Y')
            input_datum.value = datum_auswahl  # Eingabefeld aktualisieren


        with ui.dialog() as dialog_wartung_neu:
            with ui.card().style("width: 100%; height: 400px;"):
                ui.button('', icon='close', on_click=dialog_wartung_neu.close).classes('absolute top-3 right-3')
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
                    ui.button("Speichern", icon='save', on_click=lambda: wartung_eintrag_neu_speichern(input_datum.value, input_wartung.value)).props('color=' + speichernbutton)
        dialog_wartung_neu.open()      

    def wartung_eintrag_aendern():
        global wartung_selected_row
        global dialog_wartung_aendern        

        if not wartung_selected_row:
            ui.notify("Bitte Wartungseintrag auswählen", type="info")
            return

        wartung_data = wartung_selected_row
        with ui.dialog() as dialog_wartung_aendern:
            with ui.card().style("width: 100%; height: 400px;"):
                ui.button('', icon='close', on_click=dialog_wartung_aendern.close).classes('absolute top-3 right-3')
                with ui.row():
                    ui.label("Datum: " + wartung_data["Datum"])
                with ui.row():
                    input_wartung = ui.textarea(label='Wartungsdaten',value=wartung_data["Wartungseintrag"]).style('width: 400px')
                with ui.row():
                    ui.button("Speichern", icon='save', on_click=lambda: wartung_eintrag_geaendert_speichern(input_wartung.value)).props('color=' + speichernbutton)
        dialog_wartung_aendern.open()



    def loeschen_bestaetigen(wartung_data, dialog):
        """
        Löscht den ausgewählten Wartungseintrag für die aktuelle Ident.
        
        Parameters:
            wartung_data: dict
                Die aktuell ausgewählte Zeile im Wartungs-Grid.
            dialog: ui.dialog
                Referenz auf den geöffneten Dialog, damit er geschlossen werden kann.
        """
        global wartung_db, mitglieder_selected_row

        ident = mitglieder_selected_row["Ident"]  # aktuelle Mitglieds-ID

        # Wartungseintrag löschen
        for item in wartung_db:
            if item["0"] == wartung_data["Datum"]:
                item[ident] = ""

        # Log-Eintrag erstellen
        loginfo = (
            f"Ident: {ident} "
            f"{mitglieder_selected_row['Name']} {mitglieder_selected_row['Vorname']} "
            f"::: Datum {wartung_data['Datum']} ===> Eintrag gelöscht: "
            f"{wartung_data.get('Wartungseintrag', '').replace(chr(10),'\\n')}"
        )
        change_log_info('WARTUNG', loginfo)

        # Daten speichern
        db_datei_speichern(db_wartung, wartung_db)

        # Grid aktualisieren
        wartung_grid_update()

        # Dialog schließen
        dialog.close()


    def wartung_eintrag_loeschen():
        global wartung_selected_row

        if not wartung_selected_row:
            ui.notify("Bitte Wartungseintrag auswählen", type="info")
            return

        wartung_data = wartung_selected_row

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
        global wartung_selected_row
        wartung_selected_row = event.args['data']

    # Hauptteil bei Wartung

    if row_data == None:
        ui.notify("Bitte Zeile in Tabelle selektieren.", type="info")
        return

    with ui.dialog().style("width: 800px; max-width: none") as dialog:
        global wartung_grid
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
                wartung_grid = ui.aggrid({
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



# Ausgewählter Anschluss in Tabelle wird zu neuem Abnehmer gewechselt

mitglieder_changes = []

def anschluss_aendern():
    global mitglieder_db, mitglieder_selected_row

    row_auswahl = mitglieder_selected_row

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
        for row in mitglieder_db:
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
            for row in mitglieder_db:
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
            mitglieder_changes.append(loginfo)

            mitglieder_grid_update()
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
                for row in mitglieder_db
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


def mitglieder_neu():
    global mitglieder_db
    def aenderung_speichern():
        neuer_eintrag = {}
        neuer_eintrag["Laufende Nummer"] = neue_lnr
        neuer_eintrag["Ident"] = ""
        neuer_eintrag["Name"] = input_name.value
        neuer_eintrag["Vorname"] = input_vorname.value
        for key in mitglieder_db[0]:
            if key not in ["Laufende Nummer","Ident","Name","Vorname"]:
                neuer_eintrag[key] = ""
        mitglieder_db.append(neuer_eintrag)
        ui.notify('Eintrag ' + input_name.value + " " + input_vorname.value + " wurde mit der Nummer " + str(neue_lnr) + " angelegt.", type="positive")
        loginfo = 'Lfd-Nr. ' + str(neue_lnr) + ' ::: Neuanlage ' + neuer_eintrag["Name"] + ' ' + neuer_eintrag["Vorname"]
        mitglieder_changes.append(loginfo)
        mitglieder_grid_update()
        dialog.close()

    with ui.dialog() as dialog:
        with ui.card().style("width: 600px; height: 400px;"):
            ui.button('', icon='close', on_click=dialog.close).classes('absolute top-3 right-3')
            with ui.row():
                ui.label('Neuen Eintrag anlegen').style("font-size: 24px; font-weight: bold;")
            with ui.row():
                neue_lnr = max(int(x["Laufende Nummer"]) for x in mitglieder_db) + 1
                input_name = ui.input(label='Name').style('width: 200px')
            with ui.row():
                input_vorname = ui.input(label='Vorname').style('width: 200px')
            with ui.row():
                ui.button("Übernehmen", icon='save', on_click=aenderung_speichern)
    dialog.open()


def dialog_mitglieder_editieren():
    global mitglieder_selected_row

    if not mitglieder_selected_row:
        ui.notify('Bitte zuerst einen Eintrag auswählen')
        return

    row_data = mitglieder_selected_row

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
                global mitglieder_grid, mitglieder_db
                # Das gesamte `rowData`-Array holen
                row_data_list = mitglieder_grid.options['rowData']
                
                # Aktuelle Zeile anhand der Referenz suchen und aktualisieren
                for row in row_data_list:
                    if row['Laufende Nummer'] == row_data['Laufende Nummer']:  # Eindeutiges Feld zum Identifizieren
                        for col_name, input_field in fields.items():
                            row[col_name] = input_field.value  # Checkbox-Wert
                        row_neu = row
                        break
                # Grid-Daten explizit neu setzen und aktualisieren
                mitglieder_grid.options['rowData'] = row_data_list
                mitglieder_db = row_data_list
                mitglieder_grid_update()
                loginfo = 'Lfd-Nr. ' + str(row_data["Laufende Nummer"]) + ' ::: Anschlussdaten geändert für  ' + row_data["Name"] + ' ' + row_data["Vorname"]
                mitglieder_changes.append(loginfo)
                loginfo = 'Lfd-Nr. ' + str(row_data["Laufende Nummer"]) + ' ::: ALT: ' + str(row_data)
                mitglieder_changes.append(loginfo)
                loginfo = 'Lfd-Nr. ' + str(row_data["Laufende Nummer"]) + ' ::: NEU: ' + str(row_neu)
                mitglieder_changes.append(loginfo)
                dialog.close()

            with ui.row():
                ui.button('Übernehmen', icon='save', on_click=save_changes)
                ui.button('Abbrechen', icon='close', on_click=dialog.close)

    dialog.open()


def dialog_mitglieder_loeschen():
    global mitglieder_selected_row, mitglieder_db

    row_auswahl = mitglieder_selected_row

    if not row_auswahl:
        ui.notify('Bitte zuerst einen Eintrag auswählen')
        return

    def loeschen_ja():
        for row in mitglieder_db[:]:
            if row["Laufende Nummer"] == row_auswahl["Laufende Nummer"]:
                mitglieder_db.remove(row)

                button_edit.disable()
                button_loeschen.disable()

                loginfo = (
                    f"Lfd-Nr. {row_auswahl['Laufende Nummer']} ::: "
                    f"Anschlussnehmer {row_auswahl['Name']} "
                    f"{row_auswahl['Vorname']} gelöscht."
                )
                mitglieder_changes.append(loginfo)

                mitglieder_grid_update()
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



# Doppelte Einträge werden erkannt, der zweite Eintrag entfernt und beim ersten Eintrag wird die Laufende Nummer und Ident des zweiten Eintrags per Komma angehängt

def duplikate_zusammensetzen(mitglieder_tabelle):
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



def mitglieder_grid_update():
    global mitglieder_grid
    global mitglieder_tabelle
    global mitglieder_db
    global wartung_db
    check_ordner_exists(ordner_downloads)
    check_ordner_exists(ordner_vorlagen)
    # Fortschrittsanzeige ausblenden
    mgl_progress.classes('invisible')

    columns = []
    for row in mitglieder_db:

        # Daten werden auf True oder False (binär) harmonisiert

        if row["ehrenamtlich aktiv"] == 'True' or row["ehrenamtlich aktiv"] == 'False':
            row["ehrenamtlich aktiv"] = row["ehrenamtlich aktiv"] == 'True'
        elif row["ehrenamtlich aktiv"] == True or row["ehrenamtlich aktiv"] == False:
            row["ehrenamtlich aktiv"] = row["ehrenamtlich aktiv"] == True           
        else:   
            row["ehrenamtlich aktiv"] = row["ehrenamtlich aktiv"] == 'x'

    # notwendig für den Fall, dass die Tabellendaten editiert werden
    mitglieder_tabelle = mitglieder_db
    # Nur ausführen, wenn Editiermodus ausgeschalten ist
    if edit_switch.value != True:
        button_word_export.disable()
        mitglieder_tabelle = []

        # Filtert Daten in Abhängigkeit von Dropdown Auswahl. Es wird lediglich die Anzeige angepasst. Gespeicherte Daten werden nicht verändert
        # Sortierung wandelt String in Int um, um nicht 10 nach 1 zu erhalten
        mitglieder_tabelle_temp_row = {}
        mitglieder_tabelle_temp = []        

        if mitglieder_filter_dropdown.value == 'kein Filter':
            radio_filter.enable()
            button_serienbrief.enable()
            mitglieder_tabelle = mitglieder_db
        elif mitglieder_filter_dropdown.value == 'Verbraucheranschlüsse':
            radio_filter.enable()
            button_serienbrief.enable()
            for mitglied in mitglieder_db:
                if str(mitglied['Ident']) != '':
                    mitglieder_tabelle.append(mitglied)
        elif mitglieder_filter_dropdown.value == 'Aktive Helfer':
            radio_filter.enable()
            button_serienbrief.enable()
            for mitglied in mitglieder_db:
                mitglieder_tabelle_row = {}
                for key,value in mitglied.items():
                    if key in ['Name','Vorname','Geburtsdatum','Straße','Hausnummer','Festnetz','Mobil','E-Mail 1','E-Mail 2','Postleitzahl','Wohnort','Anrede-Adressat','Anrede-Geschlecht','Anrede-Formel','Anrede-Name']:
                        mitglieder_tabelle_row[key] = value
                if mitglied["ehrenamtlich aktiv"] == True:
                    mitglieder_tabelle.append(mitglied)
        elif mitglieder_filter_dropdown.value == 'Mitgliederliste (Jahresabschluss)':
            button_word_export.enable()
            button_serienbrief.disable()
            radio_filter.set_value("Name")
            radio_filter.disable()
            for mitglied in mitglieder_db:
                mitglieder_tabelle_temp_row = {}
                for key,value in mitglied.items():
                    if key in ['Laufende Nummer','Ident','Name','Vorname','Straße','Hausnummer','Postleitzahl','Wohnort']:
                        mitglieder_tabelle_temp_row[key] = value
                if str(mitglied["Ident"]) != '':
                    mitglieder_tabelle_temp.append(mitglieder_tabelle_temp_row)
            mitglieder_tabelle = duplikate_zusammensetzen(mitglieder_tabelle_temp)
        elif mitglieder_filter_dropdown.value == 'Mitgliederliste (Generalversammlung)':
            button_word_export.enable()
            button_serienbrief.disable()
            radio_filter.set_value("Name")
            radio_filter.disable()
            for mitglied in mitglieder_db:
                mitglieder_tabelle_temp_row = {}
                for key,value in mitglied.items():
                    if key in ['Laufende Nummer','Ident','Name','Vorname']:
                        mitglieder_tabelle_temp_row[key] = value
                if str(mitglied["Ident"]) != '':
                    mitglieder_tabelle_temp.append(mitglieder_tabelle_temp_row)
            mitglieder_tabelle = duplikate_zusammensetzen(mitglieder_tabelle_temp)
        elif mitglieder_filter_dropdown.value == 'Verbraucher mit Wartungsdaten':
            button_word_export.disable()
            button_serienbrief.disable()
            radio_filter.set_value("Ident")
            radio_filter.disable()
            # db_wartung wird eingelesen
            if db_datei_oeffnen(db_wartung)[0] != 'file not found':
                wartung_db = db_datei_oeffnen(db_wartung)
            else:
                return
            for mitglied in mitglieder_db:
                mitglieder_tabelle_temp_row = {}
                datum_wartung = []
                # nur Mitglieder mit Anschluss berücksichtigen
                if mitglied["Ident"] == "":
                    continue
                # Anzahl der Tage mit Wartungseintrag ermitteln
                for zeile in wartung_db:
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
                    for zeile in wartung_db:
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
            mitglieder_tabelle = mitglieder_tabelle_temp

    # Radio Filter wird ausgewertet    
    if radio_filter.value == "Laufende Nummer":
        mitglieder_tabelle = sorted(mitglieder_tabelle, key=lambda x: int(x["Laufende Nummer"]))
    elif radio_filter.value == "Ident":
        # Wenn kein Wert in Spalte, soll die Zeile hinten angestellt werden
        mitglieder_tabelle = sorted(mitglieder_tabelle, key=lambda x: (not x.get("Ident") or not x["Ident"].isdigit(), int(x["Ident"]) if x.get("Ident") and x["Ident"].isdigit() else 0))
    elif radio_filter.value == "Name":
        mitglieder_tabelle = sorted(mitglieder_tabelle,key=lambda x: (x["Name"], x["Vorname"]))
    elif radio_filter.value == "Straße":
        mitglieder_tabelle = sorted(mitglieder_tabelle, key=lambda x: (not x.get("Reihenfolge Straße") or not x["Reihenfolge Straße"].isdigit(), int(x["Reihenfolge Straße"]) if x.get("Reihenfolge Straße") and x["Reihenfolge Straße"].isdigit() else 0))

    if mitglieder_tabelle != []:
        for key in mitglieder_tabelle[0].keys():
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
    mitglieder_grid.options['columnDefs'] = columns
    mitglieder_grid.options['rowData'] = mitglieder_tabelle
    mitglieder_grid.options['rowSelection'] = 'multiple'
    mitglieder_grid.options['pagination'] = 'true'
    mitglieder_grid.options['paginationPageSize'] = pagination
    mitglieder_grid.options['alwaysShowHorizontalScroll'] = 'true'
    mitglieder_grid.options['fullWidthCellRenderer'] = 'fullWidthCellRenderer'
    mitglieder_grid.update()

async def editiermodus_aendern():
    global mitglieder_filter_dropdown

    async def confirm_save():
        # Funktion zum Anzeigen des Bestätigungsdialogs
        with ui.dialog() as dialog:
            with ui.card():
                ui.label("Möchten Sie Ihre Änderungen speichern?")
                with ui.row():
                    # "Ja" ruft die Funktion auf und schließt den Dialog
                    ui.button("Ja", on_click=lambda: (mitglieder_speichern(), dialog.close()))
                    # "Nein" schließt nur den Dialog
                    ui.button("Nein", on_click=lambda: (nicht_speichern(),dialog.close()))

        dialog.open()

    def nicht_speichern():
        mitglieder_aus_db()

    def apply_switch_off_state():
        # Status setzen, wenn der Switch ausgeschaltet wird
        button_edit.disable()
        button_anschluss.disable()
        button_neu.disable()
        button_loeschen.disable()
        mitglieder_filter_dropdown.enable()
        button_csv_export.enable()
        button_serienbrief.enable()
        button_email.enable()
        mitglieder_grid_update()

    # Logik bei Statuswechsel
    if edit_switch.value == True:
        # Switch wird eingeschaltet -> direkter Wechsel
        button_edit.disable()
        button_anschluss.disable()
        button_neu.enable()
        button_loeschen.disable()
        mitglieder_filter_dropdown.disable()
        button_csv_export.disable()
        button_word_export.disable()
        button_serienbrief.disable()
        button_email.disable()
#        mitglieder_aus_db()
    else:
        # Switch wird ausgeschaltet
        await confirm_save()  # Zeigt den Dialog an
        apply_switch_off_state()  # Setzt den "ausgeschalteten" Zustand immer

def edit_aktivieren(event):
    global mitglieder_selected_row
    mitglieder_selected_row = event.args['data']

    if not edit_switch.value:
        return

    if not mitglieder_selected_row:
        button_edit.disable()
        button_anschluss.disable()
        return

    button_edit.enable()

    if mitglieder_selected_row.get("Ident", "") == "":
        button_anschluss.disable()
        button_loeschen.enable()
    else:
        button_anschluss.enable()
        button_loeschen.disable()


def mitglieder_upload(e: events.UploadEventArguments):
    global mitglieder_db
    with StringIO(e.content.read().decode('iso-8859-1', errors='ignore')) as f:
        mitglieder_import = import_csv_inhalt(f)
    if string_in_dict(mitglieder_import[0], 'Ident') == True and string_in_dict(mitglieder_import[0], 'Name') == True and string_in_dict(mitglieder_import[0], 'Vorname') == True:
        mitglieder_db = mitglieder_import
    else:
        ui.notify('Importdaten entsprechen nicht dem erforderlichen Format. Es müssen mindestens Tabellenspalten für Ident, Name, Vorname enthalten sein.', type="warning")
        return
    db_sichern("Upload Mitgliederdaten")
    button_mitglieder_pruefen.enable()
    button_mitglieder_speichern.enable()
    mitglieder_grid_update()

def mitglieder_aus_db():
    global mitglieder_db
    mitglieder_db = db_datei_oeffnen(db_mitglieder)
    mitglieder_grid_update()


def mitglieder_speichern():
    if mitglieder_changes != []:
        for eintrag in mitglieder_changes:
            change_log_info("MITGLIEDER", eintrag)
    db_sichern("Mitglieder gespeichert")
    db_datei_speichern(db_mitglieder, mitglieder_db)
    ui.notify('Mitgliederdaten gespeichert', type="positive")
    mitglieder_aus_db()
    button_mitglieder_speichern.disable()
    dbs_mitglieder_aktualisieren()

# Es wird geprüft, ob Name und Vorname der Mitgliederliste mit den anderen Listen übereinstimmen. Die Korrektur wird beim Speichern vorgenommen
def mitglieder_pruefen():
    mitglieder_ok = 1
    if abnehmer_db != []:
        for row in abnehmer_db:
            for mitglied in mitglieder_db:
                if row["Ident"] == mitglied["Ident"]:
                    if row["Name"] != mitglied["Name"]:
                        ui.notify("Mitglied Nr. " + row["Ident"] + ": Name in ABNEHMER DB stimmt nicht überein: " + mitglied["Name"] + " |vs| " + row["Name"], type="warning")
                        mitglieder_ok = 0
                    if row["Vorname"] != mitglied["Vorname"]:
                        ui.notify("Mitglied Nr. " + row["Ident"] + ": Vorname in ABNEHMER DB stimmt nicht überein: " + mitglied["Vorname"] + " |vs| " + row["Vorname"], type="warning")
                        mitglieder_ok = 0
    if zaehler_db != []:
        for row in zaehler_db:
            for mitglied in mitglieder_db:
                if row["Ident"] == mitglied["Ident"]:
                    if row["Name"] != mitglied["Name"]:
                        ui.notify("Mitglied Nr. " + row["Ident"] + ": Name in ZÄHLER-DB stimmt nicht überein: " + mitglied["Name"] + " |vs| " + row["Name"], type="warning")
                        mitglieder_ok = 0
                    if row["Vorname"] != mitglied["Vorname"]:
                        ui.notify("Mitglied Nr. " + row["Ident"] + ": Vorname in ZÄHLER-DB stimmt nicht überein: " + mitglied["Vorname"] + " |vs| " + row["Vorname"], type="warning")
                        mitglieder_ok = 0
    if abschlag_db != []:
        for row in abschlag_db:
            for mitglied in mitglieder_db:
                if row["Ident"] == mitglied["Ident"]:
                    if row["Name"] != mitglied["Name"]:
                        ui.notify("Mitglied Nr. " + row["Ident"] + ": Name in ABSCHLAG-DB stimmt nicht überein: " + mitglied["Name"] + " |vs| " + row["Name"], type="warning")
                        mitglieder_ok = 0
                    if row["Vorname"] != mitglied["Vorname"]:
                        ui.notify("Mitglied Nr. " + row["Ident"] + ": Vorname in ABSCHLAG-DB stimmt nicht überein:" + mitglied["Vorname"] + " |vs| " + row["Vorname"], type="warning")
                        mitglieder_ok = 0
    if konto_db != []:
        for row in konto_db:
            for mitglied in mitglieder_db:
                if row["Ident"] == mitglied["Ident"]:
                    if row["Name"] != mitglied["Name"]:
                        ui.notify("Mitglied Nr. " + row["Ident"] + ": Name in KONTO-DB stimmt nicht überein: " + mitglied["Name"] + " |vs| " + row["Name"], type="warning")
                        mitglieder_ok = 0
                    if row["Vorname"] != mitglied["Vorname"]:
                        ui.notify("Mitglied Nr. " + row["Ident"] + ": Vorname in KONTO-DB stimmt nicht überein:" + mitglied["Vorname"] + " |vs| " + row["Vorname"], type="warning")
                        mitglieder_ok = 0
    if mitglieder_ok == 1:
        ui.notify('Mitglieder wurden erfolgreich geprüft.', type="positive")

def disable_row_splitting(table):
    """Verhindert das Teilen aller Zeilen einer Tabelle zwischen Seiten."""
    for row in table.rows:
        tr = row._tr  # Zugriff auf die zugrunde liegende XML-Struktur der Zeile
        trPr = tr.get_or_add_trPr()  # Zeilen-Eigenschaften hinzufügen/abrufen
        cant_split = OxmlElement('w:cantSplit')  # Keine Teilung zulassen
        trPr.append(cant_split)


def mitglieder_ja_word_erstellen(dateiname):
    # Neues Word-Dokument erstellen für Jahresabschluss
    pythoncom.CoInitialize()
    mgl_progress.set_value(0)
    button_word_export.disable()
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
    mgl_progress.set_value(4)

    #  # Tabelle erstellen
    table = doc.add_table(rows=len(mitglieder_tabelle)+1, cols=len(mitglieder_tabelle[0]), style='Table Grid')
    mgl_progress.set_value(8)

    # # Tabelle Spaltenüberschriften
    column = 0
    for key in mitglieder_tabelle[0].keys():
        cell = table.cell(0, column)
        paragraph = cell.add_paragraph()
        run = paragraph.add_run(key)
        run.bold = True
        run.font.size = Pt(10)
        column = column + 1
    mgl_progress.set_value(10)

    progress_step = 89 / len(mitglieder_tabelle)
    progress_akt = 10 + progress_step
    row = 1
    for element in mitglieder_tabelle:
        column = 0
        for value in element.values():
            cell = table.cell(row, column)
            paragraph = cell.add_paragraph()
            run = paragraph.add_run(value)
            run.font.size = Pt(10)  # Kleinere Schriftgröße (z. B. 8 pt) für die Zelleninhalte
            column += 1
        row += 1
        mgl_progress.set_value(int(progress_akt))
        progress_akt = progress_akt + progress_step
    disable_row_splitting(table)

    doc.save(ordner_downloads + '\\' + dateiname)
    mgl_progress.set_value(100)
    button_word_export.enable()

def mitglieder_gv_word_erstellen(dateiname, datum, ort):
    # Neues Word-Dokument erstellen für Generalversammlung
    pythoncom.CoInitialize()
    mgl_progress.set_value(0)
    button_word_export.disable()
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
    mgl_progress.set_value(4)

    #  # Tabelle erstellen
    table = doc.add_table(rows=len(mitglieder_tabelle)+1, cols=len(mitglieder_tabelle[0])+2, style='Table Grid')
    mgl_progress.set_value(8)

    # # Tabelle Spaltenüberschriften
    column = 0
    for key in mitglieder_tabelle[0].keys():
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

    mgl_progress.set_value(10)

    progress_step = 89 / len(mitglieder_tabelle)
    progress_akt = 10 + progress_step
    row = 1
    for element in mitglieder_tabelle:
        column = 0
        for value in element.values():
            cell = table.cell(row, column)
            paragraph = cell.add_paragraph()
            run = paragraph.add_run(value)
            run.font.size = Pt(10)  # Kleinere Schriftgröße (z. B. 8 pt) für die Zelleninhalte
            column += 1
        row += 1
        mgl_progress.set_value(int(progress_akt))
        progress_akt = progress_akt + progress_step
    disable_row_splitting(table)

    doc.save(ordner_downloads + '\\' + dateiname)
    mgl_progress.set_value(100)
    button_word_export.enable()


# Prozess für Hintergrundtask wird in eigener Funktion gestartet, um das UI Element für GV entsprechend abbilden zu können

def mitglieder_word_process(quelle, dateiname, datum, ort):
    # eigene Funktion für die Tabellen erstellung, da resourcenhungrig und in eigenem Thread
    # Komma hinter Dateiname, da sonst die Zeichen des Strings einzeln übergeben werden
    global word_erstellung_background
    mgl_progress.set_value(0)
    mgl_progress.classes(remove='invisible')
    if quelle == "ja":
        word_erstellung_background = threading.Thread(target=mitglieder_ja_word_erstellen, args=(dateiname,))
    elif quelle == "gv":
        word_erstellung_background = threading.Thread(target=mitglieder_gv_word_erstellen, args=(dateiname,datum,ort,))
    word_erstellung_background.start()


async def mitglieder_word_download():
    async def gv_dialog():
        global selected_date
        global ort_input

        def word_ja_start():
            ui.notify("Datei " + dateiname + " wird im Ordner " + ordner_downloads + " abgelegt.", type="info")
            dialog.close()
            mitglieder_word_process("gv", dateiname, selected_date, ort_input.value)
      
        # Dialog erstellen
        # Funktion für das aktuelle Datum
        current_date = datetime.now().strftime('%d.%m.%Y')
        selected_date = current_date
 
        def update_datum(e):
            global selected_date
            # Datum in das gewünschte Format konvertieren
            selected_date = datetime.strptime(e.value, '%Y-%m-%d').strftime('%d.%m.%Y')
            date_input.value = selected_date  # Eingabefeld aktualisieren



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
                    ort_input = ui.input("Ort").style("width: 250px;")
                with ui.row():
                    ui.button("Word export", icon='file_download', on_click=word_ja_start)
        
        dialog.open()

    current_datetime = datetime.now().strftime("%Y-%m-%d")
    dateiname = mitglieder_filter_dropdown.value.replace(" ","-") + '-' + current_datetime + '.docx'
    if "Jahresabschluss" in mitglieder_filter_dropdown.value:
        ui.notify("Datei " + dateiname + " wird im Ordner " + ordner_downloads + " abgelegt.", type="info")
        mitglieder_word_process("ja", dateiname,"","")
    elif "Generalversammlung" in mitglieder_filter_dropdown.value:
        await gv_dialog()


def mitglieder_csv_download():
    mgl_progress.set_value(0)
    time.sleep(1)
    mgl_progress.classes(remove='invisible')
    mgl_progress.set_value(1)
    current_datetime = datetime.now().strftime("%Y-%m-%d")
    dateiname = 'Mitglieder-' + mitglieder_filter_dropdown.value.replace(" ","-") + '-' + current_datetime + '.csv'
    dateipfad = ordner_downloads + '\\' + dateiname
    datei_speichern(dateipfad,mitglieder_tabelle)
    mgl_progress.set_value(100)
    ui.notify("Datei " + dateiname + " wurde unter " + ordner_downloads + " abgelegt.", type="positive")

def serienbrief_dialog():
    datum_aktuell = datetime.now().strftime("%d.%m.%Y")

    def update_datum(e):
        global datum_auswahl
        # Datum in das gewünschte Format konvertieren
        datum_auswahl = datetime.strptime(e.value, '%Y-%m-%d').strftime('%d.%m.%Y')
        date_input.value = datum_auswahl  # Eingabefeld aktualisieren

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
        progress_step = 100/len(mitglieder_tabelle)
        mgl_progress.classes(remove='invisible')

        # Vorhandensein Vorlage prüfen
        serienbrief_daten = {}
        serienbrief_vorlage = ordner_vorlagen + "\\" + "Vorlage-Serienbrief.docx"
        pfad_serienbrief_vorlage = Path(serienbrief_vorlage)
        if not pfad_serienbrief_vorlage.exists(): 
            ui.notify('Bitte Serienbrief-Vorlage ' + serienbrief_vorlage + ' ablegen.', type="info")
            return

        # Datum für Brief mit Punkten
        datum_brief = datetime.now().strftime("%d.%m.%Y")
        pfad_ordner_serienbrief = Path(ordner_serienbrief)
        if not pfad_ordner_serienbrief.exists():
#            pfad_ordner_serienbrief.mkdir()
            os.makedirs(ordner_serienbrief)
        else:
            dateien_in_ordner_loeschen(ordner_serienbrief)
        for mitglied in mitglieder_tabelle:
            serienbrief_felder = ["Ident","Name", "Vorname", "Straße", "Hausnummer", "Postleitzahl", "Wohnort", "Anrede-Geschlecht", "Anrede-Formal", "Anrede-Name"]
            for key,value in mitglieder_tabelle[0].items():
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
            if radio_filter.value == "Laufende Nummer":
                prefix = "lnr" + mitglied["Laufende Nummer"] + "-"
            elif radio_filter.value == "Ident":
                prefix = "id" + mitglied["Ident"] + "-"
            elif radio_filter.value == "Name":
                prefix = ""
            elif radio_filter.value == "Straße":
                prefix = "str" + mitglied["Reihenfolge Straße"] + "-"
            datei_serienbrief = prefix + "Brief-" + mitglied["Name"].replace(" ","-") + "-" + mitglied["Vorname"] + ".docx"            
            document.write(ordner_serienbrief + "\\" + datei_serienbrief)
            progress_akt += progress_step
            mgl_progress.set_value(int(progress_akt))


    def serienbrief_process(betreff,text):
        global ordner_serienbrief
        # Datum für Ordner und Datei mit Strichen
        datum_aktuell = datetime.now().strftime("%Y-%m-%d")
        ordner_serienbrief = ordner_downloads + "\\" + "Serienbrief-" + datum_aktuell + "-" + betreff.replace(" ","-") + "\\word"
        ui.notify("Serienbriefe werden unter " + ordner_serienbrief + " abgelegt.", type="info")
        dialog.close()
        mgl_progress.set_value(0)
        mgl_progress.classes(remove='invisible')
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


def mitglieder_ui():
    global db_mitglieder_found
    global mitglieder_grid
    global button_mitglieder_speichern
    global button_mitglieder_pruefen
    global mitglieder_filter_dropdown
    global button_csv_export, button_word_export, button_serienbrief, button_email
    global edit_switch, button_edit, button_anschluss, button_neu, button_loeschen, mgl_progress, radio_filter
    columns = []
    table = []
    mitglieder_label_ui('')
    with ui.row():
        button_wartung = ui.button('Wartung', icon='engineering', on_click=dialog_wartung).props('color=accent')
    ui.separator().style("height: 2px; background-color: black")
    with ui.row():
        mitglieder_filter_dropdown = ui.select(options=['kein Filter','Verbraucheranschlüsse','Aktive Helfer','Mitgliederliste (Jahresabschluss)','Mitgliederliste (Generalversammlung)', 'Verbraucher mit Wartungsdaten'], label='Filtervorlagen', value='kein Filter',on_change=mitglieder_grid_update).classes('w-96')
        ui.label("Sortierung:")
        radio_filter = ui.radio(["Laufende Nummer", "Ident", "Name", "Straße"], value="Laufende Nummer", on_change=mitglieder_grid_update).props('inline')
    with ui.row():
        button_csv_export = ui.button('CSV Export', icon='file_download', on_click=mitglieder_csv_download)
        button_word_export = ui.button('Word Export', icon='file_download', on_click=mitglieder_word_download)
        button_word_export.disable()
        button_serienbrief = ui.button('Serienbrief', icon='keyboard', on_click=serienbrief_dialog)
        button_email = ui.button('E-Mail', icon='email')
        button_email.disable()
        mgl_progress = ui.circular_progress(min=0, max=100, color="black").classes('invisible')
    ui.separator().style("height: 2px; background-color: black")
    with ui.row():
        edit_switch = ui.switch('Editiermodus', on_change=editiermodus_aendern)
        button_neu = ui.button('Eintrag neu', icon='add_circle', on_click=mitglieder_neu)
        button_neu.disable()
        button_edit = ui.button('Eintrag editieren', icon='edit',on_click=dialog_mitglieder_editieren)
        button_edit.disable()
        button_loeschen = ui.button('Eintrag löschen',icon='delete', on_click=dialog_mitglieder_loeschen)
        button_loeschen.disable()
        button_anschluss = ui.button('Anschlussnehmer ändern',icon='change_circle', on_click=anschluss_aendern)
        button_anschluss.disable()
    mitglieder_grid = ui.aggrid({
        'defaultColDef': {'flex': 1, 'editable': True, 'resizable': True, 'wrapHeaderText': True, 'autoHeaderHeight': True},
        'columnDefs': columns,
        'rowData': table,
        'domLayout': 'autoHeight',
    }).on('cellClicked', edit_aktivieren).style('height: 100%')
    ui.separator().style("height: 2px; background-color: black")
    with ui.row():
        ui.upload(label='Upload Vorlage Mitgliederdaten',on_upload=mitglieder_upload, auto_upload=True, max_files=1).props("accept=.csv").classes('max-w-full')
        button_mitglieder_pruefen = ui.button("Prüfen", icon='task_alt', on_click=mitglieder_pruefen)
        button_mitglieder_speichern = ui.button('Speichern', icon='save', on_click=lambda: (mitglieder_speichern())).props('color=' + speichernbutton)
        button_mitglieder_pruefen.disable()
        button_mitglieder_speichern.disable()

    if db_datei_oeffnen(db_mitglieder)[0] == "file not found":
        mitglieder_label_ui.refresh('Keine Mitgliederdaten in Datenbank. Upload CSV-Datei mit Basisdaten der Mitglieder.')
        db_mitglieder_found = 0
    else:
        db_mitglieder_found = 1
        mitglieder_label_ui.refresh('Mitglieder-Datenbank wurde gefunden! Daten wurden geladen und können über einen neuen Upload überschrieben und ergänzt werden.')
        mitglieder_aus_db() 


###########################################################################################################################
### ENDE MITGLIEDER
###########################################################################################################################


###########################################################################################################################
### ANFANG ABNEHMER / BASISDATEN
###########################################################################################################################

@ui.refreshable
def abnehmer_label_ui(label):
    ui.label(label).style('font-size:100%')

# Daten wie Ident, Name und Vorname werden aus Abnehmerdaten extrahiert

# Änderung für v2: abnehmer_aus_daten unverändert aus berechnungen importiert.

def abnehmer_upload(e: events.UploadEventArguments):
    global abnehmer_db
    if mitglieder_db == []:
        ui.notify('Mitglieder sind noch nicht erfasst. Bitte vorher Mitgliederliste anlegen.', type="info")
        return
    with StringIO(e.content.read().decode('iso-8859-1', errors='ignore')) as f:
        abnehmer_import = import_csv_inhalt(f)
    if string_in_dict(abnehmer_import[0], 'Ident') == True and string_in_dict(abnehmer_import[0], 'Name') == True and string_in_dict(abnehmer_import[0], 'Vorname') == True and string_in_dict(abnehmer_import[0], 'Original-Vertragsleistung') == True and string_in_dict(abnehmer_import[0], 'Mindest-Vertragsleistung') == True:
        for mrow in mitglieder_db:
            ident_found = 0
            temprow = {}
            for row in abnehmer_import:
                if mrow["Ident"] == row["Ident"]:
                    for key,value in row.items():
                        if key == "Ident" or key == "Name" or key == "Vorname":
                            temprow[key] = mrow[key]
                        else:
                            temprow[key] = row[key]
                    abnehmer_db.append(temprow)
                    ident_found = 1
            if ident_found != 1 and mrow["Ident"] != "":
                temprow = {}
                temprow["Ident"] = mrow["Ident"]
                temprow["Name"] = mrow["Name"]
                temprow["Voranme"] = mrow["Vorname"]
                ui.notify("Ident " + mrow["Ident"] + " nicht gefunden.", type="warning")
                abnehmer_db.append(temprow)
    else:
        ui.notify('Importdaten entsprechen nicht dem erforderlichen Format. Es müssen Tabellenspalten für Ident, Name, Vorname, Original-Vertragsleistung und Mindest-Vertragsleistung-<Jahr> enthalten sein.', type="Warning")
        return
    abnehmer_db = sorted(abnehmer_db, key=lambda x: int(x["Ident"]))  
    for row in abnehmer_db:
        for key,value in row.items():
            if "Ident" in key or "Vertragsleistung" in key:
                row[key] = int(value)
    db_sichern("Upload Abnehmerdaten")
    button_abnehmer_speichern.enable()
    abnehmer_grid_ui.refresh()

def abnehmer_aus_db():
    global abnehmer_db
    abnehmer_db = db_datei_oeffnen(db_abnehmer)
    abnehmer_db = tablefields_to_int(abnehmer_db)
    abnehmer_grid_ui.refresh()
    button_abnehmer_speichern.disable()

# Abnehmerdaten werden bei Zellveränderung automatisch gespeichert

def abnehmerdaten_speichern():
    db_datei_speichern(db_abnehmer, abnehmer_db)
    abschlag_speichern()
    abschlag_grid_ui.refresh()
    button_abnehmer_speichern.disable()
    ui.notify("Abnehmerdaten gespeichert", type='positive')


def abnehmer_tabelle_on_change(event):
    global abnehmer_grid
    global abnehmer_db
    global abschlag_db
    if event["newValue"] == None:
        return
    abnehmer_db[int(event["rowId"])][event["colId"]] = event["newValue"]
    if "Mindest" in event["colId"]:
        abschlag_db_wert_alt = abschlag_db[int(event["rowId"])]["Abschlag-" + str(event["colId"])[-4:]]
        if event["newValue"] != 0:
            abschlag_db[int(event["rowId"])]["Abschlag-" + str(event["colId"])[-4:]] = round((event["newValue"] / 100 * arbeitspreis / 4),2)
        abschlag_db_wert_neu = abschlag_db[int(event["rowId"])]["Abschlag-" + str(event["colId"])[-4:]]
        log_daten = event["data"]["Ident"] + " " + event["data"]["Name"] + " " + event["data"]["Vorname"] + " ::: " + "Abschlag-" + str(event["colId"])[-4:] + " ::: " + str(abschlag_db_wert_alt) + " ===> " + str(abschlag_db_wert_neu)
        change_log_info("ABSCHLAG", log_daten)
    change_log("ABNEHMER", event)
    button_abnehmer_speichern.enable()



# Spalten für Tabelle definieren

def abnehmer_columns_erstellen(table):
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
                column_element["cellStyle"] = {'backgroundColor': col_cell_mod}
                column_element["cellEditor"]='agStringCellEditor'
            if "Mindest-" in key:
                column_element["editable"] = True
                column_element["cellStyle"] = {'backgroundColor': col_cell_mod}
                column_element["cellEditor"]='agNumberCellEditor'

            columns.append(column_element)
    return columns

# Tabelle erstellen



@ui.refreshable
def abnehmer_grid_ui():
    global abnehmer_grid
    abnehmer_grid = ui.aggrid({
        'defaultColDef': {
            'editable': False,
            'resizable': True,
            'wrapHeaderText': True,
            'autoHeaderHeight': True,
        },
        'columnDefs': abnehmer_columns_erstellen(abnehmer_db),
        'rowData': abnehmer_db,
        'domLayout': 'autoHeight',
        'pagination': True,
        'paginationPageSize': pagination
    }).on(
        'cellValueChanged',
        lambda event: abnehmer_tabelle_on_change(event.args)
    ).style('height: 100%')

def abnehmer_ui():
    global abnehmer_db
    global db_abnehmer_found
    global button_abnehmer_speichern

    abnehmer_label_ui('')
    with ui.row():
        ui.upload(label='Upload Vorlage Abnehmerdaten',on_upload=abnehmer_upload, auto_upload=True, max_files=1).props("accept=.csv").classes('max-w-full')
        button_abnehmer_speichern = ui.button('Speichern', icon='save', on_click=lambda: (abnehmerdaten_speichern())).props('color=' + speichernbutton)
        button_abnehmer_speichern.disable()
    abnehmer_grid_ui()
    if db_datei_oeffnen(db_abnehmer)[0] == "file not found":
        abnehmer_label_ui.refresh('Keine Abnehmerdaten in Datenbank. Upload CSV-Datei mit Basisdaten der Abnehmer.')
    else:
        db_abnehmer_found = 1
        abnehmer_label_ui.refresh('Abnehmer-Datenbank gefunden! Daten wurden geladen und können über einen neuen Upload überschrieben und ergänzt werden.')
        abnehmer_aus_db()   

###########################################################################################################################
### ENDE ABNEHMER / BASISDATEN
###########################################################################################################################


###########################################################################################################################
### ANFANG ZÄHLER
###########################################################################################################################

@ui.refreshable
def zaehler_label_ui(label):
    ui.label(label).style('font-size:100%')

### Import zusätzliche Zähler in bestehende Zähler-DB

def import_zaehler_liste(zaehler_liste):
    global db_zaehler_found
    zaehler_liste_temp = []
    basis_liste = []

    # Prüfung, ob Zähler vom Monatsende importiert werden, da Zählerdaten an anderen Tagen nicht unterstützt werden.

    zaehler_ok = True
    for key in zaehler_liste[0].keys():
        if "Ident" not in key and "wechsel" not in key and key[4:8] not in ['0131','0228','0229','0331','0430','0531','0630','0731','0831','0930','1031','1130','1231']:
            zaehler_ok = False
    if zaehler_ok == False:
        ui.notify('Nur Import von Zählerdaten zum Monatsende erlaubt.', type="warning")
        return zaehler_db

    # Wenn eine Datenbank gefunden wird, wird diese als Basis genommen, wenn nicht, dann die Abnehmer DB
    if db_zaehler_found == 1:
        print("DB Zähler vorhanden")
        basis_liste = zaehler_db 
    else:
        print("DB Zähler nicht gefunden")
        basis_liste = abnehmer_db

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
                if key == "Kommentar" and db_zaehler_found != 1:
                    zaehler_liste_row_temp[key] = ""
        for zaehler_liste_row in zaehler_liste:
            if zaehler_liste_row["Ident"] == row["Ident"]:
                for key,value in zaehler_liste_row.items():
                    # Ein bestehender Wert wird nur überschrieben, wenn der Schalter auf "on" ist
                    if ((upload_overwrite_switch.value == False) and "-zaehler" in key and key not in row) or (upload_overwrite_switch.value == True and "-zaehler" in key):
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

# CSV-Datei aus Visualisierung wird eingelesen und entspechende Werte als Liste ausgegeben

def import_zaehlerdaten_visu(csvinput):
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
    import_file_listdict=listcsv_to_dict(imported_file)
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
            abnehmer_dict[jahr_in_datum(row["TAG BIS"]) + "-zaehlerwechsel-alt"] = row["Zaehlerstand BIS(kWh)"].replace(".",",")
            erste_zeile = 0
        # Verarbeitung zweite Zeile (nach Zählerwechsel)
        elif row["0"] in double_node and erste_zeile == 0:
            abnehmer_dict[jahr_in_datum(row["TAG VON"]) + "-zaehlerwechsel-neu"] = row["Zaehlerstand VON(kWh)"].replace(".",",")
            if datum_tage_vorher(row["TAG BIS"],1) == zaehler_bis or row["TAG BIS"] == zaehler_bis:
                abnehmer_dict[datum_in_string(zaehler_bis) + "-zaehler"] = row["Zaehlerstand BIS(kWh)"].replace(".",",")
            else:
                abnehmer_dict[datum_in_string(zaehler_bis) + "-zaehler"] = "-1"
            abnehmer_dict[jahr_in_datum(row["TAG VON"]) + "-datum-zaehlerwechsel"] = datum_in_punkt(row["TAG VON"])
            erste_zeile = 1
            tabelle_zaehler_erg.append(abnehmer_dict)
            abnehmer_dict = {}
        else:
            if double_node != []:
                abnehmer_dict[jahr_in_datum(row["TAG VON"]) + "-zaehlerwechsel-neu"] = "-1"
                abnehmer_dict[jahr_in_datum(row["TAG VON"]) + "-zaehlerwechsel-alt"] = "-1"
                abnehmer_dict[jahr_in_datum(row["TAG VON"]) + "-datum-zaehlerwechsel"] = "NICHT_VORHANDEN"
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

def zaehler_aus_db():
    global zaehler_db
    global jahre_dropdown
    global db_zaehler_found
    global zaehler_button_check
    print("Zähler werden aus DB importiert")
    zaehler_db = db_datei_oeffnen(db_zaehler)
    zaehler_db = tablefields_to_int(zaehler_db)
    zaehler_sortieren()
    zaehler_label_ui.refresh('Zähler-Datenbank gefunden!')  
    zaehler_grid_ui.refresh()
    zaehler_button_check.enable()
    db_zaehler_found = 1

def zaehler_liste_upload(e: events.UploadEventArguments):
    global zaehler_db
    jahre_in_zaehler = []
    if db_zaehler_found == 1:
        for key,value in zaehler_db[0].items():
            if "-zaehler" in key:
                jahre_in_zaehler.append(int(key[:4]))

        # Abrechnung des letzten erfassten Jahres muss erstellt sein - außer die Jahresenddaten sind nicht vorhanden

        datei_abrechnung = ordner_abrechnungen + "\\" + "Abrechnung-" + str(max(jahre_in_zaehler)) + "\\" + "Abrechnung-" + str(max(jahre_in_zaehler)) + ".csv"
        if Path(datei_abrechnung).is_file() or (str(max(jahre_in_zaehler)) + "1231-zaehler") not in zaehler_db[0].keys():
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
    zaehler_db = import_zaehler_liste(import_zaehlerdaten_visu(csv_import.getvalue()))
    print("Zählerliste importiert")
    for row in zaehler_db:
        for key,value in row.items():
            if "Ident" in key or ("-zaehler" in key and "datum" not in key):
                row[key] = int(value)
    zaehler_sortieren()
    db_sichern("Upload Zählerdaten")
    zaehler_grid_ui.refresh()

# Sortiert die Zählerspalten - neuestes Jahr ist vorne

def zaehler_sortieren():
    global zaehler_db
    zaehler_keys_temp = []
    zaehler_keys = []
    zaehlerkeys_sortiert = []
    zaehler_db_temp = []
    temprow = {}
    for key in zaehler_db[0].keys():
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
            for key in zaehler_db[0].keys():
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
            for key in zaehler_db[0].keys():
                if jahr in key and key[:8].isdigit():
                    zaehlerkeys_sortiert.append(key)

    for row in zaehler_db:
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
    zaehler_db = zaehler_db_temp


### Sucht in den Zählerdaten nach "-1" und frägt dann im Dialog nach neuem Zählerwert. 
### Es wird nur 1 Ergebnis ausgewertet und der neue Wert wird dann in der Datenbank hinterlegt

def check_zaehlerdaten():
    global zaehler_dialog_check_label01
    global zaehler_dialog_check_label02
    global dialog_zaehler_check
    global zaehler_input_values
    index = -1
    na_found = 0
    number_na_found = 0
    zaehler_input_values = {}
    for row in zaehler_db:
        if -1 in row.values() or "NICHT_VORHANDEN" in row.values():
            number_na_found = number_na_found + 1
    if number_na_found > 0:
        for row in zaehler_db:
            index = index + 1
            for key,value in row.items():
                if ("zaehler" in key) and ("datum" not in key) and (value == -1):
                    na_found = 1
                    zaehler_dialog_check_label01.set_text("Bitte Zählerstand manuell eintragen")
                    zaehler_dialog_check_label02.set_text(row["Name"] + " " + row["Vorname"] + " " + key)
                    zaehler_dialog_check_input01.label = "Zählerstand"
                    zaehler_dialog_check_input01.value = ""
                    zaehler_input_values["listid"] = index
                    zaehler_input_values["Key"] = key
                    zaehler_input_values["Type"] = "NUMBER"
                if "datum" in key and (value == "NICHT_VORHANDEN"):
                    na_found = 1
                    zaehler_dialog_check_label01.set_text("Bitte Datum manuell eintragen")
                    zaehler_dialog_check_label02.set_text(row["Name"] + " " + row["Vorname"] + " " + key)
                    zaehler_dialog_check_input01.label = "Datum Zählerwechsel"
                    zaehler_dialog_check_input01.value = ""
                    zaehler_input_values["listid"] = index
                    zaehler_input_values["Key"] = key
                    zaehler_input_values["Type"] = "TEXT"
                if na_found == 1:
                    dialog_zaehler_check.open()
                    break
    else:
        ui.notify("Zählerdaten geprüft - keine Fehler gefunden", type="positive")


def zaehler_speichern():
    for row in zaehler_db:
        if -1 in row.values() or "NICHT_VORHANDEN" in row.values():
            ui.notify("Fehler in der Tabelle gefunden. Bitte Daten vor Speichern überprüfen und korrigieren.", type="warning")
            return
    db_datei_speichern(db_zaehler, zaehler_db)
    ui.notify('Zählerdaten gespeichert', type="positive")
    zaehler_button_speichern.disable()

# Zählerstand wird nur in UI Tabelle übernommen, noch nicht in DB gespeichert

def dialog_zaehlerstand_uebernehmen():
    global zaehler_input_values
    log_daten = str(zaehler_db[zaehler_input_values["listid"]]["Ident"]) + " " + str(zaehler_db[zaehler_input_values["listid"]]["Name"]) + " " + str(zaehler_db[zaehler_input_values["listid"]]["Vorname"]) + " ::: " + str(zaehler_input_values["Key"]) + " ::: " + str(zaehler_db[zaehler_input_values["listid"]][zaehler_input_values["Key"]]) + " ===> " + str(zaehler_dialog_check_input01.value)
    change_log_info("ZÄHLER", log_daten)
    if zaehler_input_values["Type"] == "NUMBER":
        zaehler_db[zaehler_input_values["listid"]][zaehler_input_values["Key"]] = int(zaehler_dialog_check_input01.value)
    else:
        zaehler_db[zaehler_input_values["listid"]][zaehler_input_values["Key"]] = str(zaehler_dialog_check_input01.value)
    zaehler_grid_ui.refresh()
    zaehler_button_speichern.enable()
    ui.notify("Zählerstand aktualisiert", type="positive")
    dialog_zaehler_check.close()

def zaehler_tabelle_on_change(event):
    global zaehler_grid
    global zaehler_db
    if event["newValue"] == None or event["newValue"] == -1:
         return
    zaehler_db[int(event["rowId"])][event["colId"]] = event["newValue"]
    zaehler_button_speichern.enable()
    change_log("ZÄHLER", event)
    ui.notify("Daten aktualisiert", type="positive")

def zaehler_columns_erstellen(table):
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
                column_element["cellStyle"] = {'backgroundColor': col_cell_mod}
                column_element["cellEditor"] = 'agStringCellEditor'
            if "-zaehler" in key and "datum" not in key:
                column_element["filter"] = 'agNumberColumnFilter'
                column_element["editable"] = True
                column_element["cellStyle"] = {'backgroundColor': col_cell_mod}
                column_element["cellEditor"] = 'agNumberCellEditor'
                column_element["cellEditorParams"]= {"min": -1,"step": 1}
            columns.append(column_element)

    return columns   

@ui.refreshable
def zaehler_grid_ui():
    global zaehler_grid
    zaehler_grid = ui.aggrid({
        'defaultColDef': {
            'editable': False,
            'resizable': True,
            'wrapHeaderText': True,
            'autoHeaderHeight': True,
        },
        'columnDefs': zaehler_columns_erstellen(zaehler_db),
        'rowData': zaehler_db,
        'domLayout': 'autoHeight',
        'pagination': True,
        'paginationPageSize': pagination
    }).on(
        'cellValueChanged',
        lambda event: zaehler_tabelle_on_change(event.args)
    ).style('height: 100%')

def zaehlerdaten_ui():
    global zaehler_db
    global db_zaehler_found
    global upload_overwrite_switch
    global zaehler_dialog_check_label01
    global zaehler_dialog_check_label02
    global dialog_zaehler_check
    global zaehler_dialog_check_input01
    global zaehler_grid
    global zaehler_button_check
    global zaehler_button_speichern
    with ui.dialog() as dialog_zaehler_check, ui.card():
        zaehler_dialog_check_label01 = ui.label("Bitte Zählerstand manuell eintragen")
        zaehler_dialog_check_label02 = ui.label("")
        zaehler_dialog_check_input01 = ui.input("Zählerstand")
        with ui.row():
            ui.button("Übernehmen", on_click=lambda: dialog_zaehlerstand_uebernehmen())
            ui.button("Abbrechen", on_click=dialog_zaehler_check.close)
    zaehler_label_ui("")
    with ui.row():
        ui.upload(label='Zählerdaten aus Visualisierungs-Export hochladen', on_upload=zaehler_liste_upload, auto_upload=True, max_files=1).props("accept=.csv").classes('max-w-full')
        upload_overwrite_switch = ui.switch('Daten bei Upload überschreiben')
        zaehler_button_check = ui.button("Daten überprüfen", icon='task_alt', on_click=lambda: (check_zaehlerdaten()))
        zaehler_button_check.disable()
        zaehler_button_speichern = ui.button('Speichern', icon='save', on_click=lambda: (zaehler_speichern())).props('color=' + speichernbutton)
        zaehler_button_speichern.disable()    
    zaehler_grid_ui()
    if db_datei_oeffnen(db_zaehler)[0] == "file not found":
        zaehler_label_ui.refresh('Keine Zählerdaten in Datenbank. Upload CSV-Datei mit Zählerdaten.')
    else:
        db_zaehler_found = 1
        zaehler_aus_db()    

    

###########################################################################################################################
### ENDE ZÄHLER
###########################################################################################################################

###########################################################################################################################
### ANFANG ABRECHNUNG
###########################################################################################################################


### Liest aus den Zählerdaten die verfügbaren Jahre aus.

def jahre_abrechnung():
    global jahre_dropdown
    global jahrliste_einlesbar
    global jahrliste_erstellbar
    jahrliste = []
    jahrliste_erstellbar = []
    jahrliste_einlesbar = []
    zaehler_aus_db()
    if zaehler_db == []:
        ui.notify("Zählerdatenbank nicht gefüllt!", type="warning")
        return
    if abschlag_db == []:
        ui.notify("Abschlag-Datenbank nicht gefüllt", type="warning")
        return
    for key in zaehler_db[0]:
        if "1231" in key:
            if (str(int(key[0:4]) - 1) + "1231-zaehler") in zaehler_db[0].keys():
                if ("Abschlag-" + str(int(key[0:4]))) in abschlag_db[0].keys():
                    if ("Mindest-Vertragsleistung-" + str(int(key[0:4]))) in abnehmer_db[0].keys():
                        if ("Mindest-Vertragsleistung-" + str(int(key[0:4]) - 1)) in abnehmer_db[0].keys():
                            jahrliste.append(key[0:4])
                            jahrliste_erstellbar.append(key[0:4])
                        else:
                            ui.notify("Für Jahr " + str(int(key[0:4]) - 1) + " (Vorjahr von " + str(key[0:4]) + ") ist keine Mindest-Vertragsleistung hinterlegt.", type="warning")
                    else:
                        ui.notify("Für Jahr " + str(key[0:4]) + " ist keine Mindest-Vertragsleistung hinterlegt.", type="warning")
                else:
                    ui.notify("Für Jahr " + str(key[0:4]) + " ist kein Abschlag hinterlegt.", type="warning")
    pfad_ordner_abrechnungen = Path(ordner_abrechnungen)
    for item in pfad_ordner_abrechnungen.iterdir():
        if item.is_dir():
            if item.name[:-4] == 'Abrechnung-':
                datei_abrechnung = ordner_abrechnungen + "\\" + item.name + "\\" + "Abrechnung-" + item.name[-4:] + ".csv"
                if Path(datei_abrechnung).is_file():
                    jahrliste_einlesbar.append(item.name[-4:])
                    if item.name[-4:] not in jahrliste:
                        jahrliste.append(item.name[-4:])
    jahrliste.sort()
    jahre_dropdown.set_options(jahrliste)
    reset_abrechnung()

# Buttons ein/ausblenden in Abhängigkeit davon, ob Abrechnung gespeichert wurde bzw. ob alle Daten vorliegen, um Abrechnung zu erstellen

def reset_abrechnung():
    global abrechnung
    global za_switch
    abr_button_erstellen.disable()
    abr_button_einlesen.disable()
    if jahre_dropdown.value in jahrliste_einlesbar:
        abr_button_einlesen.enable()
        mwst_jahr.disable()
    if jahre_dropdown.value in jahrliste_erstellbar:
        abr_button_erstellen.enable()
        mwst_jahr.enable()
    abr_button_download.disable()
    abr_button_plausibel.disable()
    abr_button_pdf.disable()
    abrechnung = []
    za_switch.value = False
    abrechnung_grid_ui.refresh()
    label_umsatz.set_text("")

   
async def abr_speichern():
    # Speichert die Abrechnung als CSV, hinterlegt die neuen Abschläge und passt ggf. die Mindestabnahme an.
    global dialog_abr_bestaetigung
    global checkbox_ueberschreiben
    global datei_abrechnung_aktuell
    global speichern_abbruch

    # Überprüft, ob die Mindestabnahme für das neue Jahr erneut ausgesetzt werden soll. Sonst wird die Mindestabnahme des letzen Jahres, wo sie gesetzt war übernommen

    async def mindestabnahme_pruefen(jahr):
        def mv_aussetzen():
            dialog_mv.close()
            row["Mindest-Vertragsleistung-" + str(int(jahr) + 1)] = 0

        def mv_nicht_aussetzen():
            dialog_mv.close()
            row["Mindest-Vertragsleistung-" + str(int(jahr) + 1)] = letzte_mindestabnahme(row["Ident"])

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

        for row in abnehmer_db:
            if row["Mindest-Vertragsleistung-" + str(int(jahr))] == 0:
                label_mv.set_text("Für den Abnehmer " + row["Name"] + " " + row["Vorname"] + " mit der Anschluss-Nr. " + row["Ident"] + " wurde im Abrechnungsjahr die Mindestabnahme ausgesetzt.")
                dialog_mv.open()
                await dialog_mv
            else:
                row["Mindest-Vertragsleistung-" + str(int(jahr) + 1)] = letzte_mindestabnahme(row["Ident"])

    def mindestabnahme_speichern(jahr):
        global abnehmer_db
        db_datei_speichern(db_abnehmer, abnehmer_db)
        ui.notify("Mindestabnahmen aktualisiert", type="positive")
        abnehmer_aus_db()


    def abrechnung_speichern_exec():
        # Speichert neuen Abschlag und Abrechnung
        for abrechnung_row in abrechnung:
            for abschlag_row in abschlag_db:
                if abrechnung_row["Ident"] == abschlag_row["Ident"]:
                    abschlag_row["Abschlag-"+ str(abrechnung_row["Folgejahr"])] = abrechnung_row["neuer Abschlag"]
        db_datei_speichern(db_abschlag, abschlag_db)
        abschlag_aus_db()
        datei_speichern(datei_abrechnung_aktuell, abrechnung)
        ui.notify(text_bestaetigung, type="positive")
        abr_button_download.enable()
        abr_button_plausibel.enable()
        abr_button_pdf.enable()
        abr_button_speichern.disable()                

    # Überprüft, ob Vorhandensein der Abrechnung erkannt wurde und blendet dann zusätzlich Checkbox für das Überschreiben ein

    def abrechnung_speichern_check():
        global text_bestaetigung
        text_bestaetigung = ""
        if checkbox_ueberschreiben.visible == True and checkbox_ueberschreiben.value == True:
                checkbox_ueberschreiben.set_value(False)
                text_bestaetigung = "Bestehende Abrechnungs-Datei und/oder Abschläge überschrieben"
                abrechnung_speichern_exec()
                dialog_abr_bestaetigung.close()
        elif checkbox_ueberschreiben.visible == False:
                text_bestaetigung = "Abschläge und Abrechnungs-Datei gespeichert"
                abrechnung_speichern_exec()
                dialog_abr_bestaetigung.close()
        else:
            return     

    def speichern_abbrechen():
        global speichern_abbruch
        speichern_abbruch = 1
        dialog_abr_bestaetigung.close()

    async def dialog_abfrage_speichern():
        global checkbox_ueberschreiben
        global dialog_abr_bestaetigung
        with ui.dialog() as dialog_abr_bestaetigung, ui.card():
            dialog_abr_label01 = ui.label('Möchten Sie die Abrechnungsdaten wirklich speichern?')
            checkbox_ueberschreiben = ui.checkbox('bestehende Daten überschreiben')
            if ueberschr == 1:
                checkbox_ueberschreiben.set_visibility(visible=True)
            else:
                checkbox_ueberschreiben.set_visibility(visible=False)
            with ui.row():
                ui.button('Ja', on_click=abrechnung_speichern_check)
                ui.button('Nein', on_click=speichern_abbrechen)  
        dialog_abr_bestaetigung.open()
        await dialog_abr_bestaetigung    


    # Prüft, ob die Verzeichnisse vorhanden sind und ob bereits eine Abrechnung besteht
    ueberschr = 0
    if abrechnung == []:
        ui.notify("Bitte erst Abrechnung erstellen, dann speichern.", type="info")
        return
    ordner_abrechnung_aktuell = ordner_abrechnungen + "\\" + "Abrechnung-" + str(jahre_dropdown.value)
    pfad_ordner_abrechnung_aktuell = Path(ordner_abrechnung_aktuell)
    if not pfad_ordner_abrechnung_aktuell.exists():
        pfad_ordner_abrechnung_aktuell.mkdir()
    datei_abrechnung_aktuell = ordner_abrechnung_aktuell + "\\" + "Abrechnung-" + str(jahre_dropdown.value) + ".csv"
    if ("Abschlag-" + str((int(jahre_dropdown.value) + 1))) in abschlag_db[0].keys() or Path(datei_abrechnung_aktuell).exists():
        ueberschr = 1
    speichern_abbruch = 0
    await dialog_abfrage_speichern()
    if speichern_abbruch == 0:
        await mindestabnahme_pruefen(jahre_dropdown.value)
        mindestabnahme_speichern(jahre_dropdown.value)
    abr_button_plausibel.enable()




def umsatz_berechnen():
    abschlag_netto = 0
    for row in abrechnung:
        abschlag_netto=round(abschlag_netto + float(row["Zahlung Abschläge Netto"]) + float(row["Jahresabrechnung Netto"]),2)
    label_umsatz.set_text(str(abschlag_netto) + " €")

def abrechnung_von_db():
    global abrechnung
    global abr_button_download
    global abr_button_plausibel
    datei_abrechnung = ordner_abrechnungen + "\\" + "Abrechnung-" + str(jahre_dropdown.value) + "\\" + "Abrechnung-" + str(jahre_dropdown.value) + ".csv"
    abrechnung = datei_oeffnen(datei_abrechnung)
    abrechnung_grid_ui.refresh()
    abr_button_speichern.disable()
    abr_button_download.enable()
    abr_button_plausibel.enable()
    abr_button_pdf.enable()
    umsatz_berechnen()


def zwischenablesung():
    if za_switch.value == True:
        za_mwst.visible = True
        za_datum.visible = True
        za_datum_auslesen()
    else:
        za_mwst.visible = False
        za_datum.visible = False
        return

def za_datum_auslesen():
    global za_datum
    global za_switch
    za_datum_list = []
    abrechnungsjahr = jahre_dropdown.value
    if abrechnungsjahr == None:
        ui.notify('Bitte zuerst Abrechnungsjahr auswählen.', type="info")
        return 
    za_found = False
    for key in zaehler_db[0].keys():
        if str(abrechnungsjahr) in key and "wechsel" not in key and (str(abrechnungsjahr) + "1231") not in key and (str(abrechnungsjahr) + "0101") not in key:
            print(abrechnungsjahr + " zw found")
            za_datum_list.append(key)
            za_found = True 
    za_datum_list_format = []
    for element in za_datum_list:
        element_datum = element[6:8] + "." + element[4:6] + "." + element[0:4]
        za_datum_list_format.append(element_datum)
    if za_datum_list_format == []:
        za_switch.value = False
        ui.notify('Abrechnungsjahr ' + abrechnungsjahr + ' hat keine Zwischenablesung.', type="info")
    za_datum.set_options(za_datum_list_format)

# Prüfung, ob Verbrauch zum Vorjahr abweicht

def abrechnung_plausibel():

    if (str(int(jahre_dropdown.value) - 1)) not in jahrliste_einlesbar:
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

        plausibel_verbrauch_grid.options['columnDefs'] = columns
        plausibel_verbrauch_grid.options['rowData'] = pruef_erg_verbrauch
        plausibel_verbrauch_grid.options['rowSelection'] = 'multiple'
        plausibel_verbrauch_grid.options['pagination'] = 'false'
        plausibel_verbrauch_grid.options['paginationPageSize'] = '15'
        plausibel_verbrauch_grid.options['alwaysShowHorizontalScroll'] = 'true'
        plausibel_verbrauch_grid.options['fullWidthCellRenderer'] = 'fullWidthCellRenderer'
        plausibel_verbrauch_grid.update()

    def plausibel_mindestabnahme_grid_update():
        columns = []
        column_element = {}
        if pruef_erg_mindestabnahme != []:
            for key in pruef_erg_mindestabnahme[0].keys():
                column_element = {}
                column_element['headername'] = key
                column_element["field"] = key
                columns.append(column_element)

            plausibel_mindestabnahme_grid.options['columnDefs'] = columns
            plausibel_mindestabnahme_grid.options['rowData'] = pruef_erg_mindestabnahme
            plausibel_mindestabnahme_grid.options['rowSelection'] = 'multiple'
            plausibel_mindestabnahme_grid.options['pagination'] = 'false'
            plausibel_mindestabnahme_grid.options['paginationPageSize'] = '15'
            plausibel_mindestabnahme_grid.options['alwaysShowHorizontalScroll'] = 'true'
            plausibel_mindestabnahme_grid.options['fullWidthCellRenderer'] = 'fullWidthCellRenderer'
            plausibel_mindestabnahme_grid.update()

    def pruefung_verbrauch():
        global pruef_erg_verbrauch
        # Aktuelle Abrechnung wird mit Abrechnung von Vorjahr verglichen
        datei_vorjahr = ordner_abrechnungen + "\\" + "Abrechnung-" + str(int(jahre_dropdown.value)-1) + "\\" + "Abrechnung-" + str(int(jahre_dropdown.value)-1) + ".csv"
        abrechnung_vorjahr = datei_oeffnen(datei_vorjahr)
        ergebnis = []
        for anschluss in abrechnung:
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
        pruef_erg_verbrauch = sorted(ergebnis_temp, key=lambda x: x["Abw absolut"], reverse=True) 

    def pruefung_mindestabnahme():
        global pruef_erg_mindestabnahme
        ergebnis = []
        for anschluss in abrechnung:
            ergebnis_row = {}
            for anschluss_abnehmer in abnehmer_db:
                if anschluss["Ident"] == anschluss_abnehmer["Ident"]:
                    if str(anschluss["Mindestvertragsleistung"]) != str(anschluss_abnehmer["Mindest-Vertragsleistung-" + str(int(anschluss["Abrechnungsjahr"])+1)]):
                        ergebnis_row["Ident"] = anschluss["Ident"]
                        ergebnis_row["Name"] = anschluss["Name"]
                        ergebnis_row["Vorname"] = anschluss["Vorname"]
                        ergebnis_row["Mindestabnahme-" + anschluss["Abrechnungsjahr"]] = anschluss["Mindestvertragsleistung"]
                        ergebnis_row["Mindestabnahme-" + str(int(anschluss["Abrechnungsjahr"])+1)] = anschluss_abnehmer["Mindest-Vertragsleistung-" + str(int(anschluss["Abrechnungsjahr"])+1)]
                        ergebnis.append(ergebnis_row)
        pruef_erg_mindestabnahme = ergebnis

    with ui.dialog().style("width: 800px; max-width: none") as dialog_plausibel:
        global plausibel_verbrauch_grid
        global plausibel_mindestabnahme_grid
        with ui.card().style("width: 800px"):
            ui.button('', icon='close', on_click=dialog_plausibel.close).classes('absolute top-3 right-3')
            with ui.row():
                ui.label('Plausibilitätsprüfung').style("font-size: 24px; font-weight: bold;")
            with ui.row():
                ui.label('Aufstellung Veränderung der verbrauchten kWh zum Vorjahr. Es werden alle Abweichungen (positiv wie negativ) größer als 3000 kWh in "Rot" angezeigt.')
                columns = []
                table = []
                plausibel_verbrauch_grid = ui.aggrid({
                    'defaultColDef': {'flex': 1, 'editable': False, 'resizable': True, 'wrapHeaderText': True, 'autoHeaderHeight': True, 'wrapText': True, 'autoHeight': True},
                    'columnDefs': columns,
                    'rowData': table,
                    'domLayout': 'normal', 
                }).style('height: 300px; width: 500px')
            with ui.row():
                ui.label('Veränderungen bei Mindestabnahme')
                columns = []
                table = []
                plausibel_mindestabnahme_grid = ui.aggrid({
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


def abrechnung_columns_erstellen(table):
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
def abrechnung_grid_ui():
    global abrechnung_grid
    abrechnung_grid = ui.aggrid({
        'defaultColDef': {
            'editable': False,
            'resizable': True,
            'wrapHeaderText': True,
            'autoHeaderHeight': True,
        },
        'columnDefs': abrechnung_columns_erstellen(abrechnung),
        'rowData': abrechnung,
        'domLayout': 'autoHeight',
        'pagination': True,
        'paginationPageSize': pagination
    }).style('height: 100%')



def abrechnung_ui():
    global checkbox_ueberschreiben
    global naechstes_jahr
    global jahre_dropdown
    global mwst_jahr
    global dialog_abr_bestaetigung
    global abrechnung_grid
    global abr_button_erstellen
    global abr_button_einlesen
    global abr_button_pdf
    global abr_button_speichern
    global abr_button_download
    global abr_button_plausibel
    global abr_progress_pdf
    global za_datum
    global za_mwst
    global za_switch
    global label_umsatz
    ui.label('Jahresabrechnung Wärmelieferung').classes("text-2xl font-bold")
    with ui.row():
        jahre_dropdown = ui.select([], label='Abrechnungsjahr', on_change=reset_abrechnung).classes('w-48')
        mwst_jahr = ui.select(['7','19'], label='Mehrwertsteuer in %').classes('w-48')
        za_switch = ui.switch("Zwischenablesung", on_change=zwischenablesung)
        za_datum = ui.select([], label='Datum Zwischenabl.').classes('w-48').props('visible=false')
        za_datum.visible = False
        za_mwst = ui.select(['7','19'], label='MwSt. % bis Zwischenabl.').classes('w-48')
        za_mwst.visible = False
        abr_button_speichern = ui.button('Speichern', icon='save', on_click=abr_speichern).props('color=' + speichernbutton)
        abr_button_speichern.disable()

    with ui.row():
        abr_button_erstellen = ui.button('Erstellung Jahresabrechnung', icon='calculate', on_click=abrechnung_erstellen_gui)
        abr_button_einlesen = ui.button('Jahresabrechnung von DB einlesen', icon='file_open', on_click=abrechnung_von_db)
        abr_button_erstellen.disable()
        abr_button_einlesen.disable()
        abr_button_download = ui.button('CSV mit Kommas herunterladen', icon='file_download', on_click=csv_komma_abrechnung_download)
        abr_button_download.disable()
        abr_button_plausibel = ui.button("Plausibilitätsprüfung", icon="check_circle", on_click=abrechnung_plausibel)
        abr_button_plausibel.disable()
        abr_button_pdf = ui.button('Word/PDF-Abrechnungen erzeugen', icon='picture_as_pdf', on_click=abrechnungen_dateien_erstellen).props('color=red-5')
        abr_button_pdf.disable()
        abr_progress_pdf = ui.circular_progress(min=0, max=100, color="black").classes('invisible')
        ui.label('Gesamtumsatz netto: ')
        label_umsatz = ui.label("")
    abrechnung_grid_ui()


async def csv_komma_abrechnung_download():
    filename = "Abrechnung " + jahre_dropdown.value + ".csv"
    await komma_datei_speichern(abrechnung, filename)

def abrechnung_erstellen_gui():
    global abrechnung
    global abrechnung_fuer_pdf
    global abr_button_speichern
    global abr_button_download
    for row in zaehler_db:
        if "-1" in row.values():
            ui.notify("Es sind ungültige Zählerdaten vorhanden. Bitte Zählerdaten überprüfen.", type="negative")
            return
    if jahre_dropdown.value == None or mwst_jahr.value == None:
        ui.notify("Bitte Jahr und Mwst-Satz auswählen.", type="info")
        return
    # Änderung für v2: Rechnen ohne Oberfläche; Meldungen und Anzeige bleiben hier.
    abrechnung = abrechnung_berechnen(
        abnehmer_db, zaehler_db, abschlag_db, arbeitspreis, grundgebuehr,
        jahre_dropdown.value, mwst_jahr.value, za_switch.value, za_datum.value,
        za_mwst != [], za_mwst.value if za_mwst != [] else None)

    abrechnung_grid_ui.refresh()
    abr_button_speichern.enable()
    abr_button_download.enable()
    umsatz_berechnen()

#### Letzte Mindestabhnahme, die nicht 0 ist ermitteln. Wenn keine vorhanden, dann Original-Mindestabnahme


def letzte_mindestabnahme(Ident):
    # Änderung für v2: Bestehende Aufrufe behalten; Daten explizit an das Rechenmodul übergeben.
    return mindestabnahme_berechnen(Ident, abnehmer_db)


def abrechnungen_dateien_erstellen():
    abrechnungen_word_erstellen()
    abrechnungen_pdf_erstellen()

def abrechnungen_word_erstellen():
    global ordner_abrechnungen_word
    global abrechnung_fuer_pdf
    ordner_abrechnungen_word = ordner_abrechnungen + "\\" + "Abrechnung-" + jahre_dropdown.value + "\\word"
    pfad_ordner_abrechnungen_word = Path(ordner_abrechnungen_word)
    if not pfad_ordner_abrechnungen_word.exists():
        pfad_ordner_abrechnungen_word.mkdir()
    dateien_in_ordner_loeschen(ordner_abrechnungen_word)
    ordner_abrechnung_jahr = ordner_abrechnungen + "\\" + "Abrechnung-" + str(jahre_dropdown.value)
    datei_abrechnung =  ordner_abrechnung_jahr + "\\" + "Abrechnung-" + str(jahre_dropdown.value) + ".csv"
    pfad_datei_abrechnung = Path(datei_abrechnung)
    if not pfad_datei_abrechnung.exists():
        ui.notify("Bitte erst Abrechnung für Jahr " + jahre_dropdown.value + " abspeichern.", type="info")
        return
    dateiname_vorlage = "Vorlage-Abrechnung-" + str(jahre_dropdown.value) + ".docx"
    datei_vorlage_abrechnung = ordner_vorlagen + "\\" + dateiname_vorlage
    pfad_datei_vorlage_abrechnung = Path(datei_vorlage_abrechnung)
    if not pfad_datei_vorlage_abrechnung.exists():
        ui.notify("Bitte Datei " + dateiname_vorlage + " in Ordner " + ordner_vorlagen + " ablegen.", type="info")
        return
    abrechnung_fuer_pdf = datei_oeffnen(datei_abrechnung)
    # Änderung für v2: Vorprüfungen bleiben hier; die Serienschleife liegt im Dokumentmodul.
    abrechnung_word_schreiben(abrechnung_fuer_pdf, datei_vorlage_abrechnung,
                             ordner_abrechnungen_word, jahre_dropdown.value,
                             mapping_wordfelder)

def abrechnungen_pdf_erstellen():
    global ordner_abrechnungen_word
    global ordner_abrechnungen_pdf
    global abr_progress_pdf
    global abrechnung_pdf_background
    docx_files_found = 0
    ordner_abrechnungen_pdf = ordner_abrechnungen + "\\" + "Abrechnung-" + jahre_dropdown.value + "\\pdf"
    pfad_ordner_abrechnungen_pdf = Path(ordner_abrechnungen_pdf)
    if not pfad_ordner_abrechnungen_pdf.exists():
        pfad_ordner_abrechnungen_pdf.mkdir()
    word_ordner = os.listdir(ordner_abrechnungen_word)
    for datei in word_ordner:
            if datei.endswith('docx'):
                docx_files_found = 1
    if docx_files_found == 0:
        return
    dateien_in_ordner_loeschen(ordner_abrechnungen_pdf)
    abrechnung_pdf_background = threading.Thread(target=abr_pdf_process)
#    pdf_stop_flag = threading.Event()
    abrechnung_pdf_background.start()
    abr_progress_pdf.classes(remove='invisible')


# PDF Verarbeitung Performance-optimiert

def abr_pdf_process():
    # Änderung für v2: Hintergrund-Thread und Fortschrittsanzeige bleiben an dieser Schnittstelle.
    abrechnung_pdf_konvertieren(ordner_abrechnungen_word, ordner_abrechnungen_pdf,
                               abr_progress_pdf.set_value)


###########################################################################################################################
### ENDE ABRECHNUNG
########################################################################################################################### 

###########################################################################################################################
### ANFANG ABSCHLAG
###########################################################################################################################

@ui.refreshable
def abschlag_label_ui(label):
    ui.label(label).style('font-size:100%')

def abschlag_aus_db():
    global abschlag_db
    global db_abschlag_found
    print("Abschläge werden aus DB importiert")
    abschlag_db = db_datei_oeffnen(db_abschlag)
    abschlag_db = tablefields_to_dotfloat(abschlag_db)
    abschlag_label_ui.refresh('Abschlags-Datenbank gefunden! Daten wurden geladen und können über einen neuen Upload überschrieben werden.')
    abschlag_grid_ui.refresh()
    db_abschlag_found = 1

def abschlag_upload(e: events.UploadEventArguments):
    global abschlag_db
    with StringIO(e.content.read().decode('iso-8859-1', errors='ignore')) as f:
        abschlag_import = import_csv_inhalt(f)
    if string_in_dict(abschlag_import[0], 'Ident') == True and string_in_dict(abschlag_import[0], 'Name') == True and string_in_dict(abschlag_import[0], 'Vorname') == True and string_in_dict(abschlag_import[0], 'Abschlag') == True:
        abschlag_db = abschlag_import
    else:
        ui.notify('Importdaten entsprechen nicht dem erforderlichen Format. Es müssen Tabellenspalten für Ident, Name, Vorname und Abschlag-<Jahr> enthalten sein.', type="warning")
        return
    db_sichern("Upload Abschlagsdaten")
    abschlag_grid_ui.refresh()
    abschlag_button_speichern.enable()


def abschlag_speichern():
    db_datei_speichern(db_abschlag, abschlag_db)
    ui.notify('Abschlagsdaten gespeichert', type="positive")
    abschlag_button_speichern.disable()


def abschlag_tabelle_on_change(event):
    global abschlag_grid
    global abschlag_db
    if event["newValue"] == None:
        return
    abschlag_db[int(event["rowId"])][event["colId"]] = event["newValue"]
    change_log("ABSCHLAG", event)
    abschlag_button_speichern.enable()

def abschlag_columns_erstellen(table):
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
                column_element["cellStyle"] = {'backgroundColor': col_cell_mod}
                column_element["cellEditor"]='agStringCellEditor'
            if "Abschlag-" in key:
                column_element["editable"] = True
                column_element["cellStyle"] = {'backgroundColor': col_cell_mod}
                column_element["cellEditor"]='agNumberCellEditor'
            columns.append(column_element)

    return columns


@ui.refreshable
def abschlag_grid_ui():
    global abschlag_grid
    abschlag_grid = ui.aggrid({
        'defaultColDef': {
            'editable': False,
            'resizable': True,
            'wrapHeaderText': True,
            'autoHeaderHeight': True,
        },
        'columnDefs': abschlag_columns_erstellen(abschlag_db),
        'rowData': abschlag_db,
        'domLayout': 'autoHeight',
        'pagination': True,
        'paginationPageSize': pagination
    }).on(
        'cellValueChanged',
        lambda event: abschlag_tabelle_on_change(event.args)
    ).style('height: 100%')


def abschlag_ui():
    global abschlag_db
    global db_abschlag_found
    global abschlag_button_speichern
    global abschlag_grid
    abschlag_label_ui("")
    with ui.row():
        ui.upload(on_upload=abschlag_upload, auto_upload=True, max_files=1).props("accept=.csv").classes('max-w-full')
        abschlag_button_speichern = ui.button('Speichern', icon='save', on_click=lambda: abschlag_speichern()).props('color=' + speichernbutton)
        abschlag_button_speichern.disable()
    abschlag_grid_ui()

    if db_datei_oeffnen(db_abschlag)[0] == "file not found":
        abschlag_label_ui.refresh('Keine Abschlagsdaten in Datenbank! Upload Abschlag per CSV-Datei möglich.')
    else:
        db_abschlag_found = 1
        abschlag_label_ui.refresh('Abschlagsdaten gefunden! Daten wurden geladen. Daten aus Datenbank können über einen neuen Upload überschrieben und ergänzt werden.')
        abschlag_aus_db()   


###########################################################################################################################
### ENDE ABSCHLAG
###########################################################################################################################


###########################################################################################################################
### ANFANG RÜCKVERGÜTUNG
###########################################################################################################################

def rueckv_jahre_einlesen():
    global rueckv_jahre_dropdown
    global rueckv_button_einlesen
    global rueckv_jahre_einlesbar
    global rueckv_jahre_erstellbar
    rueckv_button_einlesen.disable()
    rueckv_jahr_liste = []
    rueckv_jahre_erstellbar = []
    rueckv_jahre_einlesbar = []
    pfad_ordner_abrechnungen = Path(ordner_abrechnungen)
    for item in pfad_ordner_abrechnungen.iterdir():
        if item.is_dir():
            if item.name[:-4] == 'Abrechnung-':
                datei_abrechnung = ordner_abrechnungen + "\\" + item.name + "\\" + "Abrechnung-" + item.name[-4:] + ".csv"
                if Path(datei_abrechnung).is_file():
                    rueckv_jahr_liste.append(item.name[-4:])
                    rueckv_jahre_erstellbar.append(item.name[-4:])
    pfad_ordner_rueckv = Path(ordner_rueckv)
    for item in pfad_ordner_rueckv.iterdir():
        if item.is_dir():
            if item.name[:-4] == "Rückvergütung-":
                datei_rueckv = ordner_rueckv + "\\" + item.name + "\\" + "Rückvergütung-" + item.name[-4:] + ".csv"
                if Path(datei_rueckv).is_file():
                    rueckv_jahre_einlesbar.append(item.name[-4:])
                    if item.name[-4:] not in rueckv_jahr_liste:
                        rueckv_jahr_liste.append(item.name[-4:])
    rueckv_jahr_liste.sort()
    rueckv_jahre_dropdown.set_options(rueckv_jahr_liste)


def reset_rueckv():
    rueckv_prozent.value = 0.00
    rueckv_datum_beschluss.value = ""
    rueckv_button_erstellen.disable()
    rueckv_button_einlesen.disable()
    if rueckv_jahre_dropdown.value in rueckv_jahre_einlesbar:
        rueckv_button_einlesen.enable()
        rueckv_prozent.disable()
        rueckv_datum_beschluss.disable()
        rueckv_button_speichern.disable()
    else:
        rueckv_button_einlesen.disable()
    if rueckv_jahre_dropdown.value in rueckv_jahre_erstellbar:
        rueckv_button_erstellen.enable()
        rueckv_prozent.enable()
        rueckv_datum_beschluss.enable()
        rueckv_button_speichern.disable()
    rueckv_button_download.disable()
    rueckv_button_pdf.disable()
    rueckv_grid_ui.refresh()



###### Muss Abrechnungs-File, nicht Abschlag überprüfen

def rueckv_tabelle_erstellen():
    global rueckv_button_speichern
    global rueckv_button_download
    global rueckv_mwst
    global rueckv_mwst2

    rueckv_tabelle = []
    if rueckv_jahre_dropdown.value == None:
        return
    abrechnung_datei = []
    abrechnung_datei = datei_oeffnen(ordner_abrechnungen + "\\" + "Abrechnung-" + str(rueckv_jahre_dropdown.value) + "\\" + "Abrechnung-" + str(rueckv_jahre_dropdown.value) + ".csv")
    # Änderung für v2: Reinen Tabellenaufbau ins Berechnungsmodul verlagern.
    rueckv_tabelle = rueckverguetung_vorbereiten(abrechnung_datei, rueckv_jahre_dropdown.value)
    # Änderung für v2: Wie bisher gelten anschließend die Steuersätze der letzten Zeile.
    if abrechnung_datei:
        rueckv_mwst = abrechnung_datei[-1]["MwSt-Satz"]
        if "Abrechnung ab ZA" in abrechnung_datei[0].keys():
            rueckv_mwst2 = abrechnung_datei[-1]["ZA MwSt"]
    rueckv_tabelle = rueckv_tabelle_berechnen(rueckv_tabelle)
    rueckv_button_speichern.enable()
    rueckv_button_download.enable()
    return rueckv_tabelle

def rueckv_tabelle_berechnen(table):
    # Änderung für v2: Leere Tabellen weiterhin ohne Zugriff auf Eingabefelder zurückgeben.
    if table == []:
        return table
    # Änderung für v2: Steuerwerte explizit übergeben; vorhandene Tabellen weiter direkt ändern.
    return rueckverguetung_berechnen(
        table, rueckv_prozent.value, rueckv_datum_beschluss.value, rueckv_mwst,
        rueckv_mwst2 if "MwSt bis ZA" in table[0].keys() else None)

def rueckv_tabelle_on_change(event):
    global rueckv_grid
    global rueckv_table
    global rueckv_button_speichern
    if event["newValue"] == None:
        return
    change_log("RÜCKVERGÜTUNG " + str(rueckv_jahre_dropdown.value), event)
    rueckv_table[int(event["rowId"])][event["colId"]] = event["newValue"]
    rueckv_table = rueckv_tabelle_berechnen(rueckv_table)

def rueckv_erstellen():
    global rueckv_table
    if rueckv_jahre_dropdown.value == None or rueckv_prozent.value == None or rueckv_datum_beschluss.value == "":
        ui.notify("Bitte Jahr, Mwst., Rückvergütungssatz und Beschlussdatum spezifiziern.", type="info")
        return
    rueckv_table = rueckv_tabelle_erstellen()
    rueckv_grid_ui.refresh()
    rueckv_button_speichern.enable()

def rueckv_speichern():
    global dialog_rueckv_bestaetigung
    global rueckv_checkbox_ueberschreiben
    global dialog_rueckv_label01
    global datei_rueckv_aktuell
    rueckv_checkbox_ueberschreiben.set_visibility(visible=False)
    if rueckv_table == []:
        ui.notify("Bitte erst Rückvergütung erstellen, dann speichern.", type="info")
        return
    ordner_rueckv_aktuell = ordner_rueckv + "\\" + "Rückvergütung-" + str(rueckv_jahre_dropdown.value)
    datei_rueckv_aktuell = ordner_rueckv_aktuell + "\\" + "Rückvergütung-" + str(rueckv_jahre_dropdown.value) + ".csv"
    pfad_ordner_rueckv_aktuell = Path(ordner_rueckv_aktuell)
    if not pfad_ordner_rueckv_aktuell.exists():
        pfad_ordner_rueckv_aktuell.mkdir()
    if Path(datei_rueckv_aktuell).exists():
        rueckv_checkbox_ueberschreiben.set_visibility(visible=True)
    dialog_rueckv_bestaetigung.open()

def rueckv_speichern_ja():
    global dialog_abr_bestaetigung
    if rueckv_checkbox_ueberschreiben.visible == True:
        if rueckv_checkbox_ueberschreiben.value == True:
            ui.notify("Bestehende Rückvergütungsdatei überschrieben.", type="info")
            datei_speichern(datei_rueckv_aktuell, rueckv_table)
            rueckv_von_db()         
            dialog_rueckv_bestaetigung.close()
    else:
            ui.notify("Rückvergütungsdatei gespeichert.", type="positive")
            datei_speichern(datei_rueckv_aktuell, rueckv_table)
            rueckv_von_db()
            dialog_rueckv_bestaetigung.close()


def rueckv_von_db():
    global rueckv_table
    datei_rueckv = ordner_rueckv + "\\" + "Rückvergütung-" + str(rueckv_jahre_dropdown.value) + "\\" + "Rückvergütung-" + str(rueckv_jahre_dropdown.value) + ".csv"
    rueckv_table = datei_oeffnen(datei_rueckv)
    rueckv_table = tablefields_to_dotfloat(rueckv_table)
    rueckv_grid_ui.refresh()
    rueckv_button_speichern.enable()
    rueckv_button_download.enable()
    rueckv_button_pdf.enable()

async def csv_komma_rueckv_download():
    filename = "Rückvergütung " + rueckv_jahre_dropdown.value + ".csv"
    await komma_datei_speichern(rueckv_table, filename)

def rueckv_columns_erstellen(table):
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
                column_element["cellStyle"] = {'backgroundColor': col_cell_mod}
                column_element["cellEditor"]='agNumberCellEditor'

            columns.append(column_element)

    return columns


@ui.refreshable
def rueckv_grid_ui():
    global rueckv_grid
    rueckv_grid = ui.aggrid({
        'defaultColDef': {
            'editable': False,
            'resizable': True,
            'wrapHeaderText': True,
            'autoHeaderHeight': True,
        },
        'columnDefs': rueckv_columns_erstellen(rueckv_table),
        'rowData': rueckv_table,
        'domLayout': 'autoHeight',
        'pagination': True,
        'paginationPageSize': pagination
    }).on(
        'cellValueChanged',
        lambda event: rueckv_tabelle_on_change(event.args)
    ).style('height: 100%')


def rueckverguetung_ui():
    global rueckv_jahre_dropdown
    global rueckv_mwst
    global rueckv_prozent
    global rueckv_grid
    global mwst_jahr
    global rueckv_datum_beschluss
    global rueckv_checkbox_ueberschreiben
    global dialog_rueckv_label01
    global dialog_rueckv_bestaetigung
    global rueckv_progress_pdf
    global rueckv_button_einlesen
    global rueckv_button_erstellen
    global rueckv_button_speichern
    global rueckv_button_download
    global rueckv_button_pdf
    global rueckv_table
    rueckv_table = []
    ui.label('Rückvergütung').classes("text-2xl font-bold")
    with ui.row():
        rueckv_jahre_dropdown = ui.select([], label='Jahr der Rückvergütung', on_change=reset_rueckv).classes('w-48')
        rueckv_prozent = ui.number(label='Rückergütung in %', format='%.2f')
        with ui.input('Datum Beschluss') as date:
            with date.add_slot('append'):
                ui.icon('edit_calendar').on('click', lambda: menu.open()).classes('cursor-pointer')
            with ui.menu() as menu:
                rueckv_datum_beschluss = ui.date({'from':'2024-01-01', 'to':'2024-12-31'},mask='DD.MM.YYYY').bind_value(date).props('range')
        rueckv_button_speichern = ui.button('Speichern', icon='save', on_click=rueckv_speichern).props('color=' + speichernbutton)
        rueckv_button_speichern.disable()
    with ui.row():
        rueckv_button_erstellen = ui.button('Erstellung Rückvergütung', icon='calculate', on_click=rueckv_erstellen)
        rueckv_button_erstellen.disable()
        rueckv_button_einlesen = ui.button('Rückvergütung von DB einlesen', icon='file_open', on_click=rueckv_von_db)
        rueckv_button_einlesen.disable()
        rueckv_button_download = ui.button('CSV mit Kommas herunterladen', icon='file_download', on_click=csv_komma_rueckv_download)
        rueckv_button_download.disable()
        rueckv_button_pdf = ui.button('Word/PDF-Rückvergütungen erzeugen', icon='picture_as_pdf', on_click=rueckv_dateien_erstellen).props('color=red-5')
        rueckv_button_pdf.disable()
        rueckv_progress_pdf = ui.circular_progress(min=0, max=100, color="black").classes('invisible')
    with ui.dialog() as dialog_rueckv_bestaetigung, ui.card():
        dialog_rueckv_label01 = ui.label('Möchten Sie die Rückvergütung wirklich speichern?')
        rueckv_checkbox_ueberschreiben = ui.checkbox('bestehende Daten überschreiben')
        with ui.row():
            ui.button('Ja', on_click=rueckv_speichern_ja)
            ui.button('Nein', on_click=dialog_rueckv_bestaetigung.close)
    rueckv_grid_ui()

def rueckv_dateien_erstellen():
    rueckv_word_erstellen()
    rueckv_pdf_erstellen()

def rueckv_word_erstellen():
    global ordner_rueckv_word
    global rueckv_fuer_pdf
    ordner_rueckv_word = ordner_rueckv + "\\" + "Rückvergütung-" + rueckv_jahre_dropdown.value + "\\word"
    pfad_ordner_rueckv_word = Path(ordner_rueckv_word)
    if not pfad_ordner_rueckv_word.exists():
        pfad_ordner_rueckv_word.mkdir()
    dateien_in_ordner_loeschen(ordner_rueckv_word)
    ordner_rueckv_jahr = ordner_rueckv + "\\" + "Rückvergütung-" + str(rueckv_jahre_dropdown.value)
    datei_rueckv =  ordner_rueckv_jahr + "\\" + "Rückvergütung-" + str(rueckv_jahre_dropdown.value) + ".csv"
    pfad_datei_rueckv = Path(datei_rueckv)
    if not pfad_datei_rueckv.exists():
        ui.notify("Bitte erst Rückvergütung für Jahr " + rueckv_jahre_dropdown.value + " abspeichern.", type="info")
        return
    dateiname_vorlage = "Vorlage-Rückvergütung-" + str(rueckv_jahre_dropdown.value) + ".docx"
    datei_vorlage_rueckv = ordner_vorlagen + "\\" + dateiname_vorlage
    pfad_datei_vorlage_rueckv = Path(datei_vorlage_rueckv)
    if not pfad_datei_vorlage_rueckv.exists():
        ui.notify("Bitte Datei " + dateiname_vorlage + " in Ordner " + ordner_vorlagen + " ablegen.", type="info")
        return
    rueckv_fuer_pdf = datei_oeffnen(datei_rueckv)
    # Änderung für v2: Vorprüfungen bleiben in der Oberfläche, Serienschleife auslagern.
    rueckverguetung_word_schreiben(rueckv_fuer_pdf, datei_vorlage_rueckv,
                                  ordner_rueckv_word, rueckv_jahre_dropdown.value,
                                  mapping_wordfelder)

def rueckv_pdf_erstellen():
    global ordner_rueckv_word
    global ordner_rueckv_pdf
    global rueckv_progress_pdf
    global rueckv_pdf_background
    docx_files_found = 0
    ordner_rueckv_pdf = ordner_rueckv + "\\" + "Rückvergütung-" + rueckv_jahre_dropdown.value + "\\pdf"
    pfad_ordner_rueckv_pdf = Path(ordner_rueckv_pdf)
    if not pfad_ordner_rueckv_pdf.exists():
        pfad_ordner_rueckv_pdf.mkdir()
    word_ordner = os.listdir(ordner_rueckv_word)
    for datei in word_ordner:
            if datei.endswith('docx'):
                docx_files_found = 1
    if docx_files_found == 0:
        return
    dateien_in_ordner_loeschen(ordner_rueckv_pdf)
    rueckv_pdf_background = threading.Thread(target=rueckv_pdf_process)
    rueckv_pdf_background.start()
    rueckv_progress_pdf.classes(remove='invisible')

# PDF-Erzeugung Performance-optimiert (Word wird nur 1x gestartet)

def rueckv_pdf_process():
    global ordner_rueckv_word
    global ordner_rueckv_pdf
    global pdfstop

    # Änderung für v2: Bestehenden Thread an die ausgelagerte Konvertierung anbinden.
    rueckverguetung_pdf_konvertieren(ordner_rueckv_word, ordner_rueckv_pdf,
                                    rueckv_progress_pdf.set_value)




###########################################################################################################################
### ENDE RÜCKVERGÜTUNG
###########################################################################################################################

###########################################################################################################################
### ANFANG KONTOTRANSAKTIONEN
###########################################################################################################################

@ui.refreshable
def konto_label_ui(label):
    ui.label(label).style('font-size:100%')

async def buchung_datei_speichern(content, dateiprefix):
    current_datetime = datetime.now().strftime("%Y-%m-%d")
    dateiname = str(dateiprefix) + "-" + current_datetime + ".csv"
    datei = await app.native.main_window.create_file_dialog(webview.SAVE_DIALOG, directory="%USERPROFILE\\Downloads", allow_multiple=False, save_filename=dateiname)
    if datei != None:
        with open(datei,'w') as f: 
            f.write(content)
            ui.notify(datei + " wurde gespeichert.", type="positive")
    else:
        return

def konto_upload(e: events.UploadEventArguments):
    global konto_db
    with StringIO(e.content.read().decode('iso-8859-1', errors='ignore')) as f:
        konto_db = import_csv_inhalt(f)
    templist = []
    for row in konto_db:
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
    konto_db = templist
    konto_db = sorted(konto_db, key=lambda k: k['Ident'])
    konto_grid_ui.refresh()

def db_konto_speichern():
    db_datei_speichern(db_konto, konto_db)
    button_konto_speichern.disable()
    ui.notify("Kontodaten gespeichert.", type="positive")

def konto_aus_db():
    global konto_db
    konto_db = db_datei_oeffnen(db_konto)
    konto_grid_ui.refresh()

def konto_columns_erstellen(table):
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
                column_element["cellStyle"] = {'backgroundColor': col_cell_mod}
                column_element["cellEditor"] = 'agStringCellEditor'

            columns.append(column_element)

    return columns

@ui.refreshable
def konto_grid_ui():
    global konto_grid
    konto_grid = ui.aggrid({
        'defaultColDef': {
            'editable': False,
            'resizable': True,
            'wrapHeaderText': True,
            'autoHeaderHeight': True,
        },
        'columnDefs': konto_columns_erstellen(konto_db),
        'rowData': konto_db,
        'domLayout': 'autoHeight',
        'pagination': True,
        'paginationPageSize': pagination
    }).on(
        'cellValueChanged',
        lambda event: buchung_tabelle_on_change(event.args)
    ).style('height: 100%')

def buchung_tabelle_on_change(event):
    global konto_grid
    global konto_db
    if event["newValue"] == None:
        return
    # IBAN wird geprüft und nur bei ok eingesetzt. Dazu wird sie mit Leerzeichen formatiert
    if event["colId"] == "IBAN":
        if IBAN(str(event["newValue"]).replace(" ",""), allow_invalid=True).is_valid:
            iban = IBAN(event["newValue"])
            konto_db[int(event["rowId"])][event["colId"]] = iban.formatted
            konto_db[int(event["rowId"])]["BIC"] = iban.bic 
            konto_db[int(event["rowId"])]["Bank"] = iban.bank_name
            konto_grid_ui.refresh()
        else:
            ui.notify('IBAN ist nicht korrekt. Änderung nicht gespeichert.', type="negative")
            konto_grid_ui.refresh()
            return
    else:
        konto_db[int(event["rowId"])][event["colId"]] = event["newValue"]
    button_konto_speichern.enable()
    change_log("KONTODATEN", event)

async def csv_grundgebuehr_speichern():
    await buchung_datei_speichern(csv_grundgebuehr(),'csv_grundgebuehr')

def csv_grundgebuehr():
    konto_aus_db()
    # Änderung für v2: Laden bleibt hier; Exportinhalt unabhängig von der Oberfläche erstellen.
    return grundgebuehr_csv(konto_db, grundgebuehr, betreiber_iban,
                            betreiber_name, betreiber_glaeubigerid)

async def csv_abschlag_speichern():
    if abschlagsjahr_dropdown.value == None or quartal_dropdown.value == None:
        ui.notify('Bitte Abschlagsjahr und Quartal auswählen.', type="info")
        return 
    await buchung_datei_speichern(csv_abschlag(), "csv_abschlag_" + quartal_dropdown.value + "_" + abschlagsjahr_dropdown.value)


def csv_abschlag():
    # Änderung für v2: Laden bleibt hier; Exportinhalt unabhängig von der Oberfläche erstellen.
    return abschlag_csv(konto_db, abschlag_db, abschlagsjahr_dropdown.value,
                        quartal_dropdown.value, betreiber_iban, betreiber_name, betreiber_glaeubigerid)

async def csv_abrechnung_lastschrift_speichern():
    if abrechnungsjahr_dropdown.value == None:
        ui.notify('Bitte Abrechnungsjahr auswählen.', type="info")
        return 
    await buchung_datei_speichern(csv_abrechnung_lastschrift(), "csv_abrechnung_ls_" + abrechnungsjahr_dropdown.value)


def csv_abrechnung_lastschrift():
    datei_abrechnung = ordner_abrechnungen + "\\" + "Abrechnung-" + str(abrechnungsjahr_dropdown.value) + "\\" + "Abrechnung-" + str(abrechnungsjahr_dropdown.value) + ".csv"
    abrechnung = datei_oeffnen(datei_abrechnung)
    # Änderung für v2: Laden bleibt hier; Exportinhalt unabhängig von der Oberfläche erstellen.
    return abrechnung_lastschrift_csv(konto_db, abrechnung, abrechnungsjahr_dropdown.value,
                                      vonnetto_switch.value, betreiber_iban, betreiber_name, betreiber_glaeubigerid)

async def csv_abrechnung_ueberweisung_speichern():
    if abrechnungsjahr_dropdown.value == None:
        ui.notify('Bitte Abrechnungsjahr auswählen.', type="info")
        return 
    await buchung_datei_speichern(csv_abrechnung_ueberweisung(), "csv_abrechnung_üw_" + abrechnungsjahr_dropdown.value)

def csv_abrechnung_ueberweisung():
    datei_abrechnung = ordner_abrechnungen + "\\" + "Abrechnung-" + str(abrechnungsjahr_dropdown.value) + "\\" + "Abrechnung-" + str(abrechnungsjahr_dropdown.value) + ".csv"
    abrechnung = datei_oeffnen(datei_abrechnung)
    # Änderung für v2: Laden bleibt hier; Exportinhalt unabhängig von der Oberfläche erstellen.
    return abrechnung_ueberweisung_csv(konto_db, abrechnung, abrechnungsjahr_dropdown.value,
                                       vonnetto_switch.value, betreiber_iban, betreiber_name)

async def csv_rueckv_speichern():
    if rueckvjahr_dropdown.value == None:
        ui.notify('Bitte Rückvergütungsjahr auswählen.', type="info")
        return 
    await buchung_datei_speichern(csv_rueckv(), "csv_rückvergütung_" + rueckvjahr_dropdown.value)

def csv_rueckv():
    datei_rueckv = ordner_rueckv + "\\" + "Rückvergütung-" + str(rueckvjahr_dropdown.value) + "\\" + "Rückvergütung-" + str(rueckvjahr_dropdown.value) + ".csv"
    rueckv = datei_oeffnen(datei_rueckv)
    # Änderung für v2: Laden bleibt hier; Exportinhalt unabhängig von der Oberfläche erstellen.
    return rueckverguetung_csv(konto_db, rueckv, rueckvjahr_dropdown.value,
                               vonnetto_switch.value, betreiber_iban, betreiber_name)

def dropdowns_einlesen():
    global abschlagsjahr_dropdown
    global abrechnungsjahr_dropdown
    global rueckvjahr_dropdown
    jahrliste = []
    if abschlag_db != []:
        for key in abschlag_db[0].keys():
            if "Abschlag-" in key:
                jahrliste.append(key[-4:])
        jahrliste.sort()
        abschlagsjahr_dropdown.set_options(jahrliste)
    else:
        ui.notify("Abschlag-Datenbank nicht gefüllt.", type="info")
    
    jahrliste = []
    pfad_ordner_abrechnungen = Path(ordner_abrechnungen)
    for item in pfad_ordner_abrechnungen.iterdir():
        if item.is_dir():
            if item.name[:-4] == 'Abrechnung-':
                datei_abrechnung = ordner_abrechnungen + "\\" + item.name + "\\" + "Abrechnung-" + item.name[-4:] + ".csv"
                if Path(datei_abrechnung).is_file():
                    jahrliste.append(item.name[-4:])
    jahrliste.sort()
    if len(jahrliste) == 0:
        ui.notify("Keine Abrechnungen abgespeichert.", type="info")
    abrechnungsjahr_dropdown.set_options(jahrliste)

    jahrliste = []
    pfad_ordner_rueckv = Path(ordner_rueckv)
    for item in pfad_ordner_rueckv.iterdir():
        if item.is_dir():
            if item.name[:-4] == "Rückvergütung-":
                datei_rueckv = ordner_rueckv + "\\" + item.name + "\\" + "Rückvergütung-" + item.name[-4:] + ".csv"
                if Path(datei_rueckv).is_file():
                    jahrliste.append(item.name[-4:])
    jahrliste.sort()
    if len(jahrliste) == 0:
        ui.notify("Keine Rückvergütungen gespeichert.", type="info")
    rueckvjahr_dropdown.set_options(jahrliste)





def buchung_ui():
    global konto_grid
    global abschlagsjahr_dropdown
    global abrechnungsjahr_dropdown
    global quartal_dropdown
    global rueckvjahr_dropdown
    global vonnetto_switch
    global db_konto_found
    global button_konto_speichern
    konto_label_ui('')
    with ui.row():      
        ui.upload(label='Upload Lastschriftvorlage',on_upload=konto_upload, auto_upload=True, max_files=1).props("accept=.csv").classes('max-w-full')
        button_konto_speichern = ui.button('Speichern', icon='save', on_click=lambda: (db_konto_speichern())).props('color=' + speichernbutton)
        button_konto_speichern.disable()
    konto_grid_ui()
    ui.label('Betreiber Name: ' + betreiber_name)
    ui.label('Betreiber IBAN: ' + betreiber_iban)
    ui.label('Betreiber Mandatsreferenz: ' + betreiber_glaeubigerid)
    with ui.row():
        ui.button('CSV Grundgebühr erzeugen', icon='save_alt', on_click=lambda: (csv_grundgebuehr_speichern()))
    with ui.row():
        abschlagsjahr_dropdown = ui.select([], label='Jahr Abschlag').classes('w-48')
        quartal_dropdown = ui.select(['Q1','Q2','Q3','Q4'], label='Quartal').classes('w-48')
    with ui.row():
        ui.button('CSV Abschlag erzeugen', icon='save_alt', on_click=lambda: (csv_abschlag_speichern()))
    with ui.row():
        vonnetto_switch = ui.switch("Abrechnungsbeträge von Netto erzeugen", value=True)
    with ui.row():
        abrechnungsjahr_dropdown = ui.select([], label='Jahr Abrechnung').classes('w-48')
#   with ui.row():
#       ui.button('CSV Lexware Rechnungen für Jahresabrechnung erzeugen', icon='euro').props('color=red-5')
    with ui.row():
        ui.button('CSV Lastschriften für Jahresabrechnung erzeugen', icon='save_alt', on_click=lambda: (csv_abrechnung_lastschrift_speichern()))
        ui.button('CSV Überweisungen für Jahresabrechnung erzeugen', icon='save_alt', on_click=lambda: (csv_abrechnung_ueberweisung_speichern()))
    with ui.row():
        rueckvjahr_dropdown = ui.select([], label='Jahr Rückvergütung').classes('w-48')
#   with ui.row():
#       ui.button('CSV Lexware Rechnungskorrekturen für Rückvergütung erzeugen', icon='euro').props('color=red-5')
    with ui.row():
        ui.button('CSV Überweisungen für Rückvergütung erzeugen', icon='save_alt', on_click=lambda: (csv_rueckv_speichern()))
    if db_datei_oeffnen(db_konto)[0] == "file not found":
        konto_label_ui.refresh('Keine Kontodaten in Datenbank! Upload Kontodaten per CSV-Datei möglich.')
    else:
        db_konto_found = 1
        konto_label_ui.refresh('Kontodaten wurden aus DB geladen. Daten aus Datenbank können über einen neuen Upload überschrieben werden.')
        konto_aus_db()  


###########################################################################################################################
### ENDE KONTOTRANSAKTIONEN
###########################################################################################################################

###########################################################################################################################
### ANFANG TOOLS
###########################################################################################################################


# Globale Variablen für die Ordnerpfade


# Funktion zum Extrahieren der Zahl zwischen zwei '-' im Dateinamen
def extract_numbers(filename):
    """
    Liefert alle 1–2 stelligen Zahlen zwischen '-' im Dateinamen.
    Beispiel: a-12-b-34-c.pdf -> ['12', '34']
    """
    return re.findall(r"-(\d{1,2})-", filename)


# Ordner-Auswahlfunktionen
async def pdfordner1_auswaehlen():
    global pdfordner1_pfad
    ordner_pfad = await app.native.main_window.create_file_dialog(webview.FOLDER_DIALOG)
    if ordner_pfad:
        pdfordner1_pfad = str(ordner_pfad[0])
        label_ordner1.text = pdfordner1_pfad


async def pdfordner2_auswaehlen():
    global pdfordner2_pfad
    ordner_pfad = await app.native.main_window.create_file_dialog(webview.FOLDER_DIALOG)
    if ordner_pfad:
        pdfordner2_pfad = str(ordner_pfad[0])
        label_ordner2.text = pdfordner2_pfad


async def ausgabeordner_auswaehlern():
    global ausgabeordner_pfad
    ordner_pfad = await app.native.main_window.create_file_dialog(webview.FOLDER_DIALOG)
    if ordner_pfad:
        ausgabeordner_pfad = str(ordner_pfad[0])
        label_ausgabe.text = ausgabeordner_pfad


# PDF Merging Funktion mit Fortschrittsanzeige
def pdfjoin(progress):
    log_feld.value = ''  # Logfeld leeren

    if not pdfordner1_pfad or not pdfordner2_pfad or not ausgabeordner_pfad:
        ui.notify("Bitte alle Ordner auswählen!", color="red")
        return

    pdfs1 = [f for f in os.listdir(pdfordner1_pfad) if f.lower().endswith(".pdf")]
    pdfs2 = [f for f in os.listdir(pdfordner2_pfad) if f.lower().endswith(".pdf")]

    # ID → Liste von PDFs aus Ordner 2
    id_to_pdfs2 = {}
    for f in pdfs2:
        nums = extract_numbers(f)
        if len(nums) == 1:
            id_to_pdfs2.setdefault(nums[0], []).append(f)

    count = 0
    total = len(pdfs1)

    # Fortschrittsanzeige sichtbar machen
    progress.classes(remove='invisible')

    for idx, f1 in enumerate(pdfs1, start=1):
        # Fortschritt aktualisieren
        progress.value = int((idx / total) * 100)

        nums1 = extract_numbers(f1)

        # Mehrfach-ID in Ordner 1 → überspringen + ins Log
        if len(nums1) > 1:
            log_feld.value += (
                f"[WARN] Datei übersprungen (mehrere IDs gefunden): {f1} "
                f"IDs: {', '.join(nums1)}\n"
            )
            continue

        if not nums1:
            continue  # keine ID → ignorieren

        num = nums1[0]

        if num not in id_to_pdfs2:
            continue  # kein Pendant → ignorieren

        kandidaten = id_to_pdfs2[num]

        # Mehrere Pendants in Ordner 2 → erste verwenden + Log
        if len(kandidaten) > 1:
            log_feld.value += (
                f"[INFO] Mehrere Pendants für '{f1}': {kandidaten} "
                f"→ verwende '{kandidaten[0]}'\n"
            )

        f2 = kandidaten[0]

        writer = PdfWriter()

        # PDF 1 hinzufügen
        reader1 = PdfReader(os.path.join(pdfordner1_pfad, f1))
        for page in reader1.pages:
            writer.add_page(page)

        # PDF 2 hinzufügen
        reader2 = PdfReader(os.path.join(pdfordner2_pfad, f2))
        for page in reader2.pages:
            writer.add_page(page)

        basisname = os.path.splitext(f1)[0]
        output_path = os.path.join(
            ausgabeordner_pfad,
            f"{basisname}-komplett.pdf"
        )

        with open(output_path, "wb") as out_file:
            writer.write(out_file)

        count += 1

    # Fortschrittsanzeige wieder unsichtbar
#    progress.classes(add='invisible')
    ui.notify(f"{count} PDFs wurden erstellt!", color="green")


# UI
def tools_ui():
    global label_ordner1, label_ordner2, label_ausgabe, log_feld

    BUTTON_WIDTH = "220px"

    with ui.column().style("width: 100%"):
        # Große Überschrift
        ui.label("PDF kombinieren").classes("text-2xl font-bold")

        ui.label(
            'Mit diesem Tool werden PDF-Dateien kombiniert. '
            'Ordner 1 → Ordner 2. '
            'Zuordnung erfolgt über die ID im Dateinamen.'
        )

        with ui.row():
            ui.button(
                "Ordner PDF 1",
                icon='folder',
                on_click=pdfordner1_auswaehlen
            ).props('align=left').style(f"width: {BUTTON_WIDTH}")
            label_ordner1 = ui.label('— kein Ordner gewählt —')

        with ui.row():
            ui.button(
                "Ordner PDF 2",
                icon='folder',
                on_click=pdfordner2_auswaehlen
            ).props('align=left').style(f"width: {BUTTON_WIDTH}")
            label_ordner2 = ui.label('— kein Ordner gewählt —')

        with ui.row():
            ui.button(
                "Ordner Ausgabe",
                icon='folder',
                on_click=ausgabeordner_auswaehlern
            ).props('align=left').style(f"width: {BUTTON_WIDTH}")
            label_ausgabe = ui.label('— kein Ordner gewählt —')

        # Row mit Button + Fortschrittsanzeige
        with ui.row().style("align-items: center; gap: 10px;"):
            pdf_button = ui.button(
                "PDF erstellen",
                icon='picture_as_pdf',
                on_click=lambda: pdfjoin(progress),
                color='red'
            ).props('align=left').style(f"width: {BUTTON_WIDTH}")

            progress = ui.circular_progress(min=0, max=100, value=0, color="black")

        log_feld = ui.textarea(
            label="Hinweise / Mehrfachzuordnungen"
        ).props('readonly rows=6').style(
            "width: 80%; font-family: monospace;"
        )


###########################################################################################################################
### ENDE TOOLS
###########################################################################################################################

###########################################################################################################################
### ANFANG STATISTIK
###########################################################################################################################

# def abnehmer_auslesen():
#     abnehmer_liste = []
#     for row in abnehmer_db:
#         abnehmer_kurz_row = row["Ident"] + " | " + row["Name"] + " " + row["Vorname"]
#         abnehmer_liste.append(abnehmer_kurz_row)
#     return abnehmer_liste


# def dropdown_vergleichswerte_update():
#     vergleichswerte_mapping = {
#         "Abrechnung": ["Mindestvertragssume", "Mindestvertragsleistung", "verbrauchte kWh"],
#         # Weitere Bereiche können hier hinzugefügt werden
#     }
#     print(dropdown_bereich.value)
#     print(vergleichswerte_mapping.get(dropdown_bereich.value, []))
#     dropdown_vergleichswerte.set_options(vergleichswerte_mapping.get(dropdown_bereich.value, []))

# def statistik_ui():
#     with ui.row():
#         ui.select(abnehmer_auslesen(), label='Anschlussnehmer').classes('w-48')
#     with ui.row():
#         global dropdown_bereich, dropdown_vergleichswerte
#         dropdown_bereich = ui.select(['Abrechnung'], label='Bereich', on_change=dropdown_vergleichswerte_update).classes('w-48')
#     with ui.row():
#         dropdown_vergleichswerte = ui.select([], label='Vergleichswert').classes('w-48')
#         dropdown_vergleichswerte_update()  # Initiale Befüllung
#     with ui.row():
#         fig = go.Figure()
#         fig.add_trace(go.Scatter(x=[0, 1, 2, 3, 4], y=[0, 1, 4, 9, 16], mode='lines', name='y = x^2'))
#         ui.plotly(fig)


# -----------------------------------------------------------
# Hilfsfunktionen
# -----------------------------------------------------------

def abnehmer_auslesen():
    abnehmer_liste = []
    for row in abnehmer_db:
        abnehmer_kurz_row = row["Ident"] + " | " + row["Name"] + " " + row["Vorname"]
        abnehmer_liste.append(abnehmer_kurz_row)
    return abnehmer_liste


def dropdown_vergleichswerte_update():
    vergleichswerte_mapping = {
        "Abrechnung": ["Mindestvertragssume", "Mindestvertragsleistung", "verbrauchte kWh"],
    }
    dropdown_vergleichswerte.set_options(vergleichswerte_mapping.get(dropdown_bereich.value, []))
    lade_diagramm()


def lade_diagramm():
    if not dropdown_abnehmer.value or not dropdown_vergleichswerte.value:
        return

    ident = dropdown_abnehmer.value.split(" | ")[0]  # Nur die Ident extrahieren
    spalten_name = dropdown_vergleichswerte.value

    jahre = []
    werte = []

    for eintrag in os.listdir(ordner_abrechnungen):
        if eintrag.startswith("Abrechnung-"):
            jahr = eintrag.split("-")[1]
            csv_datei = os.path.join(ordner_abrechnungen, eintrag, f"Abrechnung-{jahr}.csv")

            if os.path.isfile(csv_datei):
                df = pd.read_csv(csv_datei, sep=';', encoding='cp1252')

                row = df[df["Ident"] == ident]
                if not row.empty and spalten_name in df.columns:
                    jahre.append(int(jahr))
                    werte.append(row[spalten_name].iloc[0])

    zeichne_diagramm(jahre, werte)


def zeichne_diagramm(jahre, werte):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=jahre, y=werte, mode='lines+markers', name='Wertentwicklung'))
    fig.update_layout(xaxis_title="Jahre", yaxis_title="Wert", title="Abrechnungsstatistik")
    plot.update()


# -----------------------------------------------------------
# UI Aufbau
# -----------------------------------------------------------

def statistik_ui():
    global dropdown_abnehmer, dropdown_bereich, dropdown_vergleichswerte, plot

    with ui.row():
        dropdown_abnehmer = ui.select(
            abnehmer_auslesen(),
            label='Anschlussnehmer',
            on_change=lambda _: lade_diagramm()
        ).classes('w-64')

    with ui.row():
        dropdown_bereich = ui.select(
            ['Abrechnung'],
            label='Bereich',
            on_change=dropdown_vergleichswerte_update
        ).classes('w-48')

    with ui.row():
        dropdown_vergleichswerte = ui.select(
            [],
            label='Vergleichswert',
            on_change=lambda _: lade_diagramm()
        ).classes('w-64')
        dropdown_vergleichswerte_update()  # initiale Befüllung

    with ui.row():
        plot = ui.plotly(go.Figure())



###########################################################################################################################
### ENDE STATISTIK
###########################################################################################################################




###########################################################################################################################
### ANFANG CHANGELOG
###########################################################################################################################

def change_log(modul, event):
    current_datetime = datetime.now()
    current_datetime_str = current_datetime.strftime("%d.%m.%Y %H:%M:%S")
    content = f"{event["data"]["Ident"]}" + " " + f"{event["data"]["Name"]}" + " " + f"{event["data"]["Vorname"]}" + " ::: " + f"{event["colId"]}" + " ::: " + f"{event["oldValue"]}" + " ===> " + f"{event["newValue"]}"
    file = open(ordner_logs + "\\" + changelog, "a")
    file.write(current_datetime_str + " | " + modul + " | " + content + "\n")
    file.close()
    changelog_markdown_ui_refresh() 

def change_log_info(modul, info):
    current_datetime = datetime.now()
    current_datetime_str = current_datetime.strftime("%d.%m.%Y %H:%M:%S")
    file = open(ordner_logs + "\\" + changelog, "a")
    file.write(current_datetime_str + " | " + modul + " | " + info + "\n")
    file.close()
    changelog_markdown_ui_refresh() 

def changelog_markdown_ui():
    global changelog_markdown
    global filter_toggle
    with ui.row():
        ui.button('Changelog aktualisieren', icon='refresh', on_click=changelog_markdown_ui_refresh).props('color=secondary')
        filter_toggle = ui.toggle(['ALLE', 'MITGLIEDER','WARTUNG','ABNEHMER','ZÄHLER','ABSCHLAG','RÜCKVERGÜTUNG','KONTODATEN'], value='ALLE', on_change=changelog_markdown_ui_refresh)
    changelog_markdown = ui.markdown('')
    changelog_markdown_ui_refresh()

def changelog_markdown_ui_refresh():
    global changelog_markdown
    content_present = ""
    if Path(ordner_logs + "\\" + changelog).is_file():
        with open(ordner_logs + "\\" + changelog,'r') as datei:
            content = datei.read()
            datei.close()
            if filter_toggle.value == 'ALLE':
                content_present = content 
            else:
                for line in content.split("\n"):
                    if filter_toggle.value in line:
                        content_present = content_present + line + "\n"
            content_present = content_present.replace("\n","  \n")
            changelog_markdown.set_content(content_present)

def changelog_ui():
    changelog_markdown_ui()

###########################################################################################################################
### ENDE CHANGELOG
###########################################################################################################################

###########################################################################################################################
### ANFANG SICHERUNG
###########################################################################################################################

def max_anzahl_ordner(ordner_pfad, max_anzahl=9):
    # Liste der Untererzeichnisse auslesen
    unterverzeichnisse = [subdir for subdir in os.listdir(ordner_pfad) if os.path.isdir(os.path.join(ordner_pfad, subdir))]

    # Unterverzeichnisse werden nach Uhrzeit der Bearbeitung sortiert (neueste zuerst)
    unterverzeichnisse.sort(key=lambda x: os.path.getmtime(os.path.join(ordner_pfad, x)), reverse=True)

    # Überprüfung, ob mehr als max_anzahl Unterverzeichnisse vorhanden sind
    if len(unterverzeichnisse) > max_anzahl:
        # Löschen von allen Ordnern ausser max_anzahl
        ordner_loeschen = unterverzeichnisse[max_anzahl:]
        for ordner in ordner_loeschen:
            shutil.rmtree(os.path.join(ordner_pfad, ordner))

def db_sichern(aktion):
    # Datenbanksicherung soll nur erfolgen, wenn Datenbankordner vorhanden ist
    pfad_ordner = Path(ordner_datenbank)
    if not pfad_ordner.exists():
        return
    current_datetime = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    ordner_sic = os.path.join(ordner_sicherungen, f"{current_datetime} {aktion}")
    pfad_ordner_sic = Path(ordner_sic)
    if not pfad_ordner_sic.exists():
        os.mkdir(ordner_sic)
    max_anzahl_ordner(ordner_sicherungen)
    quellordner = Path(ordner_datenbank)
    zielordner = Path(ordner_sic)
    for item in quellordner.iterdir():
        if item.is_file():
            shutil.copy2(item, zielordner / item.name)
        elif item.is_dir():
            shutil.copytree(item, zielordner / item.name)



###########################################################################################################################
### ENDE SICHERUNG
###########################################################################################################################

def on_tab_change(e):
    if e.value == 'Abrechnungen':
        jahre_abrechnung()
    elif e.value == 'Rückvergütung':
        rueckv_jahre_einlesen()
    elif e.value == 'Buchungsvorlagen':
        dropdowns_einlesen()



def main():

    ### Initiale Checks

    ini_einlesen()

    ### Sicherung bei Programmstart
    db_sichern("Programmstart")



    ### Zentrales GUI
    with ui.header().classes('justify-between border').style('background-color: #FFFFFF; align-items: center'):
        ui.image("./ANA Logo.png").classes('w-32').style('size: (140,80)')
        ui.label("Automatische Nahwärme-Abrechnung").classes('center').style('font-size: 200%; color: #1761A0')
        ui.image('Logo NWS.JPG').classes('w-48')
    with ui.row().classes('w-full'):


    #   ui.label("Programm zur Jahresabrechnung des Wärmeverbrauchs der Nahwaerme Sulzdorf eG").classes('center').style('color: #000000; font-size: 150%; justify-content: center')
        ui.space()
        ui.label("Version: " + str("{:.2f}".format(version)))
        ui.button('', icon='settings', on_click=einstellungen_ui).props('color=dark')
        ui.button('', icon='close', on_click=app.shutdown).props('color=dark')

    with ui.tabs(on_change=on_tab_change).classes('w-full') as tabs:
        tab1 = ui.tab("Mitglieder")
        tab2 = ui.tab('Abnehmerdaten')
        tab3 = ui.tab('Zähler')
        tab4 = ui.tab('Abschlag')
        tab5 = ui.tab('Abrechnungen')
        tab6 = ui.tab('Rückvergütung')
        tab7 = ui.tab('Buchungsvorlagen')
        tab8 = ui.tab('Tools')
#        tab9 = ui.tab('Statistik (BETA)')
        tab10 = ui.tab('Changelog')
    with ui.tab_panels(tabs, value=tab1).classes('w-full'):
        with ui.tab_panel(tab1):
            mitglieder_ui()
        with ui.tab_panel(tab2):
            abnehmer_ui()
        with ui.tab_panel(tab3):
            zaehlerdaten_ui()
        with ui.tab_panel(tab4):
            abschlag_ui()
        with ui.tab_panel(tab5):
            abrechnung_ui()
        with ui.tab_panel(tab6):
            rueckverguetung_ui()
        with ui.tab_panel(tab7):
            buchung_ui()
        with ui.tab_panel(tab8):
            tools_ui()
#        with ui.tab_panel(tab9):
#            statistik_ui()
        with ui.tab_panel(tab10):
            changelog_ui()

    ui.run(reload=False, native=True, window_size=(2048, 1536), title="ANA", favicon="ANA-favicon.ico")


if __name__ == "__main__":
    main()
