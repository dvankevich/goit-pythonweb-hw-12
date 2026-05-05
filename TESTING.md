# Testing Guide

This comprehensive guide covers all aspects of testing the Contacts Management API.

## 🧪 Prerequisites

### Required Software
- **Python 3.13+**
- **Poetry** (for dependency management)
- **PostgreSQL 15+** (for integration tests)
- **Redis 6+** (for caching tests)
- **Git** (for version control)

### Development Environment
```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Set up test database
createdb contacts_test

# Set environment variables for testing
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/contacts_test"
export ENABLE_REDIS=false
export JWT_SECRET="test_secret_key_minimum_32_characters_long"
export LOG_LEVEL="DEBUG"
```

## 🧪 Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_api/               # API endpoint tests
│   ├── test_auth.py      # Authentication tests
│   ├── test_contacts.py  # Contact CRUD tests
│   └── test_users.py     # User management tests
├── test_services/           # Business logic tests
│   ├── test_auth.py      # Authentication service tests
│   ├── test_users.py     # User service tests
│   └── test_email.py    # Email service tests
├── test_repositories/       # Data layer tests
│   ├── test_contact_repository.py  # Contact repository tests
│   └── test_user_repository.py     # User repository tests
└── test_models/            # Model tests
    ├── test_user.py       # User model tests
    └── test_contact.py   # Contact model tests
```

## 🧪 Running Tests

### All Tests
```bash
# Run all tests with coverage
pytest --cov=src --cov-report=term-missing

# Run all tests with HTML coverage report
pytest --cov=src --cov-report=html

# Run all tests with coverage and generate XML report
pytest --cov=src --cov-report=xml --junitxml=test-results.xml
```

### Specific Test Modules
```bash
# Authentication API tests
pytest --cov=src.api.auth --cov-report=term-missing tests/test_api/test_auth.py

# Contact API tests
pytest --cov=src.api.contact_api --cov-report=term-missing tests/test_api/test_contacts.py

# User API tests
pytest --cov=src.api.users --cov-report=term-missing tests/test_api/test_users.py

# Service layer tests
pytest --cov=src.services --cov-report=term-missing tests/test_services/

# Repository layer tests
pytest --cov=src.repositories --cov-report=term-missing tests/test_repositories/

# Model tests
pytest --cov=src.models --cov-report=term-missing tests/test_models/
```

### Test Categories
```bash
# Unit tests only
pytest tests/ -m "unit"

# Integration tests only
pytest tests/ -m "integration"

# API tests only
pytest tests/ -m "api"

# Slow tests (marked with @pytest.mark.slow)
pytest tests/ -m "slow"

# Skip slow tests
pytest tests/ -m "not slow"
```

## 🧪 Test Configuration

### Pytest Configuration (conftest.py)
Key fixtures and configuration:

```python
# Test database setup
@pytest.fixture(scope="session")
async def test_db():
    # Creates test database session
    # Returns AsyncSession for testing
    pass

# Test client setup
@pytest.fixture(scope="session")
async def client():
    # Creates FastAPI test client
    # Returns AsyncClient for API testing
    pass

# Authentication setup
@pytest.fixture
async def test_user_token():
    # Creates test user and returns JWT token
    # Returns valid token for protected endpoints
    pass

# Mock services
@pytest.fixture
def mock_email_service():
    # Mocks email service for testing
    # Returns MagicMock instance
    pass
```

### Environment Variables for Testing
```bash
# Test database
export TEST_DATABASE_URL="postgresql+asyncpg://test_user:test_pass@localhost:5432/contacts_test"

# JWT settings
export TEST_JWT_SECRET="test_secret_key_for_testing_only_32_chars_minimum"
export TEST_JWT_ALGORITHM="HS256"
export TEST_JWT_EXPIRATION_SECONDS=1

# Email settings (mock)
export TEST_MAIL_USERNAME="test@example.com"
export TEST_MAIL_PASSWORD="test_password"
export TEST_MAIL_FROM="test@example.com"

# Cloudinary settings (mock)
export TEST_CLD_NAME="test_cloud"
export TEST_CLD_API_KEY="test_key"
export TEST_CLD_API_SECRET="test_secret"

# Redis settings
export TEST_ENABLE_REDIS=false
export TEST_REDIS_HOST="localhost"
export TEST_REDIS_PORT=6380

# CORS settings
export TEST_CORS_ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

# Logging
export TEST_LOG_LEVEL="DEBUG"
```

## 🧪 Test Writing Guidelines

### Test Structure
```python
import pytest
from httpx import AsyncClient
from src.main import app

