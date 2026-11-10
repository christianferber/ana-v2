# Änderung für v2: In anwendung/ eingeordnet; Modul- und Dateipfade angepasst.
"""Änderung für v2: CSV- und Dateihilfen unverändert aus ana.py ausgelagert."""
# Änderung: Änderungsprotokoll ergänzen; vorhandene Fachlogik unverändert ausführen.
from anwendung.aenderungsprotokoll import aenderungen_protokollieren

import csv
import os
import tempfile
from pathlib import Path


# Änderung für v2: Die folgenden Funktionskörper entsprechen der Ausgangsversion.
def check_ordner_exists(ordner):
    pfad_ordner = Path(ordner)
    if not pfad_ordner.exists():
        pfad_ordner.mkdir()


def datei_oeffnen(file):
    filepath = Path(file)
    dictionary_temp_list = []
    if filepath.is_file():
        with open(file) as csvdatei:
            csv_reader_object = csv.DictReader(csvdatei, delimiter=';')
            for row in csv_reader_object:
                dictionary_temp_list.append(row)
    else:
        dictionary_temp_list.append("file not found")
    return dictionary_temp_list


def text_sicher_speichern(file, inhalt):
    # Änderung: Erst im Zielordner vollständig schreiben, dann die Zieldatei atomar ersetzen.
    ziel = Path(file)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=ziel.parent,
                                         prefix='.ana-', suffix='.tmp', delete=False) as datei:
            temp = Path(datei.name)
            datei.write(inhalt)
            datei.flush()
            os.fsync(datei.fileno())
        os.replace(temp, ziel)
    finally:
        # Änderung: Bei Schreib- oder Austauschfehlern bleibt die alte Datei erhalten.
        if temp is not None and temp.exists():
            temp.unlink()


def datei_speichern(file, csvdict):
    csvstring = dictlist_to_csv(csvdict)
    # Änderung: CSV-Aufbereitung und Format beibehalten, nur den Schreibzugriff absichern.
    text_sicher_speichern(file, csvstring)


def dictlist_to_csv(dictlistinput):
    for row in dictlistinput:
        for key,value in row.items():
            row[key] = str(value).replace('\n', '\\n').strip()
    csv_header = ';'.join(dictlistinput[0].keys())
    csv_rows = ""
    for row in dictlistinput:
        row_as_csv = ';'.join(row.values())
        csv_rows = csv_rows + row_as_csv + '\n'
    csv_string = csv_header + '\n' + csv_rows
    return csv_string


def import_file(filetoimport):
    imported_file = []
    file = open(str(filetoimport), "r")
    content = file.read()
    imported_file = content.split("\n")
    file.close()
    return imported_file


def import_csv_inhalt(csvinput):
    dictionary_temp_list = []
    csv_reader_object = csv.DictReader(csvinput, delimiter=';')
    for row in csv_reader_object:
            dictionary_temp_list.append(row)
    return dictionary_temp_list


