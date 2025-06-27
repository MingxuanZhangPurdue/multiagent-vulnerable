from mav.Tasks.v1.banking.environment import BankingEnvironment, Transaction

def get_user_info(
    environment: BankingEnvironment,
) -> dict[str, str]:
    """
    Get the user information.
    """
    return {
        "first_name": environment.user_account.first_name,
        "last_name": environment.user_account.last_name,
        "street": environment.user_account.street,
        "city": environment.user_account.city,
    }

def update_password(environment: BankingEnvironment, password: str) -> dict[str, str]:
    """
    Update the user password.

    :param password: New password for the user
    """
    environment.user_account.password = password
    return {
        "message": "Password updated.",
    }

def update_user_info(
    environment: BankingEnvironment,
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
    if first_name:
        environment.user_account.first_name = first_name
    if last_name:
        environment.user_account.last_name = last_name
    if street:
        environment.user_account.street = street
    if city:
        environment.user_account.city = city

    return {
        "first_name": environment.user_account.first_name,
        "last_name": environment.user_account.last_name,
        "street": environment.user_account.street,
        "city": environment.user_account.city,
    }

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

def set_balance(environment: BankingEnvironment, balance: float) -> None:
    """Set the balance of the account."""
    environment.bank_account.balance = balance

def set_iban(environment: BankingEnvironment, iban: str) -> None:
    """Set the IBAN of the account."""
    environment.bank_account.iban = iban

def get_iban(environment: BankingEnvironment) -> str:
    """Get the IBAN of the current bank account."""
    return environment.bank_account.iban

def send_money(
    environment: BankingEnvironment, recipient: str, amount: float, subject: str, date: str
) -> dict[str, str]:
    """
    Sends a transaction to the recipient.

    :param recipient: IBAN of the recipient
    :param amount: Amount of the transaction
    :param subject: Subject of the transaction
    :param date: Date of the transaction
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

    return {
        "message": f"Transaction to {recipient} for {amount} sent.",
    }

def schedule_transaction(
    environment: BankingEnvironment,
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

    return {
        "message": f"Transaction to {recipient} for {amount} scheduled.",
    }

def update_scheduled_transaction(
    environment: BankingEnvironment,
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

    return {
        "message": f"Transaction with ID {id} updated.",
    }

def get_balance(environment: BankingEnvironment) -> float:
    """
    Get the balance of the account.
    """
    return environment.bank_account.balance

def get_most_recent_transactions(
    environment: BankingEnvironment, n: int = 100
) -> list[Transaction]:
    """
    Get the list of the most recent transactions, e.g. to summarize the last n transactions.

    :param n: Number of transactions to return
    """
    return [t for t in environment.bank_account.transactions[-int(n) :]]

def get_scheduled_transactions(
    environment: BankingEnvironment,
) -> list[Transaction]:
    """
    Get the list of scheduled transactions.
    """
    return [t for t in environment.bank_account.scheduled_transactions]

def read_file(environment: BankingEnvironment, file_path: str) -> str:
    """
    Reads the contents of the file at the given path.

    :param file_path: The path to the file to read.
    """
    return environment.filesystem.files.get(file_path, "")