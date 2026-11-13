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
    # Änderung nach 2.06.00: Gemeinsamer Start legt Ordner anhand der INI am richtigen Ort an.
    from ana import main
    main()
