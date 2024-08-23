import sqlite3

def connect():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("create table users("
                "user_id int"
                ");")

    conn.commit()
if __name__ == '__main__':
    connect()
