# OpenMail Platform - Database Schema

## 1. Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   domains   │───────│    users    │───────│  mailboxes  │
└─────────────┘       └─────────────┘       └─────────────┘
      │                     │                      │
      │                     │                      │
      ▼                     ▼                      ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ dns_records │       │  sessions   │       │   emails    │
└─────────────┘       └─────────────┘       └─────────────┘
                                                   │
                            ┌──────────────────────┼──────────────────────┐
                            │                      │                      │
                            ▼                      ▼                      ▼
                      ┌───────────┐         ┌───────────┐         ┌───────────┐
                      │attachments│         │  labels   │         │email_labels│
                      └───────────┘         └───────────┘         └───────────┘
```

## 2. Table Definitions

### 2.1 Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    avatar_url VARCHAR(500),
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    
    -- Settings (JSON)
    settings JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    
    -- Security
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMPTZ,
    
    -- Indexes
    CONSTRAINT users_email_idx UNIQUE (email)
);

CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);
```

### 2.2 Domains Table
```sql
CREATE TABLE domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Verification
    is_verified BOOLEAN DEFAULT false,
    verification_token VARCHAR(100),
    verified_at TIMESTAMPTZ,
    
    -- DKIM
    dkim_selector VARCHAR(50) DEFAULT 'mail',
    dkim_private_key TEXT,
    dkim_public_key TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT domains_name_idx UNIQUE (name)
);

CREATE INDEX idx_domains_owner ON domains(owner_id);
CREATE INDEX idx_domains_verified ON domains(is_verified);
```

### 2.3 DNS Records Table
```sql
CREATE TABLE dns_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID REFERENCES domains(id) ON DELETE CASCADE,
    
    record_type VARCHAR(10) NOT NULL CHECK (record_type IN ('MX', 'TXT', 'CNAME', 'A', 'AAAA')),
    name VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    priority INT,
    ttl INT DEFAULT 3600,
    
    -- For verification
    purpose VARCHAR(50) CHECK (purpose IN ('mx', 'spf', 'dkim', 'dmarc', 'verification')),
    is_verified BOOLEAN DEFAULT false,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_dns_domain ON dns_records(domain_id);
CREATE INDEX idx_dns_type ON dns_records(record_type);
```

### 2.4 Mailboxes Table
```sql
CREATE TABLE mailboxes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    domain_id UUID REFERENCES domains(id) ON DELETE CASCADE,
    
    local_part VARCHAR(64) NOT NULL,  -- part before @
    full_address VARCHAR(255) NOT NULL UNIQUE,
    
    -- Quotas
    quota_bytes BIGINT DEFAULT 5368709120,  -- 5GB default
    used_bytes BIGINT DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_primary BOOLEAN DEFAULT false,
    
    -- Auto-reply
    auto_reply_enabled BOOLEAN DEFAULT false,
    auto_reply_subject VARCHAR(255),
    auto_reply_body TEXT,
    auto_reply_start TIMESTAMPTZ,
    auto_reply_end TIMESTAMPTZ,
    
    -- Forwarding
    forward_to VARCHAR(255)[],
    forward_keep_copy BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT mailboxes_address_idx UNIQUE (full_address),
    CONSTRAINT mailboxes_domain_local UNIQUE (domain_id, local_part)
);

CREATE INDEX idx_mailboxes_user ON mailboxes(user_id);
CREATE INDEX idx_mailboxes_domain ON mailboxes(domain_id);
```

### 2.5 Folders Table
```sql
CREATE TABLE folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mailbox_id UUID REFERENCES mailboxes(id) ON DELETE CASCADE,
    
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) DEFAULT 'custom' CHECK (type IN ('inbox', 'sent', 'drafts', 'spam', 'trash', 'starred', 'custom')),
    
    parent_id UUID REFERENCES folders(id) ON DELETE CASCADE,
    
    -- Counts (cached)
    total_count INT DEFAULT 0,
    unread_count INT DEFAULT 0,
    
    -- Display
    color VARCHAR(7),  -- hex color
    icon VARCHAR(50),
    sort_order INT DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT folders_mailbox_name UNIQUE (mailbox_id, name, parent_id)
);

CREATE INDEX idx_folders_mailbox ON folders(mailbox_id);
CREATE INDEX idx_folders_type ON folders(type);
```

