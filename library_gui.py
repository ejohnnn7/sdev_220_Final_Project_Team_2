import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta

from database import initialize_db, get_connection
from book import Book, add_book, set_book_checkout_status, set_book_active_status
from member import Member, add_member, set_member_active_status, sync_fines
from loan import return_loan as db_return_loan, FINE_PER_DAY
from checkout import checkout_book


#ROOT WINDOW
root = tk.Tk()
root.title("Library System")
root.geometry("1200x600")
root.resizable(True, True)

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both", padx=8, pady=8)

books_tab    = ttk.Frame(notebook)
members_tab  = ttk.Frame(notebook)
loans_tab    = ttk.Frame(notebook)
checkout_tab = ttk.Frame(notebook)

notebook.add(books_tab,    text="  Books  ")
notebook.add(members_tab,  text=" Members ")
notebook.add(loans_tab,    text="  Loans  ")
notebook.add(checkout_tab, text=" Checkout ")


# Build a styled Treeview
def make_treeview(parent, columns: list[tuple], row: int, columnspan: int = 3) -> ttk.Treeview:
    """
    columns: list of (col_id, heading, width) tuples.
    Returns the Treeview widget (already gridded with a scrollbar).
    """
    frame = ttk.Frame(parent)
    frame.grid(row=row, column=0, columnspan=columnspan, sticky="nsew", padx=5, pady=8)
    parent.grid_rowconfigure(row, weight=1)
    parent.grid_columnconfigure(0, weight=1)

    col_ids = [c[0] for c in columns]
    tv = ttk.Treeview(frame, columns=col_ids, show="headings", selectmode="browse")

    for col_id, heading, width in columns:
        tv.heading(col_id, text=heading)
        tv.column(col_id, width=width, anchor="w", minwidth=width, stretch=True)

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=vsb.set)

    tv.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    return tv


#  BOOKS TAB

# Add form
tk.Label(books_tab, text="Add Title").grid(row=0, column=0, padx=5, pady=5, sticky="e")
tk.Label(books_tab, text="Add Author").grid(row=1, column=0, padx=5, pady=5, sticky="e")
title_entry  = tk.Entry(books_tab, width=30)
author_entry = tk.Entry(books_tab, width=30)
title_entry.grid(row=0, column=1, sticky="w")
author_entry.grid(row=1, column=1, sticky="w")

# Search bar
book_search_var = tk.StringVar()
tk.Label(books_tab, text="Search").grid(row=2, column=0, padx=5, pady=(8, 2), sticky="e")
ttk.Entry(books_tab, textvariable=book_search_var, width=30).grid(row=2, column=1, sticky="w", pady=(8, 2))

book_show_inactive = tk.BooleanVar(value=False)

book_tree = make_treeview(
    books_tab,
    columns=[
        ("book_id", "Book ID", 65),
        ("title",   "Title",   260),
        ("author",  "Author",  200),
        ("status",  "Status",  110),
    ],
    row=4,
    columnspan=3,
)


def load_books_from_db(filter_text=""):
    book_tree.delete(*book_tree.get_children())
    conn = get_connection()
    cur  = conn.cursor()
    like = f"%{filter_text}%"
    if book_show_inactive.get():
        cur.execute("""
            SELECT book_id, title, author, is_checked_out, active FROM books
            WHERE title LIKE ? OR author LIKE ? OR CAST(book_id AS TEXT) LIKE ?
            ORDER BY active DESC, book_id;
        """, (like, like, like))
    else:
        cur.execute("""
            SELECT book_id, title, author, is_checked_out, 1 AS active FROM books
            WHERE active = 1 AND (title LIKE ? OR author LIKE ? OR CAST(book_id AS TEXT) LIKE ?)
            ORDER BY book_id;
        """, (like, like, like))
    for book_id, title, author, checked, active in cur.fetchall():
        if active:
            status = "Checked Out" if checked else "Available"
            tag    = "out" if checked else "avail"
        else:
            status = "Inactive"
            tag    = "inactive"
        book_tree.insert("", "end", iid=str(book_id),
                         values=(book_id, title, author, status), tags=(tag,))
    conn.close()
    book_tree.tag_configure("out",      foreground="#b00020")
    book_tree.tag_configure("avail",    foreground="#1a7a1a")
    book_tree.tag_configure("inactive", foreground="#999999")

