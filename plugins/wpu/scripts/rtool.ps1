# Typed tools on the remote site, through the bridge's /tools and /tool routes (WPU Bridge 2.1+).
#
# A tool is a fixed, named action with checked arguments: page content, Gutenberg blocks, page builders
# (Elementor text and templates, Divi 4 layouts, Bricks, Beaver Builder, Breakdance, SeedProd), WooCommerce,
# ACF, updates and draft themes. No code is sent or run. Changes are logged and almost all can be undone.
#
#   powershell -File scripts/rtool.ps1 list [word]                 every tool this site offers (filter by a word)
#   powershell -File scripts/rtool.ps1 info <tool>[,<tool>]        what a tool does and its arguments
#   powershell -File scripts/rtool.ps1 <tool> [args.json]          run a tool that only reads, or a dry run
#   powershell -File scripts/rtool.ps1 <tool> <args.json> apply    run a tool that CHANGES the site (asks first)
#   powershell -File scripts/rtool.ps1 undo <change_id> apply      put one change back
#
# args.json is a file holding the tool's arguments as a JSON object, e.g. sites/<slug>/work/hero.args.json:
#   { "id": 42, "operations": [ { "op": "set_content", "path": "0.0.0.0", "content": "<p>New text</p>" } ] }
# Short arguments can be given inline instead of a file:  rtool.ps1 content_get '{"id":42}'
# The result is printed as JSON. Without the word apply, a tool that changes things only does a dry run
# (if it has one) or is refused: the site decides that, not this script.
. "$PSScriptRoot\_remote.ps1"

if ($args.Count -lt 1) {
    Get-Content $PSCommandPath | Select-Object -Skip 1 -First 15 | ForEach-Object { $_ -replace '^# ?', '' }
    exit 2
}

function Show-WpuJson($Value) {
    if ($null -eq $Value) { Write-Output 'null'; return }
    Write-Output ($Value | ConvertTo-Json -Depth 60)
}

$mode = [string]$args[0]

if ($mode -eq 'list') {
    $r = Invoke-Wpu -Route '/tools'
    $word = if ($args.Count -ge 2) { [string]$args[1] } else { '' }
    foreach ($t in $r.tools) {
        if ($word -and ($t.name -notlike "*$word*") -and ($t.title -notlike "*$word*")) { continue }
        Write-Host ("{0,-30} {1,-7} {2}  ({3})" -f $t.name, $(if ($t.writes) { 'CHANGES' } else { 'reads' }), $t.title, ($t.args -join ', '))
    }
    if ($r.not_available_here -and -not $word) {
        Write-Host ''
        Write-Host ("Not available on this site (plugin not active, or switched off under Tools > WPU Bridge): {0}" -f ($r.not_available_here -join ', ')) -ForegroundColor DarkGray
    }
    exit 0
}

if ($mode -eq 'info') {
    if ($args.Count -lt 2) { Stop-Wpu 'info needs a tool name' }
    $names = ([string]$args[1]) -replace '[^a-z0-9_,]', ''
    $r = Invoke-Wpu -Route "/tools?name=$names"
    if (-not $r.tools -or @($r.tools).Count -eq 0) { Stop-Wpu "No tool called '$names' on this site. Run: rtool.ps1 list" }
    Show-WpuJson $r.tools
    exit 0
}

$tool  = $mode
$apply = $false
$argsJson = '{}'
$rest = @($args | Select-Object -Skip 1)

if ($tool -eq 'undo') {
    if ($rest.Count -lt 1) { Stop-Wpu 'undo needs a change_id (see: rtool.ps1 changes_list)' }
    $id = ([string]$rest[0]) -replace '[^A-Za-z0-9_-]', ''
    $argsJson = '{"change_id":"' + $id + '"}'
    $tool = 'change_undo'
    $rest = @($rest | Select-Object -Skip 1)
}
foreach ($a in $rest) {
    $a = [string]$a
    if ($a -eq 'apply') { $apply = $true; continue }
    if ($tool -eq 'change_undo' -and $argsJson -ne '{}') { continue }
    if ($a.TrimStart().StartsWith('{')) { $argsJson = $a }
    elseif (Test-Path -LiteralPath $a) { $argsJson = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $a).Path) -replace "^﻿", '' }
    else { Stop-Wpu "'$a' is not a file, not JSON and not the word apply." }
}
if ($tool -notmatch '^[a-z0-9_]+$') { Stop-Wpu "'$tool' is not a tool name. Run: rtool.ps1 list" }
try { $null = $argsJson | ConvertFrom-Json } catch { Stop-Wpu "The arguments are not valid JSON: $($_.Exception.Message)" }
if (-not $argsJson.TrimStart().StartsWith('{')) { Stop-Wpu 'The arguments must be a JSON object: { ... }' }

# "apply" travels in the address, never in the JSON, so nothing inside the arguments can switch it on.
$body  = '{"tool":"' + $tool + '","args":' + $argsJson + '}'
$route = if ($apply) { '/tool?apply=1' } else { '/tool' }
$r = Invoke-Wpu -Route $route -Method 'POST' -TimeoutSec 600 -Body $body -RawJson

if (-not $r.ok) {
    Write-Host ''
    Write-Host ("{0}: {1}" -f $tool, $r.error) -ForegroundColor Red
    Write-Host ''
    exit 1
}
Show-WpuJson $r.result
if ($r.result.change_id) {
    Write-Host ''
    Write-Host ("undo with:  rtool.ps1 undo {0} apply" -f $r.result.change_id) -ForegroundColor DarkGray
}
