from mav.Tasks.slack.environment import Message, SlackEnvironment

def get_channels(environment: SlackEnvironment) -> list[str]:
    """Get the list of channels in the slack."""
    return environment.slack.channels
    
def add_user_to_channel(environment: SlackEnvironment, user: str, channel: str) -> None:
    """Add a user to a given channel.

    :param user: The user to add to the channel.
    :param channel: The channel to add the user to.
    """
    if user not in environment.slack.users:
        raise ValueError(f"User {user} not found in the users list")
    if channel not in environment.slack.channels:
        raise ValueError(f"Channel {channel} not found in the channels list")
    environment.slack.user_channels[user].append(channel)


def read_channel_messages(environment: SlackEnvironment, channel: str) -> list[Message]:
    """Read the messages from the given channel.

    :param channel: The channel to read the messages from.
    """
    if channel not in environment.slack.channels:
        raise ValueError("Channel does not exist!")
    return environment.slack.channel_inbox.get(channel, [])


def read_inbox(environment: SlackEnvironment, user: str) -> list[Message]:
    """Read the messages from the given user inbox.

    :param user: The user whose inbox to read.
    """
    if user not in environment.slack.users:
        raise ValueError(f"User {user} not found in the users list")
    return environment.slack.user_inbox.get(user, [])


def send_direct_message(environment: SlackEnvironment, recipient: str, body: str) -> None:
    """Send a direct message from `author` to `recipient` with the given `content`.

    :param recipient: The recipient of the message.
    :param body: The body of the message.
    """
    sender = "bot"
    if recipient not in environment.slack.users:
        raise ValueError(f"Recipient {recipient} not found in the users list")
    msg = Message(sender=sender, recipient=recipient, body=body)
    if recipient not in environment.slack.user_inbox:
        environment.slack.user_inbox[recipient] = []
    environment.slack.user_inbox[recipient].append(msg)


def send_channel_message(environment: SlackEnvironment, channel: str, body: str) -> None:
    """Send a channel message from `author` to `channel` with the given `content`.

    :param channel: The channel to send the message to.
    :param body: The body of the message.
    """
    sender = "bot"
    if channel not in environment.slack.channels:
        raise ValueError(f"Channel {channel} not found in the channels list")
    msg = Message(sender=sender, recipient=channel, body=body)
    if channel not in environment.slack.channel_inbox:
        environment.slack.channel_inbox[channel] = []
    environment.slack.channel_inbox[channel].append(msg)


def invite_user_to_slack(environment: SlackEnvironment, user: str, user_email: str) -> None:
    """Invites a user to the Slack workspace.

    :param user: The user to invite.
    :param user_email: The user email where invite should be sent.
    """
    if user in environment.slack.users:
        raise ValueError(f"User {user} already in the users list")
    environment.slack.users.append(user)
    environment.slack.user_inbox[user] = []
    environment.slack.user_channels[user] = []


def remove_user_from_slack(environment: SlackEnvironment, user: str) -> None:
    """Remove a user from the Slack workspace.

    :param user: The user to remove.
    """
    if user not in environment.slack.users:
        raise ValueError(f"User {user} not found in the users list")
    environment.slack.users.remove(user)
    del environment.slack.user_inbox[user]
    del environment.slack.user_channels[user]


def get_users_in_channel(environment: SlackEnvironment, channel: str) -> list[str]:
    """Get the list of users in the given channel.

    :param channel: The channel to get the users from.
    """
    if channel not in environment.slack.channels:
        raise ValueError(f"Channel {channel} not found in the channels list")
    users = []
    for user, channels in environment.slack.user_channels.items():
        if channel in channels:
            users.append(user)
    return users

def standardize_url(url):
    if url.startswith("https://"):
        url = url[8:]
    if url.startswith("http://"):
        url = url[7:]
    return url

def post_webpage(environment: SlackEnvironment, url: str, content: str) -> None:
    """Posts a webpage at a given URL with the given content.

    :param url: The URL of the webpage.
    :param content: The content of the webpage.
    """
    url = standardize_url(url)
    environment.web.web_requests.append(url)
    environment.web.web_content[url] = content

def get_webpage(environment: SlackEnvironment, url: str) -> str | None:
    """Returns the content of the webpage at a given URL.

    :param url: The URL of the webpage.
    """
    url = standardize_url(url)
    environment.web.web_requests.append(url)
    if url not in environment.web.web_content:
        return "404 Not Found"
    return environment.web.web_content.get(url)
