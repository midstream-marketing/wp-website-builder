# Upload local images/files into the REMOTE site's Media Library.
#
#   powershell -File scripts/rmedia.ps1 assets/hero.jpg
#   powershell -File scripts/rmedia.ps1 assets/logo.svg "Company logo"
#   powershell -File scripts/rmedia.ps1 assets/*.webp
#
# Goes through WordPress's own upload handling (wp_handle_sideload +
# wp_insert_attachment), so thumbnails are generated and the file is a real
# attachment. Do NOT write images into uploads/ with a PHP script instead: on some
# hosts files written that way are removed by a scanner within minutes
# (knowledge/GOTCHAS.md - firparkds.ie lost two font files like this).
#
# Prints "id  url" per file - paste the id into the plan or the Elementor data.
. "$PSScriptRoot\_remote.ps1"

if ($args.Count -lt 1) {
    Write-Host 'usage: powershell -File scripts/rmedia.ps1 <file-or-glob> [alt text]'
    exit 2
}

$alt = ''
if ($args.Count -ge 2) { $alt = [string]$args[1] }

$files = @(Get-ChildItem -Path $args[0] -File -ErrorAction Stop)
if (-not $files.Count) { Stop-Wpsb "no files match $($args[0])" }

foreach ($f in $files) {
    $bytes = [IO.File]::ReadAllBytes($f.FullName)
    if ($bytes.Length -gt 20MB) { Write-Host ("skip {0}: larger than 20 MB" -f $f.Name) -ForegroundColor Yellow; continue }

    $r = Invoke-Wpsb -Route '/media' -Method 'POST' -TimeoutSec 300 -Body @{
        filename    = $f.Name
        content_b64 = [Convert]::ToBase64String($bytes)
        alt         = $alt
    }

    if ($r.reused) {
        Write-Host ("{0,-6} {1}  (already in library - reused)" -f $r.id, $r.url) -ForegroundColor DarkGray
    } else {
        Write-Host ("{0,-6} {1}  ({2}, {3:N0} bytes)" -f $r.id, $r.url, $r.mime, $r.bytes) -ForegroundColor Green
    }
}
