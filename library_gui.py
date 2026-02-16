import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

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


def add_member():
    member_id = member_id_entry.get()
    name = member_name_entry.get()

    if not member_id or not name:
        messagebox.showerror("Error", "All fields required")
        return

    if not messagebox.askyesno("Confirm", "Add this member?"):
        return

    members[member_id] = Member(member_id, name)
    member_listbox.insert(tk.END, f"{member_id} - {name}")

    messagebox.showinfo("Success", "Member added successfully")

    member_id_entry.delete(0, tk.END)
    member_name_entry.delete(0, tk.END)


# LOANS TAB
tk.Label(loans_tab, text="Book ID").grid(row=0, column=0, padx=5, pady=5)
tk.Label(loans_tab, text="Member ID").grid(row=1, column=0, padx=5, pady=5)

loan_book_entry = tk.Entry(loans_tab)
loan_member_entry = tk.Entry(loans_tab)

loan_book_entry.grid(row=0, column=1)
loan_member_entry.grid(row=1, column=1)

loan_listbox = tk.Listbox(loans_tab, width=50)
loan_listbox.grid(row=4, column=0, columnspan=3, pady=10)


def add_loan():
    book_id = loan_book_entry.get()
    member_id = loan_member_entry.get()

    if not book_id or not member_id:
        messagebox.showerror("Error", "All fields required")
        return

    if book_id not in books or member_id not in members:
        messagebox.showerror("Error", "Invalid book or member")
        return

    if not messagebox.askyesno("Confirm", "Create this loan?"):
        return

    loans.append(Loan(book_id, member_id))
    loan_listbox.insert(tk.END, f"Book {book_id} loaned to Member {member_id}")

    messagebox.showinfo("Success", "Loan added successfully")

    loan_book_entry.delete(0, tk.END)
    loan_member_entry.delete(0, tk.END)


tk.Button(loans_tab, text="Add Loan", command=add_loan).grid(row=3, column=0, pady=5)


load_books_from_db()

root.mainloop()
