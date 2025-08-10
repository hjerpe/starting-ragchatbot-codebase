# Contributing Guide

## Development Setup

1. **Clone and install dependencies**
   ```bash
   git clone <repository-url>
   cd starting-ragchatbot-codebase
   uv sync
   ```

2. **Environment setup**
   ```bash
   cp .env.example .env
   # Edit .env with your Anthropic API key
   ```

3. **Run tests before making changes**
   ```bash
   uv run pytest tests/ -v
   ```

## Code Quality Standards

### Backend (Python)
- Follow PEP 8 style guidelines
- Use type hints for function parameters and returns
- Write docstrings for public methods
- Use `uv` for all package management

### Frontend (JavaScript)
- Use modern ES6+ syntax
- Follow consistent naming conventions
- Add JSDoc comments for complex functions
- Implement proper error handling with user-friendly messages

### Testing Philosophy
- **Focus on core functionality** - Test what users actually do
- **Avoid brittle mocks** - Use real components when possible
- **Test end-to-end workflows** - Ensure the system works as a whole
- **Keep tests simple** - Easy to understand and maintain
- **High-value, low-maintenance** - Tests should catch real issues

## Project Structure

```
starting-ragchatbot-codebase/
├── backend/                    # FastAPI backend application
│   ├── app.py                 # Main FastAPI application
│   ├── rag_system.py          # RAG orchestrator
│   ├── ai_generator.py        # Anthropic API integration
│   ├── vector_store.py        # ChromaDB operations
│   ├── search_tools.py        # Search tools and tool manager
│   ├── document_processor.py  # Document parsing and chunking
│   ├── session_manager.py     # Conversation history
│   ├── models.py              # Pydantic data models
│   ├── config.py              # Configuration settings
│   ├── tests/                 # Test suite
│   │   ├── conftest.py        # Pytest fixtures
│   │   ├── test_*.py          # Test files
│   │   └── test_utils.py      # Test utilities
│   └── chroma_db/             # Vector database (auto-created)
├── frontend/                   # Frontend web application
│   ├── index.html             # Main HTML file
│   ├── script.js              # JavaScript functionality
│   └── style.css              # CSS styles
├── docs/                       # Course documents (auto-loaded)
│   └── *.txt                  # Course content files
├── .devcontainer/             # Development container config
├── .env                       # Environment variables (not in git)
├── .env.example               # Environment template
├── pyproject.toml             # Python project configuration
├── uv.lock                    # Dependency lock file
├── run.sh                     # Quick start script
├── README.md                  # Main documentation
├── CONTRIBUTING.md            # This file
└── CLAUDE.md                  # Claude Code assistant instructions
```

## Making Changes

### 1. Feature Development
1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Write tests for your feature first (TDD approach)
3. Implement the feature
4. Run tests: `uv run pytest tests/ -v`
5. Update documentation if needed

### 2. Bug Fixes
1. Write a test that reproduces the bug
2. Fix the bug
3. Ensure all tests pass
4. Document the fix in commit message

### 3. Frontend Changes
1. Test error scenarios as well as happy path
2. Ensure error messages are user-friendly
3. Test with network issues and API failures
4. Update error handling documentation

## Testing Guidelines

### Running Tests
```bash
# All tests
uv run pytest tests/ -v

# Specific component
uv run pytest tests/test_search_tools.py -v

# With debugging output
uv run pytest tests/test_real_system.py -v -s

# Coverage report
uv run pytest tests/ --cov=. --cov-report=html
```

### Writing Tests
- Use descriptive test names: `test_execute_successful_search`
- Include both success and failure scenarios
- Mock external dependencies (Anthropic API, etc.)
- Use pytest fixtures for common setup
- Test error handling thoroughly

### Test Categories
- **Unit Tests**: Individual component functionality
- **Integration Tests**: Component interactions
- **End-to-End Tests**: Full system workflows
- **Error Handling Tests**: Failure scenarios and recovery

## Debugging

### Backend Issues
1. Check logs in console output
2. Verify API key configuration
3. Test with `uv run pytest tests/test_real_system.py -v -s`
4. Use FastAPI docs at `http://localhost:8000/docs`

### Frontend Issues
1. Open browser developer console
2. Check network tab for API calls
3. Verify error messages are descriptive
4. Test retry functionality

## Code Review Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Error handling is user-friendly
- [ ] Documentation is updated
- [ ] No sensitive data in commits
- [ ] API key is in `.env`, not code
- [ ] Uses `uv` for dependency management

## Common Commands

```bash
# Development server
uv run uvicorn app:app --reload --port 8000

# Add dependency
uv add package-name

# Add dev dependency
uv add --dev package-name

# Update dependencies
uv sync

# Run specific test
uv run pytest tests/test_name.py::TestClass::test_method -v
```

## Getting Help

1. Check the README.md for setup instructions
2. Run diagnostic tests: `uv run pytest tests/test_real_system.py -v -s`
3. Check existing issues in the repository
4. Ask questions in discussions or create an issue

## Performance Considerations

- Use vector search efficiently (limit results)
- Implement proper error retry logic
- Cache frequently accessed data
- Monitor API usage and costs
- Optimize document chunking strategy
