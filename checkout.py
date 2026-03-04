from datetime import date, timedelta
from database import get_connection
from book import set_book_checkout_status
from loan import Loan, add_loan

# Rules
LOAN_PERIOD_DAYS    = 14
MAX_BOOKS_PER_MEMBER = 3


def checkout_book(book_id: int, member_id: int) -> tuple[bool, str]:
    """
    Checks out a book to a member.

    Validates:
      - Book exists and is active
      - Book is not already checked out
      - Member exists and is active
      - Member has no outstanding fines
      - Member has not reached the checkout limit

    On success:
      - Creates a new loan record (checkout + due date)
      - Marks the book as checked out

    Returns:
      (True,  success message)  on success
      (False, error message)    on any validation or DB failure
    """
    conn = get_connection()
    cur  = conn.cursor()

    try:
        # Validate book
        cur.execute("""
            SELECT title, is_checked_out, active
            FROM books
            WHERE book_id = ?;
        """, (book_id,))
        book_row = cur.fetchone()

        if not book_row:
            return False, f"Book ID {book_id} does not exist."

        book_title, is_checked_out, book_active = book_row

        if not book_active:
            return False, f'Book "{book_title}" is inactive and cannot be checked out.'

        if is_checked_out:
            return False, f'Book "{book_title}" is already checked out.'

        # Validate member
        cur.execute("""
            SELECT first_name, last_name, fines_due, active
            FROM members
            WHERE member_id = ?;
        """, (member_id,))
        member_row = cur.fetchone()

        if not member_row:
            return False, f"Member ID {member_id} does not exist."

        first_name, last_name, fines_due, member_active = member_row
        full_name = f"{first_name} {last_name}".strip()

        if not member_active:
            return False, f'Member "{full_name}" is inactive and cannot check out books.'

        if fines_due > 0:
            return False, (
                f'Member "{full_name}" has an outstanding fine of ${fines_due:.2f}. '
                f"Please clear all fines before checking out."
            )

        # Enforce checkout limit
        cur.execute("""
            SELECT COUNT(*)
            FROM loans
            WHERE member_id = ? AND return_date IS NULL;
        """, (member_id,))
        open_loans = cur.fetchone()[0]

        if open_loans >= MAX_BOOKS_PER_MEMBER:
            return False, (
                f'Member "{full_name}" already has {open_loans} book(s) checked out '
                f"(limit is {MAX_BOOKS_PER_MEMBER})."
            )

    finally:
        conn.close()

    # Create the loan
    checkout_date = date.today()
    due_date      = checkout_date + timedelta(days=LOAN_PERIOD_DAYS)

    loan = Loan(
        book_id=book_id,
        member_id=member_id,
        checkout_date=checkout_date,
        due_date=due_date,
    )
    add_loan(loan)

    if loan.loan_id is None:
        return False, "Loan could not be created due to a database error."

    set_book_checkout_status(book_id, True)

    return True, (
        f'"{book_title}" checked out to {full_name}. '
        f"Due: {due_date.isoformat()} (Loan ID: {loan.loan_id})"
    )
