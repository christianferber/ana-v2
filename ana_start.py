"""Änderung für v2: Windows-Pakete unabhängig vom Aufrufverzeichnis starten."""

import multiprocessing
import os
from pathlib import Path
import sys


if __name__ == '__main__':
    # Änderung für v2: Native Fenster und Hintergrundprozesse in der EXE unterstützen.
    multiprocessing.freeze_support()
    # Änderung für v2: Logos und Konfiguration neben der EXE beziehungsweise diesem Skript suchen.
    ordner = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
    os.chdir(ordner)
    # Änderung 2.06.00: Die früher mitgelieferten leeren Datenordner erst beim EXE-Start anlegen.
    # Damit enthält die Freigabe ausschließlich die in AGENTS.md Schritt 7 erlaubten Dateien.
    if getattr(sys, 'frozen', False):
        for name in ('Datenbank', 'Sicherungen', 'Logs', 'Downloads', 'Abrechnungen',
                     'Rückvergütungen', 'Vorlagen'):
            (ordner / name).mkdir(exist_ok=True)
    from ana import main
    main()
