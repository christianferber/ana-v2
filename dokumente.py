"""Änderung für v2: Dokumentverarbeitung unabhängig von NiceGUI bereitstellen."""

import os

from mailmerge import MailMerge
import pythoncom
from win32com.client import Dispatch
# Änderung für v2: Rückvergütungen verwenden weiterhin die bisherige docx2pdf-Konvertierung.
from docx2pdf import convert


def rueckverguetung_word_schreiben(rueckv_fuer_pdf, datei_vorlage_rueckv,
                                  ordner_rueckv_word, jahr, mapping_wordfelder):
    # Änderung für v2: Rückvergütungs-Serienschleife mit unveränderter Feld- und Dateiformatierung.
    for row in rueckv_fuer_pdf:
        name = str(row["Ident"] + "-" + row["Name"] + "-" + row["Vorname"]).replace(" ","-")
        document = MailMerge(datei_vorlage_rueckv)
        docmergelist = mapping_wordfelder(row)
        merged_content = document.merge(**docmergelist)
        document.write(ordner_rueckv_word + "\\" + "Rückvergütung-" + jahr + "-" + name + ".docx")


def rueckverguetung_pdf_konvertieren(ordner_rueckv_word, ordner_rueckv_pdf, fortschritt):
    # Änderung für v2: Dateifilter, Konvertierung und Fortschrittsreihenfolge beibehalten.
    pythoncom.CoInitialize()
    word_ordner = [
        f for f in os.listdir(ordner_rueckv_word)
        if f.lower().endswith(".docx")
    ]
    if not word_ordner:
        fortschritt(0)
        return
    pdfstep = 100 / len(word_ordner)
    pdfstatus = 0.0
    for i, datei in enumerate(word_ordner):
        pdfstatus += pdfstep
        pdfstatus_int = int(pdfstatus)
        if i % 2 == 0 or i == len(word_ordner) - 1:
            fortschritt(pdfstatus_int)
        word_datei = os.path.join(ordner_rueckv_word, datei)
        pdf_datei = os.path.join(
            ordner_rueckv_pdf,
            datei[:-4] + "pdf"
        )
        convert(word_datei, pdf_datei)


def abrechnung_word_schreiben(abrechnung_fuer_pdf, datei_vorlage_abrechnung,
                             ordner_abrechnungen_word, jahr, mapping_wordfelder):
    # Änderung für v2: Bestehende Serienschleife mit expliziten Eingaben auslagern.
    # Feldformatierung und Dateinamensbildung bleiben unverändert.
    for row in abrechnung_fuer_pdf:
        name = str(row["Ident"] + "-" + row["Name"] + "-" + row["Vorname"]).replace(" ","-")
        document = MailMerge(datei_vorlage_abrechnung)
        docmergelist = mapping_wordfelder(row)
        merged_content = document.merge(**docmergelist)
        document.write(ordner_abrechnungen_word + "\\" + "Abrechnung-" + jahr + "-" + name + ".docx")


def abrechnung_pdf_konvertieren(ordner_abrechnungen_word, ordner_abrechnungen_pdf,
                               fortschritt):
    # Änderung für v2: Bestehende COM-Konvertierung auslagern; Fortschritt als Rückruf.
    # Reihenfolge, Dateiauswahl und Word-Aufrufe entsprechen der Ausgangsversion.
    pythoncom.CoInitialize()
    word = Dispatch("Word.Application")
    word.Visible = False

    files = [f for f in os.listdir(ordner_abrechnungen_word) if f.endswith(".docx")]
    step = 100 / len(files)

    for i, datei in enumerate(files, 1):
        doc = word.Documents.Open(os.path.join(ordner_abrechnungen_word, datei))
        pdf = os.path.join(ordner_abrechnungen_pdf, datei[:-4] + "pdf")
        doc.SaveAs(pdf, FileFormat=17)
        doc.Close(False)

        fortschritt(int(i * step))

    word.Quit()
