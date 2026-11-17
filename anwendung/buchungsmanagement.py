"""Änderung nach 2.06.00: Lokaler, eigenständiger Konto- und Rechnungsabgleich."""
from collections import Counter
import csv
from datetime import datetime
from decimal import Decimal
import hashlib
import io
import json
import os
from pathlib import Path
import re
import tempfile

from pypdf import PdfReader
from anwendung.pdf_texterkennung import pdf_texte_lokal_erkennen

# Änderung: Wie die vorhandenen Datenbanken als db_*.csv im Datenbankverzeichnis speichern.
AUSBLENDUNGEN_DATEINAME = 'db_buchungsmanagement.csv'


# Änderung: Nur das lokal verifizierte Auszugsformat akzeptieren; nie Zeilen raten.
BUCHUNG = re.compile(r'^(\d{2}\.\d{2}\.)\s+(\d{2}\.\d{2}\.)\s+(.+?)\s+([\d.]+,\d{2})\s+([SH])\s*$')
# Änderung: Empfänger oder Zweck sind Pflicht; weitere Rechnungsangaben sind optional.
RECHNUNG = re.compile(r'^(\d{8})(?:-([1-9]\d*))?(b)?\s+(\S.*)$', re.I)


def rechnungsname_lesen(name):
    # Änderung: Keine Rechnungsnummer aus mehrteiligen Empfänger-/Zwecktexten erraten.
    treffer = RECHNUNG.fullmatch(name)
    if not treffer:
        raise ValueError('Erwartet: Buchungsdatum[-Nr.] Empfänger oder Zweck, optional Rechnungsnummer und Rechnungsdatum.')
    tag, nr, zusatz, beschreibung = treffer.groups()
    beschreibung = beschreibung.strip()
    datum = None
    # Änderung: Ein vorhandenes abschließendes Datum prüfen, mit oder ohne „vom“.
    datumstreffer = re.search(r'(?:^|\s)(\d{8})$', beschreibung)
    if datumstreffer:
        datum = datumstreffer.group(1)
        davor = beschreibung[:datumstreffer.start()].strip()
        if not re.search(r'(?:^|\s)vom$', davor, re.I):
            try:
                datetime.strptime(datum, '%d%m%Y')
            except ValueError:
                # Änderung: Ohne „vom“ kann eine achtstellige Zahl auch eine Rechnungsnummer sein.
                datum = None
        if datum:
            beschreibung = re.sub(r'(?:^|\s)vom$', '', davor, flags=re.I).strip()
    elif re.search(r'(?:^|\s)vom(?:\s+[\d./-]+)?$', beschreibung, re.I):
        # Änderung: Optional bedeutet weglassen; ein begonnenes Datumsfeld muss gültig sein.
        raise ValueError('Nach „vom“ wird ein Rechnungsdatum im Format TTMMYYYY erwartet.')
    if not beschreibung:
        raise ValueError('Empfänger oder Zweck fehlt im Dateinamen.')
    return tag, nr, zusatz, beschreibung, datum

# Änderung: Endbeträge nur an eindeutigen Gesamt-/Zahlbetragskennzeichnungen lesen.
ENDSUMME = re.compile(r'\b(?:Rechnungsbetrag|Rechnungssumme|Gesamtbetrag|Gesamtsumme|'
                     r'Endbetrag|Endsumme|Zahlbetrag|Zahlungsbetrag|Bruttobetrag|Gesamtpreis|'
                     r'zu\s+zahlender\s+Betrag|zu\s+zahlen|Gesamt(?:\s+brutto)?|Summe|Total)\b', re.I)
# Änderung: Prozentangaben auch mit Leerzeichen niemals als Geldbetrag übernehmen.
GELDBETRAG = re.compile(r'(?<![\w.,])[-−+]?(?:\d{1,3}(?:[.\u00a0 ]\d{3})+|\d+),\d{2}(?![\d.,]|\s*%)')


def rechnungsbetrag_lesen(datei):
    # Änderung: Layout-Text erhält Spaltenzuordnung; leere Scanseiten lokal per OCR lesen.
    reader = PdfReader(datei)
    texte = [page.extract_text(extraction_mode='layout') or '' for page in reader.pages]
    if any(not t.strip() for t in texte):
        texte = pdf_texte_lokal_erkennen(datei)
    try:
        return endbetrag_aus_texten(texte)
    except ValueError:
        # Änderung: Auch beschädigte PDF-Textschichten dürfen lokale OCR versuchen.
        # Widersprüchliche gelesene Beträge werden dabei nicht durch OCR überstimmt.
        if any(ENDSUMME.search(t) and GELDBETRAG.search(t) for t in texte):
            raise
        return endbetrag_aus_texten(pdf_texte_lokal_erkennen(datei))


