from flask import Flask, render_template, request, redirect, url_for, Response
from database import get_db, init_db
import json
import os


app = Flask(__name__)
init_db()
@app.context_processor
def utility_processor():
    def get_genres():
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM genres ORDER BY name")
        g = c.fetchall()
        return g
    return dict(get_genres=get_genres)

def to_json(data):
    return Response(json.dumps(data, ensure_ascii=False), mimetype="application/json")

@app.route("/")
@app.route("/artists")
def artists_list():
    conn = get_db()
    c = conn.cursor()
    
    country_filter = request.args.get('country', '').strip()
    sort_order = request.args.get('sort', 'name_asc')
    
    query = "SELECT * FROM artists"
    params = []
    
    if country_filter:
        query += " WHERE country = ?"
        params.append(country_filter)
    
    if sort_order == 'name_asc':
        query += " ORDER BY name ASC" 
    elif sort_order == 'name_desc':
        query += " ORDER BY name DESC"  
    elif sort_order == 'country_asc':
        query += " ORDER BY country ASC, name ASC" 
    else:
        query += " ORDER BY name ASC" 
    
    
    c.execute(query, params)
    artists = c.fetchall()
    
    c.execute("SELECT DISTINCT country FROM artists WHERE country IS NOT NULL ORDER BY country")
    all_countries = c.fetchall()
    
    return render_template("artists.html", 
                          artists=artists,
                          all_countries=all_countries,
                          selected_country=country_filter,
                          selected_sort=sort_order)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/artists/add", methods=["POST"])
def add_artist():
    name = request.form.get("name")
    country = request.form.get("country")
    bio = request.form.get("bio")

    if not name:
        return redirect(url_for("artists_list"))

    photo_file = request.files.get("photo")
    photo_name = None

    if photo_file and photo_file.filename != "":
        filename = photo_file.filename
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        photo_file.save(save_path)
        photo_name = filename
  

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO artists (name, country, bio, photo)
        VALUES (?, ?, ?, ?)
    """, (name, country, bio, photo_name))
    conn.commit()
    conn.close()

    return redirect(url_for("artists_list"))

@app.route("/artists/<int:artist_id>")
def artist_page(artist_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM artists WHERE id = ?", (artist_id,))
    artist = c.fetchone()
    if not artist:
        conn.close()
        return "Artist not found", 404
    c.execute("SELECT * FROM albums WHERE artist_id = ? ORDER BY year DESC, title", (artist_id,))
    albums = c.fetchall()
    conn.close()
    return render_template("artist.html", artist=artist, albums=albums)

@app.route("/albums/add", methods=["POST"])
def add_album():
    title = request.form.get("title")
    artist_id = request.form.get("artist_id")
    year = request.form.get("year")
    genre_id = request.form.get("genre_id")
    tracks_count = request.form.get("tracks_count") or 0
    if not title or not artist_id:
        return redirect(url_for("artists_list"))
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO albums (title, artist_id, year, genre_id, tracks_count)
        VALUES (?, ?, ?, ?, ?)
    """, (title, artist_id, year or None, genre_id or None, int(tracks_count)))
    conn.commit()
    conn.close()
    return redirect(url_for("artist_page", artist_id=artist_id))

