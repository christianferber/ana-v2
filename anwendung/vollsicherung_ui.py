"""Änderung nach 2.05.00: Sicherungseinstellungen und Fortschritt ohne Fachänderungen."""
import threading
from types import SimpleNamespace

from nicegui import app, ui
import webview

from anwendung.vollsicherung import einstellungen_lesen, einstellungen_pruefen, vollsicherung_erstellen


class VollsicherungSteuerung:
    # Änderung: Eine gemeinsame Startsperre verhindert gleichzeitige manuelle/automatische ZIPs.
    def __init__(self, anwendung):
        self.anwendung = anwendung
        self.sperre = threading.Lock()
        self.thread = None
        self.status = SimpleNamespace(wert=0, text='', fertig=False, fehler=None, ergebnis=None)

    def starten(self, werte):
        if not self.sperre.acquire(blocking=False):
            raise ValueError('Eine Sicherung läuft bereits. Bitte warten.')
        self.status = SimpleNamespace(wert=0, text='Sicherung wird vorbereitet …', fertig=False,
                                      fehler=None, ergebnis=None)
        def fortschritt(wert, text):
            self.status.wert, self.status.text = wert, text
        def sichern():
            try:
                self.status.ergebnis = vollsicherung_erstellen(
                    self.anwendung.arbeitsordner, self.anwendung.ini, dict(werte), fortschritt)
            except Exception as fehler:
                # Änderung: Dateninhalte und interne Fehlermeldungen nicht in der Oberfläche ausgeben.
                self.status.fehler = str(fehler) if isinstance(fehler, ValueError) else (
                    'Sicherung fehlgeschlagen. Bitte freien Speicher, Zugriffsrechte und geänderte oder geöffnete Dateien prüfen.')
            finally:
                self.status.fertig = True
                self.sperre.release()
        try:
            self.thread = threading.Thread(target=sichern, name='ANA-Vollsicherung', daemon=False)
            self.thread.start()
        except Exception:
            self.sperre.release()
            raise

    def manuell(self, werte):
        # Änderung: Der Hintergrundthread meldet nur Status; UI-Zugriffe bleiben im Client-Kontext.
        try:
            einstellungen_pruefen(werte, self.anwendung.arbeitsordner)
            self.starten(werte)
        except (ValueError, TypeError, OSError) as fehler:
            ui.notify(str(fehler) if isinstance(fehler, ValueError) else 'Sicherung konnte nicht gestartet werden.', type='negative')
            return
        with ui.dialog().props('persistent') as dialog, ui.card().classes('ana-backup-progress'):
            ui.label('Vollsicherung').classes('text-xl shrink-0')
            # Änderung: Fester, scrollbarer Meldungsbereich hält den Dialog auch bei langen Pfaden stabil.
            with ui.column().classes('ana-backup-message'):
                text = ui.label(self.status.text)
                pfad = ui.label('')
            # Änderung: Ein Gesamtbalken für Komprimieren, ZIP-Prüfung und fertige Sicherung.
            # Änderung: Automatische Rohwertbeschriftung (zum Schluss „1“) ausdrücklich deaktivieren.
            balken = ui.linear_progress(value=0, show_value=False, size='12px').classes('w-full shrink-0 ana-backup-total').props('aria-label="Gesamtfortschritt Komprimieren und Sichern"')
            prozent = ui.label('Gesamtfortschritt: 0 %').classes('shrink-0')
            # Änderung: Buttonplatz von Anfang an reservieren, erst nach Abschluss freigeben.
            schliessen = ui.button('Schließen', on_click=dialog.close).classes('self-start shrink-0')
            schliessen.disable()
        def aktualisieren():
            balken.set_value(self.status.wert)
            # Änderung: Vor Abschluss keine auf 100 % aufgerundete Anzeige.
            prozent.set_text(f'Gesamtfortschritt: {int(self.status.wert * 100)} %')
            text.set_text(self.status.text)
            if not self.status.fertig:
                return
            timer.deactivate()
            schliessen.enable()
            if self.status.fehler:
                text.set_text(self.status.fehler)
                prozent.set_text('Nicht abgeschlossen')
            else:
                archiv, warnungen = self.status.ergebnis
                text.set_text('Sicherung gespeichert:')
                pfad.set_text(str(archiv))
                if warnungen:
                    text.set_text('Sicherung vollständig. Einige alte Sicherungen konnten nicht gelöscht werden.')
        timer = ui.timer(.1, aktualisieren)
        dialog.open()

    def beim_beenden(self):
        # Änderung: Dieser NiceGUI-Hook greift auch beim Schließen mit dem Fenster-X.
        # Das Hauptfenster ist dann bereits geschlossen; deshalb eigener nativer Fortschritt.
        try:
            werte = einstellungen_lesen(self.anwendung.ini)
            if self.thread is not None and self.thread.is_alive():
                sicherung_beim_beenden_anzeigen(self, starten=None)
                # Änderung: Eine bei Programmende laufende Sicherung nicht doppelt erstellen.
                return
            if werte['automatisch']:
                sicherung_beim_beenden_anzeigen(self, starten=werte)
        except Exception:
            # Änderung: Ein fehlendes Sicherungsziel darf keinen stillen Erfolg vortäuschen.
            native_fehler_anzeigen('Die Sicherung beim Programmende konnte nicht erstellt werden. Bitte Sicherungseinstellungen, Zielordner und Zugriffsrechte prüfen.')


def native_fehler_anzeigen(text):
    # Änderung: Auch nach geschlossenem Hauptfenster bleibt ein Sicherungsfehler erkennbar.
    import ctypes
    # Änderung: Auch Anzeige-/Aufräumhinweise können eine erfolgreich erstellte Sicherung betreffen.
    ctypes.windll.user32.MessageBoxW(None, text, 'ANA – Datensicherung', 0x30)


