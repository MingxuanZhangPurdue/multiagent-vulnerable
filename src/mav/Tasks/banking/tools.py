import json
from mav.Tasks.banking.environment import BankingEnvironment, Transaction

def get_user_info(
    environment: BankingEnvironment,
) -> str:
    """Get the user information."""
    return json.dumps({
        "first_name": environment.user_account.first_name,
        "last_name": environment.user_account.last_name,
        "street": environment.user_account.street,
        "city": environment.user_account.city,
    }, indent=2)

def update_password(
    environment: BankingEnvironment, 
    password: str
) -> str:
    """Update the user password.

    Args:
        password: New password for the user
    """
    environment.user_account.password = password
    return json.dumps({
        "message": "Password updated.",
    }, indent=2)

def update_user_info(
    environment: BankingEnvironment,
    first_name: str | None = None,
    last_name: str | None = None,
    street: str | None = None,
    city: str | None = None,
) -> str:
    """Update the user information.

    Args:
        first_name: First name of the user (optional)
        last_name: Last name of the user (optional)
        street: Street of the user (optional)
        city: City of the user (optional)
    """
    if first_name:
        environment.user_account.first_name = first_name
    if last_name:
        environment.user_account.last_name = last_name
    if street:
        environment.user_account.street = street
    if city:
        environment.user_account.city = city

    return json.dumps({
        "first_name": environment.user_account.first_name,
        "last_name": environment.user_account.last_name,
        "street": environment.user_account.street,
        "city": environment.user_account.city,
    }, indent=2)

def next_id(
    environment: BankingEnvironment,
) -> int:
    """Get the next ID for a transaction."""
    return (
        max(
            [t.id for t in environment.bank_account.transactions] + [t.id for t in environment.bank_account.scheduled_transactions],
            default=0,
        )
        + 1
    )

def set_balance(
    environment: BankingEnvironment, 
    balance: float
) -> str:
    """Set the balance of the account.

    Args:
        balance: New balance for the account
    """
    environment.bank_account.balance = balance
    return "Balance updated to " + str(balance)

def set_iban(
    environment: BankingEnvironment, 
    iban: str
) -> str:
    """Set the IBAN of the account.

    Args:
        iban: New IBAN for the account
    """
    environment.bank_account.iban = iban

    return "IBAN updated to " + iban

def get_iban(
    environment: BankingEnvironment
) -> str:
    """Get the IBAN of the current bank account."""
    return str(environment.bank_account.iban)

def send_money(
    environment: BankingEnvironment, 
    recipient: str, 
    amount: float, 
    subject: str, 
    date: str
) -> str:
    """Sends a transaction to the recipient.

    Args:
        recipient: IBAN of the recipient
        amount: Amount of the transaction
        subject: Subject of the transaction
        date: Date of the transaction
    """
    transaction = Transaction(
        id=next_id(environment),
        sender=get_iban(environment),
        recipient=recipient,
        amount=amount,
        subject=subject,
        date=date,
        recurring=False,
    )
    environment.bank_account.transactions.append(transaction)

    return json.dumps({
        "message": f"Transaction to {recipient} for {amount} sent.",
    }, indent=2)

def schedule_transaction(
    environment: BankingEnvironment,
    recipient: str,
    amount: float,
    subject: str,
    date: str,
    recurring: bool,
) -> str:
    """Schedule a transaction.

    Args:
        recipient: IBAN of the recipient
        amount: Amount of the transaction
        subject: Subject of the transaction
        date: Next date of the transaction
        recurring: Is the transaction recurring
    """
    transaction = Transaction(
        id=next_id(environment),
        sender=get_iban(environment),
        recipient=recipient,
        amount=amount,
        subject=subject,
        date=date,
        recurring=recurring,
    )
    environment.bank_account.scheduled_transactions.append(transaction)

    return json.dumps({
        "message": f"Transaction to {recipient} for {amount} scheduled.",
    }, indent=2)

def update_scheduled_transaction(
    environment: BankingEnvironment,
    id: int,
    recipient: str | None = None,
    amount: float | None = None,
    subject: str | None = None,
    date: str | None = None,
    recurring: bool | None = None,
) -> str:
    """Update a scheduled transaction.

    Args:
        id: ID of the transaction (mandatory)
        recipient: IBAN of the recipient (optional)
        amount: Amount of the transaction (optional)
        subject: Subject of the transaction (optional)
        date: Next date of the transaction (optional)
        recurring: Is the transaction recurring (optional)
    """
    transaction = next((t for t in environment.bank_account.scheduled_transactions if t.id == id), None)
    if transaction:
        if recipient:
            transaction.recipient = recipient
        if amount:
            transaction.amount = amount
        if subject:
            transaction.subject = subject
        if date:
            transaction.date = date
        if recurring:
            transaction.recurring = recurring
    else:
        raise ValueError(f"Transaction with ID {id} not found.")

    return json.dumps({
        "message": f"Transaction with ID {id} updated.",
    }, indent=2)

def get_balance(
    environment: BankingEnvironment
) -> str:
    """Get the balance of the account."""
    return str(environment.bank_account.balance)

def get_most_recent_transactions(
    environment: BankingEnvironment, 
    n: int = 100
) -> str:
    """ Get the list of the most recent transactions, e.g. to summarize the last n transactions.

    Args:
        n: Number of transactions to return
    """
    transactions = [t.model_dump() for t in environment.bank_account.transactions[-int(n) :]]
    return json.dumps(transactions, indent=2)

def get_scheduled_transactions(
    environment: BankingEnvironment,
) -> str:
    """Get the list of scheduled transactions."""
    transactions = [t.model_dump() for t in environment.bank_account.scheduled_transactions]
    return json.dumps(transactions, indent=2)

def read_file(
    environment: BankingEnvironment, 
    file_path: str
) -> str:
    """Reads the contents of the file at the given path.

    Args:
        file_path: The path to the file to read.
    """
    return environment.filesystem.files.get(file_path, "")