@app.route("/albums/<int:album_id>")
def album_page(album_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT a.*, ar.name as artist_name, g.name as genre_name
        FROM albums a
        LEFT JOIN artists ar ON a.artist_id = ar.id
        LEFT JOIN genres g ON a.genre_id = g.id
        WHERE a.id = ?
    """, (album_id,))
    album = c.fetchone()
    if not album:
        conn.close()
        return "Album not found", 404
    c.execute("SELECT * FROM tracks WHERE album_id = ? ORDER BY track_number", (album_id,))
    tracks = c.fetchall()
    conn.close()
    return render_template("album.html", album=album, tracks=tracks)

@app.route("/tracks/add", methods=["POST"])
def add_track():
    title = request.form.get("title")
    album_id = request.form.get("album_id")
    duration = request.form.get("duration")
    track_number = request.form.get("track_number") or None
    if not title or not album_id:
        return redirect(url_for("artists_list"))
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO tracks (title, album_id, duration, track_number) VALUES (?, ?, ?, ?)",
              (title, album_id, duration, track_number))

    c.execute("UPDATE albums SET tracks_count = (SELECT COUNT(*) FROM tracks WHERE album_id = ?) WHERE id = ?",
              (album_id, album_id))
    conn.commit()

    conn.close()
    return redirect(url_for("album_page", album_id=album_id))

@app.route("/genres")
def genres_list():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM genres ORDER BY name")
    genres = c.fetchall()
    conn.close()
    return render_template("genres.html", genres=genres)

@app.route("/genres/add", methods=["POST"])
def add_genre():
    name = request.form.get("name")
    if not name:
        return redirect(url_for("genres_list"))
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO genres (name) VALUES (?)", (name,))
        conn.commit()
    except Exception:
        pass
    conn.close()
    return redirect(url_for("genres_list"))

@app.route("/playlist")
def playlist_view():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT pt.id as pt_id, t.*, a.title as album_title, ar.name as artist_name
        FROM playlist_tracks pt
        JOIN tracks t ON pt.track_id = t.id
        JOIN albums a ON t.album_id = a.id
        JOIN artists ar ON a.artist_id = ar.id
        ORDER BY pt.added_at DESC
    """)
    items = c.fetchall()
    conn.close()
    return render_template("playlist.html", items=items)

@app.route("/playlist/add", methods=["POST"])
def playlist_add():
    track_id = request.form.get("track_id")
    if not track_id:
        return redirect(url_for("artists_list"))
    conn = get_db()
    c = conn.cursor()

    try:
        c.execute("INSERT INTO playlist_tracks (track_id) VALUES (?)", (track_id,))
        conn.commit()
    except Exception:
        pass
    conn.close()

    album_id = request.form.get("album_id")
    if album_id:
        return redirect(url_for("album_page", album_id=album_id))
    return redirect(url_for("playlist_view"))

@app.route("/playlist/remove/<int:pt_id>", methods=["POST"])
def playlist_remove(pt_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM playlist_tracks WHERE id = ?", (pt_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("playlist_view"))

@app.route("/api/albums/<int:album_id>")
def api_album(album_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM albums WHERE id = ?", (album_id,))
    album = c.fetchone()
    if not album:
        conn.close()
        return to_json({"error": "not found"}), 404
    c.execute("SELECT * FROM tracks WHERE album_id = ? ORDER BY track_number", (album_id,))
    tracks = c.fetchall()
    conn.close()
    return to_json({"album": dict(album), "tracks": [dict(t) for t in tracks]})

@app.route("/artists/<int:artist_id>/delete", methods = ["POST"])
def delete_artist(artist_id):
    conn = get_db()
    c = conn.cursor()

    c.execute("DELETE FROM tracks WHERE album_id IN (SELECT id FROM albums WHERE artist_id=?)", (artist_id,))
    c.execute("DELETE FROM albums WHERE artist_id=?", (artist_id,))
    
    c.execute("DELETE FROM artists WHERE id=?", (artist_id,))

    conn.commit()
    conn.close()

    return redirect("/artists")

@app.route("/albums/<int:album_id>/delete", methods =["POST"])
def delete_album(album_id):
    conn = get_db()
    c = conn.cursor()
    
    c.execute("DELETE FROM tracks WHERE album_id = ?",(album_id,))
    
    c.execute("DELETE FROM albums where id = ?", (album_id,))
    
    conn.commit()
    conn.close()
    return redirect(url_for("/artists"))

@app.route("/tracks/<int:track_id>/delete", methods=["POST"])
def delete_track(track_id):
    album_id = request.args.get("album_id")

    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("album_page", album_id=album_id))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
