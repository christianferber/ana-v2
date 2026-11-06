"""Änderung: ANA-Tests einzeln starten und sämtliche Unterprozesse schließen."""
import hashlib
import json
import re
from pathlib import Path
import subprocess
import time

import win32api
import win32event
import win32job


def prozessliste():
    # Änderung: Befehlszeilen nur lokal auswerten, niemals ausgeben.
    befehl = '[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(); Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,CommandLine,ExecutablePath | ConvertTo-Json -Compress'
    ergebnis = subprocess.run(['powershell', '-NoProfile', '-Command', befehl],
                              capture_output=True, text=True, encoding='utf-8', check=True,
                              creationflags=subprocess.CREATE_NO_WINDOW)
    return json.loads(ergebnis.stdout) or []


def ana_prozesse(basis):
    # Änderung: Verwaiste Fenster zusätzlich über die lokalen Test-PID-Dateien zuordnen.
    eltern = set()
    for datei in (basis / '.lokal').glob('oberflaechentest-*/app.pid'):
        eltern.add(int(datei.read_text()))
    gefunden = []
    for prozess in prozessliste():
        name = (prozess['Name'] or '').lower()
        befehl = (prozess['CommandLine'] or '').lower()
        pfad = (prozess['ExecutablePath'] or '').lower()
        python = name in ('python.exe', 'pythonw.exe')
        test = python and 'tests.oberflaeche_pruefen' in befehl and '--app' in befehl
        fenster = python and 'multiprocessing.spawn' in befehl and prozess['ParentProcessId'] in eltern
        direkt = python and (any(str(basis / datei).lower() in befehl for datei in ('ana.py', 'ana_start.py'))
                             or re.search(r'(?:^|[\s\"])ana(?:_start)?\.py(?:[\"\s]|$)', befehl) is not None)
        exe = name == 'ana.exe' and pfad.startswith(str(basis).lower() + '\\')
        if test or fenster or direkt or exe:
            gefunden.append(prozess['ProcessId'])
    return gefunden


class TestProzesse:
    # Änderung: Betriebssystem-Sperre verhindert zwei gleichzeitige Testläufe.
    def __init__(self, basis):
        self.basis = Path(basis).resolve()
        self.sperre = None
        self.job = None
        self.prozesse = []

    def __enter__(self):
        name = 'Local\\ANA-Test-' + hashlib.sha256(str(self.basis).lower().encode()).hexdigest()[:20]
        self.sperre = win32event.CreateMutex(None, False, name)
        status = win32event.WaitForSingleObject(self.sperre, 0)
        if status not in (win32event.WAIT_OBJECT_0, win32event.WAIT_ABANDONED):
            self.sperre.Close()
            self.sperre = None
            raise RuntimeError('Es läuft bereits ein ANA-Test; kein weiterer Start.')
        try:
            # Änderung: Vor jedem Start vorhandene ANA-Instanzen vollständig beenden.
            for pid in ana_prozesse(self.basis):
                subprocess.run(['taskkill', '/PID', str(pid), '/T', '/F'],
                               capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if ana_prozesse(self.basis):
                raise RuntimeError('Vorhandene ANA-Instanz konnte nicht beendet werden.')
            # Änderung: Ein Windows-Job umfasst App, Fenster, Browser und weitere Kinder.
            self.job = win32job.CreateJobObject(None, '')
            info = win32job.QueryInformationJobObject(self.job, win32job.JobObjectExtendedLimitInformation)
            info['BasicLimitInformation']['LimitFlags'] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            win32job.SetInformationJobObject(self.job, win32job.JobObjectExtendedLimitInformation, info)
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def starten(self, argumente, **optionen):
        # Änderung: Jeden gestarteten Prozess sofort dem gemeinsamen Job zuordnen.
        prozess = subprocess.Popen(argumente, **optionen)
        try:
            handle = win32api.OpenProcess(0x0100 | 0x0001, False, prozess.pid)
            try:
                win32job.AssignProcessToJobObject(self.job, handle)
            finally:
                handle.Close()
        except BaseException:
            subprocess.run(['taskkill', '/PID', str(prozess.pid), '/T', '/F'], capture_output=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
            prozess.wait(timeout=30)
            raise
        self.prozesse.append(prozess)
        return prozess

    def __exit__(self, typ, wert, traceback):
        try:
            if self.job is not None:
                # Änderung: Auch nach Erfolg, Fehler und Abbruch den gesamten Job beenden.
                win32job.TerminateJobObject(self.job, 1)
                try:
                    for _ in range(100):
                        info = win32job.QueryInformationJobObject(self.job, win32job.JobObjectBasicAccountingInformation)
                        if info['ActiveProcesses'] == 0:
                            break
                        time.sleep(.1)
                    else:
                        raise RuntimeError('Test-Unterprozesse wurden nicht vollständig beendet.')
                    for prozess in self.prozesse:
                        prozess.wait(timeout=30)
                finally:
                    self.job.Close()
                    self.job = None
        finally:
            if self.sperre is not None:
                win32event.ReleaseMutex(self.sperre)
                self.sperre.Close()
                self.sperre = None


