# Save every public URL of the remote site to sites/<slug>/shots/url-inventory.json.
# The SEO, link and responsive audits read that file.
#
#   powershell -File scripts/rinventory.ps1
. "$PSScriptRoot\_remote.ps1"

$code = [IO.File]::ReadAllBytes((Join-Path $script:Root 'php/url-inventory.php'))
$r = Invoke-Wpu -Route '/run' -Method 'POST' -TimeoutSec 300 -Body @{ code_b64 = [Convert]::ToBase64String($code); filename = 'url-inventory.php'; args = @() }
if (-not $r.ok) { Write-WpuResult $r }

$shots = Join-Path $script:SiteDir 'shots'
if (-not (Test-Path $shots)) { New-Item -ItemType Directory -Force -Path $shots | Out-Null }
$out = Join-Path $shots 'url-inventory.json'
[IO.File]::WriteAllText($out, $r.output, (New-Object System.Text.UTF8Encoding($false)))

$inv = $r.output | ConvertFrom-Json
foreach ($t in $inv.types.PSObject.Properties) { Write-Host ("  {0,-22} {1,5}" -f $t.Name, @($t.Value).Count) }
Write-Host "-> $out" -ForegroundColor DarkGray
