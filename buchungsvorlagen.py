"""Änderung für v2: CSV-Buchungsvorlagen ohne Oberfläche oder Dateizugriffe erstellen."""

from decimal import Decimal

from datenhaltung import dictlist_to_csv
from berechnungen import round_half_up


def grundgebuehr_csv(konto_db, grundgebuehr, betreiber_iban,
                     betreiber_name, betreiber_glaeubigerid):
    # Änderung für v2: Bestehende Schleifen, Felder, Filter und Formatierung unverändert übernehmen.
    csvgrundgebuehr = []
    for row in konto_db:
        csvzeile = {}
        for key, value in row.items():
            if key == "Zahlungspflichtiger":
                csvzeile["Bezeichnung der Basislastschrift"] = value
                csvzeile[key] = value
                csvzeile["Adresse"] = ""
                csvzeile["Länder-Kennzeichen"] = ""
                csvzeile["Land"] = ""
            if key == "IBAN":
                csvzeile["IBAN des Zahlungspflichtigen"] = value.replace(" ","")
            if key == "BIC":
                csvzeile[key] = value
            if key == "Bank":
                csvzeile["Bei Kreditinstitut"] = value
                csvzeile["Betrag"] = str(grundgebuehr).replace(".",",")
                csvzeile["Verwendungszweck 1"] = "Grundgebuehr NWSeG @MMJJ@"
                csvzeile["Verwendungszweck 2"] = ""
                csvzeile["IBAN des Zahlungsempfängers"] = betreiber_iban.replace(" ","")
                csvzeile["Zahlungsempfänger"] = betreiber_name
                csvzeile["Mandatsreferenz"] = str(csvzeile["Zahlungspflichtiger"]).replace(" ",",")
            if key == "Datum SEPA-Auftrag":
                csvzeile["Unterschrieben am"] = value
                csvzeile["Gläubiger ID des Zahlungsempfängers"] = betreiber_glaeubigerid
        csvgrundgebuehr.append(csvzeile)
    csv_download = dictlist_to_csv(csvgrundgebuehr)
    return csv_download


def abschlag_csv(konto_db, abschlag_db, abschlagsjahr,
                 quartal, betreiber_iban, betreiber_name, betreiber_glaeubigerid):
    # Änderung für v2: Bestehende Schleifen, Felder, Filter und Formatierung unverändert übernehmen.
    csvabschlag = []
    for row in konto_db:
        csvzeile = {}
        for key, value in row.items():
            if key == "Zahlungspflichtiger":
                csvzeile["Bezeichnung der Basislastschrift"] = value
                csvzeile[key] = value
                csvzeile["Adresse"] = ""
                csvzeile["Länder-Kennzeichen"] = ""
                csvzeile["Land"] = ""
            if key == "IBAN":
                csvzeile["IBAN des Zahlungspflichtigen"] = value.replace(" ","")
            if key == "BIC":
                csvzeile[key] = value
            if key == "Bank":
                csvzeile["Bei Kreditinstitut"] = value
                for abschlagrow in abschlag_db:
                    if row["Ident"] == abschlagrow["Ident"]:
                        csvzeile["Betrag"] = str(abschlagrow["Abschlag-" + abschlagsjahr]).replace(".",",")
                csvzeile["Verwendungszweck 1"] = "Abschlag NWSeG " + quartal + "/" + abschlagsjahr
                csvzeile["Verwendungszweck 2"] = ""
                csvzeile["IBAN des Zahlungsempfängers"] = betreiber_iban.replace(" ","")
                csvzeile["Zahlungsempfänger"] = betreiber_name
                csvzeile["Mandatsreferenz"] = str(csvzeile["Zahlungspflichtiger"]).replace(" ",",")
            if key == "Datum SEPA-Auftrag":
                csvzeile["Unterschrieben am"] = value
                csvzeile["Gläubiger ID des Zahlungsemfängers"] = betreiber_glaeubigerid
        csvabschlag.append(csvzeile)
    csv_download = dictlist_to_csv(csvabschlag)
    return csv_download