book_search_var.trace_add("write", lambda *_: load_books_from_db(book_search_var.get()))


def add_book_cmd():
    title  = title_entry.get().strip()
    author = author_entry.get().strip()
    if not title or not author:
        messagebox.showerror("Error", "Title and Author are required")
        return
    if not messagebox.askyesno("Confirm", f'Add "{title}" by {author}?'):
        return

    book_obj = Book(title=title, author=author)
    add_book(book_obj)

    if book_obj.book_id is None:
        messagebox.showerror("Error", "Could not add book (duplicate or DB error)")
        return

    load_books_from_db(book_search_var.get())
    messagebox.showinfo("Success", f'Book "{title}" added (ID {book_obj.book_id})')
    title_entry.delete(0, tk.END)
    author_entry.delete(0, tk.END)


def inactivate_book_cmd():
    selected = book_tree.selection()
    if not selected:
        messagebox.showwarning("Select", "Please select a book first")
        return

    book_id = int(selected[0])
    vals    = book_tree.item(selected[0], "values")
    title, status = vals[1], vals[3]

    if status == "Inactive":
        messagebox.showwarning("Already Inactive", f'"{title}" is already inactive.')
        return
    if status == "Checked Out":
        messagebox.showerror("Error", "Book is checked out. Return it first.")
        return
    if not messagebox.askyesno("Confirm", f'Inactivate "{title}"?'):
        return

    set_book_active_status(book_id, False)
    load_books_from_db(book_search_var.get())
    messagebox.showinfo("Inactivated", f'"{title}" has been inactivated.')


def reactivate_book_cmd():
    selected = book_tree.selection()
    if not selected:
        messagebox.showwarning("Select", "Please select a book first")
        return

    book_id = int(selected[0])
    vals    = book_tree.item(selected[0], "values")
    title, status = vals[1], vals[3]

    if status != "Inactive":
        messagebox.showwarning("Not Inactive", f'"{title}" is already active.')
        return
    if not messagebox.askyesno("Confirm", f'Reactivate "{title}"?'):
        return

    set_book_active_status(book_id, True)
    load_books_from_db(book_search_var.get())
    messagebox.showinfo("Reactivated", f'"{title}" has been reactivated.')


btn_frame_books = ttk.Frame(books_tab)
btn_frame_books.grid(row=3, column=0, columnspan=3, pady=4)
ttk.Button(btn_frame_books, text="Add Book",        command=add_book_cmd).pack(side="left", padx=6)
ttk.Button(btn_frame_books, text="Inactivate Book", command=inactivate_book_cmd).pack(side="left", padx=6)
ttk.Button(btn_frame_books, text="Reactivate Book", command=reactivate_book_cmd).pack(side="left", padx=6)
ttk.Checkbutton(btn_frame_books, text="Show Inactive",
                variable=book_show_inactive, command=lambda: load_books_from_db(book_search_var.get())).pack(side="left", padx=10)


#  MEMBERS TAB

# Add form
tk.Label(members_tab, text="Add Name").grid(row=0, column=0, padx=5, pady=5, sticky="e")
member_name_entry = tk.Entry(members_tab, width=30)
member_name_entry.grid(row=0, column=1, sticky="w")

# Search bar
member_search_var = tk.StringVar()
tk.Label(members_tab, text="Search").grid(row=1, column=0, padx=5, pady=(8, 2), sticky="e")
ttk.Entry(members_tab, textvariable=member_search_var, width=30).grid(row=1, column=1, sticky="w", pady=(8, 2))

member_show_inactive = tk.BooleanVar(value=False)

member_tree = make_treeview(
    members_tab,
    columns=[
        ("member_id",  "Member ID", 75),
        ("first_name", "First",     140),
        ("last_name",  "Last",      140),
        ("fines_due",  "Fines Due", 90),
        ("status",     "Status",    80),
    ],
    row=3,
    columnspan=3,
)