def endbetrag_aus_texten(texte):
    # Änderung: Kein Treffer auf beliebige Einzelpreise, Steuern oder Buchungsbeträge.
    kandidaten = {True: set(), False: set()}
    mehrdeutig = {True: False, False: False}
    for text in texte:
        zeilen = text.splitlines()
        for index, zeile in enumerate(zeilen):
            treffer = ENDSUMME.search(zeile)
            if not treffer or re.search(r'\b(?:netto|net|Zwischensumme|Mehrwertsteuer|Umsatzsteuer|MwSt)\b', zeile, re.I):
                continue
            stark = treffer.group().casefold() not in ('gesamt', 'summe', 'total')
            rest = zeile[treffer.end():].strip(' :\t')
            betraege = GELDBETRAG.findall(rest)
            # Änderung: Betrag in Folgezeile nur direkt unter einer alleinstehenden Beschriftung.
            if not betraege and re.fullmatch(r'(?:\(?EUR\)?|€)?', rest, re.I):
                for folgezeile in zeilen[index + 1:index + 3]:
                    if not folgezeile.strip():
                        continue
                    if re.fullmatch(r'[\s\d.,+−\-€()]+|\s*EUR\s*[\d.,+−\- ]+|[\d.,+−\- ]+\s*EUR\s*', folgezeile, re.I):
                        betraege = GELDBETRAG.findall(folgezeile)
                    break
            # Änderung: Mehrere Zahlen hinter einer Beschriftung bleiben ein manueller Prüffall.
            if len(betraege) > 1:
                mehrdeutig[stark] = True
            if betraege:
                wert = betraege[0].replace('.', '').replace(' ', '').replace('\u00a0', '').replace(',', '.').replace('−', '-')
                kandidaten[stark].add(Decimal(wert))
    # Änderung: Eindeutige Endbetragsbezeichnungen haben Vorrang vor allgemeinen Summenzeilen.
    stark = bool(kandidaten[True] or mehrdeutig[True])
    if mehrdeutig[stark]:
        raise ValueError('Mehrere Beträge an einer Endbetragskennzeichnung; bitte manuell prüfen.')
    werte = kandidaten[stark]
    if len(werte) != 1:
        raise ValueError('Kein eindeutiger Rechnungsendbetrag lesbar; bitte manuell prüfen.'
                         if not werte else 'Unterschiedliche Endbeträge im PDF; bitte manuell prüfen.')
    return werte.pop()


def betreff_schluessel(text):
    # Änderung: Nur Schreibweise/Leerraum vereinheitlichen, keine Namen abschneiden.
    return ' '.join(text.split()).casefold()


def empfaenger_und_zweck(detailzeilen):
    # Änderung: Im verifizierten Format steht die Gegenpartei zuerst, danach der Verwendungszweck.
    empfaenger = ' '.join(detailzeilen[0].split()) if detailzeilen else ''
    text = ' '.join(' '.join(z.split()) for z in detailzeilen[1:])
    metadaten = r'\b(?:EREF|MREF|CRED|IBAN|BIC|KREF|ABWA|ABWE|ZREF|SVWZ)\s*:'
    # Änderung: Expliziten SEPA-Verwendungszweck bevorzugen; Bankkennungen gehören nicht zum Zweck.
    svwz = re.search(r'\bSVWZ\s*:\s*(.*?)(?=' + metadaten + r'|$)', text, re.I)
    zweck = svwz.group(1) if svwz else re.split(metadaten, text, maxsplit=1, flags=re.I)[0]
    return empfaenger, ' '.join(zweck.split())


def regel_normalisieren(regel):
    # Änderung: Alte Betreff-Regeln bleiben gültig; neue Regeln enthalten zusätzlich Empfänger und Zweck.
    if isinstance(regel, str):
        regel = (regel, '', '')
    if not isinstance(regel, (list, tuple)) or len(regel) != 3 or not all(isinstance(x, str) for x in regel):
        raise ValueError('Ungültige Buchungsmanagement-Ausschlussregel.')
    regel = tuple(betreff_schluessel(x) for x in regel)
    if not regel[0] and not (regel[1] and regel[2]):
        raise ValueError('Eine Ausschlussregel benötigt Betreff oder Empfänger und Zweck.')
    if bool(regel[1]) != bool(regel[2]):
        raise ValueError('Empfänger und Zweck müssen gemeinsam vorliegen.')
    return regel


