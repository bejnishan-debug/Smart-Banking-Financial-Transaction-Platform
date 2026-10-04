from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import wraps
import time
import re
import threading


customers = []
accounts = []
transactions = []
transaction_counter = 1


# =========================
# Helper Functions
# =========================

def require_authorization(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        code = input("Enter authorization code: ")

        if code != "BANK123":
            print("Unauthorized access.")
            return

        return func(*args, **kwargs)

    return wrapper


def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except Exception as e:
            print(f"[ERROR] {func.__name__}: {e}")
            return None

    return wrapper


def find_account(account_id):
    for account in accounts:
        if account.get_account_id() == account_id:
            return account

    return None


def find_customer(customer_id):
    for customer in customers:
        if customer.get_customer_id() == customer_id:
            return customer

    return None


def get_customer_accounts(customer_id):
    customer_accounts = []

    for account in accounts:
        if account.get_customer_id() == customer_id:
            customer_accounts.append(account)

    return customer_accounts


def record_transaction(account_id, transaction_type, amount):
    global transaction_counter

    transaction = Transaction.create_transaction(
        f"T{transaction_counter:03}",
        account_id,
        transaction_type,
        amount
    )

    if not transaction.is_valid():
        print("Invalid transaction.")
        return

    transactions.append(transaction)

    save_transactions_to_file()

    transaction_counter += 1


def transaction_generator():
    for transaction in transactions:
        yield transaction


def validate_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.fullmatch(pattern, email) is not None


def validate_phone(phone):
    pattern = r"^\d{10}$"
    return re.fullmatch(pattern, phone) is not None


def validate_amount(amount_input):
    try:
        amount = float(amount_input)

    except ValueError:
        print("Invalid amount.")
        return False

    if amount <= 0:
        print("Amount must be greater than 0.")
        return False

    return amount


def confirm_action(message):
    confirmation = input(
        f"{message} (yes/no): "
    ).strip().lower()

    return confirmation == "yes"


def display_customer(customer):
    print(customer)
    print("----------------------------")


def display_account(account):
    print(account)
    print("----------------------------")


def display_transaction(transaction):
    print(transaction)
    print("----------------------------")


def display_balance(account):
    print("Account ID:", account.get_account_id())
    print("Account Type:", account.get_account_type())
    print("Current Balance:", account.get_balance())
    print("Status:", account.get_status())


def display_account_summary():
    print("Total Accounts:", len(accounts))

    active_count = 0
    inactive_count = 0
    total_balance = 0

    for account in accounts:
        if account.is_active():
            active_count += 1
        else:
            inactive_count += 1

        total_balance += account.get_balance()

    print("Active Accounts:", active_count)
    print("Inactive Accounts:", inactive_count)
    print("Total Balance:", total_balance)


# =========================
# Banking Operations
# =========================

def create_account():
    customer_id = input(
        "Enter Customer ID: "
    ).strip()

    customer = find_customer(customer_id)

    if customer is None:
        print("Customer not found.")
        return

    account_type = input(
        "Enter Account Type (Savings/Current): "
    ).strip().title()

    if not Account.validate_account_type(account_type):
        print("Invalid account type.")
        return

    initial_deposit_input = input(
        "Enter Initial Deposit Amount: "
    ).strip()

    initial_deposit = validate_amount(
        initial_deposit_input
    )

    if initial_deposit is False:
        return

    if accounts:
        number = max(
            int(account.get_account_id()[1:])
            for account in accounts
        ) + 1
    else:
        number = 1

    while True:
        account_id = Account.generate_account_id(number)

        if find_account(account_id) is None:
            break

        number += 1

    if not Account.validate_account_id(account_id):
        print("Invalid Account ID.")
        return

    try:
        account = Account(
            account_id,
            customer_id,
            account_type,
            initial_deposit
        )

        accounts.append(account)
        save_accounts_to_file()

    except (ValueError, OSError) as e:
        print("Error while creating account:", e)
        return

    print(account.account_info())
    print("Account created successfully.")
    print("Account ID:", account_id)


def display_customers():
    if not customers:
        print("No customers found.")
        return

    print("Total Customers:", len(customers))

    for customer in customers:
        display_customer(customer)


def display_accounts():
    if not accounts:
        print("No accounts found.")
        return

    display_account_summary()

    for account in accounts:
        display_account(account)


def log_activity(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"\n[LOG] Starting: {func.__name__}")

        result = func(*args, **kwargs)

        print(f"[LOG] Completed: {func.__name__}")

        return result

    return wrapper


def check_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("[CHECK] Function validation started")

        result = func(*args, **kwargs)

        print("[CHECK] Function validation completed")

        return result

    return wrapper


def log_level(level):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f"[{level}] Starting: {func.__name__}")

            result = func(*args, **kwargs)

            print(f"[{level}] Completed: {func.__name__}")

            return result

        return wrapper

    return decorator


