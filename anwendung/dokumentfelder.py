# Änderung für v2: In anwendung/ eingeordnet; Modul- und Dateipfade angepasst.
"""Änderung für v2: Word-Feldformatierung unverändert aus ana.py ausgelagert.

Die Funktionen benötigen weder NiceGUI noch Microsoft Word.
"""


# Änderung für v2: Alle folgenden Funktionskörper entsprechen der Ausgangsversion.
def format_fuer_serienbrief(liste):
    for row in liste:
        for key,value in row.items():
            if isinstance(row[key],(float, int)) == True:
                row[key] = f"{row[key]:,.2f}"
                row[key] = str(row[key]).replace('.', ',')
                row[key] = row[key].replace(',', '.', str(row[key]).count(',') - 1)


def form_betrag(wert):
    wert = float(wert)
    if isinstance(wert,(float, int, complex)) == True:
        wert = f"{wert:,.2f}"
        wert = str(wert).replace('.', ',')
        wert = wert.replace(',', '.', wert.count(',') - 1)
        wert = wert + " €"
    return str(wert)


def form_zaehler(wert):
    wert = int(wert)
    wert = f"{int(wert):,.0f}"
    wert = wert.replace(",",".")
    return str(wert)


def form_mwst(wert):
    wert = int(wert)
    wert = str(wert) + " %"
    return str(wert)


def form_rvsatz(wert):
    wert = float(wert)
    wert = f"{wert:,.2f}"
    wert = str(wert).replace('.',',')
    wert = wert + " %"
    return str(wert)


def mapping_wordfelder(row):
    mergestring = {}
    for key,value in row.items():
        if key != "Ident":
            string1 = str(key).replace(" ","_")
            if "Wärmepreis" in key:
                mergestring[string1] = str(value).replace(".",",")
            elif "Datum" in key or "jahr" in key:
                mergestring[string1] = str(value)
            elif "leistung" in key or "Zähler" in key or "kWh" in key or "Wärmeverbrauch" in key:
                mergestring[string1] = form_zaehler(value)
            elif "Satz" in key or "ZA MwSt" == key:
                mergestring[string1] = form_mwst(value)
            elif "Rückvergütungssatz" in key:
                mergestring[string1] = form_rvsatz(value)
            elif "MwSt" in key or "Netto" in key or "summe" in key or "kosten" in key or "Kosten" in key or "Zahlung" in key or "Grundgebühr" in key or "abrechnung" in key or "Abrechnung" in key or "Abschlag" in key or "umsatz" in key or "Umsatz" in key or "Rückvergütung" in key:
                mergestring[string1] = form_betrag(value)
            else:
                mergestring[string1] = str(value)
    return mergestring