def load_members_from_db(filter_text=""):
    member_tree.delete(*member_tree.get_children())
    conn = get_connection()
    cur  = conn.cursor()
    like = f"%{filter_text}%"
    try:
        exact_id = int(filter_text)
    except ValueError:
        exact_id = -1
    if member_show_inactive.get():
        cur.execute("""
            SELECT member_id, first_name, last_name, fines_due, active FROM members
            WHERE member_id = ? OR first_name LIKE ? OR last_name LIKE ?
            ORDER BY active DESC, member_id;
        """, (exact_id, like, like))
    else:
        cur.execute("""
            SELECT member_id, first_name, last_name, fines_due, 1 AS active FROM members
            WHERE active = 1 AND (member_id = ? OR first_name LIKE ? OR last_name LIKE ?)
            ORDER BY member_id;
        """, (exact_id, like, like))
    for member_id, first_name, last_name, fines, active in cur.fetchall():
        fine_str = f"${fines:.2f}"
        status   = "Active" if active else "Inactive"
        tag      = "inactive" if not active else ("fines" if fines > 0 else "")
        member_tree.insert("", "end", iid=str(member_id),
                           values=(member_id, first_name, last_name, fine_str, status), tags=(tag,))
    conn.close()
    member_tree.tag_configure("fines",    foreground="#b00020")
    member_tree.tag_configure("inactive", foreground="#999999")

member_search_var.trace_add("write", lambda *_: load_members_from_db(member_search_var.get()))


def add_member_cmd():
    name = member_name_entry.get().strip()

    # Check if the box is totally empty
    if not name:
        messagebox.showerror("Error", "Name is required")
        return
    
    # If something is entered into the box we split it
    parts = name.split()

    # Guards to ensure we have a first and last name
    if len(parts) < 2:
        messagebox.showerror("Error", "Please enter a first and last name.")
        return
    
    # If we pass the check, we use the parts
    first_name = parts[0]
    last_name  = " ".join(parts[1:])

    if not messagebox.askyesno("Confirm", f"Add member '{first_name} {last_name}'?"):
        return

    member_obj = Member(first_name=first_name, last_name=last_name, fines_due=0)
    add_member(member_obj)

    if member_obj.member_id is None:
        messagebox.showerror("Error", "Could not add member (DB error)")
        return

    load_members_from_db(member_search_var.get())
    messagebox.showinfo("Success", f"Member '{name}' added (ID {member_obj.member_id})")
    member_name_entry.delete(0, tk.END)


def inactivate_member_cmd():
    selected = member_tree.selection()
    if not selected:
        messagebox.showwarning("Select", "Please select a member first")
        return

    member_id = int(selected[0])
    vals      = member_tree.item(selected[0], "values")
    full_name = f"{vals[1]} {vals[2]}"
    status    = vals[4]

    if status == "Inactive":
        messagebox.showwarning("Already Inactive", f"'{full_name}' is already inactive.")
        return
    if not messagebox.askyesno("Confirm", f"Inactivate member '{full_name}'?"):
        return

    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM loans WHERE member_id = ? AND return_date IS NULL;", (member_id,))
    if cur.fetchone()[0] > 0:
        conn.close()
        messagebox.showerror("Error", "Member has open loans. Return all books first.")
        return
    conn.close()

    set_member_active_status(member_id, False)
    load_members_from_db(member_search_var.get())
    messagebox.showinfo("Inactivated", f"Member '{full_name}' has been inactivated.")


def reactivate_member_cmd():
    selected = member_tree.selection()
    if not selected:
        messagebox.showwarning("Select", "Please select a member first")
        return

    member_id = int(selected[0])
    vals      = member_tree.item(selected[0], "values")
    full_name = f"{vals[1]} {vals[2]}"
    status    = vals[4]

    if status != "Inactive":
        messagebox.showwarning("Not Inactive", f"'{full_name}' is already active.")
        return
    if not messagebox.askyesno("Confirm", f"Reactivate member '{full_name}'?"):
        return

    set_member_active_status(member_id, True)
    load_members_from_db(member_search_var.get())
    messagebox.showinfo("Reactivated", f"Member '{full_name}' has been reactivated.")


btn_frame_members = ttk.Frame(members_tab)
btn_frame_members.grid(row=2, column=0, columnspan=3, pady=4)
ttk.Button(btn_frame_members, text="Add Member",        command=add_member_cmd).pack(side="left", padx=6)
ttk.Button(btn_frame_members, text="Inactivate Member", command=inactivate_member_cmd).pack(side="left", padx=6)
ttk.Button(btn_frame_members, text="Reactivate Member", command=reactivate_member_cmd).pack(side="left", padx=6)
ttk.Checkbutton(btn_frame_members, text="Show Inactive",
                variable=member_show_inactive, command=lambda: load_members_from_db(member_search_var.get())).pack(side="left", padx=10)