def regel_fuer_buchung(buchung):
    # Änderung: Keine breite Paarregel erzeugen, wenn eine der beiden Angaben fehlt.
    empfaenger = buchung.get('empfaenger', '')
    zweck = buchung.get('zweck', '')
    return regel_normalisieren((buchung['betreff'], empfaenger if zweck else '', zweck if empfaenger else ''))


def regeln_ueberlappen(links, rechts):
    # Änderung: Gleicher Betreff bleibt gültig; alternativ müssen beide Paarfelder übereinstimmen.
    return bool((links[0] and links[0] == rechts[0]) or
                (links[1] and links[2] and links[1:] == rechts[1:]))


def ist_ausgeblendet(buchung, regeln):
    # Änderung: Historische Betreffe (nur Gegenpartei) behalten bei der Migration ihre Wirkung.
    schluessel = regel_fuer_buchung(buchung)
    alt = betreff_schluessel(buchung.get('betreff_alt', ''))
    for regel in regeln:
        regel = regel_normalisieren(regel)
        if regeln_ueberlappen(schluessel, regel) or (alt and not regel[1] and not regel[2] and regel[0] == alt):
            return True
    return False


def regeln_ergaenzen(buchungen, regeln):
    # Änderung: Alle bereits passenden Buchungen samt Paaren übernehmen, auch für spätere Importe.
    neu = {regel_normalisieren(r) for r in regeln}
    while True:
        vorher = len(neu)
        for buchung in buchungen:
            if ist_ausgeblendet(buchung, neu):
                neu.add(regel_fuer_buchung(buchung))
        if len(neu) == vorher:
            return sorted(neu)


def auswahl_regeln_aendern(buchungen, regeln, auswahl, ausblenden):
    # Änderung: Zusammengehörige Buchungen sofort gemeinsam ausblenden oder wieder aktivieren.
    bisher = {regel_normalisieren(r) for r in regeln}
    anfang = [regel_fuer_buchung(b) for b in auswahl]
    if not ausblenden:
        # Änderung: Auch verantwortliche Altregeln aufheben, damit die Auswahl nicht sofort wieder verborgen wird.
        anfang.extend(r for r in bisher if any(ist_ausgeblendet(b, [r]) for b in auswahl))
    gruppe = regeln_ergaenzen(buchungen, anfang)
    if ausblenden:
        return regeln_ergaenzen(buchungen, bisher | set(gruppe))
    return sorted(r for r in bisher if not any(regeln_ueberlappen(r, g) for g in gruppe))


