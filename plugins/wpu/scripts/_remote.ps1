# Shared transport for the remote wrappers (WP Ultimate Build).
#
# Instead of a local php.exe pointed at wp-load.php, we POST to the WPU Bridge
# plugin on the live site. Everything above this layer - the scripts, the
# dry-run/apply convention, the knowledge base - is unchanged from WP Site
# Doctor / WP Site Build.
#
# sites/<slug>/site.json has a "remote" block with NO secrets in it:
#
#   "remote": { "url": "https://clientsite.com", "auth": "key" }
#   "remote": { "url": "https://clientsite.com", "auth": "apppassword", "user": "admin-login" }
#
# The key or Application Password comes from the member's own encrypted store
# (scripts/wpu-secret.ps1). Optional: "restRoute": true (WP Engine cached 404s),
# "useCurl": true (Cloudflare challenging .NET's TLS handshake).
$ErrorActionPreference = 'Stop'

# NB: a `trap` here would NOT work. Dot-sourcing carries functions and variables
# into the caller's scope, but not trap handlers, so a thrown error surfaced as a
# raw PowerShell stack dump with the throw site quoted back. Every failure path
# below therefore calls Stop-Wpu, which prints one line and exits.
function Stop-Wpu {
    param([string] $Message)
    Write-Host ''
    Write-Host "ERROR: $Message" -ForegroundColor Red
    Write-Host ''
    # [Environment]::Exit, not exit: during dot-sourcing, exit only leaves _remote.ps1
    # and the wrapper carries on with Invoke-Wpu undefined (seen in testing).
    [Environment]::Exit(1)
}

# try/catch does not open a new scope, so the dot-sourced variables stay ours.
try { . "$PSScriptRoot\_site.ps1" } catch { Stop-Wpu $_.Exception.Message }
$script:Root = $script:PluginRoot

if (-not $script:Cfg.remote) {
    Stop-Wpu @"
$($script:Site.Path) has no "remote" block. Add one:

  "remote": { "url": "https://clientsite.com", "auth": "key" }

then save the key with:  powershell -File scripts/wpu-secret.ps1 set $($script:Site.Slug) key
See knowledge/REMOTE.md.
"@
}

$R = $script:Cfg.remote
if (-not $R.url) { Stop-Wpu "$($script:Site.Path): remote.url is empty." }
if (-not $R.key -and -not ($R.user -and $R.appPassword)) {
    Stop-Wpu "No credential for '$($script:Site.Slug)'. Save the bridge key with:  powershell -File scripts/wpu-secret.ps1 set $($script:Site.Slug) key"
}

# Older hosts still negotiate down; without this, PS 5.1 can fail the handshake
# with a bare "underlying connection was closed" and no clue why.
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls11

$script:RemoteBase = ($R.url.TrimEnd('/')) + '/wp-json/wpu/v1'
# remote.restRoute = true: call /?rest_route=/wpu/v1... instead. WP Engine can keep serving a cached
# 404 for /wp-json/wpu/* from before the bridge was activated; the query-string form is not cached.
$script:RemoteRestRoute = [bool]$R.restRoute
if ($script:RemoteRestRoute) { $script:RemoteBase = ($R.url.TrimEnd('/')) + '/?rest_route=/wpu/v1' }

# Invoke-RestMethod's -Credential does NOT send Basic auth pre-emptively - it
# waits for a 401 challenge, and the REST API does not issue one. The header has
# to be built by hand or every call comes back unauthenticated.
# PowerShell's default user agent is challenged by some WAFs (Cloudflare on
# zerenclinics.com answers it with an interactive "Just a moment..." page, so
# every bridge call comes back as HTTP 403 HTML). Identify the tool honestly
# instead - a browser string would be a lie, and is challenged there anyway.
$script:RemoteHeaders = @{ Accept = 'application/json' }
if ($R.key) {
    $script:RemoteHeaders['X-WPU-Key'] = $R.key
}
else {
    $pair = '{0}:{1}' -f $R.user, $R.appPassword
    $script:RemoteHeaders['Authorization'] = 'Basic ' + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($pair))
}
$script:RemoteUserAgent = 'WP Ultimate Build/1.0 (authorised site maintenance)'

