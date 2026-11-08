"""Änderung 2.043: Gemeinsame Sicherung mit unverändertem Verhalten."""
import os
import shutil
from pathlib import Path
from datetime import datetime


class Sicherung:
    # Änderung: Aktuelle Pfade über die übergebene Anwendung lesen.
    def __init__(self, anwendung):
        self.anwendung = anwendung

    # Änderung 2.043: Bisherigen Ablauf mit aktuellen Anwendungswerten erhalten.
    def max_anzahl_ordner(self, ordner_pfad, max_anzahl=9):
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


    # Änderung 2.043: Bisherigen Ablauf mit aktuellen Anwendungswerten erhalten.
    def db_sichern(self, aktion):
        # Datenbanksicherung soll nur erfolgen, wenn Datenbankordner vorhanden ist
        pfad_ordner = Path(self.anwendung.ordner_datenbank)
        if not pfad_ordner.exists():
            return
        current_datetime = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        ordner_sic = os.path.join(self.anwendung.ordner_sicherungen, f"{current_datetime} {aktion}")
        pfad_ordner_sic = Path(ordner_sic)
        if not pfad_ordner_sic.exists():
            os.mkdir(ordner_sic)
        self.anwendung.max_anzahl_ordner(self.anwendung.ordner_sicherungen)
        quellordner = Path(self.anwendung.ordner_datenbank)
        zielordner = Path(ordner_sic)
        for item in quellordner.iterdir():
            if item.is_file():
                shutil.copy2(item, zielordner / item.name)
            elif item.is_dir():
                shutil.copytree(item, zielordner / item.name)
