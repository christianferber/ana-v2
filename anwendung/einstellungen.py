# Änderung für v2: In anwendung/ eingeordnet; Modul- und Dateipfade angepasst.
"""Änderung für v2: Arbeitsordnerpfade ohne Abhängigkeit von der Oberfläche bilden."""

import configparser
from pathlib import Path


def datenordner_anlegen(ini_datei, programmordner):
    # Änderung nach 2.06.00: Fehlende Datenordner ausschließlich am konfigurierten Ort anlegen.
    arbeitsordner = ''
    if Path(ini_datei).is_file():
        config = ini_datei_lesen(ini_datei)
        arbeitsordner = config.get('Anwendung', 'Arbeitsordner', fallback='')
    basis = Path(programmordner).resolve()
    ziel = Path(arbeitsordner) if arbeitsordner.strip() else basis
    if not ziel.is_absolute():
        ziel = basis / ziel
    # Änderung: Bestehende Pfaddefinitionen wiederverwenden, vorhandene Verzeichnisse überspringen.
    for name, pfad in pfade_erstellen(str(ziel)).items():
        if name == 'arbeitsordner':
            continue
        ordner = Path(pfad)
        if not ordner.is_dir():
            ordner.mkdir(parents=True, exist_ok=True)


def ini_datei_lesen(datei):
    # Änderung für v2: Bisherigen UTF-8-Lesezugriff zentral bereitstellen.
    config = configparser.ConfigParser()
    with open(datei, 'r', encoding='utf-8') as f:
        config.read_file(f)
    return config


def ini_datei_schreiben(datei, config):
    # Änderung für v2: ConfigParser und bisherige Schreibparameter beibehalten.
    with open(datei, 'w', encoding='utf-8') as configfile:
        config.write(configfile)


def pfade_erstellen(arbeitsordner):
    # Änderung für v2: Bisherige Pfadbildung aus pfade_setzen übernehmen.
    # Absichtlich keine Normalisierung: Auch relative Pfade bleiben wie bisher.
    if arbeitsordner == "":
        arbeitsordner = "."
    ordner_abrechnungen = str(arbeitsordner) + "\\Abrechnungen"
    ordner_rueckv = str(arbeitsordner) + "\\Rückvergütungen"
    ordner_logs = str(arbeitsordner) + "\\Logs"
    ordner_datenbank = str(arbeitsordner) + "\\Datenbank"
    ordner_sicherungen = str(arbeitsordner) + "\\Sicherungen"
    ordner_downloads = str(arbeitsordner) + "\\Downloads"
    ordner_vorlagen = str(arbeitsordner) + "\\Vorlagen"

    # Änderung für v2: Werte zurückgeben, statt globale Variablen zu verändern.
    return {
        'arbeitsordner': arbeitsordner,
        'ordner_abrechnungen': ordner_abrechnungen,
        'ordner_rueckv': ordner_rueckv,
        'ordner_logs': ordner_logs,
        'ordner_datenbank': ordner_datenbank,
        'ordner_sicherungen': ordner_sicherungen,
        'ordner_downloads': ordner_downloads,
        'ordner_vorlagen': ordner_vorlagen,
    }
