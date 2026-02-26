# 🚀 OpenMail Platform - DevOps Deployment Guide

**Version:** 1.0  
**Last Updated:** 2026-02-26  
**Target:** Production Deployment

---

## 📋 Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Architecture Overview](#2-architecture-overview)
3. [Development Setup](#3-development-setup)
4. [Production Deployment](#4-production-deployment)
5. [DNS Configuration](#5-dns-configuration)
6. [SSL/TLS Setup](#6-ssltls-setup)
7. [Environment Configuration](#7-environment-configuration)
8. [Monitoring & Logging](#8-monitoring--logging)
9. [Backup & Recovery](#9-backup--recovery)
10. [Scaling](#10-scaling)
11. [Maintenance](#11-maintenance)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Prerequisites

### 1.1 Server Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Storage | 50 GB SSD | 200+ GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

### 1.2 Software Requirements

```bash
# Docker & Docker Compose
docker --version          # 24.0+
docker compose version    # 2.20+

# Domain & DNS access
# SSL certificate (Let's Encrypt or commercial)
```

### 1.3 Network Requirements

| Port | Service | Protocol |
|------|---------|----------|
| 25 | SMTP (inbound) | TCP |
| 80 | HTTP (redirect) | TCP |
| 443 | HTTPS | TCP |
| 587 | SMTP (submission) | TCP |
| 993 | IMAPS | TCP |
| 995 | POP3S | TCP |

### 1.4 DNS Requirements

- A domain name you control
- Access to DNS management
- Static IP address for mail server

---

## 2. Architecture Overview

### 2.1 Production Stack

```
┌─────────────────────────────────────────────────────────────┐
│                        INTERNET                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     NGINX PROXY                              │
│              (SSL Termination, Load Balancing)               │
│                    Ports: 80, 443                            │
└────────┬────────────────────────────────────┬───────────────┘
         │                                    │
┌────────▼────────┐                ┌─────────▼─────────┐
│    FRONTEND     │                │   MAIL SERVER     │
│    (Next.js)    │                │                   │
│    Port: 3000   │                │ Postfix (25,587)  │
└────────┬────────┘                │ Dovecot (993,995) │
         │                         │ SpamAssassin      │
         │                         │ OpenDKIM          │
┌────────▼────────┐                └─────────┬─────────┘
│    BACKEND      │                          │
│    (FastAPI)    │◄─────────────────────────┘
│    Port: 8000   │
└────────┬────────┘
         │
┌────────┼────────────────────────────────────┐
│        │              DATA LAYER            │
│  ┌─────▼─────┐  ┌───────┐  ┌────────────┐  │
│  │ PostgreSQL│  │ Redis │  │Elasticsearch│  │
│  │   :5432   │  │ :6379 │  │   :9200    │  │
│  └───────────┘  └───────┘  └────────────┘  │
│                                             │
│  ┌────────────┐  ┌─────────────────────┐   │
│  │   MinIO    │  │   Prometheus/Grafana│   │
│  │   :9000    │  │   :9090 / :3001     │   │
│  └────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────┘
```

### 2.2 Container Services

| Service | Image | Purpose |
|---------|-------|---------|
| nginx | nginx:alpine | Reverse proxy, SSL |
| frontend | node:20-alpine | Next.js app |
| backend | python:3.11-slim | FastAPI API |
| postgres | postgres:15 | Primary database |
| redis | redis:7-alpine | Cache, sessions |
| elasticsearch | elasticsearch:8 | Full-text search |
| minio | minio/minio | Object storage |
| postfix | custom | SMTP server |
| dovecot | custom | IMAP/POP3 |
| prometheus | prom/prometheus | Metrics |
| grafana | grafana/grafana | Dashboards |

---

## 3. Development Setup

### 3.1 Clone Repository

```bash
git clone https://github.com/RajmaniShukla/openmail-platform.git
cd openmail-platform
```

### 3.2 Create Environment File

```bash
cp .env.example .env
# Edit .env with development settings
vim .env
```

### 3.3 Start Development Stack

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### 3.4 Access Development URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/api/docs |
| Grafana | http://localhost:3001 |
| MinIO | http://localhost:9001 |

### 3.5 Development Workflow

```bash
# Backend development (hot reload)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend development (hot reload)
cd frontend
npm install
npm run dev

# Run tests
cd backend && pytest
cd frontend && npm test
```

---

## 4. Production Deployment

### 4.1 Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Create deployment directory
sudo mkdir -p /opt/openmail
sudo chown $USER:$USER /opt/openmail
```

### 4.2 Clone and Configure

```bash
cd /opt/openmail
git clone https://github.com/RajmaniShukla/openmail-platform.git .

# Create production environment
cp .env.example .env.production
vim .env.production
```

### 4.3 Production Environment Variables

```bash
# .env.production

# App
APP_NAME=OpenMail
DEBUG=false
DOMAIN=mail.yourdomain.com

# Database (use strong password!)
POSTGRES_PASSWORD=your-super-strong-password-here
DATABASE_URL=postgresql+asyncpg://openmail:${POSTGRES_PASSWORD}@postgres:5432/openmail

# Redis
REDIS_URL=redis://redis:6379/0

# Security (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=your-256-bit-secret-key-here

# CORS
CORS_ORIGINS=["https://mail.yourdomain.com"]

# SMTP
MAIL_SERVER_HOSTNAME=mail.yourdomain.com
POSTFIX_HOST=postfix
POSTFIX_PORT=25

# MinIO/S3
S3_ENDPOINT=minio:9000
S3_ACCESS_KEY=your-minio-access-key
S3_SECRET_KEY=your-minio-secret-key

# SSL
SSL_CERTIFICATE=/etc/letsencrypt/live/mail.yourdomain.com/fullchain.pem
SSL_PRIVATE_KEY=/etc/letsencrypt/live/mail.yourdomain.com/privkey.pem
```

### 4.4 Deploy with Docker Compose

```bash
# Build and start production stack
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Initialize database
docker compose exec backend alembic upgrade head

# Create admin user
docker compose exec backend python -m scripts.create_admin

# Verify all services running
docker compose ps
```

### 4.5 Automated Deployment Script

```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 Starting OpenMail deployment..."

# Pull latest code
git pull origin main

# Build images
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Stop old containers
docker compose down

# Start new containers
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Run migrations
docker compose exec -T backend alembic upgrade head

# Clean old images
docker image prune -f

echo "✅ Deployment complete!"
```

---

## 5. DNS Configuration

### 5.1 Required DNS Records

```
# A Record - Mail server IP
mail.yourdomain.com.     A      YOUR_SERVER_IP

# MX Record - Mail routing
yourdomain.com.          MX     10 mail.yourdomain.com.

# SPF Record - Sender authorization
yourdomain.com.          TXT    "v=spf1 mx a ip4:YOUR_SERVER_IP ~all"

# DKIM Record - Email signing (get key from admin panel)
mail._domainkey.yourdomain.com.  TXT  "v=DKIM1; k=rsa; p=MIIBIjANBgkq..."

# DMARC Record - Authentication policy
_dmarc.yourdomain.com.   TXT    "v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com"

# PTR Record - Reverse DNS (set at hosting provider)
YOUR_SERVER_IP           PTR    mail.yourdomain.com.
```

### 5.2 DNS Verification

```bash
# Verify MX record
dig MX yourdomain.com +short

# Verify SPF
dig TXT yourdomain.com +short

# Verify DKIM
dig TXT mail._domainkey.yourdomain.com +short

# Verify PTR (reverse DNS)
dig -x YOUR_SERVER_IP +short

# Test email deliverability
# Use: https://www.mail-tester.com/
```

---

## 6. SSL/TLS Setup

### 6.1 Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt install certbot -y

# Stop nginx temporarily
docker compose stop nginx

# Get certificate
sudo certbot certonly --standalone -d mail.yourdomain.com

# Certificate files location:
# /etc/letsencrypt/live/mail.yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/mail.yourdomain.com/privkey.pem
```

### 6.2 Auto-Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Add cron job for auto-renewal
sudo crontab -e
# Add: 0 3 * * * certbot renew --post-hook "docker compose -C /opt/openmail restart nginx"
```

### 6.3 Nginx SSL Configuration

```nginx
# nginx/conf.d/ssl.conf
server {
    listen 443 ssl http2;
    server_name mail.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/mail.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mail.yourdomain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
```

---

## 7. Environment Configuration

### 7.1 Complete Environment Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `APP_NAME` | Application name | OpenMail | No |
| `DEBUG` | Debug mode | false | No |
| `DOMAIN` | Mail domain | localhost | Yes |
| `DATABASE_URL` | PostgreSQL connection | - | Yes |
| `REDIS_URL` | Redis connection | - | Yes |
| `JWT_SECRET_KEY` | JWT signing key | - | Yes |
| `CORS_ORIGINS` | Allowed origins | [] | Yes |
| `POSTFIX_HOST` | Postfix hostname | localhost | Yes |
| `S3_ENDPOINT` | MinIO endpoint | - | Yes |
| `S3_ACCESS_KEY` | MinIO access key | - | Yes |
| `S3_SECRET_KEY` | MinIO secret key | - | Yes |
| `ELASTICSEARCH_URL` | ES endpoint | - | No |

### 7.2 Secrets Management

```bash
# Generate secure secrets
openssl rand -hex 32  # JWT secret
openssl rand -base64 32  # Database password
openssl rand -base64 24  # MinIO keys

# Store secrets securely
# Option 1: Docker secrets
echo "your-secret" | docker secret create jwt_secret -

# Option 2: HashiCorp Vault
vault kv put secret/openmail jwt_secret="your-secret"

# Option 3: AWS Secrets Manager / GCP Secret Manager
```

---

## 8. Monitoring & Logging

### 8.1 Prometheus Configuration

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: /metrics

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
```

### 8.2 Grafana Dashboards

Access Grafana at `http://your-server:3001`

Pre-configured dashboards:
- **OpenMail Overview** - Main metrics
- **API Performance** - Request rates, latency
- **Database Health** - PostgreSQL metrics
- **Mail Server** - Postfix/Dovecot stats

### 8.3 Log Aggregation

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f backend

# Export logs to file
docker compose logs --no-color > openmail.log

# Tail last 100 lines
docker compose logs --tail=100 backend
```

### 8.4 Alert Configuration

```yaml
# monitoring/prometheus/rules/alerts.yml
groups:
  - name: openmail
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
          
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: PostgreSQL is down
```

---

## 9. Backup & Recovery

### 9.1 Database Backup

```bash
#!/bin/bash
# scripts/backup-db.sh

BACKUP_DIR="/opt/openmail/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="openmail_db_${DATE}.sql.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker compose exec -T postgres pg_dump -U openmail openmail | gzip > $BACKUP_DIR/$FILENAME

# Keep last 7 days
find $BACKUP_DIR -name "openmail_db_*.sql.gz" -mtime +7 -delete

echo "Backup created: $FILENAME"
```

### 9.2 Attachment Backup

```bash
#!/bin/bash
# scripts/backup-attachments.sh

BACKUP_DIR="/opt/openmail/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup MinIO data
docker compose exec -T minio mc mirror local/attachments /backup/

# Or use rclone for S3-compatible backup
rclone sync minio:attachments backup:openmail-attachments/
```

### 9.3 Automated Backup Schedule

```bash
# /etc/cron.d/openmail-backup
0 2 * * * root /opt/openmail/scripts/backup-db.sh >> /var/log/openmail-backup.log 2>&1
0 3 * * * root /opt/openmail/scripts/backup-attachments.sh >> /var/log/openmail-backup.log 2>&1
```

### 9.4 Restore Procedures

```bash
# Restore database
gunzip -c backup.sql.gz | docker compose exec -T postgres psql -U openmail openmail

# Restore attachments
docker compose exec -T minio mc mirror /backup/ local/attachments
```

---

## 10. Scaling

### 10.1 Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G

  frontend:
    deploy:
      replicas: 2
```

```bash
# Scale services
docker compose up -d --scale backend=3 --scale frontend=2
```

### 10.2 Database Read Replicas

```yaml
# Add read replica
services:
  postgres-replica:
    image: postgres:15
    environment:
      POSTGRES_PRIMARY_HOST: postgres
    command: |
      postgres -c hot_standby=on
```

### 10.3 Redis Cluster

```yaml
services:
  redis:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes
```

---

## 11. Maintenance

### 11.1 Update Procedures

```bash
# Pull latest images
docker compose pull

# Rebuild custom images
docker compose build --no-cache

# Rolling update
docker compose up -d --no-deps backend
docker compose up -d --no-deps frontend

# Run migrations
docker compose exec backend alembic upgrade head
```

### 11.2 Security Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Rebuild containers with latest base images
docker compose build --pull --no-cache
docker compose up -d
```

### 11.3 Database Maintenance

```bash
# Vacuum and analyze
docker compose exec postgres psql -U openmail -c "VACUUM ANALYZE;"

# Reindex
docker compose exec postgres psql -U openmail -c "REINDEX DATABASE openmail;"

# Check table sizes
docker compose exec postgres psql -U openmail -c "
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 10;"
```

---

## 12. Troubleshooting

See `TROUBLESHOOTING.md` for detailed troubleshooting guide.

### Quick Diagnostics

```bash
# Check all services status
docker compose ps

# Check service health
docker compose exec backend curl -s localhost:8000/health

# View recent errors
docker compose logs --tail=100 backend | grep -i error

# Check disk space
df -h

# Check memory usage
docker stats --no-stream

# Test email flow
docker compose exec postfix postqueue -p
```

### Common Issues Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| 502 Bad Gateway | `docker compose restart backend` |
| Database connection error | `docker compose restart postgres` |
| Email not sending | Check Postfix: `docker compose logs postfix` |
| SSL certificate error | Renew: `certbot renew` |
| Out of disk space | Clean: `docker system prune -a` |

---

*DevOps Deployment Guide v1.0*
*Generated by Chanakya 🧠*
