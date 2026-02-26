# ✅ OpenMail Platform - QA Test Plan

**Version:** 1.0  
**Last Updated:** 2026-02-26  
**Test Environment:** Staging

---

## 📋 Table of Contents

1. [Test Overview](#1-test-overview)
2. [Functional Testing](#2-functional-testing)
3. [Security Testing](#3-security-testing)
4. [Performance Testing](#4-performance-testing)
5. [Accessibility Testing](#5-accessibility-testing)
6. [Compatibility Testing](#6-compatibility-testing)
7. [Regression Testing](#7-regression-testing)
8. [Test Execution](#8-test-execution)

---

## 1. Test Overview

### 1.1 Testing Objectives

- Verify all features work as specified
- Ensure security vulnerabilities are addressed
- Validate performance under load
- Confirm accessibility compliance
- Test cross-browser/device compatibility

### 1.2 Test Scope

| In Scope | Out of Scope |
|----------|--------------|
| Web application | Mobile native apps |
| API endpoints | Third-party integrations |
| Email send/receive | Mail server internals |
| User authentication | DNS infrastructure |
| Search functionality | CDN caching |

### 1.3 Test Environments

| Environment | URL | Purpose |
|-------------|-----|---------|
| Development | localhost:3000 | Developer testing |
| Staging | staging.openmail.com | QA testing |
| Production | mail.openmail.com | Smoke testing only |

---

## 2. Functional Testing

### 2.1 Authentication Module

#### ☐ User Registration
- [ ] Register with valid email and password
- [ ] Receive verification email
- [ ] Complete email verification
- [ ] Attempt registration with existing email
- [ ] Test password strength validation
- [ ] Test email format validation

#### ☐ User Login
- [ ] Login with valid credentials
- [ ] Login with invalid password
- [ ] Login with non-existent email
- [ ] Test "Remember me" functionality
- [ ] Test account lockout after failed attempts
- [ ] Test account unlock after timeout

#### ☐ Password Management
- [ ] Change password (authenticated)
- [ ] Forgot password flow
- [ ] Password reset email delivery
- [ ] Reset link expiration
- [ ] Use reset link twice (should fail)

#### ☐ Session Management
- [ ] Session persists across page reloads
- [ ] Session expires after inactivity
- [ ] Logout clears session
- [ ] Multiple device sessions
- [ ] View active sessions
- [ ] Terminate other sessions

### 2.2 Email Module

#### ☐ Compose Email
- [ ] Open compose modal
- [ ] Add single recipient
- [ ] Add multiple recipients
- [ ] Add CC recipients
- [ ] Add BCC recipients
- [ ] Type subject line
- [ ] Type plain text body
- [ ] Use rich text formatting (bold, italic, links)
- [ ] Attach single file
- [ ] Attach multiple files
- [ ] Remove attachment
- [ ] Send email successfully
- [ ] Verify email appears in Sent folder
- [ ] Save as draft
- [ ] Discard draft

#### ☐ Read Email
- [ ] Open email from list
- [ ] Email marked as read automatically
- [ ] View full email content
- [ ] View HTML email correctly
- [ ] View plain text email
- [ ] View email headers (advanced)
- [ ] Download attachments
- [ ] Preview attachments (PDF, images)

#### ☐ Email Actions
- [ ] Reply to email
- [ ] Reply all
- [ ] Forward email
- [ ] Forward with attachments
- [ ] Star/unstar email
- [ ] Mark as unread
- [ ] Delete email (move to trash)
- [ ] Archive email
- [ ] Move to folder
- [ ] Apply label
- [ ] Remove label
- [ ] Print email

#### ☐ Email Threads
- [ ] View conversation thread
- [ ] Expand/collapse quoted text
- [ ] Reply within thread
- [ ] Thread ordering correct

### 2.3 Folder Management

#### ☐ Default Folders
- [ ] Inbox shows incoming emails
- [ ] Sent shows sent emails
- [ ] Drafts shows saved drafts
- [ ] Starred shows starred emails
- [ ] Trash shows deleted emails
- [ ] Spam shows spam emails
- [ ] Archive shows archived emails

#### ☐ Custom Folders
- [ ] Create new folder
- [ ] Create nested folder
- [ ] Rename folder
- [ ] Delete folder
- [ ] Move folder
- [ ] Cannot delete system folders

### 2.4 Label Management

#### ☐ Label Operations
- [ ] Create new label
- [ ] Choose label color
- [ ] Rename label
- [ ] Delete label
- [ ] Apply label to email
- [ ] Remove label from email
- [ ] Filter by label
- [ ] Multiple labels on one email

### 2.5 Search Functionality

#### ☐ Basic Search
- [ ] Search by keyword
- [ ] Search results display correctly
- [ ] Click search result opens email

#### ☐ Advanced Search
- [ ] Search by sender (from:)
- [ ] Search by recipient (to:)
- [ ] Search by subject (subject:)
- [ ] Search by date range
- [ ] Search for attachments (has:attachment)
- [ ] Search unread (is:unread)
- [ ] Combined search operators

### 2.6 Settings

#### ☐ General Settings
- [ ] Change display name
- [ ] Change timezone
- [ ] Change language
- [ ] Change date format
- [ ] Toggle dark mode

#### ☐ Email Settings
- [ ] Create email signature
- [ ] Enable/disable signature
- [ ] Set reply position (top/bottom)
- [ ] Set default reply mode (reply/reply all)
- [ ] Set undo send delay

#### ☐ Notification Settings
- [ ] Enable/disable desktop notifications
- [ ] Enable/disable sound
- [ ] Set email digest preferences

#### ☐ Vacation Responder
- [ ] Enable auto-reply
- [ ] Set date range
- [ ] Compose auto-reply message
- [ ] Disable auto-reply

---

## 3. Security Testing

### 3.1 Authentication Security

| Test | Method | Expected Result |
|------|--------|-----------------|
| Brute force protection | 10 rapid login attempts | Account locked |
| Password hashing | Check database | bcrypt hash stored |
| Session hijacking | Steal session cookie | Should fail (httpOnly) |
| CSRF protection | Cross-site request | Should fail |
| JWT validation | Tampered token | Rejected |

### 3.2 Input Validation

| Test | Input | Expected Result |
|------|-------|-----------------|
| SQL Injection | `' OR '1'='1` | Input sanitized |
| XSS Stored | `<script>alert(1)</script>` | Escaped on display |
| XSS Reflected | `?q=<script>` | Escaped |
| Command Injection | `; ls -la` | Input rejected |
| Path Traversal | `../../../etc/passwd` | Path sanitized |

### 3.3 Authorization Testing

| Test | Action | Expected Result |
|------|--------|-----------------|
| IDOR - Email | Access other user's email | 403 Forbidden |
| IDOR - Folder | Access other user's folder | 403 Forbidden |
| Privilege Escalation | User→Admin actions | 403 Forbidden |
| Expired Token | Use expired JWT | 401 Unauthorized |

### 3.4 Email Security

| Test | Method | Expected Result |
|------|--------|-----------------|
| Spam filtering | Send known spam | Moved to spam folder |
| DKIM verification | Check signature | Valid DKIM |
| SPF check | Check sender IP | SPF pass |
| Malicious attachment | Send EICAR test | Quarantined |

---

## 4. Performance Testing

### 4.1 Load Testing

| Scenario | Target | Acceptance Criteria |
|----------|--------|---------------------|
| Normal load | 100 concurrent users | Response < 500ms |
| Peak load | 500 concurrent users | Response < 2s |
| Stress test | 1000 concurrent users | Graceful degradation |
| Sustained load | 100 users for 1 hour | No memory leaks |

### 4.2 Response Time Targets

| Operation | Target | Maximum |
|-----------|--------|---------|
| Login | 200ms | 1s |
| Load inbox | 300ms | 2s |
| Send email | 500ms | 3s |
| Search | 500ms | 3s |
| Open email | 200ms | 1s |

### 4.3 Scalability Testing

| Test | Method | Pass Criteria |
|------|--------|---------------|
| Database scaling | Add read replicas | Linear improvement |
| API scaling | Add backend instances | Linear improvement |
| Cache effectiveness | Measure cache hit ratio | >80% hit rate |

---

## 5. Accessibility Testing

### 5.1 WCAG 2.1 Compliance

#### Level A (Must Have)

| Criterion | Test | Status |
|-----------|------|--------|
| 1.1.1 Non-text Content | All images have alt text | ☐ |
| 1.3.1 Info and Relationships | Proper heading structure | ☐ |
| 1.4.1 Use of Color | Color not only indicator | ☐ |
| 2.1.1 Keyboard | All functions via keyboard | ☐ |
| 2.4.1 Bypass Blocks | Skip navigation link | ☐ |
| 3.1.1 Language | Page language specified | ☐ |
| 4.1.1 Parsing | Valid HTML | ☐ |

#### Level AA (Should Have)

| Criterion | Test | Status |
|-----------|------|--------|
| 1.4.3 Contrast | 4.5:1 minimum ratio | ☐ |
| 1.4.4 Resize Text | 200% zoom works | ☐ |
| 2.4.6 Headings | Descriptive headings | ☐ |
| 2.4.7 Focus Visible | Focus indicator visible | ☐ |
| 3.2.3 Consistent Navigation | Same navigation order | ☐ |

### 5.2 Screen Reader Testing

| Reader | Browser | Test Status |
|--------|---------|-------------|
| NVDA | Chrome | ☐ |
| JAWS | Chrome | ☐ |
| VoiceOver | Safari | ☐ |
| TalkBack | Chrome Android | ☐ |

### 5.3 Keyboard Navigation

| Action | Keys | Status |
|--------|------|--------|
| Focus next element | Tab | ☐ |
| Focus previous | Shift+Tab | ☐ |
| Activate button | Enter/Space | ☐ |
| Close modal | Escape | ☐ |
| Navigate email list | Arrow keys | ☐ |

---

## 6. Compatibility Testing

### 6.1 Browser Compatibility

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | 120+ | ☐ |
| Firefox | 120+ | ☐ |
| Safari | 17+ | ☐ |
| Edge | 120+ | ☐ |
| Chrome Mobile | Latest | ☐ |
| Safari iOS | Latest | ☐ |

### 6.2 Device Testing

| Device Type | Screen Size | Status |
|-------------|-------------|--------|
| Desktop | 1920×1080 | ☐ |
| Laptop | 1366×768 | ☐ |
| Tablet (landscape) | 1024×768 | ☐ |
| Tablet (portrait) | 768×1024 | ☐ |
| Mobile (large) | 414×896 | ☐ |
| Mobile (small) | 375×667 | ☐ |

### 6.3 Responsive Design

| Breakpoint | Behavior | Status |
|------------|----------|--------|
| >1200px | Full desktop layout | ☐ |
| 992-1199px | Condensed sidebar | ☐ |
| 768-991px | Collapsible sidebar | ☐ |
| <768px | Mobile hamburger menu | ☐ |

---

## 7. Regression Testing

### 7.1 Smoke Tests (Run Every Deploy)

| # | Test | Expected |
|---|------|----------|
| 1 | Homepage loads | 200 OK |
| 2 | Login works | Access granted |
| 3 | Inbox loads | Emails displayed |
| 4 | Send email works | Email sent |
| 5 | Search works | Results returned |
| 6 | Logout works | Session ended |

### 7.2 Regression Suite (Run Weekly)

- [ ] All authentication tests
- [ ] All email operation tests
- [ ] All folder/label tests
- [ ] Search functionality
- [ ] Settings changes
- [ ] API endpoint tests

---

## 8. Test Execution

### 8.1 Test Environment Setup

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Seed test data
docker-compose exec backend python -m scripts.seed_test_data
```

### 8.2 Running Tests

```bash
# Backend tests
cd backend
pytest -v --cov=app

# Frontend tests
cd frontend
npm test -- --coverage

# E2E tests
npx playwright test

# Security scan
npm run security-audit
```

### 8.3 Test Reporting

| Report Type | Tool | Location |
|-------------|------|----------|
| Unit test coverage | pytest-cov | htmlcov/index.html |
| E2E test results | Playwright | playwright-report/ |
| Security scan | npm audit | console output |
| Performance | k6 | results/perf-report.html |

### 8.4 Bug Reporting Template

```markdown
## Bug Report

**Title:** [Brief description]

**Environment:**
- Browser: Chrome 120
- OS: Windows 11
- User: test@example.com

**Steps to Reproduce:**
1. Step one
2. Step two
3. Step three

**Expected Result:**
What should happen

**Actual Result:**
What actually happened

**Screenshots/Videos:**
[Attach if applicable]

**Severity:** Critical/High/Medium/Low

**Additional Notes:**
Any other context
```

---

## Sign-Off Checklist

Before release, ensure:

- [ ] All critical tests passing
- [ ] No high-severity bugs open
- [ ] Performance within targets
- [ ] Security scan clean
- [ ] Accessibility review complete
- [ ] Cross-browser testing done
- [ ] Regression suite passed
- [ ] Documentation updated

---

*QA Test Plan v1.0*
*Generated by Chanakya 🧠*
