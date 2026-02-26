# 🧪 OpenMail Platform - Test Cases

**Version:** 1.0  
**Framework:** pytest (Backend), Jest (Frontend)  
**Last Updated:** 2026-02-26

---

## 📋 Table of Contents

1. [Authentication Tests](#1-authentication-tests)
2. [Email Operations Tests](#2-email-operations-tests)
3. [Folder & Label Tests](#3-folder--label-tests)
4. [Domain & Mailbox Tests](#4-domain--mailbox-tests)
5. [Search Tests](#5-search-tests)
6. [API Endpoint Tests](#6-api-endpoint-tests)
7. [Integration Tests](#7-integration-tests)
8. [Frontend Component Tests](#8-frontend-component-tests)

---

## 1. Authentication Tests

### 1.1 User Registration

| Test ID | Test Case | Input | Expected Result |
|---------|-----------|-------|-----------------|
| AUTH-001 | Valid registration | Valid email, strong password | 201 Created, user created |
| AUTH-002 | Duplicate email | Existing email | 400 Bad Request, "email already exists" |
| AUTH-003 | Invalid email format | "notanemail" | 422 Validation Error |
| AUTH-004 | Weak password | "123" | 422 Validation Error, password requirements |
| AUTH-005 | Missing required fields | No email/password | 422 Validation Error |
| AUTH-006 | SQL injection attempt | `'; DROP TABLE users;--` | 422 Validation Error, sanitized |
| AUTH-007 | XSS in name | `<script>alert(1)</script>` | Sanitized, stored safely |

```python
# Test: AUTH-001 - Valid Registration
async def test_register_valid_user(client):
    response = await client.post("/api/v1/auth/register", json={
        "email": "newuser@test.com",
        "password": "SecurePass123!",
        "first_name": "Test",
        "last_name": "User"
    })
    assert response.status_code == 201
    assert response.json()["email"] == "newuser@test.com"
    assert "password" not in response.json()

# Test: AUTH-002 - Duplicate Email
async def test_register_duplicate_email(client, existing_user):
    response = await client.post("/api/v1/auth/register", json={
        "email": existing_user.email,
        "password": "SecurePass123!"
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]
```

### 1.2 User Login

| Test ID | Test Case | Input | Expected Result |
|---------|-----------|-------|-----------------|
| AUTH-010 | Valid login | Correct credentials | 200 OK, JWT tokens returned |
| AUTH-011 | Invalid password | Wrong password | 401 Unauthorized |
| AUTH-012 | Non-existent user | Unknown email | 401 Unauthorized |
| AUTH-013 | Inactive user | Deactivated account | 403 Forbidden |
| AUTH-014 | Locked account | After 5 failed attempts | 423 Locked, retry after X |
| AUTH-015 | Case insensitive email | UPPERCASE@email.com | 200 OK, matches |

```python
# Test: AUTH-010 - Valid Login
async def test_login_valid(client, test_user):
    response = await client.post("/api/v1/auth/login", json={
        "email": test_user.email,
        "password": "testpassword"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()

# Test: AUTH-014 - Account Lockout
async def test_account_lockout(client, test_user):
    for _ in range(5):
        await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "wrongpassword"
        })
    
    response = await client.post("/api/v1/auth/login", json={
        "email": test_user.email,
        "password": "testpassword"
    })
    assert response.status_code == 423
    assert "locked" in response.json()["detail"]
```

### 1.3 Token Management

| Test ID | Test Case | Input | Expected Result |
|---------|-----------|-------|-----------------|
| AUTH-020 | Access protected route | Valid token | 200 OK |
| AUTH-021 | Expired token | Expired JWT | 401 Unauthorized |
| AUTH-022 | Invalid token | Malformed JWT | 401 Unauthorized |
| AUTH-023 | Refresh token | Valid refresh token | New access token |
| AUTH-024 | Revoked refresh token | Used refresh token | 401 Unauthorized |
| AUTH-025 | Logout | Valid session | Session invalidated |

---

## 2. Email Operations Tests

### 2.1 Send Email

| Test ID | Test Case | Input | Expected Result |
|---------|-----------|-------|-----------------|
| EMAIL-001 | Send simple email | To, subject, body | 200 OK, email sent |
| EMAIL-002 | Send with CC/BCC | Multiple recipients | 200 OK, all receive |
| EMAIL-003 | Send with attachment | File < 25MB | 200 OK, attachment saved |
| EMAIL-004 | Large attachment | File > 25MB | 413 Payload Too Large |
| EMAIL-005 | Invalid recipient | "notanemail" | 422 Validation Error |
| EMAIL-006 | Empty subject | No subject | 200 OK, "(No Subject)" |
| EMAIL-007 | HTML email | HTML body | 200 OK, HTML preserved |
| EMAIL-008 | Too many recipients | > 100 recipients | 400 Bad Request |
| EMAIL-009 | Rate limit exceeded | > 100/hour | 429 Too Many Requests |

```python
# Test: EMAIL-001 - Send Simple Email
async def test_send_email(client, auth_headers, test_mailbox):
    response = await client.post("/api/v1/emails", 
        headers=auth_headers,
        json={
            "to": ["recipient@example.com"],
            "subject": "Test Email",
            "body_text": "This is a test email"
        }
    )
    assert response.status_code == 200
    assert response.json()["id"] is not None
    assert response.json()["is_sent"] == True

# Test: EMAIL-003 - Send with Attachment
async def test_send_email_with_attachment(client, auth_headers, test_file):
    response = await client.post("/api/v1/emails",
        headers=auth_headers,
        files={"attachments": ("test.pdf", test_file, "application/pdf")},
        data={
            "to": '["recipient@example.com"]',
            "subject": "With Attachment",
            "body_text": "See attached"
        }
    )
    assert response.status_code == 200
    assert len(response.json()["attachments"]) == 1
```

### 2.2 Read/Fetch Email

| Test ID | Test Case | Input | Expected Result |
|---------|-----------|-------|-----------------|
| EMAIL-010 | List inbox | Folder=inbox | List of emails |
| EMAIL-011 | Get single email | Valid email ID | Email details |
| EMAIL-012 | Get non-existent | Invalid ID | 404 Not Found |
| EMAIL-013 | Get other user's email | Another's email ID | 403 Forbidden |
| EMAIL-014 | Mark as read | Email ID | is_read = true |
| EMAIL-015 | Mark as unread | Email ID | is_read = false |
| EMAIL-016 | Pagination | page=2, per_page=20 | Correct page returned |

### 2.3 Email Actions

| Test ID | Test Case | Input | Expected Result |
|---------|-----------|-------|-----------------|
| EMAIL-020 | Star email | Email ID | is_starred = true |
| EMAIL-021 | Unstar email | Email ID | is_starred = false |
| EMAIL-022 | Delete email | Email ID | Moved to trash |
| EMAIL-023 | Permanent delete | Email in trash | 200 OK, deleted |
| EMAIL-024 | Archive email | Email ID | Moved to archive |
| EMAIL-025 | Move to folder | Email ID, folder ID | Folder updated |
| EMAIL-026 | Apply label | Email ID, label ID | Label applied |
| EMAIL-027 | Remove label | Email ID, label ID | Label removed |
| EMAIL-028 | Reply | Original email ID | Email with reply reference |
| EMAIL-029 | Forward | Original email ID | Email with forward prefix |

---

## 3. Folder & Label Tests

### 3.1 Folder Operations

| Test ID | Test Case | Input | Expected Result |
|---------|-----------|-------|-----------------|
| FOLDER-001 | List folders | Mailbox ID | System + custom folders |
| FOLDER-002 | Create folder | Name | 201 Created |
| FOLDER-003 | Duplicate name | Existing name | 400 Bad Request |
| FOLDER-004 | Nested folder | Parent folder ID | Folder with parent |
| FOLDER-005 | Rename folder | New name | 200 OK, renamed |
| FOLDER-006 | Delete empty folder | Folder ID | 200 OK, deleted |
| FOLDER-007 | Delete folder with emails | Folder ID | 400 or move emails |
| FOLDER-008 | Delete system folder | inbox/sent/etc | 403 Forbidden |

### 3.2 Label Operations

| Test ID | Test Case | Input | Expected Result |
|---------|-----------|-------|-----------------|
| LABEL-001 | List labels | Mailbox ID | All labels |
| LABEL-002 | Create label | Name, color | 201 Created |
| LABEL-003 | Update label | New color | 200 OK, updated |
| LABEL-004 | Delete label | Label ID | 200 OK, removed from emails |
| LABEL-005 | Label statistics | Label ID | Email count |

---

## 4. Domain & Mailbox Tests

### 4.1 Domain Operations

| Test ID | Test Case | Input | Expected Result |
|---------|-----------|-------|-----------------|
| DOMAIN-001 | Add domain | Valid domain | 201 Created, pending verification |
| DOMAIN-002 | Duplicate domain | Existing domain | 400 Bad Request |
| DOMAIN-003 | Invalid domain | "not a domain" | 422 Validation Error |
| DOMAIN-004 | Verify domain | Verification token | is_verified = true |
| DOMAIN-005 | Verification fail | Wrong DNS | 400, verification failed |
| DOMAIN-006 | Generate DKIM | Domain ID | Keys generated |
| DOMAIN-007 | Delete domain | Domain ID | Cascade delete mailboxes |

### 4.2 Mailbox Operations

| Test ID | Test Case | Input | Expected Result |
|---------|-----------|-------|-----------------|
| MBOX-001 | Create mailbox | Local part, domain | 201 Created |
| MBOX-002 | Duplicate address | Existing address | 400 Bad Request |
| MBOX-003 | Invalid local part | "has spaces" | 422 Validation Error |
| MBOX-004 | Set auto-reply | Subject, body, dates | Auto-reply enabled |
| MBOX-005 | Set forwarding | Forward address | Forwarding enabled |
| MBOX-006 | Check quota | Mailbox ID | Used/total bytes |

---

## 5. Search Tests

| Test ID | Test Case | Input | Expected Result |
|---------|-----------|-------|-----------------|
| SEARCH-001 | Simple search | "keyword" | Matching emails |
| SEARCH-002 | From search | from:sender@email.com | Emails from sender |
| SEARCH-003 | Subject search | subject:meeting | Matching subjects |
| SEARCH-004 | Date range | after:2026-01-01 before:2026-02-01 | Emails in range |
| SEARCH-005 | Has attachment | has:attachment | Emails with files |
| SEARCH-006 | Combined query | from:x subject:y has:attachment | Combined results |
| SEARCH-007 | No results | "xyznonexistent" | Empty list |
| SEARCH-008 | Special characters | "hello & goodbye" | Escaped, valid results |
| SEARCH-009 | Full-text search | Phrase in body | Matching emails |

---

## 6. API Endpoint Tests

### 6.1 Response Format Tests

| Test ID | Test Case | Expected |
|---------|-----------|----------|
| API-001 | Success response | `{"success": true, "data": {...}}` |
| API-002 | Error response | `{"success": false, "error": {...}}` |
| API-003 | Validation error | `{"detail": [...], "type": "validation_error"}` |
| API-004 | 404 response | `{"detail": "Not found"}` |
| API-005 | Rate limit response | `{"detail": "Rate limit exceeded", "retry_after": N}` |

### 6.2 HTTP Method Tests

| Test ID | Endpoint | Method | Expected |
|---------|----------|--------|----------|
| API-010 | /api/v1/emails | GET | List emails |
| API-011 | /api/v1/emails | POST | Create email |
| API-012 | /api/v1/emails/{id} | GET | Get email |
| API-013 | /api/v1/emails/{id} | PATCH | Update email |
| API-014 | /api/v1/emails/{id} | DELETE | Delete email |
| API-015 | /api/v1/emails | PUT | 405 Not Allowed |

### 6.3 Content-Type Tests

| Test ID | Content-Type | Expected |
|---------|--------------|----------|
| API-020 | application/json | Accepted |
| API-021 | multipart/form-data | Accepted (uploads) |
| API-022 | text/plain | 415 Unsupported |
| API-023 | Invalid JSON | 400 Bad Request |

---

## 7. Integration Tests

### 7.1 Email Flow Tests

| Test ID | Test Case | Steps | Expected |
|---------|-----------|-------|----------|
| INT-001 | Complete send flow | Send → Queue → Deliver | Email delivered |
| INT-002 | Receive flow | SMTP → Process → Store | Email in inbox |
| INT-003 | Reply thread | Send → Reply → Thread | Thread maintained |
| INT-004 | Forward chain | Receive → Forward → Receive | Forwarded content |
| INT-005 | Spam handling | Spam email → Process | Moved to spam folder |

### 7.2 Database Integration

| Test ID | Test Case | Expected |
|---------|-----------|----------|
| INT-010 | Transaction rollback | Failed op → no partial data |
| INT-011 | Cascade delete | Delete user → delete all related |
| INT-012 | Concurrent access | Multiple users → data integrity |
| INT-013 | Connection pool | High load → connections managed |

---

## 8. Frontend Component Tests

### 8.1 Email List Component

```typescript
// Test: EmailList renders correctly
describe('EmailList', () => {
  it('renders email items', () => {
    render(<EmailList emails={mockEmails} />);
    expect(screen.getAllByRole('listitem')).toHaveLength(mockEmails.length);
  });

  it('shows unread indicator', () => {
    render(<EmailList emails={[unreadEmail]} />);
    expect(screen.getByTestId('unread-indicator')).toBeInTheDocument();
  });

  it('handles empty list', () => {
    render(<EmailList emails={[]} />);
    expect(screen.getByText('No emails')).toBeInTheDocument();
  });

  it('selects email on click', async () => {
    const onSelect = jest.fn();
    render(<EmailList emails={mockEmails} onSelect={onSelect} />);
    await userEvent.click(screen.getAllByRole('listitem')[0]);
    expect(onSelect).toHaveBeenCalledWith(mockEmails[0]);
  });
});
```

### 8.2 Compose Modal Component

```typescript
describe('ComposeModal', () => {
  it('opens when isOpen is true', () => {
    render(<ComposeModal isOpen={true} onClose={jest.fn()} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('validates email addresses', async () => {
    render(<ComposeModal isOpen={true} onClose={jest.fn()} />);
    await userEvent.type(screen.getByLabelText('To'), 'invalid-email');
    await userEvent.click(screen.getByText('Send'));
    expect(screen.getByText('Invalid email address')).toBeInTheDocument();
  });

  it('sends email on submit', async () => {
    const mockSend = jest.spyOn(emailApi, 'send');
    render(<ComposeModal isOpen={true} onClose={jest.fn()} />);
    await userEvent.type(screen.getByLabelText('To'), 'test@example.com');
    await userEvent.type(screen.getByLabelText('Subject'), 'Test');
    await userEvent.click(screen.getByText('Send'));
    expect(mockSend).toHaveBeenCalled();
  });
});
```

### 8.3 Authentication Components

```typescript
describe('LoginForm', () => {
  it('submits credentials', async () => {
    const mockLogin = jest.spyOn(authApi, 'login');
    render(<LoginForm />);
    await userEvent.type(screen.getByLabelText('Email'), 'user@test.com');
    await userEvent.type(screen.getByLabelText('Password'), 'password');
    await userEvent.click(screen.getByRole('button', { name: 'Sign In' }));
    expect(mockLogin).toHaveBeenCalledWith({
      email: 'user@test.com',
      password: 'password'
    });
  });

  it('shows validation errors', async () => {
    render(<LoginForm />);
    await userEvent.click(screen.getByRole('button', { name: 'Sign In' }));
    expect(screen.getByText('Email is required')).toBeInTheDocument();
  });
});
```

---

## Running Tests

### Backend (pytest)

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_login_valid

# Verbose output
pytest -v
```

### Frontend (Jest)

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch

# Run specific file
npm test -- EmailList.test.tsx
```

---

*Test Cases Document v1.0*
*Generated by Chanakya 🧠*
