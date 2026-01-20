from dataclasses import dataclass
from .shared_entities import SpotifyFollowers, SpotifyImage

@dataclass(frozen=True)
class SpotifySimpleArtist():
    external_url:str
    href:str
    id:str
    name:str
    type:str
    uri:str
    
@dataclass(frozen=True)
class SpotifyArtist():
    external_urls:str
    followers:SpotifyFollowers
    genres:list[str]
    href:str
    id:str
    images:list[SpotifyImage]
    name:str
    popularity:int
    type:str
    uri:str