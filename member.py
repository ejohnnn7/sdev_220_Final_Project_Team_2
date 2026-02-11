import sqlite3

class Member:
    #Initialize member_id last as None to make it increment automatically instead of passing an arbitrary id
    def __init__(self, first_name, last_name, fines_due, member_id=None, active=1):
        self.member_id = member_id
        self.first_name = first_name
        self.last_name = last_name
        self.fines_due = fines_due
        self.active = active


# Access the member database
def initialize_member_db():
    """Sets up the table if it doesn't exist."""
    conn = sqlite3.connect('member.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            member_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            fines_due INTEGER,
            active INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

# Add member to database
def add_member_to_db(member_obj):
    """Inserts a Member object into the database."""
    conn = sqlite3.connect('member.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO members (first_name, last_name, fines_due)
            VALUES (?, ?, ?)
        ''', (member_obj.first_name, member_obj.last_name, int(member_obj.fines_due)))
        
        conn.commit()
        
        #Make the member id be the unique row number
        member_obj.member_id = cursor.lastrowid
        
        print(f"Added: {member_obj.first_name}")
    except sqlite3.IntegrityError:
        print(f"Error: Book ID {member_obj.member_id} already exists.")
    finally:
        conn.close()

def set_member_active_status(member_id, is_active):
    """
    Updates the active status of a member.
    is_active: True (1) to activate, False (0) to deactivate
    """
    conn = sqlite3.connect('member.db')
    cursor = conn.cursor()
    
    status_int = 1 if is_active else 0
    status_text = "Active" if is_active else "Inactive"

    try:
        cursor.execute('''
            UPDATE members 
            SET active = ? 
            WHERE member_id = ?
        ''', (status_int, member_id))
        
        if cursor.rowcount == 0:
            print(f"No member found with ID {member_id}")
        else:
            conn.commit()
            print(f"Member {member_id} is now set to: {status_text}")
            
    except sqlite3.Error as e:
        print(f"Error updating status: {e}")
    finally:
        conn.close()

def search_members(query):
    """
    Searches for members.
    - ID search is EXACT.
    - Name search is PARTIAL.
    - Active members appear first.
    """
    conn = sqlite3.connect('member.db')
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
        SELECT member_id, first_name, last_name, fines_due, active 
        FROM members 
        WHERE member_id = ? OR first_name LIKE ? OR last_name LIKE ?
        ORDER BY active DESC, last_name ASC
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
        results.append(Member(row[1], row[2], row[3], member_id=row[0], active=row[4]))

    return results

if __name__ == "__main__":
    # #--- Execution Examples ---
    # initialize_member_db()

    # #1. Create a new member instance
    # new_member = Member("Andrew", "Catlin", 0)
    # add_member_to_db(new_member)
    
    # new_member = Member("Bob", "Cat", 0)
    # add_member_to_db(new_member)

    # #2. Deactivate the member (Soft Delete)
    # #The row stays in the DB, but 'active' becomes 0
    # set_member_active_status(new_member.member_id, False)

    # #3. Reactivate them later if they return
    # #set_member_active_status(new_member.member_id, True)
    
    # #4. Search members
    # for m in search_members("Cat"):
    #     print(m.member_id, m.first_name, m.last_name, m.fines_due, m.active)
    pass
    


# The above will be used in adding a new member, it just needs a GUI to access it cleanly. 
# The initialize_member_db will also be used to search the DB.
