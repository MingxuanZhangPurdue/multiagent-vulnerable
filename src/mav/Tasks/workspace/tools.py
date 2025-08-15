"""Workspace tools for calendar, email, and cloud drive operations."""

import datetime
from typing import List, Dict, Optional, Any
from mav.Tasks.workspace.environment import WorkspaceEnvironment, CalendarEvent, Email, CloudFile


def get_current_day(environment: WorkspaceEnvironment) -> Dict[str, Any]:
    """Get the current day."""
    return {"current_day": environment.calendar.current_day.isoformat()}


def get_day_calendar_events(environment: WorkspaceEnvironment, day: str) -> Dict[str, Any]:
    """Get all calendar events for a specific day."""
    target_date = datetime.date.fromisoformat(day)
    events = []
    
    for event in environment.calendar.events.values():
        if event.start_time.date() == target_date:
            events.append({
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "start_time": event.start_time.isoformat(),
                "end_time": event.end_time.isoformat(),
                "location": event.location,
                "participants": event.participants,
            })
    
    return {"events": events}


def search_calendar_events(
    environment: WorkspaceEnvironment, 
    query: str, 
    date: Optional[str] = None
) -> Dict[str, Any]:
    """Search for calendar events by query and optionally by date."""
    events = []
    target_date = None
    if date:
        target_date = datetime.date.fromisoformat(date)
    
    for event in environment.calendar.events.values():
        # Check if query matches title or description
        if query.lower() in event.title.lower() or query.lower() in event.description.lower():
            # If date filter is specified, check date match
            if target_date is None or event.start_time.date() == target_date:
                events.append({
                    "id": event.id,
                    "title": event.title,
                    "description": event.description,
                    "start_time": event.start_time.isoformat(),
                    "end_time": event.end_time.isoformat(),
                    "location": event.location,
                    "participants": event.participants,
                })
    
    return {"events": events}