def execution_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        result = func(*args, **kwargs)

        end_time = time.time()

        elapsed = end_time - start_time

        print(
            f"[TIME] Execution time for "
            f"{func.__name__}: {elapsed:.4f} seconds"
        )

        return result

    return wrapper


def audit_log(message):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f"[AUDIT] {message}")

            try:
                return func(*args, **kwargs)

            except Exception as e:
                print(f"[AUDIT] Error: {e}")
                return None

        return wrapper

    return decorator


@handle_errors
@log_activity
@check_function
@log_level("INFO")
@execution_time
@audit_log("Customer deposit operation")
def deposit_money():
    account_id = input(
        "Enter Account ID: "
    ).strip()

    if not Account.validate_account_id(account_id):
        print("Invalid Account ID. Format should be A001.")
        return

    account = find_account(account_id)

    if account is None:
        print("Account not found.")
        return

    if not account.is_active():
        print("Account is not active.")
        return

    amount_input = input(
        "Enter deposit amount: "
    ).strip()

    amount = validate_amount(amount_input)

    if amount is False:
        return

    try:
        result = account.process_transaction(amount)

        if result == "Deposit successful":
            print("Deposit successful.")
            print("New balance:", account.get_balance())

        else:
            print("Deposit failed.")
            return

        record_transaction(
            account_id,
            "Deposit",
            amount
        )

        save_accounts_to_file()

        print("Transaction recorded successfully.")

    except (ValueError, OSError) as e:
        print("Error while processing deposit:", e)


@handle_errors
@log_activity
@check_function
@log_level("INFO")
@execution_time
@require_authorization
@audit_log("Customer withdrawal operation")
def withdraw_money():
    account_id = input(
        "Enter Account ID: "
    ).strip()

    if not Account.validate_account_id(account_id):
        print("Invalid Account ID. Format should be A001.")
        return

    account = find_account(account_id)

    if account is None:
        print("Account not found.")
        return

    if not account.is_active():
        print("Account is not active.")
        return

    amount_input = input(
        "Enter withdrawal amount: "
    ).strip()

    amount = validate_amount(amount_input)

    if amount is False:
        return

    try:
        result = account.process_transaction(-amount)

        if result == "Withdrawal successful":
            print("Withdrawal successful.")
            print("New balance:", account.get_balance())

        else:
            print("Withdrawal failed.")
            return

        record_transaction(
            account_id,
            "Withdrawal",
            amount
        )

        save_accounts_to_file()

        print("Transaction recorded successfully.")

    except (ValueError, OSError) as e:
        print("Error while processing withdrawal:", e)


def transaction_history():
    if not transactions:
        print("No transactions found.")
        return

    print("Total Transactions:", len(transactions))

    total_deposit = 0
    total_withdrawal = 0
    total_transfer_out = 0
    total_transfer_in = 0

    transaction_iterator = TransactionIterator(transactions)

    for transaction in transaction_iterator:
        transaction_type = transaction.get_transaction_type()

        if transaction_type == "Deposit":
            total_deposit += transaction.get_amount()

        elif transaction_type == "Withdrawal":
            total_withdrawal += transaction.get_amount()

        elif transaction_type == "Transfer Out":
            total_transfer_out += transaction.get_amount()

        elif transaction_type == "Transfer In":
            total_transfer_in += transaction.get_amount()

    print("Total Deposited:", total_deposit)
    print("Total Withdrawn:", total_withdrawal)
    print("Total Transfer Out:", total_transfer_out)
    print("Total Transfer In:", total_transfer_in)

    account_id = input(
        "Enter Account ID to filter transactions: "
    ).strip()

    if not Account.validate_account_id(account_id):
        print("Invalid Account ID. Format should be A001.")
        return

    transaction_type = input(
        "Enter Transaction Type "
        "(Deposit/Withdrawal/Transfer Out/Transfer In/"
        "Account Deactivation/Account Reactivation): "
    ).strip().title()

    if transaction_type not in [
        "Deposit",
        "Withdrawal",
        "Account Deactivation",
        "Account Reactivation",
        "Transfer Out",
        "Transfer In"
    ]:
        print("Invalid transaction type.")
        return

    transaction_found = False

    generator = transaction_generator()

    for transaction in generator:
        if (
            transaction.get_account_id() == account_id
            and
            transaction.get_transaction_type() == transaction_type
        ):
            transaction_found = True
            display_transaction(transaction)

    if not transaction_found:
        print("No matching transactions found.")


