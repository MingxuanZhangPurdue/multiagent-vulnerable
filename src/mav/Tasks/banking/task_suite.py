from mav.Tasks.banking.tools import (
    get_balance,
    get_iban,
    get_most_recent_transactions,
    get_scheduled_transactions,
    schedule_transaction,
    send_money,
    update_scheduled_transaction,
    read_file,
    get_user_info, 
    update_password, 
    update_user_info
)

tools = [
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
]