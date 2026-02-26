# 📧 OpenMail Platform

A production-grade, self-hosted email platform similar to Gmail. Built with modern technologies for reliability, security, and scalability.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![Next.js](https://img.shields.io/badge/next.js-14-black.svg)

## ✨ Features

### 📬 Complete Email Solution
- **Full Email Server**: Postfix (SMTP) + Dovecot (IMAP/POP3)
- **Modern Webmail**: Gmail-like interface with React/Next.js
- **API-First**: RESTful API for all operations
- **Custom Domains**: Add and verify your own domains
- **DKIM/SPF/DMARC**: Built-in email authentication

### 🔐 Security
- **TLS Encryption**: End-to-end encryption for all connections
- **JWT Authentication**: Secure token-based auth with refresh
- **Rate Limiting**: Protection against abuse
- **Spam Filtering**: SpamAssassin integration
- **Virus Scanning**: ClamAV support (optional)

### 📊 Monitoring & Observability
- **Prometheus Metrics**: Full observability stack
- **Grafana Dashboards**: Pre-configured dashboards
- **Structured Logging**: JSON logs for easy parsing
- **Health Checks**: Automatic service monitoring

### 🚀 Performance
- **Async Backend**: FastAPI with async PostgreSQL
- **Elasticsearch**: Full-text email search
- **Redis Caching**: Fast session and cache layer
- **Background Tasks**: Celery for async processing

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         NGINX (Reverse Proxy)                    │
│                    SSL Termination / Load Balancing              │
└─────────────────┬───────────────────────────────┬───────────────┘
                  │                               │
    ┌─────────────▼─────────────┐   ┌────────────▼────────────┐
    │    Frontend (Next.js)     │   │   Backend API (FastAPI) │
    │     React + TailwindCSS   │   │   REST API + WebSocket  │
    └───────────────────────────┘   └────────────┬────────────┘
                                                  │
    ┌─────────────────────────────────────────────┼─────────────────┐
    │                    Data Layer               │                 │
    │  ┌──────────┐ ┌───────┐ ┌─────────────┐    │    ┌─────────┐  │
    │  │PostgreSQL│ │ Redis │ │Elasticsearch│    │    │  MinIO  │  │
    │  │  (Data)  │ │(Cache)│ │  (Search)   │    │    │(Storage)│  │
    │  └──────────┘ └───────┘ └─────────────┘    │    └─────────┘  │
    └─────────────────────────────────────────────┼─────────────────┘
                                                  │
    ┌─────────────────────────────────────────────┼─────────────────┐
    │                  Mail Server                │                 │
    │  ┌──────────────┐      ┌───────────────┐   │ ┌─────────────┐ │
    │  │   Postfix    │──────│   Dovecot     │───┴─│SpamAssassin │ │
    │  │  (SMTP MTA)  │      │ (IMAP/POP3)   │     │  (Filter)   │ │
    │  └──────────────┘      └───────────────┘     └─────────────┘ │
    └─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- A domain name (for production)
- DNS access (to configure MX, SPF, DKIM records)

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/openmail-platform.git
cd openmail-platform

# Start with Docker Compose
./scripts/deploy.sh

# Or manually:
cp .env.example .env
# Edit .env with your settings
docker compose up -d
```

Access the webmail at `https://localhost`

### Production Deployment

```bash
# 1. Configure your domain
export DOMAIN=mail.yourdomain.com

# 2. Update .env with production values
vim .env

# 3. Deploy
./scripts/deploy.sh

# 4. Configure DNS records (see DNS Setup section)
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DOMAIN` | Your mail domain | `localhost` |
| `POSTGRES_PASSWORD` | Database password | (generated) |
| `JWT_SECRET` | JWT signing key | (generated) |
| `DKIM_SELECTOR` | DKIM selector | `default` |

See `.env.example` for all available options.

### DNS Setup

For your domain to send/receive emails, add these DNS records:

```
# MX Record
yourdomain.com.    MX    10    mail.yourdomain.com.

# SPF Record
yourdomain.com.    TXT   "v=spf1 mx a ip4:YOUR_SERVER_IP ~all"

# DKIM Record (get from admin panel)
default._domainkey.yourdomain.com.  TXT  "v=DKIM1; k=rsa; p=YOUR_PUBLIC_KEY"

# DMARC Record
_dmarc.yourdomain.com.  TXT  "v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com"
```

## 📁 Project Structure

```
openmail-platform/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Config, security
│   │   ├── db/             # Database
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   └── Dockerfile
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # Pages (App Router)
│   │   ├── components/    # React components
│   │   ├── lib/           # API client
│   │   └── stores/        # Zustand stores
│   └── Dockerfile
├── mailserver/            # Mail server configs
│   ├── postfix/           # SMTP (Postfix)
│   └── dovecot/           # IMAP/POP3 (Dovecot)
├── nginx/                 # Reverse proxy
├── monitoring/            # Prometheus + Grafana
├── database/              # SQL schemas
├── scripts/               # Deployment scripts
└── docker-compose.yml
```

## 🛠️ API Documentation

Once running, access the API documentation at:
- Swagger UI: `https://localhost/api/docs`
- ReDoc: `https://localhost/api/redoc`

### Key Endpoints

```
POST   /api/v1/auth/login       # Login
POST   /api/v1/auth/register    # Register
GET    /api/v1/emails           # List emails
POST   /api/v1/emails           # Send email
GET    /api/v1/emails/{id}      # Get email
DELETE /api/v1/emails/{id}      # Delete email
GET    /api/v1/folders          # List folders
GET    /api/v1/labels           # List labels
GET    /api/v1/domains          # List domains
```

## 📊 Monitoring

### Grafana Dashboards
Access Grafana at `http://localhost:3001` (admin/admin by default)

Pre-configured dashboards:
- OpenMail Overview
- API Performance
- Mail Server Metrics
- Database Health

### Prometheus Metrics
Access Prometheus at `http://localhost:9090`

Key metrics:
- `http_requests_total` - API request count
- `http_request_duration_seconds` - API latency
- `postfix_queue_size` - Mail queue size
- `dovecot_auth_success_total` - IMAP auth stats

## 🔒 Security Considerations

1. **Change default passwords** in `.env`
2. **Enable TLS** for all external connections
3. **Configure firewall** rules appropriately
4. **Set up fail2ban** for brute-force protection
5. **Regular backups** using `./scripts/backup.sh`
6. **Keep updated** with security patches

## 📝 Development

```bash
# Backend development
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend development
cd frontend
npm install
npm run dev

# Run tests
cd backend
pytest

cd frontend
npm test
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [Postfix](http://www.postfix.org/)
- [Dovecot](https://dovecot.org/)
- [TailwindCSS](https://tailwindcss.com/)

---

Made with ❤️ by OpenMail Team
