# OpenMail Platform - System Architecture

## 1. Executive Summary

OpenMail is a production-grade, self-hosted email platform providing Gmail-like functionality for businesses and individuals. It supports custom domains, SMTP/IMAP protocols, webmail interface, and enterprise security features.

## 2. System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INTERNET                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
              ┌─────────┐    ┌─────────┐    ┌─────────┐
              │ Port 25 │    │Port 443 │    │Port 993 │
              │  SMTP   │    │ HTTPS   │    │  IMAPS  │
              └────┬────┘    └────┬────┘    └────┬────┘
                   │              │              │
┌──────────────────┼──────────────┼──────────────┼──────────────────────────┐
│                  │     NGINX REVERSE PROXY     │                          │
│                  │              │              │                          │
│   ┌──────────────▼──────┐  ┌───▼────┐  ┌─────▼──────┐                   │
│   │      POSTFIX        │  │FRONTEND│  │  DOVECOT   │                   │
│   │    SMTP Server      │  │Next.js │  │IMAP Server │                   │
│   │   (Send/Receive)    │  │        │  │            │                   │
│   └──────────┬──────────┘  └───┬────┘  └─────┬──────┘                   │
│              │                 │              │                          │
│              │         ┌───────▼───────┐     │                          │
│              │         │   BACKEND     │     │                          │
│              └────────►│   FastAPI     │◄────┘                          │
│                        │   REST API    │                                 │
│                        └───────┬───────┘                                 │
│                                │                                         │
│         ┌──────────────────────┼──────────────────────┐                 │
│         │                      │                      │                 │
│    ┌────▼────┐           ┌─────▼─────┐         ┌─────▼─────┐           │
│    │PostgreSQL│           │   Redis   │         │   MinIO   │           │
│    │ Database │           │   Cache   │         │  Storage  │           │
│    └──────────┘           └───────────┘         └───────────┘           │
│                                                                          │
│    ┌────────────┐    ┌─────────────┐    ┌─────────────────┐            │
│    │SpamAssassin│    │Elasticsearch│    │  Celery Workers │            │
│    │   Filter   │    │   Search    │    │  (Background)   │            │
│    └────────────┘    └─────────────┘    └─────────────────┘            │
│                                                                          │
│                         DOCKER NETWORK                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

## 3. Component Architecture

### 3.1 Frontend (Webmail Client)
- **Technology:** Next.js 14 + TypeScript + TailwindCSS
- **Features:**
  - Inbox, Sent, Drafts, Spam, Trash, Starred
  - Labels and folders management
  - Email composition with rich text editor
  - Attachments (drag & drop)
  - Email threading/conversation view
  - Real-time notifications (WebSocket)
  - Search with filters
  - Dark/Light mode
  - Mobile responsive
  - Multiple account support

### 3.2 Backend API
- **Technology:** Python FastAPI
- **Features:**
  - RESTful API
  - JWT Authentication
  - Rate limiting
  - Email CRUD operations
  - Domain management
  - User management
  - Attachment handling
  - Search integration

### 3.3 Mail Server
- **SMTP:** Postfix
  - Handles sending and receiving
  - TLS encryption
  - DKIM signing
  - SPF/DMARC validation
- **IMAP/POP3:** Dovecot
  - Mailbox access
  - Folder management
  - IDLE push notifications

### 3.4 Database Layer
- **PostgreSQL:** Primary data store
  - Users, domains, mailboxes
  - Email metadata
  - Settings and preferences
- **Redis:** Caching and sessions
  - Session management
  - Rate limiting counters
  - Queue management
- **Elasticsearch:** Search engine
  - Full-text email search
  - Filters and facets

### 3.5 Storage Layer
- **MinIO (S3-compatible):**
  - Email attachments
  - Large email bodies
- **Maildir:** Local mail storage
  - `/var/mail/vhosts/{domain}/{user}/`

### 3.6 Security Layer
- **Authentication:**
  - JWT tokens
  - bcrypt password hashing
  - OAuth2 support (optional)
- **Email Security:**
  - DKIM signing
  - SPF validation
  - DMARC enforcement
- **Infrastructure:**
  - TLS everywhere
  - Fail2ban
  - Rate limiting

## 4. Data Flow

### 4.1 Sending Email
```
User → Frontend → Backend API → Postfix → Internet → Recipient MX
                      │
                      ├── Store in PostgreSQL (metadata)
                      ├── Store in MinIO (attachments)
                      └── Queue via Celery
```

### 4.2 Receiving Email
```
Internet → MX Record → Postfix → SpamAssassin → Dovecot → Maildir
                                      │
                                      ├── Index in Elasticsearch
                                      ├── Store metadata in PostgreSQL
                                      └── Notify via WebSocket
```

### 4.3 Reading Email (Webmail)
```
User → Frontend → Backend API → PostgreSQL (metadata)
                      │              │
                      │              └── Elasticsearch (search)
                      │
                      └── MinIO (attachments)
```

