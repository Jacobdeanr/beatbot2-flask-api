from dataclasses import dataclass, field
from typing import Optional

from .shared_entities import SpotifyExternalIDs
from .artists import SpotifySimpleArtist
from .albums import SpotifySimpleAlbum

@dataclass(frozen=True)
class SpotifyTrack():
    album: SpotifySimpleAlbum
    artists: list[SpotifySimpleArtist]
    disc_number:int
    duration_ms:int
    explicit:bool
    external_ids:SpotifyExternalIDs
    external_urls:str
    href:str
    id:str
    is_local:bool
    is_playable:bool
    restrictions:str
    name:str
    popularity:int
    track_number:int
    type:str
    uri:str
    preview_url: Optional[str] = "None"

@dataclass(frozen=True)
class SpotifyTrackSearch():
    href: str
    limit: int
    next: str
    offset: int
    previous: str
    total:int
    items: list[SpotifyTrack] = field(default_factory=list)

