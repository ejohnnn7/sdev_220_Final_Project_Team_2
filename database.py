import sqlite3

def get_connection():
    """Returns a connection to the library database with foreign keys enabled."""
    conn = sqlite3.connect("library.db")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_db():
    """
    Sets up all tables if they don't already exist.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS books (
            book_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            title          TEXT    NOT NULL,
            author         TEXT    NOT NULL,
            is_checked_out INTEGER NOT NULL DEFAULT 0,
            active         INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS members (
            member_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT    NOT NULL,
            last_name  TEXT    NOT NULL,
            fines_due  INTEGER NOT NULL DEFAULT 0,
            active     INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS loans (
            loan_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id       INTEGER NOT NULL,
            member_id     INTEGER NOT NULL,
            checkout_date TEXT    NOT NULL,
            due_date      TEXT    NOT NULL,
            return_date   TEXT,
            FOREIGN KEY (book_id)   REFERENCES books(book_id),
            FOREIGN KEY (member_id) REFERENCES members(member_id)
        );
    ''')

    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialize_db()