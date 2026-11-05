"""Änderung für v2: Abrechnungen ohne Oberfläche und globale Eingabedaten berechnen."""

from datetime import datetime, timedelta
# Änderung für v2: Bestehende Dezimalrundung für Buchungsvorlagen bereitstellen.
from decimal import Decimal, ROUND_HALF_UP

# Änderung für v2: Bestehende Hilfsfunktion mit unverändertem Funktionskörper.
def abnehmer_aus_daten(abnehmer_db):
    abnehmer_liste_temp = []
    for row in abnehmer_db:
        abnehmer_liste_row_temp = {}
        for key,value in row.items():
            if key == "Ident" or key == "Name" or key == "Vorname":
                abnehmer_liste_row_temp[key] = value
        abnehmer_liste_temp.append(abnehmer_liste_row_temp)
    return abnehmer_liste_temp


# Änderung für v2: Bestehende Hilfsfunktion mit unverändertem Funktionskörper.
def mwst_berechnen(ziel,wert,satz,nachkomma):
    if ziel == "mwst":
        ergebnis = round((float(wert) / (100 + int(satz)) * int(satz)),nachkomma)
    elif ziel == "netto":
        ergebnis = round((float(wert) / (100 + int(satz)) * 100),nachkomma)
    else:
        print("Zielwert bei MwSt-Berechnung nicht spezifiziert.")
        return
    return ergebnis


# Änderung für v2: Bestehende Hilfsfunktion mit unverändertem Funktionskörper.
def datum_in_string(datum):
    if "." in datum:
        datum_split = datum.split(".")
        datum_string = datum_split[2] + datum_split[1] + datum_split[0]
    elif "-" in datum:
        datum_string = datum.replace("-","")
    return datum_string


# Änderung für v2: Bestehende Hilfsfunktion mit unverändertem Funktionskörper.
def datum_in_punkt(datum):
    if "-" in datum:
        datum_split = datum.split("-")
        datum_string = datum_split[2] + "." + datum_split[1] + "." + datum_split[0]
    return datum_string


# Änderung für v2: Bestehende Hilfsfunktion mit unverändertem Funktionskörper.
def datum_tage_vorher(datum,tage):
    datum = str(datum)
    if "." in datum:
        datum_split = datum.split(".")
        datum_string = datum_split[2] + "-" + datum_split[1] + "-" + datum_split[0]
    elif "-" in datum:
        datum_string = datum
    else:
        if len(datum) == 8:
            jahr = datum[:4]
            monat = datum[4:6]
            tag = datum[6:9]
            datum_string = jahr + "-" + monat + "-" + tag
        else:
            print('Kein korrektes Datums-Format.')
            return
    datum_object = datetime.strptime(datum_string, '%Y-%m-%d')
    datum_vorher = str((datum_object - timedelta(days=tage)).date())
    return datum_vorher


# Änderung für v2: Bestehende Hilfsfunktion mit unverändertem Funktionskörper.
def letzte_mindestabnahme(Ident, abnehmer_db):
    mv_jahre = []
    for row in abnehmer_db:
        if row["Ident"] == Ident:
            for key in row.keys():
                if "Mindest-Vertragsleistung-" in key:
                    mv_jahre.append(key)
            mv_jahre.sort()
            i = len(mv_jahre) - 1
            mv_letzte = 0
            while i > -1:
                if row[mv_jahre[i]] > 0:
                    mv_letzte = row[mv_jahre[i]]
                    i = -1
                else:
                    i = i - 1
            if mv_letzte == 0:
                mv_letzte = row["Original-Vertragsleistung"]
    return mv_letzte


