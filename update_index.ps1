Write-Host "Rebuilding RAG index..."
python build_index.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "Index build failed. Aborting."
    exit 1
}

if (!(Test-Path "faiss.index") -or !(Test-Path "docs.pkl")) {
    Write-Error "faiss.index or docs.pkl not found. Aborting."
    exit 1
}

Write-Host ""
Write-Host "Git status:"
git status --short

Write-Host ""
$confirm = Read-Host "Commit updated index files? (y/n)"
if ($confirm -ne "y") {
    Write-Host "Commit cancelled."
    exit 0
}

git add faiss.index docs.pkl
git commit -m "Update RAG index (faiss.index, docs.pkl)"

Write-Host ""
$pushConfirm = Read-Host "Push to remote (triggers Render deploy)? (y/n)"
if ($pushConfirm -eq "y") {
    git push
    Write-Host "Pushed. Render will redeploy automatically."
} else {
    Write-Host "Commit created locally. Remember to push when ready."
}
