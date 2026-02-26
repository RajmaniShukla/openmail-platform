"""
OpenMail Platform - Input Validators
"""
import re
from typing import List, Optional
from email_validator import validate_email, EmailNotValidError


def validate_email_address(email: str) -> tuple[bool, str]:
    """
    Validate an email address.
    Returns (is_valid, error_message_or_normalized_email)
    """
    try:
        result = validate_email(email, check_deliverability=False)
        return True, result.normalized
    except EmailNotValidError as e:
        return False, str(e)


def validate_email_list(emails: List[str]) -> tuple[List[str], List[str]]:
    """
    Validate a list of email addresses.
    Returns (valid_emails, invalid_emails)
    """
    valid = []
    invalid = []
    
    for email in emails:
        is_valid, result = validate_email_address(email)
        if is_valid:
            valid.append(result)
        else:
            invalid.append(email)
    
    return valid, invalid


def validate_domain_name(domain: str) -> tuple[bool, str]:
    """
    Validate a domain name.
    Returns (is_valid, error_message_or_empty)
    """
    if not domain:
        return False, "Domain cannot be empty"
    
    # Basic domain pattern
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    
    if not re.match(pattern, domain):
        return False, "Invalid domain format"
    
    if len(domain) > 253:
        return False, "Domain name too long"
    
    return True, ""


def validate_password_strength(password: str, min_length: int = 8) -> tuple[bool, List[str]]:
    """
    Validate password strength.
    Returns (is_valid, list_of_issues)
    """
    issues = []
    
    if len(password) < min_length:
        issues.append(f"Password must be at least {min_length} characters")
    
    if not re.search(r'[a-z]', password):
        issues.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'[A-Z]', password):
        issues.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'\d', password):
        issues.append("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        issues.append("Password must contain at least one special character")
    
    return len(issues) == 0, issues


def validate_folder_name(name: str) -> tuple[bool, str]:
    """
    Validate folder name.
    Returns (is_valid, error_message_or_empty)
    """
    if not name:
        return False, "Folder name cannot be empty"
    
    if len(name) > 100:
        return False, "Folder name too long (max 100 characters)"
    
    # Check for invalid characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        if char in name:
            return False, f"Folder name cannot contain '{char}'"
    
    return True, ""


def validate_label_name(name: str) -> tuple[bool, str]:
    """
    Validate label name.
    Returns (is_valid, error_message_or_empty)
    """
    if not name:
        return False, "Label name cannot be empty"
    
    if len(name) > 100:
        return False, "Label name too long (max 100 characters)"
    
    return True, ""


def validate_color_hex(color: str) -> tuple[bool, str]:
    """
    Validate hex color code.
    Returns (is_valid, error_message_or_empty)
    """
    if not color:
        return True, ""  # Optional
    
    pattern = r'^#[0-9A-Fa-f]{6}$'
    if not re.match(pattern, color):
        return False, "Invalid hex color format (use #RRGGBB)"
    
    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe storage.
    """
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # Remove other dangerous characters
    filename = re.sub(r'[<>:"|?*]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_len = 255 - len(ext) - 1 if ext else 255
        filename = name[:max_name_len] + ('.' + ext if ext else '')
    
    return filename


def validate_attachment_type(content_type: str, allowed_types: Optional[List[str]] = None) -> tuple[bool, str]:
    """
    Validate attachment content type.
    Returns (is_valid, error_message_or_empty)
    """
    if allowed_types is None:
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/webp',
            'text/plain',
            'text/csv',
            'text/html',
            'application/zip',
            'application/x-zip-compressed',
        ]
    
    if content_type not in allowed_types:
        return False, f"File type '{content_type}' not allowed"
    
    return True, ""


def validate_attachment_size(size_bytes: int, max_size_mb: int = 25) -> tuple[bool, str]:
    """
    Validate attachment size.
    Returns (is_valid, error_message_or_empty)
    """
    max_bytes = max_size_mb * 1024 * 1024
    
    if size_bytes > max_bytes:
        return False, f"File too large (max {max_size_mb}MB)"
    
    return True, ""
