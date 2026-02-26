# OpenMail Platform - API Specification

## Base URL
```
Production: https://api.openmail.example.com/v1
Development: http://localhost:8000/api/v1
```

## Authentication
All API requests (except auth endpoints) require a JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

## Response Format
All responses follow this format:
```json
{
  "success": true,
  "data": { ... },
  "message": "Success message",
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 100,
    "total_pages": 2
  }
}
```

Error responses:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email address",
    "details": { ... }
  }
}
```

---

## 1. Authentication Endpoints

### POST /auth/register
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe"
    },
    "message": "Verification email sent"
  }
}
```

### POST /auth/login
Authenticate user and get tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "first_name": "John"
    }
  }
}
```

### POST /auth/refresh
Refresh access token.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

### POST /auth/logout
Logout and invalidate tokens.

### POST /auth/forgot-password
Request password reset.

**Request:**
```json
{
  "email": "user@example.com"
}
```

### POST /auth/reset-password
Reset password with token.

**Request:**
```json
{
  "token": "reset-token",
  "password": "NewSecurePass123!"
}
```

### POST /auth/verify-email
Verify email address.

**Request:**
```json
{
  "token": "verification-token"
}
```

---

## 2. User Endpoints

### GET /users/me
Get current user profile.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "avatar_url": "https://...",
    "timezone": "America/New_York",
    "language": "en",
    "settings": {
      "signature": "<p>Best regards,<br>John</p>",
      "notifications": true,
      "theme": "dark"
    },
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### PUT /users/me
Update user profile.

**Request:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "timezone": "America/New_York",
  "settings": {
    "signature": "<p>Updated signature</p>"
  }
}
```

### PUT /users/me/password
Change password.

**Request:**
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

### PUT /users/me/avatar
Upload avatar image.

**Request:** multipart/form-data
- `avatar`: Image file (max 5MB, jpg/png)

---

## 3. Mailbox Endpoints

### GET /mailboxes
List user's mailboxes.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "full_address": "john@example.com",
      "domain": "example.com",
      "is_primary": true,
      "quota_bytes": 5368709120,
      "used_bytes": 1073741824,
      "unread_count": 5
    }
  ]
}
```

### POST /mailboxes
Create a new mailbox (alias).

**Request:**
```json
{
  "local_part": "john.work",
  "domain_id": "domain-uuid"
}
```

### GET /mailboxes/{id}/stats
Get mailbox statistics.

---

## 4. Email Endpoints

### GET /emails
List emails with filters.

**Query Parameters:**
- `folder`: Folder ID or type (inbox, sent, drafts, spam, trash)
- `label`: Label ID
- `is_read`: true/false
- `is_starred`: true/false
- `from`: Filter by sender
- `to`: Filter by recipient
- `subject`: Search in subject
- `q`: Full-text search
- `date_from`: Start date (ISO 8601)
- `date_to`: End date (ISO 8601)
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 50, max: 100)
- `sort`: Sort field (date, from, subject)
- `order`: asc/desc (default: desc)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "thread_id": "thread-uuid",
      "from": {
        "address": "sender@example.com",
        "name": "Sender Name"
      },
      "to": [
        {"address": "me@example.com", "name": "Me"}
      ],
      "subject": "Hello World",
      "snippet": "This is the beginning of the email...",
      "date": "2024-01-15T10:30:00Z",
      "is_read": false,
      "is_starred": true,
      "has_attachments": true,
      "attachment_count": 2,
      "labels": [
        {"id": "uuid", "name": "Important", "color": "#ff0000"}
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 156,
    "total_pages": 4
  }
}
```

### GET /emails/{id}
Get single email with full content.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "thread_id": "thread-uuid",
    "message_id": "<uuid@example.com>",
    "from": {
      "address": "sender@example.com",
      "name": "Sender Name"
    },
    "to": [...],
    "cc": [...],
    "bcc": [...],
    "reply_to": "reply@example.com",
    "subject": "Hello World",
    "body_text": "Plain text version...",
    "body_html": "<html>...</html>",
    "date": "2024-01-15T10:30:00Z",
    "is_read": true,
    "is_starred": false,
    "folder": {
      "id": "uuid",
      "name": "Inbox",
      "type": "inbox"
    },
    "labels": [...],
    "attachments": [
      {
        "id": "uuid",
        "filename": "document.pdf",
        "content_type": "application/pdf",
        "size_bytes": 1048576
      }
    ],
    "security": {
      "dkim": "pass",
      "spf": "pass",
      "dmarc": "pass"
    },
    "thread": [
      {"id": "uuid", "snippet": "...", "date": "..."}
    ]
  }
}
```

### POST /emails
Send a new email.

**Request:**
```json
{
  "from_mailbox_id": "uuid",
  "to": ["recipient@example.com"],
  "cc": ["cc@example.com"],
  "bcc": ["bcc@example.com"],
  "subject": "Hello World",
  "body_text": "Plain text version",
  "body_html": "<p>HTML version</p>",
  "reply_to": "reply@example.com",
  "in_reply_to": "<message-id>",
  "attachments": ["attachment-uuid-1", "attachment-uuid-2"],
  "is_draft": false,
  "send_at": null
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "message_id": "<uuid@example.com>",
    "status": "sent"
  }
}
```

### PUT /emails/{id}
Update email (move, mark read, star, labels).

**Request:**
```json
{
  "is_read": true,
  "is_starred": false,
  "folder_id": "uuid",
  "label_ids": ["uuid1", "uuid2"]
}
```

### DELETE /emails/{id}
Move to trash or permanently delete.

**Query Parameters:**
- `permanent`: true = permanent delete, false = move to trash

### POST /emails/{id}/reply
Reply to email.

**Request:**
```json
{
  "body_text": "Reply text",
  "body_html": "<p>Reply HTML</p>",
  "reply_all": false,
  "attachments": []
}
```

### POST /emails/{id}/forward
Forward email.

**Request:**
```json
{
  "to": ["forward@example.com"],
  "body_text": "Forwarded message...",
  "include_attachments": true
}
```

### POST /emails/bulk
Bulk operations on emails.

**Request:**
```json
{
  "email_ids": ["uuid1", "uuid2"],
  "action": "mark_read" | "mark_unread" | "star" | "unstar" | "trash" | "delete" | "move" | "label",
  "folder_id": "uuid",
  "label_ids": ["uuid"]
}
```

### GET /emails/search
Advanced search.

**Query Parameters:**
- `q`: Search query (supports Gmail-like syntax: from:, to:, subject:, has:attachment, is:unread)
- `page`, `per_page`

---

## 5. Folder Endpoints

### GET /folders
List all folders for a mailbox.

**Query Parameters:**
- `mailbox_id`: Filter by mailbox

### POST /folders
Create custom folder.

**Request:**
```json
{
  "mailbox_id": "uuid",
  "name": "Projects",
  "parent_id": null,
  "color": "#3498db"
}
```

### PUT /folders/{id}
Update folder.

### DELETE /folders/{id}
Delete folder (moves emails to parent or inbox).

---

## 6. Label Endpoints

### GET /labels
List all labels.

### POST /labels
Create label.

**Request:**
```json
{
  "name": "Important",
  "color": "#e74c3c"
}
```

### PUT /labels/{id}
Update label.

### DELETE /labels/{id}
Delete label.

---

## 7. Attachment Endpoints

### POST /attachments/upload
Upload attachment (before sending email).

**Request:** multipart/form-data
- `file`: File to upload (max 25MB)

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "filename": "document.pdf",
    "content_type": "application/pdf",
    "size_bytes": 1048576
  }
}
```

