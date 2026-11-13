"""Änderung nach 2.049: Lesender Kostenvergleich aller Abnehmer und Jahre."""
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re

from nicegui import ui


def kostenwerte_lesen(datei):
    # Änderung: Gespeicherte Eurobeträge vergleichen, keine Abrechnung neu berechnen.
    try:
        try:
            inhalt = Path(datei).read_text(encoding='utf-8-sig')
        except UnicodeDecodeError:
            inhalt = Path(datei).read_text(encoding='cp1252')
        quelle = csv.DictReader(inhalt.splitlines(), delimiter=';')
        pflicht = {'Ident', 'Name', 'Vorname', 'Wärmekosten tats Verbrauch', 'Mindestvertragssumme'}
        if not pflicht <= set(quelle.fieldnames or []):
            return [], 1
        zeilen, fehler = [], 0
        for nummer, zeile in enumerate(quelle):
            # Änderung: Ungültige Beträge bleiben sichtbar; niemals als Null ausgeben.
            werte = []
            for feld in ('Wärmekosten tats Verbrauch', 'Mindestvertragssumme'):
                try:
                    wert = Decimal(zeile[feld].strip().replace(',', '.'))
                    if not wert.is_finite():
                        raise InvalidOperation
                    werte.append(wert)
                except (InvalidOperation, AttributeError, TypeError):
                    werte.append(None)
                    fehler += 1
            kosten, minimum = werte
            differenz = kosten - minimum if None not in werte else None
            def anzeigen(wert):
                # Änderung: Deutsche Beträge mit Centgenauigkeit anzeigen.
                return '–' if wert is None else f'{wert:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
            zeilen.append({'schluessel': nummer, 'ident': zeile['Ident'], 'name': zeile['Name'],
                           'vorname': zeile['Vorname'], 'kosten': anzeigen(kosten),
                           'minimum': anzeigen(minimum), 'differenz': anzeigen(differenz),
                           'sortierwert': differenz,
                           'farbe': 'text-green-800 bg-green-50' if differenz is not None and differenz > 0
                           else 'text-red-800 bg-red-50' if differenz is not None and differenz < 0 else ''})
        # Änderung: Numerisch aufsteigend; fehlende Beträge zuletzt. Decimal bleibt nur lokal.
        zeilen.sort(key=lambda z: (z['sortierwert'] is None, z['sortierwert'] or Decimal(0)))
        for zeile in zeilen:
            del zeile['sortierwert']
        return zeilen, fehler
    except (OSError, UnicodeError, csv.Error):
        return [], 1


def kostenmatrix_lesen(dateien):
    # Änderung: Abnehmer über ihre Text-Ident verbinden; je Jahr nur die Differenz zeigen.
    abnehmer, fehler = {}, 0
    jahre = sorted(dateien)
    for jahr in jahre:
        zeilen, lesefehler = kostenwerte_lesen(dateien[jahr])
        fehler += lesefehler
        gesehen = set()
        for zeile in zeilen:
            ident = str(zeile['ident'] or '').strip()
            if not ident:
                fehler += 1
                continue
            if ident not in abnehmer:
                abnehmer[ident] = {'ident': ident, 'name': '', 'vorname': '', 'farben': {}}
                for j in jahre:
                    abnehmer[ident][f'jahr_{j}'] = '–'
                    abnehmer[ident][f'sort_{j}'] = None
            ziel = abnehmer[ident]
            feld = f'jahr_{jahr}'
            if ident in gesehen:
                # Änderung: Mehrdeutige Jahreswerte nicht still überschreiben oder summieren.
                ziel[feld], ziel[f'sort_{jahr}'], ziel['farben'][feld] = '–', None, ''
                fehler += 1
                continue
            gesehen.add(ident)
            ziel['name'], ziel['vorname'] = zeile['name'], zeile['vorname']
            ziel[feld] = zeile['differenz']
            ziel['farben'][feld] = zeile['farbe']
            if zeile['differenz'] != '–':
                # Änderung: Centbeträge als Zahlen für die Sortierung, Anzeige bleibt deutsch formatiert.
                ziel[f'sort_{jahr}'] = int(Decimal(zeile['differenz'].replace('.', '').replace(',', '.')) * 100)
    zeilen = list(abnehmer.values())
    if jahre:
        feld = f'sort_{jahre[-1]}'
        zeilen.sort(key=lambda z: (z[feld] is None, z[feld] or 0, z['ident']))
    return zeilen, fehler


