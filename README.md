# Contacts Management API (FastAPI)

A high-performance, stateless, and secure RESTful API for managing contact lists, built with FastAPI, PostgreSQL, and Docker. This project emphasizes modern DevOps practices, including immutable container architecture and automated infrastructure orchestration.

## Key Features

*   **FastAPI Framework**: High performance, asynchronous API development.
*   **Alembic Migrations**: Automated database schema management.
*   **Dockerized Architecture**: Fully isolated environment using `docker-compose`.
*   **Immutable Containers**: Optimized for 0-byte `SizeRw` to ensure statelessness and security.
*   **Automated Orchestration**: Integrated `entrypoint.sh` for database readiness checks and automatic migrations.
*   **Security**: JWT authentication, CORS configuration, and isolated internal networking.
*   **Media & Notifications**: Avatar management via Cloudinary and email verification via Brevo (SMTP).

---

## 🛠 Prerequisites

*   **Docker** and **Docker Compose**
*   **Python 3.13** (if running locally)
*   **Poetry** (for dependency management)

---

## 🚀 Quick Start (Docker Compose)

The recommended way to run the project is using Docker Compose, which sets up the API, the database, and an isolated bridge network.

### 1. Configure Environment Variables
Copy the example environment file and fill in your credentials:
```bash
cp env.example .env
```
> **Note:** For Docker Compose, `POSTGRES_HOST` is automatically set to `db` within the internal network, overriding any `localhost` setting in your `.env`.

### 2. Launch the Application
```bash
docker-compose up -d --build
```
This command builds the optimized image, starts the PostgreSQL container, waits for the database to be ready, and automatically runs all migrations.

### 3. Verify Status
Check if the containers are running and "healthy":
```bash
docker ps
```
*   **API**: [http://localhost:8000](http://localhost:8000)
*   **Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## ⚙️ Environment Configuration (.env)

The `.env` file controls all aspects of the application. Ensure the following sections are configured:

### Database (PostgreSQL)
*   `POSTGRES_USER` / `POSTGRES_PASSWORD`: Database credentials.
*   `POSTGRES_DB`: Name of the database.
*   `POSTGRES_PORT`: Default is `5432`.

### Security (JWT)
Generate a secure secret key using:
```bash
openssl rand -base64 32
```
*   `JWT_SECRET`: Your generated key.
*   `JWT_ALGORITHM`: Typically `HS256`.

### Third-Party Services
*   **Brevo (Email)**: Provide `MAIL_USERNAME` and `MAIL_PASSWORD` (SMTP Key) for account verification emails.
*   **Cloudinary**: Provide `CLD_NAME`, `CLD_API_KEY`, and `CLD_API_SECRET` for user avatar storage.

---

## 🏗 Architecture & DevOps

### 1. Container Immutability
The Dockerfile is optimized using a multi-stage build and `python -m compileall`. This results in:
*   **Statelessness**: The container does not write to its own file system during runtime.
*   **Optimization**: `SizeRw` is **0 bytes**, verified by `docker inspect`.
*   **Performance**: `PYTHONDONTWRITEBYTECODE=1` ensures no `__pycache__` clutter.

### 2. Networking & Security
*   **Isolated Bridge Network**: The database is hidden from the host machine and only accessible by the API container.
*   **Healthchecks**: Built-in Docker healthchecks monitor the API's responsiveness via `curl`.
*   **Non-Root User**: The application runs under a dedicated `dima` user for security.

### 3. Database Management
To connect to the database manually while it is in the isolated network:
```bash
docker exec -it hw10_postgres_db psql -U postgres -d contacts_db
```

---

## 🛠 Local Development

If you prefer to run the application outside of Docker:

1.  **Install dependencies**:
    ```bash
    poetry install
    ```
2.  **Run migrations**:
    ```bash
    alembic upgrade head
    ```
3.  **Start development server**:
    ```bash
    fastapi dev main.py
    ```

This is a professional and clear section for your **README.md** file, covering the setup and execution of the admin creation script.

---

## 🛠 Administrative Tasks

### Creating an Initial Admin User

The project includes a utility script to quickly seed the database with an administrative account. This is particularly useful for initial deployment or resetting the development environment.

#### 1. Configure Credentials
Before running the script, ensure your `.env` file contains the following variables. The script uses `SecretStr` to handle the password securely.

| Variable | Description |
| :--- | :--- |
| `ADMIN_USERNAME` | The login username for the admin account. |
| `ADMIN_EMAIL` | The email address (used for login and identification). |
| `ADMIN_PASSWORD` | A strong password for the account. |

#### 2. Run the Script
To ensure all internal package imports (from `src`) are resolved correctly, run the utility as a module from the project root:

```bash
python -m src.utils.create_admin
```

#### What the script does:
*   **Validation:** Checks if a user with the same email or username already exists to prevent duplicates.
*   **Security:** Hashes the `ADMIN_PASSWORD` using the application's authentication service.
*   **Status:** Sets the user's role to `ADMIN` and automatically marks the account as `confirmed`.
*   **Integrity:** Performs a database commit and provides logging feedback on success or failure.

---

### Pro-tips for Development:
*   **Python Path:** If you encounter import errors, ensure you are in the root directory (`goit-pythonweb-hw-12`) and your virtual environment is active.

---

## 📊 Monitoring
To view live logs and verify the automated `entrypoint` sequence:
```bash
docker-compose logs -f app
```

---

## run tests
```bash
export PYTHONPATH=$PYTHONPATH:.
pytest --cov=src --cov-report=term-missing # run all tests

pytest --cov=src.api.auth --cov-report=term-missing tests/test_api_auth.py # run test module
```