def abrechnung_berechnen(abnehmer_db, zaehler_db, abschlag_db, arbeitspreis,
                          grundgebuehr, jahr, mwst_satz, zwischen_aktiv,
                          zwischen_datum, zwischen_mwst_vorhanden, zwischen_mwst):
    # Änderung für v2: Oberflächenwerte als Parameter; Rechenschritte unverändert übernommen.
    abrechnung = abnehmer_aus_daten(abnehmer_db)
    abrechnungsjahr = jahr
    for abrechnung_row in abrechnung:
        for zaehler_row in zaehler_db:
            if abrechnung_row["Ident"] == zaehler_row["Ident"]:
                abrechnung_row["Wärmepreis"] = arbeitspreis
                abrechnung_row["Abrechnungsjahr"] = abrechnungsjahr
                abrechnung_row["Folgejahr"] = int(abrechnungsjahr) + 1
                for abnehmer_row in abnehmer_db:
                    if abrechnung_row["Ident"] == abnehmer_row["Ident"]:
                        abrechnung_row["Mindestvertragsleistung"] = int(abnehmer_row["Mindest-Vertragsleistung-" + abrechnungsjahr])
                abrechnung_row["MwSt-Satz"] = mwst_satz
                abrechnung_row["Mindestvertragssumme"] = round((float(abrechnung_row["Wärmepreis"]) * float(abrechnung_row["Mindestvertragsleistung"]) / 100),2)
                abrechnung_row["Mindestv MwSt"] = mwst_berechnen("mwst", abrechnung_row["Mindestvertragssumme"],mwst_satz,2)
                abrechnung_row["Mindestv Netto"] = mwst_berechnen("netto", abrechnung_row["Mindestvertragssumme"],mwst_satz,2)
                abrechnung_row["Abrechnung Datum von"] = "01.01." + abrechnungsjahr
                abrechnung_row["Abrechnung Datum bis"] = "31.12." + abrechnungsjahr
                abrechnung_row["Datum Zählerstart"] = datum_in_punkt(datum_tage_vorher(abrechnung_row["Abrechnung Datum von"],1))
                zaehlerprojahr = 0
                zaehlerwechsel = False
                for key in zaehler_row.keys():
                    if str(abrechnungsjahr) in key:
                        zaehlerprojahr += 1
                        if "wechsel" in key:
                            zaehlerwechsel = True

                # wenn kein Zähler hinterlegt

                if zaehlerprojahr == 0:
                    print("Zählerstand für Jahr " + str(abrechnungsjahr) + " nicht hinterlegt.")

                # wenn kein Zählerwechsel erfolgt ist

                elif zaehlerwechsel == False:
                    abrechnung_row["Zählerstand Start"] = int(zaehler_row[str(int(abrechnungsjahr) - 1) + "1231-zaehler"])
                    abrechnung_row["Zählerstand Ende"] = int(zaehler_row[str(abrechnungsjahr) + "1231-zaehler"])
                    abrechnung_row["verbrauchte kWh"] = int(abrechnung_row["Zählerstand Ende"]) - int(abrechnung_row["Zählerstand Start"])

                # wenn ein Zählerwechsel erfolgt ist

                elif zaehlerwechsel == True:
                #   print("Es fand im Jahr " + str(abrechnungsjahr) + " ein Zählerwechsel statt.")
                    abrechnung_row["Datum Zählerwechsel"] = str(zaehler_row[abrechnungsjahr + "-datum-zaehlerwechsel"])
                    abrechnung_row["Zählerstand Start alt"] = int(zaehler_row[str(int(abrechnungsjahr) - 1) + "1231-zaehler"])
                    for key in zaehler_row.keys():
                        if (str(abrechnungsjahr)) +"-zaehlerwechsel-alt" in key:
                            abrechnung_row["Zählerstand Wechsel alt"] = int(zaehler_row[key])
                        abrechnung_row["Zählerstand Wechsel neu"] = 0
                        # Zählerstand des neuen Zählers wird mit "0" angenommen. Alternativ kann der erste erfasste Zählerstand aktiviert - durch uncomment der 2 Zeilen
                    abrechnung_row["Zählerstand Ende neu"] = int(zaehler_row[str(abrechnungsjahr) + "1231-zaehler"])
                    abrechnung_row["verbrauchte kWh Zähler alt"] = int(abrechnung_row["Zählerstand Wechsel alt"]) - int(abrechnung_row["Zählerstand Start alt"])
                    abrechnung_row["verbrauchte kWh Zähler neu"] = int(abrechnung_row["Zählerstand Ende neu"]) - int(abrechnung_row["Zählerstand Wechsel neu"])
                    abrechnung_row["verbrauchte kWh"] = (int(abrechnung_row["Zählerstand Ende neu"]) - int(abrechnung_row["Zählerstand Wechsel neu"]) + (abrechnung_row["Zählerstand Wechsel alt"]) - int(abrechnung_row["Zählerstand Start alt"]))
                abrechnung_row["Wärmekosten tats Verbrauch"] = round((int(abrechnung_row["verbrauchte kWh"]) * arbeitspreis / 100),2)
                abrechnung_row["Wärmekosten tats Verbr MwSt"] = mwst_berechnen("mwst",abrechnung_row["Wärmekosten tats Verbrauch"],mwst_satz,2)
                abrechnung_row["Wärmekosten tats Verbr Netto"] = mwst_berechnen("netto",abrechnung_row["Wärmekosten tats Verbrauch"],mwst_satz,2)
        for abschlag_row in abschlag_db:
            if abrechnung_row["Ident"] == abschlag_row["Ident"]:
                abschlag_quartal = float(abschlag_row["Abschlag-" + str(abrechnungsjahr)])
                abrechnung_row["Abschlag Quartal"] = abschlag_quartal
                abrechnung_row["Zahlung Abschläge"] = abschlag_quartal * 4
                abrechnung_row["Zahlung Abschläge MwSt"] =  mwst_berechnen("mwst",abrechnung_row["Zahlung Abschläge"],mwst_satz,2)
                abrechnung_row["Zahlung Abschläge Netto"] =  mwst_berechnen("netto",abrechnung_row["Zahlung Abschläge"],mwst_satz,2)
                abrechnung_row["Grundgebühr"] = grundgebuehr * 12
                abrechnung_row["Grundgebühr MwSt"] = mwst_berechnen("mwst",abrechnung_row["Grundgebühr"],mwst_satz,2)
                abrechnung_row["Grundgebühr Netto"] = mwst_berechnen("netto",abrechnung_row["Grundgebühr"],mwst_satz,2)
                abrechnung_row["Grundgebühr bez"] = grundgebuehr * 12
                abrechnung_row["Grundgebühr bez MwSt"] = mwst_berechnen("mwst",abrechnung_row["Grundgebühr bez"],mwst_satz,2)
                abrechnung_row["Grundgebühr bez Netto"] = mwst_berechnen("netto",abrechnung_row["Grundgebühr bez"],mwst_satz,2)                 
        for abnehmer_db_row in abnehmer_db:
            if abrechnung_row["Ident"] == abnehmer_db_row["Ident"]:
                abrechnung_row["Mindestvertragsleistung"] = int(abnehmer_db_row["Mindest-Vertragsleistung-" + str(abrechnungsjahr)])
                if int(abrechnung_row["verbrauchte kWh"]) <= int(abrechnung_row["Mindestvertragsleistung"]):
                    abrechnung_row["Kosten Wärme"] = abrechnung_row["Mindestvertragssumme"]
                    abrechnung_row["Abr nach Mindestabnahme"] = "[x]"
                    abrechnung_row["Abr nach tats Verbrauch"] = ""
                else:
                    abrechnung_row["Kosten Wärme"] = abrechnung_row["Wärmekosten tats Verbrauch"]
                    abrechnung_row["Abr nach Mindestabnahme"] = ""
                    abrechnung_row["Abr nach tats Verbrauch"] = "[x]"
                abrechnung_row["Jahresabrechnung"] = round((float(abrechnung_row["Kosten Wärme"]) - abrechnung_row["Zahlung Abschläge"]),2)
                if abrechnung_row["Abr nach Mindestabnahme"] == "[x]" and -0.03 < float(abrechnung_row["Jahresabrechnung"]) < 0.03:
                    abrechnung_row["Jahresabrechnung"] = 0
                abrechnung_row["Jahresabrechnung MwSt"] = mwst_berechnen("mwst",abrechnung_row["Jahresabrechnung"],mwst_satz,2)
                abrechnung_row["Jahresabrechnung Netto"] = mwst_berechnen("netto",abrechnung_row["Jahresabrechnung"],mwst_satz,2)

                # Berechnung neuer Abschlag
                if abrechnung_row["Abschlag Quartal"] == 0:
                    abrechnung_row["neuer Abschlag"] = round((int(letzte_mindestabnahme(abnehmer_db_row["Ident"], abnehmer_db)) * arbeitspreis / 100 / 4),2)
                elif abrechnung_row["Mindestvertragsleistung"] < int(abnehmer_db_row["Mindest-Vertragsleistung-" + str(int(abrechnungsjahr) - 1)]) and abrechnung_row["Mindestvertragsleistung"] != 0:
                    abrechnung_row["neuer Abschlag"] = round(float((abrechnung_row["Mindestvertragsleistung"]) * arbeitspreis / 100 / 4),2)

                # Abschlag nur verringern, wenn neuer Abschlag nicht unter Mindestabnahme ist

                elif abrechnung_row["Jahresabrechnung"] < 0:
                    if abschlag_quartal - 50 < abrechnung_row["Mindestvertragssumme"] / 4:
                        abrechnung_row["neuer Abschlag"] = round(float((abrechnung_row["Mindestvertragsleistung"]) * arbeitspreis / 100 / 4),2)
                    else:
                        abrechnung_row["neuer Abschlag"] = abschlag_quartal - 50    
                elif abrechnung_row["Jahresabrechnung"] > 1000:
                    abrechnung_row["neuer Abschlag"] = abschlag_quartal + 150
                elif abrechnung_row["Jahresabrechnung"] > 600:
                    abrechnung_row["neuer Abschlag"] = abschlag_quartal + 100
                elif abrechnung_row["Jahresabrechnung"] > 500:
                    abrechnung_row["neuer Abschlag"] = abschlag_quartal + 80
                elif abrechnung_row["Jahresabrechnung"] > 400:
                    abrechnung_row["neuer Abschlag"] = abschlag_quartal + 70
                elif abrechnung_row["Jahresabrechnung"] > 300:
                    abrechnung_row["neuer Abschlag"] = abschlag_quartal + 50
                else:
                    abrechnung_row["neuer Abschlag"] = abschlag_quartal
                # Wenn der neue Abschlag unter der Mindestabnahme liegt, dann wird der Abschlag an die Mindestabnahme angeglichen
                if abrechnung_row["neuer Abschlag"] * 4 < round(float((abrechnung_row["Mindestvertragsleistung"]) * arbeitspreis / 100 / 4),2):
                    abrechnung_row["neuer Abschlag"] = round(float((abrechnung_row["Mindestvertragsleistung"]) * arbeitspreis / 100 / 4),2)

