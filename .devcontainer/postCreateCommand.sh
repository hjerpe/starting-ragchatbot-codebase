#!/bin/bash

SCRIPT_DIR_PARENT=$( cd -- "$( dirname -- "$(dirname -- "${BASH_SOURCE[0]}")" )" &> /dev/null && pwd )
sudo apt-get --yes update && sudo apt-get --yes upgrade

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Playwright MCP server
npm install @playwright/mcp

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Claude Code CLI
curl -fsSL https://claude.ai/install.sh | bash
