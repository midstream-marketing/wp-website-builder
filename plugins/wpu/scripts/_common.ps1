# Shared config + PHP argument list for the wrappers.
#
# Local's bundled php.exe ships WITHOUT a php.ini, so every extension has to be
# loaded explicitly or scripts die on undefined functions (mysqli_connect,
# mb_strlen, curl_init...). And this site's MySQL is on a non-default port.
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\_site.ps1"   # picks the site from $env:WPU_SITE (sites/<slug>/site.json)
$script:Root = $script:PluginRoot

if (-not $script:Cfg.phpDir -or -not (Test-Path $script:Cfg.phpDir)) {
    throw "phpDir is not set or does not exist. Run: powershell -File scripts/detect.ps1"
}

$script:Php = Join-Path $script:Cfg.phpDir 'php.exe'

$script:PhpArgs = @(
    '-d', "extension_dir=$($script:Cfg.phpDir)\ext"
    '-d', 'extension=php_mysqli.dll'
    '-d', 'extension=php_mbstring.dll'
    '-d', 'extension=php_openssl.dll'
    '-d', 'extension=php_curl.dll'
    '-d', 'extension=php_zip.dll'
    '-d', 'extension=php_gd.dll'
    '-d', 'extension=php_exif.dll'
    '-d', 'extension=php_fileinfo.dll'
    '-d', 'extension=php_intl.dll'
    '-d', 'extension=php_sodium.dll'
    '-d', 'memory_limit=512M'
)

if ($script:Cfg.dbPort) {
    $script:PhpArgs += @('-d', "mysqli.default_port=$($script:Cfg.dbPort)")
}

# Plugins that read $_SERVER['HTTP_HOST'] at load time warn on every CLI call
# without this. Harmless noise, but it buries real output.
# NB: $host is a read-only PowerShell built-in — never use that variable name.
$script:SiteHost = $script:Cfg.baseUrl -replace '^https?://', '' -replace '/$', ''
$env:HTTP_HOST = $script:SiteHost
$env:SERVER_NAME = $script:SiteHost
