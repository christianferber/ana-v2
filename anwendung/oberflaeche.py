# Änderung 2.044: Bisherige Namen durch direkte Importe der unveränderten Hilfen erhalten.
from anwendung.datenaufbereitung import (string_in_dict, listcsv_to_dict, jahr_in_datum,
                                         tablefields_to_dotfloat, tablefields_to_int)
# Änderung für v2: In anwendung/ eingeordnet; Modul- und Dateipfade angepasst.

# Mail bei Mitglieder implementieren
# Serienbrief PDF implementieren
# Diagramme für Auswertung implementieren
# Weitere Felder für Anreden bei Serienbrief implementieren

# Änderung für v2: Dateihilfen zentral aus datenhaltung laden; Aufrufe bleiben gleich.
from anwendung.datenhaltung import (DatenbankZugriff, check_ordner_exists, datei_oeffnen, datei_speichern,
                         dictlist_to_csv, import_file, import_csv_inhalt)
# Änderung für v2: Arbeitsordnerpfade unabhängig von der Oberfläche erzeugen.
from anwendung.einstellungen import pfade_erstellen, ini_datei_lesen, ini_datei_schreiben
# Änderung 2.03: Abrechnungsansicht mit eigenem Bereichszustand einbinden.
from anwendung.abrechnung_ui import AbrechnungOberflaeche
# Änderung: Abschlagsbereich mit eigenem Bedienzustand einbinden.
# Änderung 2.034: Abnehmeransicht einbinden.
from anwendung.abnehmer_ui import AbnehmerOberflaeche
# Änderung 2.036: Kontodatenansicht einbinden.
from anwendung.kontodaten_ui import KontodatenOberflaeche
# Änderung 2.037: Werkzeugeansicht einbinden.
from anwendung.werkzeuge_ui import WerkzeugeOberflaeche
# Änderung 2.038: Einstellungsansicht einbinden.
from anwendung.einstellungen_ui import EinstellungenOberflaeche
# Änderung 2.039: Changelog-Ansicht einbinden.
from anwendung.changelog_ui import ChangelogOberflaeche
# Änderung 2.040: Statistikansicht einbinden; Register bleibt deaktiviert.
from anwendung.statistik_ui import StatistikOberflaeche
# Änderung 2.041: Buchungsexport-Bedienabläufe einbinden.
from anwendung.buchungsexport_ui import BuchungsexportOberflaeche
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
# Änderung 2.046: Gemeinsame Exporthilfe vor dem Ansichtsaufbau bereitstellen.
from anwendung.exporthilfe import ExportHilfe
exporthilfe = ExportHilfe(sys.modules[__name__])
# Änderung 2.045: Datenbankzugriffe vor dem Ansichtsaufbau bereitstellen.
datenhaltung_hilfe = DatenbankZugriff(sys.modules[__name__])
# Änderung 2.043: Gemeinsame Hilfen vor dem Aufbau der Ansichten bereitstellen.
from anwendung.sicherung import Sicherung
from anwendung.protokollierung import Protokollierung
sicherung_hilfe = Sicherung(sys.modules[__name__])
protokollierung_hilfe = Protokollierung(sys.modules[__name__])
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

# Änderung 2.041: Bedienhilfe ohne UI-Start an aktuelle gemeinsame Daten anbinden.
buchungsexport_ansicht = BuchungsexportOberflaeche(sys.modules[__name__])

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
# Änderung 2.036: Kontodatenauslagerung kennzeichnen.
# Änderung 2.037: Werkzeugeauslagerung kennzeichnen.
# Änderung 2.038: Einstellungsauslagerung kennzeichnen.
# Änderung 2.039: Changelog-Auslagerung kennzeichnen.
# Änderung 2.040: Statistikauslagerung kennzeichnen.
# Änderung 2.041: Buchungsexport-Auslagerung kennzeichnen.
# Änderung 2.042: Erneute Auslagerung erst nach vollständig erfolgreicher regulärer Prüfung freigeben.
# Änderung 2.043: Gemeinsame Sicherungs- und Protokollhilfen auslagern.
# Änderung 2.044: Gemeinsame Datenaufbereitung auslagern.
# Änderung 2.045: Datenbankzugriffe auslagern.
# Änderung 2.046: Gemeinsame CSV-Speicherhilfe auslagern.
# Änderung 2.049: Geprüfte UI-Modernisierung und angepasste Startanzeige veröffentlichen.
version = 2.049
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
    

