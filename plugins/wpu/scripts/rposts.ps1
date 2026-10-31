# Blog posts on the remote site, through the bridge's typed /posts route.
#
#   powershell -File scripts/rposts.ps1 list [search]
#   powershell -File scripts/rposts.ps1 push <post.json>                 create as a draft (refuses an existing slug)
#   powershell -File scripts/rposts.ps1 push <post.json> update          update the post with that slug
#   powershell -File scripts/rposts.ps1 push <post.json> publish         publish now - ONLY after a person approved it
#
# post.json:
#   { "title": "...", "slug": "...", "content": "<!-- wp:paragraph --><p>...</p><!-- /wp:paragraph -->",
#     "excerpt": "...", "status": "draft" | "pending" | "future", "date": "2026-11-05T09:00:00+05:30",
#     "categories": ["Roof Repair"], "tags": ["storm damage"], "featured_media": 123, "author": "editor-login",
#     "seo": { "title": "...", "description": "...", "focus_keyword": "..." } }
#
# Images: upload them first with scripts/rmedia.ps1 and put the id in featured_media.
# The "seo" block is written through /seo right after the post is saved.
. "$PSScriptRoot\_remote.ps1"

if ($args.Count -lt 1) {
    Get-Content $PSCommandPath | Select-Object -Skip 1 -First 16 | ForEach-Object { $_ -replace '^# ?', '' }
    exit 2
}

switch ($args[0].ToLower()) {

    'list' {
        $q = if ($args.Count -ge 2) { '?search=' + [Uri]::EscapeDataString([string]$args[1]) } else { '' }
        $r = Invoke-Wpu -Route "/posts$q"
        foreach ($p in $r.posts) { Write-Host ("{0,-6} {1,-8} {2,-19} {3}" -f $p.id, $p.status, $p.date, $p.title) }
    }

    'push' {
        if ($args.Count -lt 2) { Stop-Wpu 'push needs a post.json file' }
        $file = (Resolve-Path $args[1] -ErrorAction Stop).Path
        $flag = if ($args.Count -ge 3) { [string]$args[2] } else { '' }
        try { $post = [IO.File]::ReadAllText($file) -replace "^﻿", '' | ConvertFrom-Json } catch { Stop-Wpu "not valid JSON: $($_.Exception.Message)" }

        $seo = $post.seo
        $post.PSObject.Properties.Remove('seo')
        $body = @{ post = $post; update = ($flag -eq 'update') }
        if ($flag -eq 'publish') {
            $post | Add-Member -NotePropertyName status -NotePropertyValue 'publish' -Force
            $body.confirm_publish = $true
            $body.update = $true
        }

        $r = Invoke-Wpu -Route '/posts' -Method 'POST' -TimeoutSec 180 -Body $body
        Write-Host ("{0} #{1} [{2}] {3}" -f $(if ($r.created) { 'created' } else { 'updated' }), $r.id, $r.status, $r.url) -ForegroundColor Green
        if ($r.status -ne 'publish') { Write-Host "preview: $($r.preview)" -ForegroundColor DarkGray }

        if ($seo) {
            $item = @{ id = $r.id }
            foreach ($p in $seo.PSObject.Properties) { $item[$p.Name] = $p.Value }
            $s = Invoke-Wpu -Route '/seo' -Method 'POST' -Body @{ items = @($item); apply = $true }
            $changed = @($s.results[0].changes.PSObject.Properties).Count
            Write-Host ("seo: {0} field(s) set via {1}{2}" -f $changed, $s.seo_plugin, $(if ($s.backup_ref) { "  (backup $($s.backup_ref))" } else { '' })) -ForegroundColor DarkGray
        }
    }

    default { Stop-Wpu "unknown mode '$($args[0])' - list or push" }
}
