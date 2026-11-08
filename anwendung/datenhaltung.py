# Änderung für v2: In anwendung/ eingeordnet; Modul- und Dateipfade angepasst.
"""Änderung für v2: CSV- und Dateihilfen unverändert aus ana.py ausgelagert."""

import csv
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


def datei_speichern(file, csvdict):
    csvstring = dictlist_to_csv(csvdict)
    fileobject = open(file, "w")
    fileobject.write(csvstring)
    fileobject.close()


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
        # Überprüfen, ob die Unterordner vorhanden sind und anlegen, wenn nicht
        self.anwendung.check_ordner_exists(self.anwendung.ordner_abrechnungen)
        self.anwendung.check_ordner_exists(self.anwendung.ordner_rueckv)
        self.anwendung.check_ordner_exists(self.anwendung.ordner_logs)
        self.anwendung.check_ordner_exists(self.anwendung.ordner_datenbank)
        self.anwendung.check_ordner_exists(self.anwendung.ordner_sicherungen)
        self.anwendung.check_ordner_exists(self.anwendung.ordner_downloads)
        csvstring = self.anwendung.dictlist_to_csv(csvdict)
        dbfile = self.anwendung.ordner_datenbank + "\\" + dbfile
        dbfileobject = open(dbfile, "w")
        dbfileobject.write(csvstring)
        dbfileobject.close()
