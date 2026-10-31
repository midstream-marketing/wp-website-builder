# Apply one group of speed settings on the remote site, keeping a rollback file.
#
#   powershell -File scripts/rspeed.ps1 info                      read-only snapshot (php/speed-info.php)
#   powershell -File scripts/rspeed.ps1 <group>                   dry run
#   powershell -File scripts/rspeed.ps1 <group> apply             apply; saves sites/<slug>/perf/rollback/<group>-<time>.json
#   powershell -File scripts/rspeed.ps1 restore <rollback.json>   put those values back
#
# Groups: elementor, fonts, lazybg, cssfile, cssinline, transients (see php/speed-apply.php).
# The loop is: python tools/perf/psi.py run baseline -> apply ONE group -> psi.py run after-<group>
# -> psi.py compare baseline after-<group>. Worse? restore it.
. "$PSScriptRoot\_remote.ps1"

if ($args.Count -lt 1) {
    Get-Content $PSCommandPath | Select-Object -Skip 1 -First 10 | ForEach-Object { $_ -replace '^# ?', '' }
    exit 2
}

function Invoke-WpuScript([string] $Rel, [string[]] $ScriptArgs) {
    $code = [IO.File]::ReadAllBytes((Join-Path $script:Root $Rel))
    return Invoke-Wpu -Route '/run' -Method 'POST' -TimeoutSec 300 -Body @{ code_b64 = [Convert]::ToBase64String($code); filename = (Split-Path $Rel -Leaf); args = @($ScriptArgs) }
}

$mode = $args[0].ToLower()
if ($mode -eq 'info') { Write-WpuResult (Invoke-WpuScript 'php/speed-info.php' @()); exit 0 }

if ($mode -eq 'restore') {
    if ($args.Count -lt 2) { Stop-Wpu 'restore needs a rollback json file' }
    $json = [IO.File]::ReadAllText((Resolve-Path $args[1]).Path)
    $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($json))
    Write-WpuResult (Invoke-WpuScript 'php/speed-apply.php' @("restore_b64=$b64", 'apply'))
    exit 0
}

$apply = ($args.Count -ge 2 -and $args[1] -eq 'apply')
$sargs = @("group=$mode"); if ($apply) { $sargs += 'apply' }
$r = Invoke-WpuScript 'php/speed-apply.php' $sargs

$text = [string]$r.output
$m = [regex]::Match($text, '(?m)^BEFORE_JSON (.*)$')
Write-Host ($text -replace '(?m)^BEFORE_JSON .*$', '').TrimEnd()

if ($apply -and $m.Success -and $m.Groups[1].Value -ne '{}' -and $m.Groups[1].Value -ne '[]') {
    $dir = Join-Path $script:SiteDir 'perf/rollback'
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $file = Join-Path $dir ("{0}-{1}.json" -f $mode, (Get-Date -Format 'yyyyMMdd-HHmmss'))
    [IO.File]::WriteAllText($file, $m.Groups[1].Value, (New-Object System.Text.UTF8Encoding($false)))
    Write-Host "rollback -> $file" -ForegroundColor Yellow
}
if (-not $r.ok) { exit 1 }
