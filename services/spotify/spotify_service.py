import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from util.utilities import load_env, require_env

#Base models
from .albums import *
from .artists import *
from .playlists import *
from .shared_entities import *
from .tracks import *

def create_spotify_client() -> spotipy.Spotify:
    env = load_env()
    client_id = require_env(env, "SPOTIFY_CLIENT_ID")
    client_secret = require_env(env, "SPOTIFY_CLIENT_SECRET")
    creds = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    return spotipy.Spotify(client_credentials_manager=creds)

#Singleton class called SpotifyService
class SpotifyService:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_client()
        return cls._instance
    
    def __str__(self):
        return "Spotify Service"
    
    def __repr__(self) -> str:
        return "Spotify Service"

    #Utilities
    def _initialize_client(self):
        self.spotify_client = create_spotify_client()

    def _create_spotify_simple_artist(self, artist_data) -> SpotifySimpleArtist:
        return SpotifySimpleArtist(
            external_url=artist_data.get('external_urls', {}).get('spotify', 'default_url'),
            href=artist_data['href'],
            id=artist_data['id'],
            name=artist_data['name'],
            type=artist_data['type'],
            uri=artist_data['uri']
        )

    def _create_spotify_image(self, image_data) -> SpotifyImage:
        return SpotifyImage(
            height=image_data['height'],
            url=image_data['url'],
            width=image_data['width']
        )
    
    
    # Albums
    def _create_spotify_album_track_search(self,album_data: dict) -> SpotifyAlbumTrackSearch:
        return SpotifyAlbumTrackSearch(
            href = album_data['href'],
            limit = album_data['limit'],
            next = album_data['next'],
            offset = album_data['offset'],
            previous = album_data['previous'],
            total = album_data['total'],
            items = [self._create_spotify_album_track(item) for item in album_data['items']]
        ) 
     
    def _create_spotify_album_track(self,album_data: dict) -> SpotifyAlbumTrack:
        return SpotifyAlbumTrack(
            artists=[self._create_spotify_simple_artist(artist) for artist in album_data['artists']],
            disc_number=album_data['disc_number'],
            duration_ms=album_data['duration_ms'],
            explicit=album_data['explicit'],
            external_urls=album_data.get('external_urls', {}).get('spotify', 'default_url'),
            href=album_data['href'],
            id=album_data['id'],
            is_local=album_data['is_local'],
            name=album_data['name'],
            preview_url=album_data['preview_url'],
            track_number=album_data['track_number'],
            type=album_data['type'],
            uri=album_data['uri']

        )
    
    def _create_spotify_track_list(self, tracks: list[dict]) -> list[SpotifyTrack]:
        """
        Helper method to create a list of SpotifyTrack objects from a list of track data dictionaries.

        :param tracks: A list of dictionaries containing track data.
        :return: A list of SpotifyTrack objects.
        """
        tracklist = []
        for track in tracks:
            spotify_track = self._create_spotify_track(track)
            tracklist.append(spotify_track)
        return tracklist

    # Tracks
    def _create_spotify_simple_album(self,album_data: dict) -> SpotifySimpleAlbum:
        return SpotifySimpleAlbum(album_type = album_data['album_type'],
            artists = [self._create_spotify_simple_artist(data) for data in album_data['artists']],
            external_url = album_data['external_urls']['spotify'],
            href = album_data['href'],
            id = album_data['id'],
            is_playable = False,
            images = [self._create_spotify_image(image) for image in album_data['images']],
            name = album_data['name'],
            release_date = album_data['release_date'],
            release_date_precision = album_data['release_date_precision'],
            total_tracks = album_data['total_tracks'],
            type = album_data['type'],
            uri = album_data['uri'],
        )
    
    def _create_spotify_track(self, track_data: dict) -> SpotifyTrack:
        try:
            st = SpotifyTrack(
                album=self._create_spotify_simple_album(track_data['album']),
                artists=[self._create_spotify_simple_artist(data) for data in track_data['artists']],
                disc_number=track_data['disc_number'],
                duration_ms=track_data['duration_ms'],
                explicit=track_data['explicit'],
                external_ids=None,
                external_urls=track_data['external_urls']['spotify'],
                href=track_data['href'],
                id=track_data['id'],
                is_local=track_data['is_local'],
                is_playable=False,
                restrictions=None,
                name=track_data['name'],
                popularity=track_data['popularity'],
                track_number=track_data['track_number'],
                type=track_data['type'],
                uri=track_data['uri'],
                preview_url=track_data['preview_url']
            )
        except Exception:
            return
        return st

    def _create_spotify_track_search(self,track_data: dict) -> SpotifyTrackSearch:
        return SpotifyTrackSearch(
            href=track_data['href'],
            limit=track_data['limit'],
            next=track_data['next'],
            offset=track_data['offset'],
            previous=track_data['previous'],
            total=track_data['total'],
            items=self._create_spotify_track_list(track_data['items'])
        )
   

    # Playlists
    def _create_spotify_playlist_track_search(self, playlist_data: dict) -> SpotifyPlaylistTrackSearch:
        return SpotifyPlaylistTrackSearch(
            href=playlist_data['href'],
            limit=playlist_data['limit'],
            next=playlist_data['next'],
            offset=playlist_data['offset'],
            previous=playlist_data['previous'],
            total=playlist_data['total'],
            items=[self._create_spotify_playlist_track_items(item) for item in playlist_data['items']]
        )
    
    def _create_spotify_playlist_track_items(self, item: dict) -> SpotifyPlaylistTrackItems:
        return SpotifyPlaylistTrackItems(
            added_at=item['added_at'],
            added_by=item['added_by']['external_urls']['spotify'],
            is_local=item['is_local'],
            track=self._create_spotify_track(item['track'])
        )


    # Getters by ID
    def get_album_by_id(self,album_id:str) -> SpotifyAlbum:
        try:
            response = self.spotify_client.album(album_id=album_id)
        except Exception as e:
            return
        return SpotifyAlbum(
            album_type = response['album_type'],
            artists = [self._create_spotify_simple_artist(data) for data in response['artists']],
            external_urls = response['external_urls']['spotify'],
            genres = response['genres'],
            href = response['href'],
            id = response['id'],
            images = [self._create_spotify_image(image) for image in response['images']],
            label = response['label'],
            name = response['name'],
            popularity = response['popularity'],
            release_date = response['release_date'],
            release_date_precision = response['release_date_precision'],
            total_tracks = response['total_tracks'],
            type = response['type'],
            uri = response['uri'],
            tracks = self._create_spotify_album_track_search(response['tracks'])
        )
    
    def get_track_by_id(self, track_id:str) -> SpotifyTrack:
        response = self.spotify_client.track(track_id=track_id)
        return self._create_spotify_track(response)
    
    def get_playlist_by_id(self,playlist_id:str) -> SpotifyPlaylist:
        try:
            response = self.spotify_client.playlist(playlist_id=playlist_id)
        except Exception as exc:
            return
        return SpotifyPlaylist(
            collaborative=response['collaborative'],
            description=response['description'],
            external_urls=response['external_urls']['spotify'],
            followers=response['followers']['total'],
            href=response['href'],
            id=response['id'],
            images=[self._create_spotify_image(image) for image in response['images']],
            name=response['name'],
            owner=response['owner'],
            public=response['public'],
            snapshot_id=response['snapshot_id'],
            tracks=self._create_spotify_playlist_track_search(response['tracks']),
            type=response['type'],
            uri=response['uri']            
        )


    def get_artist_by_id(self,artist_id:str) -> SpotifyArtist:
        response = self.spotify_client.artist(artist_id=artist_id)
        return SpotifyArtist(
            external_urls=response['external_urls']['spotify'],
            followers=response['followers']['total'],
            genres=response['genres'],
            href=response['href'],
            id=response['id'],
            images=[self._create_spotify_image(image) for image in response['images']],
            name=response['name'],
            popularity=response['popularity'],
            type=response['type'],
            uri=response['uri']
        )
    
    # Searches
    def search_artist(self, query, limit) -> list[SpotifySimpleArtist]:
        result = self.spotify_client.search(query, limit=limit, type='artist')
        return [self._create_spotify_simple_artist(data) for data in result['artists']['items']]
    
    def perform_search(self, query: str, limit=1) -> list[SpotifyTrack]:
        response = self.spotify_client.search(query, limit=limit, type='track')
        return self._create_spotify_track_list(response['tracks']['items'])
    
    def get_artist_top_songs(self, artist_id:str) -> list[SpotifyTrack]:
        response = self.spotify_client.artist_top_tracks(artist_id=artist_id)
        return self._create_spotify_track_list(response['tracks'])
    
    
    #Recommendation Engine stuff
    def get_track_recommendations(self, seed_artists: list[str] = None, seed_tracks: list[str] = None, search_limit: int = 20, country: str = 'US') -> list[SpotifyTrack]:
        """
        Fetches track recommendations based on provided seed artists and/or tracks.

        :param seed_artists: A list of artist IDs to use as seed artists.
        :param seed_tracks: A list of track IDs to use as seed tracks.
        :param search_limit: The number of tracks to limit the search to.
        :param country: The country code to use for the recommendations.
        :return: A list of SpotifyTrack objects.
        """
        # Ensure at least one of seed_artists or seed_tracks is provided
        if not seed_artists and not seed_tracks:
            raise ValueError("At least one of seed_artists or seed_tracks must be provided.")

        try:
            response = self.spotify_client.recommendations(seed_artists=seed_artists, seed_tracks=seed_tracks, limit=search_limit, country=country)
            return self._create_spotify_track_list(response['tracks'])
        except Exception as e:
            # Handle exceptions such as network errors, API limits, or incorrect parameters
            print(f"An error occurred while fetching track recommendations: {e}")
            return []

    def get_playlist_tracks(self, playlist_id: str, *, max_items: int = 500) -> list["SpotifyTrack"]:
        """
        Returns up to max_items SpotifyTrack objects for a playlist (public playlists work with client credentials).
        """
        tracks: list["SpotifyTrack"] = []
        offset = 0
        page_size = 100
        try:
            while len(tracks) < max_items:
                resp = self.spotify_client.playlist_items(
                    playlist_id,
                    limit=page_size,
                    offset=offset,
                    additional_types=["track"],
                )

                items = resp.get("items") or []
                if not items:
                    break

                for it in items:
                    t = it.get("track")
                    if not t or t.get("type") != "track":
                        continue
                    try:
                        tracks.append(self._create_spotify_track(t))
                    except Exception:
                        # Skip malformed items
                        continue

                    if len(tracks) >= max_items:
                        break

                if not resp.get("next"):
                    break

                offset += len(items)
        except Exception as e:
            return

        return tracks

    def get_album_tracks(self, album_id: str, *, max_items: int = 500) -> list[SpotifyAlbumTrack]:
        """
        Return up to max_items tracks from an album, paging through the Spotify API.
        Uses the album_tracks endpoint (max 50 per page).
        """
        out: list[SpotifyAlbumTrack] = []
        offset = 0
        limit = 50

        while len(out) < max_items:
            resp = self.spotify_client.album_tracks(album_id, limit=limit, offset=offset)
            items = resp.get("items") or []
            if not items:
                break

            for item in items:
                try:
                    out.append(self._create_spotify_album_track(item))
                except Exception:
                    # skip malformed items
                    continue

                if len(out) >= max_items:
                    break

            if not resp.get("next"):
                break

            offset += len(items)

        return out