# Weitere Daten bei Zwischenablesung

    if zwischen_aktiv == True and zwischen_datum != None and zwischen_mwst_vorhanden:
        for abrechnung_row in abrechnung:
            for zaehler_row in zaehler_db:
                if abrechnung_row["Ident"] == zaehler_row["Ident"]:
                    abrechnung_row["Datum Zwischenablesung"] = zwischen_datum
                    abrechnung_row["Zählerstand Zwischenablesung"] = zaehler_row[datum_in_string(zwischen_datum) + "-zaehler"]
                    abrechnung_row["Wärmeverbrauch bis ZA"] = int(abrechnung_row["Zählerstand Zwischenablesung"]) - int(abrechnung_row["Zählerstand Start"])
                    abrechnung_row["Wärmeverbrauch ab ZA"] = int(abrechnung_row["Zählerstand Ende"]) - int(abrechnung_row["Zählerstand Zwischenablesung"])
                    abrechnung_row["ZA MwSt"] = zwischen_mwst
                    abrechnung_row["Mindestvertragssumme bis ZA"] = round(abrechnung_row["Mindestvertragssumme"] / 12 * int(zwischen_datum[3:5]),2)
                    abrechnung_row["Mindestvertragssumme bis ZA MwSt"] = mwst_berechnen("mwst",abrechnung_row["Mindestvertragssumme bis ZA"],zwischen_mwst,2)
                    abrechnung_row["Mindestvertragssumme bis ZA Netto"] = mwst_berechnen("netto",abrechnung_row["Mindestvertragssumme bis ZA"],zwischen_mwst,2)
                    abrechnung_row["Wärmekosten tats Verbr bis ZA"] = round((int(abrechnung_row["Wärmeverbrauch bis ZA"]) * arbeitspreis / 100),2)
                    abrechnung_row["Wärmekosten tats Verbr bis ZA MwSt"] = mwst_berechnen("mwst",abrechnung_row["Wärmekosten tats Verbr bis ZA"],zwischen_mwst,2)
                    abrechnung_row["Wärmekosten tats Verbr bis ZA Netto"] = mwst_berechnen("netto",abrechnung_row["Wärmekosten tats Verbr bis ZA"],zwischen_mwst,2)
                    abrechnung_row["Zahlung Abschläge bis ZA"] = round((abrechnung_row["Zahlung Abschläge"] / 12 * int(zwischen_datum[3:5])),2)
                    abrechnung_row["Zahlung Abschläge bis ZA MwSt"] = mwst_berechnen("mwst",abrechnung_row["Zahlung Abschläge bis ZA"],zwischen_mwst,2)
                    abrechnung_row["Zahlung Abschläge bis ZA Netto"] = mwst_berechnen("netto",abrechnung_row["Zahlung Abschläge bis ZA"],zwischen_mwst,2)
                    abrechnung_row["Grundgebühr bis ZA"] = grundgebuehr * int(zwischen_datum[3:5])
                    abrechnung_row["Grundgebühr bis ZA MwSt"] = mwst_berechnen("mwst",abrechnung_row["Grundgebühr bis ZA"],zwischen_mwst,2)
                    abrechnung_row["Grundgebühr bis ZA Netto"] = mwst_berechnen("netto",abrechnung_row["Grundgebühr bis ZA"],zwischen_mwst,2)
                    abrechnung_row["Grundgebühr bez bis ZA"] = grundgebuehr * int(zwischen_datum[3:5])
                    abrechnung_row["Grundgebühr bez bis ZA MwSt"] = mwst_berechnen("mwst",abrechnung_row["Grundgebühr bez bis ZA"],zwischen_mwst,2)
                    abrechnung_row["Grundgebühr bez bis ZA Netto"] = mwst_berechnen("netto",abrechnung_row["Grundgebühr bez bis ZA"],zwischen_mwst,2)
                    if abrechnung_row["Abr nach Mindestabnahme"] == "[x]":
                        abrechnung_row["Kosten Wärme bis ZA"] = abrechnung_row["Mindestvertragssumme bis ZA"]
                    else:
                        abrechnung_row["Kosten Wärme bis ZA"] = abrechnung_row["Wärmekosten tats Verbr bis ZA"]
                    abrechnung_row["Kosten Wärme bis ZA MwSt"] = mwst_berechnen("mwst",abrechnung_row["Kosten Wärme bis ZA"],zwischen_mwst,2)
                    abrechnung_row["Kosten Wärme bis ZA Netto"] = mwst_berechnen("netto",abrechnung_row["Kosten Wärme bis ZA"],zwischen_mwst,2)
                    abrechnung_row["Abrechnung bis ZA"] = round((float(abrechnung_row["Kosten Wärme bis ZA"]) - float(abrechnung_row["Zahlung Abschläge bis ZA"])),2)
                    abrechnung_row["Abrechnung bis ZA MwSt"] = mwst_berechnen("mwst",abrechnung_row["Abrechnung bis ZA"],zwischen_mwst,2)
                    abrechnung_row["Abrechnung bis ZA Netto"] = mwst_berechnen("netto",abrechnung_row["Abrechnung bis ZA"],zwischen_mwst,2)
                    if abrechnung_row["Abr nach Mindestabnahme"] == "[x]" and -0.03 < float(abrechnung_row["Abrechnung bis ZA"]) < 0.03:
                        abrechnung_row["Abrechnung bis ZA"] = 0
                        abrechnung_row["Abrechnung bis ZA MwSt"] = 0
                        abrechnung_row["Abrechnung bis ZA Netto"] = 0

                    abrechnung_row["Mindestvertragssumme ab ZA"] = round(abrechnung_row["Mindestvertragssumme"] / 12 * (12 - int(zwischen_datum[3:5])),2)
                    abrechnung_row["Mindestvertragssumme ab ZA MwSt"] = mwst_berechnen("mwst",abrechnung_row["Mindestvertragssumme ab ZA"],mwst_satz,2)
                    abrechnung_row["Mindestvertragssumme ab ZA Netto"] = mwst_berechnen("netto",abrechnung_row["Mindestvertragssumme ab ZA"],mwst_satz,2)
                    abrechnung_row["Wärmekosten tats Verbr ab ZA"] = round((int(abrechnung_row["Wärmeverbrauch ab ZA"]) * arbeitspreis / 100),2)
                    abrechnung_row["Wärmekosten tats Verbr ab ZA MwSt"] = mwst_berechnen("mwst",abrechnung_row["Wärmekosten tats Verbr ab ZA"],mwst_satz,2)
                    abrechnung_row["Wärmekosten tats Verbr ab ZA Netto"] = mwst_berechnen("netto",abrechnung_row["Wärmekosten tats Verbr ab ZA"],mwst_satz,2)
                    abrechnung_row["Zahlung Abschläge ab ZA"] = round((abrechnung_row["Zahlung Abschläge"] / 12 * (12 - int(zwischen_datum[3:5]))),2)
                    abrechnung_row["Zahlung Abschläge ab ZA MwSt"] = mwst_berechnen("mwst",abrechnung_row["Zahlung Abschläge ab ZA"],mwst_satz,2)
                    abrechnung_row["Zahlung Abschläge ab ZA Netto"] = mwst_berechnen("netto",abrechnung_row["Zahlung Abschläge ab ZA"],mwst_satz,2)
                    abrechnung_row["Grundgebühr ab ZA"] = grundgebuehr * (12 - int(zwischen_datum[3:5]))
                    abrechnung_row["Grundgebühr ab ZA MwSt"] = mwst_berechnen("mwst",abrechnung_row["Grundgebühr ab ZA"],mwst_satz,2)
                    abrechnung_row["Grundgebühr ab ZA Netto"] = mwst_berechnen("netto",abrechnung_row["Grundgebühr ab ZA"],mwst_satz,2)
                    abrechnung_row["Grundgebühr bez ab ZA"] = grundgebuehr * (12 - int(zwischen_datum[3:5]))
                    abrechnung_row["Grundgebühr bez ab ZA MwSt"] = mwst_berechnen("mwst",abrechnung_row["Grundgebühr bez ab ZA"],mwst_satz,2)
                    abrechnung_row["Grundgebühr bez ab ZA Netto"] = mwst_berechnen("netto",abrechnung_row["Grundgebühr bez ab ZA"],mwst_satz,2)
                    if abrechnung_row["Abr nach Mindestabnahme"] == "[x]":
                        abrechnung_row["Kosten Wärme ab ZA"] = abrechnung_row["Mindestvertragssumme ab ZA"]
                    else:
                        abrechnung_row["Kosten Wärme ab ZA"] = abrechnung_row["Wärmekosten tats Verbr ab ZA"]
                    abrechnung_row["Kosten Wärme ab ZA MwSt"] = mwst_berechnen("mwst",abrechnung_row["Kosten Wärme ab ZA"],mwst_satz,2)
                    abrechnung_row["Kosten Wärme ab ZA Netto"] =  mwst_berechnen("netto",abrechnung_row["Kosten Wärme ab ZA"],mwst_satz,2)
 
                    abrechnung_row["Abrechnung ab ZA"] = round((float(abrechnung_row["Kosten Wärme ab ZA"]) - float(abrechnung_row["Zahlung Abschläge ab ZA"])),2)
                    abrechnung_row["Abrechnung ab ZA MwSt"] = mwst_berechnen("mwst",abrechnung_row["Abrechnung ab ZA"],mwst_satz,2)
                    abrechnung_row["Abrechnung ab ZA Netto"] =  mwst_berechnen("netto",abrechnung_row["Abrechnung ab ZA"],mwst_satz,2)                

                    if abrechnung_row["Abr nach Mindestabnahme"] == "[x]" and -0.03 < float(abrechnung_row["Abrechnung ab ZA"]) < 0.03:
                        abrechnung_row["Abrechnung ab ZA"] = 0
                        abrechnung_row["Abrechnung ab ZA MwSt"] = 0
                        abrechnung_row["Abrechnung ab ZA Netto"] = 0

