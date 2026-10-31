# Fills in the LocalWP-specific parts of the selected site's site.json automatically
# (only needed when the site is built or fixed in LocalWP rather than live).
#
# Finds:
#   phpDir  - Local's bundled PHP (it ships without a php.ini, hence the -d flags elsewhere)
#   wpCli   - Local's bundled wp-cli.phar
#   dbPort  - this site's MySQL port, which is NOT the one in wp-config.php
#
# Usage:  powershell -File scripts/detect.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
. "$PSScriptRoot\_site.ps1"
$cfgPath = $script:Site.Path
# Re-read from disk: _site.ps1 adds secrets to the in-memory copy, and those must never be written back.
$cfg = [IO.File]::ReadAllText($cfgPath) -replace "^\uFEFF", '' | ConvertFrom-Json

# --- Local's PHP -----------------------------------------------------------
$lightning = "$env:LOCALAPPDATA\Programs\Local\resources\extraResources\lightning-services"

if (Test-Path $lightning) {
    $php = Get-ChildItem $lightning -Directory -Filter 'php-*' |
        Sort-Object Name -Descending |
        ForEach-Object {
            foreach ($arch in @('win64', 'win32')) {
                $p = Join-Path $_.FullName "bin\$arch\php.exe"
                if (Test-Path $p) { return (Split-Path $p -Parent) }
            }
        } | Select-Object -First 1

    if ($php) {
        $cfg.phpDir = $php
        Write-Host "phpDir : $php"
    }
}

# --- Local's wp-cli --------------------------------------------------------
$wpcli = "$env:LOCALAPPDATA\Programs\Local\resources\extraResources\bin\wp-cli\wp-cli.phar"
if (Test-Path $wpcli) {
    $cfg.wpCli = $wpcli
    Write-Host "wpCli  : $wpcli"
}

# --- This site's MySQL port ------------------------------------------------
# wp-config.php says DB_HOST=localhost, but Local runs each site's MySQL on its
# own port. Without this, every DB connection fails with a vague error.
$sitesJson = "$env:APPDATA\Local\sites.json"

if ((Test-Path $sitesJson) -and $cfg.sitePath) {
    $sites = Get-Content $sitesJson -Raw | ConvertFrom-Json
    $want = ($cfg.sitePath -replace '\\', '/').TrimEnd('/').ToLower()

    foreach ($prop in $sites.PSObject.Properties) {
        $s = $prop.Value

        # Local stores paths with a leading ~ for the user profile.
        $path = ($s.path -replace '^~', $env:USERPROFILE) -replace '\\', '/'
        $path = $path.TrimEnd('/').ToLower()

        if ($want -eq $path -or $want.StartsWith("$path/")) {
            # The port is nested: services.mysql.ports.MYSQL is an array.
            $port = $s.services.mysql.ports.MYSQL

            if ($port -is [array]) { $port = $port[0] }

            if ($port) {
                $cfg.dbPort = [string]$port
                Write-Host "dbPort : $($cfg.dbPort)   (site '$($s.name)')"
            }
            break
        }
    }
}

if (-not $cfg.dbPort) {
    Write-Warning "Could not determine the DB port. Open $sitesJson and copy services.mysql.port for this site into site.json."
}

# Written without a BOM: Set-Content -Encoding utf8 adds one, and JSON.parse
# rejects it. See knowledge/GOTCHAS.md.
$json = $cfg | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($cfgPath, $json, (New-Object System.Text.UTF8Encoding($false)))

Write-Host "`nwrote $cfgPath"
Write-Host "Now check: baseUrl, sitePath, user, urls. The admin password goes in your secret store: scripts/wpu-secret.ps1 set <site> adminpass"
