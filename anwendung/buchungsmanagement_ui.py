"""Änderung nach 2.06.00: Tools-Ansicht für lokale PDF-Kontoauszüge und Rechnungen."""
from pathlib import Path
import asyncio
import re
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


# Änderung 16.11.2026: Bank-App-Verweise nur aus der Anzeige entfernen; Ausschlussregeln bleiben unverändert.
def zweck_anzeigen(text):
    # Änderung: Auch TAN-Verfahren und verbundene Bank-App-Namen ausblenden, normale Wörter wie Tankstelle erhalten.
    bankverweise = r'\b(?:(?:vr[-\s]*)?secure(?:[-\s]*go(?:[-\s]*plus)?)?|(?:(?:mobile|sms|chip|photo|push|smart|sm@rt)[-\s]*)?tan(?:[-\s]*plus)?)\b'
    return ' '.join(re.sub(bankverweise, '', text, flags=re.I).split())


class BuchungsmanagementOberflaeche:
    async def mit_fortschritt(self, arbeit):
        # Änderung: Worker meldet nur Zähler; ausschließlich der UI-Timer bedient die Anzeige.
        meldungen = SimpleQueue()
        with ui.dialog().props('persistent') as dialog, ui.card().classes('ana-kontomanager-fortschritt'):
            ui.label('Buchungsmanagement – Fortschritt').classes('text-lg font-bold')
            # Änderung 16.11.2026: Vor bekanntem Objektbestand keine scheinbaren Prozentwerte anzeigen.
            phase = ui.label('Kontoauszüge werden vorbereitet …').classes('ana-konto-phase').props('aria-live=polite')
            balken = ui.linear_progress(value=0, show_value=False).classes('w-full').props('indeterminate aria-label="Buchungsmanagement-Fortschritt"')
            stand = ui.label('Vorbereitung …').classes('ana-konto-stand')
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
                balken.props(remove='indeterminate')
                balken.value = wert
                stand.text = f'{aktuell} von {gesamt} Objekten geprüft · {wert:.0%}'

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

    async def oeffnen(self):
        # Änderung 16.11.2026: Ein einziger Einstieg zur Prüfung einschließlich Aktivieren/Ausblenden.
        # Änderung: PDF-Arbeit im Hintergrund; keine Cloud-Aufrufe und keine doppelten Läufe.
        if self.beschaeftigt:
            return
        self.beschaeftigt = True
        self.status.text = 'Kontoauszüge werden lokal gelesen …'
        try:
            self.laden()
            if not self.daten['kontoordner'] or not Path(self.daten['kontoordner']).is_dir():
                raise ValueError('Bitte einen vorhandenen Kontoauszugsordner auswählen.')
            if not self.daten['rechnungsordner']:
                raise ValueError('Bitte einen Rechnungsordner auswählen.')

            def arbeit(melden):
                # Änderung: Ein Fortschrittsfenster begleitet Import und anschließende Rechnungsprüfung.
                # Änderung: Import ist Vorbereitung; der lineare Zähler beginnt mit dem bekannten Prüfbestand.
                buchungen = kontoauszuege_lesen(self.daten['kontoordner'])
                # Änderung: Neue Buchungen gegen vorhandene Regeln prüfen und passende Paare dauerhaft ergänzen.
                regeln = regeln_ergaenzen(buchungen, self.daten['ausgeblendet'])
                probleme = rechnungen_pruefen(buchungen, self.daten['rechnungsordner'],
                                               regeln, melden, vollstaendig=True)
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
            # Änderung 16.11.2026: Bedienhinweise platzsparend bei Bedarf öffnen.
            with ui.expansion('Hinweise zur Buchungsprüfung', icon='info').classes('w-full text-sm'):
                ui.label('Ausblenden gilt auch bei späteren Importen für gleichen Betreff oder gleichen Empfänger und Zweck. Aktivieren hebt zusammengehörige Ausschlüsse auf. Rechnung und Betrag werden getrennt geprüft; unlesbare Beträge bitte manuell prüfen.')
            with ui.row().classes('w-full items-center'):
                anzeigen = ui.switch('Ausgeblendete Buchungen anzeigen')
                suche = ui.input('Suchen').props('clearable').classes('grow')
            # Änderung: Anzeigefilter verändern keine gespeicherten Ausschlussregeln.
            # Änderung 16.11.2026: Filterzustand ohne Dropdown; erneuter Klick zeigt wieder alle Gruppen.
            statusfilter = None
            # Änderung 16.11.2026: Drei vollständige, gegenseitig ausschließende Prüfgruppen als Schnellfilter.
            gruppen = ['OK', 'Betrag prüfen', 'Fehlerhaft']
            zaehler = {}
            if pruefen:
                # Änderung: Gesamtstatus richtet sich ausschließlich nach fehlerhaften Rechnungen, nicht offenen Beträgen.
                with ui.row().classes('items-center ana-rechnung-gesamtstatus').props('aria-live=polite'):
                    gesamt_symbol = ui.icon('check_circle', color='green')
                    gesamt_text = ui.label()
                def gruppe_waehlen(gruppe):
                    nonlocal statusfilter
                    # Änderung: Suche und ausgeblendete Zeilen zurücksetzen, damit die gezählte Gruppe sichtbar wird.
                    suche.value = ''
                    anzeigen.value = False
                    statusfilter = None if statusfilter == gruppe else gruppe
                    aktualisieren()
                with ui.row().classes('w-full items-center'):
                    for gruppe, symbol, farbe in zip(gruppen, ['check_circle', 'warning', 'error'], ['green', 'amber-9', 'red']):
                        zaehler[gruppe] = ui.button(icon=symbol, color=farbe, on_click=lambda g=gruppe: gruppe_waehlen(g)).props('outline')
                        zaehler[gruppe].tooltip('Gruppe anzeigen; erneut klicken, um alle anzuzeigen.')
                filtertext = ui.label().classes('text-sm ana-rechnung-filter')
            spalten = [{'name': name, 'label': label, 'field': name, 'align': 'left', 'sortable': True}
                       for name, label in [('aktiviert', 'Aktiv'), ('status', 'Rechnung' if pruefen else 'Status'),
                                           ('betrag_status', 'Betrag OK'), ('datum_anzeige', 'Datum'),
                                           # Änderung: Beide Ansichten zeigen die nach Ausschlüssen neu berechnete Buchungs-ID.
                                           ('pruef_id', 'Dateianfang' if pruefen else 'Buchungs-ID'), ('betrag_anzeige', 'Betrag (EUR)'),
                                           ('empfaenger', 'Empfänger / Auftraggeber'), ('zweck', 'Zweck'),
                                           ('rechnungsbetrag_anzeige', 'PDF-Endbetrag (EUR)'),
                                           ('datei', 'Rechnungsdatei'), ('hinweis', 'Hinweis')]]
            if not pruefen:
                # Änderung: Verwaltung zeigt keine leeren Rechnungsspalten; Datum/Betrag bleiben erhalten.
                spalten = [s for s in spalten if s['name'] not in ('betrag_status', 'rechnungsbetrag_anzeige', 'datei', 'hinweis')]
            # Änderung: Immer chronologisch absteigend anzeigen; Spaltenklicks ändern diese feste Reihenfolge nicht.
            for spalte in spalten:
                spalte['sortable'] = False
            tabelle = ui.table(columns=spalten, rows=[], row_key='zeile', selection='multiple',
                               pagination=20).props('dense').classes('w-full ana-kontomanager-tabelle').style('min-height: 0; flex: 1')
            # Änderung: Aktivzustand als Symbol mit verständlichem Text für Tooltip und Bildschirmleser.
            tabelle.add_slot('body-cell-aktiviert', '''
                <q-td :props="props"><q-icon v-if="props.value !== '—'"
                :name="props.value === 'Ja' ? 'check' : 'close'"
                :color="props.value === 'Ja' ? 'green' : 'red'" size="18px"
                role="img" :aria-label="props.value === 'Ja' ? 'Aktiv' : 'Inaktiv'">
                <q-tooltip>{{ props.value === 'Ja' ? 'Aktiv' : 'Inaktiv' }}</q-tooltip>
                </q-icon><span v-else>—</span></q-td>''')
            # Änderung: Datum als vollständige, ungeteilte Zeichenfolge in einer Zeile darstellen.
            tabelle.add_slot('body-cell-datum_anzeige', '''
                <q-td :props="props" class="ana-konto-datum"><span>{{ props.value }}</span></q-td>''')
            # Änderung 16.11.2026: Lange Texte begrenzen; vollständiger Inhalt bleibt als Tooltip erreichbar.
            for feld in ('empfaenger', 'zweck', 'datei', 'hinweis'):
                tabelle.add_slot('body-cell-' + feld, '''
                    <q-td :props="props"><div class="ana-konto-kurztext">{{ props.value }}</div>
                    <q-tooltip v-if="props.value" class="ana-konto-volltext">{{ props.value }}</q-tooltip></q-td>''')
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
                summen = dict.fromkeys(gruppen, 0)
                quelle = probleme if pruefen else self.buchungen
                for index, eintrag in enumerate(quelle):
                    b = bestand.get(eintrag.get('id'))
                    verborgen = bool(b and ist_ausgeblendet(b, ausgeschlossen))
                    if verborgen and not anzeigen.value:
                        continue
                    zeile = {**(b or {}), **eintrag, 'zeile': 'eintrag-' + str(index)}
                    zeile['status'] = 'Ausgeblendet' if verborgen else eintrag.get('status', 'Aktiv')
                    if not verborgen and pruefen:
                        # Änderung: Zähler immer vor dem Anzeigefilter aus dem vollständigen aktiven Ergebnis bilden.
                        gruppe = (gruppen[0] if zeile.get('betrag_status') == 'OK' else gruppen[1]) if zeile['status'] == 'OK' else gruppen[2]
                        summen[gruppe] += 1
                        if statusfilter is not None and statusfilter != gruppe:
                            continue
                    zeilen.append(zeile)
                if anzeigen.value and pruefen:
                    for b in self.buchungen:
                        if ist_ausgeblendet(b, ausgeschlossen) and not any(z.get('id') == b['id'] for z in zeilen):
                            zeilen.append({**b, 'zeile': 'aus-' + b['id'], 'status': 'Ausgeblendet'})
                for z in zeilen:
                    # Änderung: ISO-Datum bleibt intern für Zuordnung/Sortierung, Anzeige erhält TT.MM.JJJJ.
                    datum = z.get('datum', '')
                    z['datum_anzeige'] = '.'.join(reversed(datum.split('-'))) if datum else '—'
                    # Änderung: Reine Dateifehler ohne zugehörige Buchung besitzen keinen Aktivierungsstatus.
                    z['aktiviert'] = ('Nein' if z['status'] == 'Ausgeblendet' else 'Ja') if z.get('id') in bestand else '—'
                    # Änderung: Nur die Tabellenkopie bereinigen, niemals Buchungsdaten oder gespeicherte Regeln.
                    z['zweck'] = zweck_anzeigen(z.get('zweck', ''))
                    if z.get('id') in bestand:
                        z['pruef_id'] = aktive_ids.get(z['id'], '—')
                    z['betrag_anzeige'] = z.get('betrag', '').replace('.', ',')
                    # Änderung: Abweichenden Rechnungsbetrag neben dem Buchungsbetrag anzeigen.
                    z['rechnungsbetrag_anzeige'] = z.get('rechnungsbetrag', '').replace('.', ',')
                zeilen.sort(key=lambda z: z.get('datum', ''), reverse=True)
                tabelle.rows = zeilen
                tabelle.selected = []
                tabelle.update()
                zusammenfassung.text = f'{len(zeilen)} Einträge angezeigt.'
                for gruppe, knopf in zaehler.items():
                    knopf.text = f'{gruppe}: {summen[gruppe]}'
                    knopf.props('aria-pressed=' + str(statusfilter == gruppe).lower())
                if pruefen:
                    # Änderung: Gesamtstatus bleibt auch bei Suche/Filter auf den gesamten aktiven Bestand bezogen.
                    fehlerhaft = summen['Fehlerhaft'] > 0
                    gesamt_symbol.props('name=' + ('error' if fehlerhaft else 'check_circle') + ' color=' + ('red' if fehlerhaft else 'green'))
                    gesamt_text.text = 'Gesamtstatus: Fehlerhafte Rechnungen vorhanden' if fehlerhaft else 'Gesamtstatus: Keine fehlerhaften Rechnungen'
                    filtertext.text = 'Anzeige: ' + (statusfilter or 'Alle')

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
                # Änderung 16.11.2026: Separate Umsatzverwaltung entfällt; alle Aktionen stehen in der Prüfung.
                ui.button('Rechnungen überprüfen', icon='fact_check', on_click=self.oeffnen)
            ui.label('Unterstützt wird das PDF-Auszugsformat der bereitgestellten Vorlagen (Buchung/Wert, Betrag mit S/H). Keine gescannten PDFs.').classes('text-sm')
            # Änderung: Empfänger oder Zweck genügt; Rechnungsdetails sind gemäß neuer Vorgabe optional.
            ui.label('Rechnungen: Buchungsdatum[-Nr.] Empfänger oder Zweck.pdf. Rechnungsnummer, „vom“ und Rechnungsdatum sind optional. Endbeträge gescannter Rechnungen werden bei Bedarf mit lokaler Windows-Texterkennung gelesen.').classes('text-sm')
            ui.label('Die Rechnungsprüfung nummeriert aktive Tagesbuchungen in Auszugsreihenfolge. Bleibt nur eine übrig, darf der Anhang entfallen. Zusatzdateien mit b ersetzen keine Hauptrechnung.').classes('text-sm')
            self.status = ui.label()
            try:
                self.laden()
            except Exception:
                self.status.text = 'Einstellungen oder Buchungsmanagement-Datenbank konnten nicht geladen werden. Bitte buchungsmanagement.json und Datenbank/db_buchungsmanagement.csv prüfen.'