def kontoauszuege_lesen(ordner, fortschritt=None):
    # Änderung: Original-PDFs nur lesen; unlesbare oder unbekannte Dateien melden.
    dateien = sorted(Path(ordner).glob('*'))
    dateien = [p for p in dateien if p.is_file() and p.suffix.lower() == '.pdf']
    if not dateien:
        raise ValueError('Im Kontoauszugsordner wurden keine PDF-Dateien gefunden.')
    auszuege = []
    gesehen = set()
    for index, datei in enumerate(dateien):
        # Änderung: Nur abgeschlossene Dateien zählen; Aufrufer übernimmt die UI-Anzeige.
        if fortschritt:
            fortschritt(index, len(dateien), 'Kontoauszüge lesen')
        digest = hashlib.sha256(datei.read_bytes()).hexdigest()
        if digest in gesehen:
            continue
        gesehen.add(digest)
        reader = PdfReader(datei)
        seiten = [(page.extract_text() or '').splitlines() for page in reader.pages]
        text = '\n'.join('\n'.join(s) for s in seiten)
        marker = set(re.findall(r'^\s*(\d{1,3})/(20\d{2})\s*$', text, re.M))
        if 'Kontoauszug' not in text or len(marker) != 1:
            raise ValueError(f'Unbekanntes Auszugsformat oder fehlender Jahresbezug: {datei.name}')
        nummer, jahr = next(iter(marker))
        # Änderung: Zeitraum und Salden sichern Jahreswechsel und vollständigen Import ab.
        salden = {}
        for typ in ('alter', 'neuer'):
            # Änderung: Der Tabellenkopf kann zwischen Datum und Eröffnungssaldo stehen.
            saldo = re.search(typ + r' Kontostand vom\s+(\d{2}\.\d{2}\.\d{4})\s+(?:[^\n]+\n\s*)?([\d.]+,\d{2})\s+([SH])\b', text)
            if not saldo:
                raise ValueError(f'Kontostand/Zeitraum nicht lesbar: {datei.name}')
            saldo_datum, wert, richtung = saldo.groups()
            wert = Decimal(wert.replace('.', '').replace(',', '.'))
            salden[typ] = (datetime.strptime(saldo_datum, '%d.%m.%Y').date(), -wert if richtung == 'S' else wert)
        if salden['alter'][0] > salden['neuer'][0]:
            raise ValueError(f'Ungültiger Auszugszeitraum: {datei.name}')
        zeilen = []
        for seite, lines in enumerate(seiten, 1):
            for index, line in enumerate(lines):
                treffer = BUCHUNG.fullmatch(line.strip())
                if not treffer:
                    if re.match(r'^\d{2}\.\d{2}\.\s+\d{2}\.\d{2}\.', line.strip()):
                        raise ValueError(f'Buchungszeile nicht lesbar: {datei.name}, Seite {seite}')
                    continue
                # Änderung: Die erste Datumsspalte ist der Buchungstag. Die zweite
                # Spalte (Wertstellung) bestimmt weder Datum noch Rechnungszuordnung.
                buchungstag, _wertstellung, art, betrag, richtung = treffer.groups()
                kandidaten = []
                for jahr_kandidat in range(salden['alter'][0].year, salden['neuer'][0].year + 1):
                    try:
                        datum = datetime.strptime(buchungstag + str(jahr_kandidat), '%d.%m.%Y').date()
                    except ValueError:
                        continue
                    if salden['alter'][0] <= datum <= salden['neuer'][0]:
                        kandidaten.append(datum)
                if len(kandidaten) != 1:
                    raise ValueError(f'Buchungsdatum nicht eindeutig im Auszugszeitraum: {datei.name}')
                datum = kandidaten[0]
                # Änderung: Empfänger/Auftraggeber steht im geprüften Format direkt darunter.
                if index + 1 >= len(lines) or BUCHUNG.fullmatch(lines[index + 1].strip()):
                    raise ValueError(f'Buchungsbetreff fehlt: {datei.name}, Seite {seite}')
                betreff = ' '.join(lines[index + 1].split())
                if not betreff:
                    raise ValueError(f'Buchungsbetreff fehlt: {datei.name}, Seite {seite}')
                # Änderung: Weitere Buchungszeilen bis zur nächsten Buchung oder zum Seitenabschluss erfassen.
                details = []
                for detail in lines[index + 1:]:
                    if (re.match(r'^\d{2}\.\d{2}\.\s+\d{2}\.\d{2}\.', detail.strip())
                            or re.match(r'^(?:Übertrag|neuer Kontostand|alter Kontostand)\b', detail.strip(), re.I)):
                        break
                    details.append(detail)
                empfaenger, zweck = empfaenger_und_zweck(details)
                # Änderung: Vereinfachter Betreff umfasst Empfänger und Geschäftszweck statt nur die Gegenpartei.
                einfacher_betreff = empfaenger + (' · ' + zweck if zweck else '')
                wert = Decimal(betrag.replace('.', '').replace(',', '.'))
                if richtung == 'S':
                    wert = -wert
                zeilen.append({'datum': datum.isoformat(), 'betreff': einfacher_betreff, 'betreff_alt': betreff,
                               'empfaenger': empfaenger, 'zweck': zweck,
                               'betrag': str(wert), 'quelle': datei.name,
                               'seite': seite, 'art': art})
        if not zeilen:
            raise ValueError(f'Keine lesbaren Buchungen: {datei.name}')
        if sum((Decimal(b['betrag']) for b in zeilen), Decimal('0')) != salden['neuer'][1] - salden['alter'][1]:
            raise ValueError(f'Saldenprüfung fehlgeschlagen; Import möglicherweise unvollständig: {datei.name}')
        auszuege.append((int(jahr), int(nummer), digest, zeilen))
    # Änderung: Reihenfolge im Auszug bestimmt die Tagesnummer, auch bei ausgeblendeten Zeilen.
    auszuege.sort(key=lambda a: (a[0], a[1]))
    perioden = [(a[0], a[1]) for a in auszuege]
    if len(perioden) != len(set(perioden)):
        raise ValueError('Mehrere unterschiedliche PDFs für denselben Auszug. Bitte eindeutig auswählen.')
    buchungen = [b for a in auszuege for b in a[3]]
    anzahl = Counter(b['datum'] for b in buchungen)
    laufend = Counter()
    for b in buchungen:
        laufend[b['datum']] += 1
        b['nummer'] = laufend[b['datum']]
        b['id'] = b['datum'].replace('-', '')
        if anzahl[b['datum']] > 1:
            b['id'] += '-' + str(b['nummer'])
    if fortschritt:
        fortschritt(len(dateien), len(dateien), 'Kontoauszüge lesen')
    return buchungen