class Kostenstatistik:
    # Änderung: Gemeinsame Tabelle mit einer Spalte je gespeichertem Jahr.
    def __init__(self, anwendung, verbraucherspezifisch=False):
        self.anwendung = anwendung
        self.dateien = {}
        # Änderung: Dieselbe Kostenauswertung allgemein oder für genau eine Text-Ident verwenden.
        self.verbraucherspezifisch = verbraucherspezifisch

    def aktualisieren(self, ident=None):
        basis = Path(self.anwendung.ordner_abrechnungen)
        self.dateien = {}
        if basis.is_dir():
            for ordner in basis.iterdir():
                treffer = re.fullmatch(r'Abrechnung-(\d{4})', ordner.name)
                datei = ordner / (ordner.name + '.csv')
                if treffer and ordner.is_dir() and datei.is_file():
                    self.dateien[int(treffer[1])] = datei
        jahre = sorted(self.dateien)
        # Änderung: Alle gespeicherten Jahre nebeneinander statt einer Jahresauswahl.
        zeilen, fehler = kostenmatrix_lesen(self.dateien)
        # Änderung: Ohne Verbraucherauswahl keine fremden Daten in der Einzelansicht zeigen.
        if self.verbraucherspezifisch:
            zeilen = [z for z in zeilen if ident is not None and z['ident'] == str(ident).strip()]
        self.tabelle.columns = [
            {'name': name, 'label': titel, 'field': name, 'align': 'left'}
            for name, titel in [('ident', 'Ident'), ('name', 'Name'), ('vorname', 'Vorname')]]
        # Änderung: Im Verbraucherbereich ist die Person bereits durch die Auswahl festgelegt.
        if self.verbraucherspezifisch:
            self.tabelle.columns = []
        self.tabelle.columns += [
            # Änderung: Jahreskopf ohne Einheit, Währung nur am angezeigten Betrag.
            {'name': f'jahr_{jahr}', 'label': str(jahr), 'field': f'sort_{jahr}',
             'align': 'right', 'sortable': True,
             ':rawSort': '(a,b) => a === null ? (b === null ? 0 : 1) : b === null ? -1 : a-b'}
            for jahr in jahre]
        self.tabelle.rows = zeilen
        self.tabelle.pagination = {'rowsPerPage': 0, 'sortBy': f'jahr_{jahre[-1]}' if jahre else None,
                                   'descending': False}
        self.tabelle.update()
        hinweis = ('Tatsächliche Wärmekosten − Mindestvertragssumme (Euro). '
                   'Eine Spalte je Jahr; positive Werte grün, negative rot, Null neutral. '
                   'Aufsteigend nach dem neuesten Jahr sortiert; zum Umsortieren auf eine Jahresspalte klicken. '
                   '„–“ bedeutet kein eindeutiger Jahreswert verfügbar.')
        if not zeilen:
            hinweis += ' Keine gespeicherten Kostenwerte verfügbar.'
        if self.verbraucherspezifisch and ident is None:
            hinweis = 'Bitte oben einen Verbraucher auswählen.'
        if fehler:
            hinweis += ' Einige Kostenwerte konnten nicht gelesen werden; fehlende Werte erscheinen als „–“.'
        self.hinweis.set_text(hinweis)

    def aufbauen(self):
        with ui.column().classes('w-full ana-kostenstatistik') as self.bereich:
            ui.label('Kostenvergleich zu Mindestabnahme').classes('text-h6')
            self.hinweis = ui.label('').classes('text-sm text-slate-600')
            self.tabelle = ui.table(columns=[], rows=[], row_key='ident',
                                    pagination={'rowsPerPage': 0}).classes('w-full')
            # Änderung: Jede Jahreszelle erhält ihre eigene Vorzeichenfarbe und formatierte Differenz.
            self.tabelle.add_slot('body-cell', '''
                <q-td :props="props" :class="props.row.farben[props.col.name] || ''">
                    {{ props.row[props.col.name] }}{{ props.col.name.startsWith('jahr_') && props.row[props.col.name] !== '–' ? ' €' : '' }}
                </q-td>
            ''')
