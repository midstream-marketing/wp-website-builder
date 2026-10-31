# Read or write a file under the remote wp-content.
#
#   powershell -File scripts/rfile.ps1 get mu-plugins/awl-account.php
#   powershell -File scripts/rfile.ps1 get mu-plugins/awl-account.php ./local-copy.php
#   powershell -File scripts/rfile.ps1 put ./awl-account.php mu-plugins/awl-account.php
#
# Use this rather than /run for anything file-shaped. Writing an mu-plugin
# through a PHP script means escaping a PHP file inside a PHP string, which is
# where the mistakes live - this sends the bytes as bytes.
#
# The server refuses anything outside wp-content, and parse-checks .php files
# BEFORE writing, because an unparseable mu-plugin white-screens the whole site
# and you would then have no way in to fix it.
. "$PSScriptRoot\_remote.ps1"

if ($args.Count -lt 2) {
    Write-Host 'usage: powershell -File scripts/rfile.ps1 get <remote-path> [local-out]'
    Write-Host '       powershell -File scripts/rfile.ps1 put <local-file> <remote-path>'
    Write-Host ''
    Write-Host 'remote-path is relative to wp-content, e.g. mu-plugins/awl-account.php'
    exit 2
}

$mode = $args[0].ToLower()

switch ($mode) {

    'get' {
        $remote = $args[1]
        $r = Invoke-Wpsb -Route ("/file?path={0}" -f [Uri]::EscapeDataString($remote)) -TimeoutSec 120
        $bytes = [Convert]::FromBase64String($r.content_b64)

        if ($args.Count -ge 3) {
            $out = $args[2]
            [IO.File]::WriteAllBytes((Join-Path (Get-Location) $out), $bytes)
            Write-Host ("{0} -> {1}  ({2} bytes, modified {3})" -f $remote, $out, $r.bytes, $r.modified)
        }
        else {
            [Text.Encoding]::UTF8.GetString($bytes)
        }
    }

    'put' {
        $local = (Resolve-Path $args[1] -ErrorAction Stop).Path
        $remote = $args[2]
        if (-not $remote) { throw 'put needs a remote path: scripts/rfile.ps1 put <local-file> <remote-path>' }

        $bytes = [IO.File]::ReadAllBytes($local)

        $r = Invoke-Wpsb -Route '/file' -Method 'POST' -TimeoutSec 120 -Body @{
            path        = $remote
            content_b64 = [Convert]::ToBase64String($bytes)
        }

        Write-Host ("wrote wp-content/{0}  ({1} bytes)" -f $r.path, $r.bytes) -ForegroundColor Green
        if ($r.linted) { Write-Host '  PHP parse check passed' -ForegroundColor DarkGray }
        if ($r.backup) { Write-Host ("  previous version kept as {0}" -f $r.backup) -ForegroundColor DarkGray }
    }

    default {
        throw "unknown mode '$mode' - expected get or put"
    }
}