# Parse a bridge response that may not be the only thing in the body.
#
# Two real causes of junk arriving ahead of our JSON, both hit during testing:
#   - a UTF-8 BOM in any loaded PHP file (Set-Content -Encoding utf8 adds one),
#     which is emitted as body bytes on every request
#   - any plugin echoing a notice or warning before headers
#
# Invoke-RestMethod just fails to parse and hands back a bare string, so every
# field reads as empty and it looks like the bridge returned nothing. Since all
# bridge responses begin {"ok": we can find ours and, importantly, SHOW the junk
# rather than hide it - stray output before headers is a real site defect.
function ConvertFrom-WpuBody {
    param([string] $Text)

    if ($null -eq $Text) { $Text = '' }
    $Text = $Text -replace "^﻿", ''

    try { return $Text | ConvertFrom-Json } catch { }

    $idx = $Text.LastIndexOf('{"ok"')
    if ($idx -ge 0) {
        $stray = $Text.Substring(0, $idx).Trim()
        try {
            $obj = $Text.Substring($idx) | ConvertFrom-Json
        }
        catch {
            Stop-Wpu "Could not parse the response. Body was:`n$Text"
        }
        if ($stray) {
            Write-Host ''
            Write-Host 'WARNING: this site emitted output before its response headers:' -ForegroundColor Yellow
            Write-Host "  $($stray -replace "`r?`n", ' ')" -ForegroundColor Yellow
            Write-Host '  Usually a UTF-8 BOM in a PHP file, or a plugin echoing a notice.' -ForegroundColor Yellow
            Write-Host '  It breaks redirects and cookies site-wide - worth fixing.' -ForegroundColor Yellow
            Write-Host ''
        }
        return $obj
    }

    Stop-Wpu "Response was not JSON. Body was:`n$Text"
}