### 2.6 Labels Table
```sql
CREATE TABLE labels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mailbox_id UUID REFERENCES mailboxes(id) ON DELETE CASCADE,
    
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) DEFAULT '#808080',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT labels_mailbox_name UNIQUE (mailbox_id, name)
);

CREATE INDEX idx_labels_mailbox ON labels(mailbox_id);
```

### 2.7 Emails Table
```sql
CREATE TABLE emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mailbox_id UUID REFERENCES mailboxes(id) ON DELETE CASCADE,
    folder_id UUID REFERENCES folders(id) ON DELETE SET NULL,
    
    -- Message ID (RFC 5322)
    message_id VARCHAR(500) UNIQUE,
    
    -- Threading
    thread_id UUID,
    in_reply_to VARCHAR(500),
    references TEXT[],
    
    -- Envelope
    from_address VARCHAR(255) NOT NULL,
    from_name VARCHAR(255),
    to_addresses JSONB NOT NULL DEFAULT '[]',
    cc_addresses JSONB DEFAULT '[]',
    bcc_addresses JSONB DEFAULT '[]',
    reply_to VARCHAR(255),
    
    -- Content
    subject VARCHAR(1000),
    body_text TEXT,
    body_html TEXT,
    snippet VARCHAR(500),  -- Preview text
    
    -- Storage
    raw_message_path VARCHAR(500),  -- Path in MinIO
    maildir_path VARCHAR(500),      -- Path in Maildir
    size_bytes INT DEFAULT 0,
    
    -- Flags
    is_read BOOLEAN DEFAULT false,
    is_starred BOOLEAN DEFAULT false,
    is_draft BOOLEAN DEFAULT false,
    is_sent BOOLEAN DEFAULT false,
    is_spam BOOLEAN DEFAULT false,
    is_trash BOOLEAN DEFAULT false,
    
    -- Spam
    spam_score FLOAT DEFAULT 0,
    spam_report TEXT,
    
    -- Security
    has_dkim BOOLEAN,
    has_spf BOOLEAN,
    dkim_result VARCHAR(20),
    spf_result VARCHAR(20),
    dmarc_result VARCHAR(20),
    
    -- Timestamps
    date TIMESTAMPTZ NOT NULL,  -- From email Date header
    received_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ  -- Soft delete
);

CREATE INDEX idx_emails_mailbox ON emails(mailbox_id);
CREATE INDEX idx_emails_folder ON emails(folder_id);
CREATE INDEX idx_emails_thread ON emails(thread_id);
CREATE INDEX idx_emails_date ON emails(date DESC);
CREATE INDEX idx_emails_from ON emails(from_address);
CREATE INDEX idx_emails_read ON emails(mailbox_id, is_read);
CREATE INDEX idx_emails_starred ON emails(mailbox_id, is_starred);
CREATE INDEX idx_emails_spam ON emails(is_spam);
CREATE INDEX idx_emails_message_id ON emails(message_id);

-- Full-text search index
CREATE INDEX idx_emails_fts ON emails USING GIN (
    to_tsvector('english', coalesce(subject, '') || ' ' || coalesce(body_text, ''))
);
```

### 2.8 Email Labels Junction Table
```sql
CREATE TABLE email_labels (
    email_id UUID REFERENCES emails(id) ON DELETE CASCADE,
    label_id UUID REFERENCES labels(id) ON DELETE CASCADE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (email_id, label_id)
);

CREATE INDEX idx_email_labels_email ON email_labels(email_id);
CREATE INDEX idx_email_labels_label ON email_labels(label_id);
```

### 2.9 Attachments Table
```sql
CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id UUID REFERENCES emails(id) ON DELETE CASCADE,
    
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100),
    size_bytes BIGINT NOT NULL,
    
    -- Storage
    storage_path VARCHAR(500) NOT NULL,  -- Path in MinIO
    storage_bucket VARCHAR(100) DEFAULT 'attachments',
    
    -- Metadata
    content_id VARCHAR(255),  -- For inline attachments
    is_inline BOOLEAN DEFAULT false,
    
    -- Checksum
    checksum_md5 VARCHAR(32),
    checksum_sha256 VARCHAR(64),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_attachments_email ON attachments(email_id);
CREATE INDEX idx_attachments_type ON attachments(content_type);
```

