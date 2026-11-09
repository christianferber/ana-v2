"""Änderung 2.046: Gemeinsame CSV-Speicherung für Abrechnung und Rückvergütung."""


class ExportHilfe:
    # Änderung 2.046: Aktuelle CSV- und Dialoghilfen von der Anwendung lesen.
    def __init__(self, anwendung):
        self.anwendung = anwendung

    # Änderung 2.046: Bisherigen asynchronen Ablauf unverändert übernehmen.
    async def komma_datei_speichern(self, dictlist, dateiname):
        kommacsv = []
        kommacsvrow = {}
        for row in dictlist:
            for key,value in row.items():
                if str(value).count('.') == 1:
                    kommacsvrow[key] = str(value).replace(".",",")
                else:
                    kommacsvrow[key] = value
            kommacsv.append(kommacsvrow)
            kommacsvrow = {}
        content = self.anwendung.dictlist_to_csv(kommacsv)
        datei = await self.anwendung.app.native.main_window.create_file_dialog(self.anwendung.webview.SAVE_DIALOG, directory="%USERPROFILE\\Downloads", allow_multiple=False, save_filename=dateiname)
        if datei != None:
            with open(datei,'w') as f:
                f.write(content)
                self.anwendung.ui.notify(datei + " wurde gespeichert.", type="positive")
        else:
            return