#    abrechnung_grid_update(abrechnung)
    # Änderung für v2: Berechnungsergebnis an die Oberfläche zurückgeben.
    return abrechnung


def rueckverguetung_vorbereiten(abrechnung_datei, jahr):
    # Änderung für v2: Bisherigen Tabellenaufbau ohne Datei- und GUI-Zugriff ausführen.
    rueckv_tabelle = []
    for row in abrechnung_datei:

        # Standard MwSt-Satz wird von erster Zeile der Abrechnung ausgelesen - ist auch MwSt ab ZA

        rueckv_mwst = row["MwSt-Satz"]
        rueckv_tabelle_element = {}
        for key,value in row.items():
            if key == "Ident" or key == "Name" or key == "Vorname":
                rueckv_tabelle_element[key] = value

            # Wenn Zwischenabrechnung in Jahresabrechnung erkannt

            if "Abrechnung ab ZA" in abrechnung_datei[0].keys():
                #MwSt bis ZA
                rueckv_mwst2 = row["ZA MwSt"]
                if key == "Grundgebühr bis ZA":
                    rueckv_tabelle_element["Abrechnungsjahr"] = jahr
                    rueckv_tabelle_element["MwSt bis ZA"] = rueckv_mwst2
                    rueckv_tabelle_element["Grundgebühr bis ZA"] = float(value)
                    rueckv_tabelle_element["Grundgebühr bis ZA MwSt"] = mwst_berechnen("mwst",value,rueckv_mwst2,2)
                    rueckv_tabelle_element["Grundgebühr bis ZA Netto"] = mwst_berechnen("netto",value,rueckv_mwst2,2)
                if key == "Kosten Wärme bis ZA":
                    rueckv_tabelle_element["Wärmeumsatz bis ZA"] = float(value)
                    rueckv_tabelle_element["Wärmeumsatz bis ZA MwSt"] = mwst_berechnen("mwst",value,rueckv_mwst2,2)
                    rueckv_tabelle_element["Wärmeumsatz bis ZA Netto"] = mwst_berechnen("netto",value,rueckv_mwst2,2)
                if key == "Grundgebühr ab ZA":
                    rueckv_tabelle_element["MwSt ab ZA"] = rueckv_mwst
                    rueckv_tabelle_element["Grundgebühr ab ZA"] = float(value)
                    rueckv_tabelle_element["Grundgebühr ab ZA MwSt"] = mwst_berechnen("mwst",value,rueckv_mwst,2)
                    rueckv_tabelle_element["Grundgebühr ab ZA Netto"] = mwst_berechnen("netto",value,rueckv_mwst,2)
                if key == "Kosten Wärme ab ZA":
                    rueckv_tabelle_element["Wärmeumsatz ab ZA"] = float(value)
                    rueckv_tabelle_element["Wärmeumsatz ab ZA MwSt"] = mwst_berechnen("mwst",value,rueckv_mwst,2)
                    rueckv_tabelle_element["Wärmeumsatz ab ZA Netto"] = mwst_berechnen("netto",value,rueckv_mwst,2)

            # Wenn keine Zwischnabrechnung erkannt

            else:
                if key == "Grundgebühr bez":
                    rueckv_tabelle_element["MwSt-Satz"] = int(rueckv_mwst)
                    rueckv_tabelle_element["Grundgebühr"] = float(value)
                    rueckv_tabelle_element["Grundgebühr MwSt"] = mwst_berechnen("mwst",value,rueckv_mwst,2)
                    rueckv_tabelle_element["Grundgebühr Netto"] = mwst_berechnen("netto",value,rueckv_mwst,2)
                if key == "Kosten Wärme":
                    rueckv_tabelle_element["Wärmeumsatz"] = float(value)
                    rueckv_tabelle_element["Wärmeumsatz MwSt"] = mwst_berechnen("mwst",value,rueckv_mwst,2)
                    rueckv_tabelle_element["Wärmeumsatz Netto"] = mwst_berechnen("netto",value,rueckv_mwst,2)
        rueckv_tabelle_element["Materialumsatz"] = float(0)
        rueckv_tabelle.append(rueckv_tabelle_element)
    return rueckv_tabelle


