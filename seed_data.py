from database import get_db, init_db
import random

init_db()

genres = ["Pop", "Rock", "Hip-Hop", "Electronic", "Jazz", "Classical", "Metal", "Folk", "R&B", "Reggae"]
albums_per_artist = 3
tracks_per_album = 8

conn = get_db()
c = conn.cursor()

for g in genres:
    try:
        c.execute("INSERT INTO genres (name) VALUES (?)", (g,))
    except Exception:
        pass
    
conn.commit()
conn.close()
print("Seeded DB with sample data.")