#  LOANS TAB

loans_tab.grid_columnconfigure(0, weight=1)
loans_tab.grid_columnconfigure(1, weight=2)
loans_tab.grid_rowconfigure(0, weight=1)

#Left panel: members with open loans
ln_left = ttk.LabelFrame(loans_tab, text=" Members with Open Loans ")
ln_left.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
ln_left.grid_rowconfigure(1, weight=1)
ln_left.grid_columnconfigure(0, weight=1)

ln_member_search_var = tk.StringVar()
ttk.Entry(ln_left, textvariable=ln_member_search_var, width=24).grid(
    row=0, column=0, padx=6, pady=(6, 2), sticky="ew")
ttk.Label(ln_left, text="\U0001f50d Search name / ID").grid(
    row=0, column=1, padx=(0, 6), sticky="w")

ln_member_frame = ttk.Frame(ln_left)
ln_member_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)
ln_member_frame.grid_rowconfigure(0, weight=1)
ln_member_frame.grid_columnconfigure(0, weight=1)

ln_member_tree = ttk.Treeview(
    ln_member_frame,
    columns=("member_id", "name", "loans", "fines"),
    show="headings",
    selectmode="browse",
)
ln_member_tree.heading("member_id", text="ID")
ln_member_tree.heading("name",      text="Name")
ln_member_tree.heading("loans",     text="Out")
ln_member_tree.heading("fines",     text="Fines")
ln_member_tree.column("member_id", width=45,  anchor="center", minwidth=45,  stretch=False)
ln_member_tree.column("name",      width=160, anchor="w",      minwidth=100, stretch=True)
ln_member_tree.column("loans",     width=40,  anchor="center", minwidth=40,  stretch=False)
ln_member_tree.column("fines",     width=75,  anchor="e",      minwidth=75,  stretch=False)

ln_member_vsb = ttk.Scrollbar(ln_member_frame, orient="vertical", command=ln_member_tree.yview)
ln_member_tree.configure(yscrollcommand=ln_member_vsb.set)
ln_member_tree.grid(row=0, column=0, sticky="nsew")
ln_member_vsb.grid(row=0, column=1, sticky="ns")

#Right panel: books checked out by selected member
ln_right = ttk.LabelFrame(loans_tab, text=" Checked-Out Books ")
ln_right.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
ln_right.grid_rowconfigure(1, weight=1)
ln_right.grid_columnconfigure(0, weight=1)

ln_book_search_var = tk.StringVar()
ttk.Entry(ln_right, textvariable=ln_book_search_var, width=28).grid(
    row=0, column=0, padx=6, pady=(6, 2), sticky="ew")
ttk.Label(ln_right, text="\U0001f50d Filter title / author").grid(
    row=0, column=1, padx=(0, 6), sticky="w")

ln_book_frame = ttk.Frame(ln_right)
ln_book_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)
ln_book_frame.grid_rowconfigure(0, weight=1)
ln_book_frame.grid_columnconfigure(0, weight=1)

ln_book_tree = ttk.Treeview(
    ln_book_frame,
    columns=("loan_id", "title", "author", "due_date", "status"),
    show="headings",
    selectmode="browse",
)
ln_book_tree.heading("loan_id",  text="Loan")
ln_book_tree.heading("title",    text="Title")
ln_book_tree.heading("author",   text="Author")
ln_book_tree.heading("due_date", text="Due Date")
ln_book_tree.heading("status",   text="Status")
ln_book_tree.column("loan_id",  width=50,  anchor="center", minwidth=50,  stretch=False)
ln_book_tree.column("title",    width=210, anchor="w",      minwidth=100, stretch=True)
ln_book_tree.column("author",   width=150, anchor="w",      minwidth=80,  stretch=True)
ln_book_tree.column("due_date", width=95,  anchor="center", minwidth=95,  stretch=False)
ln_book_tree.column("status",   width=105, anchor="w",      minwidth=105, stretch=False)

ln_book_vsb = ttk.Scrollbar(ln_book_frame, orient="vertical", command=ln_book_tree.yview)
ln_book_tree.configure(yscrollcommand=ln_book_vsb.set)
ln_book_tree.grid(row=0, column=0, sticky="nsew")
ln_book_vsb.grid(row=0, column=1, sticky="ns")

#Bottom bar
ln_bottom = ttk.Frame(loans_tab)
ln_bottom.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
ln_bottom.grid_columnconfigure(2, weight=1)