class TestUserAuthentication:
    """Test user authentication endpoints."""
    
    async def test_register_user_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123!"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "password" not in data
    
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email."""
        # Create user first
        await client.post("/api/auth/register", json={
            "username": "user1",
            "email": "test@example.com",
            "password": "TestPassword123!"
        })
        
        # Try to register with same email
        response = await client.post("/api/auth/register", json={
            "username": "user2",
            "email": "test@example.com",
            "password": "TestPassword123!"
        })
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()
```

### Best Practices
1. **Descriptive test names**: Use `test_` prefix and describe what's being tested
2. **Arrange-Act-Assert**: Structure tests clearly
3. **Test one thing**: Each test should verify one specific behavior
4. **Use fixtures**: Reuse setup code through pytest fixtures
5. **Mock external services**: Use unittest.mock for external dependencies
6. **Clean up**: Ensure tests don't interfere with each other
7. **Test edge cases**: Include boundary conditions and error scenarios
8. **Use type hints**: Add proper type annotations to test functions

## 🧪 Coverage Requirements

### Minimum Coverage Standards
- **Overall coverage**: 90% minimum, 95% target
- **Critical paths**: 100% coverage for authentication and user management
- **New code**: 100% coverage for all new features

### Coverage Reports
```bash
# Terminal coverage report
pytest --cov=src --cov-report=term-missing

# HTML coverage report (detailed)
pytest --cov=src --cov-report=html

# Coverage for specific module
pytest --cov=src.api.auth --cov-report=term-missing --cov-fail-under=80

# Coverage with branch analysis
pytest --cov=src --cov-branch --cov-report=html
```

### Coverage Exclusions
```python
# In pytest.ini or pyproject.toml
[tool:pytest]
addopts = --cov=src --cov-report=term-missing
markers = 
    unit: Unit tests
    integration: Integration tests
    api: API tests
    slow: Slow running tests

# Coverage exclusions
[tool:coverage:run]
omit = 
    */tests/*
    */venv/*
    */__pycache__/*
    */conftest.py
    */migrations/*
```

## 🧪 Continuous Integration

### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.13]
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test_db
        ENABLE_REDIS: true
        REDIS_HOST: localhost
        REDIS_PORT: 6379
      run: |
        pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## 🧪 Performance Testing

### Load Testing
```bash
# Install locust
pip install locust

# Run load tests
locust -f tests/performance/locustfile.py --host=http://localhost:8000 --users=10 --spawn-rate=2 --run-time=60s --html=reports/performance.html
```

### API Performance Tests
```python
# tests/performance/test_api_performance.py
import pytest
from httpx import AsyncClient
import time

class TestAPIPerformance:
    async def test_contact_creation_performance(self, client: AsyncClient):
        """Test contact creation endpoint performance."""
        start_time = time.time()
        
        # Create 100 contacts
        for i in range(100):
            await client.post("/api/contacts/", json={
                "first_name": f"Test{i}",
                "last_name": f"User{i}",
                "email": f"test{i}@example.com",
                "phone": "1234567890"
            })
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within 10 seconds
        assert duration < 10.0, f"Performance test failed: {duration:.2f}s"
```

## 🧪 Debugging Tests

### Running Individual Tests
```bash
# Run specific test with verbose output
pytest tests/test_api/test_auth.py::TestUserAuthentication::test_register_user_success -v

# Run with debugging
pytest --pdb tests/test_api/test_auth.py

# Run with specific markers
pytest -m "not slow" -v

# Stop on first failure
pytest -x --tb=short
```

### Test Database Issues
```bash
# Reset test database
pytest tests/test_api/test_auth.py --create-db

# Check test database state
pytest tests/test_api/test_auth.py --db-shell

# Clean test database
dropdb contacts_test
```

## 🧪 Test Data Management

### Test Fixtures
```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import User, Contact
from src.db.base import Base

@pytest.fixture(scope="session")
async def test_db_session():
    """Create test database session."""
    # Setup test database
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session for tests
    async_session = sessionmaker(engine, class_=AsyncSession)
    yield async_session()
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def test_user(test_db_session):
    """Create test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        confirmed=True
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user
```

### Test Data Factory
```python
# tests/factories.py
import factory
from src.models import User, Contact

class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    username = factory.Faker("user_name")
    email = factory.Faker("email")
    is_active = True

class ContactFactory(factory.Factory):
    class Meta:
        model = Contact
    
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    phone = factory.Faker("phone_number")
```

## 🧪 Test Reports

### Generating Reports
```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# Generate JSON report
pytest --cov=src --cov-report=json --cov-report=term-missing

# Generate JUnit XML for CI
pytest --junitxml=test-results.xml --cov=src --cov-report=term-missing

# Benchmark tests
pytest --benchmark-only --benchmark-json=benchmark.json
```

### Analyzing Results
```bash
# Coverage summary
coverage report --show-missing

# Find failing tests
pytest --lf --tb=short

# Run slowest tests
pytest --durations=10
```

This testing guide ensures comprehensive test coverage, maintainable test code, and reliable quality assurance for the Contacts Management API.
