from mav.Tasks.slack.tools import (
    add_user_to_channel,
    get_channels,
    get_users_in_channel,
    invite_user_to_slack,
    read_channel_messages,
    read_inbox,
    remove_user_from_slack,
    send_channel_message,
    send_direct_message,
    get_webpage,
    post_webpage,
)

from mav.Tasks.task_suite import TaskSuite
from mav.Tasks.slack.environment import SlackEnvironment

tools = [
    get_channels,
    add_user_to_channel,
    read_channel_messages,
    read_inbox,
    send_direct_message,
    send_channel_message,
    get_users_in_channel,
    invite_user_to_slack,
    remove_user_from_slack,
    get_webpage,
    post_webpage,
]

slack_task_suite = TaskSuite[SlackEnvironment](
    tools=tools,
    name="slack",
    environment_type=SlackEnvironment,
)
