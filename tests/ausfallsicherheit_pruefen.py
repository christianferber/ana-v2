"""Änderung: Schreib- und Kopierfehler ausschließlich mit künstlichen lokalen Dateien prüfen."""
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from anwendung import datenhaltung
from anwendung.sicherung import Sicherung


# Änderung: Fachvergleich isoliert Zusatzprotokoll; echte Protokolle separat prüfen.
@patch('anwendung.aenderungsprotokoll.protokolliere', lambda *args: None)
def pruefen():
    basis = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(dir=basis / '.lokal') as tmp:
        wurzel = Path(tmp).resolve()
        assert wurzel.is_relative_to((basis / '.lokal').resolve())
        app = SimpleNamespace(**{name: str(wurzel / name) for name in (
            'ordner_abrechnungen', 'ordner_rueckv', 'ordner_logs',
            'ordner_datenbank', 'ordner_sicherungen', 'ordner_downloads')})
        app.check_ordner_exists = datenhaltung.check_ordner_exists
        app.dictlist_to_csv = datenhaltung.dictlist_to_csv
        for wert in vars(app).values():
            if isinstance(wert, str):
                Path(wert).mkdir()
        ziel = Path(app.ordner_datenbank) / 'test.csv'
        # Änderung: Auch einen echten Teilinhalt vor einem simulierten Schreibfehler prüfen.
        echtes_temp = tempfile.NamedTemporaryFile
        def fehlerdatei(*args, **kwargs):
            datei = echtes_temp(*args, **kwargs)
            echtes_write = datei.write
            def teil_schreiben(text):
                echtes_write(text[:3])
                raise OSError('simulierter Teil-Schreibfehler')
            datei.write = teil_schreiben
            return datei
        for speichern in (
            lambda: datenhaltung.datei_speichern(ziel, [{'Wert': 'neu'}]),
            lambda: datenhaltung.DatenbankZugriff(app).db_datei_speichern('test.csv', [{'Wert': 'neu'}]),
        ):
            # Änderung: fsync simuliert Fehler nach dem Schreiben; replace simuliert gesperrtes Ziel.
            for stelle in ('os.fsync', 'os.replace'):
                for vorhanden in (False, True):
                    if vorhanden:
                        ziel.write_bytes(b'ALTER INHALT')
                    else:
                        ziel.unlink(missing_ok=True)
                    with patch('anwendung.datenhaltung.' + stelle, side_effect=OSError('Testfehler')):
                        try:
                            speichern()
                        except OSError:
                            pass
                        else:
                            raise AssertionError('Fehler wurde verschluckt')
                    assert ziel.read_bytes() == b'ALTER INHALT' if vorhanden else not ziel.exists()
                    assert not list(ziel.parent.glob('.ana-*.tmp'))
            speichern()
            assert datenhaltung.datei_oeffnen(ziel) == [{'Wert': 'neu'}]
            ziel.write_bytes(b'ALTER INHALT')
            with patch('anwendung.datenhaltung.tempfile.NamedTemporaryFile', side_effect=fehlerdatei):
                try:
                    speichern()
                except OSError:
                    pass
                else:
                    raise AssertionError('Schreibfehler fehlt')
            assert ziel.read_bytes() == b'ALTER INHALT'
            assert not list(ziel.parent.glob('.ana-*.tmp'))

        sicherungen = Path(app.ordner_sicherungen)
        for n in range(9):
            p = sicherungen / ('alt-' + str(n))
            p.mkdir()
            (p / 'test.csv').write_bytes(b'VOLLSTAENDIG')
            os.utime(p, (1000 + n, 1000 + n))
        (ziel.parent / 'unterordner').mkdir()
        (ziel.parent / 'unterordner/test.csv').write_bytes(b'KUNSTDATEN')
        hilfe = Sicherung(app)
        app.max_anzahl_ordner = hilfe.max_anzahl_ordner
        vorher = {str(p.relative_to(sicherungen)): p.read_bytes() for p in sicherungen.rglob('*') if p.is_file()}
        for stelle in ('shutil.copy2', 'shutil.copytree', 'Path.rename'):
            with patch('anwendung.sicherung.' + stelle, side_effect=OSError('Testfehler')):
                try:
                    hilfe.db_sichern('Pruefung')
                except OSError:
                    pass
                else:
                    raise AssertionError('Fehler wurde verschluckt')
            nachher = {str(p.relative_to(sicherungen)): p.read_bytes() for p in sicherungen.rglob('*') if p.is_file()}
            assert vorher == nachher
            assert len(list(sicherungen.iterdir())) == 9
        hilfe.db_sichern('Pruefung')
        assert len(list(sicherungen.iterdir())) == 9
        assert not (sicherungen / 'alt-0').exists()


if __name__ == '__main__':
    pruefen()
    print('CSV-Fehler, Austauschfehler, Sicherungsfehler und erfolgreiche Aufbewahrung: bestanden.')
