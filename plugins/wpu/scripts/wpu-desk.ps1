# Start WPU Desk - the local dashboard for WP Ultimate Build.
#
#   powershell -ExecutionPolicy Bypass -File scripts\wpu-desk.ps1 -InstallShortcut [-Workspace "$env:USERPROFILE\Desktop\WPU-Work"]
#       one-time: puts a "WPU Desk" shortcut on your Desktop (it keeps working after plugin updates)
#   powershell -ExecutionPolicy Bypass -File scripts\wpu-desk.ps1 [-Workspace <folder>]
#       start the Desk now (opens your browser)
#
# The Desk runs the official Claude Code signed in with YOUR Claude account. Sign in once first:
# open a terminal, run "claude", and log in.
param(
    [string] $Workspace = '',
    [switch] $InstallShortcut
)
$ErrorActionPreference = 'Stop'
$home2 = Join-Path $env:APPDATA 'WPU'
New-Item -ItemType Directory -Force -Path $home2 | Out-Null
$prefs = Join-Path $home2 'desk.json'

# Remember the workspace so the shortcut needs no arguments.
if (-not $Workspace -and (Test-Path $prefs)) { try { $Workspace = (Get-Content $prefs -Raw | ConvertFrom-Json).workspace } catch { } }
if (-not $Workspace) {
    $guess = Join-Path ([Environment]::GetFolderPath('Desktop')) 'WPU-Work'
    $Workspace = $guess
}
if (-not (Test-Path $Workspace)) { New-Item -ItemType Directory -Force -Path $Workspace | Out-Null }
$Workspace = (Resolve-Path $Workspace).Path
[IO.File]::WriteAllText($prefs, (@{ workspace = $Workspace } | ConvertTo-Json), (New-Object System.Text.UTF8Encoding($false)))

if ($InstallShortcut) {
    # A stable copy of this launcher: the plugin's own folder name changes with every update.
    $stable = Join-Path $home2 'wpu-desk.ps1'
    Copy-Item -Force $PSCommandPath $stable
    $lnk = Join-Path ([Environment]::GetFolderPath('Desktop')) 'WPU Desk.lnk'
    $sh = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk)
    $sh.TargetPath = (Get-Command powershell.exe).Source
    $sh.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$stable`""
    # Not the workspace: programs are never looked up in a folder that jobs write to.
    $sh.WorkingDirectory = $home2
    $sh.Description = 'WPU Desk - WP Ultimate Build dashboard'
    $sh.Save()
    Write-Host "Shortcut created on your Desktop: WPU Desk (workspace: $Workspace)" -ForegroundColor Green
    return
}

# Find the Desk: next to this script when run from the plugin, else the newest installed plugin.
$server = Join-Path (Split-Path $PSScriptRoot -Parent) 'desk\server.mjs'
if (-not (Test-Path $server)) {
    $cands = Get-ChildItem -Path (Join-Path $env:USERPROFILE '.claude\plugins') -Recurse -Filter 'server.mjs' -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match '[\\/]wpu[\\/].*[\\/]desk[\\/]server\.mjs$' } |
        Sort-Object LastWriteTime -Descending
    if (-not $cands) { throw 'WP Ultimate Build is not installed for this Windows user. Install the plugin in Claude Code first (/plugin install wpu@webelite-wpu).' }
    $server = $cands[0].FullName
}
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw 'Node.js is not installed. Install it from nodejs.org (LTS), then start the Desk again.' }
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) { Write-Warning 'Claude Code was not found. The Desk will open, but jobs need Claude Code installed and signed in.' }

$host.UI.RawUI.WindowTitle = 'WPU Desk - keep this window open'
$profileDir = [Environment]::GetFolderPath('UserProfile')
if (-not $Workspace.StartsWith($profileDir + '\', [StringComparison]::OrdinalIgnoreCase)) {
    Write-Warning "The workspace $Workspace is outside your user folder, so other Windows users on this PC may be able to read or change it. Use a folder under $profileDir (for example Desktop\WPU-Work) unless you are the only user."
}
Set-Location $home2
$env:NoDefaultCurrentDirectoryInExePath = '1'
$env:WPU_WORKSPACE = $Workspace
& node $server $Workspace
