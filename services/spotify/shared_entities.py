from dataclasses import dataclass

@dataclass(frozen=True)
class SpotifyFollowers():
    href:str
    total:int

@dataclass(frozen=True)
class SpotifyExternalIDs():
    isrc:str
    ean:str
    upc:str

@dataclass(frozen=True)
class SpotifyImage():
    height:int
    url:str 
    width:int