# Tail the remote fatal-error log.
#
#   powershell -File scripts/rlog.ps1
#   powershell -File scripts/rlog.ps1 500
#
# The log is where the real answer usually is - see knowledge/GOTCHAS.md, "Where the
# errors actually are". If this reports nothing readable, WP_DEBUG_LOG is off
# and you are guessing rather than diagnosing.
. "$PSScriptRoot\_remote.ps1"

$lines = 200
if ($args.Count -ge 1) { $lines = [int]$args[0] }

$r = Invoke-Wpsb -Route ("/log?lines={0}" -f $lines) -TimeoutSec 120

if (-not $r.ok) {
    Write-Host $r.note -ForegroundColor Yellow
    Write-Host ''
    Write-Host 'looked in:' -ForegroundColor DarkGray
    foreach ($p in $r.checked) { Write-Host "  $p" -ForegroundColor DarkGray }
    exit 1
}

Write-Host ("{0}  ({1} bytes, last {2} lines)" -f $r.path, $r.size, $r.lines) -ForegroundColor DarkGray
Write-Host ''
Write-Host $r.log
