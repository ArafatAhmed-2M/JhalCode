# Jhal Code installer (Windows). Usage: powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = "Stop"
$Repo = "ArafatAhmed-2M/JhalCode"
try { python --version | Out-Null } catch { Write-Host "install python from python.org first"; exit 1 }
$Headers = @{}
if ($env:GITHUB_TOKEN) { $Headers.Authorization = "Bearer $($env:GITHUB_TOKEN)" }
try { Invoke-WebRequest -Uri "https://api.github.com/repos/$Repo" -Headers $Headers -UseBasicParsing | Out-Null }
catch {
  $t = Read-Host "private repo - paste a GitHub PAT (read-only is enough)"
  $env:GITHUB_TOKEN = $t
  $Headers.Authorization = "Bearer $t"
}
$zip = "$env:TEMP\jhalcode.zip"
Invoke-WebRequest -Uri "https://api.github.com/repos/$Repo/zipball/beta" -Headers $Headers -OutFile $zip
python -m pip install "$zip"
Remove-Item $zip -Force
$scripts = Join-Path (Split-Path (Get-Command python).Source) "Scripts"
$upath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($upath -notlike "*$scripts*") {
  [Environment]::SetEnvironmentVariable("Path", "$upath;$scripts", "User")
  Write-Host "added Scripts to PATH (restart terminal)"
}
Write-Host "done - run: jcc"
