# 🗄️ OpenMail Platform - Database Schema Documentation

**Version:** 1.0  
**Database:** PostgreSQL 15+  
**ORM:** SQLAlchemy 2.0  
**Last Updated:** 2026-02-26

---

## 📋 Table of Contents

1. [Overview](#1-overview)
2. [Entity Relationship Diagram](#2-entity-relationship-diagram)
3. [Table Definitions](#3-table-definitions)
4. [Relationships](#4-relationships)
5. [Indexes](#5-indexes)
6. [Constraints](#6-constraints)
7. [Migrations](#7-migrations)
8. [Performance Optimization](#8-performance-optimization)

---

## 1. Overview

### Database Statistics

| Metric | Value |
|--------|-------|
| Total Tables | 13 |
| Primary Tables | 8 |
| Junction Tables | 1 |
| System Tables | 4 |
| Enum Types | 1 |
| Total Indexes | 25+ |

### Core Entities

| Entity | Table | Description |
|--------|-------|-------------|
| User | `users` | User accounts and authentication |
| Domain | `domains` | Custom email domains |
| Mailbox | `mailboxes` | Email addresses |
| Folder | `folders` | Email organization |
| Email | `emails` | Email messages |
| Label | `labels` | Email tags/categories |
| Attachment | `attachments` | File attachments |
| Contact | `contacts` | Address book |

---

## 2. Entity Relationship Diagram

```
                                    ┌─────────────────┐
                                    │     USERS       │
                                    ├─────────────────┤
                                    │ id (PK)         │
                                    │ email           │
                                    │ password_hash   │
                                    │ first_name      │
                                    │ last_name       │
                                    │ role            │
                                    │ is_active       │
                                    │ settings        │
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
                    ▼                        ▼                        ▼
           ┌────────────────┐      ┌────────────────┐      ┌────────────────┐
           │    DOMAINS     │      │    SESSIONS    │      │  VERIFICATION  │
           ├────────────────┤      ├────────────────┤      │    TOKENS      │
           │ id (PK)        │      │ id (PK)        │      ├────────────────┤
           │ owner_id (FK)  │◄─────│ user_id (FK)   │      │ id (PK)        │
           │ name           │      │ token_hash     │      │ user_id (FK)   │
           │ is_verified    │      │ expires_at     │      │ token          │
           │ dkim_keys      │      │ ip_address     │      │ token_type     │
           └───────┬────────┘      └────────────────┘      │ expires_at     │
                   │                                        └────────────────┘
                   │
                   ▼
           ┌────────────────┐
           │   MAILBOXES    │
           ├────────────────┤
           │ id (PK)        │
           │ user_id (FK)   │◄──────────────────────────────┐
           │ domain_id (FK) │                               │
           │ local_part     │                               │
           │ full_address   │                               │
           │ quota_bytes    │                               │
           │ forward_to     │                               │
           └───────┬────────┘                               │
                   │                                        │
      ┌────────────┼────────────┬──────────────┐           │
      │            │            │              │           │
      ▼            ▼            ▼              ▼           │
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│  FOLDERS  │ │  LABELS   │ │  FILTERS  │ │ CONTACTS  │   │
├───────────┤ ├───────────┤ ├───────────┤ ├───────────┤   │
│ id (PK)   │ │ id (PK)   │ │ id (PK)   │ │ id (PK)   │   │
│ mailbox_id│ │ mailbox_id│ │ mailbox_id│ │ user_id   │───┘
│ name      │ │ name      │ │ name      │ │ email     │
│ type      │ │ color     │ │ conditions│ │ name      │
│ parent_id │ └─────┬─────┘ │ actions   │ │ phone     │
└─────┬─────┘       │       └───────────┘ └───────────┘
      │             │
      │             │              ┌─────────────────┐
      │             │              │   EMAIL_LABELS  │
      │             │              │   (Junction)    │
      │             │              ├─────────────────┤
      │             └──────────────│ label_id (FK)   │
      │                            │ email_id (FK)   │
      │                            └────────┬────────┘
      │                                     │
      ▼                                     │
┌─────────────────────────────────────────────────────┐
│                      EMAILS                          │
├─────────────────────────────────────────────────────┤
│ id (PK)                                             │
│ mailbox_id (FK)                                     │
│ folder_id (FK)  ◄───────────────────────────────────┘
│ message_id                                          │
│ thread_id                                           │
│ from_address, from_name                             │
│ to_addresses (JSON), cc_addresses, bcc_addresses   │
│ subject                                             │
│ body_text, body_html, snippet                       │
│ is_read, is_starred, is_draft, is_spam             │
│ spam_score, dkim_result, spf_result                │
│ date, received_at                                   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  ATTACHMENTS   │
              ├────────────────┤
              │ id (PK)        │
              │ email_id (FK)  │
              │ filename       │
              │ content_type   │
              │ size_bytes     │
              │ storage_path   │
              │ checksum       │
              └────────────────┘
```

---

## 3. Table Definitions

### 3.1 Users Table

Stores user account information and authentication data.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role user_role DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    avatar_url VARCHAR(500),
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMPTZ
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Primary key |
| email | VARCHAR(255) | No | Unique login email |
| password_hash | VARCHAR(255) | No | Bcrypt password hash |
| first_name | VARCHAR(100) | Yes | User's first name |
| last_name | VARCHAR(100) | Yes | User's last name |
| role | ENUM | No | admin or user |
| is_active | BOOLEAN | No | Account active status |
| is_verified | BOOLEAN | No | Email verified |
| avatar_url | VARCHAR(500) | Yes | Profile picture URL |
| timezone | VARCHAR(50) | No | User timezone |
| language | VARCHAR(10) | No | Preferred language |
| settings | JSONB | No | User preferences |
| created_at | TIMESTAMPTZ | No | Account creation |
| updated_at | TIMESTAMPTZ | No | Last update |
| last_login_at | TIMESTAMPTZ | Yes | Last login time |
| failed_login_attempts | INT | No | Failed logins |
| locked_until | TIMESTAMPTZ | Yes | Lockout end time |

### 3.2 Domains Table

Custom email domains owned by users.

```sql
CREATE TABLE domains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    is_verified BOOLEAN DEFAULT false,
    verification_token VARCHAR(100),
    verified_at TIMESTAMPTZ,
    dkim_selector VARCHAR(50) DEFAULT 'mail',
    dkim_private_key TEXT,
    dkim_public_key TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Primary key |
| name | VARCHAR(255) | No | Domain name (unique) |
| owner_id | UUID | Yes | Owner user FK |
| is_verified | BOOLEAN | No | DNS verified |
| verification_token | VARCHAR(100) | Yes | DNS TXT token |
| verified_at | TIMESTAMPTZ | Yes | Verification time |
| dkim_selector | VARCHAR(50) | No | DKIM selector |
| dkim_private_key | TEXT | Yes | DKIM private key |
| dkim_public_key | TEXT | Yes | DKIM public key |
| is_active | BOOLEAN | No | Domain active |

### 3.3 Mailboxes Table

Email addresses/mailboxes for users.

```sql
CREATE TABLE mailboxes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    domain_id UUID REFERENCES domains(id) ON DELETE CASCADE,
    local_part VARCHAR(64) NOT NULL,
    full_address VARCHAR(255) UNIQUE NOT NULL,
    quota_bytes BIGINT DEFAULT 5368709120,
    used_bytes BIGINT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    is_primary BOOLEAN DEFAULT false,
    auto_reply_enabled BOOLEAN DEFAULT false,
    auto_reply_subject VARCHAR(255),
    auto_reply_body TEXT,
    auto_reply_start TIMESTAMPTZ,
    auto_reply_end TIMESTAMPTZ,
    forward_to VARCHAR(255)[],
    forward_keep_copy BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(domain_id, local_part)
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Primary key |
| user_id | UUID | Yes | Owner user FK |
| domain_id | UUID | Yes | Domain FK |
| local_part | VARCHAR(64) | No | Local part (before @) |
| full_address | VARCHAR(255) | No | Full email address |
| quota_bytes | BIGINT | No | Storage quota (default 5GB) |
| used_bytes | BIGINT | No | Used storage |
| is_active | BOOLEAN | No | Mailbox active |
| is_primary | BOOLEAN | No | Primary mailbox |
| auto_reply_enabled | BOOLEAN | No | Vacation responder |
| forward_to | VARCHAR[] | Yes | Forwarding addresses |

### 3.4 Folders Table

Email folders for organization.

```sql
CREATE TABLE folders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mailbox_id UUID REFERENCES mailboxes(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) DEFAULT 'custom',
    parent_id UUID REFERENCES folders(id) ON DELETE CASCADE,
    total_count INT DEFAULT 0,
    unread_count INT DEFAULT 0,
    color VARCHAR(7),
    icon VARCHAR(50),
    sort_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Primary key |
| mailbox_id | UUID | Yes | Parent mailbox FK |
| name | VARCHAR(100) | No | Folder name |
| type | VARCHAR(20) | No | inbox/sent/drafts/spam/trash/custom |
| parent_id | UUID | Yes | Parent folder (nested) |
| total_count | INT | No | Email count cache |
| unread_count | INT | No | Unread count cache |
| color | VARCHAR(7) | Yes | Hex color code |
| sort_order | INT | No | Display order |

### 3.5 Emails Table

The main email storage table.

```sql
CREATE TABLE emails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mailbox_id UUID REFERENCES mailboxes(id) ON DELETE CASCADE,
    folder_id UUID REFERENCES folders(id) ON DELETE SET NULL,
    message_id VARCHAR(500) UNIQUE,
    thread_id UUID,
    in_reply_to VARCHAR(500),
    "references" TEXT[],
    from_address VARCHAR(255) NOT NULL,
    from_name VARCHAR(255),
    to_addresses JSONB NOT NULL DEFAULT '[]',
    cc_addresses JSONB DEFAULT '[]',
    bcc_addresses JSONB DEFAULT '[]',
    reply_to VARCHAR(255),
    subject VARCHAR(1000),
    body_text TEXT,
    body_html TEXT,
    snippet VARCHAR(500),
    raw_message_path VARCHAR(500),
    maildir_path VARCHAR(500),
    size_bytes INT DEFAULT 0,
    is_read BOOLEAN DEFAULT false,
    is_starred BOOLEAN DEFAULT false,
    is_draft BOOLEAN DEFAULT false,
    is_sent BOOLEAN DEFAULT false,
    is_spam BOOLEAN DEFAULT false,
    is_trash BOOLEAN DEFAULT false,
    spam_score FLOAT DEFAULT 0,
    spam_report TEXT,
    has_dkim BOOLEAN,
    has_spf BOOLEAN,
    dkim_result VARCHAR(20),
    spf_result VARCHAR(20),
    dmarc_result VARCHAR(20),
    date TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | No | Primary key |
| mailbox_id | UUID | Yes | Parent mailbox FK |
| folder_id | UUID | Yes | Current folder FK |
| message_id | VARCHAR(500) | Yes | RFC 5322 Message-ID |
| thread_id | UUID | Yes | Thread grouping |
| in_reply_to | VARCHAR(500) | Yes | Reply reference |
| from_address | VARCHAR(255) | No | Sender email |
| from_name | VARCHAR(255) | Yes | Sender display name |
| to_addresses | JSONB | No | Recipients array |
| cc_addresses | JSONB | No | CC recipients |
| bcc_addresses | JSONB | No | BCC recipients |
| subject | VARCHAR(1000) | Yes | Email subject |
| body_text | TEXT | Yes | Plain text body |
| body_html | TEXT | Yes | HTML body |
| snippet | VARCHAR(500) | Yes | Preview text |
| size_bytes | INT | No | Email size |
| is_read | BOOLEAN | No | Read status |
| is_starred | BOOLEAN | No | Starred flag |
| is_draft | BOOLEAN | No | Draft status |
| is_spam | BOOLEAN | No | Spam flag |
| spam_score | FLOAT | No | SpamAssassin score |
| date | TIMESTAMPTZ | No | Email date |

### 3.6 Labels Table

Email labels/tags for categorization.

```sql
CREATE TABLE labels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mailbox_id UUID REFERENCES mailboxes(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) DEFAULT '#808080',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(mailbox_id, name)
);
```

### 3.7 Email Labels Junction Table

Many-to-many relationship between emails and labels.

```sql
CREATE TABLE email_labels (
    email_id UUID REFERENCES emails(id) ON DELETE CASCADE,
    label_id UUID REFERENCES labels(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (email_id, label_id)
);
```

### 3.8 Attachments Table

File attachments for emails.

```sql
CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id UUID REFERENCES emails(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100),
    size_bytes BIGINT NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    storage_bucket VARCHAR(100) DEFAULT 'attachments',
    content_id VARCHAR(255),
    is_inline BOOLEAN DEFAULT false,
    checksum_md5 VARCHAR(32),
    checksum_sha256 VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.9 Sessions Table

User session management.

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    refresh_token_hash VARCHAR(255),
    device_info VARCHAR(500),
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    refresh_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.10 Email Filters Table

User-defined email filter rules.

```sql
CREATE TABLE email_filters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mailbox_id UUID REFERENCES mailboxes(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    priority INT DEFAULT 0,
    conditions JSONB NOT NULL,
    actions JSONB NOT NULL,
    stop_processing BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Conditions JSON Format:**
```json
[
    {"field": "from", "operator": "contains", "value": "@company.com"},
    {"field": "subject", "operator": "matches", "value": "urgent*"}
]
```

**Actions JSON Format:**
```json
[
    {"type": "move", "folder_id": "uuid"},
    {"type": "label", "label_id": "uuid"},
    {"type": "star", "value": true},
    {"type": "mark_read", "value": true}
]
```

---

## 4. Relationships

### One-to-Many Relationships

| Parent | Child | Foreign Key |
|--------|-------|-------------|
| users | domains | domains.owner_id |
| users | mailboxes | mailboxes.user_id |
| users | sessions | sessions.user_id |
| domains | mailboxes | mailboxes.domain_id |
| mailboxes | folders | folders.mailbox_id |
| mailboxes | labels | labels.mailbox_id |
| mailboxes | emails | emails.mailbox_id |
| mailboxes | filters | email_filters.mailbox_id |
| folders | emails | emails.folder_id |
| folders | folders | folders.parent_id (self-ref) |
| emails | attachments | attachments.email_id |

### Many-to-Many Relationships

| Table 1 | Table 2 | Junction Table |
|---------|---------|----------------|
| emails | labels | email_labels |

---

## 5. Indexes

### Primary Indexes

```sql
-- Users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Domains
CREATE INDEX idx_domains_owner ON domains(owner_id);
CREATE INDEX idx_domains_name ON domains(name);

-- Mailboxes
CREATE INDEX idx_mailboxes_user ON mailboxes(user_id);
CREATE INDEX idx_mailboxes_address ON mailboxes(full_address);

-- Folders
CREATE INDEX idx_folders_mailbox ON folders(mailbox_id);

-- Emails (Critical for performance)
CREATE INDEX idx_emails_mailbox ON emails(mailbox_id);
CREATE INDEX idx_emails_folder ON emails(folder_id);
CREATE INDEX idx_emails_thread ON emails(thread_id);
CREATE INDEX idx_emails_date ON emails(date DESC);
CREATE INDEX idx_emails_read ON emails(mailbox_id, is_read);
CREATE INDEX idx_emails_starred ON emails(mailbox_id, is_starred);

-- Sessions
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(token_hash);

-- Attachments
CREATE INDEX idx_attachments_email ON attachments(email_id);
```

### Composite Indexes

```sql
-- Optimized for inbox queries
CREATE INDEX idx_emails_mailbox_date ON emails(mailbox_id, date DESC);

-- Optimized for folder + unread queries  
CREATE INDEX idx_emails_folder_unread ON emails(folder_id, is_read) WHERE is_read = false;

-- Optimized for search
CREATE INDEX idx_emails_from ON emails(from_address);
```

---

## 6. Constraints

### Unique Constraints

| Table | Columns | Description |
|-------|---------|-------------|
| users | email | Unique login |
| domains | name | Unique domain |
| mailboxes | full_address | Unique email address |
| mailboxes | (domain_id, local_part) | Unique per domain |
| labels | (mailbox_id, name) | Unique per mailbox |
| emails | message_id | RFC Message-ID |

### Foreign Key Constraints

All foreign keys use `ON DELETE CASCADE` except:
- `emails.folder_id` uses `ON DELETE SET NULL` (preserve email if folder deleted)

### Check Constraints

```sql
-- Ensure valid email quota
ALTER TABLE mailboxes ADD CONSTRAINT chk_quota 
    CHECK (quota_bytes >= 0 AND used_bytes >= 0);

-- Ensure valid spam score
ALTER TABLE emails ADD CONSTRAINT chk_spam_score 
    CHECK (spam_score >= 0 AND spam_score <= 100);
```

---

## 7. Migrations

### Using Alembic

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Show history
alembic history
```

### Initial Migration

Located at: `backend/alembic/versions/001_initial_schema.py`

---

## 8. Performance Optimization

### Query Optimization Tips

1. **Inbox Queries**
   ```sql
   -- Use covering index
   SELECT id, from_address, subject, date, is_read 
   FROM emails 
   WHERE mailbox_id = $1 AND folder_id = $2
   ORDER BY date DESC 
   LIMIT 50;
   ```

2. **Unread Count**
   ```sql
   -- Use partial index
   SELECT COUNT(*) FROM emails 
   WHERE mailbox_id = $1 AND is_read = false;
   ```

3. **Thread Loading**
   ```sql
   SELECT * FROM emails 
   WHERE thread_id = $1 
   ORDER BY date ASC;
   ```

### Maintenance

```sql
-- Vacuum analyze (run weekly)
VACUUM ANALYZE emails;
VACUUM ANALYZE attachments;

-- Reindex (run monthly)
REINDEX TABLE emails;
```

### Connection Pooling

Recommended settings:
- Pool size: 20
- Max overflow: 10
- Pool timeout: 30s
- Pool recycle: 1800s

---

*Database Schema Documentation v1.0*
*Generated by Chanakya 🧠*