def sicherung_beim_beenden_anzeigen(steuerung, starten):
    # Änderung: Eigenen Fensterprozess vor dem Sichern öffnen und sichtbar bestätigen lassen.
    from anwendung.sicherungsanzeige import Sicherungsanzeige
    import time

    anzeige = None
    sichtbar = False
    try:
        try:
            anzeige = Sicherungsanzeige()
            sichtbar = anzeige.starten()
        except Exception:
            # Änderung: Bei Anzeigefehlern trotzdem sichern und anschließend ausdrücklich informieren.
            sichtbar = False
        if starten is not None:
            steuerung.starten(starten)
        while steuerung.thread is not None and steuerung.thread.is_alive():
            if anzeige is not None:
                sichtbar = anzeige.aktualisieren(steuerung.status) and sichtbar
            time.sleep(.075)
        if steuerung.thread is not None:
            steuerung.thread.join()
        if anzeige is not None:
            sichtbar = anzeige.aktualisieren(steuerung.status) and sichtbar
    finally:
        if steuerung.thread is not None:
            steuerung.thread.join()
        if anzeige is not None:
            anzeige.schliessen()
    if steuerung.status.fehler:
        native_fehler_anzeigen(steuerung.status.fehler)
    elif not sichtbar:
        native_fehler_anzeigen('Die Sicherung ist abgeschlossen. Die Fortschrittsanzeige konnte nicht geöffnet werden.')
    elif steuerung.status.ergebnis and steuerung.status.ergebnis[1]:
        native_fehler_anzeigen('Die neue Sicherung ist vollständig. Einige alte Sicherungen konnten nicht gelöscht werden.')

def sicherungswerte(ansicht):
    # Änderung: Noch nicht gespeicherte Auswahl wird für „Jetzt sichern“ unmittelbar verwendet.
    return dict(ordner=ansicht.backup_ordner.value or '', automatisch=ansicht.backup_automatisch.value,
                aufraeumen=ansicht.backup_aufraeumen.value, wochen=ansicht.backup_wochen.value)


def sicherungskonfiguration_ergaenzen(ansicht, config):
    # Änderung: Unveränderte Einstellungsaufrufe ohne Backup-Bereich weiterhin unterstützen.
    if not hasattr(ansicht, 'backup_ordner'):
        return
    werte = sicherungswerte(ansicht)
    config['Sicherung'] = dict(Ordner=werte['ordner'], BeiProgrammende='ja' if werte['automatisch'] else 'nein',
                              Aufraeumen='ja' if werte['aufraeumen'] else 'nein',
                              AufbewahrungWochen=str(int(werte['wochen'])))


def sicherungskonfiguration_pruefen(ansicht):
    # Änderung: Vor dem bisherigen Speichern validieren; Fehler lassen alle INIs unverändert.
    if not hasattr(ansicht, 'backup_ordner'):
        return True
    try:
        einstellungen_pruefen(sicherungswerte(ansicht), ansicht.ini_arbeitsordner.text or '.')
        return True
    except ValueError as fehler:
        ui.notify(str(fehler), type='negative')
        return False
    except (TypeError, OverflowError):
        ui.notify('Bitte Sicherungsordner und Aufbewahrung (1 bis 520 ganze Wochen) prüfen.', type='negative')
        return False


def sicherungseinstellungen_aufbauen(ansicht, ziel):
    # Änderung: Sicherung ist im bisherigen Einstellungsdialog verwaltbar und über Speichern persistent.
    try:
        werte = einstellungen_lesen(ansicht.anwendung.ini)
    except ValueError as fehler:
        ui.notify(str(fehler), type='negative')
        werte = dict(ordner='', automatisch=False, aufraeumen=False, wochen=12)
    with ziel:
        ui.label('Datensicherung').classes('ana-settings-section')
        with ui.column().classes('w-full ana-backup-settings'):
            ui.label('ZIP mit allen gespeicherten Daten im Arbeitsordner und den Programmeinstellungen. Nicht gespeicherte Eingaben werden nicht übernommen.').classes('ana-settings-note')
            ansicht.backup_ordner = ui.input('Sicherungsordner', value=werte['ordner']).classes('w-full')
            async def auswaehlen():
                auswahl = await app.native.main_window.create_file_dialog(webview.FOLDER_DIALOG)
                if auswahl:
                    ansicht.backup_ordner.set_value(str(auswahl[0]))
            ui.button('Sicherungsordner auswählen', icon='folder', on_click=auswaehlen).classes('ana-secondary-button')
            ansicht.backup_automatisch = ui.checkbox('Bei Programmbeendigung sichern', value=werte['automatisch'])
            ansicht.backup_aufraeumen = ui.checkbox('Alte Vollsicherungen nach erfolgreicher Sicherung aufräumen', value=werte['aufraeumen'])
            # Änderung: Wochen nur bei aktiviertem Aufräumen zeigen; gewählten Wert erhalten.
            with ui.column().classes('w-full ana-backup-retention').bind_visibility_from(ansicht.backup_aufraeumen, 'value'):
                ansicht.backup_wochen = ui.number('Aufbewahrung in Wochen', value=werte['wochen'], min=1, max=520, step=1, precision=0).classes('w-full')
            ui.label('Aufräumen betrifft nur eigene ZIP-Vollsicherungen im gewählten Zielordner. Ein Sicherungsziel innerhalb des Arbeitsordners wird nicht mitgesichert.').classes('ana-settings-note')
            ui.button('Jetzt sichern', icon='backup', on_click=lambda: ansicht.anwendung.vollsicherung.manuell(sicherungswerte(ansicht)))
