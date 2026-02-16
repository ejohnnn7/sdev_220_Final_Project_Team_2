import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date, timedelta

#  CLASSES
class Book:
    def __init__(self, book_id, title, author):
        self.book_id = book_id
        self.title = title
        self.author = author


class Member:
    def __init__(self, member_id, name):
        self.member_id = member_id
        self.name = name


class Loan:
    def __init__(self, book_id, member_id):
        self.book_id = book_id
        self.member_id = member_id


# COLLECTIONS
books = {}
members = {}
loans = []


#  GUI
def get_connection():
    return sqlite3.connect("library.db")


LOAN_PERIOD_DAYS = 14
FINE_PER_DAY = 0.25
MAX_BOOKS_PER_MEMBER = 3


root = tk.Tk()
root.title("Library System")
root.geometry("600x500")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

books_tab = ttk.Frame(notebook)
members_tab = ttk.Frame(notebook)
loans_tab = ttk.Frame(notebook)

notebook.add(books_tab, text="Books")
notebook.add(members_tab, text="Members")
notebook.add(loans_tab, text="Loans")


# BOOKS TAB
tk.Label(books_tab, text="Book ID").grid(row=0, column=0, padx=5, pady=5)
tk.Label(books_tab, text="Title").grid(row=1, column=0, padx=5, pady=5)
tk.Label(books_tab, text="Author").grid(row=2, column=0, padx=5, pady=5)

book_id_entry = tk.Entry(books_tab)
title_entry = tk.Entry(books_tab)
author_entry = tk.Entry(books_tab)

book_id_entry.grid(row=0, column=1)
title_entry.grid(row=1, column=1)
author_entry.grid(row=2, column=1)

book_listbox = tk.Listbox(books_tab, width=60)
book_listbox.grid(row=4, column=0, columnspan=3, pady=10)


def load_books_from_db():
    book_listbox.delete(0, tk.END)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT book_id, book_code, title, author
        FROM books
        WHERE active = 1
        ORDER BY book_id;
    """)

    rows = cur.fetchall()
    conn.close()

    for book_id, book_code, title, author in rows:
        display_id = book_code if book_code else str(book_id)
        book_listbox.insert(tk.END, f"{display_id} - {title} by {author}")


def add_book():
    book_id = book_id_entry.get()
    title = title_entry.get()
    author = author_entry.get()

    if not book_id or not title or not author:
        messagebox.showerror("Error", "All fields required")
        return

    if not messagebox.askyesno("Confirm", "Add this book?"):
        return

    try:
        book_num = int(book_id)
    except ValueError:
        messagebox.showerror("Error", "Book ID must be a number")
        return

    book_code = f"B{book_num:03d}"

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO books (book_id, book_code, title, author, is_checked_out, active)
            VALUES (?, ?, ?, ?, 0, 1);
        """, (book_num, book_code, title, author))
        conn.commit()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Book ID already exists")
        return
    finally:
        conn.close()

    load_books_from_db()

    messagebox.showinfo("Success", "Book added successfully")

    book_id_entry.delete(0, tk.END)
    title_entry.delete(0, tk.END)
    author_entry.delete(0, tk.END)


def remove_book():
    selected = book_listbox.curselection()
    if not selected:
        return

    selected_text = book_listbox.get(selected[0])
    book_identifier = selected_text.split(" - ")[0]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT is_checked_out
        FROM books
        WHERE book_code = ? OR book_id = ?;
    """, (book_identifier, book_identifier))
    row = cur.fetchone()

    if row and row[0] == 1:
        conn.close()
        messagebox.showerror("Error", "Book is checked out. Return it first.")
        return

    cur.execute("""
        UPDATE books
        SET active = 0
        WHERE book_code = ? OR book_id = ?;
    """, (book_identifier, book_identifier))

    conn.commit()
    conn.close()

    load_books_from_db()


tk.Button(books_tab, text="Add Book", command=add_book).grid(row=3, column=0, pady=5)
tk.Button(books_tab, text="Remove Book", command=remove_book).grid(row=3, column=1, pady=5)


# MEMBERS TAB
tk.Label(members_tab, text="Member ID").grid(row=0, column=0, padx=5, pady=5)
tk.Label(members_tab, text="Name").grid(row=1, column=0, padx=5, pady=5)

member_id_entry = tk.Entry(members_tab)
member_name_entry = tk.Entry(members_tab)

member_id_entry.grid(row=0, column=1)
member_name_entry.grid(row=1, column=1)

member_listbox = tk.Listbox(members_tab, width=50)
member_listbox.grid(row=4, column=0, columnspan=3, pady=10)


def load_members_from_db():
    member_listbox.delete(0, tk.END)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT member_id, member_code, first_name, last_name
        FROM members
        WHERE active = 1
        ORDER BY member_id;
    """)

    rows = cur.fetchall()
    conn.close()

    for member_id, member_code, first_name, last_name in rows:
        display_id = member_code if member_code else str(member_id)
        full_name = f"{first_name} {last_name}".strip()
        member_listbox.insert(tk.END, f"{display_id} - {full_name}")


