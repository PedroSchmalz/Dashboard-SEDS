$ErrorActionPreference = "Stop"
$projectDir = $PSScriptRoot
$python = Join-Path $projectDir ".venv\Scripts\python.exe"
$app = Join-Path $projectDir "app.py"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Ambiente virtual não encontrado em: $python"
}

& $python -c "import streamlit" | Out-Null
& $python -m streamlit run $app