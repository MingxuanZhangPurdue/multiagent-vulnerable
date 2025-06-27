from agents import RunContextWrapper, function_tool

from mav.Tasks.v1.banking.environment import BankingEnvironment, Transaction

from mav.Tasks.v1.banking.tools.tools import (
    get_iban,
    send_money,
    schedule_transaction,
    update_scheduled_transaction,
    get_balance,
    get_most_recent_transactions,
    get_scheduled_transactions,
    read_file,
    get_user_info,
    update_password,
    update_user_info,
)

@function_tool(name_override="get_user_info")
def get_user_info_openai(
    wrapper: RunContextWrapper[BankingEnvironment],
) -> dict[str, str]:
    """
    Get the user information.
    """
    return get_user_info(wrapper.context)

@function_tool(name_override="update_password")
def update_password_openai(wrapper: RunContextWrapper[BankingEnvironment], password: str) -> dict[str, str]:
    """
    Update the user password.

    :param password: New password for the user
    """
    return update_password(wrapper.context, password)

@function_tool(name_override="update_user_info")
def update_user_info_openai(
    wrapper: RunContextWrapper[BankingEnvironment],
    first_name: str | None = None,
    last_name: str | None = None,
    street: str | None = None,
    city: str | None = None,
) -> dict[str, str]:
    """
    Update the user information.

    :param first_name: First name of the user (optional)
    :param last_name: Last name of the user (optional)
    :param street: Street of the user (optional)
    :param city: City of the user (optional)
    """
    return update_user_info(wrapper.context, first_name, last_name, street, city)

@function_tool(name_override="next_id")
def get_iban_openai(wrapper: RunContextWrapper[BankingEnvironment]) -> str:
    """Get the IBAN of the current bank account."""
    return get_iban(wrapper.context)

@function_tool(name_override="send_money")
def send_money_openai(
     wrapper: RunContextWrapper[BankingEnvironment], recipient: str, amount: float, subject: str, date: str
) -> dict[str, str]:
    """
    Sends a transaction to the recipient.

    :param recipient: IBAN of the recipient
    :param amount: Amount of the transaction
    :param subject: Subject of the transaction
    :param date: Date of the transaction
    """
    return send_money(wrapper.context, recipient, amount, subject, date)

@function_tool(name_override="schedule_transaction")
def schedule_transaction_openai(
    wrapper: RunContextWrapper[BankingEnvironment],
    recipient: str,
    amount: float,
    subject: str,
    date: str,
    recurring: bool,
) -> dict[str, str]:
    """
    Schedule a transaction.

    :param recipient: IBAN of the recipient
    :param amount: Amount of the transaction
    :param subject: Subject of the transaction
    :param date: Next date of the transaction
    :param recurring: Is the transaction recurring
    """
    return schedule_transaction(wrapper.context, recipient, amount, subject, date, recurring)

@function_tool(name_override="update_scheduled_transaction")
def update_scheduled_transaction_openai(
    account: RunContextWrapper[BankingEnvironment],
    id: int,
    recipient: str | None = None,
    amount: float | None = None,
    subject: str | None = None,
    date: str | None = None,
    recurring: bool | None = None,
) -> dict[str, str]:
    """
    Update a scheduled transaction.

    :param id: ID of the transaction (mandatory)
    :param recipient: IBAN of the recipient (optional)
    :param amount: Amount of the transaction (optional)
    :param subject: Subject of the transaction (optional)
    :param date: Next date of the transaction (optional)
    :param recurring: Is the transaction recurring (optional)
    """
    return update_scheduled_transaction(account.context, id, recipient, amount, subject, date, recurring)

@function_tool(name_override="get_balance")
def get_balance_openai(account: RunContextWrapper[BankingEnvironment]) -> float:
    """
    Get the balance of the account.
    """
    return get_balance(account.context)

@function_tool(name_override="get_most_recent_transactions")
def get_most_recent_transactions_openai(
    account: RunContextWrapper[BankingEnvironment], n: int = 100
) -> list[Transaction]:
    """
    Get the list of the most recent transactions, e.g. to summarize the last n transactions.

    :param n: Number of transactions to return
    """
    return get_most_recent_transactions(account.context, n)

@function_tool(name_override="get_scheduled_transactions")
def get_scheduled_transactions_openai(
    account: RunContextWrapper[BankingEnvironment],
) -> list[Transaction]:
    """
    Get the list of scheduled transactions.
    """
    return get_scheduled_transactions(account.context)

@function_tool(name_override="read_file")
def read_file_openai(wrapper: RunContextWrapper[BankingEnvironment], file_path: str) -> str:
    """
    Reads the contents of the file at the given path.

    :param file_path: The path to the file to read.
    """
    return read_file(wrapper.context, file_path)