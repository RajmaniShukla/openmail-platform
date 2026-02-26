# 🔧 OpenMail Platform - Troubleshooting Guide

**Version:** 1.0  
**Last Updated:** 2026-02-26

---

## 📋 Table of Contents

1. [Diagnostic Commands](#1-diagnostic-commands)
2. [Installation Issues](#2-installation-issues)
3. [Authentication Issues](#3-authentication-issues)
4. [Email Delivery Issues](#4-email-delivery-issues)
5. [Performance Issues](#5-performance-issues)
6. [Database Issues](#6-database-issues)
7. [SSL/TLS Issues](#7-ssltls-issues)
8. [Service-Specific Issues](#8-service-specific-issues)
9. [Log Analysis](#9-log-analysis)
10. [Emergency Procedures](#10-emergency-procedures)

---

## 1. Diagnostic Commands

### 1.1 Quick Health Check

```bash
#!/bin/bash
# health-check.sh

echo "=== OpenMail Health Check ==="

# Check Docker
echo -n "Docker: "
docker info > /dev/null 2>&1 && echo "✓ Running" || echo "✗ Not running"

# Check all containers
echo -e "\n=== Container Status ==="
docker compose ps

# Check API health
echo -e "\n=== API Health ==="
curl -s http://localhost:8000/health | jq .

# Check disk space
echo -e "\n=== Disk Space ==="
df -h / | tail -1

# Check memory
echo -e "\n=== Memory Usage ==="
free -h

# Check database connections
echo -e "\n=== Database Connections ==="
docker compose exec -T postgres psql -U openmail -c "SELECT count(*) FROM pg_stat_activity;"
```

### 1.2 Service Status Commands

```bash
# All services
docker compose ps

# Specific service logs
docker compose logs -f backend
docker compose logs -f postfix
docker compose logs -f postgres

# Container resource usage
docker stats --no-stream

# Network status
docker network ls
docker network inspect openmail_default
```

---

## 2. Installation Issues

### 2.1 Docker Compose Fails to Start

**Symptom:** `docker compose up` fails or containers exit immediately

**Solutions:**

```bash
# Check for port conflicts
sudo lsof -i :80
sudo lsof -i :443
sudo lsof -i :5432

# Stop conflicting services
sudo systemctl stop apache2
sudo systemctl stop nginx
sudo systemctl stop postgresql

# Check Docker logs
docker compose logs --tail=50

# Rebuild from scratch
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### 2.2 Permission Denied Errors

**Symptom:** `Permission denied` when accessing files/volumes

**Solutions:**

```bash
# Fix ownership
sudo chown -R $USER:$USER /opt/openmail

# Fix Docker socket permissions
sudo chmod 666 /var/run/docker.sock

# Add user to docker group
sudo usermod -aG docker $USER
# Then log out and back in
```

### 2.3 Database Migration Fails

**Symptom:** `alembic upgrade head` fails

**Solutions:**

```bash
# Check database is running
docker compose ps postgres

# Connect to database directly
docker compose exec postgres psql -U openmail

# Check migration status
docker compose exec backend alembic current

# Reset migrations (CAUTION: data loss)
docker compose exec backend alembic downgrade base
docker compose exec backend alembic upgrade head
```

---

## 3. Authentication Issues

### 3.1 Cannot Login

**Symptom:** Login always fails even with correct credentials

**Diagnostic:**
```bash
# Check backend logs
docker compose logs backend | grep -i "login\|auth"

# Check database for user
docker compose exec postgres psql -U openmail -c \
  "SELECT email, is_active, is_verified, locked_until FROM users WHERE email='user@example.com';"
```

**Solutions:**

| Cause | Solution |
|-------|----------|
| Account locked | Wait for lockout period or reset: `UPDATE users SET locked_until=NULL, failed_login_attempts=0 WHERE email='...'` |
| Account inactive | Activate: `UPDATE users SET is_active=true WHERE email='...'` |
| Account not verified | Verify: `UPDATE users SET is_verified=true WHERE email='...'` |
| Wrong password | Reset password via admin or forgot password flow |

### 3.2 JWT Token Invalid

**Symptom:** "Invalid token" or "Token expired" errors

**Solutions:**

```bash
# Check server time sync
timedatectl status

# Sync time if needed
sudo timedatectl set-ntp true

# Check JWT secret matches
grep JWT_SECRET .env

# Clear all sessions (logout everyone)
docker compose exec postgres psql -U openmail -c "TRUNCATE sessions;"
```

### 3.3 Session Expired Too Fast

**Symptom:** Users logged out unexpectedly

**Check:**
```bash
# Verify token expiry settings
grep TOKEN_EXPIRE .env

# Check Redis is working
docker compose exec redis redis-cli PING
```

---

## 4. Email Delivery Issues

### 4.1 Emails Not Sending

**Symptom:** Send button works but email never arrives

**Diagnostic:**
```bash
# Check Postfix queue
docker compose exec postfix postqueue -p

# Check Postfix logs
docker compose logs postfix | tail -100

# Test SMTP connection
docker compose exec postfix swaks --to test@gmail.com --from test@yourdomain.com
```

**Solutions:**

| Cause | Solution |
|-------|----------|
| Queue blocked | Flush queue: `docker compose exec postfix postqueue -f` |
| DNS issues | Check MX record: `dig MX yourdomain.com` |
| Blocked port 25 | Contact hosting provider to unblock |
| SPF fail | Update SPF record in DNS |
| Blacklisted IP | Check at mxtoolbox.com/blacklists |

### 4.2 Emails Not Receiving

**Symptom:** Incoming emails never appear in inbox

**Diagnostic:**
```bash
# Check Postfix is listening
docker compose exec postfix netstat -tlnp | grep 25

# Check Dovecot
docker compose exec dovecot doveadm mailbox list -u user@domain.com

# Check mail logs
docker compose logs postfix | grep "from=<" | tail -20
```

**Solutions:**

| Cause | Solution |
|-------|----------|
| MX record wrong | Verify: `dig MX yourdomain.com +short` |
| Firewall blocking | Open port 25: `sudo ufw allow 25/tcp` |
| Dovecot not running | Restart: `docker compose restart dovecot` |

### 4.3 Emails Going to Spam

**Symptom:** Sent emails land in recipient's spam folder

**Diagnostic:**
```bash
# Test email score
# Send test to: https://www.mail-tester.com/

# Check DKIM signature
docker compose exec opendkim opendkim-testkey -d yourdomain.com -s mail

# Check SPF
dig TXT yourdomain.com | grep spf
```

**Solutions:**

1. **Set up DKIM properly** - Ensure key is in DNS
2. **Configure SPF** - Add all sending IPs
3. **Set up DMARC** - Add DMARC record
4. **Warm up IP** - Start with low volume
5. **Check content** - Avoid spam trigger words

### 4.4 Attachment Issues

**Symptom:** Attachments fail to upload or download

**Diagnostic:**
```bash
# Check MinIO status
docker compose exec minio mc admin info local

# Check bucket exists
docker compose exec minio mc ls local/attachments

# Check disk space
docker compose exec minio df -h
```

**Solutions:**
```bash
# Recreate bucket
docker compose exec minio mc mb local/attachments

# Fix permissions
docker compose exec minio mc policy set download local/attachments
```

---

## 5. Performance Issues

### 5.1 Slow Page Load

**Symptom:** Pages take > 3 seconds to load

**Diagnostic:**
```bash
# Check backend response time
time curl -s http://localhost:8000/health

# Check database query time
docker compose exec postgres psql -U openmail -c "EXPLAIN ANALYZE SELECT * FROM emails LIMIT 100;"

# Check Redis latency
docker compose exec redis redis-cli --latency
```

**Solutions:**

| Cause | Solution |
|-------|----------|
| Slow queries | Add indexes, optimize queries |
| No caching | Enable Redis caching |
| Large response | Implement pagination |
| High memory | Increase container memory limit |

### 5.2 High CPU Usage

**Diagnostic:**
```bash
# Find high CPU containers
docker stats --no-stream

# Check running processes
docker compose exec backend top
```

**Solutions:**
- Add more backend replicas
- Optimize email processing
- Add rate limiting

### 5.3 Database Slow

**Diagnostic:**
```bash
# Check slow queries
docker compose exec postgres psql -U openmail -c \
  "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check index usage
docker compose exec postgres psql -U openmail -c \
  "SELECT relname, idx_scan, seq_scan FROM pg_stat_user_tables ORDER BY seq_scan DESC LIMIT 10;"
```

**Solutions:**
```bash
# Run vacuum
docker compose exec postgres psql -U openmail -c "VACUUM ANALYZE;"

# Add missing indexes
docker compose exec postgres psql -U openmail -c \
  "CREATE INDEX CONCURRENTLY idx_emails_subject ON emails(subject);"
```

---

## 6. Database Issues

### 6.1 Connection Refused

**Symptom:** `could not connect to server: Connection refused`

**Solutions:**
```bash
# Check PostgreSQL is running
docker compose ps postgres

# Restart PostgreSQL
docker compose restart postgres

# Check logs
docker compose logs postgres | tail -50

# Check connection limit
docker compose exec postgres psql -U openmail -c "SHOW max_connections;"
```

### 6.2 Disk Full

**Symptom:** `No space left on device`

**Solutions:**
```bash
# Check disk usage
docker system df

# Clean Docker
docker system prune -a --volumes

# Clean old emails (careful!)
docker compose exec postgres psql -U openmail -c \
  "DELETE FROM emails WHERE deleted_at < NOW() - INTERVAL '30 days';"

# Vacuum to reclaim space
docker compose exec postgres psql -U openmail -c "VACUUM FULL;"
```

### 6.3 Corrupted Data

**Symptom:** Errors reading from database

**Solutions:**
```bash
# Check database integrity
docker compose exec postgres pg_isready

# Run consistency check
docker compose exec postgres psql -U openmail -c \
  "SELECT relname, n_dead_tup FROM pg_stat_user_tables WHERE n_dead_tup > 1000;"

# Restore from backup if needed
gunzip -c backup.sql.gz | docker compose exec -T postgres psql -U openmail openmail
```

---

## 7. SSL/TLS Issues

### 7.1 Certificate Expired

**Symptom:** Browser shows security warning

**Solutions:**
```bash
# Check certificate expiry
openssl x509 -enddate -noout -in /etc/letsencrypt/live/yourdomain.com/cert.pem

# Renew certificate
sudo certbot renew

# Restart nginx
docker compose restart nginx
```

### 7.2 Mixed Content Warnings

**Symptom:** Browser blocks some resources

**Solutions:**
- Ensure all URLs use HTTPS
- Update `CORS_ORIGINS` to use HTTPS
- Check for hardcoded HTTP URLs

### 7.3 Certificate Chain Incomplete

**Symptom:** Some clients can't connect

**Solutions:**
```bash
# Verify certificate chain
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Use fullchain.pem instead of cert.pem
```

---

## 8. Service-Specific Issues

### 8.1 Elasticsearch Not Indexing

```bash
# Check Elasticsearch health
curl http://localhost:9200/_cluster/health

# Check index status
curl http://localhost:9200/_cat/indices

# Rebuild index
docker compose exec backend python -m scripts.reindex_emails
```

### 8.2 Redis Memory Issues

```bash
# Check memory usage
docker compose exec redis redis-cli INFO memory

# Clear cache if needed
docker compose exec redis redis-cli FLUSHDB
```

### 8.3 Celery Workers Stuck

```bash
# Check worker status
docker compose exec celery celery -A app.services.celery_tasks inspect active

# Restart workers
docker compose restart celery

# Purge stuck tasks
docker compose exec celery celery -A app.services.celery_tasks purge
```

---

## 9. Log Analysis

### 9.1 Common Log Patterns

```bash
# Find errors
docker compose logs --tail=1000 | grep -i "error\|exception\|failed"

# Find slow requests
docker compose logs backend | grep -E "took [0-9]{4,}ms"

# Find authentication failures
docker compose logs backend | grep -i "401\|unauthorized\|invalid.*token"

# Find email delivery issues
docker compose logs postfix | grep -i "reject\|bounce\|deferred"
```

### 9.2 Log Locations

| Service | Log Location |
|---------|--------------|
| Backend | stdout (docker logs) |
| Nginx | /var/log/nginx/ |
| Postfix | /var/log/mail.log |
| PostgreSQL | stdout (docker logs) |

---

## 10. Emergency Procedures

### 10.1 Complete Service Restart

```bash
# Stop all services
docker compose down

# Clear any stuck containers
docker rm -f $(docker ps -aq)

# Start fresh
docker compose up -d

# Verify all services
docker compose ps
```

### 10.2 Database Emergency Recovery

```bash
# Stop application
docker compose stop backend frontend

# Restore from latest backup
docker compose exec -T postgres psql -U openmail < /backups/latest.sql

# Start application
docker compose start backend frontend
```

### 10.3 Rollback Deployment

```bash
# Rollback to previous version
git checkout HEAD~1

# Rebuild and redeploy
docker compose build
docker compose up -d
```

### 10.4 Contact Information

For critical issues:
- Check GitHub Issues
- Community Discord
- Admin contact: admin@yourdomain.com

---

*Troubleshooting Guide v1.0*
*Generated by Chanakya 🧠*
