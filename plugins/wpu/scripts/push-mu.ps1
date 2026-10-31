# Copy this site's mu-plugins from the repo into the LocalWP install, parse-checking each file first.
# The repo copy under remote-files/<site>/mu-plugins is the source of truth; the site gets a copy.
#
#   powershell -File scripts/push-mu.ps1 remote-files/tractorsupply/mu-plugins
#   powershell -File scripts/push-mu.ps1 remote-files/tractorsupply/mu-plugins/tsc-theme.php
. "$PSScriptRoot\_common.ps1"

if ($args.Count -lt 1) {
    Write-Host 'usage: powershell -File scripts/push-mu.ps1 <file-or-folder>'
    exit 2
}

$src = (Resolve-Path $args[0] -ErrorAction Stop).Path
$files = if (Test-Path $src -PathType Container) { Get-ChildItem $src -Filter *.php -File } else { Get-Item $src }

$dest = Join-Path $script:Cfg.sitePath 'wp-content/mu-plugins'
if (-not (Test-Path $dest)) { New-Item -ItemType Directory -Force -Path $dest | Out-Null }

foreach ($f in $files) {
    # Never ship a file that will not parse - an mu-plugin fatal takes the whole site down.
    $lint = & $script:Php @($script:PhpArgs) -l $f.FullName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "PARSE ERROR in $($f.Name)" -ForegroundColor Red
        Write-Host $lint
        exit 1
    }
    Copy-Item $f.FullName (Join-Path $dest $f.Name) -Force
    Write-Host ("  ok  {0,-34} {1,7:N0} bytes" -f $f.Name, $f.Length)
}
Write-Host "-> $dest"
