from dataclasses import dataclass, field
from .artists import SpotifySimpleArtist
from .shared_entities import SpotifyImage

@dataclass(frozen=True)
class SpotifySimpleAlbum:
    album_type:str
    artists:list[SpotifySimpleArtist]
    external_url:str
    href:str
    id:str
    is_playable:bool
    images:list[SpotifyImage]
    name:str
    release_date:str
    release_date_precision:str
    total_tracks:int
    type:str
    uri:str

@dataclass(frozen=True)
class SpotifyAlbumTrack:
    artists: list[SpotifySimpleArtist]
    disc_number:int
    duration_ms:int
    explicit:bool
    external_urls:str
    href:str
    id:str
    is_local:bool
    name:str
    preview_url:str
    track_number:int
    type:str
    uri:str

@dataclass(frozen=True)
class SpotifyAlbumTrackSearch:
    href: str
    limit: int
    next: str
    offset: int
    previous: str
    total:int
    items: list[SpotifyAlbumTrack] = field(default_factory=list)

@dataclass(frozen=True)
class SpotifyAlbum:
    album_type:str
    artists:list[SpotifySimpleArtist]
    external_urls:str
    genres: list[str]
    href:str
    id:str
    images:list[SpotifyImage]
    label:str
    name: str
    popularity:int
    release_date:str
    release_date_precision:str
    total_tracks:int
    type:str
    uri:str
    tracks: SpotifyAlbumTrackSearch