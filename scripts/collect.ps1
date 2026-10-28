$ErrorActionPreference = "Continue"
$log = Join-Path $PSScriptRoot "..\collect.log"
Set-Location (Join-Path $PSScriptRoot "..\backend")
$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
# The model is already downloaded, so skip network checks and their warnings.
$env:HF_HUB_OFFLINE = "1"

function Step($label, [scriptblock]$command) {
    & $command *>> $log
    if ($LASTEXITCODE -ne 0) { "FAILED: $label (exit code $LASTEXITCODE)" *>> $log }
}

"=== $(Get-Date -Format o) ===" *>> $log
Step "collect" { uv run python -m app.collectors.run }
Step "extract" { uv run python -m app.collectors.extract_run --limit 20 }
Step "embed" { uv run --group ml python -m app.embeddings.embed_articles --limit 400 }