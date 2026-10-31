# Bring client sites from wp-site-build / wp-site-doctor into the WP Ultimate Build workspace.
#
#   powershell -File scripts/migrate-legacy.ps1 -From "C:\Users\me\Desktop\wp-site-doctor"          dry run
#   powershell -File scripts/migrate-legacy.ps1 -From "C:\Users\me\Desktop\wp-site-doctor" -Apply   do it
#
# For every config.<site>.json in the old folder:
#   - writes sites/<site>/site.json WITHOUT secrets (remote.key, remote.appPassword, pass, sftp.pass removed;
#     an old "sftp" block becomes hosting.sftp - run 'python tools/hosting/sftp.py trust' once per site after)
#   - moves those secrets into YOUR encrypted store (scripts/wpu-secret.ps1), for this Windows user only
#   - copies docs/SITE-NOTES-<site>.md -> sites/<site>/SITE-NOTES.md, plans/<site>.plan.json -> sites/<site>/plan.json
# Existing sites/<site>/ folders are never overwritten. The old folder is only read.
#
# Run it in your own terminal (it handles live credentials). Each team member who needs a
# site's key runs it for themselves, or saves the key with wpu-secret.ps1 set.
param(
    [Parameter(Mandatory = $true)][string] $From,
    [switch] $Apply
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\_secrets.ps1"

$ws = if ($env:WPU_WORKSPACE) { $env:WPU_WORKSPACE } else { (Get-Location).Path }
$sites = Join-Path $ws 'sites'
$From = (Resolve-Path $From).Path
$utf8 = New-Object System.Text.UTF8Encoding($false)

$configs = Get-ChildItem $From -Filter 'config.*.json' -File | Where-Object { $_.Name -notmatch '\.(bak|example)' -and $_.Name -ne 'config.example.json' }
Write-Host ("{0} config file(s) in {1}" -f $configs.Count, $From) -ForegroundColor Cyan
Write-Host ''

foreach ($c in $configs) {
    $slug = ($c.BaseName -replace '^config\.', '').ToLower() -replace '[^a-z0-9_-]', '-'
    $dest = Join-Path $sites $slug
    if (Test-Path (Join-Path $dest 'site.json')) { Write-Host ("  skip  {0,-28} already in the workspace" -f $slug) -ForegroundColor DarkGray; continue }

    $cfg = [IO.File]::ReadAllText($c.FullName) -replace "^\uFEFF", '' | ConvertFrom-Json
    $secrets = [ordered]@{}
    if ($cfg.remote) {
        if ($cfg.remote.key) { $secrets['key'] = [string]$cfg.remote.key; $cfg.remote.PSObject.Properties.Remove('key') }
        if ($cfg.remote.appPassword) { $secrets['apppassword'] = [string]$cfg.remote.appPassword; $cfg.remote.PSObject.Properties.Remove('appPassword') }
        $auth = if ($secrets.Contains('key')) { 'key' } else { 'apppassword' }
        $cfg.remote | Add-Member -NotePropertyName auth -NotePropertyValue $auth -Force
    }
    if ($cfg.pass -and $cfg.pass -ne 'changeme') { $secrets['adminpass'] = [string]$cfg.pass }
    $cfg.PSObject.Properties.Remove('pass')
    # Old Site Doctor "sftp" block (plain-text password) -> hosting.sftp without it, password to the store.
    if ($cfg.sftp) {
        if ($cfg.sftp.pass) { $secrets['sftp_pass'] = [string]$cfg.sftp.pass }
        $h = [ordered]@{ host = $cfg.sftp.host; port = $(if ($cfg.sftp.port) { [int]$cfg.sftp.port } else { 22 }); user = $cfg.sftp.user
                         root = $(if ($cfg.sftp.root) { ([string]$cfg.sftp.root) -replace '/wp-content/?$', '' } else { '' }); auth = 'password'; keyFile = '' }
        $cfg | Add-Member -NotePropertyName hosting -NotePropertyValue ([pscustomobject]@{ sftp = [pscustomobject]$h }) -Force
        $cfg.PSObject.Properties.Remove('sftp')
    }
    $cfg.PSObject.Properties.Remove('_comment')

    $notes = Join-Path $From "docs\SITE-NOTES-$($c.BaseName -replace '^config\.', '').md"
    $plan  = Join-Path $From "plans\$($c.BaseName -replace '^config\.', '').plan.json"
    $extra = @()
    if (Test-Path $notes) { $extra += 'notes' }
    if (Test-Path $plan) { $extra += 'plan' }
    Write-Host ("  {0}  {1,-28} {2,-34} secrets: {3}  {4}" -f $(if ($Apply) { 'add ' } else { 'would' }), $slug, $cfg.baseUrl, $(if ($secrets.Count) { ($secrets.Keys -join ',') } else { 'none' }), ($extra -join ' '))

    if (-not $Apply) { continue }
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    [IO.File]::WriteAllText((Join-Path $dest 'site.json'), ($cfg | ConvertTo-Json -Depth 10), $utf8)
    foreach ($k in $secrets.Keys) {
        Set-WpuSecret -Scope $slug -Name $k -Value (ConvertTo-SecureString $secrets[$k] -AsPlainText -Force)
    }
    if (Test-Path $notes) { Copy-Item $notes (Join-Path $dest 'SITE-NOTES.md') }
    if (Test-Path $plan) { Copy-Item $plan (Join-Path $dest 'plan.json') }
}

Write-Host ''
if ($Apply) {
    Write-Host 'Done. The old config files still hold live credentials - delete them (or the old folder) once you have checked a site works:' -ForegroundColor Yellow
    Write-Host '  $env:WPU_SITE = "<slug>"; powershell -File scripts/rdoctor.ps1' -ForegroundColor Yellow
} else {
    Write-Host '(dry run - add -Apply)' -ForegroundColor DarkGray
}
