from mav.Tasks.workspace.tools import (
    # Calendar tools
    get_current_day,
    get_day_calendar_events,
    search_calendar_events,
    create_calendar_event,
    reschedule_calendar_event,
    add_calendar_event_participants,
    
    # Email tools
    search_emails,
    get_unread_emails,
    send_email,
    
    # Cloud drive tools
    list_files,
    search_files,
    search_files_by_filename,
    create_file,
    append_to_file,
    delete_file,
    share_file,
    
    # Contact tools
    search_contacts_by_name,
)

from mav.Tasks.task_suite import TaskSuite
from mav.Tasks.workspace.environment import WorkspaceEnvironment

from functools import partial
from deepdiff.diff import DeepDiff

tools = [
    # Calendar tools
    get_current_day,
    get_day_calendar_events,
    search_calendar_events,
    create_calendar_event,
    reschedule_calendar_event,
    add_calendar_event_participants,
    
    # Email tools
    search_emails,
    get_unread_emails,
    send_email,
    
    # Cloud drive tools
    list_files,
    search_files,
    search_files_by_filename,
    create_file,
    append_to_file,
    delete_file,
    share_file,
    
    # Contact tools
    search_contacts_by_name,
]

deepdiff_paths_to_exclude = [
    "root.inbox.sent",
    "root.inbox.received", 
    "root.inbox.drafts",
    "root.responses",
    "root.model_fields_set",
    "root.calendar.initial_events",
    "root.inbox.initial_emails",
    "root.cloud_drive.initial_files",
]

WorkspaceDeepDiff = partial(DeepDiff, exclude_paths=deepdiff_paths_to_exclude)

workspace_task_suite = TaskSuite[WorkspaceEnvironment](
    tools=tools,
    name="workspace",
    environment_type=WorkspaceEnvironment
)