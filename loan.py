from database import get_connection
from datetime import date, timedelta
import sqlite3

class Loan:
    def __init__(self, book_id, member_id, checkout_date, due_date, return_date=None, loan_id=None):
        self.loan_id = loan_id
        self.book_id = book_id
        self.member_id = member_id
        self.checkout_date = checkout_date
        self.due_date = due_date
        self.return_date = return_date

    def is_overdue(self, today):
        """Returns True if the loan is overdue and not yet returned."""
        return self.return_date is None and today > self.due_date

    def days_overdue(self, today):
        """Returns the number of days overdue, or 0 if not overdue."""
        if not self.is_overdue(today):
            return 0
        return (today - self.due_date).days

    def close_loan(self, return_date):
        """Marks the loan as returned."""
        self.return_date = return_date


def add_loan(loan_obj):
    """Inserts a Loan object into the database."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO loans (book_id, member_id, checkout_date, due_date, return_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            loan_obj.book_id,
            loan_obj.member_id,
            loan_obj.checkout_date.isoformat(),
            loan_obj.due_date.isoformat(),
            loan_obj.return_date.isoformat() if loan_obj.return_date else None
        ))

        conn.commit()
        loan_obj.loan_id = cursor.lastrowid
        print(f"Loan created: ID {loan_obj.loan_id} (Book {loan_obj.book_id} -> Member {loan_obj.member_id})")

    except sqlite3.IntegrityError as e:
        print(f"Error: Could not create loan. {e}")
    finally:
        conn.close()


def return_loan(loan_id, return_date):
    """
    Records a return date on an open loan, closing it out.
    return_date: a datetime.date object
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE loans
            SET return_date = ?
            WHERE loan_id = ? AND return_date IS NULL
        ''', (return_date.isoformat(), loan_id))

        if cursor.rowcount == 0:
            print(f"No open loan found with ID {loan_id}")
        else:
            conn.commit()
            print(f"Loan {loan_id} returned on {return_date}")

    except sqlite3.Error as e:
        print(f"Error returning loan: {e}")
    finally:
        conn.close()


def search_loans_by_member(member_id, open_only=False):
    """
    Returns all loans for a given member.
    If open_only is True, only returns loans that have not been returned.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = '''
            SELECT loan_id, book_id, member_id, checkout_date, due_date, return_date
            FROM loans
            WHERE member_id = ?
        '''
        if open_only:
            query += ' AND return_date IS NULL'
        query += ' ORDER BY due_date ASC'

        cursor.execute(query, (member_id,))
        rows = cursor.fetchall()

    except sqlite3.Error as e:
        print(f"Search Error: {e}")
        return []
    finally:
        conn.close()

    return [_row_to_loan(row) for row in rows]


def search_loans_by_book(book_id, open_only=False):
    """
    Returns all loans for a given book.
    If open_only is True, only returns loans that have not been returned.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = '''
            SELECT loan_id, book_id, member_id, checkout_date, due_date, return_date
            FROM loans
            WHERE book_id = ?
        '''
        if open_only:
            query += ' AND return_date IS NULL'
        query += ' ORDER BY due_date ASC'

        cursor.execute(query, (book_id,))
        rows = cursor.fetchall()

    except sqlite3.Error as e:
        print(f"Search Error: {e}")
        return []
    finally:
        conn.close()

    return [_row_to_loan(row) for row in rows]


def get_overdue_loans(today):
    """
    Returns all loans that are overdue as of the given date.
    today: a datetime.date object
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT loan_id, book_id, member_id, checkout_date, due_date, return_date
            FROM loans
            WHERE return_date IS NULL AND due_date < ?
            ORDER BY due_date ASC
        ''', (today.isoformat(),))

        rows = cursor.fetchall()

    except sqlite3.Error as e:
        print(f"Search Error: {e}")
        return []
    finally:
        conn.close()

    return [
        Loan(
            loan_id=row[0],
            book_id=row[1],
            member_id=row[2],
            checkout_date=date.fromisoformat(row[3]),
            due_date=date.fromisoformat(row[4]),
            return_date=date.fromisoformat(row[5]) if row[5] else None
        )
        for row in rows
    ]


if __name__ == "__main__":
    from database import initialize_db

    initialize_db()

    checkout_date = date.today()
    due_date = checkout_date + timedelta(days=14)

    loan = Loan(book_id=1, member_id=1, checkout_date=checkout_date, due_date=due_date)
    add_loan(loan)

    # Test overdue logic
    test_date = due_date + timedelta(days=3)
    print("Is overdue:", loan.is_overdue(test_date))
    print("Days overdue:", loan.days_overdue(test_date))

    # Return the loan
    return_loan(loan.loan_id, test_date)