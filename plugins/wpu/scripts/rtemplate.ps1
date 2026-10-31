# Import an Elementor template export (.json) into the REMOTE site's template library.
#
#   powershell -File scripts/rtemplate.ps1 templates/header.json
#   powershell -File scripts/rtemplate.ps1 templates/*.json
#
# Uses Elementor's own importer (templates_manager->import_template), exactly as
# Templates > Saved Templates > Import does - so kit/global references, dynamic
# tags and image re-hosting behave the same as an import through wp-admin.
#
# It only IMPORTS. Putting a template on a page, or giving a header/footer its
# display conditions, is done by build/apply-plan.php from the site plan, where
# it can be dry-run and re-run safely.
. "$PSScriptRoot\_remote.ps1"

if ($args.Count -lt 1) {
    Write-Host 'usage: powershell -File scripts/rtemplate.ps1 <template.json | glob>'
    exit 2
}

$files = @(Get-ChildItem -Path $args[0] -File -Filter *.json -ErrorAction Stop)
if (-not $files.Count) { Stop-Wpsb "no .json files match $($args[0])" }

foreach ($f in $files) {
    $raw = [IO.File]::ReadAllBytes($f.FullName)

    # Refuse obviously wrong files before sending: an Elementor export is JSON with
    # a "content" array. A page's raw _elementor_data (a bare array) is not an
    # export and the importer rejects it with an unhelpful message.
    try {
        $probe = [Text.Encoding]::UTF8.GetString($raw) -replace "^﻿", '' | ConvertFrom-Json
    } catch {
        Write-Host ("skip {0}: not valid JSON" -f $f.Name) -ForegroundColor Yellow; continue
    }
    if ($null -eq $probe.content) {
        Write-Host ("skip {0}: no 'content' key - not an Elementor template export" -f $f.Name) -ForegroundColor Yellow; continue
    }

    $r = Invoke-Wpsb -Route '/template' -Method 'POST' -TimeoutSec 300 -Body @{
        filename = $f.Name
        json_b64 = [Convert]::ToBase64String($raw)
    }

    foreach ($t in @($r.templates)) {
        Write-Host ("{0,-6} {1,-14} {2}" -f $t.id, $t.type, $t.title) -ForegroundColor Green
    }
}