# Änderung 2.038: Bestehenden Einstiegspunkt der Einstellungen erhalten.
def einstellungen_ui():
    global einstellungen_ansicht
    einstellungen_ansicht = EinstellungenOberflaeche(sys.modules[__name__])
    return einstellungen_ansicht.einstellungen_ui()

# Änderung 2.038: Bestehenden Einstiegspunkt der Einstellungen erhalten.
def ordner_standard():
    return einstellungen_ansicht.ordner_standard()

# Änderung 2.038: Bestehenden Einstiegspunkt der Einstellungen erhalten.
async def ordner_auswaehlen():
    return await einstellungen_ansicht.ordner_auswaehlen()

# Änderung 2.038: Bestehenden Einstiegspunkt der Einstellungen erhalten.
def ini_speichern():
    return einstellungen_ansicht.ini_speichern()


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

# Änderung 2.045: Bestehenden Datenbankaufruf weitergeben.
def db_datei_oeffnen(dbfile):
    return datenhaltung_hilfe.db_datei_oeffnen(dbfile)

# Änderung für v2: datei_oeffnen ist unverändert in datenhaltung.py ausgelagert.

# Änderung 2.045: Bestehenden Datenbankaufruf weitergeben.
def db_datei_speichern(dbfile, csvdict):
    return datenhaltung_hilfe.db_datei_speichern(dbfile, csvdict)


# Änderung für v2: datei_speichern ist unverändert in datenhaltung.py ausgelagert.


# Änderung für v2: dictlist_to_csv ist unverändert in datenhaltung.py ausgelagert.

# Änderung: Ungenutzte Textumwandlungshilfen entfernt; aktive Textverarbeitung bleibt unverändert.

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



# Änderung für v2: import_file ist unverändert in datenhaltung.py ausgelagert.

# Änderung für v2: import_csv_inhalt ist unverändert in datenhaltung.py ausgelagert.


### Wandelt Format dd.mm.yyyy um in yyyymmdd

# Änderung: Ungenutzte Datumshilfe entfernt; importierte Datumsfunktionen bleiben erhalten.

# Änderung für v2: datum_in_string unverändert aus berechnungen importiert.

### Wandelt Datum JJJJ-MM-TT und in TT.MM.JJJJ

# Änderung für v2: datum_in_punkt unverändert aus berechnungen importiert.

### Liest Jahr aus Datumsstring aus



### Zieht Tage x von Datum ab und speichert Datum im Format YYYY-MM-DD

# Änderung für v2: datum_tage_vorher unverändert aus berechnungen importiert.


# Änderung 2.047: Bisherigen Einstiegspunkt der Mitgliederaktualisierung erhalten.
def dbs_mitglieder_aktualisieren():
    return datenhaltung_hilfe.dbs_mitglieder_aktualisieren()


# Tabellenfelder werden als floats markiert, wenn Zahlen enthalten sind. Ansonsten kann man Tabellenzellen im Grid nicht mit numerischen Werten anpassen




# Änderung: Ungenutzte Einzelfeldhilfe entfernt; tablefields_to_int bleibt unverändert.

# Änderung für v2: Die sechs unveränderten Formatierungsfunktionen liegen in dokumentfelder.py.


# Änderung 2.046: Bestehenden asynchronen Einstiegspunkt erhalten.
async def komma_datei_speichern(dictlist, dateiname):
    return await exporthilfe.komma_datei_speichern(dictlist, dateiname)
    
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

# Änderung 2.036: Bestehenden Einstiegspunkt für die Kontodatenansicht erhalten.
@ui.refreshable
def konto_label_ui(label):
    return kontodaten_ansicht.konto_label_ui(label)

# Änderung 2.041: Bestehenden Export-Einstiegspunkt erhalten.
async def buchung_datei_speichern(content, dateiprefix):
    return await buchungsexport_ansicht.buchung_datei_speichern(content, dateiprefix)

# Änderung 2.036: Bestehenden Einstiegspunkt für die Kontodatenansicht erhalten.
def konto_upload(e: events.UploadEventArguments):
    return kontodaten_ansicht.konto_upload(e)

# Änderung 2.036: Bestehenden Einstiegspunkt für die Kontodatenansicht erhalten.
def db_konto_speichern():
    return kontodaten_ansicht.db_konto_speichern()

