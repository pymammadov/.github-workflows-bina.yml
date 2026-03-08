"""Flask API entrypoint for the Bible Art App."""

from flask import Flask, jsonify

from database import get_connection, init_db

app = Flask(__name__)


@app.route("/health")
def health_check():
    return jsonify({"status": "ok"})


@app.route("/api/testaments")
def list_testaments():
    with get_connection() as conn:
        rows = conn.execute("SELECT id, name FROM testaments ORDER BY id").fetchall()
    return jsonify([dict(row) for row in rows])


@app.route("/api/stories")
def list_stories():
    query = """
        SELECT stories.id, stories.title, stories.summary, testaments.name AS testament
        FROM stories
        JOIN testaments ON stories.testament_id = testaments.id
        ORDER BY stories.id
    """
    with get_connection() as conn:
        rows = conn.execute(query).fetchall()
    return jsonify([dict(row) for row in rows])


@app.route("/api/artworks")
def list_artworks():
    query = """
        SELECT artworks.id,
               artworks.title,
               artworks.medium,
               stories.title AS story,
               artists.name AS artist,
               locations.name AS location
        FROM artworks
        JOIN stories ON artworks.story_id = stories.id
        JOIN artists ON artworks.artist_id = artists.id
        JOIN locations ON artworks.location_id = locations.id
        ORDER BY artworks.id
    """
    with get_connection() as conn:
        rows = conn.execute(query).fetchall()
    return jsonify([dict(row) for row in rows])


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