def view_account_balance():
    account_id = input(
        "Enter Account ID: "
    ).strip()

    if not Account.validate_account_id(account_id):
        print("Invalid Account ID. Format should be A001.")
        return

    account = find_account(account_id)

    if account is None:
        print("Account not found.")
        return

    display_balance(account)


def deactivate_account():
    account_id = input(
        "Enter Account ID: "
    ).strip()

    if not Account.validate_account_id(account_id):
        print("Invalid Account ID. Format should be A001.")
        return

    account = find_account(account_id)

    if account is None:
        print("Account not found.")
        return

    if not account.is_active():
        print("Account is already inactive.")
        return

    if account.deactivate():
        print("Account deactivated successfully.")
    else:
        print("Account deactivation failed.")
        return

    record_transaction(
        account_id,
        "Account Deactivation",
        0
    )

    save_accounts_to_file()

    print("Deactivation transaction recorded.")


def reactivate_account():
    account_id = input(
        "Enter Account ID: "
    ).strip()

    if not Account.validate_account_id(account_id):
        print("Invalid Account ID. Format should be A001.")
        return

    account = find_account(account_id)

    if account is None:
        print("Account not found.")
        return

    if account.is_active():
        print("Account is already active.")
        return

    if account.reactivate():
        print("Account reactivated successfully.")
    else:
        print("Account reactivation failed.")
        return

    record_transaction(
        account_id,
        "Account Reactivation",
        0
    )

    save_accounts_to_file()

    print("Reactivation transaction recorded.")


def customer_account_lookup():
    customer_id = input(
        "Enter Customer ID: "
    ).strip()

    if not Customer.validate_customer_id(customer_id):
        print("Invalid Customer ID. Format should be C001.")
        return

    customer = find_customer(customer_id)

    if customer is None:
        print("Customer not found.")
        return

    customer_accounts = get_customer_accounts(
        customer_id
    )

    if not customer_accounts:
        print("This customer has no accounts.")
        return

    for account in customer_accounts:
        display_account(account)


def search_customer():
    customer_id = input(
        "Enter Customer ID: "
    ).strip()

    customer = find_customer(customer_id)

    if customer is None:
        print("Customer not found.")
        return

    display_customer(customer)


@require_authorization
def delete_customer():
    customer_id = input(
        "Enter Customer ID: "
    ).strip()

    if not Customer.validate_customer_id(customer_id):
        print("Invalid Customer ID. Format should be C001.")
        return

    customer = find_customer(customer_id)

    if customer is None:
        print("Customer not found.")
        return

    has_account = False

    for account in accounts:
        if account.get_customer_id() == customer_id:
            has_account = True
            break

    if has_account:
        print(
            "Customer cannot be deleted because "
            "an account exists."
        )
        return

    if not confirm_action(
        "Are you sure you want to delete this customer?"
    ):
        print("Customer deletion cancelled.")
        return

    customers.remove(customer)

    save_customers_to_file()

    print("Customer deleted successfully.")


def update_customer():
    customer_id = input(
        "Enter Customer ID: "
    ).strip()

    if not Customer.validate_customer_id(customer_id):
        print("Invalid Customer ID. Format should be C001.")
        return

    customer = find_customer(customer_id)

    if customer is None:
        print("Customer not found.")
        return

    if not confirm_action(
        "Are you sure you want to update this customer?"
    ):
        print("Customer update cancelled.")
        return

    new_name = input(
        "Enter new name: "
    ).strip()

    if not new_name:
        print("Name cannot be empty.")
        return

    new_email = input(
        "Enter new email: "
    ).strip()

    if not validate_email(new_email):
        print("Invalid email format.")
        return

    new_phone = input(
        "Enter new phone: "
    ).strip()

    if not validate_phone(new_phone):
        print("Invalid phone number.")
        return

    customer.set_name(new_name)
    customer.set_email(new_email)
    customer.set_phone(new_phone)

    save_customers_to_file()

    print("Customer updated successfully.")


