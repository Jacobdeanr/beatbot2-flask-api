from typing import Iterator, Optional
from services.spotify.albums import SpotifyAlbum, SpotifyAlbumTrack
from services.spotify.artists import SpotifyArtist, SpotifySimpleArtist
from services.spotify.playlists import SpotifyPlaylist
from services.spotify.spotify_service import SpotifyService
from services.spotify.tracks import SpotifyTrack

class SpotifyExpansionHelper:
    def __init__(self, spotify: SpotifyService):
        self._spotify = spotify
    
    def _track_to_string(self, track: SpotifyTrack) -> str:
        artist = track.artists[0].name
        title = track.name
        return f"{artist} - {title}"

    def _artists_to_string(self, artists: list[SpotifySimpleArtist]) -> str:
        names = [a.name.strip() for a in artists if a and a.name]
        return ", ".join(names).strip()

    def _album_track_to_query(self, t: SpotifyAlbumTrack) -> Optional[str]:
        artist = self._artists_to_string(t.artists)
        title = (t.name or "").strip()
        if not artist or not title:
            return None
        return f"{artist} - {title}"

    def to_search_queries(self, obj, *, max_items: int = 500) -> Iterator[str]:
        if isinstance(obj, SpotifyTrack):
            yield self._track_to_string(obj)
            return

        # SpotifyArtist: fetch top songs (SpotifyTrack list)
        if isinstance(obj, SpotifyArtist):
            tracks: list[SpotifyTrack] = self._spotify.get_artist_top_songs(obj.id)
            for t in tracks[:max_items]:
                yield self._track_to_string(t)
            return

        # SpotifyPlaylist: has playlist.tracks.items -> each has .track: SpotifyTrack
        if isinstance(obj, SpotifyPlaylist):
            print("Playlist")
            tracks: list[SpotifyTrack] = self._spotify.get_playlist_tracks(obj.id, max_items=max_items)
            for t in tracks:
                yield self._track_to_string(t)
            return

        # SpotifyAlbum: your service method returns SpotifyAlbumTrack list (not SpotifyTrack)
        if isinstance(obj, SpotifyAlbum):
            album_tracks = self._spotify.get_album_tracks(obj.id, max_items=max_items)
            for at in album_tracks:
                q:SpotifyAlbumTrack = self._album_track_to_query(at)
                if q:
                    yield q
            return

        # Unknown: yield nothing
        return
