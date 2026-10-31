# Which client site am I working on? Shared by every wrapper.
#
# The workspace is the folder Claude Code was opened in (or $env:WPU_WORKSPACE).
# Each client lives in   <workspace>\sites\<slug>\site.json
# and is picked with     $env:WPU_SITE = '<slug>'
#
# There is deliberately NO fallback to "the last site": these scripts write to
# live client sites, and pointing one at the previous client because a default
# was left over is the accident worth engineering out.
#
# Old configs still work: WPU_SITE (or WPSB_CONFIG / WPSD_CONFIG) may name a
# config.<x>.json file from wp-site-build or wp-site-doctor. Live secrets found
# inside a config file are used, with a warning to move them to the store.
. "$PSScriptRoot\_secrets.ps1"

$script:PluginRoot = Split-Path $PSScriptRoot -Parent
$script:Workspace  = if ($env:WPU_WORKSPACE) { $env:WPU_WORKSPACE } else { (Get-Location).Path }

function Resolve-WpuSite {
    $want = $env:WPU_SITE
    if (-not $want) { $want = $env:WPSB_CONFIG }
    if (-not $want) { $want = $env:WPSD_CONFIG }
    if (-not $want) {
        throw "No site selected. Run:  `$env:WPU_SITE = '<slug>'   (folders in $script:Workspace/sites)"
    }
    $candidates = @(
        (Join-Path $script:Workspace "sites/$want/site.json"),
        (Join-Path $script:Workspace $want),
        (Join-Path $script:Workspace "config.$want.json"),
        (Join-Path $script:Workspace "$want.json")
    )
    foreach ($c in $candidates) { if (Test-Path $c -PathType Leaf) { return @{ Slug = ($want -replace '^config\.|\.json$', ''); Path = (Resolve-Path $c).Path } } }
    throw "WPU_SITE='$want' matched nothing. Looked for sites/$want/site.json and config.$want.json in $script:Workspace"
}

$script:Site    = Resolve-WpuSite
$script:SiteDir = Split-Path $script:Site.Path -Parent
$raw = [IO.File]::ReadAllText($script:Site.Path) -replace "^﻿", ''
$script:Cfg = $raw | ConvertFrom-Json

# Pull secrets from the store into the in-memory config. Never written back to disk.
function Add-WpuSecretsToConfig {
    $slug = $script:Site.Slug.ToLower()
    $r = $script:Cfg.remote
    if ($r) {
        if ($r.key -or $r.appPassword) {
            Write-Host "WARNING: $($script:Site.Path) holds a live credential. Move it to your secret store (scripts/wpu-secret.ps1 set $slug key) and delete it from the file." -ForegroundColor Yellow
        }
        if (-not $r.key) {
            $k = Get-WpuSecret -Scope $slug -Name 'key'
            if ($k) { $r | Add-Member -NotePropertyName key -NotePropertyValue $k -Force }
        }
        if (-not $r.key -and -not $r.appPassword) {
            $ap = Get-WpuSecret -Scope $slug -Name 'apppassword'
            if ($ap) { $r | Add-Member -NotePropertyName appPassword -NotePropertyValue $ap -Force }
        }
    }
    if (-not $script:Cfg.pass) {
        $p = Get-WpuSecret -Scope $slug -Name 'adminpass'
        if ($p) { $script:Cfg | Add-Member -NotePropertyName pass -NotePropertyValue $p -Force }
    }
}
Add-WpuSecretsToConfig
