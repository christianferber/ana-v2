# Änderung für v2: In scripts/ eingeordnet; Modul- und Dateipfade angepasst.
"""Änderung für v2: Ein Windows-Paket ohne lokale Einstellungen oder Testdaten erstellen."""

import ast
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    basis = Path(__file__).resolve().parents[1]
    # Änderung für v2: Strukturtests in einem separaten Zielordner bauen, ohne Releases zu überschreiben.
    parser = argparse.ArgumentParser(description='ANA als kompaktes Windows-Paket erstellen')
    parser.add_argument('--ausgabe', type=Path, default=basis)
    ziel = parser.parse_args().ausgabe.resolve()
    # Änderung für v2: Versionsnummer aus dem Programm übernehmen.
    baum = ast.parse((basis / 'anwendung' / 'oberflaeche.py').read_text(encoding='utf-8'))
    version = next(k.value.value for k in baum.body if isinstance(k, ast.Assign)
                   and any(isinstance(ziel, ast.Name) and ziel.id == 'version' for ziel in k.targets))
    # Änderung 2.05.01: Buildnummer im Paketnamen erhalten, ältere Quellen weiterhin unterstützen.
    paket_version = next((k.value.value for k in baum.body if isinstance(k, ast.Assign)
                          and any(isinstance(name, ast.Name) and name.id == 'build_version'
                                  for name in k.targets)), format(version, '.2f'))
    # Änderung für v2: Nur Programm- und Bibliotheksressourcen einbinden, keine Fachdaten.
    # Änderung 2.06.00: Freigabeprozess 7 verlangt eingebettete Laufzeitdateien in einer Onefile-EXE.
    befehl = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onefile', '--windowed',
              '--name', 'ANA', '--distpath', str(ziel / 'dist'), '--workpath', str(ziel / 'build'),
              '--specpath', str(ziel / 'build'), '--icon', str(basis / 'ressourcen' / 'ANA-icon.ico'),
              '--collect-all', 'nicegui', '--collect-all', 'webview',
              '--hidden-import', 'pythoncom', '--hidden-import', 'win32com.client',
              str(basis / 'ana_start.py')]
    subprocess.run(befehl, cwd=basis, check=True)
    release = ziel / 'release'
    release.mkdir(exist_ok=True)
    archiv = release / ('ANA-' + paket_version + '-Windows-x64')
    # Änderung 2.06.00: Frisches Paket enthält nur EXE, Release Notes, Ressourcen und neutrale INI.
    # Eigene temporäre Dateien verhindern Altbestände aus früheren Ordner-Builds.
    with tempfile.TemporaryDirectory(prefix='paket-', dir=ziel / 'build') as temp:
        assert Path(temp).resolve().is_relative_to((ziel / 'build').resolve())
        ausgabe = Path(temp) / 'ANA'
        ausgabe.mkdir()
        shutil.copy2(ziel / 'dist' / 'ANA.exe', ausgabe / 'ANA.exe')
        shutil.copytree(basis / 'ressourcen', ausgabe / 'ressourcen')
        shutil.copy2(basis / 'RELEASE_NOTES.md', ausgabe / 'RELEASE_NOTES.md')
        shutil.copy2(basis / 'konfiguration' / 'ana.example.ini', ausgabe / 'ana.ini')
        shutil.make_archive(str(archiv), 'zip', root_dir=temp, base_dir='ANA')
    print('Windows-Paket erstellt: ' + archiv.name + '.zip')


if __name__ == '__main__':
    main()
