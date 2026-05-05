# create_project.ps1
$ErrorActionPreference = "Stop"

$folders = @(
    "backend/api/v1/routers",
    "backend/core",
    "backend/db/models",
    "backend/db/migrations",
    "backend/ml/vision",
    "backend/ml/nlp",
    "backend/ml/fusion",
    "backend/ml/rag",
    "backend/orchestration",
    "backend/utils",
    "backend/tests/fixtures",
    "backend/tests/unit",
    "backend/tests/integration",
    "backend/tests/load",
    "backend/logs",
    "backend/temp",
    "frontend",
    "training/notebooks",
    "training/scripts",
    "data/raw",
    "data/processed",
    "data/chromadb",
    "models",
    "docs/architecture",
    ".github/workflows",
    ".github/ISSUE_TEMPLATE"
)

$initFiles = @(
    "backend/api/v1/routers/__init__.py", "backend/api/v1/routers/auth.py", "backend/api/v1/routers/analyze.py", "backend/api/v1/routers/chat.py", "backend/api/v1/routers/report.py", "backend/api/v1/routers/users.py", "backend/api/v1/routers/health.py", "backend/api/v1/__init__.py",
    "backend/core/__init__.py", "backend/core/config.py", "backend/core/security.py", "backend/core/exceptions.py", "backend/core/middleware.py", "backend/core/dependencies.py", "backend/core/logging_config.py",
    "backend/db/__init__.py", "backend/db/base.py", "backend/db/session.py",
    "backend/db/models/__init__.py", "backend/db/models/user.py", "backend/db/models/session.py", "backend/db/models/task.py", "backend/db/models/api_key.py", "backend/db/models/stats.py",
    "backend/db/migrations/env.py",
    "backend/ml/__init__.py", "backend/ml/registry.py",
    "backend/ml/vision/__init__.py", "backend/ml/vision/anomaly.py", "backend/ml/vision/gradcam.py",
    "backend/ml/nlp/__init__.py", "backend/ml/nlp/ner.py", "backend/ml/nlp/classifier.py", "backend/ml/nlp/whisper.py",
    "backend/ml/fusion/__init__.py", "backend/ml/fusion/medclip.py",
    "backend/ml/rag/__init__.py", "backend/ml/rag/vectorstore.py", "backend/ml/rag/retriever.py", "backend/ml/rag/generator.py",
    "backend/orchestration/__init__.py", "backend/orchestration/pipeline.py", "backend/orchestration/queue.py", "backend/orchestration/workers.py", "backend/orchestration/resilience.py", "backend/orchestration/scheduler.py",
    "backend/utils/__init__.py", "backend/utils/pdf.py", "backend/utils/image.py", "backend/utils/audio.py", "backend/utils/cache.py", "backend/utils/validators.py",
    "backend/tests/__init__.py", "backend/tests/conftest.py", "backend/tests/unit/__init__.py", "backend/tests/integration/__init__.py", "backend/tests/load/__init__.py",
    "backend/main.py"
)

$gitkeeps = @(
    "backend/tests/fixtures/.gitkeep", "backend/logs/.gitkeep", "backend/temp/.gitkeep",
    "frontend/.gitkeep", "training/notebooks/.gitkeep", "training/scripts/.gitkeep",
    "data/raw/.gitkeep", "data/processed/.gitkeep", "data/chromadb/.gitkeep",
    "models/.gitkeep", "docs/architecture/.gitkeep", ".github/workflows/.gitkeep"
)

$createdFolders = 0

foreach ($folder in $folders) {
    if (-not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
        Write-Host "Created: $folder" -ForegroundColor Green
        $createdFolders++
    } else {
        Write-Host "Already exists: $folder" -ForegroundColor Yellow
    }
}

foreach ($file in $initFiles) {
    if (-not (Test-Path $file)) {
        New-Item -ItemType File -Path $file -Force | Out-Null
    }
}

foreach ($file in $gitkeeps) {
    if (-not (Test-Path $file)) {
        New-Item -ItemType File -Path $file -Force | Out-Null
    }
}

# Create empty requirement files
if (-not (Test-Path "backend/requirements.txt")) { New-Item -ItemType File -Path "backend/requirements.txt" -Force | Out-Null }
if (-not (Test-Path "backend/pyproject.toml")) { New-Item -ItemType File -Path "backend/pyproject.toml" -Force | Out-Null }

Write-Host ""
Write-Host "Total folders created: $createdFolders" -ForegroundColor Cyan