def buchungs_pruef_ids(buchungen, ausgeblendet):
    # Änderung: Tagesnummern für die Prüfung nur aus den noch zu verwaltenden Buchungen bilden.
    aktiv = [b for b in buchungen if not ist_ausgeblendet(b, ausgeblendet)]
    anzahl = Counter(b['datum'] for b in aktiv)
    laufend = Counter()
    ids = {}
    for b in aktiv:
        laufend[b['datum']] += 1
        ident = b['datum'].replace('-', '')
        if anzahl[b['datum']] > 1:
            ident += '-' + str(laufend[b['datum']])
        ids[b['id']] = ident
    return ids


def rechnungen_pruefen(buchungen, ordner, ausgeblendet, fortschritt=None, vollstaendig=False):
    # Änderung: Erst Datum/Tagesnummer zuordnen, danach PDF-Endbetrag centgenau vergleichen.
    pfad = Path(ordner)
    if not pfad.is_dir():
        raise ValueError('Bitte einen vorhandenen Rechnungsordner auswählen.')
    pruef_ids = buchungs_pruef_ids(buchungen, ausgeblendet)
    bestand = {pruef_ids[b['id']]: b for b in buchungen if b['id'] in pruef_ids}
    original = {b['id']: b for b in buchungen}
    # Änderung: Alte nummerierte Rechnungen bleiben bei einer einzigen aktiven Tagesbuchung gültig.
    tage = Counter(b['datum'] for b in bestand.values())
    for b in list(bestand.values()):
        if tage[b['datum']] == 1:
            bestand.setdefault(b['id'], b)
    zuordnung = {}
    probleme = []
    dateiliste = [p for p in sorted(pfad.iterdir()) if p.is_file() and p.suffix.lower() in ('.pdf', '.xml')]
    # Änderung 16.11.2026: Ein gemeinsamer Objektzähler verhindert Rücksprünge zwischen Zuordnung und Betragsprüfung.
    gesamt = len(dateiliste) + len(buchungen)
    for index, datei in enumerate(dateiliste):
        # Änderung: Echte Arbeitsstände für die neue Fortschrittsanzeige melden.
        if fortschritt:
            fortschritt(index, gesamt, 'Rechnungsdateien zuordnen')
        try:
            tag, nr, zusatz, beschreibung, rechnungsdatum = rechnungsname_lesen(datei.stem)
        except ValueError as fehler:
            probleme.append({'status': 'Dateiname fehlerhaft', 'datei': datei.name, 'id': '',
                             'hinweis': str(fehler)})
            continue
        ident = tag + ('-' + nr if nr else '')
        # Änderung: Zugeordnete Rechnungen ausgeblendeter Betreffe ebenfalls nicht verwalten.
        buchung = bestand.get(ident)
        # Änderung: Interne Buchungs-ID bleibt trotz neu berechnetem Dateianfang stabil.
        zugeordnete_id = buchung['id'] if buchung else ''
        if not buchung and ident in original and ist_ausgeblendet(original[ident], ausgeblendet):
            continue
        # Änderung: XML-Zusätze müssen das vereinbarte b im Dateinamen tragen.
        if datei.suffix.lower() == '.xml' and not zusatz:
            probleme.append({'status': 'Dateiname fehlerhaft', 'datei': datei.name, 'id': zugeordnete_id, 'pruef_id': ident,
                             'hinweis': 'XML-Zusatzdateien benötigen b hinter Buchungsdatum/Tagesnummer.'})
            continue
        try:
            datetime.strptime(tag, '%Y%m%d')
            if rechnungsdatum:
                datetime.strptime(rechnungsdatum, '%d%m%Y')
        except ValueError:
            probleme.append({'status': 'Datum ungültig', 'datei': datei.name, 'id': zugeordnete_id, 'pruef_id': ident, 'hinweis': 'Datumsangabe im Dateinamen prüfen.'})
            continue
        if zusatz or datei.suffix.lower() == '.xml':
            # Änderung: Zusatzdatei b ergänzt eine Hauptrechnung und ersetzt sie nicht.
            hauptname = re.sub(r'^(\d{8}(?:-\d+)?)b(?=\s)', r'\1', datei.stem, flags=re.I)
            hauptdateien = [p for p in pfad.iterdir() if p.suffix.lower() == '.pdf'
                           and p.stem.casefold() == hauptname.casefold() and p != datei]
            if not hauptdateien:
                probleme.append({'status': 'Zusatz ohne Hauptrechnung', 'datei': datei.name, 'id': zugeordnete_id, 'pruef_id': ident, 'hinweis': 'Zugehörige PDF-Hauptrechnung fehlt.'})
            continue
        zuordnung.setdefault(buchung['id'] if buchung else ident, []).append(datei.name)
        if ident not in bestand:
            probleme.append({'status': 'Rechnung ohne Buchung', 'datei': datei.name, 'id': '', 'pruef_id': ident, 'hinweis': 'Buchungsdatum und Tagesnummer prüfen.'})
    if fortschritt:
        fortschritt(len(dateiliste), gesamt, 'Rechnungsdateien zuordnen')
    for index, b in enumerate(buchungen):
        if fortschritt:
            fortschritt(len(dateiliste) + index, gesamt, 'Buchungen und PDF-Beträge prüfen')
        if ist_ausgeblendet(b, ausgeblendet):
            continue
        dateien = zuordnung.get(b['id'], [])
        basis = {**b, 'pruef_id': pruef_ids[b['id']], 'betrag_status': 'Nicht geprüft'}
        if len(dateien) != 1:
            probleme.append({**basis, 'status': 'Rechnung fehlt' if not dateien else ('OK' if vollstaendig else 'Mehrere Rechnungen'),
                             'betrag_status': 'Nicht geprüft' if not dateien else 'Mehrere Rechnungen',
                             'datei': ' | '.join(dateien), 'hinweis': 'Erwarteter Dateianfang: ' + basis['pruef_id'] + ' '})
        else:
            # Änderung: Unlesbare/mehrdeutige PDFs niemals als erfolgreich geprüft ausgeben.
            try:
                rechnungsbetrag = rechnungsbetrag_lesen(pfad / dateien[0])
            except ValueError as fehler:
                probleme.append({**basis, 'status': 'OK' if vollstaendig else 'Betrag nicht prüfbar',
                                 'betrag_status': 'Betrag nicht prüfbar', 'datei': dateien[0], 'hinweis': str(fehler)})
            except Exception:
                probleme.append({**basis, 'status': 'OK' if vollstaendig else 'Betrag nicht prüfbar',
                                 'betrag_status': 'Betrag nicht prüfbar', 'datei': dateien[0],
                                 'hinweis': 'PDF nicht lesbar oder geschützt; bitte manuell prüfen.'})
            else:
                # Änderung: Abbuchungen sind negativ, normale Rechnungsbeträge positiv.
                if abs(rechnungsbetrag) != abs(Decimal(b['betrag'])):
                    probleme.append({**basis, 'status': 'OK' if vollstaendig else 'Betrag abweichend',
                                     'betrag_status': 'Betrag abweichend', 'datei': dateien[0],
                                     'rechnungsbetrag': str(rechnungsbetrag),
                                     'hinweis': 'PDF-Endbetrag stimmt im Absolutwert nicht mit der Buchung überein.'})
                elif vollstaendig:
                    # Änderung: Erfolgreiche Zuordnung und Betragsprüfung als getrennte grüne Ergebnisse anzeigen.
                    probleme.append({**basis, 'status': 'OK', 'betrag_status': 'OK', 'datei': dateien[0],
                                     'rechnungsbetrag': str(rechnungsbetrag), 'hinweis': ''})
    # Änderung: Fehlerhafte Rechnungen bleiben sichtbar, auch wenn kein Betreff zugeordnet werden kann.
    if fortschritt:
        fortschritt(gesamt, gesamt, 'Buchungen und PDF-Beträge prüfen')
    if vollstaendig:
        for zeile in probleme:
            zeile.setdefault('pruef_id', zeile.get('id', ''))
            zeile.setdefault('betrag_status', 'Nicht geprüft')
    return probleme


