"""Änderung 2.043: Gemeinsame Protokollierung mit unverändertem Verhalten."""
from datetime import datetime


class Protokollierung:
    # Änderung: Aktuelle Pfade über die übergebene Anwendung lesen.
    def __init__(self, anwendung):
        self.anwendung = anwendung

    # Änderung 2.043: Bisherigen Ablauf mit aktuellen Anwendungswerten erhalten.
    def change_log(self, modul, event):
        current_datetime = datetime.now()
        current_datetime_str = current_datetime.strftime("%d.%m.%Y %H:%M:%S")
        content = f"{event["data"]["Ident"]}" + " " + f"{event["data"]["Name"]}" + " " + f"{event["data"]["Vorname"]}" + " ::: " + f"{event["colId"]}" + " ::: " + f"{event["oldValue"]}" + " ===> " + f"{event["newValue"]}"
        file = open(self.anwendung.ordner_logs + "\\" + self.anwendung.changelog, "a")
        file.write(current_datetime_str + " | " + modul + " | " + content + "\n")
        file.close()
        self.anwendung.changelog_markdown_ui_refresh()


    # Änderung 2.043: Bisherigen Ablauf mit aktuellen Anwendungswerten erhalten.
    def change_log_info(self, modul, info):
        current_datetime = datetime.now()
        current_datetime_str = current_datetime.strftime("%d.%m.%Y %H:%M:%S")
        file = open(self.anwendung.ordner_logs + "\\" + self.anwendung.changelog, "a")
        file.write(current_datetime_str + " | " + modul + " | " + info + "\n")
        file.close()
        self.anwendung.changelog_markdown_ui_refresh()
