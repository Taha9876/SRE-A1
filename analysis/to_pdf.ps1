# Convert the .docx deliverables to PDF with Word (updates the table of contents first).
param([string[]]$Files)

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    foreach ($f in $Files) {
        $path = (Resolve-Path $f).Path
        $doc = $word.Documents.Open($path)
        foreach ($toc in $doc.TablesOfContents) {
            $toc.Update()
            # compact entries so the contents list stays on one page
            $toc.Range.ParagraphFormat.SpaceAfter = 2
            $toc.Range.ParagraphFormat.SpaceBefore = 0
            $toc.Range.ParagraphFormat.LineSpacingRule = 0
            $toc.Range.Font.Size = 10
            $doc.Repaginate()
            $toc.UpdatePageNumbers()
        }
        $doc.Fields.Update() | Out-Null
        $doc.Save()
        $pdf = [IO.Path]::ChangeExtension($path, ".pdf")
        $doc.SaveAs2($pdf, 17)
        "{0}: {1} pages" -f (Split-Path $pdf -Leaf), $doc.ComputeStatistics(2)
        $doc.Close($false)
    }
}
finally {
    $word.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}

