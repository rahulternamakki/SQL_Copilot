# ==============================================================================
# Governed AI Database Copilot - Unified Local Start Script (PowerShell)
# Launches Docker infrastructure, MCP Database Server, Agent Service, and Next.js UI
# ==============================================================================

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting Governed AI Database Copilot Ecosystem" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Start Docker Infrastructure (Postgres & Qdrant)
Write-Host "`n[1/4] Starting Docker Compose infrastructure (Postgres + Qdrant)..." -ForegroundColor Yellow
docker compose up -d

# 2. Start MCP DB Server (Port 8001)
Write-Host "`n[2/4] Starting Isolated MCP Database Server (Port 8001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..\apps\mcp-db-server'; python server.py"

# 3. Start Multi-Agent Service (Port 8000)
Write-Host "`n[3/4] Starting LangGraph Multi-Agent Service (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..\apps\agent-service'; python main.py"

# 4. Start Next.js Frontend (Port 3000)
Write-Host "`n[4/4] Starting Next.js Web UI (Port 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..\apps\web'; npm run dev"

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host "  All Services Started Successfully!" -ForegroundColor Green
Write-Host "  - Next.js Web UI:       http://localhost:3000" -ForegroundColor White
Write-Host "  - Agent Service API:    http://localhost:8000" -ForegroundColor White
Write-Host "  - MCP DB Server:        http://localhost:8001" -ForegroundColor White
Write-Host "  - Qdrant Vector DB:     http://localhost:6333" -ForegroundColor White
Write-Host "  - Postgres Demo DB:     localhost:5432 (ecommerce_demo)" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Green
