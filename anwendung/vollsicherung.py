"""Änderung nach 2.05.00: Vollständige lokale ZIP-Sicherung und INI-Einstellungen."""
from datetime import datetime, timedelta
from pathlib import Path
import os
import re
import tempfile
import hashlib
import json
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile, ZipInfo

from anwendung.einstellungen import ini_datei_lesen


# Änderung: Nur eindeutig eigene Archive werden bei der Aufbewahrung berücksichtigt.
ARCHIVNAME = re.compile(r'ANA-Vollsicherung-\d{8}-\d{6}-\d{6}\.zip\Z')
PROJEKTORDNER = {'.git', '.lokal', '.agents', '.codex', '__pycache__', 'build', 'dist', 'release'}
# Änderung: Ein gemeinsamer Status für den gesamten Komprimierungs- und Sicherungsvorgang.
FORTSCHRITT_TEXT = 'Daten werden komprimiert und gesichert …'


def einstellungen_lesen(ini):
    # Änderung: Alte INIs bleiben gültig; automatische Sicherung ist zunächst aus.
    config = ini_datei_lesen(ini)
    werte = config['Sicherung'] if config.has_section('Sicherung') else {}
    try:
        wochen = int(werte.get('AufbewahrungWochen', '12'))
        if not 1 <= wochen <= 520:
            raise ValueError
        automatisch = str(werte.get('BeiProgrammende', 'nein')).lower() in ('ja', 'yes', 'true', '1')
        aufraeumen = str(werte.get('Aufraeumen', 'nein')).lower() in ('ja', 'yes', 'true', '1')
    except ValueError:
        raise ValueError('Die Aufbewahrung muss zwischen 1 und 520 ganzen Wochen liegen.') from None
    return dict(ordner=werte.get('Ordner', ''), automatisch=automatisch,
                aufraeumen=aufraeumen, wochen=wochen)


def einstellungen_pruefen(werte, arbeitsordner):
    # Änderung: Vor dem Speichern und Sichern verständliche Eingabefehler abfangen.
    zahl = float(werte['wochen'])
    if not zahl.is_integer() or not 1 <= zahl <= 520:
        raise ValueError('Die Aufbewahrung muss zwischen 1 und 520 ganzen Wochen liegen.')
    if not werte['ordner'].strip():
        if werte['automatisch']:
            raise ValueError('Bitte einen Sicherungsordner auswählen.')
        return
    ziel = Path(werte['ordner']).expanduser()
    if not ziel.is_absolute():
        raise ValueError('Bitte einen vollständigen Sicherungsordner auswählen.')
    if ziel.resolve() == Path(arbeitsordner).resolve():
        raise ValueError('Arbeitsordner und Sicherungsordner müssen verschieden sein.')
    # Änderung: Die unveränderte alte Datenbanksicherung rotiert Unterordner von „Sicherungen“.
    # ZIPs direkt darin sind sicher; darunterliegende Zielordner könnten sonst gelöscht werden.
    bisherige_sicherungen = Path(arbeitsordner).resolve() / 'Sicherungen'
    if ziel.resolve() != bisherige_sicherungen and ziel.resolve().is_relative_to(bisherige_sicherungen):
        raise ValueError('Bitte „Sicherungen“ direkt oder einen Ordner außerhalb davon wählen. Unterordner werden von der bisherigen Datenbanksicherung aufgeräumt.')
    if ziel.exists() and not ziel.is_dir():
        raise ValueError('Das Sicherungsziel muss ein Ordner sein.')


def dateiliste(quelle, ziel):
    # Änderung: Keine Verknüpfungen verfolgen und keine Sicherung in sich selbst aufnehmen.
    dateien = []
    def fehler_melden(fehler):
        raise fehler
    for ordner, unterordner, namen in os.walk(quelle, onerror=fehler_melden):
        basis = Path(ordner)
        behalten = []
        for name in sorted(unterordner):
            pfad = basis / name
            if pfad.resolve() == ziel or name in PROJEKTORDNER:
                continue
            if pfad.is_symlink() or pfad.is_junction():
                raise ValueError('Der Arbeitsordner enthält eine Ordnerverknüpfung. Bitte diese vor der Sicherung prüfen.')
            behalten.append(name)
        unterordner[:] = behalten
        # Änderung: Auch leere Datenordner müssen wiederherstellbar bleiben.
        dateien.append((basis, 0, None))
        for name in sorted(namen):
            pfad = basis / name
            if ARCHIVNAME.fullmatch(name) or name.startswith('.ana-vollsicherung-'):
                continue
            if pfad.is_symlink():
                raise ValueError('Der Arbeitsordner enthält eine Dateiverknüpfung. Bitte diese vor der Sicherung prüfen.')
            status = pfad.stat()
            dateien.append((pfad, status.st_size, status.st_mtime_ns))
    return dateien


