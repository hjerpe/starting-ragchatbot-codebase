#!/bin/bash
# Format code using black
echo "🎨 Running black formatter..."
uv run black .
echo "✅ Code formatting complete!"
