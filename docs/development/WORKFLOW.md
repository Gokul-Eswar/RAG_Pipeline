# Development Workflow

## Guiding Principles

1. **Test-Driven Development**: Write tests before implementation
2. **Code Quality**: Maintain >80% test coverage
3. **Clean Architecture**: Separation of concerns (API → Infrastructure)
4. **Type Safety**: Use type hints throughout
5. **Documentation**: Clear docstrings and examples

## Project Structure

```
src/
├── api/              # FastAPI application
│   ├── handlers/     # Route handlers
│   ├── middleware/   # Middleware and error handling
│   └── main.py       # Application factory
├── infrastructure/   # External services
│   ├── database/     # Neo4j, Qdrant
│   └── messaging/    # Kafka
├── processing/       # Data pipelines
│   ├── ingestion/    # Event ingestion
│   ├── extraction/   # NLP extraction
│   └── transformation/ # Spark jobs
├── storage/         # Storage abstraction
│   ├── vector/      # Vector storage
│   └── graph/       # Graph storage
├── ai/              # LLM integration
├── orchestration/   # Airflow/Dagster
├── models/          # Data models
├── utils/           # Configuration and logging
└── core/            # CLI interface

tests/
├── unit/            # Unit tests
├── integration/     # Integration tests
├── fixtures/        # Test fixtures
└── conftest.py      # Test configuration
```

## Development Guidelines

### Adding a New Feature

1. **Create Tests First**
   ```bash
   # Write tests/unit/test_my_feature.py
   # Write tests/integration/test_my_feature_flow.py
   pytest tests/ -v
   ```

2. **Implement Feature**
   - Add implementation in appropriate src/ module
   - Follow existing code style and patterns
   - Include docstrings and type hints

3. **Update Documentation**
   - Add API docs if new endpoint
   - Update guides if new capability

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# With coverage
pytest --cov=src --cov-report=html

# Specific test
pytest tests/unit/test_neo4j_repository.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Check types
mypy src/

# Lint
flake8 src/ tests/

# All checks
black src/ tests/ && mypy src/ && flake8 src/ tests/ && pytest
```

## Workflow

1. Create feature branch: `git checkout -b feature/my-feature`
2. Write failing tests
3. Implement feature
4. Run tests: `pytest -v`
5. Check coverage: `pytest --cov=src`
6. Format code: `black src/`
7. Commit with message: `feat: Add my feature`
8. Push and create pull request

## Local Development

```bash
# Setup
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Start services
cd docker
docker-compose up -d

# Run API
python -m uvicorn src.api.main:app --reload

# Run tests
pytest

# View API docs
# http://localhost:8000/docs
```
