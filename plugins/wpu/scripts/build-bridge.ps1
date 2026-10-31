# Package the WPU Bridge as an installable plugin zip.
#
#   powershell -File scripts/build-bridge.ps1            -> <workspace>/dist/wpu-bridge.zip
#   powershell -File scripts/build-bridge.ps1 -Out x.zip
#
# Not Compress-Archive: Windows PowerShell writes backslash entry names and no
# directory entry, and WordPress then installs into a double-nested folder
# ("Plugin file does not exist" on Activate). Written by hand instead:
#   - forward-slash entry names, one top-level folder with an explicit entry
#   - LF line endings and no BOM on PHP (a BOM breaks the plugin header)
param([string] $Out = '')
$ErrorActionPreference = 'Stop'

$root = Split-Path $PSScriptRoot -Parent
$slug = 'wpu-bridge'
if (-not $Out) {
    $ws = if ($env:WPU_WORKSPACE) { $env:WPU_WORKSPACE } else { (Get-Location).Path }
    $dist = Join-Path $ws 'dist'
    if (-not (Test-Path $dist)) { New-Item -ItemType Directory -Force -Path $dist | Out-Null }
    $Out = Join-Path $dist 'wpu-bridge.zip'
}

$files = [ordered]@{
    'wpu-bridge.php' = Join-Path $root 'bridge/wpu-bridge.php'
    'index.php'      = Join-Path $root 'bridge/plugin-src/index.php'
    'readme.txt'     = Join-Path $root 'bridge/plugin-src/readme.txt'
}
foreach ($src in $files.Values) { if (-not (Test-Path $src)) { throw "missing source file: $src" } }

Add-Type -AssemblyName System.IO.Compression | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem | Out-Null
if (Test-Path $Out) { Remove-Item $Out -Force }

$fs  = [System.IO.File]::Open($Out, [System.IO.FileMode]::CreateNew)
$zip = New-Object System.IO.Compression.ZipArchive($fs, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    $zip.CreateEntry("$slug/") | Out-Null
    foreach ($dest in $files.Keys) {
        $bytes = [System.IO.File]::ReadAllBytes($files[$dest])
        if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { $bytes = $bytes[3..($bytes.Length - 1)] }
        if ($dest -match '\.(php|txt)$') {
            $text  = [System.Text.Encoding]::UTF8.GetString($bytes) -replace "`r`n", "`n"
            $bytes = (New-Object System.Text.UTF8Encoding($false)).GetBytes($text)
        }
        $entry  = $zip.CreateEntry("$slug/$dest", [System.IO.Compression.CompressionLevel]::Optimal)
        $stream = $entry.Open(); $stream.Write($bytes, 0, $bytes.Length); $stream.Close()
    }
}
finally { $zip.Dispose(); $fs.Dispose() }

Write-Host ("built {0}  ({1:N0} bytes)" -f $Out, (Get-Item $Out).Length) -ForegroundColor Green
Write-Host ''
Write-Host 'Install on a client site (no hosting access needed):' -ForegroundColor Cyan
Write-Host '  1. Plugins > Add New > Upload Plugin > this zip > Install Now > Activate'
Write-Host '     (or: node audit/install-bridge.mjs, with the admin login in your secret store)'
Write-Host '  2. Tools > WPU Bridge > type your name > Make a connection key'
Write-Host '  3. wpu-secret set <site> key        (paste the key; it is stored encrypted for your Windows user only)'
Write-Host '  4. powershell -File scripts/rdoctor.ps1'
Write-Host ''
Write-Host 'At handover: delete the plugin (this deletes every key).' -ForegroundColor Yellow