function Invoke-Wpu {
    param(
        [Parameter(Mandatory = $true)][string] $Route,
        [string] $Method = 'GET',
        $Body = $null,
        [int] $TimeoutSec = 600
    )

    $params = @{
        Uri             = $script:RemoteBase + $(if ($script:RemoteRestRoute) { $Route -replace '\?', '&' } else { $Route })
        Method          = $Method
        Headers         = $script:RemoteHeaders
        TimeoutSec      = $TimeoutSec
        UseBasicParsing = $true
        # Must be the parameter, not a Headers entry: Invoke-WebRequest ignores
        # User-Agent in -Headers and sends its own, which Cloudflare challenges.
        UserAgent       = $script:RemoteUserAgent
    }

    if ($null -ne $Body) {
        $json = $Body | ConvertTo-Json -Depth 8 -Compress
        # Send bytes, not a string: otherwise the body is encoded with the
        # console codepage and any non-ASCII in a script arrives mangled.
        $params.Body        = [Text.Encoding]::UTF8.GetBytes($json)
        $params.ContentType = 'application/json; charset=utf-8'
    }

    # Some WAFs judge the client, not the request: Cloudflare on zerenclinics.com
    # answers .NET's TLS handshake with an interactive challenge page (HTTP 403
    # HTML) while the identical request from curl.exe is served normally. Set
    # "useCurl": true in the config's remote block for those hosts.
    if ($R.useCurl) {
        $curl = (Get-Command curl.exe -ErrorAction SilentlyContinue)
        if (-not $curl) { Stop-Wpu 'remote.useCurl is set but curl.exe was not found.' }
        # NB: $args is a PowerShell automatic variable - using it here silently
        # broke the call. Any other name is fine.
        $curlArgs = @('-s', '-S', '--max-time', "$TimeoutSec", '-A', $script:RemoteUserAgent, '-X', $Method, '-w', "`n%{http_code}")
        foreach ($h in $script:RemoteHeaders.Keys) { $curlArgs += @('-H', "${h}: $($script:RemoteHeaders[$h])") }
        $tmp = $null
        if ($null -ne $Body) {
            $tmp = [IO.Path]::GetTempFileName()
            [IO.File]::WriteAllBytes($tmp, $params.Body)
            $curlArgs += @('-H', 'Content-Type: application/json; charset=utf-8', '--data-binary', "@$tmp")
        }
        $curlArgs += $params.Uri
        $out = (& $curl.Source @curlArgs 2>&1 | Out-String).TrimEnd()
        if ($tmp) { Remove-Item $tmp -ErrorAction SilentlyContinue }
        $lines = $out -split "`r?`n"
        $code = [int]($lines[-1] -replace '[^\d]', '')
        $bodyText = ($lines[0..($lines.Count - 2)] -join "`n")
        if ($code -ge 400) {
            if ($bodyText -match 'Just a moment|challenge-platform') {
                Stop-Wpu "HTTP $code - the site's firewall (Cloudflare) answered with a bot challenge instead of the bridge. Ask the site owner to allow /wp-json/wpu/* or this IP."
            }
            Stop-Wpu "HTTP $code - $($bodyText.Substring(0, [Math]::Min(400, $bodyText.Length)))"
        }
        return ConvertFrom-WpuBody $bodyText
    }

    try {
        $raw = Invoke-WebRequest @params
        return ConvertFrom-WpuBody $raw.Content
    }
    catch {
        # Do NOT add a catch for [RuntimeException] above this one. PowerShell
        # wraps a cmdlet's terminating error in ActionPreferenceStopException,
        # which derives from RuntimeException, so such a clause swallows every
        # HTTP error and rethrows it as a raw stack dump.
        $resp = $null
        if ($_.Exception.PSObject.Properties.Name -contains 'Response') { $resp = $_.Exception.Response }

        if (-not $resp) {
            Stop-Wpu "Could not reach $($script:RemoteBase). $($_.Exception.Message)"
        }

        $code = 0
        try { $code = [int]$resp.StatusCode } catch { }

        # $_.ErrorDetails.Message first: on Windows PowerShell 5.1 the response
        # stream has usually already been consumed by the time we get here, so
        # reading it returns nothing and the real reason for the failure is lost
        # - "HTTP 500 - " with an empty message. ErrorDetails still holds the
        # body. Falling back to the stream keeps this working where it doesn't.
        $text = ''
        try { if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $text = $_.ErrorDetails.Message } } catch { }

        if (-not $text) {
            try {
                $reader = New-Object IO.StreamReader($resp.GetResponseStream())
                $text = $reader.ReadToEnd()
                $reader.Close()
            } catch { }
        }

        $msg = $text
        try {
            $parsed = $text -replace "^﻿", '' | ConvertFrom-Json
            if ($parsed.message) { $msg = $parsed.message }
        } catch { }

        switch ($code) {
            401 {
                if ($R.key) { Stop-Wpu "HTTP 401 - $msg`n`nCheck your key against Tools > WPU Bridge on the site (it may have been revoked), then save a new one with scripts/wpu-secret.ps1." }
                Stop-Wpu "HTTP 401 - $msg`n`nCheck the application password, then run scripts/rdoctor.ps1. Some hosts strip the Authorization header."
            }
            403 { Stop-Wpu "HTTP 403 - $msg" }
            404 {
                Stop-Wpu "HTTP 404 - route not found. Is the WPU Bridge plugin installed and active on $($R.url)? Its routes also disappear once it expires (30 days)."
            }
            default { Stop-Wpu "HTTP $code - $msg" }
        }
    }
}

function Write-WpuResult {
    param($Result)

    if ($Result.output) { Write-Host $Result.output }

    if ($Result.fatal) {
        Write-Host ''
        Write-Host "FATAL: $($Result.fatal)" -ForegroundColor Red
    }

    Write-Host ''
    Write-Host ("-- elapsed {0}ms, peak {1}MB" -f $Result.elapsed_ms, $Result.peak_mb) -ForegroundColor DarkGray

    if (-not $Result.ok) { exit 1 }
}

# The wrappers and ~150 fix scripts inherited from WP Site Build and WP Site
# Doctor call these older names. Keep them working.
Set-Alias -Name Invoke-Wpsb -Value Invoke-Wpu -Scope Script
Set-Alias -Name Invoke-Wpsd -Value Invoke-Wpu -Scope Script
Set-Alias -Name Write-WpsbResult -Value Write-WpuResult -Scope Script
Set-Alias -Name Write-WpsdResult -Value Write-WpuResult -Scope Script
Set-Alias -Name Stop-Wpsb -Value Stop-Wpu -Scope Script
Set-Alias -Name Stop-Wpsd -Value Stop-Wpu -Scope Script
