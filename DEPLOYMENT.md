# Production Deployment Guide

This guide covers production deployment of the Contacts Management API on Debian/Ubuntu servers.

## 🏗 System Requirements

### Minimum Requirements
- **OS**: Debian 11+ or Ubuntu 20.04+
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 20GB minimum, 50GB recommended
- **CPU**: 2 cores minimum, 4 cores recommended
- **Network**: Stable internet connection

### Software Requirements
- **Docker**: 20.10+ and Docker Compose 2.0+
- **Python**: 3.13+ (for local management)
- **PostgreSQL**: 15+ (if not using Docker)
- **Nginx**: 1.18+ (recommended for production)

## 🚀 Deployment Steps

### 1. Server Preparation

#### Update System Packages
```bash
# Update package lists and upgrade existing packages
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl wget git htop unzip
```

#### Install Docker and Docker Compose
```bash
# Remove old versions
sudo apt remove -y docker docker-engine docker.io containerd runc

# Install Docker repository
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture)] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Configure Docker User
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply changes (logout and login required)
newgrp docker
```

#### Install Python and Poetry (Optional)
```bash
# Install Python dependencies
sudo apt install -y python3.13 python3.13-venv python3-pip python3-dev

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
sudo mv poetry /usr/local/bin/

# Verify installation
poetry --version
```

### 2. Application Setup

#### Clone Repository
```bash
# Clone the application
git clone https://github.com/your-username/goit-pythonweb-hw-12.git
cd goit-pythonweb-hw-12

# Switch to production branch if exists
git checkout production
```

#### Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit production configuration
nano .env
```

**Critical Production Settings:**
```bash
# Database Configuration
POSTGRES_USER=contacts_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=contacts_prod
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Security Configuration
JWT_SECRET=your_very_long_and_secure_jwt_secret_key_minimum_32_characters
JWT_ALGORITHM=HS256
JWT_EXPIRATION_SECONDS=3600

# Email Configuration (Brevo)
MAIL_USERNAME=your_email@domain.com
MAIL_PASSWORD=your_brevo_smtp_key
MAIL_FROM=noreply@yourdomain.com
MAIL_FROM_NAME="Contacts API"
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_STARTTLS=true
MAIL_SSL_TLS=false

# Cloudinary Configuration
CLD_NAME=your_cloud_name
CLD_API_KEY=your_cloudinary_api_key
CLD_API_SECRET=your_cloudinary_api_secret

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=very_secure_admin_password

# CORS Configuration
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Redis Configuration
ENABLE_REDIS=true
REDIS_HOST=redis
REDIS_PORT=6379

# Logging
LOG_LEVEL=INFO
```

### 3. Production Docker Compose

Create `docker-compose.prod.yml`:
```yaml
services:
  db:
    image: postgres:15-alpine
    container_name: hw12_postgres_db
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - internal_app_net

  redis:
    image: redis:7-alpine
    container_name: hw12_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - internal_app_net
    restart: always

  app:
    build: .
    container_name: hw12_fastapi_app
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      POSTGRES_HOST: db
      REDIS_HOST: redis
      REDIS_PORT: 6379
    depends_on:
      - db
      - redis
    networks:
      - internal_app_net

volumes:
  postgres_data:
  redis_data:

networks:
  internal_app_net:
    driver: bridge
```

### 4. Deploy Application

```bash
# Build and start production services
docker-compose -f docker-compose.prod.yml up -d --build

# Monitor deployment progress
docker-compose -f docker-compose.prod.yml logs -f app
```

### 5. Verify Deployment

#### Health Checks
```bash
# Check all services status
docker-compose -f docker-compose.prod.yml ps

# Check application health
curl -f http://localhost:8000/healthcheck

# Check database connection
docker exec contacts_postgres_prod psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT COUNT(*) FROM contacts;"

# Check Redis connection
docker exec contacts_redis_prod redis-cli ping
```

#### Service Logs
```bash
# View application logs
docker-compose -f docker-compose.prod.yml logs -f app

# View database logs
docker-compose -f docker-compose.prod.yml logs -f postgres_db

# View Redis logs
docker-compose -f docker-compose.prod.yml logs -f redis
```

## 🔒 Security Configuration

### Firewall Setup
```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp  # If direct access needed
```

### SSL Certificate (Let's Encrypt)
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -m admin@yourdomain.com

# Auto-renewal setup
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

## 🌐 Nginx Reverse Proxy

### Production Nginx Configuration
Create `/etc/nginx/sites-available/contacts-api`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /healthcheck {
        proxy_pass http://127.0.0.1:8000;
        access_log off;
    }
}
```