### 4.4 Reading Email (IMAP Client)
```
User → Email Client → Dovecot → Maildir
                         │
                         └── PostgreSQL (auth)
```

## 5. API Architecture

### 5.1 REST Endpoints

```
/api/v1/
├── auth/
│   ├── POST   /register
│   ├── POST   /login
│   ├── POST   /logout
│   ├── POST   /refresh
│   └── POST   /forgot-password
│
├── users/
│   ├── GET    /me
│   ├── PUT    /me
│   ├── PUT    /me/password
│   └── PUT    /me/settings
│
├── emails/
│   ├── GET    /                    # List emails (inbox)
│   ├── GET    /{id}                # Get email
│   ├── POST   /                    # Send email
│   ├── PUT    /{id}                # Update (labels, read)
│   ├── DELETE /{id}                # Delete/trash
│   ├── POST   /{id}/reply
│   ├── POST   /{id}/forward
│   └── GET    /search
│
├── folders/
│   ├── GET    /                    # List folders
│   ├── POST   /                    # Create folder
│   ├── PUT    /{id}
│   └── DELETE /{id}
│
├── labels/
│   ├── GET    /
│   ├── POST   /
│   ├── PUT    /{id}
│   └── DELETE /{id}
│
├── attachments/
│   ├── POST   /upload
│   └── GET    /{id}/download
│
├── domains/
│   ├── GET    /
│   ├── POST   /
│   ├── GET    /{id}/verify
│   ├── GET    /{id}/dns-records
│   └── DELETE /{id}
│
└── admin/
    ├── GET    /users
    ├── GET    /domains
    ├── GET    /stats
    └── GET    /logs
```

## 6. Security Architecture

### 6.1 Authentication Flow
```
┌────────┐     ┌─────────┐     ┌──────────┐
│ Client │────►│ Backend │────►│PostgreSQL│
└────────┘     └─────────┘     └──────────┘
     │              │
     │   JWT Token  │
     │◄─────────────┤
     │              │
     │   API Calls  │
     │─────────────►│
     │  (with JWT)  │
```

### 6.2 Email Security
```
Outgoing: User → Backend → Postfix (DKIM Sign) → Internet
Incoming: Internet → Postfix → SpamAssassin → DKIM/SPF Check → Deliver
```

### 6.3 TLS Configuration
- All external connections require TLS
- Internal connections use TLS where possible
- Certificates: Let's Encrypt (auto-renewal)

## 7. Deployment Architecture

### 7.1 Docker Services
```yaml
services:
  - frontend        # Next.js (port 3000)
  - backend         # FastAPI (port 8000)
  - postfix         # SMTP (ports 25, 587, 465)
  - dovecot         # IMAP (ports 143, 993)
  - postgres        # Database (port 5432)
  - redis           # Cache (port 6379)
  - elasticsearch   # Search (port 9200)
  - minio           # Storage (port 9000)
  - spamassassin    # Spam filter
  - celery          # Background workers
  - nginx           # Reverse proxy (ports 80, 443)
```

### 7.2 Volume Mounts
```
./data/postgres     → /var/lib/postgresql/data
./data/mail         → /var/mail/vhosts
./data/minio        → /data
./data/elasticsearch → /usr/share/elasticsearch/data
./certs             → /etc/ssl/certs
./config            → /etc/postfix, /etc/dovecot
```

## 8. Scaling Strategy

### 8.1 Horizontal Scaling
- **Frontend:** Multiple containers behind load balancer
- **Backend:** Multiple containers with shared session (Redis)
- **Postfix:** Multiple MX records pointing to different servers
- **Dovecot:** Shared storage (NFS/GlusterFS) or director proxy

### 8.2 Vertical Scaling
- PostgreSQL: Increase resources, add read replicas
- Elasticsearch: Add nodes to cluster
- Redis: Redis Cluster for high availability

## 9. Monitoring & Logging

### 9.1 Metrics (Prometheus)
- Email send/receive rates
- Queue depths
- Error rates
- Response times
- Resource utilization

### 9.2 Logging (ELK Stack)
- Application logs
- Mail server logs
- Access logs
- Security events

### 9.3 Alerting
- Failed deliveries
- High spam rates
- Authentication failures
- Resource exhaustion

## 10. Technology Stack Summary

| Component | Technology | Version |
|-----------|------------|---------|
| Frontend | Next.js | 14.x |
| Backend | FastAPI | 0.109+ |
| Database | PostgreSQL | 16 |
| Cache | Redis | 7 |
| Search | Elasticsearch | 8.x |
| SMTP | Postfix | 3.8 |
| IMAP | Dovecot | 2.3 |
| Storage | MinIO | Latest |
| Spam | SpamAssassin | 4.0 |
| Proxy | NGINX | 1.25 |
| Container | Docker | 24+ |
| Orchestration | Docker Compose | 2.x |
