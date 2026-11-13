"""Änderung nach 2.05.00: Eigenständiges sichtbares Fortschrittsfenster beim Beenden."""
import multiprocessing
from queue import Empty


def fenster_anzeigen(meldungen, sichtbar):
    # Änderung: Tk im Hauptthread eines eigenen Prozesses betreiben, unabhängig von NiceGUI.
    import tkinter as tk
    from tkinter import ttk

    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        root.title('ANA – Sicherung beim Beenden')
        x = max(0, (root.winfo_screenwidth() - 510) // 2)
        y = max(0, (root.winfo_screenheight() - 170) // 2)
        root.geometry(f'510x170+{x}+{y}')
        root.resizable(False, False)
        root.attributes('-topmost', True)
        root.protocol('WM_DELETE_WINDOW', lambda: None)
        ttk.Label(root, text='ANA wird nach der Sicherung beendet.').pack(padx=20, pady=(20, 10))
        text = ttk.Label(root, text='Sicherung wird vorbereitet …')
        text.pack(padx=20, pady=5)
        balken = ttk.Progressbar(root, maximum=100)
        balken.pack(fill='x', padx=20, pady=10)
        root.deiconify()
        root.lift()
        root.update()
        if root.winfo_viewable():
            sichtbar.set()

        def aktualisieren():
            nachricht = None
            try:
                while True:
                    nachricht = meldungen.get_nowait()
            except Empty:
                pass
            if nachricht is not None:
                wert, status, fertig, fehler = nachricht
                text.configure(text=status + f'  {int(wert * 100)} %')
                balken.configure(value=wert * 100)
                if fertig:
                    if fehler:
                        root.quit()
                    else:
                        text.configure(text='Sicherung abgeschlossen.  100 %')
                        balken.configure(value=100)
                        root.after(1200, root.quit)
                    return
            root.after(75, aktualisieren)

        root.after(0, aktualisieren)
        root.mainloop()
    finally:
        if root is not None:
            root.destroy()


class Sicherungsanzeige:
    # Änderung: Nur Status übermitteln, keine UI-Zugriffe aus dem Sicherungsthread.
    def __init__(self):
        kontext = multiprocessing.get_context('spawn')
        self.meldungen = kontext.Queue()
        self.sichtbar = kontext.Event()
        self.prozess = kontext.Process(target=fenster_anzeigen,
                                      args=(self.meldungen, self.sichtbar),
                                      name='ANA-Sicherungsanzeige')

    def starten(self):
        self.prozess.start()
        # Änderung: Die Sicherung erst nach dem sichtbaren Fenster beginnen lassen.
        return self.sichtbar.wait(8) and self.prozess.is_alive()

    def aktualisieren(self, status):
        try:
            if self.prozess.is_alive():
                self.meldungen.put((status.wert, status.text, status.fertig, bool(status.fehler)))
                return True
        except (OSError, ValueError):
            pass
        return False

    def schliessen(self):
        # Änderung: Abschlussanzeige abwarten und ausschließlich den eigenen Fensterprozess bereinigen.
        if self.prozess.pid is not None:
            self.prozess.join(timeout=5)
            if self.prozess.is_alive():
                self.prozess.terminate()
                self.prozess.join(timeout=3)
        self.meldungen.cancel_join_thread()
        self.meldungen.close()
