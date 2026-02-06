import sqlite3
class Member:
    def __init__(self, member_id, first_name, last_name, fines_due):
        self.member_id = member_id
        self.first_name = first_name
        self.last_name = last_name
        self.fines_due = fines_due


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
            fines_due INTEGER
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
            INSERT INTO members (member_id, first_name, last_name, fines_due)
            VALUES (?, ?, ?, ?)
        ''', (member_obj.member_id, member_obj.first_name, member_obj.last_name, int(member_obj.fines_due)))
        conn.commit()
        print(f"✅ Added: {member_obj.first_name}")
    except sqlite3.IntegrityError:
        print(f"❌ Error: Book ID {member_obj.member_id} already exists.")
    finally:
        conn.close()

# --- Execution Examples ---
initialize_member_db()

# Create a new member instance
new_member = Member(1001, "Andrew", "Catlin", 0)

# Save it
add_member_to_db(new_member)


# The above will be used in adding a new member, it just needs a GUI to access it cleanly. 
# The initialize_member_db will also be used to serach the DB.
