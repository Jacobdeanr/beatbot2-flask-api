from urllib.parse import urlparse, parse_qs, urlencode
import re
from typing import Optional

_YT_ID_PREFIX_RE = re.compile(r"^[A-Za-z0-9_-]+")
_SPOTIFY_URI_RE = re.compile(r"^spotify:(track|playlist|album):([A-Za-z0-9]+)$")

class UrlParser:
    def __init__(self):
        pass

    def _is_url(self, input: str) -> bool:
        raw = input.strip()
        try:
            result = urlparse(raw)
            return all([result.scheme, result.netloc]) 
        except AttributeError:
        # Handles cases where the input is not a string
            return False
        except ValueError:
            # Handles cases with invalid characters or structure
            return False
        
    def parse_spotify_ref(self, text: str) -> Optional[tuple[str, str]]:
        """
        Returns (kind, id) where kind in {"track","playlist","album"}.
        Supports:
        - spotify:track:<id>
        - https://open.spotify.com/track/<id>?si=...
        - https://open.spotify.com/playlist/<id>?si=...
        """
        t = text.strip()
        m = _SPOTIFY_URI_RE.match(t)
        if m:
            return (m.group(1), m.group(2))

        if not self._is_url(t):
            return None

        p = urlparse(t)

        parts = [seg for seg in p.path.split("/") if seg]
        # open.spotify.com/<kind>/<id>
        if len(parts) >= 2 and parts[0] in ("track", "playlist", "album", "artist"):
            return (parts[0], parts[1])

        return None
        
    
    def canonicalize_youtube_url(self, url: str) -> str:
        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        path = parsed.path or ""

        # TODO: need to return valueerror for this
        # "https://www.youtube.com/watch?v=eVLS4hAmLtI&list=RDeVLS4hAmLtI&start_radio=1" # Unsupported playlist (anything with &start_radio will fail. Refuse outright.)

        if not host:
            raise ValueError(f"Invalid URL (missing host): {url}")

        # Convert youtu.be short links to watch URLs
        if host == "youtu.be":
            vid = path.lstrip("/").split("/", 1)[0]
            if not vid:
                raise ValueError(f"Invalid YouTube short URL (missing video id): {url}")
            return f"https://www.youtube.com/watch?v={vid}"

        # Normalize any *.youtube.com (including music.youtube.com) to www.youtube.com
        if host == "youtube.com" or host.endswith(".youtube.com"):
            host = "www.youtube.com"
        else:
            raise ValueError(f"Not a YouTube URL: {url}")

        qs = parse_qs(parsed.query)

        # Validate supported URL forms
        video_id = None
        playlist_id = None

        # Reject YouTube "radio/mix" URLs (not a real playlist)
        if "start_radio" in qs or "radio" in qs:
            raise ValueError(f"Unsupported YouTube radio URL: {url}")

        list_id = (qs.get("list") or [None])[0]
        if list_id and list_id.startswith("RD"):
            raise ValueError(f"Unsupported YouTube mix/radio playlist: {url}")

        if path == "/watch":
            video_id = (qs.get("v") or [None])[0]
            if not video_id:
                raise ValueError(f"Invalid YouTube watch URL (missing v=): {url}")

        elif path == "/playlist":
            playlist_id = (qs.get("list") or [None])[0]
            if not playlist_id:
                raise ValueError(f"Invalid YouTube playlist URL (missing list=): {url}")

        elif path.startswith("/shorts/"):
            video_id = path.split("/", 3)[2] if len(path.split("/")) > 2 else None
            if not video_id:
                raise ValueError(f"Invalid YouTube shorts URL (missing id): {url}")

        elif path.startswith("/embed/"):
            video_id = path.split("/", 3)[2] if len(path.split("/")) > 2 else None
            if not video_id:
                raise ValueError(f"Invalid YouTube embed URL (missing id): {url}")

        else:
            raise ValueError(f"Unsupported YouTube URL (not a video/playlist): {url}")

        # Keep only the params you care about
        keep: dict[str, str] = {}
        for k in ("v", "list", "t", "start"):
            if k in qs and qs[k]:
                keep[k] = qs[k][0]

        return parsed._replace(
            scheme="https",
            netloc=host,
            path=path,
            query=urlencode(keep),
            fragment="",
        ).geturl()

    def playlist_id_from_url(self, url: str) -> Optional[str]:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        pid = (qs.get("list") or [None])[0]
        if not pid:
            return None

        pid = pid.strip().split()[0]  # drop accidental whitespace/newlines
        m = _YT_ID_PREFIX_RE.match(pid)  # keep only valid id prefix
        return m.group(0) if m else None
        
    def get_domain(self, url: str) -> str | None:
        if not self._is_url(url):
            return None
        
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        return host