"""Importing this package registers every core table on Base.metadata."""

from docu.db.base import Base
from docu.db.models.auth import AuthToken, Identity, Session
from docu.db.models.catalog import Template, Theme
from docu.db.models.documents import Document, DocumentAccess, DocumentRevision
from docu.db.models.platform import PlatformSettings, PromptVersion
from docu.db.models.threads import Message, Thread
from docu.db.models.turns import PendingInput, Turn
from docu.db.models.users import User
from docu.db.models.workspaces import Invitation, Membership, Workspace

__all__ = [
    "AuthToken",
    "Base",
    "Document",
    "DocumentAccess",
    "DocumentRevision",
    "Identity",
    "Invitation",
    "Membership",
    "Message",
    "PendingInput",
    "PlatformSettings",
    "PromptVersion",
    "Session",
    "Template",
    "Theme",
    "Thread",
    "Turn",
    "User",
    "Workspace",
]
