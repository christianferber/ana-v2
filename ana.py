"""Änderung für v2: Einfacher Programmeinstieg; Oberfläche liegt in anwendung/."""

import multiprocessing
import os
from pathlib import Path

# Änderung: Die Startanzeige vor den großen Oberflächenbibliotheken laden.
from anwendung.startanzeige import Startanzeige


def main():
    # Änderung: Anzeige und Fachanwendung laufen in derselben App-Instanz.
    with Startanzeige() as startanzeige:
        from anwendung.oberflaeche import main as oberflaeche_starten
        from nicegui import app

        startanzeige.status(55, 'Oberfläche wird vorbereitet …')
        app.on_startup(lambda: startanzeige.status(85, 'Anwendungsfenster wird geöffnet …'))
        app.on_connect(startanzeige.bereit)
        oberflaeche_starten()


if __name__ == '__main__':
    # Änderung für v2: Bisherigen Python-Befehl und den Start aus anderen Ordnern unterstützen.
    multiprocessing.freeze_support()
    os.chdir(Path(__file__).resolve().parent)
    main()
