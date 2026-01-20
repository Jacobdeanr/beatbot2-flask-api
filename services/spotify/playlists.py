from dataclasses import dataclass, field
from .artists import SpotifySimpleArtist
from .shared_entities import SpotifyImage, SpotifyFollowers
from .tracks import SpotifyTrack

@dataclass(frozen=True)
class SpotifyPlaylistOwner():
    display_name: str
    external_urls: dict
    href: str
    id: str
    type: str
    uri: str

@dataclass(frozen=True)
class SpotifyPlaylistTrackItems():
    added_at: str
    added_by: SpotifySimpleArtist
    is_local: bool
    track: SpotifyTrack

@dataclass(frozen=True)
class SpotifyPlaylistTrackSearch():
    href: str
    limit: int
    next: str
    offset: int
    previous: str
    total: int
    items: list[SpotifyPlaylistTrackItems] = field(default_factory=list)

@dataclass(frozen=True)
class SpotifyPlaylist():
    collaborative: bool
    description: str
    external_urls: dict
    followers: SpotifyFollowers
    href: str
    id: str
    images: list[SpotifyImage]
    name: str
    owner: SpotifyPlaylistOwner
    public: bool
    snapshot_id: str
    tracks: SpotifyPlaylistTrackSearch
    type: str
    uri: str