def vollsicherung_erstellen(arbeitsordner, ini, werte, fortschritt=lambda wert, text: None):
    # Änderung: Nur gespeicherte Dateien lesen; Fachberechnung und Datenbestände nicht verändern.
    einstellungen_pruefen(werte, arbeitsordner)
    if not werte['ordner'].strip():
        raise ValueError('Bitte einen Sicherungsordner auswählen.')
    quelle = Path(arbeitsordner).resolve()
    ziel = Path(werte['ordner']).expanduser().resolve()
    if not quelle.is_dir():
        raise ValueError('Der Arbeitsordner ist nicht verfügbar.')
    ziel.mkdir(parents=True, exist_ok=True)
    fortschritt(0, FORTSCHRITT_TEXT)
    dateien = dateiliste(quelle, ziel)
    # Änderung: Programmeinstellungen zusätzlich aufnehmen, auch bei externem Arbeitsordner.
    konfiguration = Path(ini).resolve()
    status = konfiguration.stat()
    ini_status = (status.st_size, status.st_mtime_ns)
    zeit = datetime.now()
    # Änderung: Bei gemeinsam genutzten Zielen nur Sicherungen desselben Arbeitsordners aufräumen.
    kennung = hashlib.sha256(os.path.normcase(str(quelle)).encode('utf-8')).hexdigest()
    # Änderung: Schreiben und anschließendes Prüfen zählen mit demselben Maßstab.
    # Pro ZIP-Eintrag eine zusätzliche Einheit, damit auch leere Dateien/Ordner zählen.
    metadaten = json.dumps({'format': 1, 'arbeitsordner_kennung': kennung,
                           'erstellt': zeit.isoformat()}, ensure_ascii=False).encode('utf-8')
    datenmenge = sum(groesse for _, groesse, _ in dateien) + status.st_size + len(metadaten)
    gesamt = 2 * (datenmenge + len(dateien) + 2) + 1
    erledigt = 0
    def weiter(anzahl):
        nonlocal erledigt
        erledigt += anzahl
        # Änderung: Eine Einheit bleibt bis zum erfolgreichen Abschluss reserviert.
        fortschritt(min(erledigt, gesamt - 1) / gesamt, FORTSCHRITT_TEXT)
    archiv = ziel / ('ANA-Vollsicherung-' + zeit.strftime('%Y%m%d-%H%M%S-%f') + '.zip')
    handle, name = tempfile.mkstemp(prefix='.ana-vollsicherung-', suffix='.tmp', dir=ziel)
    os.close(handle)
    temp = Path(name)
    try:
        with ZipFile(temp, 'w', compression=ZIP_DEFLATED, compresslevel=6, allowZip64=True) as zipdatei:
            # Änderung: Dateien blockweise komprimieren, damit auch große Dateien Fortschritt zeigen.
            def aufnehmen(datei, archivname):
                # Änderung: Ursprünglichen Änderungszeitpunkt für spätere Wiederherstellung erhalten.
                info = ZipInfo.from_file(datei, archivname, strict_timestamps=False)
                info.compress_type = ZIP_DEFLATED
                with datei.open('rb') as eingabe, zipdatei.open(info, 'w', force_zip64=True) as ausgabe:
                    while block := eingabe.read(1024 * 1024):
                        ausgabe.write(block)
                        weiter(len(block))
                weiter(1)
            for datei, _, _ in dateien:
                relativ = datei.relative_to(quelle).as_posix()
                archivname = 'Arbeitsordner' + ('/' + relativ if relativ != '.' else '')
                if datei.is_dir():
                    zipdatei.writestr(archivname + '/', '')
                    weiter(1)
                else:
                    aufnehmen(datei, archivname)
            aufnehmen(konfiguration, 'Programmeinstellungen/ana.ini')
            zipdatei.writestr('Sicherungsinformation.json', metadaten)
            weiter(len(metadaten) + 1)
        # Änderung: Eine Änderung während des Kopierens führt zu keiner fertigen Sicherung.
        if dateiliste(quelle, ziel) != dateien or (konfiguration.stat().st_size, konfiguration.stat().st_mtime_ns) != ini_status:
            raise OSError('Dateien wurden während der Sicherung geändert. Bitte erneut sichern.')
        # Änderung: Auch die ZIP-Prüfung blockweise nach Bytes zählen, ohne Phasensprung.
        with ZipFile(temp) as zipdatei:
            for eintrag in zipdatei.infolist():
                with zipdatei.open(eintrag) as inhalt:
                    while block := inhalt.read(1024 * 1024):
                        weiter(len(block))
                weiter(1)
        # Änderung: Erst vollständig geschlossene und geprüfte ZIPs als Sicherung bereitstellen.
        # Änderung: Windows benötigt für das explizite Schreiben auf den Datenträger Schreibzugriff.
        with temp.open('r+b') as stream:
            os.fsync(stream.fileno())
        temp.rename(archiv)
    finally:
        temp.unlink(missing_ok=True)
    warnungen = 0
    if werte['aufraeumen']:
        grenze = zeit - timedelta(weeks=int(werte['wochen']))
        try:
            kandidaten = list(ziel.iterdir())
        except OSError:
            kandidaten = []
            warnungen += 1
        for datei in kandidaten:
            # Änderung: Keine fremden ZIPs, Unterordner oder verlinkten Dateien löschen.
            if datei == archiv or not ARCHIVNAME.fullmatch(datei.name) or datei.is_symlink() or not datei.is_file():
                continue
            try:
                datum = datetime.strptime(datei.name, 'ANA-Vollsicherung-%Y%m%d-%H%M%S-%f.zip')
                if datum < grenze:
                    # Änderung: Der Dateiname allein genügt nicht als Löschberechtigung.
                    with ZipFile(datei) as alt:
                        info = alt.getinfo('Sicherungsinformation.json')
                        if info.file_size > 4096:
                            continue
                        metadaten = json.loads(alt.read(info))
                    if isinstance(metadaten, dict) and metadaten.get('format') == 1 and metadaten.get('arbeitsordner_kennung') == kennung:
                        datei.unlink()
            except (OSError, ValueError, KeyError, BadZipFile):
                warnungen += 1
    fortschritt(1, 'Sicherung abgeschlossen.')
    return archiv, warnungen