ttk.Button(ln_bottom, text="↩  Return Loan", command=lambda: return_loan_cmd()).grid(
    row=0, column=0, padx=(0, 10))
ttk.Button(ln_bottom, text="📋  Overdue Report", command=lambda: open_overdue_report()).grid(
    row=0, column=1, padx=(0, 10))

ln_status_var = tk.StringVar(value="Select a member to see their checked-out books.")
ttk.Label(ln_bottom, textvariable=ln_status_var,
          foreground="#555555", anchor="w", wraplength=460).grid(
    row=0, column=2, sticky="ew")


#Data loaders
def _ln_load_members(filter_text=""):
    ln_member_tree.delete(*ln_member_tree.get_children())
    conn = get_connection()
    cur  = conn.cursor()
    like = f"%{filter_text}%"
    try:
        exact_id = int(filter_text)
    except ValueError:
        exact_id = -1
    cur.execute("""
        SELECT m.member_id,
               m.first_name || ' ' || m.last_name AS full_name,
               COUNT(l.loan_id)                    AS open_loans,
               m.fines_due
        FROM members m
        JOIN loans l ON l.member_id = m.member_id AND l.return_date IS NULL
        WHERE m.active = 1
          AND (m.member_id = ? OR m.first_name LIKE ? OR m.last_name LIKE ?)
        GROUP BY m.member_id
        ORDER BY full_name;
    """, (exact_id, like, like))
    for member_id, full_name, open_loans, fines in cur.fetchall():
        tag = "fines" if fines > 0 else ""
        ln_member_tree.insert("", "end", iid=f"m{member_id}",
                              values=(member_id, full_name, open_loans, f"${fines:.2f}"),
                              tags=(tag,))
    conn.close()
    ln_member_tree.tag_configure("fines", foreground="#b00020")


def _ln_load_books_for_member(member_id, filter_text=""):
    ln_book_tree.delete(*ln_book_tree.get_children())
    if member_id is None:
        return
    conn = get_connection()
    cur  = conn.cursor()
    like = f"%{filter_text}%"
    cur.execute("""
        SELECT l.loan_id, b.title, b.author, l.due_date
        FROM loans l
        JOIN books b ON b.book_id = l.book_id
        WHERE l.member_id = ? AND l.return_date IS NULL
          AND (b.title LIKE ? OR b.author LIKE ?)
        ORDER BY l.due_date ASC;
    """, (member_id, like, like))
    today = date.today()
    for loan_id, title, author, due_date_str in cur.fetchall():
        due_dt  = date.fromisoformat(due_date_str)
        overdue = today > due_dt
        status  = f"Overdue {(today - due_dt).days}d" if overdue else "On Loan"
        tag     = "overdue" if overdue else ""
        ln_book_tree.insert("", "end", iid=f"l{loan_id}",
                            values=(loan_id, title, author, due_date_str, status),
                            tags=(tag,))
    conn.close()
    ln_book_tree.tag_configure("overdue", foreground="#b00020")


def _get_selected_member_id():
    sel = ln_member_tree.selection()
    if not sel:
        return None
    return int(ln_member_tree.item(sel[0], "values")[0])


def load_open_loans_from_db():
    """Refresh the full loans tab (called from other tabs after changes)."""
    sync_fines()
    _ln_load_members(ln_member_search_var.get())
    mid = _get_selected_member_id()
    _ln_load_books_for_member(mid, ln_book_search_var.get())
    _update_ln_status()


#Live search traces
ln_member_search_var.trace_add("write",
    lambda *_: _ln_load_members(ln_member_search_var.get()))

ln_book_search_var.trace_add("write",
    lambda *_: _ln_load_books_for_member(
        _get_selected_member_id(), ln_book_search_var.get()))


#Status bar updates
def _update_ln_status(*_):
    book_sel   = ln_book_tree.selection()
    member_sel = ln_member_tree.selection()
    if book_sel and member_sel:
        bvals = ln_book_tree.item(book_sel[0], "values")
        mvals = ln_member_tree.item(member_sel[0], "values")
        ln_status_var.set(
            f'Ready to return: "{bvals[1]}"  ←  {mvals[1]}  (click Return Loan)'
        )
    elif member_sel:
        mvals = ln_member_tree.item(member_sel[0], "values")
        ln_status_var.set(f'{mvals[1]} — select a book to return.')
    else:
        ln_status_var.set("Select a member to see their checked-out books.")

