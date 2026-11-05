# Änderung für v2: In scripts/ eingeordnet; Modul- und Dateipfade angepasst.
"""Änderung für v2: Ein Windows-Paket ohne lokale Einstellungen oder Testdaten erstellen."""

import ast
import argparse
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    basis = Path(__file__).resolve().parents[1]
    # Änderung für v2: Strukturtests in einem separaten Zielordner bauen, ohne Releases zu überschreiben.
    parser = argparse.ArgumentParser(description='ANA als Windows-Ordnerpaket erstellen')
    parser.add_argument('--ausgabe', type=Path, default=basis)
    ziel = parser.parse_args().ausgabe.resolve()
    # Änderung für v2: Versionsnummer aus dem Programm übernehmen.
    baum = ast.parse((basis / 'anwendung' / 'oberflaeche.py').read_text(encoding='utf-8'))
    version = next(k.value.value for k in baum.body if isinstance(k, ast.Assign)
                   and any(isinstance(ziel, ast.Name) and ziel.id == 'version' for ziel in k.targets))
    # Änderung für v2: Nur Programm- und Bibliotheksressourcen einbinden, keine Fachdaten.
    befehl = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onedir', '--windowed',
              '--name', 'ANA', '--distpath', str(ziel / 'dist'), '--workpath', str(ziel / 'build'),
              '--specpath', str(ziel / 'build'), '--icon', str(basis / 'ressourcen' / 'ANA-icon.ico'),
              '--collect-all', 'nicegui', '--collect-all', 'webview',
              '--hidden-import', 'pythoncom', '--hidden-import', 'win32com.client',
              str(basis / 'ana_start.py')]
    subprocess.run(befehl, cwd=basis, check=True)
    ausgabe = ziel / 'dist' / 'ANA'
    # Änderung für v2: Ausschließlich freigegebene Programmressourcen kopieren.
    # Änderung für v2: Die neue Ressourcengliederung auch im Windows-Paket beibehalten.
    shutil.copytree(basis / 'ressourcen', ausgabe / 'ressourcen', dirs_exist_ok=True)
    # Änderung für v2: Die im Handbuch verlinkte Dokumentation auch im Windows-Paket bereitstellen.
    shutil.copytree(basis / 'docs', ausgabe / 'docs', dirs_exist_ok=True)
    for name in ('README.md', 'RELEASE_NOTES.md'):
        shutil.copy2(basis / name, ausgabe / name)
    shutil.copy2(basis / 'konfiguration' / 'ana.example.ini', ausgabe / 'ana.ini')
    # Änderung für v2: Leere Standardordner für einen ersten Start ohne Daten bereitstellen.
    for name in ('Datenbank', 'Sicherungen', 'Logs', 'Downloads', 'Abrechnungen',
                 'Rückvergütungen', 'Vorlagen'):
        (ausgabe / name).mkdir(exist_ok=True)
    release = ziel / 'release'
    release.mkdir(exist_ok=True)
    archiv = release / ('ANA-' + format(version, '.2f') + '-Windows-x64')
    shutil.make_archive(str(archiv), 'zip', root_dir=ziel / 'dist', base_dir='ANA')
    print('Windows-Paket erstellt: ' + archiv.name + '.zip')


if __name__ == '__main__':
    main()
