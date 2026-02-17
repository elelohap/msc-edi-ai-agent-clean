$ErrorActionPreference = "Stop"

Write-Host "Rebuilding FAISS index..."

# Step 1: Run index builder
python rag/build_index_openai.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Index build failed."
    exit 1
}

# Step 2: Verify artefacts exist in repo root
if (!(Test-Path "docs.pkl")) {
    Write-Host "docs.pkl not found in repo root."
    exit 1
}

if (!(Test-Path "faiss.index")) {
    Write-Host "faiss.index not found in repo root."
    exit 1
}

Write-Host "Index artefacts generated successfully."

# Step 3: Stage artefacts
git add docs.pkl faiss.index

# Step 4: Commit only if there are changes
$changes = git status --porcelain

if ($changes) {
    git commit -m "Rebuild FAISS index after updating knowledge sources"
    Write-Host "Index committed locally."
} else {
    Write-Host "No index changes detected. Nothing to commit."
}

Write-Host "If ready, run: git push"