ln_member_tree.bind("<<TreeviewSelect>>", lambda e: (
    _ln_load_books_for_member(_get_selected_member_id(), ln_book_search_var.get()),
    _update_ln_status(),
))
ln_book_tree.bind("<<TreeviewSelect>>", _update_ln_status)


#Overdue report window
def open_overdue_report():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT m.member_id,
               m.first_name || ' ' || m.last_name AS full_name,
               m.fines_due,
               COUNT(l.loan_id) AS open_loans
        FROM members m
        LEFT JOIN loans l ON l.member_id = m.member_id AND l.return_date IS NULL
        WHERE m.fines_due > 0
        GROUP BY m.member_id
        ORDER BY m.fines_due DESC;
    """)
    rows  = cur.fetchall()
    total = sum(r[2] for r in rows)
    conn.close()

    win = tk.Toplevel(root)
    win.title("Overdue Report")
    win.geometry("520x400")
    win.resizable(True, True)

    # Summary header
    tk.Label(win, text=f"Total Fines Due:  ${total:.2f}",
             font=("", 12, "bold"), foreground="#b00020").pack(pady=(14, 4))
    tk.Label(win, text=f"{len(rows)} member(s) with outstanding fines",
             foreground="#555555").pack(pady=(0, 10))

    # Report table
    frame = ttk.Frame(win)
    frame.pack(fill="both", expand=True, padx=12, pady=(0, 4))
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    tree = ttk.Treeview(frame,
                        columns=("member_id", "name", "fines", "open_loans"),
                        show="headings", selectmode="none")
    tree.heading("member_id",  text="ID")
    tree.heading("name",       text="Member")
    tree.heading("fines",      text="Fines Due")
    tree.heading("open_loans", text="Books Out")
    tree.column("member_id",  width=50,  anchor="center", minwidth=40)
    tree.column("name",       width=220, anchor="w",      minwidth=100)
    tree.column("fines",      width=100, anchor="e",      minwidth=70)
    tree.column("open_loans", width=80,  anchor="center", minwidth=50)

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")

    for member_id, full_name, fines, open_loans in rows:
        tree.insert("", "end", values=(member_id, full_name, f"${fines:.2f}", open_loans))

    ttk.Button(win, text="Close", command=win.destroy).pack(pady=8)


#Return loan action
def return_loan_cmd():
    book_sel = ln_book_tree.selection()
    if not book_sel:
        messagebox.showwarning("Select", "Please select a book to return.")
        return

    bvals   = ln_book_tree.item(book_sel[0], "values")
    loan_id = int(bvals[0])
    title   = bvals[1]

    if not messagebox.askyesno("Confirm Return", f'Return "{title}"?'):
        return

    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT book_id, member_id, due_date
        FROM loans WHERE loan_id = ? AND return_date IS NULL;
    """, (loan_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        messagebox.showerror("Error", "Loan not found or already returned.")
        return

    book_id, member_id, due_date_str = row
    due_dt       = date.fromisoformat(due_date_str)
    return_dt    = date.today()
    days_overdue = max(0, (return_dt - due_dt).days)
    fine         = round(days_overdue * FINE_PER_DAY, 2)

    # Require fine payment confirmation before allowing the return
    if fine > 0:
        confirmed = messagebox.askyesno(
            "Fine Due",
            f'"{title}" is {days_overdue} day(s) overdue.\n'
            f'Fine amount: ${fine:.2f}\n\n'
            f'Confirm that the fine has been collected before returning?'
        )
        if not confirmed:
            messagebox.showinfo("Cancelled", "Return cancelled. Please collect the fine first.")
            return

    db_return_loan(loan_id, return_dt)
    set_book_checkout_status(book_id, False)

    # Fine was collected in cash — clear the member's balance
    if fine > 0:
        conn3 = get_connection()
        cur3  = conn3.cursor()
        cur3.execute("UPDATE members SET fines_due = 0 WHERE member_id = ?;", (member_id,))
        conn3.commit()
        conn3.close()

    load_open_loans_from_db()
    load_books_from_db()
    load_members_from_db()
    refresh_checkout_tab()

    if fine > 0:
        messagebox.showinfo("Returned",
            f'"{title}" returned.\nDays overdue: {days_overdue}\nFine collected: ${fine:.2f}')
    else:
        messagebox.showinfo("Returned", f'"{title}" returned on time. No fine.')




#  CHECKOUT TAB

#Layout: two panels side by side, status bar at bottom
checkout_tab.grid_columnconfigure(0, weight=1)
checkout_tab.grid_columnconfigure(1, weight=1)
checkout_tab.grid_rowconfigure(1, weight=1)

# Left panel — available books
left_panel = ttk.LabelFrame(checkout_tab, text=" Available Books ")
left_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(8, 4), pady=8)
left_panel.grid_rowconfigure(1, weight=1)
left_panel.grid_columnconfigure(0, weight=1)