class DatenbankZugriff:
    # Änderung 2.045: Pfade und Dateihilfen dynamisch von der Anwendung lesen.
    def __init__(self, anwendung):
        self.anwendung = anwendung

    # Änderung 2.045: Bisherigen Zugriff mit aktuellen Anwendungspfaden erhalten.
    def db_datei_oeffnen(self, dbfile):
        dbfilepath = Path(self.anwendung.ordner_datenbank + "\\" + dbfile)
        dictionary_temp_list = []
        if dbfilepath.is_file():
            with open(self.anwendung.ordner_datenbank + "\\" + dbfile) as csvdatei:
                csv_reader_object = csv.DictReader(csvdatei, delimiter=';')
                for row in csv_reader_object:
                    dictionary_temp_list.append(row)
        else:
            dictionary_temp_list.append("file not found")
        return dictionary_temp_list

    # Änderung 2.045: Bisherigen Zugriff mit aktuellen Anwendungspfaden erhalten.
    def db_datei_speichern(self, dbfile, csvdict):
        # Änderung: Tatsächliche Daten-/Dateiänderungen zusätzlich protokollieren.
        with aenderungen_protokollieren(
            self.anwendung, 'DATENBANK', 'Datenbank speichern',
            daten=lambda: {},
            dateien=lambda: (Path(self.anwendung.ordner_datenbank) / dbfile,),
        ):
            # Überprüfen, ob die Unterordner vorhanden sind und anlegen, wenn nicht
            self.anwendung.check_ordner_exists(self.anwendung.ordner_abrechnungen)
            self.anwendung.check_ordner_exists(self.anwendung.ordner_rueckv)
            self.anwendung.check_ordner_exists(self.anwendung.ordner_logs)
            self.anwendung.check_ordner_exists(self.anwendung.ordner_datenbank)
            self.anwendung.check_ordner_exists(self.anwendung.ordner_sicherungen)
            self.anwendung.check_ordner_exists(self.anwendung.ordner_downloads)
            csvstring = self.anwendung.dictlist_to_csv(csvdict)
            dbfile = self.anwendung.ordner_datenbank + "\\" + dbfile
            # Änderung: Bestehende Datenbank erst nach vollständigem Schreiben ersetzen.
            text_sicher_speichern(dbfile, csvstring)

    # Änderung 2.047: Namenaktualisierung mit bisheriger Speicher-/Ladereihenfolge übernehmen.
    def dbs_mitglieder_aktualisieren(self):
        # Änderung: Tatsächliche Daten-/Dateiänderungen zusätzlich protokollieren.
        with aenderungen_protokollieren(
            self.anwendung, 'MITGLIEDERABGLEICH', 'Mitgliedernamen in abhängigen Datenbeständen aktualisieren',
            daten=lambda: {'Abnehmer': self.anwendung.abnehmer_db, 'Zähler': self.anwendung.zaehler_db, 'Abschläge': self.anwendung.abschlag_db, 'Kontodaten': self.anwendung.konto_db},
        ):
            if self.anwendung.abnehmer_db != []:
                for row in self.anwendung.abnehmer_db:
                    for mitglied in self.anwendung.mitglieder_db:
                        if row["Ident"] == mitglied["Ident"]:
                            row["Name"] = mitglied["Name"]
                            row["Vorname"] = mitglied["Vorname"]
            if (self.anwendung.db_abnehmer_found == 1):
                self.anwendung.db_datei_speichern(self.anwendung.db_abnehmer, self.anwendung.abnehmer_db)
                self.anwendung.abnehmer_aus_db()
            if self.anwendung.zaehler_db != []:
                for row in self.anwendung.zaehler_db:
                    for mitglied in self.anwendung.mitglieder_db:
                        if row["Ident"] == mitglied["Ident"]:
                            row["Name"] = mitglied["Name"]
                            row["Vorname"] = mitglied["Vorname"]
            if (self.anwendung.db_zaehler_found == 1):
                self.anwendung.db_datei_speichern(self.anwendung.db_zaehler, self.anwendung.zaehler_db)
                self.anwendung.zaehler_aus_db()
            if self.anwendung.abschlag_db != []:
                for row in self.anwendung.abschlag_db:
                    for mitglied in self.anwendung.mitglieder_db:
                        if row["Ident"] == mitglied["Ident"]:
                            row["Name"] = mitglied["Name"]
                            row["Vorname"] = mitglied["Vorname"]
            if (self.anwendung.db_abschlag_found == 1):
                self.anwendung.db_datei_speichern(self.anwendung.db_abschlag, self.anwendung.abschlag_db)
                self.anwendung.abschlag_aus_db()
            if self.anwendung.konto_db != []:
                for row in self.anwendung.konto_db:
                    for mitglied in self.anwendung.mitglieder_db:
                        if row["Ident"] == mitglied["Ident"]:
                            row["Name"] = mitglied["Name"]
                            row["Vorname"] = mitglied["Vorname"]
            if (self.anwendung.db_konto_found == 1):
                self.anwendung.db_datei_speichern(self.anwendung.db_konto, self.anwendung.konto_db)
                self.anwendung.konto_aus_db()