#This only exists to test the API
#def main():
#    spotify = SpotifyService()
   
#    while True:
#        user_input = input('\nEnter something to search:\n')
#
        #Search an artist and a track
#        found_tracks:SpotifyTrack = spotify.perform_search(user_input,1)
#        track = found_tracks.items[0]
#        printable_track_artists = ', '.join([artist.name for artist in track.artists])
#        track_id = track.id
#        print(track_id)
#        tracks_by_id:list[SpotifyTrack] = spotify.get_track_by_id(track_id)
#        #print(f'\nFound:\n{printable_track_artists} - {track.name} - Track ID: {track.id}\nAlbum: {track.album.name} - Album ID: {track_id}\n Album Image: {track.album.images[1].url}\n Album Height: {track.album.images[1].height}\n Album Width: {track.album.images[1].width}\n')
#        for item in tracks_by_id:
#            pprint.pprint(item)
#
#        #Lookup a track by its ID
#    
#        #Ask if the user wants to get the Album, the artist's top tracks, or track recommendations.
#        print('Would you like to get the Album, the artist\'s top tracks, or similar tracks?')
#        user_input = input('Enter \'album\', \'top\', \'song\', or \'similar\':\n')
#
#        #switch on user input
#        if user_input == 'album':
#            #Build album request. Returns a tuple of song name, artist, and track id.
#            album_id = track.album.id
#            print(f'\nLooking up album by ID: {album_id}\n')
#            tracks_on_album:list[tuple] = spotify.get_track_names_by_album_id(album_id)
#            print(f'\nFound {len(tracks_on_album)} tracks on Album Name: {tracks_on_album[0][3].name}')
#            for track_info in tracks_on_album:
#                print(f'{track_info[0]} - {track_info[1]}')
#
#            #ask user if they want to add the album to queue
#            print('\nWould you like to add the album to queue?')
#            user_input = input('Enter \'yes\' or \'no\':\n')
#            if user_input == 'yes':
#                print(f'Added {len(tracks_on_album)} tracks to queue')
#            else:
#                print('\nNo tracks added to queue')
#
#
#        elif user_input == 'top':
#            #Get a list of that artist's top tracks.
#            artist_id:str = tracks_by_id[0].artists[0].id
#            print(f"\nHere are {tracks_by_id[0].artists[0].name}'s top songs:\n")
#            top_track_list:list[SpotifyTrack] = spotify.get_artist_top_songs(artist_id)
#            for track_info in top_track_list:
#                print(f'{track_info.artists[0].name} - {track_info.name}')
#            
#            #ask user if they want to add the tracks to queue
#            print('\nWould you like to add the tracks to queue?')
#            user_input = input('Enter \'yes\' or \'no\':\n')
#            if user_input == 'yes':
#                print(f'Added {len(top_track_list)} tracks to queue')
#            else:
#                print('\nNo tracks added to queue')
#
#        elif user_input == 'song':
#            print(f'\nFound: {tracks_by_id[0].artists[0].name} - {tracks_by_id[0].name}\n')
#            
#            #ask user if they want to add the track to queue
#            print('\nWould you like to add the track to queue?')
#            user_input = input('Enter \'yes\' or \'no\':\n')
#            if user_input == 'yes':
#                print(f'Added {tracks_by_id[0].name} to queue')
#            else:
#                print('\nNo tracks added to queue')
#            
#        elif user_input == 'similar':
#            #Similar tracks based on track id.
#            print(f'\nSimilar Tracks that you might enjoy based on track: {tracks_by_id[0].artists[0].name} - {tracks_by_id[0].name} - {track_id}')
#            recommended_track_list:list[SpotifyTrack] = spotify.get_track_recommendations_by_track_ids([track_id],20)
#            for track in recommended_track_list:
#                print(f'{track.album.artists[0].name} - {track.name}')
#            
#            #ask user if they want to add the recommendations to queue
#            print('\nWould you like to add the similar tracks to queue?')
#            user_input = input('Enter \'yes\' or \'no\':\n')
#            if user_input == 'yes':
#                print(f'Added {len(recommended_track_list)} tracks to queue')
#            else:
#                print('\nNo tracks added to queue')

#if __name__ == "__main__":
#    main()