def show_account_info(account):
    print(account.account_info())


@handle_errors
@require_authorization
def transfer_money():
    sender_id = input(
        "Enter Sender Account ID: "
    ).strip()

    if not Account.validate_account_id(sender_id):
        print("Invalid Sender Account ID. Format should be A001.")
        return

    sender = find_account(sender_id)

    if sender is None:
        print("Sender account not found.")
        return

    if not sender.is_active():
        print("Sender account is inactive.")
        return

    receiver_id = input(
        "Enter Receiver Account ID: "
    ).strip()

    if not Account.validate_account_id(receiver_id):
        print("Invalid Receiver Account ID. Format should be A001.")
        return

    receiver = find_account(receiver_id)

    if receiver is None:
        print("Receiver account not found.")
        return

    if not receiver.is_active():
        print("Receiver account is inactive.")
        return

    if sender_id == receiver_id:
        print("Sender and receiver accounts cannot be the same.")
        return

    amount_input = input(
        "Enter Transfer Amount: "
    ).strip()

    amount = validate_amount(amount_input)

    if amount is False:
        print("Invalid transfer amount.")
        return

    if sender.get_balance() < amount:
        print("Insufficient balance.")
        return

    if not confirm_action(
        f"Transfer {amount} from {sender_id} to {receiver_id}"
    ):
        print("Transfer cancelled.")
        return

    try:
        if not sender.withdraw(amount):
            print("Transfer failed.")
            return

        if not receiver.deposit(amount):
            sender.deposit(amount)
            print("Transfer failed. Amount restored to sender.")
            return

        record_transaction(
            sender_id,
            "Transfer Out",
            amount
        )

        record_transaction(
            receiver_id,
            "Transfer In",
            amount
        )

        save_accounts_to_file()

        print("Transfer successful.")
        print(
            "Sender new balance:",
            sender.get_balance()
        )
        print(
            "Receiver new balance:",
            receiver.get_balance()
        )

    except (ValueError, OSError) as e:
        print("Error while processing transfer:", e)


# =========================
# File Handling
# =========================

def save_customers_to_file():
    try:
        with open("customers.txt", "w") as file:
            for customer in customers:
                file.write(
                    f"{customer.get_customer_id()},"
                    f"{customer.get_name()},"
                    f"{customer.get_email()},"
                    f"{customer.get_phone()}\n"
                )

    except OSError:
        print("Error while saving customer data.")


def load_customers_from_file():
    customers.clear()

    try:
        with open("customers.txt", "r") as file:
            for line in file:
                if not line.strip():
                    continue

                try:
                    (
                        customer_id,
                        name,
                        email,
                        phone
                    ) = line.strip().split(",")

                    if not Customer.validate_customer_id(
                        customer_id
                    ):
                        print(
                            "Invalid customer ID found. "
                            "Skipping line."
                        )
                        continue

                    customer = Customer(
                        customer_id,
                        name,
                        email,
                        phone
                    )

                    customers.append(customer)

                except ValueError:
                    print(
                        "Invalid customer data found. "
                        "Skipping line."
                    )
                    continue

    except FileNotFoundError:
        pass

    except OSError:
        print("Error while reading customer data.")


def save_accounts_to_file():
    try:
        with open("accounts.txt", "w") as file:
            for account in accounts:
                file.write(
                    f"{account.get_account_id()},"
                    f"{account.get_customer_id()},"
                    f"{account.get_account_type()},"
                    f"{account.get_balance()},"
                    f"{account.get_status()}\n"
                )

    except OSError:
        print("Error while saving account data.")


def load_accounts_from_file():
    accounts.clear()

    try:
        with open("accounts.txt", "r") as file:
            for line in file:
                if not line.strip():
                    continue

                try:
                    (
                        account_id,
                        customer_id,
                        account_type,
                        balance,
                        status
                    ) = line.strip().split(",")

                    if not Account.validate_account_id(
                        account_id
                    ):
                        print(
                            "Invalid account ID found. "
                            "Skipping line."
                        )
                        continue

                    if find_customer(customer_id) is None:
                        print(
                            "Customer not found for account. "
                            "Skipping line."
                        )
                        continue

                    if not Account.validate_account_type(
                        account_type
                    ):
                        print(
                            "Invalid account type found. "
                            "Skipping line."
                        )
                        continue

                    balance = float(balance)

                    account = Account(
                        account_id,
                        customer_id,
                        account_type,
                        balance
                    )

                    if not account.set_status(status):
                        print(
                            "Invalid account status found. "
                            "Skipping line."
                        )
                        continue

                    accounts.append(account)

                except ValueError:
                    print(
                        "Invalid account data found. "
                        "Skipping line."
                    )
                    continue

    except FileNotFoundError:
        pass

    except OSError:
        print("Error while reading account data.")