# Änderung 2.036: Bestehenden Einstiegspunkt für die Kontodatenansicht erhalten.
def konto_aus_db():
    return kontodaten_ansicht.konto_aus_db()

# Änderung 2.036: Bestehenden Einstiegspunkt für die Kontodatenansicht erhalten.
def konto_columns_erstellen(table):
    return kontodaten_ansicht.konto_columns_erstellen(table)

# Änderung 2.036: Bestehenden Einstiegspunkt für die Kontodatenansicht erhalten.
@ui.refreshable
def konto_grid_ui():
    return kontodaten_ansicht.konto_grid_ui()

# Änderung 2.036: Bestehenden Einstiegspunkt für die Kontodatenansicht erhalten.
def buchung_tabelle_on_change(event):
    return kontodaten_ansicht.buchung_tabelle_on_change(event)

# Änderung 2.041: Bestehenden Export-Einstiegspunkt erhalten.
async def csv_grundgebuehr_speichern():
    return await buchungsexport_ansicht.csv_grundgebuehr_speichern()

def csv_grundgebuehr():
    konto_aus_db()
    # Änderung für v2: Laden bleibt hier; Exportinhalt unabhängig von der Oberfläche erstellen.
    return grundgebuehr_csv(konto_db, grundgebuehr, betreiber_iban,
                            betreiber_name, betreiber_glaeubigerid)

# Änderung 2.041: Bestehenden Export-Einstiegspunkt erhalten.
async def csv_abschlag_speichern():
    return await buchungsexport_ansicht.csv_abschlag_speichern()


def csv_abschlag():
    # Änderung für v2: Laden bleibt hier; Exportinhalt unabhängig von der Oberfläche erstellen.
    return abschlag_csv(konto_db, abschlag_db, abschlagsjahr_dropdown.value,
                        quartal_dropdown.value, betreiber_iban, betreiber_name, betreiber_glaeubigerid)

# Änderung 2.041: Bestehenden Export-Einstiegspunkt erhalten.
async def csv_abrechnung_lastschrift_speichern():
    return await buchungsexport_ansicht.csv_abrechnung_lastschrift_speichern()


def csv_abrechnung_lastschrift():
    datei_abrechnung = ordner_abrechnungen + "\\" + "Abrechnung-" + str(abrechnungsjahr_dropdown.value) + "\\" + "Abrechnung-" + str(abrechnungsjahr_dropdown.value) + ".csv"
    abrechnung = datei_oeffnen(datei_abrechnung)
    # Änderung für v2: Laden bleibt hier; Exportinhalt unabhängig von der Oberfläche erstellen.
    return abrechnung_lastschrift_csv(konto_db, abrechnung, abrechnungsjahr_dropdown.value,
                                      vonnetto_switch.value, betreiber_iban, betreiber_name, betreiber_glaeubigerid)

# Änderung 2.041: Bestehenden Export-Einstiegspunkt erhalten.
async def csv_abrechnung_ueberweisung_speichern():
    return await buchungsexport_ansicht.csv_abrechnung_ueberweisung_speichern()

def csv_abrechnung_ueberweisung():
    datei_abrechnung = ordner_abrechnungen + "\\" + "Abrechnung-" + str(abrechnungsjahr_dropdown.value) + "\\" + "Abrechnung-" + str(abrechnungsjahr_dropdown.value) + ".csv"
    abrechnung = datei_oeffnen(datei_abrechnung)
    # Änderung für v2: Laden bleibt hier; Exportinhalt unabhängig von der Oberfläche erstellen.
    return abrechnung_ueberweisung_csv(konto_db, abrechnung, abrechnungsjahr_dropdown.value,
                                       vonnetto_switch.value, betreiber_iban, betreiber_name)

# Änderung 2.041: Bestehenden Export-Einstiegspunkt erhalten.
async def csv_rueckv_speichern():
    return await buchungsexport_ansicht.csv_rueckv_speichern()

def csv_rueckv():
    datei_rueckv = ordner_rueckv + "\\" + "Rückvergütung-" + str(rueckvjahr_dropdown.value) + "\\" + "Rückvergütung-" + str(rueckvjahr_dropdown.value) + ".csv"
    rueckv = datei_oeffnen(datei_rueckv)
    # Änderung für v2: Laden bleibt hier; Exportinhalt unabhängig von der Oberfläche erstellen.
    return rueckverguetung_csv(konto_db, rueckv, rueckvjahr_dropdown.value,
                               vonnetto_switch.value, betreiber_iban, betreiber_name)

