#!/usr/bin/env bash
# ==============================================================================
# Governed AI Database Copilot - Unified Local Start Script (Bash)
# Launches Docker infrastructure, MCP Database Server, Agent Service, and Next.js UI
# ==============================================================================

set -e

echo -e "\033[1;36m========================================================\033[0m"
echo -e "\033[1;36m  Starting Governed AI Database Copilot Ecosystem       \033[0m"
echo -e "\033[1;36m========================================================\033[0m"

# 1. Start Docker Containers
echo -e "\n\033[1;33m[1/4] Starting Docker Compose infrastructure...\033[0m"
docker compose up -d

# 2. Start MCP DB Server
echo -e "\n\033[1;33m[2/4] Starting MCP Database Server (Port 8001)...\033[0m"
(cd apps/mcp-db-server && python server.py) &

# 3. Start Agent Service
echo -e "\n\033[1;33m[3/4] Starting Agent Service (Port 8000)...\033[0m"
(cd apps/agent-service && python main.py) &

# 4. Start Next.js Frontend
echo -e "\n\033[1;33m[4/4] Starting Next.js Web UI (Port 3000)...\033[0m"
(cd apps/web && npm run dev) &

echo -e "\n\033[1;32m========================================================\033[0m"
echo -e "\033[1;32m  All Services Launched!                                \033[0m"
echo -e "  - Web UI:        http://localhost:3000"
echo -e "  - Agent Service: http://localhost:8000"
echo -e "  - MCP Server:    http://localhost:8001"
echo -e "  - Qdrant:        http://localhost:6333"
echo -e "\033[1;32m========================================================\033[0m"

wait
