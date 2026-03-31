"""Email adapter - SMTP email sending.

Provides the email sending adapter using btx_lib_mail.

Structure:
    * :mod:`.config` - Email configuration model and loader
    * :mod:`.transport` - SMTP send functions
    * :mod:`.sender` - Re-exports for backward compatibility

Contents:
    * :class:`.config.EmailConfig` - Email configuration container
    * :func:`.config.load_email_config_from_dict` - Config dict loader
    * :func:`.transport.send_email` - Primary email sending interface
    * :func:`.transport.send_notification` - Simple notification wrapper
"""

from __future__ import annotations

# Primary imports from specific modules
from .config import EmailConfig, load_email_config_from_dict
from .transport import send_email, send_notification

__all__ = [
    "EmailConfig",
    "send_email",
    "send_notification",
    "load_email_config_from_dict",
]