def save_transactions_to_file():
    try:
        with open("transactions.txt", "w") as file:
            for transaction in transactions:
                file.write(
                    f"{transaction.get_transaction_id()},"
                    f"{transaction.get_account_id()},"
                    f"{transaction.get_transaction_type()},"
                    f"{transaction.get_amount()},"
                    f"{transaction.get_date_time().isoformat()}\n"
                )

    except OSError:
        print("Error while saving transaction data.")


def load_transactions_from_file():
    global transaction_counter

    transactions.clear()

    try:
        with open("transactions.txt", "r") as file:
            for line in file:
                if not line.strip():
                    continue

                try:
                    (
                        transaction_id,
                        account_id,
                        transaction_type,
                        amount,
                        date_time
                    ) = line.strip().split(",")

                    if not Account.validate_account_id(
                        account_id
                    ):
                        print(
                            "Invalid account ID found. "
                            "Skipping line."
                        )
                        continue

                    if transaction_type not in [
                        "Deposit",
                        "Withdrawal",
                        "Account Deactivation",
                        "Account Reactivation",
                        "Transfer Out",
                        "Transfer In"
                    ]:
                        print(
                            "Invalid transaction type found. "
                            "Skipping line."
                        )
                        continue

                    amount = float(amount)

                    if transaction_type in [
                        "Deposit",
                        "Withdrawal",
                        "Transfer Out",
                        "Transfer In"
                    ] and amount <= 0:
                        print(
                            "Invalid transaction amount. "
                            "Skipping line."
                        )
                        continue

                    if transaction_type in [
                        "Account Deactivation",
                        "Account Reactivation"
                    ] and amount != 0:
                        print(
                            "Invalid transaction amount. "
                            "Skipping line."
                        )
                        continue

                    transaction = Transaction(
                        transaction_id,
                        account_id,
                        transaction_type,
                        amount,
                        datetime.fromisoformat(date_time)
                    )

                    if not transaction.is_valid():
                        print(
                            "Invalid transaction found. "
                            "Skipping line."
                        )
                        continue

                    transactions.append(transaction)

                except ValueError:
                    print(
                        "Invalid transaction data found. "
                        "Skipping line."
                    )
                    continue

    except FileNotFoundError:
        pass

    except OSError:
        print("Error while reading transaction data.")

    if transactions:
        transaction_counter = max(
            int(transaction.get_transaction_id()[1:])
            for transaction in transactions
        ) + 1


# =========================
# Classes
# =========================

class Customer:

    def __init__(
        self,
        customer_id,
        name,
        email,
        phone
    ):
        self.__customer_id = customer_id
        self.__name = name
        self.__email = email
        self.__phone = phone

    def __str__(self):
        return (
            f"Customer ID: {self.get_customer_id()}\n"
            f"Name: {self.get_name()}\n"
            f"Email: {self.get_email()}\n"
            f"Phone: {self.get_phone()}"
        )

    def get_customer_id(self):
        return self.__customer_id

    def get_name(self):
        return self.__name

    def get_email(self):
        return self.__email

    def get_phone(self):
        return self.__phone

    def set_name(self, name):
        self.__name = name

    def set_email(self, email):
        self.__email = email

    def set_phone(self, phone):
        self.__phone = phone

    @classmethod
    def create_default_customer(cls, customer_id):
        return cls(
            customer_id,
            "Unknown",
            "unknown@email.com",
            "0000000000"
        )

    @classmethod
    def generate_customer_id(cls, number):
        return f"C{number:03}"

    @staticmethod
    def validate_customer_id(customer_id):
        pattern = r"^C\d{3}$"
        return re.fullmatch(pattern, customer_id) is not None


class BankAccount(ABC):

    @abstractmethod
    def account_info(self):
        pass

    @abstractmethod
    def process_transaction(self, amount):
        pass


