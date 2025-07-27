"""Unit tests for fill_playlist.py.

These tests cover the core helper functions in the fill_playlist module
without requiring an actual network connection or the real spotipy
library. A dummy `spotipy` module is inserted into `sys.modules` so
that the module can be imported even when spotipy is not installed.
"""

from __future__ import annotations

import sys
import types
import tempfile
from pathlib import Path
import unittest

# Insert a minimal dummy spotipy module to satisfy imports in the
# module under test. The real spotipy library is not available in
# this environment, but the functions we test do not rely on any
# functionality from spotipy itself. We need to create proper module
# objects so that ``from spotipy.oauth2 import SpotifyOAuth`` works.
dummy_spotipy = types.ModuleType("spotipy")
dummy_spotipy.Spotify = object  # placeholder for the Spotify client class
dummy_oauth = types.ModuleType("spotipy.oauth2")
dummy_oauth.SpotifyOAuth = object  # placeholder for the OAuth handler
dummy_spotipy.oauth2 = dummy_oauth
sys.modules.setdefault("spotipy", dummy_spotipy)
sys.modules.setdefault("spotipy.oauth2", dummy_oauth)

# Now import the module under test. It's important this happens after
# we insert our dummy module so that the import will succeed. We use a
# relative import because the test file resides in the same package.
from . import fill_playlist  # type: ignore


class DummySpotifyClient:
    """A minimal stand‑in for spotipy.Spotify used in tests.

    The client captures calls made to ``playlist_items`` and
    ``playlist_add_items`` so that unit tests can assert against them.
    """

    def __init__(self, playlist_responses: list[dict]) -> None:
        # A list of responses that will be returned sequentially when
        # ``playlist_items`` is called. Each element should be a dict
        # mimicking the structure returned by the real API.
        self._playlist_responses = playlist_responses
        self.playlist_items_calls: int = 0
        self.added_batches: list[list[str]] = []

    def playlist_items(self, playlist_id: str, offset: int, limit: int, fields: str) -> dict:
        # Return the next response in the list. If there are no more
        # responses, return an empty page to signal completion.
        if self.playlist_items_calls < len(self._playlist_responses):
            response = self._playlist_responses[self.playlist_items_calls]
        else:
            response = {"items": []}
        self.playlist_items_calls += 1
        return response

    def playlist_add_items(self, playlist_id: str, items: list[str]) -> None:
        # Capture the batch of items being added so tests can inspect it.
        self.added_batches.append(items)


class ReadTrackIdsTests(unittest.TestCase):
    """Tests for the ``read_track_ids`` helper function."""

    def test_read_track_ids_ignores_comments_and_whitespace(self) -> None:
        # Create a temporary file with a mix of comments, blank lines and URIs/IDs.
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "tracks.txt"
            contents = """
            # This is a comment line

            6rqhFgbbKwnb9MLmUQDhG6
            spotify:track:60nZcImufyMA1MKQY3dcCH
            invalid:format:should:just:take:last
            """
            path.write_text(contents, encoding="utf-8")
            ids = fill_playlist.read_track_ids(path)
            # The parser should ignore empty lines and comments. It
            # should return only the last segment of colon‑separated
            # strings.
            expected = [
                "6rqhFgbbKwnb9MLmUQDhG6",
                "60nZcImufyMA1MKQY3dcCH",
                "last",
            ]
            self.assertEqual(ids, expected)


class GetExistingTrackIdsTests(unittest.TestCase):
    """Tests for the ``get_existing_track_ids`` helper function."""

    def test_get_existing_track_ids_paginates_results(self) -> None:
        # The helper uses a pagination size of 100. To force more than one
        # call we simulate a first page containing 100 items and a
        # second page containing one additional item. This ensures the
        # loop continues until the final page is fetched.
        first_page_items = [
            {"track": {"id": f"id{n}"}} for n in range(1, 101)
        ]
        second_page_items = [
            {"track": {"id": "id101"}},
        ]
        responses = [
            {"items": first_page_items},
            {"items": second_page_items},
        ]
        dummy_sp = DummySpotifyClient(responses)
        result = fill_playlist.get_existing_track_ids(dummy_sp, playlist_id="dummy")
        # The set should contain all 101 IDs.
        expected_ids = {f"id{n}" for n in range(1, 102)}
        self.assertEqual(result, expected_ids)
        # The helper should have called playlist_items twice (once per page).
        self.assertEqual(dummy_sp.playlist_items_calls, 2)


class AddTracksToPlaylistTests(unittest.TestCase):
    """Tests for ``add_tracks_to_playlist`` ensuring duplicates are skipped."""

    def test_add_tracks_skips_existing_and_batches(self) -> None:
        # Set up existing tracks so that "id1" is already in the playlist.
        responses = [
            {
                "items": [
                    {"track": {"id": "id1"}},
                ]
            },
        ]
        dummy_sp = DummySpotifyClient(responses)
        # Provide a list with duplicates and both existing and new IDs.
        track_ids = ["id1", "id2", "id2", "id3", "id4", "id5"]
        fill_playlist.add_tracks_to_playlist(dummy_sp, playlist_id="dummy", track_ids=track_ids)
        # After removing the existing track id1, the helper does not
        # deduplicate the remaining list. Therefore the batch should
        # contain id2 twice followed by id3, id4 and id5.
        expected_batch = ["id2", "id2", "id3", "id4", "id5"]
        # Should have called playlist_add_items once with the expected batch.
        self.assertEqual(dummy_sp.added_batches, [expected_batch])


if __name__ == "__main__":
    unittest.main()