# Änderung 2.041: Bestehenden Export-Einstiegspunkt erhalten.
def dropdowns_einlesen():
    return buchungsexport_ansicht.dropdowns_einlesen()





# Änderung 2.036: Bestehenden Einstiegspunkt für die Kontodatenansicht erhalten.
def buchung_ui():
    global kontodaten_ansicht
    kontodaten_ansicht = KontodatenOberflaeche(sys.modules[__name__])
    return kontodaten_ansicht.buchung_ui()


###########################################################################################################################
### ENDE KONTOTRANSAKTIONEN
###########################################################################################################################

###########################################################################################################################
### ANFANG TOOLS
###########################################################################################################################


# Globale Variablen für die Ordnerpfade


# Funktion zum Extrahieren der Zahl zwischen zwei '-' im Dateinamen
# Änderung 2.037: Bestehenden Einstiegspunkt der Werkzeuge erhalten.
def extract_numbers(filename):
    return werkzeuge_ansicht.extract_numbers(filename)


# Ordner-Auswahlfunktionen
# Änderung 2.037: Bestehenden Einstiegspunkt der Werkzeuge erhalten.
async def pdfordner1_auswaehlen():
    return await werkzeuge_ansicht.pdfordner1_auswaehlen()


# Änderung 2.037: Bestehenden Einstiegspunkt der Werkzeuge erhalten.
async def pdfordner2_auswaehlen():
    return await werkzeuge_ansicht.pdfordner2_auswaehlen()


# Änderung 2.037: Bestehenden Einstiegspunkt der Werkzeuge erhalten.
async def ausgabeordner_auswaehlern():
    return await werkzeuge_ansicht.ausgabeordner_auswaehlern()


# PDF Merging Funktion mit Fortschrittsanzeige
# Änderung 2.037: Bestehenden Einstiegspunkt der Werkzeuge erhalten.
def pdfjoin(progress):
    return werkzeuge_ansicht.pdfjoin(progress)


# UI
# Änderung 2.037: Bestehenden Einstiegspunkt der Werkzeuge erhalten.
def tools_ui():
    global werkzeuge_ansicht
    werkzeuge_ansicht = WerkzeugeOberflaeche(sys.modules[__name__])
    return werkzeuge_ansicht.tools_ui()


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

# Änderung 2.040: Bestehenden Statistikeinstieg ohne Aktivierung erhalten.
def abnehmer_auslesen():
    return statistik_ansicht.abnehmer_auslesen()


# Änderung 2.040: Bestehenden Statistikeinstieg ohne Aktivierung erhalten.
def dropdown_vergleichswerte_update():
    return statistik_ansicht.dropdown_vergleichswerte_update()


# Änderung 2.040: Bestehenden Statistikeinstieg ohne Aktivierung erhalten.
def lade_diagramm():
    return statistik_ansicht.lade_diagramm()


# Änderung 2.040: Bestehenden Statistikeinstieg ohne Aktivierung erhalten.
def zeichne_diagramm(jahre, werte):
    return statistik_ansicht.zeichne_diagramm(jahre, werte)


# -----------------------------------------------------------
# UI Aufbau
# -----------------------------------------------------------

# Änderung 2.040: Bestehenden Statistikeinstieg ohne Aktivierung erhalten.
def statistik_ui():
    global statistik_ansicht
    statistik_ansicht = StatistikOberflaeche(sys.modules[__name__])
    return statistik_ansicht.statistik_ui()



###########################################################################################################################
### ENDE STATISTIK
###########################################################################################################################




###########################################################################################################################
### ANFANG CHANGELOG
###########################################################################################################################

# Änderung 2.043: Bestehenden Aufruf an die gemeinsame Hilfe weitergeben.
def change_log(modul, event):
    return protokollierung_hilfe.change_log(modul, event)

# Änderung 2.043: Bestehenden Aufruf an die gemeinsame Hilfe weitergeben.
def change_log_info(modul, info):
    return protokollierung_hilfe.change_log_info(modul, info)

# Änderung 2.039: Bestehenden Einstiegspunkt der Changelog-Anzeige erhalten.
def changelog_markdown_ui():
    return changelog_ansicht.changelog_markdown_ui()

