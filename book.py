from database import get_connection
import sqlite3

# Class Book implementation
class Book:
    def __init__(self, title, author, is_checked_out=0, book_id=None, active=1):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.is_checked_out = is_checked_out
        self.active = active

def add_book_to_db(book_obj):
    """Inserts a Book object into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO books (title, author, is_checked_out, active)
            VALUES (?, ?, ?, ?)
        ''', (book_obj.title, book_obj.author, int(book_obj.is_checked_out), int(book_obj.active)))
        
        conn.commit()
        book_obj.book_id = cursor.lastrowid
        print(f"Added: {book_obj.title}")

    except sqlite3.IntegrityError:
        print(f"Error: Could not insert book '{book_obj.title}'.")
    finally:
        conn.close()

def set_book_checkout_status(book_id, is_checked_out):
    """
    Updates the checkout status of a book.
    is_checked_out: True (1) to check out, False (0) to return
    """
    conn = get_connection()
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
        print(f"Error updating checkout status: {e}")
    finally:
        conn.close()
        
def set_book_active_status(book_id, is_active):
    """
    Updates the active status of a book.
    is_active: True (1) to activate, False (0) to deactivate
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    status_int = 1 if is_active else 0
    status_text = "Active" if is_active else "Inactive"

    try:
        cursor.execute('''
            UPDATE books 
            SET active = ? 
            WHERE book_id = ?
        ''', (status_int, book_id))
        
        if cursor.rowcount == 0:
            print(f"No book found with ID {book_id}")
        else:
            conn.commit()
            print(f"Book {book_id} is now set to: {status_text}")
            
    except sqlite3.Error as e:
        print(f"Error updating active status: {e}")
    finally:
        conn.close()

def search_books(query):
    """
    Searches for books.
    - ID search is EXACT.
    - Title and author search is PARTIAL.
    - Available books appear first, then ordered by book_id.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    name_search = f"%{query}%"

    try:
        exact_id = int(query)
    except ValueError:
        exact_id = -1

    try:
        cursor.execute('''
            SELECT book_id, title, author, is_checked_out, active
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

    return [
        Book(title=row[1], author=row[2], is_checked_out=row[3], book_id=row[0], active=row[4])
        for row in rows
    ]


if __name__ == "__main__":
    from database import initialize_db

    initialize_db()

    my_book = Book("The Odyssey", "Homer")
    add_book_to_db(my_book)
    set_book_checkout_status(my_book.book_id, True)

    results = search_books("Odyssey")
    for book in results:
        print(book.book_id, book.title, book.author, book.is_checked_out, book.active)