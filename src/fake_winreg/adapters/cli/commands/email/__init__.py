"""Email sending CLI commands.

Provides commands for sending emails and notifications via SMTP.

Contents:
    * :func:`.send_email.cli_send_email` - Send email with optional HTML and attachments.
    * :func:`.send_notification.cli_send_notification` - Send simple plain-text notification.
"""

from __future__ import annotations

from ._common import filter_sentinels
from .send_email import cli_send_email
from .send_notification import cli_send_notification

__all__ = ["cli_send_email", "cli_send_notification", "filter_sentinels"]