co_book_search_var = tk.StringVar()
co_book_search = ttk.Entry(left_panel, textvariable=co_book_search_var, width=28)
co_book_search.grid(row=0, column=0, padx=6, pady=(6, 2), sticky="ew")
ttk.Label(left_panel, text="🔍 Search title / author").grid(row=0, column=1, padx=(0, 6), sticky="w")

co_book_frame = ttk.Frame(left_panel)
co_book_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)
co_book_frame.grid_rowconfigure(0, weight=1)
co_book_frame.grid_columnconfigure(0, weight=1)

co_book_tree = ttk.Treeview(
    co_book_frame,
    columns=("book_id", "title", "author"),
    show="headings",
    selectmode="browse",
)
co_book_tree.heading("book_id", text="ID")
co_book_tree.heading("title",   text="Title")
co_book_tree.heading("author",  text="Author")
co_book_tree.column("book_id", width=45,  anchor="center", minwidth=45,  stretch=False)
co_book_tree.column("title",   width=190, anchor="w",      minwidth=80,  stretch=True)
co_book_tree.column("author",  width=140, anchor="w",      minwidth=80,  stretch=True)

co_book_vsb = ttk.Scrollbar(co_book_frame, orient="vertical", command=co_book_tree.yview)
co_book_tree.configure(yscrollcommand=co_book_vsb.set)
co_book_tree.grid(row=0, column=0, sticky="nsew")
co_book_vsb.grid(row=0, column=1, sticky="ns")

#Right panel — active members
right_panel = ttk.LabelFrame(checkout_tab, text=" Active Members ")
right_panel.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(4, 8), pady=8)
right_panel.grid_rowconfigure(1, weight=1)
right_panel.grid_columnconfigure(0, weight=1)

co_member_search_var = tk.StringVar()
co_member_search = ttk.Entry(right_panel, textvariable=co_member_search_var, width=28)
co_member_search.grid(row=0, column=0, padx=6, pady=(6, 2), sticky="ew")
ttk.Label(right_panel, text="🔍 Search name / ID").grid(row=0, column=1, padx=(0, 6), sticky="w")

co_member_frame = ttk.Frame(right_panel)
co_member_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)
co_member_frame.grid_rowconfigure(0, weight=1)
co_member_frame.grid_columnconfigure(0, weight=1)

co_member_tree = ttk.Treeview(
    co_member_frame,
    columns=("member_id", "name", "loans"),
    show="headings",
    selectmode="browse",
)
co_member_tree.heading("member_id", text="ID")
co_member_tree.heading("name",      text="Name")
co_member_tree.heading("loans",     text="Books Out")
co_member_tree.column("member_id", width=45,  anchor="center", minwidth=45,  stretch=False)
co_member_tree.column("name",      width=190, anchor="w",      minwidth=100, stretch=True)
co_member_tree.column("loans",     width=75,  anchor="center", minwidth=75,  stretch=False)

co_member_vsb = ttk.Scrollbar(co_member_frame, orient="vertical", command=co_member_tree.yview)
co_member_tree.configure(yscrollcommand=co_member_vsb.set)
co_member_tree.grid(row=0, column=0, sticky="nsew")
co_member_vsb.grid(row=0, column=1, sticky="ns")

# Bottom bar — status label + button
bottom_bar = ttk.Frame(checkout_tab)
bottom_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
bottom_bar.grid_columnconfigure(0, weight=1)

co_status_var = tk.StringVar(value="Select an available book and an active member, then click Checkout.")
co_status_lbl = ttk.Label(bottom_bar, textvariable=co_status_var,
                           foreground="#555555", anchor="w", wraplength=500)
co_status_lbl.grid(row=0, column=0, sticky="ew", padx=(4, 10))

