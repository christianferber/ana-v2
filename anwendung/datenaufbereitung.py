"""Änderung 2.044: Gemeinsame Datenaufbereitung ohne GUI und Anwendungszustand."""


# Änderung 2.044: Unverändert aus oberflaeche.py übernommen.
def string_in_dict(my_dict, my_string):
    for key in my_dict:
        if my_string in key:
            return True
    return False

# Änderung 2.044: Unverändert aus oberflaeche.py übernommen.
def listcsv_to_dict(listcsv):
    dictrow = {}
    vardict = []
    dictkeys = listcsv[0].split(";")
    del dictkeys[-1]
    del listcsv[0]
    for row in listcsv:
        dictvalues = row.split(";")
        del dictvalues[-1]
        for x in range(len(dictkeys)):
            dictrow[dictkeys[x]] = dictvalues[x]
        vardict.append(dictrow)
        dictrow = {}
    return vardict

# Änderung 2.044: Unverändert aus oberflaeche.py übernommen.
def jahr_in_datum(datum):
    if "." in datum:
        datum_split = datum.split(".")
        jahr = datum_split[2]
    elif "-" in datum:
        datum_split = datum.split("-")
        jahr = datum_split[0]
    return jahr

# Änderung 2.044: Unverändert aus oberflaeche.py übernommen.
def tablefields_to_dotfloat(table):
    for row in table:
        for key,value in row.items():
            if key != "Ident" and key != "Name" and key != "Vorname" and key != "Kommentar" and "Datum" not in key:
                modifiedvalue = str(value).replace(".","")
                modifiedvalue = modifiedvalue.replace(",","")
                if modifiedvalue.isnumeric() and modifiedvalue != None:
                    row[key] = float(str(value).replace(",","."))
    return table

# Änderung 2.044: Unverändert aus oberflaeche.py übernommen.
def tablefields_to_int(table):
    table_new = []

    for row in table:
        row_new = {}
        for key, value in row.items():
            if (
                key not in ("Ident", "Name", "Vorname", "Kommentar") and "datum" not in key):
                if value is None or value == "":
                    row_new[key] = None
                else:
                    try:
                        row_new[key] = int(value)
                    except (TypeError, ValueError):
                        row_new[key] = None
            else:
                row_new[key] = value

        table_new.append(row_new)

    return table_new
