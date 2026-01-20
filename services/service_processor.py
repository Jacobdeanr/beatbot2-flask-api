from pytubefix import Search, YouTube, Playlist
from models.service_type import ServiceType
from services.url_parser import UrlParser
from services.spotify.spotify_service import SpotifyService
from services.spotify.albums import SpotifyAlbum
from services.spotify.artists import SpotifyArtist
from services.spotify.playlists import SpotifyPlaylist
from services.spotify.tracks import SpotifyTrack

SpotifyResult = SpotifyAlbum | SpotifyArtist | SpotifyPlaylist | SpotifyTrack

class ServiceProcessor:
    def __init__(self, url_parser:UrlParser, spotify:SpotifyService):
        self._parser = url_parser
        self._spotify = spotify

    def _handle_unknown(self, query):
        #print("Unknown service for requested URL:", query)
        return None

    def _handle_spotify(self, query) -> SpotifyResult | None:
        # open.spotify.com/<kind>/<id>
        kind, spotify_id = self._parser.parse_spotify_ref(query)
        match kind:
            case "album":
                results:SpotifyAlbum = self._spotify.get_album_by_id(spotify_id)
            case "artist":
                results:SpotifyArtist = self._spotify.get_artist_by_id(spotify_id)
            case "playlist":
                results:SpotifyPlaylist = self._spotify.get_playlist_by_id(spotify_id)
            case "track":
                results:SpotifyTrack = self._spotify.get_track_by_id(spotify_id)
            case _:
                return None
            
        if results is None:
            return None
        
        return results

    def _handle_youtube(self, query):
        try:
            canon = self._parser.canonicalize_youtube_url(query)
        except ValueError:
            return None

        pid = self._parser.playlist_id_from_url(canon)

        if pid:
            try:
                pl = Playlist(url=canon)
                return pl if pl.video_urls else None
            except Exception:
                return None

        try:
            return YouTube(canon)
        except Exception:
            return None 

    def _handle_search(self, query: str) -> Search:
        return Search(query)

    def resolve_query(self, service, query) -> SpotifyResult | Playlist | YouTube | Search | None:
        match service:
            case ServiceType.Unknown:
                result = self._handle_unknown(query)
            case ServiceType.Spotify:
                result = self._handle_spotify(query)
            case ServiceType.YouTube:
                result = self._handle_youtube(query)
            case ServiceType.Search:
                result = self._handle_search(query)
            case _: 
                return None
            
        return result
    
    # --------------------------------------------------
    # Figure out how to output data.
    # --------------------------------------------------
    def _desc_yt_playlist(self, playlist: Playlist) -> list[str]:
        out = []
        for u in playlist.video_urls:
            try:
                out.append(self._parser.canonicalize_youtube_url(u))
            except ValueError:
                continue
        return out
    
    def _desc_yt(self, video: YouTube) -> list[str] | None:
        try:
            return [self._parser.canonicalize_youtube_url(video.watch_url)]
        except ValueError:
            return None
    
    def _desc_yt_search(self, search: Search) -> list[str] | None:
        try:
            videos = search.videos
        except Exception:
            return None

        if not videos:
            return None

        try:
            return self._desc_yt(videos[0])
        except Exception:
            return None
    
    def _desc_spot_album(self,album: SpotifyAlbum) -> list[str]:
        output = []
        for item in album.tracks.items:
            # Album objects do not have "Track", but instead a different 'AlbumTrack' class. Cannot re-use _desc_spot_track
            desc = self._format_spotify_search_str(item.artists[0].name, item.name)
            output.append(desc)
        return output
    
    def _desc_spot_artist(self,artist: SpotifyArtist) -> list[str]:
        tracks: list[SpotifyTrack] = self._spotify.get_artist_top_songs(artist_id = artist.id)
        output = []
        for track in tracks:
            desc = self._format_spotify_search_str(track.artists[0].name, track.name)
            output.append(desc)
        return output
    
    def _desc_spot_playlist(self, playlist: SpotifyPlaylist) -> list[str]:
        output = []
        for item in playlist.tracks.items:
            desc = self._format_spotify_search_str(item.track.artists[0].name, item.track.name)
            output.append(desc)
        return output
    
    def _desc_spot_track(self, track: SpotifyTrack) -> list[str]:
        return [self._format_spotify_search_str(track.artists[0].name, track.name)]
    
    def _format_spotify_search_str(self,artist_name, track_name) -> str:
        return f"{artist_name} - {track_name}"
    
    def describe(self, obj) -> str | list[str] | None:
        if isinstance(obj, YouTube):
            desc = self._desc_yt(obj)
        elif isinstance(obj, Search):
            desc = self._desc_yt_search(obj)
        elif isinstance(obj, Playlist):
            desc = self._desc_yt_playlist(obj)
        elif isinstance(obj, SpotifyAlbum):
            desc = self._desc_spot_album(obj)
        elif isinstance(obj, SpotifyArtist):
            desc = self._desc_spot_artist(obj)
        elif isinstance(obj, SpotifyPlaylist):
            desc = self._desc_spot_playlist(obj)
        elif isinstance(obj, SpotifyTrack):
            desc = self._desc_spot_track(obj)
        else: 
            desc = None
        
        if desc is None:
                return None
        return desc
    
    def classify_input(self, obj) -> tuple[str, str]:
        if isinstance(obj, YouTube):
            return ("youtube", "video")
        if isinstance(obj, Playlist):
            return ("youtube", "playlist")
        if isinstance(obj, Search):
            return ("youtube", "search")
        if isinstance(obj, SpotifyAlbum):
            return ("spotify", "album")
        if isinstance(obj, SpotifyArtist):
            return ("spotify", "artist")
        if isinstance(obj, SpotifyPlaylist):
            return ("spotify", "playlist")
        if isinstance(obj, SpotifyTrack):
            return ("spotify", "track")
        return ("unknown", "unknown")

    def item_kind_for_obj(self, obj) -> str:
        # how the bot should interpret each item string
        if isinstance(obj, (YouTube, Playlist, Search)):
            return "youtube_url"
        # Spotify strings are not URLs (in your current output)
        if isinstance(obj, (SpotifyAlbum, SpotifyArtist, SpotifyPlaylist, SpotifyTrack)):
            return "search"
        return "unknown"


    # 

    def resolve_youtube_video(self, url: str) -> YouTube | None:
        # Canonicalize and reject unsupported radio URLs here
        try:
            canon = self._parser.canonicalize_youtube_url(url)
        except ValueError:
            return None

        # If someone accidentally passes a playlist URL, do not accept it here
        # (resolve endpoint expects a single playable item)
        pid = self._parser.playlist_id_from_url(canon)
        if pid:
            return None

        try:
            return YouTube(canon)
        except Exception:
            return None

    def resolve_youtube_search_first(self, query: str) -> YouTube | None:
        try:
            s = Search(query)
            videos = s.videos
        except Exception:
            return None

        if not videos:
            return None

        # videos[0] is usually a YouTube object already, but normalize anyway
        try:
            first = videos[0]
            return YouTube(first.watch_url)
        except Exception:
            return None

    def youtube_video_payload(self, yt: YouTube) -> dict:
        # Keep it minimal and stable. Add fields later if needed.
        # Some attributes may trigger extra fetches depending on library behavior.
        data: dict = {
            "kind": "youtube_url",
            "value": yt.watch_url,
        }

        # Optional fields; guard because these can sometimes throw
        try:
            data["title"] = yt.title
        except Exception:
            pass

        try:
            data["video_id"] = yt.video_id
        except Exception:
            pass

        try:
            data["author"] = yt.author
        except Exception:
            pass

        try:
            data["length_seconds"] = yt.length
        except Exception:
            pass

        return data
    
    def resolve_youtube_search_first(self, query: str) -> YouTube | None:
        try:
            s = Search(query)
            videos = s.videos
        except Exception:
            return None

        if not videos:
            return None

        # videos[0] is usually a YouTube object already, but normalize anyway
        try:
            first = videos[0]
            return YouTube(first.watch_url)
        except Exception:
            return None

    def youtube_video_payload(self, yt: YouTube) -> dict:
        # Keep it minimal and stable. Add fields later if needed.
        # Some attributes may trigger extra fetches depending on library behavior.
        data: dict = {
            "kind": "youtube_url",
            "value": yt.watch_url,
        }

        # Optional fields; guard because these can sometimes throw
        try:
            data["title"] = yt.title
        except Exception:
            pass

        try:
            data["video_id"] = yt.video_id
        except Exception:
            pass

        try:
            data["author"] = yt.author
        except Exception:
            pass

        try:
            data["length_seconds"] = yt.length
        except Exception:
            pass

        return data