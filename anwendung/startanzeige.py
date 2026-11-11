"""Änderung: Sichtbare Startphasen anzeigen, bevor die Oberfläche geladen wird."""
import sys
import threading
from pathlib import Path


class Startanzeige:
    # Änderung: Nur der Fensterthread greift auf Tk zu; die Anwendung meldet Zustände.
    def __init__(self):
        self._status = (10, 'Programm wird geladen …')
        self._sperre = threading.Lock()
        self._schliessen = threading.Event()
        self._bereit = threading.Event()
        self._sichtbar = threading.Event()
        self._thread = None

    def __enter__(self):
        self._thread = threading.Thread(target=self._fenster, name='ANA-Startanzeige', daemon=True)
        self._thread.start()
        # Änderung: Die Anzeige vor dem Laden großer Programmbibliotheken öffnen.
        self._sichtbar.wait(timeout=3)
        return self

    def status(self, wert, text):
        with self._sperre:
            self._status = (wert, text)

    def bereit(self):
        # Änderung: Erst die tatsächliche Verbindung des Hauptfensters beendet die Anzeige.
        self.status(100, 'Bereit')
        self._bereit.set()

    def __exit__(self, typ, wert, traceback):
        # Änderung: Auch ein Startfehler oder das Beenden der App schließt die Anzeige.
        self._schliessen.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _fenster(self):
        root = None
        try:
            # Änderung: Tk erst im eigenen Fensterthread laden und ausschließlich dort bedienen.
            import tkinter as tk
            from tkinter import ttk

            root = tk.Tk()
            root.withdraw()
            root.title('ANA wird gestartet')
            root.overrideredirect(True)
            root.attributes('-topmost', True)
            root.configure(background='#ffffff')
            # Änderung 2.049: Platz für das offizielle Logo und den Fortschrittsbereich vorsehen.
            breite, hoehe = 460, 230
            x = (root.winfo_screenwidth() - breite) // 2
            y = (root.winfo_screenheight() - hoehe) // 2
            root.geometry(f'{breite}x{hoehe}+{x}+{y}')
            ordner = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]
            icon = ordner / 'ressourcen' / 'ANA-icon.ico'
            if icon.is_file():
                root.iconbitmap(str(icon))
            rahmen = tk.Frame(root, background='#ffffff', highlightbackground='#d6e1e8', highlightthickness=1)
            rahmen.pack(fill='both', expand=True)
            # Änderung 2.049: Dasselbe offizielle ANA-Logo wie im Hauptfenster verwenden.
            # Ganzzahlig verkleinern, Seitenverhältnis bewahren und im Fensterthread halten.
            logo = tk.PhotoImage(master=root, file=str(ordner / 'ressourcen' / 'ANA logo.png'))
            faktor = max(1, (logo.width() + 199) // 200, (logo.height() + 69) // 70)
            logo = logo.subsample(faktor, faktor)
            tk.Label(rahmen, image=logo, background='#ffffff').pack(anchor='w', padx=28, pady=(20, 8))
            tk.Label(rahmen, text='Die Anwendung wird gestartet.', font=('Segoe UI', 11),
                     background='#ffffff', foreground='#334155').pack(anchor='w', padx=30, pady=(0, 15))
            stil = ttk.Style(root)
            stil.theme_use('clam')
            stil.configure('ANA.Horizontal.TProgressbar', background='#1761a0',
                           troughcolor='#e7eef3', borderwidth=0, lightcolor='#1761a0', darkcolor='#1761a0')
            # Änderung 2.049: Fester Füllbalken für die gemeldeten Startphasen;
            # keine Laufanimation und keine Aussage über verbleibende Ladezeit.
            balken = ttk.Progressbar(rahmen, maximum=100, mode='determinate',
                                     style='ANA.Horizontal.TProgressbar')
            balken.pack(fill='x', padx=30)
            label = tk.Label(rahmen, font=('Segoe UI', 10), background='#ffffff', foreground='#475569')
            label.pack(anchor='w', padx=30, pady=(9, 0))
            fertig_angezeigt = False

            def aktualisieren():
                nonlocal fertig_angezeigt
                if self._schliessen.is_set():
                    root.quit()
                    return
                with self._sperre:
                    wert, text = self._status
                label.configure(text=text)
                # Änderung 2.049: Den Balken ausschließlich mit dem Phasenstatus füllen.
                balken.configure(value=wert)
                if self._bereit.is_set():
                    if not fertig_angezeigt:
                        fertig_angezeigt = True
                        root.after(350, root.quit)
                    return
                root.after(75, aktualisieren)

            aktualisieren()
            root.deiconify()
            root.update_idletasks()
            self._sichtbar.set()
            root.mainloop()
        except Exception:
            # Änderung: Eine nicht verfügbare Startanzeige darf den bisherigen App-Start nicht verhindern.
            print('Die Startanzeige konnte nicht geöffnet werden; ANA startet weiter.', file=sys.stderr)
        finally:
            if root is not None:
                root.destroy()
            # Änderung: Die rekursive Callback-Referenz im Fensterthread lösen;
            # dadurch werden auch die Tk-Objekte in diesem Thread freigegeben.
            aktualisieren = None
            self._sichtbar.set()