# Änderung 2.039: Bestehenden Einstiegspunkt der Changelog-Anzeige erhalten.
def changelog_markdown_ui_refresh():
    return changelog_ansicht.changelog_markdown_ui_refresh()

# Änderung 2.039: Bestehenden Einstiegspunkt der Changelog-Anzeige erhalten.
def changelog_ui():
    global changelog_ansicht
    changelog_ansicht = ChangelogOberflaeche(sys.modules[__name__])
    return changelog_ansicht.changelog_ui()

###########################################################################################################################
### ENDE CHANGELOG
###########################################################################################################################

###########################################################################################################################
### ANFANG SICHERUNG
###########################################################################################################################

# Änderung 2.043: Bestehenden Aufruf an die gemeinsame Hilfe weitergeben.
def max_anzahl_ordner(ordner_pfad, max_anzahl=9):
    return sicherung_hilfe.max_anzahl_ordner(ordner_pfad, max_anzahl)

# Änderung 2.043: Bestehenden Aufruf an die gemeinsame Hilfe weitergeben.
def db_sichern(aktion):
    return sicherung_hilfe.db_sichern(aktion)



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



    # Änderung 2.049: Nur den gemeinsamen Rahmen gestalten; Tabellen und Editieraufrufe bleiben unverändert.
    ui.colors(primary='#1761a0', secondary='#526879')
    ui.add_css((RESSOURCEN / 'ana-ui.css').read_text(encoding='utf-8'))

    # Änderung 2.049: Dieselben Register in einer einklappbaren Seitenleiste verwenden.
    with ui.left_drawer(bordered=True).props('width=220 breakpoint=900').classes('ana-sidebar') as navigation:
        # Änderung 2.049: Produktname nur in der Kopfzeile zeigen.
        with ui.tabs(on_change=on_tab_change).props('vertical no-caps').classes('ana-nav w-full') as tabs:
            ui.label('Stammdaten').classes('ana-nav-section')
            tab1 = ui.tab("Mitglieder", icon='groups')
            tab2 = ui.tab('Abnehmerdaten', icon='home_work')
            tab3 = ui.tab('Zähler', icon='speed')
            tab4 = ui.tab('Abschlag', icon='payments')
            ui.label('Abrechnung').classes('ana-nav-section')
            tab5 = ui.tab('Abrechnungen', icon='receipt_long')
            tab6 = ui.tab('Rückvergütung', icon='savings')
            tab7 = ui.tab('Buchungsvorlagen', icon='table_view')
            ui.label('Programm').classes('ana-nav-section')
            tab8 = ui.tab('Tools', icon='build')
            tab10 = ui.tab('Changelog', icon='history')
        ui.separator().classes('my-4')
        # Änderung 2.049: Icon und Text an den übrigen Navigationseinträgen ausrichten.
        ui.button('Einstellungen', icon='settings', on_click=einstellungen_ui).props('flat no-caps').classes('w-full ana-settings')
        # Änderung 2.049: Die bisherige Versionsformatierung unverändert übernehmen.
        ui.label("Version: " + str("{:.2f}".format(version))).classes('ana-sidebar-version')

    with ui.header().classes('ana-header'):
        with ui.row().classes('ana-header-row'):
            # Änderung 2.049: Für breite Tabellen die Navigation jederzeit aus-/einblenden können.
            ui.button(icon='menu', on_click=navigation.toggle).props('flat round aria-label="Navigation ein-/ausblenden"').tooltip('Navigation ein-/ausblenden')
            ui.image(str(RESSOURCEN / "ANA logo.png")).classes('ana-header-logo')
            ui.label("Automatische Nahwärme-Abrechnung").classes('ana-header-title')
            ui.space()
            # Änderung 2.049: Rechtes Logo vergrößern; Einstellungen ausschließlich links anbieten.
            ui.image(str(RESSOURCEN / 'Logo NWS.JPG')).classes('ana-header-logo ana-header-partner-logo')
            ui.button('', icon='close', on_click=app.shutdown).props('flat round aria-label="Programm beenden"').tooltip('Programm beenden')

    # Änderung 2.049: Keep-alive, Startregister und alle Panel-/Funktionsbindungen ausdrücklich erhalten.
    with ui.tab_panels(tabs, value=tab1, keep_alive=True).classes('ana-workspace'):
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
