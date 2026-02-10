from datetime import date

# Class Loan implementation
class Loan:
    def __init__(self, loan_id, book_id, member_id, checkout_date, due_date, return_date=None):
        self.loan_id = loan_id
        self.book_id = book_id
        self.member_id = member_id
        self.checkout_date = checkout_date
        self.due_date = due_date
        self.return_date = return_date

    def is_overdue(self, today):
        """
        Returns True if the loan is overdue and not yet returned.
        """
        return self.return_date is None and today > self.due_date

    def days_overdue(self, today):
        """
        Returns the number of days overdue.
        Returns 0 if the book is not overdue.
        """
        if not self.is_overdue(today):
            return 0
        return (today - self.due_date).days

    def close_loan(self, return_date):
        """
        Marks the loan as returned.
        """
        self.return_date = return_date


# --- Execution Examples ---
if __name__ == "__main__":
    from datetime import timedelta

    checkout_date = date(2026, 2, 1)
    due_date = checkout_date + timedelta(days=14)

    # Create a new loan
    loan = Loan(
        loan_id=1,
        book_id=101,
        member_id=1001,
        checkout_date=checkout_date,
        due_date=due_date
    )

    # Test overdue logic
    test_date = due_date + timedelta(days=3)
    print("Is overdue:", loan.is_overdue(test_date))       # Expected: True
    print("Days overdue:", loan.days_overdue(test_date))   # Expected: 3

    # Close the loan
    loan.close_loan(test_date)
    print("Is overdue after return:", loan.is_overdue(test_date))  # Expected: False
