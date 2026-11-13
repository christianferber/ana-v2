# ZIP-Vollsicherung

<!-- Änderung nach 2.05.00: Bedienung und Umfang der neuen Sicherung dokumentieren. -->
In **Einstellungen → Datensicherung** den Sicherungsordner auswählen oder dessen
vollständigen Pfad eingeben. Mit **Speichern** werden Ordner und Optionen in der
`ana.ini` im Abschnitt `[Sicherung]` hinterlegt. **Abbrechen** verwirft Änderungen.
<!-- Änderung nach 2.05.00: Register und bedingte Aufbewahrung erläutern. -->
Die Einstellungen haben vier Tabs: **Betreiber und Preise**, **Arbeitsordner**,
**Datensicherung** und **Darstellung**. Speichern und Abbrechen gelten für alle Tabs;
beim Tabwechsel bleiben die Eingaben erhalten.
<!-- Änderung nach 2.05.00: Fester Dialograhmen bei wechselndem Tabinhalt. -->
Der Dialograhmen bleibt beim Tabwechsel gleich groß. Bei kleineren Fenstern wird
seine Höhe begrenzt; längere Inhalte scrollen zwischen Tabzeile und Aktionsleiste.

**Jetzt sichern** verwendet die gerade angezeigten Sicherungsoptionen, auch wenn
diese noch nicht gespeichert wurden. Die Sicherung nimmt die bereits gespeicherten
Dateien auf; die INI im Archiv entspricht dem zuletzt gespeicherten Stand.
Vorher deshalb fachliche Änderungen speichern. Die Sicherung speichert keine
offenen Eingaben und löst keine Berechnungen oder Datenbankänderungen aus.

Das ZIP enthält unter `Arbeitsordner/` alle gespeicherten Dateien und leeren Ordner
des Arbeitsordners: insbesondere Datenbank, Vorlagen, Abrechnungen, Rückvergütungen,
Downloads, Protokolle, Betreiber-INI und vorhandene herkömmliche Datenbanksicherungen.
Unter `Programmeinstellungen/ana.ini` liegt zusätzlich die Programmkonfiguration,
auch wenn sie außerhalb des Arbeitsordners gespeichert ist.

Der gewählte Sicherungszielordner wird bei einem Ziel innerhalb des Arbeitsordners
ausgenommen. Bereits erzeugte ZIP-Vollsicherungen werden nicht erneut eingebettet.
Als Ziel ist auch `Sicherungen` selbst möglich, jedoch kein Unterordner davon:
Solche Unterordner könnten durch die unveränderte bisherige Datenbankrotation
gelöscht werden und werden deshalb als Sicherungsziel abgelehnt.
Lokale Entwicklungs-, Git- und Buildordner (`.git`, `.lokal`, `.agents`, `.codex`,
`__pycache__`, `build`, `dist`, `release`) gehören nicht zum Sicherungsumfang.
Datei- oder Ordnerverknüpfungen führen zu einer Fehlermeldung, damit keine
scheinbar vollständige Sicherung mit fehlenden oder externen Inhalten entsteht.

Die Sicherung wird komprimiert und auf Lesbarkeit geprüft, bevor sie als fertige
ZIP-Datei erscheint. Änderungen an Quelldateien während des Kopierens führen zum
Abbruch. In diesem Fall die laufende Bearbeitung bzw. den Export abschließen und
erneut sichern. Währenddessen weder ANA-Daten noch Vorlagen extern ändern.
<!-- Änderung nach 2.05.00: Durchgehenden Gesamtfortschritt beschreiben. -->
Komprimieren und Sichern teilen sich einen einzigen Gesamtfortschrittsbalken.
Dieser läuft ohne Neustart bis 100 Prozent und schließt ZIP-Prüfung, Bereitstellung
der fertigen Sicherung und gegebenenfalls Aufräumen ein.
<!-- Änderung nach 2.05.00: Datenbezogenen Fortschritt und stabilen Dialog erläutern. -->
Geschriebene und anschließend geprüfte Datenmengen zählen nach demselben Maßstab.
Gleich große Datenblöcke erhöhen den Fortschritt gleich stark; die Geschwindigkeit
über die Zeit kann je nach Komprimierbarkeit und Laufwerk schwanken. 100 Prozent
erscheinen erst nach erfolgreichem Abschluss. Im Balken steht keine zusätzliche
Rohzahl. Der Dialog behält seine Größe und die Schaltfläche bleibt während der
Sicherung sichtbar, aber gesperrt. Lange Abschlusspfade scrollen im Meldungsbereich.

**Bei Programmbeendigung sichern** aktiviert die Sicherung bei regulärem
Programmende, einschließlich Fenster-X. Ein eigenes Fortschrittsfenster bleibt bis
zum Abschluss sichtbar. Eine bereits laufende Sicherung wird abgewartet und nicht
doppelt gestartet. Fehler werden auch nach Schließen des Hauptfensters angezeigt.
<!-- Änderung nach 2.05.00: Abschluss beim Beenden kurz sichtbar bestätigen. -->
Die Fortschrittsanzeige erscheint mittig im Vordergrund. Nach erfolgreicher Sicherung
bleibt „Sicherung abgeschlossen“ mit 100 Prozent etwa 1,2 Sekunden sichtbar,
anschließend schließt die Anzeige automatisch.
<!-- Änderung nach 2.05.00: Anzeige unabhängig vom bereits geschlossenen Hauptfenster betreiben. -->
Die Anzeige läuft in einem eigenen Fensterprozess und bleibt nach dem Schließen
des ANA-Hauptfensters sichtbar. Sollte das Öffnen der Anzeige scheitern, erfolgt
nach der Sicherung eine entsprechende Meldung.
Erzwungenes Prozessende, Stromausfall oder Rechnerabsturz lösen keine Sicherung aus.

**Alte Vollsicherungen nach erfolgreicher Sicherung aufräumen** löscht ausschließlich
eigene ZIP-Vollsicherungen desselben Arbeitsordners im gewählten Zielordner, deren
Erstellungszeitpunkt außerhalb des eingestellten Zeitraums liegt. Die Aufbewahrung
ist zwischen 1 und 520 ganzen Wochen wählbar; Vorgabe sind 12 Wochen. Die gerade
erstellte Sicherung bleibt erhalten. Nach einem fehlgeschlagenen Sicherungsversuch
wird nicht aufgeräumt. Fremde Dateien, andere Arbeitsordner und die bisherige
Datenbanksicherung bleiben unberührt. Automatik und Aufräumen sind zunächst aus.
<!-- Änderung nach 2.05.00: Ausblenden erhält die bisher eingestellte Wochenzahl. -->
Das Feld **Aufbewahrung in Wochen** wird nur bei aktiviertem Aufräumen angezeigt.
Beim Ausschalten bleibt die eingestellte Wochenzahl für später erhalten.

Zur Wiederherstellung ANA beenden und das ZIP zunächst in einen separaten Ordner
entpacken. Die Nutzdaten liegen in `Arbeitsordner/`; `Programmeinstellungen/ana.ini`
ist separat enthalten und kann noch auf den bisherigen Arbeitsordner verweisen.
Eine automatische Wiederherstellung ist nicht Teil dieser Funktion.

Die ZIP-Dateien sind nicht verschlüsselt. Bei vertraulichen Daten einen entsprechend
geschützten Sicherungsordner verwenden. ANA überträgt die Sicherung nicht selbst
an einen Cloud-Dienst; für lokale Daten einen lokalen Zielordner wählen.
