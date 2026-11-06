"""Änderung: Echte Windows-Unterprozesse und Testsperre ohne Fachdaten prüfen."""
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import win32api
import win32event

from tests.testprozesse import TestProzesse, ana_prozesse


def beendet(pid, wartezeit=0):
    try:
        handle = win32api.OpenProcess(0x00100000, False, pid)
    except Exception as fehler:
        if getattr(fehler, 'winerror', None) == 87:
            return True
        raise
    try:
        return win32event.WaitForSingleObject(handle, wartezeit) == win32event.WAIT_OBJECT_0
    finally:
        handle.Close()


def pruefen():
    basis = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(dir=basis / '.lokal') as tmp:
        for fehlerfall in (False, True):
            piddatei = Path(tmp) / ('kind-' + str(fehlerfall))
            kindcode = 'import os,time; from pathlib import Path; Path(' + repr(str(piddatei)) + ').write_text(str(os.getpid())); time.sleep(120)'
            # Änderung: Der Elternprozess endet selbst; sein Kind muss trotzdem im Job bleiben.
            elterncode = 'import subprocess,sys,time; time.sleep(.5); subprocess.Popen([sys.executable,"-c",' + repr(kindcode) + '])'
            try:
                with TestProzesse(basis) as gruppe:
                    eltern = gruppe.starten([sys.executable, '-c', elterncode], creationflags=subprocess.CREATE_NO_WINDOW)
                    eltern.wait(timeout=20)
                    for _ in range(100):
                        if piddatei.is_file():
                            break
                        time.sleep(.1)
                    kindpid = int(piddatei.read_text())
                    assert not beendet(kindpid)
                    # Änderung: Ein zweiter Python-Prozess darf keinen weiteren Test starten.
                    sperrtest = ('from pathlib import Path; from tests.testprozesse import TestProzesse; '
                                 'g=TestProzesse(Path.cwd()); '
                                 '\ntry: g.__enter__()\nexcept RuntimeError: raise SystemExit(0)\nelse: g.__exit__(None,None,None); raise SystemExit(1)')
                    assert subprocess.run([sys.executable, '-c', sperrtest], cwd=basis, capture_output=True,
                                          creationflags=subprocess.CREATE_NO_WINDOW).returncode == 0
                    if fehlerfall:
                        raise ValueError('simulierter Testfehler')
            except ValueError:
                assert fehlerfall
            assert beendet(eltern.pid, 5000) and beendet(kindpid, 5000)
    assert not ana_prozesse(basis)


if __name__ == '__main__':
    try:
        pruefen()
        print('Testsperre und vollständiges Beenden verwaister Unterprozesse bei Erfolg und Fehler: bestanden.')
    except Exception as fehler:
        print('Prozessprüfung nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)

