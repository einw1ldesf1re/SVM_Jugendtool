import sqlite3

DB_FILE = 'training_manager.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.commit()
    conn.close()

def query_db(sql, params=(), single=False):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(sql, params)
    rv = c.fetchall()
    conn.commit()
    conn.close()
    if single:
        return dict(rv[0]) if rv else None
    return [dict(r) for r in rv]
