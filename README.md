
# Task Management API — Python Automation Testing

A personal project developed to practice Python-based API automation testing.

The project includes a Task Management REST API built with FastAPI
and an automated test suite implemented using PyTest.

## Tech Stack

- Python
- FastAPI
- SQLModel
- SQLite
- PyTest
- FastAPI TestClient
- Faker
- GitHub Actions

## Project Overview

The API provides basic task management functionality:

- Create a task
- Retrieve all tasks
- Retrieve a task by ID
- Update task details and status
- Delete a task

Each task includes a title, description, status, and creation timestamp.

## Automated Testing

The PyTest suite covers:

- API health check
- CRUD operations
- Positive and negative scenarios
- Request data validation
- Missing and invalid fields
- Boundary Value Analysis
- Parametrized tests
- Task status updates
- API response validation
- Data persistence and test isolation

## Test Execution

### 1. Clone the repository

git clone https://github.com/khristoev13/task-management-api

cd task-management-api

### 2. Create a virtual environment

python -m venv .venv

### 3. Activate the environment

macOS / Linux:

source .venv/bin/activate

Windows:

.venv\Scripts\activate

### 4. Install dependencies

pip install -r requirements.txt

### 5. Run automated tests

pytest -v

### 6. Run tests with coverage

pytest --cov --cov-report=term-missing

## CI/CD

GitHub Actions is configured to automatically run the
automated test suite on:

- Push to the main branch
- Pull requests targeting the main branch

The pipeline installs dependencies, executes PyTest,
and generates test reports.

## Project Structure

```
task-management-api/
├── app
│   ├── __init__.py
│   ├── database.py     # Database connection and session setup
│   ├── main.py         # FastAPI application entry point
│   ├── models.py       # SQLModel / SQLAlchemy database models
│   └── tasks.db
├── pytest.ini          # Project and PyTest configuration
├── README.md
├── reports
│   └── junit.xml
├── requirements.txt
├── tasks.db
└── tests
    ├── __init__.py
    ├── conftest.py     # PyTest fixtures and test DB setup
    └── test_tasks.py   # API endpoint tests
```

## Author

Oleksandr Khristoiev

QA Automation Engineer

GitHub: https://github.com/khristoev13
