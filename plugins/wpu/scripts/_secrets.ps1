# Per-user secret store for WP Ultimate Build.
#
# Secrets (bridge connection keys, Application Passwords, wp-admin passwords,
# the DataForSEO login) are kept OUT of project folders. Each one is encrypted
# with Windows DPAPI for the current Windows user and saved under
#   %APPDATA%\WPU\secrets\<scope>.json
# Only the same Windows user on the same machine can decrypt it. Nothing here
# is ever printed, logged or sent to Claude; scripts read a value at the moment
# they need it.
#
# Scopes: a site slug ("pepcore") or "global" (DataForSEO, PageSpeed key).
#
# Off Windows (CI, a Mac), the same names are read from environment variables:
#   WPU_SECRET_<SCOPE>_<NAME>   e.g. WPU_SECRET_PEPCORE_KEY, WPU_SECRET_GLOBAL_DATAFORSEO_PASSWORD

function Get-WpuSecretDir {
    $base = $env:APPDATA
    if (-not $base) { $base = Join-Path $HOME '.config' }
    $dir = Join-Path $base 'WPU/secrets'
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    return $dir
}

function Get-WpuSecretFile([string] $Scope) {
    if ($Scope -notmatch '^[a-z0-9][a-z0-9_-]{0,62}$') { throw "bad secret scope '$Scope' (use the site slug: lowercase letters, digits, - and _)" }
    return Join-Path (Get-WpuSecretDir) "$Scope.json"
}

function Get-WpuSecret {
    param([Parameter(Mandatory = $true)][string] $Scope, [Parameter(Mandatory = $true)][string] $Name)
    $envName = ('WPU_SECRET_{0}_{1}' -f $Scope, $Name).ToUpper() -replace '[^A-Z0-9_]', '_'
    $fromEnv = [Environment]::GetEnvironmentVariable($envName)
    if ($fromEnv) { return $fromEnv }

    $file = Get-WpuSecretFile $Scope
    if (-not (Test-Path $file)) { return $null }
    $store = Get-Content $file -Raw | ConvertFrom-Json
    $enc = $store.$Name
    if (-not $enc) { return $null }
    try {
        $sec = ConvertTo-SecureString $enc -ErrorAction Stop
    } catch {
        throw "secret '$Name' for '$Scope' could not be decrypted - it was saved by another Windows user or machine. Save it again with: wpu-secret set $Scope $Name"
    }
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

function Set-WpuSecret {
    param([Parameter(Mandatory = $true)][string] $Scope, [Parameter(Mandatory = $true)][string] $Name, [Parameter(Mandatory = $true)][Security.SecureString] $Value)
    if ($Name -notmatch '^[a-z0-9_]{1,40}$') { throw "bad secret name '$Name'" }
    # DPAPI exists only on Windows. Elsewhere ConvertFrom-SecureString is reversible encoding, not
    # encryption, so refuse rather than store something that only looks protected.
    if ((Get-Variable IsWindows -ErrorAction SilentlyContinue) -and -not $IsWindows) {
        throw "The encrypted store needs Windows. On macOS/Linux set an environment variable instead: WPU_SECRET_$($Scope.ToUpper())_$($Name.ToUpper()) (e.g. in your shell profile or a password manager's CLI)."
    }
    $file = Get-WpuSecretFile $Scope
    $store = [ordered]@{}
    if (Test-Path $file) {
        $old = Get-Content $file -Raw | ConvertFrom-Json
        foreach ($p in $old.PSObject.Properties) { $store[$p.Name] = $p.Value }
    }
    $store[$Name] = ConvertFrom-SecureString $Value   # DPAPI, current user
    ($store | ConvertTo-Json) | Set-Content -Path $file -Encoding ascii
}

function Remove-WpuSecret {
    param([Parameter(Mandatory = $true)][string] $Scope, [string] $Name = '')
    $file = Get-WpuSecretFile $Scope
    if (-not (Test-Path $file)) { return }
    if (-not $Name) { Remove-Item $file -Force; return }
    $old = Get-Content $file -Raw | ConvertFrom-Json
    $store = [ordered]@{}
    foreach ($p in $old.PSObject.Properties) { if ($p.Name -ne $Name) { $store[$p.Name] = $p.Value } }
    ($store | ConvertTo-Json) | Set-Content -Path $file -Encoding ascii
}
