"""Database schema definitions for the Bible Art App."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Testament:
    id: Optional[int]
    name: str


@dataclass
class Story:
    id: Optional[int]
    title: str
    testament_id: int
    summary: str


@dataclass
class Character:
    id: Optional[int]
    name: str
    description: str


@dataclass
class Location:
    id: Optional[int]
    name: str
    region: str


@dataclass
class Artist:
    id: Optional[int]
    name: str
    style: str


@dataclass
class Artwork:
    id: Optional[int]
    title: str
    story_id: int
    artist_id: int
    location_id: int
    medium: str


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS testaments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    testament_id INTEGER NOT NULL,
    summary TEXT,
    FOREIGN KEY (testament_id) REFERENCES testaments(id)
);

CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    region TEXT
);

CREATE TABLE IF NOT EXISTS artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    style TEXT
);

CREATE TABLE IF NOT EXISTS artworks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    story_id INTEGER NOT NULL,
    artist_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    medium TEXT,
    FOREIGN KEY (story_id) REFERENCES stories(id),
    FOREIGN KEY (artist_id) REFERENCES artists(id),
    FOREIGN KEY (location_id) REFERENCES locations(id)
);

CREATE TABLE IF NOT EXISTS story_characters (
    story_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    PRIMARY KEY (story_id, character_id),
    FOREIGN KEY (story_id) REFERENCES stories(id),
    FOREIGN KEY (character_id) REFERENCES characters(id)
);
"""