def einstellungen_laden(datei):
    # Änderung: Alte JSON-Ausschlüsse nur für die verlustfreie CSV-Übernahme mitlesen.
    if not Path(datei).exists():
        return {'kontoordner': '', 'rechnungsordner': ''}
    daten = json.loads(Path(datei).read_text(encoding='utf-8'))
    if (not isinstance(daten, dict)
            or not all(isinstance(daten.get(k), str) for k in ('kontoordner', 'rechnungsordner'))
            or not isinstance(daten.get('ausgeblendet', []), list)
            or not all(isinstance(b, str) for b in daten.get('ausgeblendet', []))):
        raise ValueError('Ungültige Buchungsmanagement-Einstellungen.')
    return daten


def einstellungen_speichern(datei, daten):
    # Änderung: JSON enthält künftig nur Ordnerpfade, keine doppelten Ausschlussdaten.
    daten = {k: daten[k] for k in ('kontoordner', 'rechnungsordner')}
    # Änderung: Atomar ersetzen, damit ein Schreibfehler den vorherigen Stand erhält.
    datei = Path(datei)
    temporaer = datei.with_suffix('.tmp')
    temporaer.write_text(json.dumps(daten, ensure_ascii=False, indent=2), encoding='utf-8')
    temporaer.replace(datei)


