"""Änderung nach 2.06.00: PDF-Seiten ausschließlich mit lokaler Windows-OCR lesen."""
import base64
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


# Änderung: Windows-Bordmittel verwenden; keine Installation, Cloud oder Bilddateien nötig.
# Dokumentation: learn.microsoft.com/uwp/api/windows.media.ocr.ocrengine
WINDOWS_OCR = r'''
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$fileType = [Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime]
$pdfType = [Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType=WindowsRuntime]
$decoderType = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType=WindowsRuntime]
$bitmapType = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Graphics.Imaging, ContentType=WindowsRuntime]
$ocrType = [Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType=WindowsRuntime]
$ocrResultType = [Windows.Media.Ocr.OcrResult, Windows.Media.Ocr, ContentType=WindowsRuntime]
$streamType = [Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType=WindowsRuntime]
$optionsType = [Windows.Data.Pdf.PdfPageRenderOptions, Windows.Data.Pdf, ContentType=WindowsRuntime]
$asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1
} | Select-Object -First 1
# Änderung: PowerShell benötigt für WinRT-Aktionen die explizite AsTask-Überladung.
$asAction = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and -not $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction'
} | Select-Object -First 1
function Warten($operation, $typ) {
    $task = $asTask.MakeGenericMethod($typ).Invoke($null, @($operation))
    $task.Wait()
    return $task.Result
}
$engine = $ocrType::TryCreateFromUserProfileLanguages()
if ($null -eq $engine) { throw 'Keine lokale OCR-Sprache verfügbar.' }
$file = Warten ($fileType::GetFileFromPathAsync($env:ANA_RECHNUNG_PDF)) $fileType
$pdf = Warten ($pdfType::LoadFromFileAsync($file)) $pdfType
$texte = @()
for ($i = 0; $i -lt $pdf.PageCount; $i++) {
    $page = $pdf.GetPage($i)
    $stream = [Activator]::CreateInstance($streamType)
    $bitmap = $null
    try {
        $options = [Activator]::CreateInstance($optionsType)
        $max = [Math]::Min(2600, $ocrType::MaxImageDimension)
        $scale = $max / [Math]::Max($page.Size.Width, $page.Size.Height)
        $options.DestinationWidth = [uint32]($page.Size.Width * $scale)
        $options.DestinationHeight = [uint32]($page.Size.Height * $scale)
        $action = $asAction.Invoke($null, @($page.RenderToStreamAsync($stream, $options)))
        $action.Wait()
        $stream.Seek(0)
        $decoder = Warten ($decoderType::CreateAsync($stream)) $decoderType
        $bitmap = Warten ($decoder.GetSoftwareBitmapAsync()) $bitmapType
        $result = Warten ($engine.RecognizeAsync($bitmap)) $ocrResultType
        $texte += (($result.Lines | ForEach-Object { $_.Text }) -join "`n")
    }
    finally {
        if ($null -ne $bitmap) { $bitmap.Dispose() }
        $stream.Dispose()
        $page.Dispose()
    }
}
ConvertTo-Json -InputObject @($texte) -Compress
'''


def pdf_texte_lokal_erkennen(datei):
    # Änderung: OCR nur pro unverändertem Dateiinhalt erneut ausführen; Cache bleibt im RAM.
    datei = Path(datei).resolve()
    checksum = hashlib.sha256(datei.read_bytes()).hexdigest()
    return list(_pdf_texte_lokal_erkennen(str(datei), checksum))


@lru_cache(maxsize=32)
def _pdf_texte_lokal_erkennen(datei, checksum):
    # Änderung: Pfad als Umgebungswert übergeben, niemals in Shell-Code einsetzen.
    if sys.platform != 'win32':
        raise ValueError('Lokale Windows-Texterkennung ist auf diesem System nicht verfügbar.')
    umgebung = os.environ.copy()
    umgebung['ANA_RECHNUNG_PDF'] = str(Path(datei).resolve())
    powershell = Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    code = base64.b64encode(WINDOWS_OCR.encode('utf-16-le')).decode('ascii')
    try:
        ergebnis = subprocess.run([str(powershell), '-NoProfile', '-NonInteractive', '-EncodedCommand', code],
                                  env=umgebung, capture_output=True, timeout=90,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
        if ergebnis.returncode:
            raise ValueError('Lokale Windows-Texterkennung fehlgeschlagen oder nicht verfügbar.')
        texte = json.loads(ergebnis.stdout.decode('utf-8-sig'))
        if not isinstance(texte, list) or not all(isinstance(t, str) for t in texte):
            raise ValueError('Lokale Texterkennung lieferte kein lesbares Ergebnis.')
        return tuple(texte)
    except (OSError, subprocess.TimeoutExpired) as fehler:
        raise ValueError('Lokale Windows-Texterkennung nicht verfügbar oder Zeitlimit erreicht.') from fehler
