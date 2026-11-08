"""Änderung 2.037: Werkzeugeoberfläche mit eigenem Anzeigezustand."""
import os
import re
from nicegui import app, ui
from pypdf import PdfReader, PdfWriter
import webview


class WerkzeugeOberflaeche:
    # Änderung: Bisherige gemeinsame Pfade über die Anwendung lesen.
    def __init__(self, anwendung):
        self.anwendung = anwendung

    def extract_numbers(self, filename):
        # Änderung 2.037: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        """
    Liefert alle 1–2 stelligen Zahlen zwischen '-' im Dateinamen.
    Beispiel: a-12-b-34-c.pdf -> ['12', '34']
    """
        return re.findall(r"-(\d{1,2})-", filename)

    async def pdfordner1_auswaehlen(self):
        # Änderung 2.037: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        ordner_pfad = await app.native.main_window.create_file_dialog(webview.FOLDER_DIALOG)
        if ordner_pfad:
            self.anwendung.pdfordner1_pfad = str(ordner_pfad[0])
            self.label_ordner1.text = self.anwendung.pdfordner1_pfad

    async def pdfordner2_auswaehlen(self):
        # Änderung 2.037: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        ordner_pfad = await app.native.main_window.create_file_dialog(webview.FOLDER_DIALOG)
        if ordner_pfad:
            self.anwendung.pdfordner2_pfad = str(ordner_pfad[0])
            self.label_ordner2.text = self.anwendung.pdfordner2_pfad

    async def ausgabeordner_auswaehlern(self):
        # Änderung 2.037: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        ordner_pfad = await app.native.main_window.create_file_dialog(webview.FOLDER_DIALOG)
        if ordner_pfad:
            self.anwendung.ausgabeordner_pfad = str(ordner_pfad[0])
            self.label_ausgabe.text = self.anwendung.ausgabeordner_pfad

    def pdfjoin(self, progress):
        # Änderung 2.037: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.
        self.log_feld.value = ''  # Logfeld leeren

        if not self.anwendung.pdfordner1_pfad or not self.anwendung.pdfordner2_pfad or not self.anwendung.ausgabeordner_pfad:
            ui.notify("Bitte alle Ordner auswählen!", color="red")
            return

        pdfs1 = [f for f in os.listdir(self.anwendung.pdfordner1_pfad) if f.lower().endswith(".pdf")]
        pdfs2 = [f for f in os.listdir(self.anwendung.pdfordner2_pfad) if f.lower().endswith(".pdf")]

        # ID → Liste von PDFs aus Ordner 2
        id_to_pdfs2 = {}
        for f in pdfs2:
            nums = self.anwendung.extract_numbers(f)
            if len(nums) == 1:
                id_to_pdfs2.setdefault(nums[0], []).append(f)

        count = 0
        total = len(pdfs1)

        # Fortschrittsanzeige sichtbar machen
        progress.classes(remove='invisible')

        for idx, f1 in enumerate(pdfs1, start=1):
            # Fortschritt aktualisieren
            progress.value = int((idx / total) * 100)

            nums1 = self.anwendung.extract_numbers(f1)

            # Mehrfach-ID in Ordner 1 → überspringen + ins Log
            if len(nums1) > 1:
                self.log_feld.value += (
                    f"[WARN] Datei übersprungen (mehrere IDs gefunden): {f1} "
                    f"IDs: {', '.join(nums1)}\n"
                )
                continue

            if not nums1:
                continue  # keine ID → ignorieren

            num = nums1[0]

            if num not in id_to_pdfs2:
                continue  # kein Pendant → ignorieren

            kandidaten = id_to_pdfs2[num]

            # Mehrere Pendants in Ordner 2 → erste verwenden + Log
            if len(kandidaten) > 1:
                self.log_feld.value += (
                    f"[INFO] Mehrere Pendants für '{f1}': {kandidaten} "
                    f"→ verwende '{kandidaten[0]}'\n"
                )

            f2 = kandidaten[0]

            writer = PdfWriter()

            # PDF 1 hinzufügen
            reader1 = PdfReader(os.path.join(self.anwendung.pdfordner1_pfad, f1))
            for page in reader1.pages:
                writer.add_page(page)

            # PDF 2 hinzufügen
            reader2 = PdfReader(os.path.join(self.anwendung.pdfordner2_pfad, f2))
            for page in reader2.pages:
                writer.add_page(page)

            basisname = os.path.splitext(f1)[0]
            output_path = os.path.join(
                self.anwendung.ausgabeordner_pfad,
                f"{basisname}-komplett.pdf"
            )

            with open(output_path, "wb") as out_file:
                writer.write(out_file)

            count += 1

        # Fortschrittsanzeige wieder unsichtbar
    #    progress.classes(add='invisible')
        ui.notify(f"{count} PDFs wurden erstellt!", color="green")

    def tools_ui(self):
        # Änderung 2.037: Bisherigen Ablauf über Ansicht und gemeinsame Anwendung ausführen.

        BUTTON_WIDTH = "220px"

        with ui.column().style("width: 100%"):
            # Große Überschrift
            ui.label("PDF kombinieren").classes("text-2xl font-bold")

            ui.label(
                'Mit diesem Tool werden PDF-Dateien kombiniert. '
                'Ordner 1 → Ordner 2. '
                'Zuordnung erfolgt über die ID im Dateinamen.'
            )

            with ui.row():
                ui.button(
                    "Ordner PDF 1",
                    icon='folder',
                    on_click=self.anwendung.pdfordner1_auswaehlen
                ).props('align=left').style(f"width: {BUTTON_WIDTH}")
                self.label_ordner1 = ui.label('— kein Ordner gewählt —')

            with ui.row():
                ui.button(
                    "Ordner PDF 2",
                    icon='folder',
                    on_click=self.anwendung.pdfordner2_auswaehlen
                ).props('align=left').style(f"width: {BUTTON_WIDTH}")
                self.label_ordner2 = ui.label('— kein Ordner gewählt —')

            with ui.row():
                ui.button(
                    "Ordner Ausgabe",
                    icon='folder',
                    on_click=self.anwendung.ausgabeordner_auswaehlern
                ).props('align=left').style(f"width: {BUTTON_WIDTH}")
                self.label_ausgabe = ui.label('— kein Ordner gewählt —')

            # Row mit Button + Fortschrittsanzeige
            with ui.row().style("align-items: center; gap: 10px;"):
                pdf_button = ui.button(
                    "PDF erstellen",
                    icon='picture_as_pdf',
                    on_click=lambda: self.anwendung.pdfjoin(progress),
                    color='red'
                ).props('align=left').style(f"width: {BUTTON_WIDTH}")

                progress = ui.circular_progress(min=0, max=100, value=0, color="black")

            self.log_feld = ui.textarea(
                label="Hinweise / Mehrfachzuordnungen"
            ).props('readonly rows=6').style(
                "width: 80%; font-family: monospace;"
            )