def rueckverguetung_berechnen(table, prozent, beschlussdatum, rueckv_mwst, rueckv_mwst2=None):
    # Änderung für v2: Bisherige Rechenregeln unverändert mit expliziten Eingaben verwenden.
    mwst_material = 19
    for row in table:
        row["Materialumsatz MwSt"] = mwst_berechnen("mwst",row["Materialumsatz"], mwst_material,2)
        row["Materialumsatz Netto"] = mwst_berechnen("netto",row["Materialumsatz"], mwst_material,2)

        # Wenn Zwischenablesung vorhanden

        if "MwSt bis ZA" in table[0].keys():
            row["Umsatz bis ZA"] = round(float(row["Grundgebühr bis ZA"]) + float(row["Wärmeumsatz bis ZA"]),2)
            row["Umsatz bis ZA MwSt"] = mwst_berechnen("mwst",row["Umsatz bis ZA"],rueckv_mwst2,2)
            row["Umsatz bis ZA Netto"] = mwst_berechnen("netto",row["Umsatz bis ZA"],rueckv_mwst2,2)
            row["Umsatz ab ZA"] = round(float(row["Grundgebühr ab ZA"]) + float(row["Wärmeumsatz ab ZA"]) + float(row["Materialumsatz"]),2)
            row["Umsatz ab ZA MwSt"] = mwst_berechnen("mwst",row["Umsatz ab ZA"],rueckv_mwst,2)
            row["Umsatz ab ZA Netto"] = mwst_berechnen("netto",row["Umsatz ab ZA"],rueckv_mwst,2)
            row["Rückvergütungssatz"] = round((float(prozent)),2)
            row["Datum Beschluss"] = str(beschlussdatum)
            row["Rückvergütung bis ZA"] = round(float(row["Umsatz bis ZA"]) / 100 * float(row["Rückvergütungssatz"]),2)
            row["Rückvergütung bis ZA MwSt"] = mwst_berechnen("mwst",row["Rückvergütung bis ZA"],rueckv_mwst2,2)
            row["Rückvergütung bis ZA Netto"] = mwst_berechnen("netto",row["Rückvergütung bis ZA"],rueckv_mwst2,2)
            row["Rückvergütung ab ZA"] = round(float(row["Umsatz ab ZA"]) / 100 * float(row["Rückvergütungssatz"]),2)
            row["Rückvergütung ab ZA MwSt"] = mwst_berechnen("mwst",row["Rückvergütung ab ZA"],rueckv_mwst,2)
            row["Rückvergütung ab ZA Netto"] = mwst_berechnen("netto",row["Rückvergütung ab ZA"],rueckv_mwst,2)
            row["Rückvergütung gesamt"] = round(row["Rückvergütung bis ZA"] + row["Rückvergütung ab ZA"],2)

        # Wenn Zwischenablesung nicht vorhanden

        else:
            row["Gesamtumsatz"] = round(float(row["Grundgebühr"]) + float(row["Wärmeumsatz"]) + float(row["Materialumsatz"]),2)
            row["Gesamtumsatz MwSt"] = mwst_berechnen("mwst",row["Gesamtumsatz"],rueckv_mwst,2)
            row["Gesamtumsatz Netto"] = mwst_berechnen("netto",row["Gesamtumsatz"],rueckv_mwst,2)
            row["Rückvergütungssatz"] = round((float(prozent)),2)
            row["Datum Beschluss"] = str(beschlussdatum)
            row["Rückvergütung"] = round(float(row["Gesamtumsatz"]) / 100 * float(row["Rückvergütungssatz"]),2)
            row["Rückvergütung MwSt"] = mwst_berechnen("mwst",row["Rückvergütung"],rueckv_mwst,2)
            row["Rückvergütung Netto"] = mwst_berechnen("netto",row["Rückvergütung"],rueckv_mwst,2)
    return table



# Änderung für v2: Unveränderte Rundungsfunktion aus ana.py.
def round_half_up(n, ndigits=0):
    factor = Decimal('1.' + '0' * ndigits) if ndigits > 0 else Decimal('1')
    return float(Decimal(str(n)).quantize(factor, rounding=ROUND_HALF_UP))

