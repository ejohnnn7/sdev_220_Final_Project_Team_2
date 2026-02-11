import tkinter as tk
from tkinter import ttk, messagebox

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

book_listbox = tk.Listbox(books_tab, width=50)
book_listbox.grid(row=4, column=0, columnspan=3, pady=10)


def add_book():
    book_id = book_id_entry.get()
    title = title_entry.get()
    author = author_entry.get()

    if book_id in books:
        messagebox.showerror("Error", "Book already exists")
        return

    books[book_id] = Book(book_id, title, author)
    book_listbox.insert(tk.END, f"{book_id} - {title} by {author}")


def remove_book():
    selected = book_listbox.curselection()
    if not selected:
        return
    book_id = list(books.keys())[selected[0]]
    del books[book_id]
    book_listbox.delete(selected)


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

    members[member_id] = Member(member_id, name)
    member_listbox.insert(tk.END, f"{member_id} - {name}")


tk.Button(members_tab, text="Add Member", command=add_member).grid(row=3, column=0, pady=5)

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

    if book_id not in books or member_id not in members:
        messagebox.showerror("Error", "Invalid book or member")
        return

    loans.append(Loan(book_id, member_id))
    loan_listbox.insert(tk.END, f"Book {book_id} loaned to Member {member_id}")


tk.Button(loans_tab, text="Add Loan", command=add_loan).grid(row=3, column=0, pady=5)

root.mainloop()