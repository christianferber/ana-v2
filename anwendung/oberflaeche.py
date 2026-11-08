# Änderung für v2: In anwendung/ eingeordnet; Modul- und Dateipfade angepasst.

# Mail bei Mitglieder implementieren
# Serienbrief PDF implementieren
# Diagramme für Auswertung implementieren
# Weitere Felder für Anreden bei Serienbrief implementieren

# Änderung für v2: Dateihilfen zentral aus datenhaltung laden; Aufrufe bleiben gleich.
from anwendung.datenhaltung import (check_ordner_exists, datei_oeffnen, datei_speichern,
                         dictlist_to_csv, import_file, import_csv_inhalt)
# Änderung für v2: Arbeitsordnerpfade unabhängig von der Oberfläche erzeugen.
from anwendung.einstellungen import pfade_erstellen, ini_datei_lesen, ini_datei_schreiben
# Änderung 2.03: Abrechnungsansicht mit eigenem Bereichszustand einbinden.
from anwendung.abrechnung_ui import AbrechnungOberflaeche
# Änderung: Abschlagsbereich mit eigenem Bedienzustand einbinden.
# Änderung 2.034: Abnehmeransicht einbinden.
from anwendung.abnehmer_ui import AbnehmerOberflaeche
# Änderung 2.035: Mitgliederansicht mit eigenem Bedienzustand einbinden.
from anwendung.mitglieder_ui import MitgliederOberflaeche
from anwendung.abschlag_ui import AbschlagOberflaeche
# Änderung 2.033: Zählerbereich mit eigenem Bedienzustand einbinden.
from anwendung.zaehler_ui import ZaehlerOberflaeche
# Änderung 2.02: Rückvergütungsansicht mit eigenem Bereichszustand einbinden.
from anwendung.rueckverguetung_ui import RueckverguetungOberflaeche
# Änderung für v2: Dokumentfeldformatierung ohne GUI- und Word-Abhängigkeiten laden.
from anwendung.dokumentfelder import (format_fuer_serienbrief, form_betrag, form_zaehler,
                            form_mwst, form_rvsatz, mapping_wordfelder)

# Änderung für v2: Berechnung und gemeinsame Hilfen ohne GUI-Abhängigkeit laden.
from anwendung.berechnungen import (abrechnung_berechnen, abnehmer_aus_daten, mwst_berechnen,
                           datum_in_string, datum_in_punkt, datum_tage_vorher)
from anwendung.berechnungen import letzte_mindestabnahme as mindestabnahme_berechnen

# Änderung für v2: CSV-Inhalte ohne Oberfläche erzeugen; Speicher- und Eingabedialoge bleiben hier.
from anwendung.buchungsvorlagen import (grundgebuehr_csv, abschlag_csv, abrechnung_lastschrift_csv,
                             abrechnung_ueberweisung_csv, rueckverguetung_csv)
from anwendung.berechnungen import round_half_up

from nicegui import events,app,native,ui
import threading                                                    # Zur Ausführung von Hintergrund-Tasks (z.B. PDF-Generierung)

import time    
time.sleep(0.5)
import csv
from io import StringIO
import re                                                           # für PDF Merger
from pypdf import PdfReader, PdfWriter                              # für PDF Merger
import os
# Änderung für v2: Ressourcen sowohl beim Python-Start als auch neben der EXE finden.
import sys
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

# Änderung für v2: Programmressourcen von Arbeitsdaten getrennt halten.
RESSOURCEN = (Path(sys.executable).resolve().parent if getattr(sys, "frozen", False)
              else Path(__file__).resolve().parents[1]) / "ressourcen"

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
# Änderung 2.03: Neue Freigabe für die ausgelagerte Abrechnungsoberfläche.
# Änderung: Versionsschritt um 0.001 gemäß aktueller AGENTS.md.
# Änderung: Neue Quellfreigabe für die bereinigte Teststeuerung.
# Änderung: Versionsschritt gemäß Freigabeprozess.
# Änderung 2.034: Abnehmerauslagerung kennzeichnen.
# Änderung 2.035: Auslagerung der Mitgliederoberfläche kennzeichnen.
version = 2.035
zaehler_liste = []
# Änderung 2.03: Abrechnungsdaten werden in AbrechnungOberflaeche initialisiert.
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

# Änderung 2.035: Aufrufe und refresh-Zugriffe über bisherige Einstiegspunkte erhalten.
@ui.refreshable
def mitglieder_label_ui(label):
    return mitglieder_ansicht.mitglieder_label_ui(label)