def abrechnung_lastschrift_csv(konto_db, abrechnung, abrechnungsjahr,
                               vonnetto, betreiber_iban, betreiber_name, betreiber_glaeubigerid):
    # Änderung für v2: Bestehende Schleifen, Felder, Filter und Formatierung unverändert übernehmen.
    csvlastschrift = []
    for row in konto_db:
        csvzeile = {}
        for abrechnungrow in abrechnung:
            if row["Ident"] == abrechnungrow["Ident"] and float(abrechnungrow["Jahresabrechnung"]) > 0:
                for key, value in row.items():
                    if key == "Zahlungspflichtiger":
                        csvzeile["Bezeichnung der Basislastschrift"] = value
                        csvzeile[key] = value
                        csvzeile["Adresse"] = ""
                        csvzeile["Länder-Kennzeichen"] = ""
                        csvzeile["Land"] = ""
                    if key == "IBAN":
                        csvzeile["IBAN des Zahlungspflichtigen"] = value.replace(" ","")
                    if key == "BIC":
                        csvzeile[key] = value
                    if key == "Bank":
                        csvzeile["Bei Kreditinstitut"] = value
                        if vonnetto == True:
                            # Wenn Zwischenablesung mit unterschiedlichen Mehrwertsteuersätzen im Jahr erfolgt ist
                            if "ZA MwSt" in abrechnung[0].keys():
                                abrechnung1brutto = round_half_up((Decimal(abrechnungrow["Abrechnung bis ZA Netto"]) * (1 + Decimal(abrechnungrow["ZA MwSt"]) / 100)),2)
                                csvzeile["Float 1"] = Decimal(abrechnungrow["Abrechnung bis ZA Netto"])
                                csvzeile["Brutto 1"] = Decimal(abrechnungrow["Abrechnung bis ZA Netto"]) * (1 + Decimal(abrechnungrow["ZA MwSt"]) / 100)
                                csvzeile["Brutto gerundet 1"] = abrechnung1brutto
                                abrechnung2brutto = round_half_up((Decimal(abrechnungrow["Abrechnung ab ZA Netto"]) * (1 + Decimal(abrechnungrow["MwSt-Satz"]) / 100)),2)
                                csvzeile["Float 2"] = Decimal(abrechnungrow["Abrechnung ab ZA Netto"])
                                csvzeile["Brutto 2"] = Decimal(abrechnungrow["Abrechnung ab ZA Netto"]) * (1 + Decimal(abrechnungrow["MwSt-Satz"]) / 100)
                                csvzeile["MwSt Faktor"] = 1 + Decimal(abrechnungrow["MwSt-Satz"]) / 100
                                csvzeile["Brutto gerundet 2"] = abrechnung2brutto
                                csvzeile["Betrag"] = str(round_half_up(Decimal(abrechnung1brutto + abrechnung2brutto),2)).replace(".",",")
                            else:
                                csvzeile["Betrag"] = str(round_half_up((Decimal(abrechnungrow["Jahresabrechnung Netto"]) * (1 + Decimal(abrechnungrow["MwSt-Satz"]) / 100)),2)).replace(".",",")
                        else:
                            csvzeile["Betrag"] = abrechnungrow["Jahresabrechnung"].replace(".",",")
                        csvzeile["Verwendungszweck 1"] = "NWS Jahresabrechnung " + str(abrechnungsjahr)
                        csvzeile["Verwendungszweck 2"] = ""
                        csvzeile["IBAN des Zahlungsempfängers"] = betreiber_iban.replace(" ","")
                        csvzeile["Zahlungsempfänger"] = betreiber_name
                        csvzeile["Mandatsreferenz"] = str(csvzeile["Zahlungspflichtiger"]).replace(" ",",")
                    if key == "Datum SEPA-Auftrag":
                        csvzeile["Unterschrieben am"] = value
                        csvzeile["Gläubiger ID des Zahlungsempfängers"] = betreiber_glaeubigerid
                csvlastschrift.append(csvzeile)
    csv_download = dictlist_to_csv(csvlastschrift)
    return csv_download 


