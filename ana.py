"""Änderung für v2: Einfacher Programmeinstieg; Oberfläche liegt in anwendung/."""

import multiprocessing
import os
from pathlib import Path

from anwendung.oberflaeche import main


if __name__ == '__main__':
    # Änderung für v2: Bisherigen Python-Befehl und den Start aus anderen Ordnern unterstützen.
    multiprocessing.freeze_support()
    os.chdir(Path(__file__).resolve().parent)
    main()