def ausblendungen_laden(datei):
    # Änderung: Neue Unicode-Dateien und alte CSVs in bisheriger Standardkodierung verlustfrei lesen.
    try:
        with Path(datei).open(encoding=ausblendungen_kodierung(datei), newline='') as quelle:
            reader = csv.DictReader(quelle, delimiter=';', strict=True)
            if reader.fieldnames not in (['Betreff'], ['Betreff', 'Empfaenger', 'Zweck']):
                raise ValueError('Ungültiger CSV-Kopf in der Buchungsmanagement-Datenbank.')
            werte = []
            for zeile in reader:
                if set(zeile) != set(reader.fieldnames) or not all(isinstance(v, str) for v in zeile.values()):
                    raise ValueError('Ungültige Zeile in der Buchungsmanagement-Datenbank.')
                werte.append(regel_normalisieren((zeile['Betreff'], zeile.get('Empfaenger', ''), zeile.get('Zweck', ''))))
    except csv.Error as fehler:
        raise ValueError('Ungültiges CSV-Format in der Buchungsmanagement-Datenbank.') from fehler
    return sorted(set(werte))


def ausblendungen_speichern(datei, ausgeblendet):
    # Änderung: Drei explizite Spalten erhalten Betreff-Regeln und ergänzen Empfänger/Zweck verlustfrei.
    werte = sorted({regel_normalisieren(b) for b in ausgeblendet})
    inhalt = io.StringIO(newline='')
    writer = csv.writer(inhalt, delimiter=';', lineterminator='\n')
    writer.writerow(['Betreff', 'Empfaenger', 'Zweck'])
    writer.writerows(werte)
    # Änderung: Zwecke enthalten auch Zeichen außerhalb der alten Windows-Kodierung. UTF-8-BOM ist Excel-erkennbar.
    ziel = Path(datei)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8-sig', newline='', dir=ziel.parent,
                                         prefix='.ana-', suffix='.tmp', delete=False) as quelle:
            temp = Path(quelle.name)
            quelle.write(inhalt.getvalue())
            quelle.flush()
            os.fsync(quelle.fileno())
        os.replace(temp, ziel)
    finally:
        # Änderung: Schreib-/Austauschfehler erhalten die vorige Datei und beseitigen temporäre Inhalte.
        if temp is not None and temp.exists():
            temp.unlink()


def ausblendungen_kodierung(datei):
    # Änderung: Nur die explizite UTF-8-Markierung auswerten, alte Windows-Dateien nicht umdeuten.
    with Path(datei).open('rb') as quelle:
        return 'utf-8-sig' if quelle.read(3) == b'\xef\xbb\xbf' else None


def ausblendungen_format_alt(datei):
    # Änderung: Einspaltige Vorgängerdateien erst nach vollständiger Ladeprüfung erweitern.
    with Path(datei).open(encoding=ausblendungen_kodierung(datei), newline='') as quelle:
        return next(csv.reader(quelle, delimiter=';'), []) == ['Betreff']
