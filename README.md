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
docker exec -it hw12_postgres_db psql -U postgres -d contacts_db
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

## 🚀 Production Deployment (Debian/Ubuntu)

### Prerequisites
* **Debian 12+** or **Ubuntu 22.04+**
* **Docker & Docker Compose** (latest versions)
* **Python 3.13+** (if running locally)
* **Poetry** (for dependency management)
* **PostgreSQL 15+** (if not using Docker)
* **Nginx** (recommended for reverse proxy)

### 1. Server Preparation
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
sudo apt install -y docker.io docker-compose-plugin

# Add user to docker group (logout and login after)
sudo usermod -aG docker $USER

# Install Python and Poetry (for local management)
sudo apt install -y python3.13 python3.13-venv python3-pip
curl -sSL https://install.python-poetry.org | python3 -
sudo mv poetry /usr/local/bin/

# Install Nginx (optional, recommended)
sudo apt install -y nginx
```

### 2. Application Deployment
```bash
# Clone repository
git clone <your-repo-url>
cd goit-pythonweb-hw-12

# Configure production environment
cp .env.example .env
nano .env  # Edit with production values

# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# Verify deployment
docker-compose ps
docker-compose logs -f app
```

### 3. Nginx Configuration (Optional)
Create `/etc/nginx/sites-available/contacts-api`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/contacts-api /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 4. SSL Certificate (Let's Encrypt)
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (add to crontab)
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### 5. Monitoring and Logs
```bash
# View application logs
docker-compose logs -f app

# Check system resources
docker stats

# Monitor database
docker exec -it contacts_postgres_db psql -U postgres -d contacts_db -c "SELECT COUNT(*) FROM contacts;"
```

### 6. Backup Strategy
```bash
# Database backup
docker exec contacts_postgres_db pg_dump -U postgres contacts_db > backup_$(date +%Y%m%d).sql

# Application data backup
docker run --rm -v contacts_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads_$(date +%Y%m%d).tar.gz -C /data .
```

---

## 🧪 Testing

```bash
# Terminal coverage report
pytest --cov=src --cov-report=term-missing

# HTML coverage report (detailed)
pytest --cov=src --cov-report=html
```
Coverage HTML written to dir htmlcov
---

## 📚 Documentation

* **API Documentation**: Available at `/docs` endpoint (Swagger UI)
* **Generated Documentation**: See `docs/` directory for Sphinx-generated docs

---

## 📞 Support & Troubleshooting

### Common Issues
* **Database Connection**: Check PostgreSQL status and credentials
* **Redis Connection**: Verify Redis is running and accessible
* **CORS Errors**: Ensure `CORS_ALLOWED_ORIGINS` includes your domain
* **Rate Limiting**: Check `ENABLE_REDIS` and Redis connectivity

### Health Checks
```bash
# Application health
curl http://localhost:8000/healthcheck

# Database health
docker exec contacts_postgres_db pg_isready -U postgres

# Redis health (if enabled)
docker exec contacts_redis redis-cli ping
```

### Log Analysis
```bash
# Error patterns
docker-compose logs app | grep ERROR

# Performance monitoring
docker-compose logs app | grep "slow\|timeout\|exception"
```

---

## 📄 Additional Files

* **[DEPLOYMENT.md](DEPLOYMENT.md)**: Detailed deployment guide