### GET /attachments/{id}/download
Download attachment.

**Response:** File stream with appropriate Content-Type header.

---

## 8. Domain Endpoints

### GET /domains
List user's domains.

### POST /domains
Add a new domain.

**Request:**
```json
{
  "name": "mydomain.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "mydomain.com",
    "is_verified": false,
    "dns_records": [
      {
        "type": "TXT",
        "name": "_openmail-verify.mydomain.com",
        "value": "openmail-verification=abc123",
        "purpose": "verification"
      },
      {
        "type": "MX",
        "name": "mydomain.com",
        "value": "mail.openmail.example.com",
        "priority": 10,
        "purpose": "mx"
      },
      {
        "type": "TXT",
        "name": "mydomain.com",
        "value": "v=spf1 include:openmail.example.com ~all",
        "purpose": "spf"
      },
      {
        "type": "TXT",
        "name": "mail._domainkey.mydomain.com",
        "value": "v=DKIM1; k=rsa; p=MIGf...",
        "purpose": "dkim"
      },
      {
        "type": "TXT",
        "name": "_dmarc.mydomain.com",
        "value": "v=DMARC1; p=quarantine; rua=mailto:dmarc@openmail.example.com",
        "purpose": "dmarc"
      }
    ]
  }
}
```

### POST /domains/{id}/verify
Verify domain DNS configuration.

**Response:**
```json
{
  "success": true,
  "data": {
    "is_verified": true,
    "checks": {
      "mx": {"status": "pass", "found": "mail.openmail.example.com"},
      "spf": {"status": "pass"},
      "dkim": {"status": "pass"},
      "dmarc": {"status": "pass"}
    }
  }
}
```

### GET /domains/{id}/dns-records
Get required DNS records.

### DELETE /domains/{id}
Remove domain.

---

## 9. Filter Endpoints

### GET /filters
List email filters.

### POST /filters
Create email filter.

**Request:**
```json
{
  "name": "Newsletter Filter",
  "conditions": [
    {"field": "from", "operator": "contains", "value": "newsletter@"}
  ],
  "actions": [
    {"type": "move", "folder_id": "uuid"},
    {"type": "mark_read"}
  ],
  "stop_processing": false
}
```

### PUT /filters/{id}
Update filter.

### DELETE /filters/{id}
Delete filter.

---

## 10. Admin Endpoints

### GET /admin/users
List all users (admin only).

### GET /admin/domains
List all domains (admin only).

### GET /admin/stats
System statistics.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_users": 1500,
    "total_domains": 50,
    "total_mailboxes": 2000,
    "emails_today": {
      "sent": 5000,
      "received": 15000
    },
    "storage_used_bytes": 107374182400,
    "spam_blocked_today": 2500
  }
}
```

### GET /admin/logs
System logs.

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| AUTH_INVALID_CREDENTIALS | 401 | Invalid email or password |
| AUTH_TOKEN_EXPIRED | 401 | Access token expired |
| AUTH_TOKEN_INVALID | 401 | Invalid token |
| AUTH_UNAUTHORIZED | 403 | Not authorized for this resource |
| RESOURCE_NOT_FOUND | 404 | Resource not found |
| VALIDATION_ERROR | 422 | Request validation failed |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| EMAIL_SEND_FAILED | 500 | Failed to send email |
| DOMAIN_VERIFICATION_FAILED | 400 | Domain DNS not configured |
| QUOTA_EXCEEDED | 403 | Storage quota exceeded |

---

## Rate Limits

| Endpoint Group | Limit |
|---------------|-------|
| Auth endpoints | 10 req/min |
| Email send | 100 req/hour |
| Email read | 1000 req/min |
| Search | 60 req/min |
| Upload | 50 req/hour |