def create_calendar_event(
    environment: WorkspaceEnvironment,
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: Optional[str] = None,
    participants: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create a new calendar event."""
    event_id = environment.calendar._get_next_id()
    
    # Parse datetime strings
    start_dt = datetime.datetime.fromisoformat(start_time.replace(" ", "T"))
    end_dt = datetime.datetime.fromisoformat(end_time.replace(" ", "T"))
    
    if participants is None:
        participants = []
    
    # Add the account email to participants if not already present
    if environment.calendar.account_email not in participants:
        participants.append(environment.calendar.account_email)
    
    event = CalendarEvent(
        id=event_id,
        title=title,
        description=description,
        start_time=start_dt,
        end_time=end_dt,
        location=location,
        participants=participants,
    )
    
    environment.calendar.events[event_id] = event
    
    # Send notification email
    email_id = environment.inbox._get_next_id()
    notification_email = Email(
        id=email_id,
        subject=f"Event Created: {title}",
        body=f"Event '{title}' has been created for {start_time} - {end_time}",
        sender="calendar@workspace.com",
        recipients=[environment.calendar.account_email],
        timestamp=datetime.datetime.now(),
        read=False,
    )
    environment.inbox.emails[email_id] = notification_email
    
    return {"event_id": event_id, "status": "created"}


def reschedule_calendar_event(
    environment: WorkspaceEnvironment,
    event_id: str,
    new_start_time: str
) -> Dict[str, Any]:
    """Reschedule a calendar event to a new start time."""
    if event_id not in environment.calendar.events:
        return {"error": "Event not found"}
    
    event = environment.calendar.events[event_id]
    old_start = event.start_time
    duration = event.end_time - event.start_time
    
    # Parse new start time
    new_start_dt = datetime.datetime.fromisoformat(new_start_time.replace(" ", "T"))
    new_end_dt = new_start_dt + duration
    
    event.start_time = new_start_dt
    event.end_time = new_end_dt
    
    # Send notification email
    email_id = environment.inbox._get_next_id()
    notification_email = Email(
        id=email_id,
        subject=f"Event Rescheduled: {event.title}",
        body=f"Event '{event.title}' has been rescheduled from {old_start.isoformat()} to {new_start_time}",
        sender="calendar@workspace.com",
        recipients=[environment.calendar.account_email],
        timestamp=datetime.datetime.now(),
        read=False,
    )
    environment.inbox.emails[email_id] = notification_email
    
    return {"status": "rescheduled"}


def add_calendar_event_participants(
    environment: WorkspaceEnvironment,
    event_id: str,
    participants: List[str]
) -> Dict[str, Any]:
    """Add participants to a calendar event."""
    if event_id not in environment.calendar.events:
        return {"error": "Event not found"}
    
    event = environment.calendar.events[event_id]
    
    for participant in participants:
        if participant not in event.participants:
            event.participants.append(participant)
    
    return {"status": "participants_added"}


def search_emails(
    environment: WorkspaceEnvironment,
    query: str,
    sender: Optional[str] = None
) -> Dict[str, Any]:
    """Search for emails by query and optionally by sender."""
    emails = []
    
    for email in environment.inbox.emails.values():
        # Check if query matches subject or body
        query_match = (query.lower() in email.subject.lower() or 
                      query.lower() in email.body.lower())
        
        # Check sender filter if provided
        sender_match = sender is None or sender.lower() in email.sender.lower()
        
        if query_match and sender_match:
            emails.append({
                "id": email.id,
                "subject": email.subject,
                "body": email.body,
                "sender": email.sender,
                "recipients": email.recipients,
                "timestamp": email.timestamp.isoformat(),
                "read": email.read,
                "attachments": email.attachments,
            })
    
    return {"emails": emails}


def get_unread_emails(environment: WorkspaceEnvironment) -> Dict[str, Any]:
    """Get all unread emails and mark them as read."""
    unread_emails = []
    
    for email in environment.inbox.emails.values():
        if not email.read:
            unread_emails.append({
                "id": email.id,
                "subject": email.subject,
                "body": email.body,
                "sender": email.sender,
                "recipients": email.recipients,
                "timestamp": email.timestamp.isoformat(),
                "attachments": email.attachments,
            })
            # Mark as read
            email.read = True
    
    return {"emails": unread_emails}


def send_email(
    environment: WorkspaceEnvironment,
    recipients: List[str],
    subject: str,
    body: str,
    attachments: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Send an email."""
    email_id = environment.inbox._get_next_id()
    
    if attachments is None:
        attachments = []
    
    email = Email(
        id=email_id,
        subject=subject,
        body=body,
        sender=environment.calendar.account_email,
        recipients=recipients,
        timestamp=datetime.datetime.now(),
        read=True,  # Sent emails are marked as read
        attachments=attachments,
    )
    
    environment.inbox.emails[email_id] = email
    
    return {"email_id": email_id, "status": "sent"}


def list_files(environment: WorkspaceEnvironment) -> Dict[str, Any]:
    """List all files in the cloud drive."""
    files = []
    
    for file in environment.cloud_drive.files.values():
        files.append({
            "id": file.id,
            "filename": file.filename,
            "size": file.size,
            "last_modified": file.last_modified.isoformat(),
            "shared_with": file.shared_with,
        })
    
    return {"files": files}


def search_files(environment: WorkspaceEnvironment, query: str) -> Dict[str, Any]:
    """Search for files by filename or content."""
    files = []
    
    for file in environment.cloud_drive.files.values():
        if (query.lower() in file.filename.lower() or 
            query.lower() in file.content.lower()):
            files.append({
                "id": file.id,
                "filename": file.filename,
                "content": file.content,
                "size": file.size,
                "last_modified": file.last_modified.isoformat(),
                "shared_with": file.shared_with,
            })
    
    return {"files": files}


def search_files_by_filename(environment: WorkspaceEnvironment, filename: str) -> Dict[str, Any]:
    """Search for files by exact filename match."""
    files = []
    
    for file in environment.cloud_drive.files.values():
        if file.filename.lower() == filename.lower():
            files.append({
                "id": file.id,
                "filename": file.filename,
                "content": file.content,
                "size": file.size,
                "last_modified": file.last_modified.isoformat(),
                "shared_with": file.shared_with,
            })
    
    return {"files": files}


def create_file(
    environment: WorkspaceEnvironment,
    filename: str,
    content: str
) -> Dict[str, Any]:
    """Create a new file in the cloud drive."""
    file_id = environment.cloud_drive._get_next_id()
    
    file = CloudFile(
        id=file_id,
        filename=filename,
        content=content,
        size=len(content),
        last_modified=datetime.datetime.now(),
        shared_with={},
    )
    
    environment.cloud_drive.files[file_id] = file
    
    return {"file_id": file_id, "status": "created"}


def append_to_file(
    environment: WorkspaceEnvironment,
    file_id: str,
    content: str
) -> Dict[str, Any]:
    """Append content to an existing file."""
    if file_id not in environment.cloud_drive.files:
        return {"error": "File not found"}
    
    file = environment.cloud_drive.files[file_id]
    file.content += "\n" + content
    file.size = len(file.content)
    file.last_modified = datetime.datetime.now()
    
    return {"status": "content_appended"}


def delete_file(environment: WorkspaceEnvironment, file_id: str) -> Dict[str, Any]:
    """Delete a file from the cloud drive."""
    if file_id not in environment.cloud_drive.files:
        return {"error": "File not found"}
    
    del environment.cloud_drive.files[file_id]
    
    return {"status": "deleted"}


def share_file(
    environment: WorkspaceEnvironment,
    file_id: str,
    email: str,
    permission: str
) -> Dict[str, Any]:
    """Share a file with another user."""
    if file_id not in environment.cloud_drive.files:
        return {"error": "File not found"}
    
    file = environment.cloud_drive.files[file_id]
    file.shared_with[email] = permission
    
    return {"status": "shared"}


def search_contacts_by_name(environment: WorkspaceEnvironment, query: str) -> Dict[str, Any]:
    """Search for contacts by name."""
    contacts = []
    
    for contact in environment.contacts.contacts.values():
        if query.lower() in contact.name.lower():
            contacts.append({
                "name": contact.name,
                "email": contact.email,
                "phone": contact.phone,
            })
    
    return {"contacts": contacts}
