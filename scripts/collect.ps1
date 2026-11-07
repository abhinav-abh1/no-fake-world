$ErrorActionPreference = "Continue"
$log = Join-Path $PSScriptRoot "..\collect.log"
$compose = Join-Path $PSScriptRoot "..\infra\docker-compose.yml"
Set-Location (Join-Path $PSScriptRoot "..\backend")
$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
# The model is already downloaded, so skip network checks and their warnings.
$env:HF_HUB_OFFLINE = "1"

function Step($label, [scriptblock]$command) {
    & $command *>> $log
    if ($LASTEXITCODE -ne 0) {
        "FAILED: $label (exit code $LASTEXITCODE)" *>> $log
        return $false
    }
    return $true
}

"=== $(Get-Date -Format o) ===" *>> $log
if (-not (Step "database" { docker compose -f $compose up -d --wait db })) {
    "SKIPPED: database not available (is Docker Desktop running?). Nothing else was run." *>> $log
    exit 1
}
$null = Step "collect" { uv run python -m app.collectors.run }
$null = Step "extract" { uv run python -m app.collectors.extract_run --limit 20 }
$null = Step "embed" { uv run --group ml python -m app.embeddings.embed_articles --limit 400 }
$null = Step "dedup" { uv run python -m app.dedup.mark_run }