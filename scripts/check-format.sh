#!/bin/bash
# Check code formatting without making changes
echo "🔍 Checking code formatting..."
uv run black --check --diff .
if [ $? -eq 0 ]; then
    echo "✅ All code is properly formatted!"
else
    echo "❌ Code formatting issues found. Run './scripts/format.sh' to fix them."
    exit 1
fi
