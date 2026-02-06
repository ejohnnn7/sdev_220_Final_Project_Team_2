import sqlite3

# Class Book implementation
class Book:
    def __init__(self, book_id, title, author, is_checked_out=False):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.is_checked_out = is_checked_out

# Access the database
def initialize_book_db():
    """Sets up the table if it doesn't exist."""
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            book_id INTEGER PRIMARY KEY,
            title TEXT,
            author TEXT,
            is_checked_out INTEGER
        )
    ''')
    conn.commit()
    conn.close()

# Add book to database
def add_book_to_db(book_obj):
    """Inserts a Book object into the database."""
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO books (book_id, title, author, is_checked_out)
            VALUES (?, ?, ?, ?)
        ''', (book_obj.book_id, book_obj.title, book_obj.author, int(book_obj.is_checked_out)))
        conn.commit()
        print(f"✅ Added: {book_obj.title}")
    except sqlite3.IntegrityError:
        print(f"❌ Error: Book ID {book_obj.book_id} already exists.")
    finally:
        conn.close()


# --- Execution Examples ---
initialize_book_db()

# Create a new book instance
my_book = Book(101, "The Odyssey", "Homer")

# Save it
add_book_to_db(my_book)


# The above will be used in adding a new book, it just needs a GUI to access it cleanly. 
# The initialize_book_db will also be used to serach the DB.