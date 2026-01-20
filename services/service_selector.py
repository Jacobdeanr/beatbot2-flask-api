from models.service_type import ServiceType
YOUTUBE_URLS = ["youtube.com", "www.youtube.com", "youtu.be", "music.youtube.com", "m.youtube.com"]
SPOTIFY_URLS = ["spotify.com", "open.spotify.com"]

class ServiceSelector:
    def __init__(self):
        pass

    def _is_service_we_have(self, domain) -> bool:
        return any(domain in lst for lst in [YOUTUBE_URLS, SPOTIFY_URLS])

    def get_service(self, domain) -> ServiceType:
        host = domain

        if host in YOUTUBE_URLS:
            return ServiceType.YouTube
        if host in SPOTIFY_URLS:
            return ServiceType.Spotify
        return ServiceType.Unknown