co_checkout_btn = ttk.Button(bottom_bar, text="✔  Checkout Book", command=lambda: do_checkout())
co_checkout_btn.grid(row=0, column=1, padx=4)


#Data loaders
def _co_load_books(filter_text=""):
    co_book_tree.delete(*co_book_tree.get_children())
    conn = get_connection()
    cur  = conn.cursor()
    like = f"%{filter_text}%"
    cur.execute("""
        SELECT book_id, title, author
        FROM books
        WHERE active = 1 AND is_checked_out = 0
          AND (title LIKE ? OR author LIKE ?)
        ORDER BY title;
    """, (like, like))
    for book_id, title, author in cur.fetchall():
        co_book_tree.insert("", "end", iid=f"b{book_id}",
                            values=(book_id, title, author))
    conn.close()


def _co_load_members(filter_text=""):
    co_member_tree.delete(*co_member_tree.get_children())
    conn = get_connection()
    cur  = conn.cursor()
    like = f"%{filter_text}%"
    try:
        exact_id = int(filter_text)
    except ValueError:
        exact_id = -1
    cur.execute("""
        SELECT m.member_id,
               m.first_name || ' ' || m.last_name AS full_name,
               COUNT(l.loan_id)                    AS open_loans
        FROM members m
        LEFT JOIN loans l ON l.member_id = m.member_id AND l.return_date IS NULL
        WHERE m.active = 1 AND m.fines_due = 0
          AND (m.member_id = ? OR m.first_name LIKE ? OR m.last_name LIKE ?)
        GROUP BY m.member_id
        ORDER BY full_name;
    """, (exact_id, like, like))
    for member_id, full_name, open_loans in cur.fetchall():
        label = f"{open_loans} / 3"
        co_member_tree.insert("", "end", iid=f"m{member_id}",
                              values=(member_id, full_name, label))
    conn.close()


def refresh_checkout_tab():
    _co_load_books(co_book_search_var.get())
    _co_load_members(co_member_search_var.get())


# Live search on keystroke
co_book_search_var.trace_add("write",
    lambda *_: _co_load_books(co_book_search_var.get()))
co_member_search_var.trace_add("write",
    lambda *_: _co_load_members(co_member_search_var.get()))

# Update status bar whenever a selection changes
def _update_co_status(*_):
    book_sel   = co_book_tree.selection()
    member_sel = co_member_tree.selection()
    if book_sel and member_sel:
        bvals = co_book_tree.item(book_sel[0], "values")
        mvals = co_member_tree.item(member_sel[0], "values")
        co_status_var.set(
            f'Ready: "{bvals[1]}"  →  {mvals[1]}  (click Checkout to confirm)'
        )
    elif book_sel:
        co_status_var.set("Book selected — now select a member.")
    elif member_sel:
        co_status_var.set("Member selected — now select a book.")
    else:
        co_status_var.set("Select an available book and an active member, then click Checkout.")

co_book_tree.bind("<<TreeviewSelect>>",   _update_co_status)
co_member_tree.bind("<<TreeviewSelect>>", _update_co_status)


#Checkout action
def do_checkout():
    book_sel   = co_book_tree.selection()
    member_sel = co_member_tree.selection()

    if not book_sel:
        messagebox.showwarning("Select", "Please select a book first.")
        return
    if not member_sel:
        messagebox.showwarning("Select", "Please select a member first.")
        return

    bvals     = co_book_tree.item(book_sel[0],   "values")
    mvals     = co_member_tree.item(member_sel[0], "values")
    book_id   = int(bvals[0])
    member_id = int(mvals[0])
    book_title = bvals[1]
    member_name = mvals[1]

    if not messagebox.askyesno(
        "Confirm Checkout",
        f'Check out "{book_title}"\nto {member_name}?'
    ):
        return

    success, message = checkout_book(book_id, member_id)

    if success:
        co_status_var.set(f"✔ {message}")
        refresh_checkout_tab()
        load_books_from_db()
        load_open_loans_from_db()
        load_members_from_db()
    else:
        co_status_var.set(f"✖ {message}")
        messagebox.showerror("Checkout Failed", message)


#STARTUP
if __name__ == "__main__":
    initialize_db()
    load_books_from_db()
    load_members_from_db()
    load_open_loans_from_db()
    refresh_checkout_tab()
    root.mainloop()