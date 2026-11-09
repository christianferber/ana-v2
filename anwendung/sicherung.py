"""Änderung 2.043: Gemeinsame Sicherung mit unverändertem Verhalten."""
import os
import shutil
import tempfile
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
        # Änderung: Gleiche Sekunde und Aktion dürfen keine vorhandene Sicherung überschreiben.
        zielordner = Path(ordner_sic)
        nummer = 1
        while zielordner.exists():
            zielordner = Path(ordner_sic + ' (' + str(nummer) + ')')
            nummer += 1
        # Änderung: Unvollständige Kopien erst nach Erfolg als fertige Sicherung bereitstellen.
        temp = Path(tempfile.mkdtemp(prefix='.ana-', dir=self.anwendung.ordner_sicherungen))
        try:
            for item in pfad_ordner.iterdir():
                if item.is_file():
                    shutil.copy2(item, temp / item.name)
                elif item.is_dir():
                    shutil.copytree(item, temp / item.name)
            temp.rename(zielordner)
        finally:
            if temp.exists():
                shutil.rmtree(temp)
        # Änderung: Alte vollständige Sicherungen erst nach erfolgreicher neuer Kopie löschen.
        self.anwendung.max_anzahl_ordner(self.anwendung.ordner_sicherungen)
