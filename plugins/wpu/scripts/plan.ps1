# Local twin of scripts/rplan.ps1: apply a site plan to a LocalWP site through scripts/wpphp.ps1.
#
#   powershell -File scripts/plan.ps1 plans/client.plan.json          dry run
#   powershell -File scripts/plan.ps1 plans/client.plan.json apply    make the changes
#
# Same convention as the remote runner: read the dry run before applying, and re-run
# freely - every step compares the site's current state with the plan first.
. "$PSScriptRoot\_common.ps1"

if ($args.Count -lt 1) {
    Write-Host 'usage: powershell -File scripts/plan.ps1 <plan.json> [apply]'
    exit 2
}

$planPath = (Resolve-Path $args[0] -ErrorAction Stop).Path
$json = [IO.File]::ReadAllText($planPath)
try { $null = $json | ConvertFrom-Json } catch { throw "plan is not valid JSON: $($_.Exception.Message)" }

$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($json))
$rest = @( if ($args.Count -gt 1) { $args[1..($args.Count - 1)] } )

Write-Host "applying $(Split-Path $planPath -Leaf) to $($script:Cfg.baseUrl)"
& (Join-Path $PSScriptRoot 'wpphp.ps1') (Join-Path (Split-Path $PSScriptRoot -Parent) 'build/apply-plan.php') "plan_b64=$b64" @rest
