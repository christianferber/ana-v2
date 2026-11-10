"""Änderung: Exportstarts sperren und Hintergrundfehler im UI-Kontext anzeigen."""
from functools import wraps
from types import SimpleNamespace

from nicegui import ui


def export_start_absichern(button_name, thread_name):
    # Änderung: Ein UI-Timer übernimmt Abschlussmeldungen im ursprünglichen Client-Kontext.
    def dekorieren(funktion):
        @wraps(funktion)
        def starten(self, *args, **kwargs):
            status = getattr(self, '_export_status', None)
            if status is not None and status.aktiv:
                ui.notify('Ein Export läuft bereits. Bitte warten.', type='info')
                return
            button = getattr(self, button_name)
            status = SimpleNamespace(aktiv=True, vorbereitet=False, fehler=False)
            self._export_status = status
            setattr(self, thread_name, None)

            def abschliessen():
                if not status.vorbereitet:
                    return
                thread = getattr(self, thread_name)
                if thread is not None and thread.is_alive():
                    return
                timer.deactivate()
                try:
                    button.enable()
                    if status.fehler:
                        ui.notify('Der Export konnte nicht vollständig erstellt werden. '
                                  'Bitte Vorlage und Zielordner prüfen und den Export erneut starten. '
                                  'Bereits erzeugte Dateien können unvollständig sein.', type='negative')
                finally:
                    status.aktiv = False

            try:
                timer = ui.timer(0.1, abschliessen)
            except Exception:
                status.aktiv = False
                raise
            try:
                button.disable()
                return funktion(self, *args, **kwargs)
            except Exception:
                # Änderung: Keine Dateninhalte oder technischen Fehlermeldungen anzeigen.
                status.fehler = True
            finally:
                status.vorbereitet = True
        return starten
    return dekorieren


def export_hintergrund_absichern(funktion):
    # Änderung: Im Hintergrund nur Fehler merken; Meldung erfolgt über den UI-Timer.
    @wraps(funktion)
    def ausfuehren(self, *args, **kwargs):
        try:
            return funktion(self, *args, **kwargs)
        except Exception:
            status = getattr(self, '_export_status', None)
            if status is None or not status.aktiv:
                raise
            status.fehler = True
    return ausfuehren
