# Build (or rebuild) a site from a plan file.
#
#   powershell -File scripts/rplan.ps1 plans/clientsite.plan.json          dry run - shows every change
#   powershell -File scripts/rplan.ps1 plans/clientsite.plan.json apply    makes them
#
# The plan is sent to build/apply-plan.php on the remote site through the bridge.
# apply-plan.php is IDEMPOTENT: every step checks the current state first and only
# changes what differs, so re-running after an interruption (a host that kills
# long requests) finishes the job instead of duplicating pages.
#
# Always dry-run first and read the output. The plan decides the site's pages,
# menus and front page - a typo there is a real change on a real site.
. "$PSScriptRoot\_remote.ps1"

if ($args.Count -lt 1) {
    Write-Host 'usage: powershell -File scripts/rplan.ps1 <plan.json> [apply]'
    exit 2
}

$planPath = (Resolve-Path $args[0] -ErrorAction Stop).Path
$apply = ($args.Count -ge 2 -and $args[1] -eq 'apply')

$planText = [IO.File]::ReadAllText($planPath) -replace "^﻿", ''
try { $null = $planText | ConvertFrom-Json } catch { Stop-Wpsb "plan is not valid JSON: $($_.Exception.Message)" }

$script = Join-Path $script:Root 'build/apply-plan.php'
$b64Script = [Convert]::ToBase64String([IO.File]::ReadAllBytes($script))
$b64Plan = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($planText))

$argList = @('plan_b64=' + $b64Plan)
if ($apply) { $argList += 'apply' }

Write-Host ("{0} {1} on {2}" -f $(if ($apply) { 'APPLYING' } else { 'dry run of' }), (Split-Path $planPath -Leaf), $script:Cfg.remote.url) -ForegroundColor $(if ($apply) { 'Yellow' } else { 'DarkGray' })
Write-Host ''

$result = Invoke-Wpsb -Route '/run' -Method 'POST' -Body @{
    code_b64 = $b64Script
    filename = 'apply-plan.php'
    args     = @($argList)
}

Write-WpsbResult $result
