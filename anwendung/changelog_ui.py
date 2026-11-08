"""Änderung 2.039: Changelog-Anzeige mit eigenem Filter- und Anzeigezustand."""
from pathlib import Path
from nicegui import ui


class ChangelogOberflaeche:
    # Änderung: Aktuellen Protokollpfad stets über die Anwendung lesen.
    def __init__(self, anwendung):
        self.anwendung = anwendung

    def changelog_markdown_ui(self):
        # Änderung 2.039: Bisherigen Anzeigeablauf über Ansicht und Anwendung ausführen.
        with ui.row():
            ui.button('Changelog aktualisieren', icon='refresh', on_click=self.anwendung.changelog_markdown_ui_refresh).props('color=secondary')
            self.filter_toggle = ui.toggle(['ALLE', 'MITGLIEDER','WARTUNG','ABNEHMER','ZÄHLER','ABSCHLAG','RÜCKVERGÜTUNG','KONTODATEN'], value='ALLE', on_change=self.anwendung.changelog_markdown_ui_refresh)
        self.changelog_markdown = ui.markdown('')
        self.anwendung.changelog_markdown_ui_refresh()

    def changelog_markdown_ui_refresh(self):
        # Änderung 2.039: Bisherigen Anzeigeablauf über Ansicht und Anwendung ausführen.
        content_present = ""
        if Path(self.anwendung.ordner_logs + "\\" + self.anwendung.changelog).is_file():
            with open(self.anwendung.ordner_logs + "\\" + self.anwendung.changelog,'r') as datei:
                content = datei.read()
                datei.close()
                if self.filter_toggle.value == 'ALLE':
                    content_present = content 
                else:
                    for line in content.split("\n"):
                        if self.filter_toggle.value in line:
                            content_present = content_present + line + "\n"
                content_present = content_present.replace("\n","  \n")
                self.changelog_markdown.set_content(content_present)

    def changelog_ui(self):
        # Änderung 2.039: Bisherigen Anzeigeablauf über Ansicht und Anwendung ausführen.
        self.anwendung.changelog_markdown_ui()
