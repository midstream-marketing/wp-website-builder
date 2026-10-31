# Preflight the bridge on a client host.
#
#   powershell -File scripts/rdoctor.ps1
#
# RUN THIS FIRST on every new site. The failure modes below all look identical
# from the outside - a call that does not work - and guessing between them is
# what burns an afternoon.
. "$PSScriptRoot\_remote.ps1"

Write-Host ("probing {0}" -f $script:Cfg.remote.url) -ForegroundColor DarkGray
Write-Host ''

$d = Invoke-Wpsd -Route '/doctor' -TimeoutSec 60

function Row($label, $value, $bad = $false) {
    $colour = 'Gray'
    if ($bad) { $colour = 'Yellow' }
    Write-Host ("  {0,-26} {1}" -f $label, $value) -ForegroundColor $colour
}

Write-Host 'BRIDGE' -ForegroundColor Cyan
Row 'version'        $d.bridge.version
Row 'expires'        ("{0}  ({1} days left)" -f $d.bridge.expires_at, $d.bridge.days_left) ($d.bridge.days_left -le 5)

Write-Host ''
Write-Host 'SITE' -ForegroundColor Cyan
Row 'url'            $d.site.url
Row 'authenticated'  $d.site.user
Row 'wordpress'      $d.site.wp
Row 'php'            $d.site.php
Row 'mysql'          $d.site.mysql
Row 'https'          $d.site.is_ssl (-not $d.site.is_ssl)

Write-Host ''
Write-Host 'STACK' -ForegroundColor Cyan
Row 'theme'          $d.stack.theme
Row 'active plugins' $d.stack.active_plugins
if ($d.stack.elementor)   { Row 'elementor'   $d.stack.elementor }
if ($d.stack.woocommerce) { Row 'woocommerce' $d.stack.woocommerce }

Write-Host ''
Write-Host 'LIMITS' -ForegroundColor Cyan
Row 'memory_limit'       $d.limits.memory_limit
Row 'max_execution_time' $d.limits.max_execution_time
Row 'set_time_limit()'   $d.limits.set_time_limit_works (-not $d.limits.set_time_limit_works)
Row 'post_max_size'      $d.limits.post_max_size

Write-Host ''
Write-Host 'CHECKS' -ForegroundColor Cyan
if ($d.checks.auth) { Row 'signed in with' $(if ($d.checks.member) { "$($d.checks.auth) ($($d.checks.member))" } else { $d.checks.auth }) }
Row 'SEO plugin'     $d.checks.seo_plugin ($d.checks.seo_plugin -in @('none', 'aioseo', 'seopress'))
Row 'Authorization header' $d.checks.authorization_header_seen ((-not $d.checks.authorization_header_seen) -and (-not $R.key))
Row 'app passwords'        $d.checks.app_passwords_available
Row 'WP_DEBUG_LOG'         $d.checks.wp_debug_log (-not $d.checks.wp_debug_log)
Row 'wp-content writable'  $d.checks.content_writable (-not $d.checks.content_writable)
Row 'mu-plugins dir'       $d.checks.mu_plugins_dir
Row 'object cache'         $d.checks.object_cache
Row 'security plugins'     $(if ($d.checks.security_plugins.Count) { $d.checks.security_plugins -join ', ' } else { 'none detected' }) ($d.checks.security_plugins.Count -gt 0)

# --- the warnings that actually predict trouble -----------------------------
$warn = @()

if (-not $d.site.is_ssl) {
    $warn += 'Site is not HTTPS. Application Passwords are refused by core over plain HTTP; this only worked because WPU_BRIDGE_ALLOW_HTTP is defined. Do not use that on a live site.'
}
if (-not $d.limits.set_time_limit_works -and [int]$d.limits.max_execution_time -gt 0 -and [int]$d.limits.max_execution_time -lt 120) {
    $warn += "max_execution_time is $($d.limits.max_execution_time)s and set_time_limit() is blocked. Long scripts will be killed PART WAY THROUGH - a half-written _elementor_data is worse than no change. Split large jobs and always dry-run first."
}
if (-not $d.checks.wp_debug_log) {
    $warn += 'WP_DEBUG_LOG is off, so scripts/rlog.ps1 has nothing to read. Ask for it to be enabled in wp-config.php, or you are debugging blind.'
}
if (-not $d.checks.content_writable) {
    $warn += 'wp-content is not writable by PHP. scripts/rfile.ps1 will fail, and so will anything that writes an mu-plugin.'
}
if ($d.checks.security_plugins.Count) {
    $warn += "Security plugin present ($($d.checks.security_plugins -join ', ')). These commonly block REST authentication or rate-limit repeated POSTs. If calls start failing intermittently, look here first."
}
if ($d.bridge.days_left -le 5) {
    $warn += "The bridge expires in $($d.bridge.days_left) days and will then stop responding."
}

Write-Host ''
if ($warn.Count) {
    Write-Host 'WARNINGS' -ForegroundColor Yellow
    foreach ($w in $warn) { Write-Host "  - $w" -ForegroundColor Yellow; Write-Host '' }
} else {
    Write-Host 'No warnings - this host looks straightforward.' -ForegroundColor Green
}
