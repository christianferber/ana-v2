"""Änderung: Startanzeige, Startreihenfolge und Bereinigung lokal prüfen."""
import contextlib
import gc
import io
from types import SimpleNamespace
from unittest.mock import patch

from anwendung.startanzeige import Startanzeige


def pruefen():
    # Änderung: Mehrfaches Öffnen/Schließen darf weder Tk-Fenster noch Threads hinterlassen.
    for fertig in (False, True, True):
        with Startanzeige() as anzeige:
            assert anzeige._sichtbar.is_set() and anzeige._thread.is_alive()
            anzeige.status(55, 'Oberfläche wird vorbereitet …')
            if fertig:
                anzeige.bereit()
                anzeige._thread.join(timeout=3)
                assert not anzeige._thread.is_alive()
        assert not anzeige._thread.is_alive()
        gc.collect()
    # Änderung: Das Programm muss auch ohne verfügbare Tk-Anzeige weiter starten können.
    with patch.dict('sys.modules', {'tkinter': None}), contextlib.redirect_stderr(io.StringIO()):
        with Startanzeige() as anzeige:
            anzeige._thread.join(timeout=3)
        assert not anzeige._thread.is_alive()
    # Änderung: Der Einstieg lädt die Fachoberfläche erst nach dem Start der Anzeige.
    import sys
    assert 'anwendung.oberflaeche' not in sys.modules
    import ana
    assert 'anwendung.oberflaeche' not in sys.modules
    for fehler in (False, True):
        ereignisse = []
        callbacks = {}
        class Anzeige:
            def __enter__(self):
                ereignisse.append('Anzeige geöffnet')
                return self
            def status(self, wert, text):
                ereignisse.append(wert)
            def bereit(self):
                ereignisse.append('Verbunden')
            def __exit__(self, *args):
                ereignisse.append('Anzeige bereinigt')
        def oberflaeche():
            ereignisse.append('Oberfläche gestartet')
            if fehler:
                raise RuntimeError('Lokaler Startfehler')
            callbacks['startup']()
            callbacks['connect']()
        app = SimpleNamespace(on_startup=lambda f: callbacks.update(startup=f),
                              on_connect=lambda f: callbacks.update(connect=f))
        with patch.object(ana, 'Startanzeige', Anzeige), patch.dict('sys.modules', {
            'anwendung.oberflaeche': SimpleNamespace(main=oberflaeche),
            'nicegui': SimpleNamespace(app=app)}):
            try:
                ana.main()
            except RuntimeError:
                assert fehler
        assert ereignisse[0] == 'Anzeige geöffnet'
        assert ereignisse[-1] == 'Anzeige bereinigt'
        if not fehler:
            assert ereignisse == ['Anzeige geöffnet',55,'Oberfläche gestartet',85,'Verbunden','Anzeige bereinigt']
    print('Startanzeige: echte Fenster, Abschluss, Startfehler, Ausfall und Ladefolge bestanden.')


if __name__ == '__main__':
    pruefen()
