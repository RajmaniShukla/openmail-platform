"""
OpenMail Platform - Utilities
"""
from app.utils.email_parser import (
    parse_email,
    parse_address,
    parse_address_list,
    generate_snippet,
    extract_email_domain,
    is_valid_email,
    sanitize_html,
    generate_thread_id,
    ParsedEmail,
    ParsedAddress,
    ParsedAttachment,
)

from app.utils.validators import (
    validate_email_address,
    validate_email_list,
    validate_domain_name,
    validate_password_strength,
    validate_folder_name,
    validate_label_name,
    validate_color_hex,
    sanitize_filename,
    validate_attachment_type,
    validate_attachment_size,
)

__all__ = [
    # Email parser
    "parse_email",
    "parse_address",
    "parse_address_list",
    "generate_snippet",
    "extract_email_domain",
    "is_valid_email",
    "sanitize_html",
    "generate_thread_id",
    "ParsedEmail",
    "ParsedAddress",
    "ParsedAttachment",
    # Validators
    "validate_email_address",
    "validate_email_list",
    "validate_domain_name",
    "validate_password_strength",
    "validate_folder_name",
    "validate_label_name",
    "validate_color_hex",
    "sanitize_filename",
    "validate_attachment_type",
    "validate_attachment_size",
]
