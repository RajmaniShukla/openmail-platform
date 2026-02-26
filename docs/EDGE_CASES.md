# ⚠️ OpenMail Platform - Edge Cases Documentation

**Version:** 1.0  
**Last Updated:** 2026-02-26

---

## 📋 Table of Contents

1. [Input Validation Edge Cases](#1-input-validation-edge-cases)
2. [Email Content Edge Cases](#2-email-content-edge-cases)
3. [File Attachment Edge Cases](#3-file-attachment-edge-cases)
4. [Concurrency Edge Cases](#4-concurrency-edge-cases)
5. [Network & Infrastructure Edge Cases](#5-network--infrastructure-edge-cases)
6. [Security Edge Cases](#6-security-edge-cases)
7. [Data Integrity Edge Cases](#7-data-integrity-edge-cases)
8. [Performance Edge Cases](#8-performance-edge-cases)

---

## 1. Input Validation Edge Cases

### 1.1 Email Address Validation

| Edge Case | Input | Expected Handling |
|-----------|-------|-------------------|
| Maximum length | 254 character email | Accept (RFC 5321 limit) |
| Over maximum | 255+ characters | Reject with clear error |
| Unicode domain | user@münchen.de | Accept (IDN support) |
| Punycode domain | user@xn--mnchen-3ya.de | Accept |
| Plus addressing | user+tag@domain.com | Accept |
| Subaddressing | user+filter@domain.com | Accept, support filtering |
| Quoted local part | "user name"@domain.com | Accept (RFC 5321) |
| IP literal domain | user@[192.168.1.1] | Accept/reject by policy |
| Multiple @ signs | user@@domain.com | Reject |
| Empty local part | @domain.com | Reject |
| Trailing dot | user@domain.com. | Normalize, accept |

### 1.2 Password Validation

| Edge Case | Input | Expected Handling |
|-----------|-------|-------------------|
| Exactly minimum | 8 characters | Accept |
| Just under minimum | 7 characters | Reject |
| Maximum length | 128 characters | Accept |
| Over maximum | 129+ characters | Truncate or reject |
| All spaces | "        " | Reject (whitespace only) |
| Leading/trailing spaces | " password " | Accept, preserve |
| Unicode characters | "pässwörd🔒" | Accept |
| Null bytes | "pass\x00word" | Reject/sanitize |
| SQL special chars | "pass'word; DROP" | Accept (properly hashed) |

### 1.3 Name Fields

| Edge Case | Input | Expected Handling |
|-----------|-------|-------------------|
| Empty string | "" | Allow or set default |
| Single character | "A" | Accept |
| Very long name | 1000 characters | Truncate to limit |
| Unicode names | "田中太郎" | Accept |
| Emoji in name | "John 🚀 Smith" | Accept |
| HTML entities | "John &amp; Jane" | Escape on display |
| Script injection | "<script>alert(1)</script>" | Sanitize |
| Control characters | "John\x00Smith" | Remove control chars |
| RTL text | "دانيال" | Accept, handle display |

---

## 2. Email Content Edge Cases

### 2.1 Subject Line

| Edge Case | Input | Expected Handling |
|-----------|-------|-------------------|
| Empty subject | (none) | Accept, display "(No Subject)" |
| Very long subject | 10,000 characters | Truncate to reasonable limit |
| Newlines in subject | "Subject\nLine 2" | Remove or replace with space |
| Unicode | "Re: 日本語メール" | Accept, preserve |
| Emoji | "Meeting 📅 Tomorrow" | Accept |
| Only whitespace | "   " | Treat as empty |
| RE: prefix variants | "Re:", "RE:", "re:", "Re[2]:" | Normalize for threading |
| FWD: variants | "Fwd:", "FW:", "Forwarded:" | Normalize |

### 2.2 Email Body

| Edge Case | Input | Expected Handling |
|-----------|-------|-------------------|
| Empty body | (none) | Accept |
| Very large body | 10MB text | Accept with limit warning |
| Plain text only | No HTML | Accept, display plain |
| HTML only | No plain text | Accept, generate plain text |
| Mixed content | Text + HTML | Accept both |
| Malicious HTML | Script tags, onclick | Sanitize, strip dangerous |
| CSS injection | `<style>body{display:none}</style>` | Strip external styles |
| External images | `<img src="http://tracker.com/pixel.gif">` | Block by default, warn |
| Data URIs | `<img src="data:image/png;base64,...">` | Accept with size limit |
| Nested quotes | Multiple reply levels | Preserve, may collapse in UI |
| Binary content | Non-UTF8 bytes | Handle encoding, show warning |

### 2.3 Threading

| Edge Case | Input | Expected Handling |
|-----------|-------|-------------------|
| Missing Message-ID | No header | Generate UUID-based ID |
| Duplicate Message-ID | Already exists | Reject as duplicate |
| Invalid References header | Malformed | Parse best-effort |
| Circular references | A→B→A | Detect and break cycle |
| Very long thread | 1000+ replies | Performance optimize |
| Cross-mailbox thread | Different users | Separate threads per user |

---

## 3. File Attachment Edge Cases

### 3.1 File Size

| Edge Case | Input | Expected Handling |
|-----------|-------|-------------------|
| Zero bytes | Empty file | Accept or reject by policy |
| Exactly at limit | 25.00 MB | Accept |
| Just over limit | 25.01 MB | Reject with clear message |
| Multiple files at limit | 5×5MB = 25MB | Accept if total ≤ limit |
| Multiple over limit | 5×6MB = 30MB | Reject |
| Claimed vs actual size | Mismatch | Use actual, verify |

### 3.2 File Names

| Edge Case | Input | Expected Handling |
|-----------|-------|-------------------|
| Very long name | 500 characters | Truncate, preserve extension |
| No extension | "document" | Accept, detect type |
| Double extension | "file.pdf.exe" | Flag as suspicious |
| Hidden files | ".hidden" | Accept |
| Unicode names | "документ.pdf" | Accept |
| Path traversal | "../../../etc/passwd" | Sanitize, remove path |
| Null bytes | "file\x00.pdf" | Remove null bytes |
| Reserved names | "CON.txt" (Windows) | Rename on Windows systems |
| Special characters | "file:name?.txt" | Sanitize for filesystem |

### 3.3 File Content

| Edge Case | Input | Expected Handling |
|-----------|-------|-------------------|
| Wrong MIME type | .pdf with image data | Detect actual type |
| Executable files | .exe, .bat, .sh | Block or quarantine |
| Archive with executable | .zip containing .exe | Scan, warn, or block |
| Password-protected ZIP | Encrypted archive | Accept, note unscanned |
| Corrupted file | Invalid format | Accept, note corrupted |
| Virus signature | Test EICAR | Detect, quarantine |
| Polyglot files | Valid PDF + valid ZIP | Accept, flag unusual |

---

## 4. Concurrency Edge Cases

### 4.1 Simultaneous Operations

| Edge Case | Scenario | Expected Handling |
|-----------|----------|-------------------|
| Double send | Click send twice fast | Deduplicate, send once |
| Concurrent edits | Two tabs editing draft | Last write wins or merge |
| Move during delete | Move email while deleting | Transaction isolation |
| Folder rename during move | Rename target folder | Atomic operation |
| Label delete during apply | Delete label being applied | Transaction rollback |

### 4.2 Race Conditions

| Edge Case | Scenario | Expected Handling |
|-----------|----------|-------------------|
| Session race | Login from two devices | Both sessions valid |
| Token refresh race | Multiple refreshes | Only first succeeds |
| Quota check race | Concurrent large sends | Accurate quota check |
| Unread count race | Mark read from multiple | Eventually consistent |
| Search index race | Index during modification | Eventual consistency |

---

## 5. Network & Infrastructure Edge Cases

### 5.1 Connection Issues

| Edge Case | Scenario | Expected Handling |
|-----------|----------|-------------------|
| Timeout mid-send | Network drops during send | Retry logic, no duplicate |
| Partial upload | Attachment upload interrupted | Resume or restart |
| Database unavailable | PostgreSQL down | Graceful degradation |
| Redis unavailable | Cache down | Fallback to DB |
| Elasticsearch down | Search unavailable | Disable search, show error |
| Mail server down | Postfix unreachable | Queue for later delivery |

### 5.2 DNS Issues

| Edge Case | Scenario | Expected Handling |
|-----------|----------|-------------------|
| MX lookup fail | No MX record | Fall back to A record |
| PTR lookup fail | No reverse DNS | Log warning, continue |
| DKIM key fetch fail | DNS timeout | Retry with backoff |
| SPF lookup timeout | Slow DNS | Timeout, fail open/closed |
| Domain verification delay | DNS propagation | Retry for 48 hours |

---

## 6. Security Edge Cases

### 6.1 Authentication

| Edge Case | Scenario | Expected Handling |
|-----------|----------|-------------------|
| Timing attack | Password comparison | Constant-time compare |
| Session fixation | Pre-set session ID | Generate new on login |
| JWT algorithm none | alg: none attack | Reject, require HS256 |
| Token replay | Reuse old token | Check expiry, blacklist |
| Password spray | Many users, one password | Rate limit by IP |
| Credential stuffing | Breached credentials | Rate limit, CAPTCHA |

### 6.2 Email Security

| Edge Case | Scenario | Expected Handling |
|-----------|----------|-------------------|
| From header spoofing | Fake sender | DMARC check |
| Reply-To hijacking | Different reply address | Display warning |
| Homograph attack | рaypal.com (Cyrillic p) | IDN display warning |
| MIME smuggling | Hidden content | Strict parsing |
| Header injection | Newline in headers | Reject/sanitize |
| Attachment disguise | Fake PDF icon | Show actual type |

### 6.3 Authorization

| Edge Case | Scenario | Expected Handling |
|-----------|----------|-------------------|
| IDOR attempt | Access other user's email | 403 Forbidden |
| Privilege escalation | User→Admin | Verify role properly |
| Token scope bypass | Use refresh as access | Validate token type |
| Multi-tenant leak | Cross-tenant access | Strict tenant isolation |

---

## 7. Data Integrity Edge Cases

### 7.1 Data Corruption

| Edge Case | Scenario | Expected Handling |
|-----------|----------|-------------------|
| Invalid UTF-8 | Corrupted encoding | Replace invalid chars |
| Truncated JSON | Incomplete metadata | Validation, reject |
| Orphaned attachments | Email deleted, file remains | Cleanup job |
| Orphaned threads | All emails deleted | Clean up thread_id |
| Duplicate emails | Same message_id | Reject duplicate |

### 7.2 Storage Issues

| Edge Case | Scenario | Expected Handling |
|-----------|----------|-------------------|
| Disk full | No space for attachment | Clear error, rollback |
| S3 unavailable | MinIO down | Queue upload, retry |
| Quota exceeded | User over limit | Reject new, warn user |
| Partial write | Incomplete file save | Checksum verify, retry |

---

## 8. Performance Edge Cases

### 8.1 High Volume

| Edge Case | Scenario | Expected Handling |
|-----------|----------|-------------------|
| Mass email receive | Thousands at once | Queue, process async |
| Large inbox load | 100,000+ emails | Pagination, lazy load |
| Heavy search | Complex query, millions | Timeout, suggest refine |
| Attachment storm | Many large files | Rate limit, queue |

### 8.2 Resource Limits

| Edge Case | Scenario | Expected Handling |
|-----------|----------|-------------------|
| Memory exhaustion | Large email processing | Stream processing |
| CPU spike | Complex filter rules | Async processing |
| Connection pool exhausted | Many concurrent users | Queue requests |
| Thread starvation | Blocking operations | Async, non-blocking |

---

## Testing Edge Cases

### Automated Testing

```python
# Example edge case test
@pytest.mark.parametrize("email,expected", [
    ("user@domain.com", True),
    ("user@münchen.de", True),  # IDN
    ("user+tag@domain.com", True),  # Plus addressing
    ('"user name"@domain.com', True),  # Quoted
    ("user@@domain.com", False),  # Invalid
    ("@domain.com", False),  # Empty local
    ("a" * 255 + "@domain.com", False),  # Too long
])
def test_email_validation_edge_cases(email, expected):
    result = validate_email(email)
    assert result.is_valid == expected
```

### Manual Testing Checklist

- [ ] Test with various Unicode inputs
- [ ] Test with maximum length inputs
- [ ] Test with empty/null inputs
- [ ] Test concurrent operations
- [ ] Test network interruptions
- [ ] Test with malicious inputs
- [ ] Test quota boundaries
- [ ] Test time-based edge cases (timezone, DST)

---

*Edge Cases Documentation v1.0*
*Generated by Chanakya 🧠*
