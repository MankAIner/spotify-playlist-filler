# Spotify Playlist Filler

Dieses Repository enthaelt ein Python‑Skript, das eine Liste von Spotify‑Track‑IDs einliest und alle fehlenden Songs zu einer angegebenen Playlist hinzufuegt. So kannst du bequem eine Liste von Titeln definieren und sicherstellen, dass deine Playlist alle gewuenschten Lieder enthaelt, ohne doppelte Eintraege zu erzeugen.

## Einrichtung

1. **Spotify‑Entwicklerkonto anlegen**

   Erstelle unter <https://developer.spotify.com/dashboard> eine App. Notiere dir die `Client ID`, `Client Secret` und richte eine `Redirect URI` ein (z. B. `http://localhost:8888/callback`).

2. **Repository klonen und Abhaengigkeiten installieren**

   ```sh
   git clone <REPO_URL>
   cd spotify_playlist_filler
   python -m venv venv
   . venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Umgebungsvariablen setzen**

   Exportiere folgende Variablen (z. B. in deiner Shell oder in einer `.env`-Datei):

   ```sh
   export SPOTIPY_CLIENT_ID="<deine_client_id>"
   export SPOTIPY_CLIENT_SECRET="<dein_client_secret>"
   export SPOTIPY_REDIRECT_URI="http://localhost:8888/callback"
   export SPOTIFY_USERNAME="<dein_spotify_username>"
   export SPOTIFY_PLAYLIST_ID="<die_ziel_playlist_id>"
   # optional: Pfad zur Trackliste
   export TRACKS_FILE="tracks.txt"
   ```

   **Wichtig:** Gib deine `Client ID` und dein `Client Secret` nicht weiter und lade sie nicht in oeffentliche Repositories hoch.

4. **Trackliste vorbereiten**

   Lege eine Datei `tracks.txt` (oder eine andere Datei entsprechend `TRACKS_FILE`) an. Jede Zeile enthaelt entweder eine vollstaendige Spotify‑URI (`spotify:track:<ID>`) oder nur die Track‑ID. Zeilen, die mit `#` beginnen, werden ignoriert.

5. **Skript ausfuehren**

   ```sh
   python fill_playlist.py
   ```

   Beim ersten Lauf oeffnet sich ein Browserfenster, in dem du Spotify den Zugriff auf dein Konto erlauben musst. Danach werden alle Titel aus der Datei, die noch nicht in der Playlist vorhanden sind, hinzugefuegt.

## Funktionsweise

Das Skript verwendet die Bibliothek [Spotipy](https://spotipy.readthedocs.io/) zur Authentifizierung und Kommunikation mit der Spotify‑API. Es liest alle Eintraege in der angegebenen Playlist, vergleicht sie mit der Trackliste und fuegt anschliessend neue Songs in Batches von maximal 100 Titeln hinzu, da die API diese Grenze vorgibt.

## Haftungsausschluss

Dieses Projekt ist als Beispiel gedacht. Achte darauf, deine API‑Keys sicher aufzubewahren und nicht oeffentlich bereitzustellen. Die Nutzung der Spotify‑API unterliegt den [Spotify‑Nutzungsbedingungen](https://developer.spotify.com/terms/).
