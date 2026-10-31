# Package a site plugin folder as an installable zip (forward-slash entry names, one top-level folder).
#
#   powershell -File scripts/build-plugin.ps1 <slug> <main.php> <includes-folder> [out.zip]
#   powershell -File scripts/build-plugin.ps1 cas-store remote-files/californiaautosupply/plugin/cas-store.php remote-files/californiaautosupply/mu-plugins
#
# Why not Compress-Archive: Windows PowerShell writes entries with backslashes, and on a Linux host
# WordPress's unzip then creates files literally named "cas-store\includes\x.php" (see build-bridge.ps1).
# Why a zip at all: some hosts (WP Engine) refuse PHP-created .php files, so code can only arrive through
# WordPress's own plugin uploader - install it with audit/install-plugin-zip.mjs.
param(
    [Parameter(Mandatory = $true)][string] $Slug,
    [Parameter(Mandatory = $true)][string] $Main,
    [Parameter(Mandatory = $true)][string] $Includes,
    [string] $Out = ''
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$root = Split-Path $PSScriptRoot -Parent
if (-not $Out) { $Out = Join-Path $root "remote\$Slug.zip" }

$files = [ordered]@{ "$Slug/$(Split-Path $Main -Leaf)" = (Resolve-Path $Main).Path }
# Everything under the includes folder, sub-folders kept (widgets/, assets/): php, css, js, svg, json.
$incRoot = (Resolve-Path $Includes).Path.TrimEnd([char]92)
foreach ($f in Get-ChildItem $incRoot -Recurse -File | Where-Object { $_.Extension -in '.php', '.css', '.js', '.svg', '.json' }) {
    $rel = $f.FullName.Substring($incRoot.Length + 1).Replace([string][char]92, '/')
    $files["$Slug/includes/$rel"] = $f.FullName
}

if (Test-Path $Out) { Remove-Item $Out -Force }
$fs  = [IO.File]::Open($Out, [IO.FileMode]::CreateNew)
$zip = New-Object System.IO.Compression.ZipArchive($fs, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    $zip.CreateEntry("$Slug/") | Out-Null
    $zip.CreateEntry("$Slug/includes/") | Out-Null
    foreach ($dir in ($files.Keys | ForEach-Object { Split-Path $_ -Parent } | ForEach-Object { $_.Replace([string][char]92, '/') } | Sort-Object -Unique)) {
        if ($dir -ne $Slug -and $dir -ne "$Slug/includes") { $zip.CreateEntry("$dir/") | Out-Null }
    }
    foreach ($entry in $files.Keys) {
        # Strip a UTF-8 BOM: before "<?php" it is output on every request ("headers already sent").
        $bytes = [IO.File]::ReadAllBytes($files[$entry])
        if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { $bytes = $bytes[3..($bytes.Length - 1)] }
        $e = $zip.CreateEntry($entry, [System.IO.Compression.CompressionLevel]::Optimal)
        $s = $e.Open(); $s.Write($bytes, 0, $bytes.Length); $s.Dispose()
        Write-Host ("  + {0,-40} {1,8:N0} bytes" -f $entry, $bytes.Length)
    }
}
finally { $zip.Dispose(); $fs.Dispose() }
Write-Host "-> $Out"