def add_member():
    member_id = member_id_entry.get().strip()
    name = member_name_entry.get().strip()

    if not member_id or not name:
        messagebox.showerror("Error", "All fields required")
        return

    if not messagebox.askyesno("Confirm", "Add this member?"):
        return

    try:
        member_num = int(member_id)
    except ValueError:
        messagebox.showerror("Error", "Member ID must be a number")
        return

    member_code = f"M{member_num:03d}"

    parts = name.split()
    first_name = parts[0]
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    conn = get_connection()
    cur = conn.cursor()

    # prevent duplicate member_code
    cur.execute("SELECT COUNT(*) FROM members WHERE member_code = ?;", (member_code,))
    if cur.fetchone()[0] > 0:
        conn.close()
        messagebox.showerror("Error", "Member ID already exists")
        return

    try:
        cur.execute("""
            INSERT INTO members (member_code, first_name, last_name, fines_due, active)
            VALUES (?, ?, ?, 0, 1);
        """, (member_code, first_name, last_name))
        conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Could not add member: {e}")
        return
    finally:
        conn.close()

    load_members_from_db()

    messagebox.showinfo("Success", "Member added successfully")

    member_id_entry.delete(0, tk.END)
    member_name_entry.delete(0, tk.END)


def remove_member():
    selected = member_listbox.curselection()
    if not selected:
        return

    if not messagebox.askyesno("Confirm", "Remove this member?"):
        return

    selected_text = member_listbox.get(selected[0])
    member_identifier = selected_text.split(" - ")[0]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT member_id
        FROM members
        WHERE member_code = ? OR member_id = ?;
    """, (member_identifier, member_identifier))
    row = cur.fetchone()

    if not row:
        conn.close()
        messagebox.showerror("Error", "Member not found")
        return

    member_id = row[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM loans
        WHERE member_id = ? AND return_date IS NULL;
    """, (member_id,))
    open_count = cur.fetchone()[0]

    if open_count > 0:
        conn.close()
        messagebox.showerror("Error", "Member has open loans. Return books first.")
        return

    cur.execute("""
        UPDATE members
        SET active = 0
        WHERE member_id = ?;
    """, (member_id,))

    conn.commit()
    conn.close()

    load_members_from_db()

    messagebox.showinfo("Success", "Member removed successfully")


tk.Button(members_tab, text="Add Member", command=add_member).grid(row=3, column=0, pady=5)
tk.Button(members_tab, text="Remove Member", command=remove_member).grid(row=3, column=1, pady=5)


# LOANS TAB
tk.Label(loans_tab, text="Book ID").grid(row=0, column=0, padx=5, pady=5)
tk.Label(loans_tab, text="Member ID").grid(row=1, column=0, padx=5, pady=5)

loan_book_entry = tk.Entry(loans_tab)
loan_member_entry = tk.Entry(loans_tab)

loan_book_entry.grid(row=0, column=1)
loan_member_entry.grid(row=1, column=1)

loan_listbox = tk.Listbox(loans_tab, width=60)
loan_listbox.grid(row=4, column=0, columnspan=3, pady=10)