### Enable Nginx Site
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/contacts-api /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

## 📊 Monitoring and Maintenance

### System Monitoring
```bash
# System resources
htop
df -h
free -h
iostat -x 1

# Docker containers
docker stats --no-stream
docker system df
```

### Application Monitoring
```bash
# Application logs with filtering
docker-compose -f docker-compose.prod.yml logs -f app | grep ERROR
docker-compose -f docker-compose.prod.yml logs -f app | grep WARNING

# Performance monitoring
```bash
curl -s -o /dev/null -w " \
@dns_time=%{time_namelookup}s\n \
@connect_time=%{time_connect}s\n \
@appconnect_time=%{time_appconnect}s\n \
@pretransfer_time=%{time_pretransfer}s\n \
@redirect_time=%{time_redirect}s\n \
@starttransfer_time=%{time_starttransfer}s\n \
@total_time=%{time_total}s\n \
@http_code=%{http_code}\n" \
"http://localhost:8000/healthcheck"
```

# Database monitoring
docker exec contacts_postgres_prod psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT COUNT(*) FROM contacts WHERE created_at > NOW() - INTERVAL '1 hour';"
```

### Backup Strategy
```bash
# Automated database backup
cat > backup_db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
mkdir -p $BACKUP_DIR

docker exec contacts_postgres_prod pg_dump -U ${POSTGRES_USER} -d ${POSTGRES_DB} | gzip > $BACKUP_DIR/contacts_backup_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "contacts_backup_*.sql.gz" -mtime +7 -delete
EOF

chmod +x backup_db.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /path/to/backup_db.sh" | crontab -

# Application data backup
cat > backup_uploads.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
mkdir -p $BACKUP_DIR

docker run --rm -v contacts_uploads:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/uploads_backup_$DATE.tar.gz -C /data .
EOF

chmod +x backup_uploads.sh

# Add to crontab (weekly on Sunday at 3 AM)
echo "0 3 * * 0 /path/to/backup_uploads.sh" | crontab -
```

## 🔄 Updates and Maintenance

### Application Updates
```bash
# Pull latest changes
git pull origin production

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Run database migrations
docker-compose -f docker-compose.prod.yml exec app alembic upgrade head
```

### Rolling Updates
```bash
# 1. Build new images without stopping current containers
docker compose -f docker-compose.prod.yml build

# 2. Execute the update
# Docker Compose will attempt to create the new container before stopping the old one.
# This minimizes downtime, though port 8000 might be momentarily occupied during the switch.
docker compose -f docker-compose.prod.yml up -d --no-deps app

# 3. Clean up obsolete images to reclaim disk space
docker image prune -f
```

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database status
docker exec contacts_postgres_prod pg_isready -U ${POSTGRES_USER}

# Check database logs
docker-compose -f docker-compose.prod.yml logs -f postgres_db

# Test connection manually
docker exec contacts_postgres_prod psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT 1;"
```

#### Application Issues
```bash
# Check application logs
docker-compose -f docker-compose.prod.yml logs -f app

# Check container status
docker inspect contacts_api_prod

# Restart application
docker-compose -f docker-compose.prod.yml restart app
```

#### Performance Issues
```bash
# Check system resources
free -h
df -h
docker stats

# Check database performance
docker exec contacts_postgres_prod psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT * FROM pg_stat_activity;"

# Optimize database
docker exec contacts_postgres_prod psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "VACUUM ANALYZE;"
```

### Emergency Recovery
```bash
# Full application restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Database recovery from backup
gunzip -c /backups/latest_backup.sql.gz
docker exec -i contacts_postgres_prod psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < /backups/latest_backup.sql
```

## 📋 Production Checklist

### Pre-Deployment Checklist
- [ ] Server requirements met (OS, RAM, Storage)
- [ ] Docker and Docker Compose installed
- [ ] Firewall configured
- [ ] SSL certificate obtained
- [ ] Environment variables configured
- [ ] Database credentials secure
- [ ] JWT secret generated (32+ characters)
- [ ] Email service configured
- [ ] Cloudinary configured
- [ ] Backup strategy planned

### Post-Deployment Checklist
- [ ] All containers running and healthy
- [ ] Health checks passing
- [ ] SSL certificate valid
- [ ] Nginx proxy working
- [ ] Database accessible
- [ ] Redis accessible (if enabled)
- [ ] Application responding on port 8000
- [ ] Monitoring configured
- [ ] Backup scripts scheduled
- [ ] Log rotation configured
- [ ] Performance baseline established

This deployment guide ensures a production-ready, secure, and maintainable Contacts Management API deployment.
