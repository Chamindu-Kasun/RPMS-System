# Open the generated .docx in Microsoft Word, refresh the contents lists and page numbers,
# save it, and export a PDF copy for checking.
# Usage: powershell -ExecutionPolicy Bypass -File docs/tools/update_docx_fields.ps1

$ErrorActionPreference = "Stop"
$docs = Resolve-Path (Join-Path $PSScriptRoot "..")
$docx = Join-Path $docs "RPMS_UI_Design_Documentation.docx"
$pdf = Join-Path $docs "RPMS_UI_Design_Documentation.pdf"
$clock = [Diagnostics.Stopwatch]::StartNew()
function Step($msg) { "{0,6:N1}s  {1}" -f $clock.Elapsed.TotalSeconds, $msg }

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
# Background proofing makes Word very slow on long documents; it is not needed here.
$word.Options.CheckSpellingAsYouType = $false
$word.Options.CheckGrammarAsYouType = $false
$word.Options.BackgroundSave = $false
try {
    $doc = $word.Documents.Open($docx, $false, $false, $false)
    Step "opened"
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
    Step "contents lists updated ($($doc.TablesOfContents.Count))"
    foreach ($toc in $doc.TablesOfContents) { $toc.UpdatePageNumbers() }
    Step "contents page numbers refreshed"
    $doc.Save()
    Step "saved .docx"
    # 17 = wdExportFormatPDF; OptimizeFor 1 = on-screen (downsampled images); no tagged-PDF
    # structure pass, which is very slow on documents with many large tables and images.
    $doc.ExportAsFixedFormat($pdf, 17, $false, 1, 0, 1, 1, 0, $true, $true, 0, $false, $true, $false)
    Step "exported PDF"
    "Pages: " + $doc.ComputeStatistics(2)  # 2 = wdStatisticPages
    $doc.Close($false)
}
finally {
    $word.Quit()
}