def load_open_loans_from_db():
    loan_listbox.delete(0, tk.END)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT l.loan_id, b.book_code, m.member_code, l.due_date
        FROM loans l
        JOIN books b ON b.book_id = l.book_id
        JOIN members m ON m.member_id = l.member_id
        WHERE l.return_date IS NULL
        ORDER BY l.due_date ASC;
    """)

    rows = cur.fetchall()
    conn.close()

    for loan_id, book_code, member_code, due_date in rows:
        loan_listbox.insert(tk.END, f"{loan_id} - {book_code} -> {member_code} (Due: {due_date})")


def add_loan():
    book_id_text = loan_book_entry.get()
    member_id_text = loan_member_entry.get()

    if not book_id_text or not member_id_text:
        messagebox.showerror("Error", "All fields required")
        return

    if not messagebox.askyesno("Confirm", "Create this loan?"):
        return

    try:
        book_id = int(book_id_text)
        member_id = int(member_id_text)
    except ValueError:
        messagebox.showerror("Error", "Book ID and Member ID must be a number")
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT is_checked_out, active
        FROM books
        WHERE book_id = ?;
    """, (book_id,))
    book_row = cur.fetchone()

    if not book_row:
        conn.close()
        messagebox.showerror("Error", "Invalid book")
        return

    if book_row[1] != 1:
        conn.close()
        messagebox.showerror("Error", "Book is not active")
        return

    if book_row[0] == 1:
        conn.close()
        messagebox.showerror("Error", "Book is already checked out")
        return

    cur.execute("""
        SELECT active
        FROM members
        WHERE member_id = ?;
    """, (member_id,))
    member_row = cur.fetchone()

    if not member_row:
        conn.close()
        messagebox.showerror("Error", "Invalid member")
        return

    if member_row[0] != 1:
        conn.close()
        messagebox.showerror("Error", "Member is not active")
        return

    cur.execute("""
        SELECT COUNT(*)
        FROM loans
        WHERE member_id = ? AND return_date IS NULL;
    """, (member_id,))
    open_loans_count = cur.fetchone()[0]

    if open_loans_count >= MAX_BOOKS_PER_MEMBER:
        conn.close()
        messagebox.showerror("Error", f"Member already has {MAX_BOOKS_PER_MEMBER} books checked out")
        return

    checkout_date = date.today()
    due_date = checkout_date + timedelta(days=LOAN_PERIOD_DAYS)

    try:
        cur.execute("""
            INSERT INTO loans (book_id, member_id, checkout_date, due_date, return_date)
            VALUES (?, ?, ?, ?, NULL);
        """, (book_id, member_id, checkout_date.isoformat(), due_date.isoformat()))

        cur.execute("""
            UPDATE books
            SET is_checked_out = 1
            WHERE book_id = ?;
        """, (book_id,))

        conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Could not create loan: {e}")
    finally:
        conn.close()

    load_open_loans_from_db()
    load_books_from_db()

    messagebox.showinfo("Success", "Loan added successfully")

    loan_book_entry.delete(0, tk.END)
    loan_member_entry.delete(0, tk.END)


def remove_loan():
    selected = loan_listbox.curselection()
    if not selected:
        return

    if not messagebox.askyesno("Confirm", "Return this loan?"):
        return

    selected_text = loan_listbox.get(selected[0])
    loan_id_text = selected_text.split(" - ")[0]

    try:
        loan_id = int(loan_id_text)
    except ValueError:
        messagebox.showerror("Error", "Could not read selected loan")
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT book_id, member_id, due_date
        FROM loans
        WHERE loan_id = ? AND return_date IS NULL;
    """, (loan_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        messagebox.showerror("Error", "Loan not found (or already returned)")
        return

    book_id = row[0]
    member_id = row[1]
    due_date_str = row[2]
    due_dt = date.fromisoformat(due_date_str)

    return_dt = date.today()
    days_overdue = (return_dt - due_dt).days
    if days_overdue < 0:
        days_overdue = 0
    fine = round(days_overdue * FINE_PER_DAY, 2)

    try:
        cur.execute("""
            UPDATE loans
            SET return_date = ?
            WHERE loan_id = ? AND return_date IS NULL;
        """, (return_dt.isoformat(), loan_id))

        cur.execute("""
            UPDATE books
            SET is_checked_out = 0
            WHERE book_id = ?;
        """, (book_id,))

        # add fine to member fines_due if overdue
        if fine > 0:
            cur.execute("""
                UPDATE members
                SET fines_due = fines_due + ?
                WHERE member_id = ?;
            """, (fine, member_id))

        conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Could not return loan: {e}")
        conn.close()
        return

    conn.close()

    load_open_loans_from_db()
    load_books_from_db()

    if fine > 0:
        messagebox.showinfo("Returned", f"Returned successfully.\nDays overdue: {days_overdue}\nFine: ${fine}")
    else:
        messagebox.showinfo("Returned", "Returned successfully.\nFine: $0.00")


tk.Button(loans_tab, text="Add Loan", command=add_loan).grid(row=3, column=0, pady=5)
tk.Button(loans_tab, text="Remove Loan", command=remove_loan).grid(row=3, column=1, pady=5)


load_books_from_db()
load_members_from_db()
load_open_loans_from_db()

root.mainloop()
