$ErrorActionPreference = "Stop"
$log = Join-Path $PSScriptRoot "..\collect.log"
Set-Location (Join-Path $PSScriptRoot "..\backend")
$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"

"=== $(Get-Date -Format o) ===" *>> $log
uv run python -m app.collectors.run *>> $log
uv run python -m app.collectors.extract_run --limit 20 *>> $log