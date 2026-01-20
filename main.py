from __future__ import annotations

import logging

from models.service_type import ServiceType
from services.url_parser import UrlParser
from services.service_selector import ServiceSelector
from services.service_resolver import ServiceResolver
from services.service_processor import ServiceProcessor
from services.spotify.spotify_service import SpotifyService
from services.spotify_expansion_helper import SpotifyExpansionHelper

class QueryParser:
    def __init__(self, resolver: ServiceResolver, service_processor: ServiceProcessor):
        self._resolver = resolver
        self._sp = service_processor

    def parse_query(self, query:str ):
        service: ServiceType = self._resolver.resolve_service(query)
        return self._sp.resolve_query(service, query)
    

def describe(obj) -> str:
    """
    This function is a "safe label maker" for debugging.

    It answers: "What shape is this thing?" without relying on class names.

    We detect by capabilities ("duck typing"):
    - If it has watch_url, it behaves like a YouTube video.
    - If it has video_urls, it behaves like a playlist.
    - If it has id/name, it behaves like a Spotify-ish model.
    - If it is a list, we describe its length and the shape of the first element.
    """

    if obj is None:
        return "Empty: None"

    # List-like
    if isinstance(obj, list):
        n = len(obj)
        if n == 0:
            return "List: empty"
        # Describe the first element by shape too (without class names)
        return f"List: len={n}, first=({describe(obj[0])})"

    # YouTube-ish: has watch_url
    watch_url = getattr(obj, "watch_url", None)
    if isinstance(watch_url, str) and watch_url.strip():
        video_id = getattr(obj, "video_id", None)
        title = getattr(obj, "title", None)
        bits = [f"Video: watch_url={watch_url!r}"]
        if isinstance(video_id, str) and video_id.strip():
            bits.append(f"video_id={video_id!r}")
        if isinstance(title, str) and title.strip():
            bits.append(f"title={title!r}")
        return ", ".join(bits)

    # Playlist-ish: has video_urls (do not list(...) it)
    video_urls = getattr(obj, "video_urls", None)
    if video_urls is not None:
        playlist_url = getattr(obj, "playlist_url", None) or getattr(obj, "url", None)
        bits = ["Playlist: has video_urls"]
        if isinstance(playlist_url, str) and playlist_url.strip():
            bits.append(f"playlist_url={playlist_url!r}")

        # Try to get a count if it is cheap. Some libs use lazy sequences.
        count_str = None
        try:
            count_str = str(len(video_urls))
        except Exception:
            count_str = "unknown"
        bits.append(f"count={count_str}")
        urls = []
        for v in video_urls:
            urls.append(v)

        bits.extend(urls)

        return ", ".join(bits)

    # Spotify-ish models: has id and/or name
    sid = getattr(obj, "id", None)
    name = getattr(obj, "name", None)
    if sid is not None or name is not None:
        bits = ["Model: spotify-like"]
        if isinstance(sid, str) and sid.strip():
            bits.append(f"id={sid!r}")
        if isinstance(name, str) and name.strip():
            bits.append(f"name={name!r}")
        return ", ".join(bits)

    # Fallback: show available keys-ish info without names
    # Keep it short to avoid dumping huge objects.
    attrs = []
    for key in ("url", "uri", "href", "type"):
        val = getattr(obj, key, None)
        if isinstance(val, str) and val.strip():
            attrs.append(f"{key}={val!r}")
    if attrs:
        return "Unknown object with hints: " + ", ".join(attrs)

    return "Unknown object (no known shape)"


def _setup_logging() -> None:
    logging.getLogger("spotipy").setLevel(logging.CRITICAL)
    logging.getLogger("spotipy").propagate = False

def build_parser() -> QueryParser:
    """
    Pure setup. No threads, no async needed.
    """
    _setup_logging()

    parser = UrlParser()
    selector = ServiceSelector()
    spotify = SpotifyService()

    resolver = ServiceResolver(parser=parser, selector=selector)
    service_processor = ServiceProcessor(url_parser=parser, spotify=spotify)

    query_parser = QueryParser(resolver, service_processor)
    return query_parser


def handle_empty_response() -> None:
    print("Results returned Empty")


def _mock_requests() -> list[str]:
    return [
        "https://www.youtube.com/watch?v=sVasknez9vY",
        "https://www.youtube.com/watch?v=sVasknez9vY&list=PLyYknuq7e2jb0QfbDhv0D_YZBTOpwtlMd",
        "https://open.spotify.com/track/2QGVKiAGTa1YcDqPMhAzF7",
        "https://open.spotify.com/artist/4LLpKhyESsyAXpc4laK94U",
        "https://open.spotify.com/playlist/1Z1gbgOZ0pe1OOsOVkosCU",
        "https://open.spotify.com/album/5sY6UIQ32GqwMLAfSNEaXb",
        "https://www.google.com",
        "www.google.com"
        ]


def main() -> None:
    qp:QueryParser = build_parser()
    
    for req in _mock_requests():
        parsed_item = qp.parse_query(req)
        print(req)
        print("->", describe(parsed_item))
        print()
        

        
    #print("Program finished.")

if __name__ == "__main__":
    main()