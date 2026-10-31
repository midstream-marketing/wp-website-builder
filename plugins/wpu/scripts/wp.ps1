# wp-cli against the configured LocalWP site.
#
#   powershell -File scripts/wp.ps1 plugin list
#   powershell -File scripts/wp.ps1 option get blogname
#
# USE THIS ONLY FOR SHORT COMMANDS.
#
# `wp eval-file` silently does nothing on files above roughly 16KB — it exits 0
# having executed none of the file, with no error even under --debug. For any
# script that matters, use scripts/wpphp.ps1 instead.
#
# If a call has not returned in ~60s it has hung; kill the php process and
# switch to wpphp.ps1:
#     Get-Process php | Select Id, StartTime, CPU
#     Stop-Process -Id <id> -Force
. "$PSScriptRoot\_common.ps1"

if (-not $script:Cfg.wpCli -or -not (Test-Path $script:Cfg.wpCli)) {
    throw "wpCli is not set or does not exist. Run: powershell -File scripts/detect.ps1"
}

& $script:Php @($script:PhpArgs) $script:Cfg.wpCli --path="$($script:Cfg.sitePath)" @args
