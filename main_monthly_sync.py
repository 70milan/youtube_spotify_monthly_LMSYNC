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
from configparser import ConfigParser
import json
from spotipy import Spotify
from spotipy.exceptions import SpotifyException
import sys
import boto3
import pandas as pd
from io import StringIO

###### S3##############
#######################
#######################
#######################
#######################
#######################

# Read configuration from file
config = ConfigParser()
config.read('awscreds.ini')


aws_access_key_id =  config.get('aws_creds', 'aws_access_key_id')
aws_secret_access_key = config.get('aws_creds', 'aws_secret_access_key')

s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

bucket_name = 's3numerone'
file_path1 = 'processed_yt_ids.txt'
file_path2 = 'existing_sp_uris.txt'
# Check if the file exists in the bucket
try:
    s3.head_object(Bucket=bucket_name, Key=file_path1)
except:
    # File does not exist, create a blank file
    s3.put_object(Body='', Bucket=bucket_name, Key=file_path1)





print("Fetching YT MUSIC")



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


########## get bucket current ############


obj = s3.get_object(Bucket=bucket_name, Key=file_path1)
processed_yt_ids = obj['Body'].read().decode().splitlines()


new_yt_ids = []
for item in response_yt['items']:
    video_id = item['snippet']['resourceId']['videoId']
    if video_id in processed_yt_ids:
        continue  # Skip this song if it has already been processed
    new_yt_ids.append(video_id)

# Use youtube-dl to extract metadata for the new YouTube video IDs
ydl_opts = {
    'quiet': True,  # Disable console output for youtube-dl
}

for video_id in new_yt_ids:
    video_url = f'https://www.youtube.com/watch?v={video_id}'
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            track = info.get('title', 'Unknown Track')
            rawartist = info.get('uploader', 'Unknown Artist')
            artist = rawartist.replace(" - Topic", "")
            yt_songs.append((track, artist))
            # After successfully processing a song, append its YouTube video ID to the list of processed IDs
            processed_yt_ids.append(video_id)
    except (youtube_dl.utils.ExtractorError, youtube_dl.utils.DownloadError) as e:
        print(f"An error occurred while extracting information from the video {video_url}. Skipping...")
        problematic_videos.append(video_id)

#######################
#######################
#######################
#######################
#######################



# Print the extracted song names and artist information
for track, artist in yt_songs:
    print(f"Track: {track}, Artist: {artist}")

len(yt_songs)

#######################
#######################
#######################
#######################
#######################





''' spotify '''



#######################
#######################
#######################
#######################
#######################





print("checking spotify user library..... ")


sp_client_id = config.get('spotify', 'client_id')
sp_client_secret = config.get('spotify', 'client_secret')
all_items=[]
sp_songs=[] #might not need
existing_liked_uris = []

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



obj = s3.get_object(Bucket=bucket_name, Key=file_path2)
file_content = obj['Body'].read().decode('utf-8')

# Split the file content into a list of URIs
existing_liked_uris = file_content.split('\n')

'''
#for j in all_items:    songs_name = [j['track']['name']]   sp_songs.append(songs_name)

existing_liked_uris = [item["track"]["uri"] for item in all_items]


existing_liked_uris.extend(existing_liked_uris)
#len(existing_liked_uris)


existing_liked_uris_str = '\n'.join(existing_liked_uris)
s3_client.put_object(Body=existing_liked_uris_str, Bucket=bucket_name, Key=file_path)
'''




''''  ytd - sp uris   

LOOKING UP THE OUT OF SYNC YOUTUBE SONG ON SPOTIFY

'''

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

#######################
#######################
#######################
#######################
##############################################
#######################
#######################
#######################
##############################################
#######################
#######################
#######################
##############################################
#######################
#######################
#######################
##############################################
#######################
#######################
#######################
##############################################
#######################
#######################
#######################
##############################################
#######################
#######################
#######################
#######################

print("Loading the songs to spotify")
total_songs_added = 0

for i in range(0, len(new_spotify_uris), 50):
    batch_uris = new_spotify_uris[i:i + 50]
    data = json.dumps({'uris': batch_uris})
    sp = Spotify(auth=access_token)
    try:
        sp.current_user_saved_tracks_add(tracks=batch_uris)
        total_songs_added += len(batch_uris)
        print(f"{len(batch_uris)} songs added successfully.")
        spotify_songs_added = True
    except SpotifyException as e:
        print(f"Error: Songs can't be added. {e}")

print(f"Total songs added: {total_songs_added}")

if spotify_songs_added:
    s3.put_object(Body='\n'.join(processed_yt_ids), Bucket=bucket_name, Key=file_path1)
    s3.put_object(Body='\n'.join(existing_liked_uris), Bucket=bucket_name, Key=file_path1)



























'''



videotitles=[]
videoids=[]

while response_yt:
    # Extract videoIds from the current page and add them to videoids 
    for item in response_yt['items']:
        video_id = item['snippet']['resourceId']['videoId']
        video_title = item['snippet']['title']
        videotitles.append(video_title)
        videoids .append(video_id)
    
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


'''