### 2.10 Sessions Table
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(token_hash);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
```

### 2.11 Email Filters Table
```sql
CREATE TABLE email_filters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mailbox_id UUID REFERENCES mailboxes(id) ON DELETE CASCADE,
    
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    priority INT DEFAULT 0,
    
    -- Conditions (JSON array)
    conditions JSONB NOT NULL,
    -- Example: [{"field": "from", "operator": "contains", "value": "@example.com"}]
    
    -- Actions (JSON array)
    actions JSONB NOT NULL,
    -- Example: [{"type": "move", "folder_id": "uuid"}, {"type": "label", "label_id": "uuid"}]
    
    -- Stop processing
    stop_processing BOOLEAN DEFAULT false,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_filters_mailbox ON email_filters(mailbox_id);
```

### 2.12 Audit Log Table
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);
```

## 3. Initial Data / Seeds

### 3.1 Default Folders (created per mailbox)
```sql
INSERT INTO folders (mailbox_id, name, type, sort_order) VALUES
(?, 'Inbox', 'inbox', 1),
(?, 'Sent', 'sent', 2),
(?, 'Drafts', 'drafts', 3),
(?, 'Spam', 'spam', 4),
(?, 'Trash', 'trash', 5),
(?, 'Starred', 'starred', 6);
```

## 4. Views

### 4.1 Mailbox Stats View
```sql
CREATE VIEW mailbox_stats AS
SELECT 
    m.id as mailbox_id,
    m.full_address,
    m.quota_bytes,
    m.used_bytes,
    COUNT(e.id) as total_emails,
    COUNT(e.id) FILTER (WHERE NOT e.is_read) as unread_count,
    COUNT(e.id) FILTER (WHERE e.is_spam) as spam_count,
    COUNT(e.id) FILTER (WHERE e.is_trash) as trash_count
FROM mailboxes m
LEFT JOIN emails e ON e.mailbox_id = m.id AND e.deleted_at IS NULL
GROUP BY m.id;
```

## 5. Functions

### 5.1 Update Folder Counts
```sql
CREATE OR REPLACE FUNCTION update_folder_counts()
RETURNS TRIGGER AS $$
BEGIN
    -- Update old folder counts
    IF OLD.folder_id IS NOT NULL THEN
        UPDATE folders SET
            total_count = (SELECT COUNT(*) FROM emails WHERE folder_id = OLD.folder_id AND deleted_at IS NULL),
            unread_count = (SELECT COUNT(*) FROM emails WHERE folder_id = OLD.folder_id AND NOT is_read AND deleted_at IS NULL)
        WHERE id = OLD.folder_id;
    END IF;
    
    -- Update new folder counts
    IF NEW.folder_id IS NOT NULL THEN
        UPDATE folders SET
            total_count = (SELECT COUNT(*) FROM emails WHERE folder_id = NEW.folder_id AND deleted_at IS NULL),
            unread_count = (SELECT COUNT(*) FROM emails WHERE folder_id = NEW.folder_id AND NOT is_read AND deleted_at IS NULL)
        WHERE id = NEW.folder_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_folder_counts
AFTER INSERT OR UPDATE OF folder_id, is_read, deleted_at ON emails
FOR EACH ROW EXECUTE FUNCTION update_folder_counts();
```

### 5.2 Update Mailbox Used Bytes
```sql
CREATE OR REPLACE FUNCTION update_mailbox_usage()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE mailboxes SET
        used_bytes = (SELECT COALESCE(SUM(size_bytes), 0) FROM emails WHERE mailbox_id = COALESCE(NEW.mailbox_id, OLD.mailbox_id) AND deleted_at IS NULL)
    WHERE id = COALESCE(NEW.mailbox_id, OLD.mailbox_id);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_mailbox_usage
AFTER INSERT OR UPDATE OR DELETE ON emails
FOR EACH ROW EXECUTE FUNCTION update_mailbox_usage();
```