def abrechnung_ueberweisung_csv(konto_db, abrechnung, abrechnungsjahr,
                                vonnetto, betreiber_iban, betreiber_name):
    # Änderung für v2: Bestehende Schleifen, Felder, Filter und Formatierung unverändert übernehmen.
    csvueberweisung = []
    for row in konto_db:
        csvzeile = {}
        for abrechnungrow in abrechnung:
            if row["Ident"] == abrechnungrow["Ident"] and float(abrechnungrow["Jahresabrechnung"]) < 0:
                for key, value in row.items():
                    if key == "Zahlungspflichtiger":
                        csvzeile["Kurzbezeichnung"] = value
                        csvzeile["Empfänger"] = value
                        csvzeile["Straße/PLZ/Ort"] = ""
                        csvzeile["Länder-Kennzeichen"] = ""
                        csvzeile["Länderbezeichnung"] = ""
                    if key == "IBAN":
                        csvzeile["IBAN des Empfängers"] = value.replace(" ","")
                    if key == "BIC":
                        csvzeile[key] = value
                    if key == "Bank":
                        csvzeile["Bei Kreditinstitut"] = value
                        if vonnetto == True:
                            # Wenn Zwischenablesung mit unterschiedlichen Mehrwertsteuersätzen im Jahr erfolgt ist
                            if "ZA MwSt" in abrechnung[0].keys():
                                abrechnung1brutto = round_half_up(Decimal(abrechnungrow["Abrechnung bis ZA Netto"]) * (1 + Decimal(abrechnungrow["ZA MwSt"]) / 100),2)
                                abrechnung2brutto = round_half_up(Decimal(abrechnungrow["Abrechnung ab ZA Netto"]) * (1 + Decimal(abrechnungrow["MwSt-Satz"]) / 100),2)
                                csvzeile["Betrag"] = str(round_half_up(Decimal(abrechnung1brutto + abrechnung2brutto),2)).replace(".",",")
                            else:
                                csvzeile["Betrag"] = str(round_half_up(((Decimal(abrechnungrow["Jahresabrechnung Netto"]) * (1 + Decimal(abrechnungrow["MwSt-Satz"]) / 100)) * -1),2)).replace(".",",")
                        else:
                            csvzeile["Betrag"] = str((Decimal(abrechnungrow["Jahresabrechnung"]) * -1)).replace(".",",")
                        csvzeile["verschl. Verwendungszweck"] = ""
                        csvzeile["Bezeichnung verschl. Verwendungszweck"] = ""
                        csvzeile["Verwendungszweck 1"] = "NWS Jahresabrechnung " + str(abrechnungsjahr)
                        csvzeile["Verwendungszweck 2"] = ""
                        csvzeile["Kundenreferenz"] = ""
                        csvzeile["IBAN des Auftraggebers"] = betreiber_iban.replace(" ","")
                        csvzeile["Auftraggeber"] = betreiber_name
                csvueberweisung.append(csvzeile)
    csv_download = dictlist_to_csv(csvueberweisung)
    return csv_download 


def rueckverguetung_csv(konto_db, rueckv, rueckvjahr,
                        vonnetto, betreiber_iban, betreiber_name):
    # Änderung für v2: Exportablauf beibehalten; die unten markierten Fehler gezielt korrigieren.
    csvrueckv = []
    for row in konto_db:
        csvzeile = {}
        for rueckvrow in rueckv:
            if row["Ident"] == rueckvrow["Ident"]:
                for key, value in row.items():
                    if key == "Zahlungspflichtiger":
                        csvzeile["Kurzbezeichnung"] = value
                        csvzeile["Empfänger"] = value
                        csvzeile["Straße/PLZ/Ort"] = ""
                        csvzeile["Länder-Kennzeichen"] = ""
                        csvzeile["Länderbezeichnung"] = ""
                    if key == "IBAN":
                        csvzeile["IBAN des Empfängers"] = value.replace(" ","")
                    if key == "BIC":
                        csvzeile[key] = value
                    if key == "Bank":
                        csvzeile["Bei Kreditinstitut"] = value
                        if vonnetto == True:
                            # Wenn Zwischenablesung mit unterschiedlichen Mehrwertsteuersätzen im Jahr erfolgt ist
                            if "MwSt bis ZA" in rueckv[0].keys():
                                rueckv1brutto = round_half_up(Decimal(rueckvrow["Rückvergütung bis ZA Netto"]) * (1 + Decimal(rueckvrow["MwSt bis ZA"]) / 100),2)
                                rueckv2brutto = round_half_up(Decimal(rueckvrow["Rückvergütung ab ZA Netto"]) * (1 + Decimal(rueckvrow["MwSt ab ZA"]) / 100),2)
                                csvzeile["Betrag"] = str(round_half_up(Decimal(rueckv1brutto + rueckv2brutto),2)).replace(".",",")
                            else:

                                # Fehlerkorrektur: CSV-Text vor der Multiplikation in Decimal umwandeln.
                                csvzeile["Betrag"] = str(round_half_up(Decimal(rueckvrow["Rückvergütung Netto"]) * (1 + Decimal(rueckvrow["MwSt-Satz"]) / 100),2)).replace(".",",")
                        else:
                            # Fehlerkorrektur: Bei Zwischenablesung steht der Gesamtbetrag im eigenen Feld.
                            if "MwSt bis ZA" in rueckv[0].keys():
                                csvzeile["Betrag"] = str(rueckvrow["Rückvergütung gesamt"]).replace(".",",")
                            else:
                                csvzeile["Betrag"] = str(rueckvrow["Rückvergütung"]).replace(".",",")
                        csvzeile["verschl. Verwendungszweck"] = ""
                        csvzeile["Bezeichnung verschl. Verwendungszweck"] = ""
                        csvzeile["Verwendungszweck 1"] = "NWS gen. Rückv. " + str(rueckvjahr)
                        csvzeile["Verwendungszweck 2"] = ""
                        csvzeile["Kundenreferenz"] = ""
                        csvzeile["IBAN des Auftraggebers"] = betreiber_iban.replace(" ","")
                        csvzeile["Auftraggeber"] = betreiber_name
                csvrueckv.append(csvzeile)
    csv_download = dictlist_to_csv(csvrueckv)
    return csv_download 


