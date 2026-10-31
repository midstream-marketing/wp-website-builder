# Run a PHP script against the site by bootstrapping wp-load.php directly.
#
#   powershell -File scripts/wpphp.ps1 php/site-info.php
#   powershell -File scripts/wpphp.ps1 my-migration.php
#
# THIS IS THE RELIABLE PATH. Prefer it over `wp eval-file` for anything that
# matters — eval-file silently no-ops on larger files (see knowledge/GOTCHAS.md).
#
# The script you pass does NOT need to require wp-load itself; this wrapper
# prepends it. Write plain WordPress code and it will work.
. "$PSScriptRoot\_common.ps1"

if ($args.Count -lt 1) {
    Write-Host 'usage: powershell -File scripts/wpphp.ps1 <script.php> [args...]'
    exit 2
}

$target = (Resolve-Path $args[0] -ErrorAction Stop).Path -replace '\\', '/'
# The @( ) MUST wrap the whole if-statement, not sit inside it. PowerShell
# unrolls a statement's output on assignment, so `$rest = if (..) { @($x) }`
# collapses a one-element array back to a bare String. Splatting a String with
# @rest then enumerates its CHARACTERS - "apply" arrives as a,p,p,l,y and the
# script silently sees the wrong argv. See knowledge/GOTCHAS.md.
$rest = @( if ($args.Count -gt 1) { $args[1..($args.Count - 1)] } )

$wpLoad = (Join-Path $script:Cfg.sitePath 'wp-load.php') -replace '\\', '/'

if (-not (Test-Path $wpLoad)) {
    throw "wp-load.php not found at $wpLoad - check sitePath in config.json"
}

# Some plugins read $_SERVER['HTTP_HOST'] at load time and warn without it.
# NB: $host is a read-only PowerShell built-in — do not use that name.
$siteHost = $script:Cfg.baseUrl -replace '^https?://', '' -replace '/$', ''

# A tiny shim so the target script does not have to know where WordPress is.
$shim = Join-Path $env:TEMP ("wpsb-shim-" + [guid]::NewGuid().ToString('N') + ".php")

# REQUEST_URI must NOT be '/'. With a warm page cache, WP Rocket's output buffer
# recognises '/' as a cacheable front-end hit, `readfile()`s the cached homepage
# and calls exit() from inside wp-load — your script never runs and you get a
# page of HTML instead of your output. It refuses any URI with a .php extension
# (Buffer\Tests::is_rejected_extension), so a .php path sidesteps it while
# leaving the request a normal GET. See knowledge/GOTCHAS.md.
$lines = @(
    '<?php'
    "define('WP_USE_THEMES', false);"
    "define('DONOTCACHEPAGE', true);"
    "define('DONOTCACHEOBJECT', true);"
    "define('DONOTMINIFY', true);"
    "`$_SERVER['HTTP_HOST'] = '$siteHost';"
    "`$_SERVER['SERVER_NAME'] = '$siteHost';"
    "`$_SERVER['REQUEST_URI'] = '/wpsb-cli.php';"
    "`$_SERVER['REQUEST_METHOD'] = 'GET';"
    "require_once '$wpLoad';"
    # Run as an administrator, as the remote bridge does (it executes as the authenticated admin). With
    # no current user, capability-checked code refuses: e.g. update_option('blogname') makes Elementor
    # sync the name into its kit, which throws "Access denied" and aborts the script mid-plan.
    "if ( ! get_current_user_id() ) { `$wpsb_admins = get_users( array( 'role' => 'administrator', 'number' => 1, 'fields' => 'ID', 'orderby' => 'ID' ) ); if ( `$wpsb_admins ) { wp_set_current_user( (int) `$wpsb_admins[0] ); } }"
    "require '$target';"
)

Set-Content -Path $shim -Value $lines -Encoding utf8

try {
    & $script:Php @($script:PhpArgs) '-d' 'display_errors=1' '-d' 'error_reporting=E_ALL & ~E_DEPRECATED & ~E_NOTICE' $shim @rest
}
finally {
    Remove-Item $shim -Force -ErrorAction SilentlyContinue
}