def dialog_wartung():
    return mitglieder_ansicht.dialog_wartung()

def anschluss_aendern():
    return mitglieder_ansicht.anschluss_aendern()

def mitglieder_neu():
    return mitglieder_ansicht.mitglieder_neu()

def dialog_mitglieder_editieren():
    return mitglieder_ansicht.dialog_mitglieder_editieren()

def dialog_mitglieder_loeschen():
    return mitglieder_ansicht.dialog_mitglieder_loeschen()

def duplikate_zusammensetzen(mitglieder_tabelle):
    return mitglieder_ansicht.duplikate_zusammensetzen(mitglieder_tabelle)

def mitglieder_grid_update():
    return mitglieder_ansicht.mitglieder_grid_update()

async def editiermodus_aendern():
    return await mitglieder_ansicht.editiermodus_aendern()

def edit_aktivieren(event):
    return mitglieder_ansicht.edit_aktivieren(event)

def mitglieder_upload(e: events.UploadEventArguments):
    return mitglieder_ansicht.mitglieder_upload(e)

def mitglieder_aus_db():
    return mitglieder_ansicht.mitglieder_aus_db()

def mitglieder_speichern():
    return mitglieder_ansicht.mitglieder_speichern()

def mitglieder_pruefen():
    return mitglieder_ansicht.mitglieder_pruefen()

def disable_row_splitting(table):
    return mitglieder_ansicht.disable_row_splitting(table)

def mitglieder_ja_word_erstellen(dateiname):
    return mitglieder_ansicht.mitglieder_ja_word_erstellen(dateiname)

def mitglieder_gv_word_erstellen(dateiname, datum, ort):
    return mitglieder_ansicht.mitglieder_gv_word_erstellen(dateiname, datum, ort)

def mitglieder_word_process(quelle, dateiname, datum, ort):
    return mitglieder_ansicht.mitglieder_word_process(quelle, dateiname, datum, ort)

async def mitglieder_word_download():
    return await mitglieder_ansicht.mitglieder_word_download()

def mitglieder_csv_download():
    return mitglieder_ansicht.mitglieder_csv_download()

def serienbrief_dialog():
    return mitglieder_ansicht.serienbrief_dialog()

def mitglieder_ui():
    global mitglieder_ansicht
    mitglieder_ansicht = MitgliederOberflaeche(sys.modules[__name__])
    return mitglieder_ansicht.mitglieder_ui()



###########################################################################################################################
### ENDE MITGLIEDER
###########################################################################################################################


###########################################################################################################################
### ANFANG ABNEHMER / BASISDATEN
###########################################################################################################################

# Änderung 2.034: Bestehende Aufrufe und refresh-Zugriffe erhalten.
@ui.refreshable
def abnehmer_label_ui(label):
    return abnehmer_ansicht.abnehmer_label_ui(label)

def abnehmer_upload(e: events.UploadEventArguments):
    return abnehmer_ansicht.abnehmer_upload(e)

def abnehmer_aus_db():
    return abnehmer_ansicht.abnehmer_aus_db()

def abnehmerdaten_speichern():
    return abnehmer_ansicht.abnehmerdaten_speichern()

def abnehmer_tabelle_on_change(event):
    return abnehmer_ansicht.abnehmer_tabelle_on_change(event)

def abnehmer_columns_erstellen(table):
    return abnehmer_ansicht.abnehmer_columns_erstellen(table)

@ui.refreshable
def abnehmer_grid_ui():
    return abnehmer_ansicht.abnehmer_grid_ui()

def abnehmer_ui():
    global abnehmer_ansicht
    abnehmer_ansicht = AbnehmerOberflaeche(sys.modules[__name__])
    return abnehmer_ansicht.abnehmer_ui()


###########################################################################################################################
### ENDE ABNEHMER / BASISDATEN
###########################################################################################################################


###########################################################################################################################
### ANFANG ZÄHLER
###########################################################################################################################

# Änderung 2.033: Bestehende Aufrufe und refresh-Zugriffe über Adapter erhalten.
@ui.refreshable
def zaehler_label_ui(label):
    return zaehler_ansicht.zaehler_label_ui(label)

def import_zaehler_liste(zaehler_liste):
    return zaehler_ansicht.import_zaehler_liste(zaehler_liste)

