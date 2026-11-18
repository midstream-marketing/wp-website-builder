# Save, check or remove a secret for WP Ultimate Build.
#
#   powershell -File scripts/wpu-secret.ps1 set  <site> key            bridge connection key
#   powershell -File scripts/wpu-secret.ps1 set  <site> apppassword    Application Password (if not using a key)
#   powershell -File scripts/wpu-secret.ps1 set  <site> adminpass      wp-admin password (only for install-bridge / admin audits)
#   powershell -File scripts/wpu-secret.ps1 set  <site> sftp_pass      hosting SFTP/SSH password (or sftp_keypass for a key's passphrase)
#   powershell -File scripts/wpu-secret.ps1 set  <site> cpanel_token   cPanel API token (cPanel > Security > Manage API Tokens)
#   powershell -File scripts/wpu-secret.ps1 set  global dataforseo_login
#   powershell -File scripts/wpu-secret.ps1 set  global dataforseo_password
#   powershell -File scripts/wpu-secret.ps1 set  global pagespeed_key
#   powershell -File scripts/wpu-secret.ps1 has  <site> key            prints yes/no, never the value
#   powershell -File scripts/wpu-secret.ps1 get  <site> key            prints the value (scripts use this; avoid running it in a chat)
#   powershell -File scripts/wpu-secret.ps1 rm   <site> [name]
#   (set-stdin <site> <name> reads the value from stdin - used by WPU Desk)
#
# "set" prompts with hidden input. Run it in your own terminal, not through Claude,
# so the value never appears in a conversation.
. "$PSScriptRoot\_secrets.ps1"
$ErrorActionPreference = 'Stop'

if ($args.Count -lt 2) {
    Get-Content $PSCommandPath | Select-Object -Skip 1 -First 16 | ForEach-Object { $_ -replace '^# ?', '' }
    exit 2
}
$mode = $args[0].ToLower(); $scope = $args[1].ToLower(); $name = if ($args.Count -ge 3) { $args[2].ToLower() } else { '' }

switch ($mode) {
    'set' {
        if (-not $name) { throw 'set needs a name' }
        $v = Read-Host -AsSecureString "Value for $scope/$name (hidden)"
        if ($v.Length -eq 0) { throw 'empty value - nothing saved' }
        Set-WpuSecret -Scope $scope -Name $name -Value $v
        Write-Host "saved $scope/$name (encrypted for $env:USERNAME on $env:COMPUTERNAME)" -ForegroundColor Green
    }
    'set-stdin' {
        # Used by WPU Desk: the value arrives on stdin from the local dashboard, never on the command line.
        if (-not $name) { throw 'set-stdin needs a name' }
        $plain = [Console]::In.ReadLine()
        if ([string]::IsNullOrEmpty($plain)) { throw 'empty value - nothing saved' }
        $v = ConvertTo-SecureString -String $plain -AsPlainText -Force
        $plain = $null
        Set-WpuSecret -Scope $scope -Name $name -Value $v
        Write-Host "saved $scope/$name"
    }
    'has' { if (Get-WpuSecret -Scope $scope -Name $name) { 'yes' } else { 'no'; exit 1 } }
    'get' { $v = Get-WpuSecret -Scope $scope -Name $name; if (-not $v) { exit 1 }; [Console]::Out.Write($v) }
    'rm'  { Remove-WpuSecret -Scope $scope -Name $name; Write-Host "removed $scope/$name" }
    default { throw "unknown mode '$mode' - set, has, get or rm" }
}
