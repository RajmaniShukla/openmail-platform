"""
OpenMail Platform - Email Parser Utilities
"""
import re
import email
from email.policy import default as email_policy
from email.utils import parseaddr, parsedate_to_datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import hashlib
import base64


@dataclass
class ParsedAddress:
    """Parsed email address with name and email."""
    name: Optional[str]
    email: str
    
    def __str__(self):
        if self.name:
            return f"{self.name} <{self.email}>"
        return self.email


@dataclass
class ParsedAttachment:
    """Parsed email attachment."""
    filename: str
    content_type: str
    content: bytes
    content_id: Optional[str]
    is_inline: bool
    size: int
    checksum: str


@dataclass
class ParsedEmail:
    """Fully parsed email message."""
    message_id: str
    subject: str
    from_address: ParsedAddress
    to_addresses: List[ParsedAddress]
    cc_addresses: List[ParsedAddress]
    bcc_addresses: List[ParsedAddress]
    reply_to: Optional[ParsedAddress]
    date: datetime
    body_text: Optional[str]
    body_html: Optional[str]
    attachments: List[ParsedAttachment]
    headers: Dict[str, str]
    in_reply_to: Optional[str]
    references: List[str]
    raw_size: int


def parse_address(addr_str: str) -> ParsedAddress:
    """Parse an email address string into name and email parts."""
    name, email_addr = parseaddr(addr_str)
    return ParsedAddress(name=name if name else None, email=email_addr.lower())


def parse_address_list(addr_str: str) -> List[ParsedAddress]:
    """Parse a comma-separated list of email addresses."""
    if not addr_str:
        return []
    
    addresses = []
    # Handle quoted names with commas
    parts = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', addr_str)
    
    for part in parts:
        part = part.strip()
        if part:
            addresses.append(parse_address(part))
    
    return addresses


def extract_body(msg: email.message.EmailMessage) -> Tuple[Optional[str], Optional[str]]:
    """Extract plain text and HTML body from email message."""
    body_text = None
    body_html = None
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            
            # Skip attachments
            if "attachment" in content_disposition:
                continue
            
            try:
                payload = part.get_content()
                
                if content_type == "text/plain" and body_text is None:
                    if isinstance(payload, bytes):
                        body_text = payload.decode("utf-8", errors="replace")
                    else:
                        body_text = payload
                elif content_type == "text/html" and body_html is None:
                    if isinstance(payload, bytes):
                        body_html = payload.decode("utf-8", errors="replace")
                    else:
                        body_html = payload
            except Exception:
                continue
    else:
        content_type = msg.get_content_type()
        try:
            payload = msg.get_content()
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8", errors="replace")
            
            if content_type == "text/plain":
                body_text = payload
            elif content_type == "text/html":
                body_html = payload
        except Exception:
            pass
    
    return body_text, body_html


def extract_attachments(msg: email.message.EmailMessage) -> List[ParsedAttachment]:
    """Extract attachments from email message."""
    attachments = []
    
    if not msg.is_multipart():
        return attachments
    
    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition", ""))
        content_type = part.get_content_type()
        
        # Check if it's an attachment
        if "attachment" in content_disposition or (
            part.get_filename() and content_type not in ["text/plain", "text/html"]
        ):
            filename = part.get_filename() or "unnamed"
            content_id = part.get("Content-ID", "").strip("<>")
            is_inline = "inline" in content_disposition
            
            try:
                content = part.get_payload(decode=True)
                if content:
                    checksum = hashlib.md5(content).hexdigest()
                    
                    attachments.append(ParsedAttachment(
                        filename=filename,
                        content_type=content_type,
                        content=content,
                        content_id=content_id if content_id else None,
                        is_inline=is_inline,
                        size=len(content),
                        checksum=checksum,
                    ))
            except Exception:
                continue
    
    return attachments


def parse_email(raw_email: str | bytes) -> ParsedEmail:
    """Parse a raw email message into structured data."""
    if isinstance(raw_email, str):
        raw_email = raw_email.encode("utf-8")
    
    msg = email.message_from_bytes(raw_email, policy=email_policy)
    
    # Extract headers
    headers = {key: str(value) for key, value in msg.items()}
    
    # Parse addresses
    from_addr = parse_address(msg.get("From", ""))
    to_addrs = parse_address_list(msg.get("To", ""))
    cc_addrs = parse_address_list(msg.get("Cc", ""))
    bcc_addrs = parse_address_list(msg.get("Bcc", ""))
    reply_to = parse_address(msg.get("Reply-To", "")) if msg.get("Reply-To") else None
    
    # Parse date
    date_str = msg.get("Date", "")
    try:
        date = parsedate_to_datetime(date_str)
    except Exception:
        date = datetime.utcnow()
    
    # Extract body
    body_text, body_html = extract_body(msg)
    
    # Extract attachments
    attachments = extract_attachments(msg)
    
    # Parse references
    references_str = msg.get("References", "")
    references = [ref.strip("<>") for ref in references_str.split() if ref.strip()]
    
    return ParsedEmail(
        message_id=msg.get("Message-ID", "").strip("<>"),
        subject=msg.get("Subject", ""),
        from_address=from_addr,
        to_addresses=to_addrs,
        cc_addresses=cc_addrs,
        bcc_addresses=bcc_addrs,
        reply_to=reply_to,
        date=date,
        body_text=body_text,
        body_html=body_html,
        attachments=attachments,
        headers=headers,
        in_reply_to=msg.get("In-Reply-To", "").strip("<>") or None,
        references=references,
        raw_size=len(raw_email),
    )


def generate_snippet(body_text: Optional[str], body_html: Optional[str], max_length: int = 200) -> str:
    """Generate a snippet from email body."""
    text = body_text
    
    if not text and body_html:
        # Strip HTML tags for snippet
        text = re.sub(r'<[^>]+>', ' ', body_html)
        text = re.sub(r'\s+', ' ', text).strip()
    
    if not text:
        return ""
    
    # Truncate and clean
    text = text[:max_length].strip()
    if len(text) == max_length:
        text = text.rsplit(' ', 1)[0] + "..."
    
    return text


def extract_email_domain(email_addr: str) -> str:
    """Extract domain from email address."""
    if "@" in email_addr:
        return email_addr.split("@")[1].lower()
    return ""


def is_valid_email(email_addr: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email_addr))


def sanitize_html(html: str) -> str:
    """Sanitize HTML content for safe display."""
    # Remove script tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove on* event handlers
    html = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
    
    # Remove javascript: URLs
    html = re.sub(r'href\s*=\s*["\']javascript:[^"\']*["\']', 'href="#"', html, flags=re.IGNORECASE)
    
    return html


def generate_thread_id(message_id: str, in_reply_to: Optional[str], references: List[str]) -> str:
    """Generate a thread ID for email threading."""
    if references:
        # Use first reference as thread root
        return hashlib.md5(references[0].encode()).hexdigest()[:16]
    elif in_reply_to:
        return hashlib.md5(in_reply_to.encode()).hexdigest()[:16]
    else:
        # New thread
        return hashlib.md5(message_id.encode()).hexdigest()[:16]
