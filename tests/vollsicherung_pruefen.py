"""Änderung nach 2.05.00: ZIP-Vollsicherung mit lokalen Daten und Fehlerfällen prüfen."""
import configparser
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
from unittest.mock import patch, Mock
from zipfile import ZipFile

from anwendung.einstellungen import ini_datei_lesen, ini_datei_schreiben
from anwendung.vollsicherung import einstellungen_lesen, vollsicherung_erstellen, FORTSCHRITT_TEXT
from anwendung.vollsicherung_ui import (VollsicherungSteuerung, sicherungskonfiguration_ergaenzen,
                                       sicherungskonfiguration_pruefen, sicherung_beim_beenden_anzeigen)

BASIS = Path(__file__).resolve().parents[1]


def bestand(ordner):
    # Änderung: Inhalte nur lokal vergleichen, keine Daten oder Dateinamen ausgeben.
    return {p.relative_to(ordner): hashlib.sha256(p.read_bytes()).digest()
            for p in ordner.rglob('*') if p.is_file()}


def pruefen():
    quelle = Path(ini_datei_lesen(BASIS / 'ana.ini')['Anwendung']['Arbeitsordner'])
    assert quelle.resolve() == (BASIS.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
    original = bestand(quelle)
    with tempfile.TemporaryDirectory(dir=BASIS / '.lokal') as tmp:
        root = Path(tmp)
        daten, ziel = root / 'daten', root / 'zip'
        shutil.copytree(quelle, daten)
        (daten / 'Leerer Ordner').mkdir()
        ini = root / 'ana.ini'
        config = configparser.ConfigParser()
        config['Anwendung'] = dict(Arbeitsordner=str(daten))
        ini_datei_schreiben(ini, config)
        werte = einstellungen_lesen(ini)
        assert werte == dict(ordner='', automatisch=False, aufraeumen=False, wochen=12)
        werte.update(ordner=str(ziel))
        vorher = bestand(daten)
        meldungen = []
        texte = []
        def fortschritt(wert, text):
            # Änderung: Ein durchgehender Gesamtfortschritt, 100 % erst bei fertigem ZIP.
            meldungen.append(wert)
            texte.append(text)
            if wert == 1:
                assert list(ziel.glob('ANA-Vollsicherung-*.zip'))
                assert not list(ziel.glob('.ana-vollsicherung-*'))
        archiv, warnungen = vollsicherung_erstellen(daten, ini, werte, fortschritt)
        assert warnungen == 0 and meldungen[0] == 0 and meldungen[-1] == 1
        assert meldungen == sorted(meldungen)
        assert all(0 <= wert < 1 for wert in meldungen[:-1])
        assert set(texte[:-1]) == {FORTSCHRITT_TEXT} and texte[-1] == 'Sicherung abgeschlossen.'
        with ZipFile(archiv) as zipdatei:
            assert zipdatei.testzip() is None
            inhalt = {Path(n.removeprefix('Arbeitsordner/')): hashlib.sha256(zipdatei.read(n)).digest()
                      for n in zipdatei.namelist() if n.startswith('Arbeitsordner/') and not n.endswith('/')}
            assert inhalt == vorher
            assert 'Arbeitsordner/Leerer Ordner/' in zipdatei.namelist()
            assert zipdatei.read('Programmeinstellungen/ana.ini') == ini.read_bytes()
            info = zipdatei.read('Sicherungsinformation.json')
        assert bestand(daten) == vorher
        # Änderung: Wiederherstellung der kompletten gespeicherten Daten bytegleich prüfen.
        with ZipFile(archiv) as zipdatei:
            zipdatei.extractall(root / 'wiederhergestellt')
        assert bestand(root / 'wiederhergestellt/Arbeitsordner') == vorher

        # Änderung: Eine große Datei zählt beim Schreiben und Prüfen im selben Maßstab.
        # Damit fällt sowohl eine 90/7-Prozent-Aufteilung als auch Fortschritt nur je Datei auf.
        testdaten = root / 'fortschrittsdaten'
        testdaten.mkdir()
        (testdaten / 'grosse-datei.bin').write_bytes(b'x' * (4 * 1024 * 1024 + 17))
        fortschritte, pruefbeginn = [], []
        def zip_oeffnen(datei, mode='r', **kwargs):
            if mode == 'r':
                pruefbeginn.append(fortschritte[-1])
            return ZipFile(datei, mode, **kwargs)
        with patch('anwendung.vollsicherung.ZipFile', side_effect=zip_oeffnen):
            vollsicherung_erstellen(testdaten, ini, dict(werte, ordner=str(root / 'fortschrittsziel')),
                                    lambda wert, text: fortschritte.append(wert))
        assert len(pruefbeginn) == 1 and .49 < pruefbeginn[0] < .51
        assert sum(pruefbeginn[0] < wert < 1 for wert in fortschritte) >= 5
        schritte = [b - a for a, b in zip(fortschritte, fortschritte[1:]) if b - a > .01]
        assert len(schritte) == 8 and max(schritte) - min(schritte) < 1e-9
        assert fortschritte == sorted(fortschritte) and fortschritte[-1] == 1

        # Änderung: Aufräumen nur für passende Herkunft, nur außerhalb der Wochenfrist.
        alt = datetime.now() - timedelta(weeks=20)
        aktuell = datetime.now() - timedelta(weeks=1)
        def altes_zip(zeit, kennung, nummer):
            pfad = ziel / ('ANA-Vollsicherung-' + zeit.strftime('%Y%m%d-%H%M%S-') + f'{nummer:06}.zip')
            with ZipFile(pfad, 'w') as zipdatei:
                zipdatei.writestr('Sicherungsinformation.json', kennung)
            return pfad
        eigener = altes_zip(alt, info, 1)
        neuer = altes_zip(aktuell, info, 2)
        fremder = altes_zip(alt, json.dumps(dict(format=1, arbeitsordner_kennung='anderer')), 3)
        fremde_datei = ziel / 'andere-sicherung.zip'
        fremde_datei.write_bytes(b'fremd')
        (ziel / 'fremder Ordner').mkdir()
        # Änderung: Ohne Aufräumen alte Sicherungen erhalten.
        vollsicherung_erstellen(daten, ini, werte)
        assert eigener.exists()
        werte['aufraeumen'] = True
        vollsicherung_erstellen(daten, ini, werte)
        assert not eigener.exists() and neuer.exists() and fremder.exists() and fremde_datei.exists()
        assert (ziel / 'fremder Ordner').is_dir()

        # Änderung: Schreibfehler und geänderte Quelldatei lassen alte Archive unangetastet.
        sicherungen = bestand(ziel)
        with patch('anwendung.vollsicherung.ZipFile.open', side_effect=OSError('Testfehler')):
            try:
                vollsicherung_erstellen(daten, ini, werte)
            except OSError:
                pass
            else:
                raise AssertionError('Schreibfehler übergangen')
        assert bestand(ziel) == sicherungen
        assert not list(ziel.glob('.ana-vollsicherung-*'))
        aenderung = daten / 'Veraenderung.txt'
        aenderung.write_text('vorher')
        geaendert = False
        def veraendern(wert, text):
            nonlocal geaendert
            if wert > 0 and not geaendert:
                geaendert = True
                aenderung.write_text('nachher laenger')
        try:
            vollsicherung_erstellen(daten, ini, werte, veraendern)
        except OSError:
            pass
        else:
            raise AssertionError('Änderung während Sicherung übergangen')
        assert bestand(ziel) == sicherungen
        aenderung.unlink()

        # Änderung: Ziel unter Arbeitsordner darf nicht rekursiv ins ZIP gelangen.
        intern = daten / 'Sicherungsziel'
        intern.mkdir()
        (intern / 'nicht-mitsichern.txt').write_text('Test')
        innenwerte = dict(werte, ordner=str(intern))
        innenzip, _ = vollsicherung_erstellen(daten, ini, innenwerte)
        with ZipFile(innenzip) as zipdatei:
            assert not any('Sicherungsziel' in n for n in zipdatei.namelist())
        for falsch in (dict(werte, ordner=str(daten)), dict(werte, ordner=''),
                       # Änderung: Unterordner der alten Datenbankrotation als Ziel ablehnen.
                       dict(werte, ordner=str(daten / 'Sicherungen' / 'Vollsicherungen')),
                       dict(werte, wochen=0), dict(werte, wochen=1.5)):
            try:
                vollsicherung_erstellen(daten, ini, falsch)
            except ValueError:
                pass
            else:
                raise AssertionError('Ungültige Einstellung akzeptiert')

        # Änderung: Alle vier Einstellungen tatsächlich in INI schreiben und neu laden.
        app = SimpleNamespace(ini=str(ini), arbeitsordner=str(daten))
        ansicht = SimpleNamespace(anwendung=app, ini_arbeitsordner=SimpleNamespace(text=str(daten)))
        for name, wert in dict(backup_ordner=str(ziel), backup_automatisch=True,
                              backup_aufraeumen=True, backup_wochen=24).items():
            setattr(ansicht, name, SimpleNamespace(value=wert))
        assert sicherungskonfiguration_pruefen(ansicht)
        sicherungskonfiguration_ergaenzen(ansicht, config)
        ini_datei_schreiben(ini, config)
        assert einstellungen_lesen(ini) == dict(ordner=str(ziel), automatisch=True, aufraeumen=True, wochen=24)

        # Änderung: Doppelstarts, automatische Ausführung und Abwarten mit echter ZIP-Arbeit.
        steuerung = VollsicherungSteuerung(app)
        steuerung.sperre.acquire()
        try:
            steuerung.starten(werte)
        except ValueError:
            pass
        else:
            raise AssertionError('Doppelstart zugelassen')
        finally:
            steuerung.sperre.release()
        steuerung.starten(werte)
        steuerung.thread.join(60)
        assert steuerung.status.fertig and steuerung.status.fehler is None
        with patch('anwendung.vollsicherung_ui.sicherung_beim_beenden_anzeigen') as anzeigen:
            steuerung.beim_beenden()
            assert anzeigen.call_args.kwargs['starten']['automatisch']
        config['Sicherung']['BeiProgrammende'] = 'nein'
        ini_datei_schreiben(ini, config)
        with patch('anwendung.vollsicherung_ui.sicherung_beim_beenden_anzeigen') as anzeigen:
            steuerung.beim_beenden()
            anzeigen.assert_not_called()
        with patch('anwendung.vollsicherung_ui.native_fehler_anzeigen') as melden:
            ini.write_text('[Sicherung]\nAufbewahrungWochen=ungueltig\n', encoding='utf-8')
            steuerung.beim_beenden()
            melden.assert_called_once()
        # Änderung: Ein fehlendes Fortschrittsfenster darf nicht mehr still übergangen werden.
        # Sicherung trotzdem vollständig erstellen und den Anzeigeausfall ausdrücklich melden.
        with patch('anwendung.sicherungsanzeige.Sicherungsanzeige') as fenster, \
                patch('anwendung.vollsicherung_ui.native_fehler_anzeigen') as melden:
            fenster.return_value.starten.return_value = False
            fenster.return_value.aktualisieren.return_value = False
            sicherung_beim_beenden_anzeigen(steuerung, starten=werte)
            assert steuerung.status.fertig and steuerung.status.fehler is None
            assert steuerung.status.ergebnis[0].is_file()
            melden.assert_called_once()
            assert 'Fortschrittsanzeige' in melden.call_args.args[0]
            fenster.return_value.schliessen.assert_called_once()
    assert bestand(quelle) == original


if __name__ == '__main__':
    try:
        pruefen()
        print('Vollsicherung: lokale Beispieldaten bytegleich, ZIP/Wiederherstellung, INI, Aufräumen, Fehler und Startsperre bestanden.')
    except Exception as fehler:
        # Änderung: Vollständige Diagnose ausschließlich lokal ablegen.
        import traceback
        (BASIS / '.lokal/vollsicherung-testfehler.txt').write_text(traceback.format_exc(), encoding='utf-8')
        print('Vollsicherungsprüfung nicht bestanden: ' + type(fehler).__name__)
        raise SystemExit(1)
