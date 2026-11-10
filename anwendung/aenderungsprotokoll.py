"""Änderung: Daten- und Dateiänderungen ergänzend im bestehenden Changelog erfassen."""
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import warnings


def dateistand(pfade):
    # Änderung: Nur Prüfsummen vergleichen; keine Datei- oder Kontoinhalte protokollieren.
    stand = {}
    for pfad in pfade:
        if pfad is None:
            continue
        datei = Path(pfad)
        stand[str(datei)] = sha256(datei.read_bytes()).hexdigest() if datei.is_file() else None
    return stand


def protokolliere(anwendung, modul, text):
    # Änderung: Bestehenden lokalen Protokollpfad und die vorhandene Anzeige verwenden.
    anwendung.change_log_info(modul, text)


@contextmanager
def aenderungen_protokollieren(anwendung, modul, aktion, daten=lambda: {}, dateien=lambda: ()):
    # Änderung: Kopien vermeiden Änderungen an den beobachteten Originaldaten.
    try:
        vorher = deepcopy(daten())
        # Änderung: Dieselben Dateien beobachten, auch wenn die Aktion Pfadeinstellungen ändert.
        pfade = tuple(dateien())
        dateien_vorher = dateistand(pfade)
    except Exception:
        # Änderung: Auch eine fehlgeschlagene Bestandsaufnahme darf den Fachablauf nicht sperren.
        warnings.warn('Der Ausgangsstand für das Änderungsprotokoll konnte nicht gelesen werden.',
                      RuntimeWarning, stacklevel=2)
        yield
        return
    abgebrochen = True
    try:
        yield
        abgebrochen = False
    finally:
        # Änderung: Auch tatsächlich ausgeführte Teiländerungen bei einem Abbruch erfassen.
        try:
            nachher = daten()
            geaendert = [name for name in vorher.keys() | nachher.keys()
                         if vorher.get(name) != nachher.get(name)]
            dateien_nachher = dateistand(pfade)
            gespeicherte_dateien = [Path(name).name for name in dateien_vorher.keys() | dateien_nachher.keys()
                                   if dateien_vorher.get(name) != dateien_nachher.get(name)]
            if geaendert or gespeicherte_dateien:
                teile = ['Änderung erfasst: ' + aktion]
                if abgebrochen:
                    teile.append('Aktion abgebrochen; bereits ausgeführte Teiländerung')
                if geaendert:
                    teile.append('Arbeitsspeicher: ' + ', '.join(sorted(geaendert)))
                if gespeicherte_dateien:
                    teile.append('Datei geändert: ' + ', '.join(sorted(gespeicherte_dateien)))
                protokolliere(anwendung, modul, ' ::: '.join(teile))
        except Exception:
            # Änderung: Ein Protokollfehler darf das Ergebnis oder den ursprünglichen Fehler nicht ersetzen.
            warnings.warn('Das Änderungsprotokoll konnte nicht vollständig aktualisiert werden.',
                          RuntimeWarning, stacklevel=2)
