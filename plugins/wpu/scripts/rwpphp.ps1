# Run a local PHP script against the REMOTE site, through the bridge plugin.
#
#   powershell -File scripts/rwpphp.ps1 php/site-info.php
#   powershell -File scripts/rwpphp.ps1 aw-fix-4.php apply
#
# This is the remote twin of scripts/wpphp.ps1 and takes the same arguments. The
# script is read from disk here and executed there; it does not need to exist on
# the server, and it does not need to require wp-load.php - WordPress is already
# loaded by the time it runs.
#
# $argv works exactly as it does locally, so the usual
#     $apply = in_array( 'apply', $argv, true );
# still does the right thing.
. "$PSScriptRoot\_remote.ps1"

if ($args.Count -lt 1) {
    Write-Host 'usage: powershell -File scripts/rwpphp.ps1 <script.php> [args...]'
    exit 2
}

$target = (Resolve-Path $args[0] -ErrorAction Stop).Path

# Same @( ) trap as scripts/wpphp.ps1: PowerShell unrolls a one-element array back to
# a bare String on assignment, and then "apply" is sent as six separate
# characters. Wrap the whole if-statement. See knowledge/GOTCHAS.md.
$rest = @( if ($args.Count -gt 1) { $args[1..($args.Count - 1)] } )

# Read as raw bytes. Get-Content -Raw would re-encode, and a UTF-8 em-dash in a
# replacement string is exactly the kind of thing these scripts match on.
$bytes = [IO.File]::ReadAllBytes($target)
$b64 = [Convert]::ToBase64String($bytes)

$name = Split-Path $target -Leaf

Write-Host ("running {0} on {1}" -f $name, $script:Cfg.remote.url) -ForegroundColor DarkGray
if ($rest.Count) { Write-Host ("args: {0}" -f ($rest -join ' ')) -ForegroundColor DarkGray }
Write-Host ''

$result = Invoke-Wpsb -Route '/run' -Method 'POST' -Body @{
    code_b64 = $b64
    filename = $name
    args     = @($rest)
}

Write-WpsbResult $result
