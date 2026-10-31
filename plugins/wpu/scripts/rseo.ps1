# SEO fields on the remote site, through the bridge's typed /seo route.
#
#   powershell -File scripts/rseo.ps1 list [page,post,product]     current fields -> sites/<slug>/seo/current.json
#   powershell -File scripts/rseo.ps1 push <changes.json>           dry run: shows every change
#   powershell -File scripts/rseo.ps1 push <changes.json> apply     writes them, keeps a backup, saves a receipt
#   powershell -File scripts/rseo.ps1 rollback <backup_ref>         puts the previous values back
#
# changes.json:  { "items": [ { "id": 12, "title": "...", "description": "...",
#                               "focus_keyword": "...", "canonical": null, "noindex": false,
#                               "schema": { "@context": "https://schema.org", "@type": "LocalBusiness", ... } } ] }
# Only the fields present are touched. null clears a field.
#
# Works with Rank Math or Yoast - the bridge maps the names. After applying,
# verify on the rendered page (node audit/seo.mjs); a stored value that a cache
# or the SEO plugin is not serving is not done.
. "$PSScriptRoot\_remote.ps1"

if ($args.Count -lt 1) {
    Get-Content $PSCommandPath | Select-Object -Skip 1 -First 16 | ForEach-Object { $_ -replace '^# ?', '' }
    exit 2
}

$seoDir = Join-Path $script:SiteDir 'seo'
if (-not (Test-Path $seoDir)) { New-Item -ItemType Directory -Force -Path $seoDir | Out-Null }
$utf8 = New-Object System.Text.UTF8Encoding($false)

switch ($args[0].ToLower()) {

    'list' {
        $types = if ($args.Count -ge 2) { [string]$args[1] } else { 'page,post' }
        $r = Invoke-Wpu -Route ("/seo?status=any&types={0}" -f [Uri]::EscapeDataString($types)) -TimeoutSec 180
        $out = Join-Path $seoDir 'current.json'
        [IO.File]::WriteAllText($out, ($r | ConvertTo-Json -Depth 12), $utf8)
        Write-Host ("SEO plugin: {0}   writable: {1}" -f $r.seo_plugin, $r.writable) -ForegroundColor Cyan
        foreach ($p in $r.pages) {
            $t = if ($p.seo.title) { $p.seo.title } else { '(default title)' }
            $d = if ($p.seo.description) { "{0} chars" -f $p.seo.description.Length } else { 'NO DESCRIPTION' }
            $k = if ($p.seo.focus_keyword) { $p.seo.focus_keyword } else { '-' }
            Write-Host ("{0,-6} {1,-8} {2,-38} kw: {3,-26} desc: {4}" -f $p.id, $p.status, ($p.url -replace '^https?://[^/]+', '').Substring(0, [Math]::Min(38, ($p.url -replace '^https?://[^/]+', '').Length)), $k, $d)
        }
        Write-Host ''
        Write-Host "-> $out" -ForegroundColor DarkGray
    }

    'push' {
        if ($args.Count -lt 2) { Stop-Wpu 'push needs a changes.json file' }
        $file  = (Resolve-Path $args[1] -ErrorAction Stop).Path
        $apply = ($args.Count -ge 3 -and $args[2] -eq 'apply')
        try { $changes = [IO.File]::ReadAllText($file) -replace "^﻿", '' | ConvertFrom-Json } catch { Stop-Wpu "not valid JSON: $($_.Exception.Message)" }
        if (-not $changes.items) { Stop-Wpu 'changes.json needs an "items" list' }

        $r = Invoke-Wpu -Route '/seo' -Method 'POST' -TimeoutSec 300 -Body @{ items = @($changes.items); apply = $apply }

        Write-Host ("{0} on {1} ({2})" -f $(if ($apply) { 'APPLIED' } else { 'DRY RUN' }), $script:Cfg.remote.url, $r.seo_plugin) -ForegroundColor $(if ($apply) { 'Yellow' } else { 'DarkGray' })
        $n = 0
        foreach ($item in $r.results) {
            if (-not $item.ok) { Write-Host ("  #{0}  ERROR {1}" -f $item.id, $item.error) -ForegroundColor Red; continue }
            $fields = @($item.changes.PSObject.Properties)
            if (-not $fields.Count) { Write-Host ("  #{0}  no change" -f $item.id) -ForegroundColor DarkGray; continue }
            Write-Host ("  #{0}  {1}" -f $item.id, $item.url)
            foreach ($f in $fields) {
                $n++
                $from = $f.Value.from | ConvertTo-Json -Compress -Depth 8
                $to   = $f.Value.to | ConvertTo-Json -Compress -Depth 8
                if ($from.Length -gt 90) { $from = $from.Substring(0, 87) + '...' }
                if ($to.Length -gt 90) { $to = $to.Substring(0, 87) + '...' }
                Write-Host ("      {0,-14} {1}" -f $f.Name, $from) -ForegroundColor DarkGray
                Write-Host ("      {0,-14} -> {1}" -f '', $to) -ForegroundColor Green
            }
        }
        Write-Host ''
        Write-Host "$n field change(s)."
        if ($apply -and $r.backup_ref) {
            $receipts = Join-Path $seoDir 'receipts'
            if (-not (Test-Path $receipts)) { New-Item -ItemType Directory -Force -Path $receipts | Out-Null }
            $rec = Join-Path $receipts ("{0}.json" -f $r.backup_ref)
            [IO.File]::WriteAllText($rec, ($r | ConvertTo-Json -Depth 12), $utf8)
            Write-Host "backup: $($r.backup_ref)   (undo: scripts/rseo.ps1 rollback $($r.backup_ref))" -ForegroundColor Yellow
            Write-Host "receipt -> $rec" -ForegroundColor DarkGray
        } elseif (-not $apply) {
            Write-Host "(dry run - add 'apply')" -ForegroundColor DarkGray
        }
    }

    'rollback' {
        if ($args.Count -lt 2) { Stop-Wpu 'rollback needs the backup_ref printed when the change was applied' }
        $r = Invoke-Wpu -Route '/seo/rollback' -Method 'POST' -Body @{ ref = [string]$args[1] }
        Write-Host ("rolled back {0}: {1} page(s) restored ({2})" -f $r.ref, @($r.restored).Count, (@($r.restored) -join ', ')) -ForegroundColor Green
    }

    default { Stop-Wpu "unknown mode '$($args[0])' - list, push or rollback" }
}
