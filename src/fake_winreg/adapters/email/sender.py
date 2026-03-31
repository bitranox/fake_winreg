"""Email sending adapter wrapping btx_lib_mail with typed configuration.

This module re-exports components from config.py and transport.py for
backward compatibility. New code should import from the specific submodules.

Contents:
    * :class:`.config.EmailConfig` - Validated email configuration model.
    * :func:`.config.load_email_config_from_dict` - Config dict loader.
    * :func:`.transport.send_email` - Primary email sending interface.
    * :func:`.transport.send_notification` - Simple notification wrapper.
"""

from __future__ import annotations

# Re-export from config module
from .config import EmailConfig, load_email_config_from_dict

# Re-export from transport module
from .transport import send_email, send_notification

__all__ = [
    "EmailConfig",
    "send_email",
    "send_notification",
    "load_email_config_from_dict",
]
