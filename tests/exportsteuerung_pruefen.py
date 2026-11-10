"""Änderung: Export-Doppelstarts, Fehleranzeige und erneute Starts lokal prüfen."""
from types import SimpleNamespace
from unittest.mock import Mock, patch

from anwendung import exportsteuerung
from anwendung.abrechnung_ui import AbrechnungOberflaeche
from anwendung.rueckverguetung_ui import RueckverguetungOberflaeche
from anwendung.mitglieder_ui import MitgliederOberflaeche


class TestThread:
    # Änderung: Hintergrundarbeit gezielt bis nach einem zweiten Start offen halten.
    def __init__(self, target, args=()):
        self.target, self.args = target, args
        self.aktiv = False

    def start(self):
        self.aktiv = True

    def is_alive(self):
        return self.aktiv

    def beenden(self):
        try:
            self.target(*self.args)
        finally:
            self.aktiv = False


def pruefen():
    for klasse, startname, buttonname, threadname, vorbereiten, pdfname in (
        (AbrechnungOberflaeche, 'abrechnungen_dateien_erstellen', 'abr_button_pdf',
         'abrechnung_pdf_background', 'abrechnungen_word_erstellen', 'abrechnungen_pdf_erstellen'),
        (RueckverguetungOberflaeche, 'rueckv_dateien_erstellen', 'rueckv_button_pdf',
         'rueckv_pdf_background', 'rueckv_word_erstellen', 'rueckv_pdf_erstellen'),
        (MitgliederOberflaeche, 'mitglieder_word_process', 'button_word_export',
         'word_erstellung_background', None, None)):
        for fehler in ('vorbereitung', 'hintergrund', 'threadstart', 'keiner', 'ohne_thread'):
            if klasse is MitgliederOberflaeche and fehler in ('vorbereitung', 'ohne_thread'):
                continue
            ansicht = klasse(SimpleNamespace())
            button = Mock()
            setattr(ansicht, buttonname, button)
            timer = Mock()
            callbacks = []
            def timer_starten(intervall, callback):
                callbacks.append(callback)
                return timer
            arbeit = Mock(side_effect=PermissionError('VERTRAULICH') if fehler == 'hintergrund' else None)
            @exportsteuerung.export_hintergrund_absichern
            def hintergrund(self):
                arbeit()
            if vorbereiten:
                vorbereitung = Mock(side_effect=OSError('VERTRAULICH') if fehler == 'vorbereitung' else None)
                setattr(ansicht, vorbereiten, vorbereitung)
                def pdf_starten():
                    if fehler == 'ohne_thread':
                        return
                    thread = TestThread(lambda: hintergrund(ansicht))
                    setattr(ansicht, threadname, thread)
                    if fehler == 'threadstart':
                        raise RuntimeError('VERTRAULICH')
                    thread.start()
                setattr(ansicht, pdfname, pdf_starten)
                argumente = ()
            else:
                ansicht.mgl_progress = Mock()
                ansicht.anwendung.mitglieder_ja_word_erstellen = lambda datei: hintergrund(ansicht)
                argumente = ('ja', 'liste.docx', '', '')
            ui = Mock()
            ui.timer.side_effect = timer_starten
            with patch.object(exportsteuerung, 'ui', ui), patch('anwendung.mitglieder_ui.threading.Thread', TestThread):
                if klasse is MitgliederOberflaeche and fehler == 'threadstart':
                    with patch.object(TestThread, 'start', side_effect=RuntimeError('VERTRAULICH')):
                        getattr(ansicht, startname)(*argumente)
                else:
                    getattr(ansicht, startname)(*argumente)
                assert ansicht._export_status.aktiv
                button.disable.assert_called_once()
                # Zweiter Aufruf darf weder neu vorbereiten noch einen Timer anlegen.
                getattr(ansicht, startname)(*argumente)
                assert len(callbacks) == 1
                if vorbereiten:
                    vorbereitung.assert_called_once()
                thread = getattr(ansicht, threadname)
                if thread is not None and thread.is_alive():
                    callbacks[0]()
                    button.enable.assert_not_called()
                    thread.beenden()
                callbacks[0]()
                button.enable.assert_called_once()
                timer.deactivate.assert_called_once()
                assert not ansicht._export_status.aktiv
                negative = [c for c in ui.notify.call_args_list if c.kwargs.get('type') == 'negative']
                assert len(negative) == (fehler in ('vorbereitung', 'hintergrund', 'threadstart'))
                assert 'VERTRAULICH' not in str(ui.notify.call_args_list)
                # Auch nach Fehlern muss ein neuer Versuch angenommen werden.
                getattr(ansicht, startname)(*argumente)
                assert len(callbacks) == 2
                thread = getattr(ansicht, threadname)
                if thread is not None and thread.is_alive():
                    thread.beenden()
                callbacks[1]()
                assert not ansicht._export_status.aktiv
    # Änderung: Tatsächliche Mitgliederfunktionen bei Fehlern in Erstellung und Speicherung prüfen.
    for quelle in ('ja', 'gv'):
        for fehlerstelle in ('erstellen', 'speichern'):
            ansicht = MitgliederOberflaeche(SimpleNamespace(disable_row_splitting=Mock(), ordner_downloads='.lokal'))
            ansicht.button_word_export = Mock()
            ansicht.mgl_progress = Mock()
            ansicht.mitglieder_tabelle = [{'Ident': '1', 'Name': 'Lokaler Test'}]
            ansicht.anwendung.mitglieder_ja_word_erstellen = ansicht.mitglieder_ja_word_erstellen
            ansicht.anwendung.mitglieder_gv_word_erstellen = ansicht.mitglieder_gv_word_erstellen
            ui = Mock()
            with patch.object(exportsteuerung, 'ui', ui), \
                    patch('anwendung.mitglieder_ui.threading.Thread', TestThread), \
                    patch('anwendung.mitglieder_ui.pythoncom.CoInitialize'), \
                    patch('docx.document.Document.save', side_effect=PermissionError('VERTRAULICH')):
                if fehlerstelle == 'erstellen':
                    with patch('anwendung.mitglieder_ui.Document', side_effect=OSError('VERTRAULICH')):
                        ansicht.mitglieder_word_process(quelle, 'liste.docx', '01.01.2027', 'Testort')
                        ansicht.word_erstellung_background.beenden()
                else:
                    ansicht.mitglieder_word_process(quelle, 'liste.docx', '01.01.2027', 'Testort')
                    ansicht.word_erstellung_background.beenden()
                assert ansicht._export_status.fehler
                ui.timer.call_args.args[1]()
                ansicht.button_word_export.enable.assert_called_once()
                assert not ansicht._export_status.aktiv
                assert ui.notify.call_args.kwargs['type'] == 'negative'
                assert 'VERTRAULICH' not in str(ui.notify.call_args_list)
    print('Exportoberfläche: Doppelstarts, Fehler, Freigabe und erneute Starts bestanden.')


if __name__ == '__main__':
    pruefen()