class Account(BankAccount):

    def __init__(
        self,
        account_id,
        customer_id,
        account_type,
        balance
    ):
        self.__account_id = account_id
        self.__customer_id = customer_id
        self.__account_type = account_type
        self.__balance = balance
        self.__status = "active"

    def __str__(self):
        return (
            f"Account ID: {self.get_account_id()}\n"
            f"Customer ID: {self.get_customer_id()}\n"
            f"Account Type: {self.get_account_type()}\n"
            f"Balance: {self.get_balance()}\n"
            f"Status: {self.get_status()}"
        )

    def deposit(self, amount):
        if amount <= 0:
            return False

        self.__balance += amount
        return True

    def withdraw(self, amount):
        if amount <= 0:
            return False

        if amount > self.__balance:
            return False

        self.__balance -= amount
        return True

    def deactivate(self):
        if self.get_status() == "inactive":
            return False

        return self.set_status("inactive")

    def reactivate(self):
        if self.get_status() == "active":
            return False

        return self.set_status("active")

    def get_balance(self):
        return self.__balance

    def is_active(self):
        return self.get_status() == "active"

    def get_account_type(self):
        return self.__account_type

    def get_account_id(self):
        return self.__account_id

    def get_customer_id(self):
        return self.__customer_id

    def get_status(self):
        return self.__status

    def set_status(self, status):
        if status in ["active", "inactive"]:
            self.__status = status
            return True

        return False

    def account_info(self):
        return "This is a customer bank account"

    def process_transaction(self, amount):
        if amount > 0:
            if self.deposit(amount):
                return "Deposit successful"
            else:
                return "Deposit failed"

        elif amount < 0:
            if self.get_balance() >= abs(amount):
                if self.withdraw(abs(amount)):
                    return "Withdrawal successful"
                else:
                    return "Withdrawal failed"
            else:
                return "Insufficient balance"

        else:
            return "Invalid transaction amount"

    @classmethod
    def generate_account_id(cls, number):
        return f"A{number:03}"

    @staticmethod
    def validate_account_id(account_id):
        if not account_id.startswith("A"):
            return False

        if len(account_id) != 4:
            return False

        return account_id[1:].isdigit()

    @staticmethod
    def validate_account_type(account_type):
        account_type = account_type.strip().title()

        if account_type in ["Savings", "Current"]:
            return True

        return False


class SavingsAccount(Account):

    def account_info(self):
        return "This is a savings account"


class CurrentAccount(Account):

    def account_info(self):
        return "This is a current account"


class TransactionIterator:

    def __init__(self, transactions):
        self.transactions = transactions
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < len(self.transactions):
            transaction = self.transactions[self.index]
            self.index += 1
            return transaction

        raise StopIteration


@dataclass
class Transaction:

    transaction_id: str
    account_id: str
    transaction_type: str
    amount: float = 0.0
    date_time: datetime = field(
        default_factory=datetime.now
    )

    @classmethod
    def create_transaction(
        cls,
        transaction_id,
        account_id,
        transaction_type,
        amount
    ):
        return cls(
            transaction_id,
            account_id,
            transaction_type,
            amount
        )

    def __str__(self):
        return (
            f"Transaction ID: {self.transaction_id}\n"
            f"Account ID: {self.account_id}\n"
            f"Transaction Type: {self.transaction_type}\n"
            f"Amount: {self.amount}\n"
            f"Date/Time: "
            f"{self.date_time.strftime('%d-%m-%Y %I:%M %p')}"
        )

    def is_valid(self):

        if not Account.validate_account_id(
            self.account_id
        ):
            return False

        if find_account(self.account_id) is None:
            return False

        if self.transaction_type not in [
            "Deposit",
            "Withdrawal",
            "Account Deactivation",
            "Account Reactivation",
            "Transfer Out",
            "Transfer In"
        ]:
            return False

        if self.transaction_type in [
            "Deposit",
            "Withdrawal",
            "Transfer Out",
            "Transfer In"
        ]:
            return self.amount > 0

        if self.transaction_type in [
            "Account Deactivation",
            "Account Reactivation"
        ]:
            return self.amount == 0

        return False

    def get_transaction_id(self):
        return self.transaction_id

    def get_account_id(self):
        return self.account_id

    def get_transaction_type(self):
        return self.transaction_type

    def get_amount(self):
        return self.amount

    def get_date_time(self):
        return self.date_time


