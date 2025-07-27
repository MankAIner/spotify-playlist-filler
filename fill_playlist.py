#!/usr/bin/env python3
"""
fill_playlist.py
===================

This script reads a list of Spotify track identifiers from a file and adds
them to a specified playlist using the Spotify Web API. Duplicate tracks
already present in the target playlist are skipped.

Configuration is provided via environment variables so that secrets such
as your client ID and client secret never need to be checked into version
control. You can set these variables in a `.env` file or export them in
your shell before running the script.

Required environment variables:

```
SPOTIPY_CLIENT_ID       – your Spotify Developer client ID
SPOTIPY_CLIENT_SECRET   – your Spotify Developer client secret
SPOTIPY_REDIRECT_URI    – redirect URI configured in your Spotify app
SPOTIFY_USERNAME        – your Spotify username (user ID)
SPOTIFY_PLAYLIST_ID     – the ID of the playlist to modify
```

Optional environment variables:

```
TRACKS_FILE             – path to file containing track IDs/URIs (default: tracks.txt)
```

The tracks file should contain one track URI or ID per line. Both full
spotify URIs (e.g. `spotify:track:6rqhFgbbKwnb9MLmUQDhG6`) and plain IDs
(e.g. `6rqhFgbbKwnb9MLmUQDhG6`) are accepted.

Usage:

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables (see above).
3. Place your track list into `tracks.txt` or set TRACKS_FILE.
4. Run the script: `python fill_playlist.py`

The script will open a browser window on first run to prompt you to
authorize access. After authorization, a cached token is stored in
`~/.cache/spotify_token`, so subsequent runs will not require logging in
again until the token expires.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable, List, Set

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
except ImportError as exc:
    print(
        "Missing dependency: spotipy. Install it with 'pip install spotipy' or via requirements.txt.",
        file=sys.stderr,
    )
    raise


def read_track_ids(file_path: Path) -> List[str]:
    """Read track URIs or IDs from a file and normalize to plain IDs.

    Lines that are empty or start with a '#' are ignored.

    Args:
        file_path: Path to the file containing track identifiers.

    Returns:
        A list of normalized track IDs.
    """
    ids: List[str] = []
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Accept full URIs like spotify:track:<id> or plain IDs
            if ":" in line:
                parts = line.split(":")
                track_id = parts[-1]
            else:
                track_id = line
            if track_id:
                ids.append(track_id)
    return ids


def get_existing_track_ids(sp: spotipy.Spotify, playlist_id: str) -> Set[str]:
    """Fetch all track IDs currently in the playlist.

    Spotify paginates playlist items; this function handles pagination
    automatically.

    Args:
        sp: An authenticated Spotipy client.
        playlist_id: ID of the playlist to inspect.

    Returns:
        A set of track IDs already in the playlist.
    """
    existing: Set[str] = set()
    offset = 0
    limit = 100
    while True:
        response = sp.playlist_items(playlist_id, offset=offset, limit=limit, fields="items.track.id,total")
        items = response.get("items", [])
        for item in items:
            track = item.get("track")
            if track and track.get("id"):
                existing.add(track["id"])
        offset += limit
        if len(items) < limit:
            break
    return existing


def add_tracks_to_playlist(sp: spotipy.Spotify, playlist_id: str, track_ids: Iterable[str]) -> None:
    """Add tracks to a playlist in batches, skipping duplicates.

    Args:
        sp: An authenticated Spotipy client.
        playlist_id: ID of the playlist to modify.
        track_ids: Iterable of track IDs to add.
    """
    # Fetch existing tracks once to avoid duplicates
    existing = get_existing_track_ids(sp, playlist_id)
    to_add: List[str] = [tid for tid in track_ids if tid not in existing]
    if not to_add:
        print("No new tracks to add; playlist already contains all provided songs.")
        return
    print(f"Adding {len(to_add)} new tracks to playlist {playlist_id}...")
    # Spotify API allows up to 100 tracks per add request
    batch_size = 100
    for start in range(0, len(to_add), batch_size):
        batch = to_add[start : start + batch_size]
        sp.playlist_add_items(playlist_id, batch)
        print(f"Added {len(batch)} tracks.")
    print("All tracks added successfully.")


def main() -> None:
    # Load configuration from environment variables
    client_id = os.environ.get("SPOTIPY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.environ.get("SPOTIPY_REDIRECT_URI")
    username = os.environ.get("SPOTIFY_USERNAME")
    playlist_id = os.environ.get("SPOTIFY_PLAYLIST_ID")
    tracks_file = Path(os.environ.get("TRACKS_FILE", "tracks.txt"))

    if not all([client_id, client_secret, redirect_uri, username, playlist_id]):
        print(
            "Missing configuration. Please set SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, "
            "SPOTIPY_REDIRECT_URI, SPOTIFY_USERNAME and SPOTIFY_PLAYLIST_ID environment variables.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not tracks_file.exists():
        print(f"Tracks file '{tracks_file}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Initialize OAuth handler
    scope = "playlist-modify-public playlist-modify-private"
    oauth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        cache_path=str(Path.home() / ".cache/spotify_token"),
        username=username,
    )
    sp = spotipy.Spotify(auth_manager=oauth)
    # Read tracks
    track_ids = read_track_ids(tracks_file)
    if not track_ids:
        print("No track IDs found in input file; nothing to do.")
        return
    add_tracks_to_playlist(sp, playlist_id, track_ids)


if __name__ == "__main__":
    main()
