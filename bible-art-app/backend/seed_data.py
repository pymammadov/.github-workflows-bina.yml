"""Seed script with sample Old and New Testament content."""

from database import get_connection, init_db


def seed() -> None:
    init_db()

    with get_connection() as conn:
        cursor = conn.cursor()

        testaments = ["Old Testament", "New Testament"]
        cursor.executemany(
            "INSERT OR IGNORE INTO testaments(name) VALUES (?)",
            [(name,) for name in testaments],
        )

        cursor.execute("SELECT id, name FROM testaments")
        testament_ids = {row["name"]: row["id"] for row in cursor.fetchall()}

        stories = [
            (
                "Creation",
                testament_ids["Old Testament"],
                "God creates the heavens, the earth, and all life in six days.",
            ),
            (
                "Noah's Ark",
                testament_ids["Old Testament"],
                "Noah builds an ark to preserve life through the flood.",
            ),
            (
                "David and Goliath",
                testament_ids["Old Testament"],
                "Young David defeats the giant Goliath with faith and courage.",
            ),
            (
                "Birth of Jesus",
                testament_ids["New Testament"],
                "Jesus is born in Bethlehem, fulfilling prophecy.",
            ),
            (
                "Sermon on the Mount",
                testament_ids["New Testament"],
                "Jesus teaches blessings, prayer, and righteous living.",
            ),
            (
                "Resurrection",
                testament_ids["New Testament"],
                "Jesus rises from the dead, bringing hope and salvation.",
            ),
        ]

        cursor.executemany(
            """
            INSERT OR IGNORE INTO stories(title, testament_id, summary)
            VALUES (?, ?, ?)
            """,
            stories,
        )

        locations = [
            ("Eden", "Ancient Near East"),
            ("Ararat", "Anatolia"),
            ("Valley of Elah", "Judah"),
            ("Bethlehem", "Judea"),
            ("Galilee", "Northern Israel"),
            ("Jerusalem", "Judea"),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO locations(name, region) VALUES (?, ?)",
            locations,
        )

        characters = [
            ("God", "Creator and sovereign over all."),
            ("Noah", "A righteous man chosen to build the ark."),
            ("David", "Future king of Israel."),
            ("Jesus", "Messiah and Son of God."),
            ("Mary", "Mother of Jesus."),
            ("Goliath", "Philistine giant warrior."),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO characters(name, description) VALUES (?, ?)",
            characters,
        )

        artists = [
            ("Miriam Hale", "Classical realism"),
            ("Ezra Cole", "Oil narrative scenes"),
            ("Naomi Rivers", "Contemporary watercolor"),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO artists(name, style) VALUES (?, ?)",
            artists,
        )

        cursor.execute("SELECT id, title FROM stories")
        story_ids = {row["title"]: row["id"] for row in cursor.fetchall()}

        cursor.execute("SELECT id, name FROM locations")
        location_ids = {row["name"]: row["id"] for row in cursor.fetchall()}

        cursor.execute("SELECT id, name FROM artists")
        artist_ids = {row["name"]: row["id"] for row in cursor.fetchall()}

        artworks = [
            (
                "Light Over Creation",
                story_ids["Creation"],
                artist_ids["Miriam Hale"],
                location_ids["Eden"],
                "Oil on canvas",
            ),
            (
                "Promise Through the Flood",
                story_ids["Noah's Ark"],
                artist_ids["Ezra Cole"],
                location_ids["Ararat"],
                "Tempera on wood",
            ),
            (
                "Stone of Courage",
                story_ids["David and Goliath"],
                artist_ids["Naomi Rivers"],
                location_ids["Valley of Elah"],
                "Watercolor",
            ),
            (
                "Star Over Bethlehem",
                story_ids["Birth of Jesus"],
                artist_ids["Miriam Hale"],
                location_ids["Bethlehem"],
                "Mixed media",
            ),
            (
                "Blessed Are",
                story_ids["Sermon on the Mount"],
                artist_ids["Naomi Rivers"],
                location_ids["Galilee"],
                "Ink and wash",
            ),
            (
                "Morning at the Tomb",
                story_ids["Resurrection"],
                artist_ids["Ezra Cole"],
                location_ids["Jerusalem"],
                "Oil on linen",
            ),
        ]

        cursor.executemany(
            """
            INSERT OR IGNORE INTO artworks(title, story_id, artist_id, location_id, medium)
            VALUES (?, ?, ?, ?, ?)
            """,
            artworks,
        )

        conn.commit()


if __name__ == "__main__":
    seed()
    print("Seeded database with Old and New Testament sample data.")
