import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import pandas as pd
import subprocess
import requests
import spotipy as sp
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import youtube_dl
import json
from spotipy import Spotify
from spotipy.exceptions import SpotifyException
import sys




print("Fetching YT MUSIC")

user_input = input("Do you want to continue (yes/no): ")

if user_input.lower() == 'yes':
    print("Continuing to the next part...")
    # ... code for fetching Spotify data goes here ...
else:
    print("Stopping the program.")
    sys.exit()


''' youtube music'''

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
api_service_name = "youtube"
api_version = "v3"

client_secrets_file = "csgo.json"

yt_ids  = []
yt_titles = []  # To store video titles
yt_songs = []
problematic_videos = []

flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)

credentials = flow.run_local_server(port=8080)


youtube = googleapiclient.discovery.build(api_service_name,
                                              api_version,
                                              credentials=credentials)

request = youtube.playlistItems().list(
    part="snippet,contentDetails",
    playlistId="LM",
    maxResults=50
)
response_yt = request.execute()



print(response_yt['pageInfo']['totalResults']) #total


ydl_opts = {
    'quiet': True,  # Disable console output for youtube-dl
}

while response_yt:
    # Extract yt_ids from the current page and add them to yt_ids 
    for item in response_yt['items']:
        video_id = item['snippet']['resourceId']['videoId']
        video_title = item['snippet']['title']
        yt_titles.append(video_title)
        yt_ids .append(video_id)
        
        # Use youtube-dl to extract metadata
        video_url = f'https://www.youtube.com/watch?v={video_id}'
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                track = info.get('title', 'Unknown Track')
                rawartist = info.get('uploader', 'Unknown Artist')
                artist = rawartist.replace(" - Topic", "")
                yt_songs.append((track, artist))
        except (youtube_dl.utils.ExtractorError, youtube_dl.utils.DownloadError) as e:
            print(f"An error occurred while extracting information from the video {video_url}. Skipping...")
            problematic_videos.append(video_id)
    
    # Check if there are more pages of results
    if 'nextPageToken' in response_yt:
        next_page_token = response_yt['nextPageToken']
        # Make a new request for the next page of results
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId="LM",
            maxResults=50,  # You can adjust this number based on your needs
            pageToken=next_page_token
        )
        response_yt = request.execute()
    else:
        # No more pages, exit the loop
        break

# Print the extracted song names and artist information
for track, artist in yt_songs:
    print(f"Track: {track}, Artist: {artist}")

len(yt_songs)

len(problematic_videos)



df2 = pd.DataFrame({'Video ID': yt_ids, 'Video Title': yt_titles})





user_input = input("Do you want to continue (yes/no): ")

if user_input.lower() == 'yes':
    print("Continuing to the next part...")
    # ... code for fetching Spotify data goes here ...
else:
    print("Stopping the program.")
    sys.exit()

''' spotify '''
print("checking spotify user library..... ")

sp_client_id = 'ca7fbe12e14546cb94ec1ec90c536bce'
sp_client_secret = 'bf412cc6cd4a458da9706b4c4e83e258'
all_items=[]
sp_songs=[] #might not need
existing_liked_uris = []

username = 'x5raulz6ufun7mia2v0s6oqeq'
scope = "user-library-modify"
redirect_uri = "http://localhost:7777/callback"

auth_manager = SpotifyOAuth(client_id=sp_client_id,
                                client_secret=sp_client_secret,
                                redirect_uri=redirect_uri,
                                scope=scope)
    # Get an access token
access_token = auth_manager.get_access_token()
access_token = access_token['access_token']
print(access_token)
headers_main = {
    'Authorization': f'Bearer {access_token}'
}

''' existing uris'''
response_sp = requests.get('https://api.spotify.com/v1/me/tracks', headers=headers_main).json()
total = response_sp['total'] 
print("Total spotify 'liked songs' found:", total)

for offset in range(0, total, 20):
    url = "https://api.spotify.com/v1/me/tracks?offset="+str(offset) + "&limit=20" 
    response_sp1 = requests.get(url, headers=headers_main).json()
    getter = response_sp1['items']
    all_items.extend(getter)
    percentage = (len(all_items) / total) * 100
    print(f"Loading... {percentage}%")

print("Processing all", total ,"songs found in Spotify user library")

#for j in all_items:    songs_name = [j['track']['name']]   sp_songs.append(songs_name)

existing_liked_uris = [item["track"]["uri"] for item in all_items]

''''  ytd - sp uris    '''
spotify_uris = []
spotify_track_names = []
total_songs_not_found = 0
for track, artist in yt_songs:
    # Search for the track on Spotify
    search_url = f"https://api.spotify.com/v1/search?q=track:{track} artist:{artist}&type=track"
    search_response = requests.get(search_url, headers=headers_main)

    search_results = search_response.json()
    tracks = search_results.get("tracks", {}).get("items", [])
    
    if tracks:
        # Get the URI of the first search result
        uri = tracks[0]["uri"]
        track_name = tracks[0]["name"]
        spotify_uris.append(uri)
        spotify_track_names.append(track_name)
    else:
        # Handle the case when the song is not found
        total_songs_not_found += 1
        print(f"Song not found on Spotify: Track='{track}', Artist='{artist}'")

print(f"Total songs not found on Spotify: {total_songs_not_found}")


# Filter out duplicates from the newly obtained Spotify URIs
new_spotify_uris = [uri for uri in spotify_uris if uri not in existing_liked_uris]
new_spotify_track_names = [name for uri, name in zip(spotify_uris, spotify_track_names) if uri in new_spotify_uris]



# Spotify allows a maximum of 50 URIs per request, so batch them if needed

#how many
print(f"Total tracks to be added in Spotify: {len(new_spotify_uris)}")


#which ones
print("Track names:")
for name in new_spotify_track_names:
    print(name)
user_input = input("Do you want to continue (yes/no): ")

if user_input.lower() == 'yes':
    print("Continuing to the next part...")
    # ... code for fetching Spotify data goes here ...
else:
    print("Stopping the program.")
    sys.exit()




print("Loading the songs to spotify")
total_songs_added = 0

for i in range(0, len(new_spotify_uris), 50):# Spotify allows a maximum of 50 URIs per request, so batch them if needed
    batch_uris = new_spotify_uris[i:i + 50]
    data = json.dumps({'uris': batch_uris})
    sp = Spotify(auth=access_token)
    try:
        sp.current_user_saved_tracks_add(tracks=batch_uris)
        total_songs_added += len(batch_uris)
        print(f"{len(batch_uris)} songs added successfully.")
    except SpotifyException as e:
        print(f"Error: Songs can't be added. {e}")

print(f"Total songs added: {total_songs_added}")


