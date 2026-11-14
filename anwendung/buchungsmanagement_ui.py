"""Änderung nach 2.06.00: Tools-Ansicht für lokale PDF-Kontoauszüge und Rechnungen."""
from pathlib import Path
import asyncio
from queue import Empty, SimpleQueue

from nicegui import app, run, ui
import webview

from anwendung.aenderungsprotokoll import aenderungen_protokollieren
from anwendung.buchungsmanagement import (
    betreff_schluessel, einstellungen_laden, einstellungen_speichern,
    kontoauszuege_lesen, rechnungen_pruefen, AUSBLENDUNGEN_DATEINAME,
    ausblendungen_laden, ausblendungen_speichern,
    ausblendungen_format_alt, regel_normalisieren, regeln_ergaenzen,
    ist_ausgeblendet, auswahl_regeln_aendern, buchungs_pruef_ids,
)


class BuchungsmanagementOberflaeche:
    async def mit_fortschritt(self, arbeit):
        # Änderung: Worker meldet nur Zähler; ausschließlich der UI-Timer bedient die Anzeige.
        meldungen = SimpleQueue()
        with ui.dialog().props('persistent') as dialog, ui.card().classes('ana-kontomanager-fortschritt'):
            ui.label('Buchungsmanagement – Fortschritt').classes('text-lg font-bold')
            phase = ui.label('Verarbeitung wird vorbereitet …').classes('ana-konto-phase').props('aria-live=polite')
            balken = ui.linear_progress(value=0, show_value=False).classes('w-full').props('aria-label="Buchungsmanagement-Fortschritt"')
            stand = ui.label('0 %').classes('ana-konto-stand')
            with ui.row().classes('items-center'):
                ui.spinner(size='sm')
                ui.label('Bei gescannten Rechnungen kann eine Buchung länger dauern.').classes('text-sm')

        def aktualisieren():
            # Änderung: Neueste Meldung anzeigen, ohne Widgets aus dem Hintergrundthread anzufassen.
            letzte = None
            while True:
                try:
                    letzte = meldungen.get_nowait()
                except Empty:
                    break
            if letzte is not None:
                aktuell, gesamt, text = letzte
                wert = aktuell / gesamt if gesamt else 1
                phase.text = text
                balken.value = wert
                stand.text = f'{aktuell} von {gesamt} · {wert:.0%}'

        timer = ui.timer(0.1, aktualisieren)
        dialog.open()
        try:
            ergebnis = await run.io_bound(arbeit, lambda *meldung: meldungen.put(meldung))
            aktualisieren()
            # Änderung: Den tatsächlichen Abschluss kurz zeigen, dann zum Ergebnis wechseln.
            await asyncio.sleep(0.2)
            return ergebnis
        finally:
            # Änderung: Timer dauerhaft beenden, damit wiederholte Prüfungen keine Timer ansammeln.
            timer.cancel()
            dialog.close()
            dialog.delete()

    # Änderung: Eigenständiger Zustand; bestehende ANA-Kontodaten bleiben unberührt.
    def __init__(self, anwendung):
        self.anwendung = anwendung
        self.buchungen = []
        self.beschaeftigt = False
        self.datei = None
        self.db_datei = None
        self.daten = {}

    def laden(self):
        # Änderung: Einen in den Einstellungen gewechselten Arbeitsordner berücksichtigen.
        datei = Path(self.anwendung.arbeitsordner or '.') / 'buchungsmanagement.json'
        daten = einstellungen_laden(datei)
        # Änderung: CSV ist maßgeblicher Ausschlussbestand; alte JSON-Regeln nur einmal übernehmen.
        db_datei = Path(self.anwendung.ordner_datenbank) / AUSBLENDUNGEN_DATEINAME
        if not db_datei.exists():
            with aenderungen_protokollieren(self.anwendung, 'DATENBANK',
                                           'Buchungsmanagement-Datenbank anlegen', dateien=lambda: (db_datei,)):
                db_datei.parent.mkdir(parents=True, exist_ok=True)
                ausblendungen_speichern(db_datei, daten.get('ausgeblendet', []))
        ausgeblendet = ausblendungen_laden(db_datei)
        if ausblendungen_format_alt(db_datei):
            # Änderung: Vorhandene Betreff-CSV ohne Verlust auf Empfänger/Zweck erweitern.
            with aenderungen_protokollieren(self.anwendung, 'DATENBANK',
                                           'Buchungsmanagement-CSV erweitern', dateien=lambda: (db_datei,)):
                ausblendungen_speichern(db_datei, ausgeblendet)
        if 'ausgeblendet' in daten:
            # Änderung: Erst nach erfolgreicher CSV-Anlage/-Prüfung die frühere JSON-Liste entfernen.
            with aenderungen_protokollieren(self.anwendung, 'EINSTELLUNGEN',
                                           'Buchungsmanagement-Ausschlüsse auf CSV umstellen', dateien=lambda: (datei,)):
                einstellungen_speichern(datei, daten)
        self.datei = datei
        self.db_datei = db_datei
        self.daten = {**daten, 'ausgeblendet': ausgeblendet}
        self.kontopfad.text = daten['kontoordner'] or '— kein Ordner gewählt —'
        self.rechnungspfad.text = daten['rechnungsordner'] or '— kein Ordner gewählt —'

    def speichern(self, daten):
        # Änderung: Nur Pfade in JSON speichern; CSV-Regeln im Arbeitsspeicher erhalten.
        with aenderungen_protokollieren(self.anwendung, 'EINSTELLUNGEN',
                                       'Buchungsmanagement-Einstellungen', dateien=lambda: (self.datei,)):
            einstellungen_speichern(self.datei, daten)
        self.daten = daten

    def ausschluesse_speichern(self, ausgeblendet):
        # Änderung: Betreff-Regeln sofort atomar in der neuen CSV-Datenbank speichern und protokollieren.
        with aenderungen_protokollieren(self.anwendung, 'DATENBANK',
                                       'Buchungsmanagement-Ausschlüsse speichern', dateien=lambda: (self.db_datei,)):
            ausblendungen_speichern(self.db_datei, ausgeblendet)
        self.daten = {**self.daten, 'ausgeblendet': sorted({regel_normalisieren(r) for r in ausgeblendet})}

    async def ordner_waehlen(self, feld):
        # Änderung: Native Ordnerauswahl; Abbrechen erhält die bisherigen Einstellungen.
        if self.beschaeftigt:
            return
        try:
            self.laden()
            auswahl = await app.native.main_window.create_file_dialog(webview.FOLDER_DIALOG)
            if auswahl:
                self.speichern({**self.daten, feld: str(auswahl[0])})
                self.laden()
                self.buchungen = []
        except Exception as fehler:
            ui.notify('Einstellungen konnten nicht gespeichert werden: ' + str(fehler), type='negative')

    async def oeffnen(self, pruefen=False):
        # Änderung: PDF-Arbeit im Hintergrund; keine Cloud-Aufrufe und keine doppelten Läufe.
        if self.beschaeftigt:
            return
        self.beschaeftigt = True
        self.status.text = 'Kontoauszüge werden lokal gelesen …'
        try:
            self.laden()
            if not self.daten['kontoordner'] or not Path(self.daten['kontoordner']).is_dir():
                raise ValueError('Bitte einen vorhandenen Kontoauszugsordner auswählen.')
            if pruefen and not self.daten['rechnungsordner']:
                raise ValueError('Bitte einen Rechnungsordner auswählen.')

            def arbeit(melden):
                # Änderung: Ein Fortschrittsfenster begleitet Import und anschließende Rechnungsprüfung.
                buchungen = kontoauszuege_lesen(self.daten['kontoordner'], melden)
                # Änderung: Neue Buchungen gegen vorhandene Regeln prüfen und passende Paare dauerhaft ergänzen.
                regeln = regeln_ergaenzen(buchungen, self.daten['ausgeblendet'])
                probleme = rechnungen_pruefen(buchungen, self.daten['rechnungsordner'],
                                               regeln, melden, vollstaendig=True) if pruefen else None
                return buchungen, probleme, regeln

            self.buchungen, probleme, regeln = await self.mit_fortschritt(arbeit)
            if regeln != self.daten['ausgeblendet']:
                self.ausschluesse_speichern(regeln)
            self.status.text = f'{len(self.buchungen)} Buchungen gelesen.'
            self.dialog_oeffnen(probleme)
        except Exception as fehler:
            self.buchungen = []
            self.status.text = 'Vorgang abgebrochen; kein vollständiges Prüfergebnis.'
            ui.notify(str(fehler), type='negative', timeout=10000)
        finally:
            self.beschaeftigt = False

    def dialog_oeffnen(self, probleme=None):
        # Änderung: Separates Dialogfenster mit Filter, Mehrfachauswahl und reaktivierbaren Betreff-Regeln.
        pruefen = probleme is not None
        bestand = {b['id']: b for b in self.buchungen}
        with ui.dialog() as dialog, ui.card().classes('ana-kontomanager-dialog'):
            ui.label('Rechnungen überprüfen' if pruefen else 'Kontoumsätze verwalten').classes('text-xl font-bold')
            ui.label('Ausblenden gilt sofort und bei späteren Importen für gleichen Betreff oder gleichen Empfänger und Zweck. Aktivieren hebt die zusammengehörigen Ausschlüsse wieder auf.').classes('text-sm')
            if pruefen:
                # Änderung: Ergänzten PDF-Betragsvergleich und offene manuelle Prüffälle erklären.
                ui.label('Rechnung und Betrag werden getrennt geprüft. Tagesnummern berücksichtigen ausgeblendete Buchungen. Nicht eindeutig lesbare Beträge bitte manuell prüfen.').classes('text-sm')
            with ui.row().classes('w-full items-center'):
                anzeigen = ui.switch('Ausgeblendete Buchungen anzeigen')
                suche = ui.input('Suchen').props('clearable').classes('grow')
            # Änderung: Anzeigefilter verändern keine gespeicherten Ausschlussregeln.
            statusfilter = None
            if pruefen:
                statusfilter = ui.select(['Alle anzeigen', 'Status OK ausblenden', 'Status OK und Betrag OK ausblenden'],
                                         value='Alle anzeigen', label='Prüfergebnisse anzeigen').classes('w-full')
            spalten = [{'name': name, 'label': label, 'field': name, 'align': 'left', 'sortable': True}
                       for name, label in [('status', 'Rechnung' if pruefen else 'Status'),
                                           ('betrag_status', 'Betrag OK'), ('datum', 'Datum'),
                                           # Änderung: Beide Ansichten zeigen die nach Ausschlüssen neu berechnete Buchungs-ID.
                                           ('pruef_id', 'Dateianfang' if pruefen else 'Buchungs-ID'), ('betrag_anzeige', 'Betrag (EUR)'),
                                           ('empfaenger', 'Empfänger / Auftraggeber'), ('zweck', 'Zweck'),
                                           ('rechnungsbetrag_anzeige', 'PDF-Endbetrag (EUR)'),
                                           ('datei', 'Rechnungsdatei'), ('hinweis', 'Hinweis')]]
            if not pruefen:
                # Änderung: Verwaltung zeigt keine leeren Rechnungsspalten; Datum/Betrag bleiben erhalten.
                spalten = [s for s in spalten if s['name'] not in ('betrag_status', 'rechnungsbetrag_anzeige', 'datei', 'hinweis')]
            tabelle = ui.table(columns=spalten, rows=[], row_key='zeile', selection='multiple',
                               pagination=20).classes('w-full ana-kontomanager-tabelle').style('min-height: 0; flex: 1')
            # Änderung: Status immer als Text und zusätzlich farblich unterscheidbar anzeigen.
            tabelle.add_slot('body-cell-status', '''
                <q-td :props="props"><q-badge
                :color="props.value === 'Ausgeblendet' ? 'grey' : ['Aktiv', 'OK'].includes(props.value) ? 'green' : props.value === 'Rechnung fehlt' ? 'orange-9' : 'red'"
                :label="props.value" /></q-td>''')
            tabelle.add_slot('body-cell-betrag_status', '''
                <q-td :props="props"><q-badge :color="props.value === 'OK' ? 'green' : props.value === 'Nicht geprüft' ? 'grey' : 'red'"
                :label="props.value || 'Nicht geprüft'" /></q-td>''')
            # Änderung: Sichtbare ID und unveränderlicher Auswahlschlüssel bleiben getrennt zuordenbar.
            tabelle.add_slot('body-cell-pruef_id', '''
                <q-td :props="props" class="ana-buchungs-id" :data-ursprung="props.row.id">{{ props.value }}</q-td>''')
            suche.bind_value(tabelle, 'filter')
            zusammenfassung = ui.label()

            def aktualisieren():
                # Änderung: Jede Ansicht aus dem vollständigen Bestand und aktuellen Regeln erzeugen.
                ausgeschlossen = set(self.daten['ausgeblendet'])
                # Änderung: Bei jedem Aktualisieren alle aktiven Tages-IDs neu erzeugen, auch in der Umsatzverwaltung.
                aktive_ids = buchungs_pruef_ids(self.buchungen, ausgeschlossen)
                zeilen = []
                quelle = probleme if pruefen else self.buchungen
                for index, eintrag in enumerate(quelle):
                    b = bestand.get(eintrag.get('id'))
                    verborgen = bool(b and ist_ausgeblendet(b, ausgeschlossen))
                    if verborgen and not anzeigen.value:
                        continue
                    zeile = {**(b or {}), **eintrag, 'zeile': 'eintrag-' + str(index)}
                    zeile['status'] = 'Ausgeblendet' if verborgen else eintrag.get('status', 'Aktiv')
                    if not verborgen and statusfilter is not None:
                        if statusfilter.value == 'Status OK ausblenden' and zeile['status'] == 'OK':
                            continue
                        if (statusfilter.value == 'Status OK und Betrag OK ausblenden'
                                and zeile['status'] == 'OK' and zeile.get('betrag_status') == 'OK'):
                            continue
                    zeilen.append(zeile)
                if anzeigen.value and pruefen:
                    for b in self.buchungen:
                        if ist_ausgeblendet(b, ausgeschlossen) and not any(z.get('id') == b['id'] for z in zeilen):
                            zeilen.append({**b, 'zeile': 'aus-' + b['id'], 'status': 'Ausgeblendet'})
                for z in zeilen:
                    if z.get('id') in bestand:
                        z['pruef_id'] = aktive_ids.get(z['id'], '—')
                    z['betrag_anzeige'] = z.get('betrag', '').replace('.', ',')
                    # Änderung: Abweichenden Rechnungsbetrag neben dem Buchungsbetrag anzeigen.
                    z['rechnungsbetrag_anzeige'] = z.get('rechnungsbetrag', '').replace('.', ',')
                tabelle.rows = zeilen
                tabelle.selected = []
                tabelle.update()
                zusammenfassung.text = f'{len(zeilen)} Einträge angezeigt.'

            async def auswahl_aendern(ausblenden):
                # Änderung: Nur Buchungen ausschließen; reine Rechnungsfehler sind keine Buchungen.
                if self.beschaeftigt:
                    return
                auswahl = [bestand[z['id']] for z in tabelle.selected if z.get('id') in bestand]
                if not auswahl:
                    ui.notify('Bitte mindestens eine Buchung auswählen.', type='warning')
                    return
                neu = auswahl_regeln_aendern(self.buchungen, self.daten['ausgeblendet'], auswahl, ausblenden)
                self.beschaeftigt = True
                try:
                    self.ausschluesse_speichern(neu)
                    if pruefen:
                        # Änderung: Reaktivierte Buchungen sofort wieder vollständig prüfen.
                        # Änderung: Auch erneute Prüfungen nach Ausschluss/Reaktivierung mit Fortschritt ausführen.
                        probleme[:] = await self.mit_fortschritt(lambda melden: rechnungen_pruefen(
                            self.buchungen, self.daten['rechnungsordner'], neu, melden, vollstaendig=True))
                    aktualisieren()
                except Exception as fehler:
                    ui.notify('Änderung/Prüfung nicht vollständig: ' + str(fehler), type='negative')
                finally:
                    self.beschaeftigt = False

            anzeigen.on_value_change(aktualisieren)
            if statusfilter is not None:
                statusfilter.on_value_change(aktualisieren)
            with ui.row().classes('w-full items-center'):
                ui.button('Auswahl ausblenden', icon='visibility_off', on_click=lambda: auswahl_aendern(True))
                ui.button('Auswahl aktivieren', icon='visibility', on_click=lambda: auswahl_aendern(False))
                ui.space()
                ui.button('Schließen', on_click=dialog.close)
            aktualisieren()
        dialog.open()

    def aufbauen(self):
        # Änderung: Beide Ordner unabhängig wählen; niemals Quelldateien verändern.
        with ui.column().classes('w-full ana-buchungsmanagement'):
            ui.label('Buchungsmanagement').classes('text-2xl font-bold')
            ui.label('PDF-Kontoauszüge lokal lesen und Rechnungsdateinamen abgleichen.')
            for feld, titel in [('kontoordner', 'Ordner Kontoauszüge'), ('rechnungsordner', 'Ordner Rechnungen')]:
                with ui.row().classes('items-center w-full'):
                    ui.button(titel, icon='folder', on_click=lambda f=feld: self.ordner_waehlen(f))
                    label = ui.label('— kein Ordner gewählt —').style('overflow-wrap: anywhere')
                    if feld == 'kontoordner':
                        self.kontopfad = label
                    else:
                        self.rechnungspfad = label
            with ui.row():
                ui.button('Kontoumsätze verwalten', icon='account_balance', on_click=lambda: self.oeffnen())
                ui.button('Rechnungen überprüfen', icon='fact_check', on_click=lambda: self.oeffnen(True))
            ui.label('Unterstützt wird das PDF-Auszugsformat der bereitgestellten Vorlagen (Buchung/Wert, Betrag mit S/H). Keine gescannten PDFs.').classes('text-sm')
            # Änderung: Empfänger oder Zweck genügt; Rechnungsdetails sind gemäß neuer Vorgabe optional.
            ui.label('Rechnungen: Buchungsdatum[-Nr.] Empfänger oder Zweck.pdf. Rechnungsnummer, „vom“ und Rechnungsdatum sind optional. Endbeträge gescannter Rechnungen werden bei Bedarf mit lokaler Windows-Texterkennung gelesen.').classes('text-sm')
            ui.label('Die Rechnungsprüfung nummeriert aktive Tagesbuchungen in Auszugsreihenfolge. Bleibt nur eine übrig, darf der Anhang entfallen. Zusatzdateien mit b ersetzen keine Hauptrechnung.').classes('text-sm')
            self.status = ui.label()
            try:
                self.laden()
            except Exception:
                self.status.text = 'Einstellungen oder Buchungsmanagement-Datenbank konnten nicht geladen werden. Bitte buchungsmanagement.json und Datenbank/db_buchungsmanagement.csv prüfen.'
