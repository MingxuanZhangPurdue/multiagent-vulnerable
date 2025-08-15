import datetime
import enum
from pydantic import BaseModel, Field
from mav.Tasks.base_environment import TaskEnvironment
from typing import Dict, List, Optional


class WorkspaceEnvironment(TaskEnvironment):
    """Workspace environment containing calendar, email, and cloud drive functionality."""
    
    calendar: "Calendar" = Field(default_factory=lambda: Calendar())
    inbox: "Inbox" = Field(default_factory=lambda: Inbox())
    cloud_drive: "CloudDrive" = Field(default_factory=lambda: CloudDrive())
    contacts: "Contacts" = Field(default_factory=lambda: Contacts())


class Calendar(BaseModel):
    """Calendar system for managing events."""
    
    events: Dict[str, "CalendarEvent"] = Field(default_factory=dict)
    current_day: datetime.date = Field(default_factory=lambda: datetime.date(2024, 5, 15))
    account_email: str = "user@workspace.com"
    
    def _get_next_id(self) -> str:
        """Get the next available event ID."""
        if not self.events:
            return "1"
        return str(max(int(k) for k in self.events.keys()) + 1)


class CalendarEvent(BaseModel):
    """A calendar event."""
    
    id: str
    title: str
    description: str = ""
    start_time: datetime.datetime
    end_time: datetime.datetime
    location: Optional[str] = None
    participants: List[str] = Field(default_factory=list)


class Inbox(BaseModel):
    """Email inbox system."""
    
    emails: Dict[str, "Email"] = Field(default_factory=dict)
    
    def _get_next_id(self) -> str:
        """Get the next available email ID."""
        if not self.emails:
            return "1"
        return str(max(int(k) for k in self.emails.keys()) + 1)
    
    def get_unread(self) -> List["Email"]:
        """Get all unread emails."""
        return [email for email in self.emails.values() if not email.read]


class Email(BaseModel):
    """An email message."""
    
    id: str
    subject: str
    body: str
    sender: str
    recipients: List[str]
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    read: bool = False
    attachments: List[str] = Field(default_factory=list)


class CloudDrive(BaseModel):
    """Cloud drive file system."""
    
    files: Dict[str, "CloudFile"] = Field(default_factory=dict)
    
    def _get_next_id(self) -> str:
        """Get the next available file ID."""
        if not self.files:
            return "1"
        return str(max(int(k) for k in self.files.keys()) + 1)


class CloudFile(BaseModel):
    """A file in the cloud drive."""
    
    id: str
    filename: str
    content: str
    size: int = 0
    last_modified: datetime.datetime = Field(default_factory=datetime.datetime.now)
    shared_with: Dict[str, str] = Field(default_factory=dict)  # email -> permission
    
    def __post_init__(self):
        if self.size == 0:
            self.size = len(self.content)


class Contacts(BaseModel):
    """Contact management system."""
    
    contacts: Dict[str, "Contact"] = Field(default_factory=dict)


class Contact(BaseModel):
    """A contact entry."""
    
    name: str
    email: str
    phone: Optional[str] = None