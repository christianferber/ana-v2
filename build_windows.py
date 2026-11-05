"""Änderung für v2: Ein Windows-Paket ohne lokale Einstellungen oder Testdaten erstellen."""

import ast
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    basis = Path(__file__).resolve().parent
    # Änderung für v2: Versionsnummer aus dem Programm übernehmen.
    baum = ast.parse((basis / 'ana.py').read_text(encoding='utf-8'))
    version = next(k.value.value for k in baum.body if isinstance(k, ast.Assign)
                   and any(isinstance(ziel, ast.Name) and ziel.id == 'version' for ziel in k.targets))
    # Änderung für v2: Nur Programm- und Bibliotheksressourcen einbinden, keine Fachdaten.
    befehl = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onedir', '--windowed',
              '--name', 'ANA', '--distpath', str(basis / 'dist'), '--workpath', str(basis / 'build'),
              '--specpath', str(basis / 'build'), '--icon', str(basis / 'ANA-icon.ico'),
              '--collect-all', 'nicegui', '--collect-all', 'webview',
              '--hidden-import', 'pythoncom', '--hidden-import', 'win32com.client',
              str(basis / 'ana_start.py')]
    subprocess.run(befehl, cwd=basis, check=True)
    ausgabe = basis / 'dist' / 'ANA'
    # Änderung für v2: Ausschließlich freigegebene Programmressourcen kopieren.
    for name in ('ANA logo.png', 'Logo NWS.JPG', 'ANA-favicon.ico', 'ANA-icon.ico',
                 'README.md', 'RELEASE_NOTES.md'):
        shutil.copy2(basis / name, ausgabe / name)
    shutil.copy2(basis / 'ana.example.ini', ausgabe / 'ana.ini')
    # Änderung für v2: Leere Standardordner für einen ersten Start ohne Daten bereitstellen.
    for name in ('Datenbank', 'Sicherungen', 'Logs', 'Downloads', 'Abrechnungen',
                 'Rückvergütungen', 'Vorlagen'):
        (ausgabe / name).mkdir(exist_ok=True)
    release = basis / 'release'
    release.mkdir(exist_ok=True)
    archiv = release / ('ANA-' + format(version, '.2f') + '-Windows-x64')
    shutil.make_archive(str(archiv), 'zip', root_dir=basis / 'dist', base_dir='ANA')
    print('Windows-Paket erstellt: ' + archiv.name + '.zip')


if __name__ == '__main__':
    main()
