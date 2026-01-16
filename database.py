import sqlite3

DB_PATH = "database.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS genres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    """)

    
    c.execute("""
    CREATE TABLE IF NOT EXISTS artists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        country TEXT,
        bio TEXT,
        photo TEXT
    );
    """)

   
    c.execute("""
    CREATE TABLE IF NOT EXISTS albums (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        artist_id INTEGER NOT NULL,
        year INTEGER,
        genre_id INTEGER,
        tracks_count INTEGER DEFAULT 0,
        FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
        FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE SET NULL
    );
    """)

    
    c.execute("""
    CREATE TABLE IF NOT EXISTS tracks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        album_id INTEGER NOT NULL,
        duration TEXT,
        track_number INTEGER,
        FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
    );
    """)

   
    c.execute("""
    CREATE TABLE IF NOT EXISTS playlist_tracks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        track_id INTEGER NOT NULL UNIQUE,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("ДБ создана")
