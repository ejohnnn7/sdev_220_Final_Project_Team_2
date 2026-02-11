from database import get_connection
import sqlite3

class Member:
    def __init__(self, first_name, last_name, fines_due, member_id=None, active=1):
        self.member_id = member_id
        self.first_name = first_name
        self.last_name = last_name
        self.fines_due = fines_due
        self.active = active

def add_member_to_db(member_obj):
    """Inserts a Member object into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO members (first_name, last_name, fines_due, active)
            VALUES (?, ?, ?, ?)
        ''', (member_obj.first_name, member_obj.last_name, int(member_obj.fines_due), int(member_obj.active)))
        
        conn.commit()
        member_obj.member_id = cursor.lastrowid
        print(f"Added: {member_obj.first_name} {member_obj.last_name}")

    except sqlite3.IntegrityError:
        print(f"Error: Could not insert member '{member_obj.first_name} {member_obj.last_name}'.")
    finally:
        conn.close()

def set_member_active_status(member_id, is_active):
    """
    Updates the active status of a member.
    is_active: True (1) to activate, False (0) to deactivate
    """
    conn = get_connection()
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
        print(f"Error updating active status: {e}")
    finally:
        conn.close()

def update_member_fines(member_id, amount):
    """
    Sets the fines_due balance for a member to the given amount.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE members
            SET fines_due = ?
            WHERE member_id = ?
        ''', (amount, member_id))

        if cursor.rowcount == 0:
            print(f"No member found with ID {member_id}")
        else:
            conn.commit()
            print(f"Member {member_id} fines updated to: {amount}")

    except sqlite3.Error as e:
        print(f"Error updating fines: {e}")
    finally:
        conn.close()

def search_members(query):
    """
    Searches for members.
    - ID search is EXACT.
    - Name search is PARTIAL.
    - Active members appear first, then ordered by last name.
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

    return [
        Member(row[1], row[2], row[3], member_id=row[0], active=row[4])
        for row in rows
    ]


if __name__ == "__main__":
    from database import initialize_db

    initialize_db()

    new_member = Member("Andrew", "Catlin", 0)
    add_member_to_db(new_member)

    new_member2 = Member("Bob", "Cat", 0)
    add_member_to_db(new_member2)

    set_member_active_status(new_member.member_id, False)

    results = search_members("Cat")
    for m in results:
        print(m.member_id, m.first_name, m.last_name, m.fines_due, m.active)