# =========================
# Main Program
# =========================

if __name__ == "__main__":

    load_customers_from_file()
    load_accounts_from_file()
    load_transactions_from_file()

    while True:

        print("\n================================")
        print("       SMART BANKING SYSTEM")
        print("================================")

        print("1. Add Customer")
        print("2. Display Customers")
        print("3. Create Account")
        print("4. Display Accounts")
        print("5. Deposit Money")
        print("6. Withdraw Money")
        print("7. Transfer Money")
        print("8. Transaction History")
        print("9. View Account Balance")
        print("10. Deactivate Account")
        print("11. Reactivate Account")
        print("12. Customer Account Lookup")
        print("13. Search Customer")
        print("14. Delete Customer")
        print("15. Update Customer")
        print("16. Exit")
        print("17. Create Default Customer")

        choice = input(
            "Enter your choice: "
        ).strip()

        if choice == "1":

            print("\nAdd Customer selected")

            generate_id = input(
                "Generate Customer ID automatically? (yes/no): "
            ).strip().lower()

            if generate_id == "yes":

                if customers:
                    number = max(
                        int(
                            customer.get_customer_id()[1:]
                        )
                        for customer in customers
                    ) + 1
                else:
                    number = 1

                while True:
                    customer_id = (
                        Customer.generate_customer_id(number)
                    )

                    if find_customer(customer_id) is None:
                        break

                    number += 1

                print(
                    "Generated Customer ID:",
                    customer_id
                )

            else:

                customer_id = input(
                    "Customer ID: "
                ).strip()

                if not Customer.validate_customer_id(
                    customer_id
                ):
                    print("Invalid Customer ID.")
                    continue

            duplicate = False

            for customer in customers:
                if customer.get_customer_id() == customer_id:
                    duplicate = True
                    break

            if duplicate:
                print("Customer ID already exists.")
                continue

            name = input("Name: ").strip()

            if not name:
                print("Name cannot be empty.")
                continue

            email = input("Email: ").strip()

            if not validate_email(email):
                print("Invalid email format.")
                continue

            phone = input("Phone: ").strip()

            if not validate_phone(phone):
                print("Invalid phone number.")
                continue

            customer = Customer(
                customer_id,
                name,
                email,
                phone
            )

            customers.append(customer)

            save_customers_to_file()

            print("Customer added successfully.")

        elif choice == "2":

            print("\nDisplay Customers selected")
            display_customers()

        elif choice == "3":

            print("\nCreate Account selected")
            create_account()

        elif choice == "4":

            print("\nDisplay Accounts selected")
            display_accounts()

        elif choice == "5":

            print("\nDeposit Money selected")
            deposit_money()

        elif choice == "6":

            print("\nWithdraw Money selected")
            withdraw_money()

        elif choice == "7":

            print("\nTransfer Money selected")
            transfer_money()

        elif choice == "8":

            print("\nTransaction History selected")
            transaction_history()

        elif choice == "9":

            print("\nView Account Balance selected")
            view_account_balance()

        elif choice == "10":

            print("\nDeactivate Account selected")
            deactivate_account()

        elif choice == "11":

            print("\nReactivate Account selected")
            reactivate_account()

        elif choice == "12":

            print("\nCustomer Account Lookup selected")
            customer_account_lookup()

        elif choice == "13":

            print("\nSearch Customer selected")
            search_customer()

        elif choice == "14":

            print("\nDelete Customer selected")
            delete_customer()

        elif choice == "15":

            print("\nUpdate Customer selected")
            update_customer()

        elif choice == "16":

            print(
                "Thank you for using Smart Banking System"
            )
            break

        elif choice == "17":

            print(
                "\nCreate Default Customer selected"
            )

            customer_id = input(
                "Customer ID: "
            ).strip()

            if not Customer.validate_customer_id(
                customer_id
            ):
                print(
                    "Invalid Customer ID. "
                    "ID must start with C."
                )
                continue

            duplicate = False

            for customer in customers:
                if customer.get_customer_id() == customer_id:
                    duplicate = True
                    break

            if duplicate:
                print("Customer ID already exists.")
                continue

            customer = Customer.create_default_customer(
                customer_id
            )

            customers.append(customer)

            save_customers_to_file()

            print(
                "Default customer created successfully."
            )

            print(customer)

        else:

            print(
                "Invalid choice, please try again."
            )