def import_zaehlerdaten_visu(csvinput):
    return zaehler_ansicht.import_zaehlerdaten_visu(csvinput)

def zaehler_aus_db():
    return zaehler_ansicht.zaehler_aus_db()

def zaehler_liste_upload(e: events.UploadEventArguments):
    return zaehler_ansicht.zaehler_liste_upload(e)

def zaehler_sortieren():
    return zaehler_ansicht.zaehler_sortieren()

def check_zaehlerdaten():
    return zaehler_ansicht.check_zaehlerdaten()

def zaehler_speichern():
    return zaehler_ansicht.zaehler_speichern()

def dialog_zaehlerstand_uebernehmen():
    return zaehler_ansicht.dialog_zaehlerstand_uebernehmen()

def zaehler_tabelle_on_change(event):
    return zaehler_ansicht.zaehler_tabelle_on_change(event)

def zaehler_columns_erstellen(table):
    return zaehler_ansicht.zaehler_columns_erstellen(table)

@ui.refreshable
def zaehler_grid_ui():
    return zaehler_ansicht.zaehler_grid_ui()

def zaehlerdaten_ui():
    global zaehler_ansicht
    zaehler_ansicht = ZaehlerOberflaeche(sys.modules[__name__])
    return zaehler_ansicht.zaehlerdaten_ui()


    

###########################################################################################################################
### ENDE ZÄHLER
###########################################################################################################################

###########################################################################################################################
### ANFANG ABRECHNUNG
###########################################################################################################################


### Liest aus den Zählerdaten die verfügbaren Jahre aus.

# Änderung 2.03: Bereichsansicht erzeugen und Jahresauswahl weiter anbinden.
def abrechnung_ui():
    global abrechnung_ansicht
    abrechnung_ansicht = AbrechnungOberflaeche(sys.modules[__name__])
    abrechnung_ansicht.abrechnung_ui()


def jahre_abrechnung():
    abrechnung_ansicht.jahre_abrechnung()


###########################################################################################################################
### ENDE ABRECHNUNG
########################################################################################################################### 

###########################################################################################################################
### ANFANG ABSCHLAG
###########################################################################################################################

# Änderung: Bestehende Aufrufe und refresh-Zugriffe bleiben über kleine Adapter erhalten.
@ui.refreshable
def abschlag_label_ui(label):
    return abschlag_ansicht.abschlag_label_ui(label)

def abschlag_aus_db():
    return abschlag_ansicht.abschlag_aus_db()

def abschlag_upload(e: events.UploadEventArguments):
    return abschlag_ansicht.abschlag_upload(e)

def abschlag_speichern():
    return abschlag_ansicht.abschlag_speichern()

def abschlag_tabelle_on_change(event):
    return abschlag_ansicht.abschlag_tabelle_on_change(event)

def abschlag_columns_erstellen(table):
    return abschlag_ansicht.abschlag_columns_erstellen(table)

@ui.refreshable
def abschlag_grid_ui():
    return abschlag_ansicht.abschlag_grid_ui()

def abschlag_ui():
    global abschlag_ansicht
    abschlag_ansicht = AbschlagOberflaeche(sys.modules[__name__])
    return abschlag_ansicht.abschlag_ui()



###########################################################################################################################
### ENDE ABSCHLAG
###########################################################################################################################


###########################################################################################################################
### ANFANG RÜCKVERGÜTUNG
###########################################################################################################################

# Änderung 2.02: Nur die beiden Einstiegspunkte bleiben im Hauptmodul.
# Der Bereich besitzt seinen eigenen Zustand; gemeinsame Einstellungen bleiben aktuell.
def rueckverguetung_ui():
    global rueckverguetung_ansicht
    rueckverguetung_ansicht = RueckverguetungOberflaeche(sys.modules[__name__])
    rueckverguetung_ansicht.rueckverguetung_ui()


def rueckv_jahre_einlesen():
    rueckverguetung_ansicht.rueckv_jahre_einlesen()


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
        ui.image(str(RESSOURCEN / "ANA logo.png")).classes('w-32').style('size: (140,80)')
        ui.label("Automatische Nahwärme-Abrechnung").classes('center').style('font-size: 200%; color: #1761A0')
        ui.image(str(RESSOURCEN / 'Logo NWS.JPG')).classes('w-48')
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

    ui.run(reload=False, native=True, window_size=(2048, 1536), title="ANA", favicon=str(RESSOURCEN / "ANA-favicon.ico"))


if __name__ == "__main__":
    main()
