# Raw PHP against Local's binary — mainly for linting.
#
#   powershell -File scripts/php.ps1 -l wp-content/themes/x/header.php     lint one file
#   powershell -File scripts/php.ps1 --lint-theme                          lint the active theme
#   powershell -File scripts/php.ps1 --lint-all                            lint every theme + plugin
#
# Run the single-file form after EVERY template edit. One stray character in a
# header or footer white-screens the whole site, and you will not notice if you
# only reload the page you were working on.
. "$PSScriptRoot\_common.ps1"

function Invoke-Lint([string[]]$files) {
    $bad = 0
    $n = 0

    foreach ($f in $files) {
        $n++
        $out = & $script:Php @($script:PhpArgs) -l $f 2>&1
        if ($LASTEXITCODE -ne 0) {
            $bad++
            Write-Host "FAIL  $f" -ForegroundColor Red
            $out | ForEach-Object { Write-Host "      $_" }
        }
    }

    Write-Host ""
    if ($bad) {
        Write-Host "$bad of $n file(s) FAILED to parse" -ForegroundColor Red
        exit 1
    }
    Write-Host "all $n file(s) parse cleanly" -ForegroundColor Green
}

if ($args.Count -ge 1 -and $args[0] -eq '--lint-theme') {
    $theme = & "$PSScriptRoot\wp.ps1" theme list --status=active --field=name 2>$null |
        Where-Object { $_ -and $_ -notmatch '^\s*$' } | Select-Object -Last 1

    if (-not $theme) { throw "could not determine the active theme" }

    $dir = Join-Path $script:Cfg.sitePath "wp-content\themes\$theme"
    Write-Host "linting theme '$theme'`n"
    Invoke-Lint (Get-ChildItem $dir -Recurse -Filter *.php | Select-Object -Expand FullName)
    return
}

if ($args.Count -ge 1 -and $args[0] -eq '--lint-all') {
    $dirs = @(
        (Join-Path $script:Cfg.sitePath 'wp-content\themes'),
        (Join-Path $script:Cfg.sitePath 'wp-content\plugins')
    )
    $files = $dirs | Where-Object { Test-Path $_ } | ForEach-Object {
        Get-ChildItem $_ -Recurse -Filter *.php -ErrorAction SilentlyContinue | Select-Object -Expand FullName
    }
    Write-Host "linting $($files.Count) file(s)`n"
    Invoke-Lint $files
    return
}

& $script:Php @($script:PhpArgs) @args
