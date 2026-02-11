import sqlite3

# Class Book implementation
class Book:
    def __init__(self, title, author, is_checked_out=0, book_id=None):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.is_checked_out = is_checked_out

# Access the database
def initialize_book_db():
    """Sets up the table if it doesn't exist."""
    conn = sqlite3.connect('book.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            book_id INTEGER PRIMARY KEY,
            title TEXT,
            author TEXT,
            is_checked_out INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Add book to database
def add_book_to_db(book_obj):
    """Inserts a Book object into the database."""
    conn = sqlite3.connect('book.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO books (title, author, is_checked_out)
            VALUES (?, ?, ?)
        ''', (book_obj.title, book_obj.author, int(book_obj.is_checked_out)))
        
        conn.commit()
        
        book_obj.book_id = cursor.lastrowid
        
        print(f"Added: {book_obj.title}")
    except sqlite3.IntegrityError:
        print(f"Error: Book ID {book_obj.book_id} already exists.")
    finally:
        conn.close()

def set_book_checkout_status(book_id, is_checked_out):
    """
    Updates the checkout status of a book.
    is_checked_out: True (1) to check out, False (0) to uncheck out
    """
    conn = sqlite3.connect('book.db')
    cursor = conn.cursor()
    
    status_int = 1 if is_checked_out else 0
    status_text = "Checked Out" if is_checked_out else "Available"

    try:
        cursor.execute('''
            UPDATE books 
            SET is_checked_out = ? 
            WHERE book_id = ?
        ''', (status_int, book_id))
        
        if cursor.rowcount == 0:
            print(f"No book found with ID {book_id}")
        else:
            conn.commit()
            print(f"Book {book_id} is now set to: {status_text}")
            
    except sqlite3.Error as e:
        print(f"Error updating status: {e}")
    finally:
        conn.close()

def search_books(query):
    """
    Searches for members.
    - ID search is EXACT.
    - Name search is PARTIAL.
    - Active members appear first.
    """
    conn = sqlite3.connect('book.db')
    cursor = conn.cursor()
    
    # Prepare the wildcards for name searching
    name_search = f"%{query}%"

    # Determine if we are searching for an ID or just a Name
    try:
        # If the query is a number, use it for the ID search
        exact_id = int(query)
    except ValueError:
        # If query is not a number, set ID to -1 (will never match a real member)
        exact_id = -1

    try:
        cursor.execute('''
        SELECT book_id, title, author, is_checked_out 
        FROM books 
        WHERE book_id = ? OR title LIKE ? OR author LIKE ?
        ORDER BY is_checked_out ASC, book_id ASC
        ''', (exact_id, name_search, name_search))
        
        rows = cursor.fetchall()
        
    except sqlite3.Error as e:
        print(f"Search Error: {e}")
        return []
    
    finally:
        conn.close()

    # Convert results to Member objects
    results = []
    for row in rows:
            # row structure: (book_id, title, author, is_checked_out)
            # We map these to the Book class: __init__(self, title, author, is_checked_out, book_id)
            found_book = Book(
                title=row[1], 
                author=row[2], 
                is_checked_out=row[3], 
                book_id=row[0]
            )
            results.append(found_book)

    return results


if __name__ == "__main__":
    # --- Execution Examples ---
    initialize_book_db()

    # Create a new book instance
    my_book = Book("The Odyssey", "Homer")

    # Save it
    add_book_to_db(my_book)
    
    # Check out book
    set_book_checkout_status(my_book.book_id, True)
    
    # Query books
    search_books("*")


# The above will be used in adding a new book, it just needs a GUI to access it cleanly. 
# The initialize_book_db will also be used to search the DB.