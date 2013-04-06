import sqlite3

def main():
    conn = sqlite3.connect("robofist.db")
    cursor = conn.cursor()
    
    cursor.execute("CREATE TABLE combatants (dbref text, pickledobject text, update_dt real)""")
    conn.commit()
    conn.close()
    
    
    
if __name__ == '__main__':
    main()