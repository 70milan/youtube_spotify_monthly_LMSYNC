import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import pandas as pd
import subprocess
 
scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
api_service_name = "youtube"
api_version = "v3"

client_secrets_file = "csgo.json"

videoids  = []
videotitles = []  # To store video titles


flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)

credentials = flow.run_local_server(port=8080)


youtube = googleapiclient.discovery.build(api_service_name,
                                              api_version,
                                              credentials=credentials)

request = youtube.playlistItems().list(
    part="snippet",
    playlistId="LM",
    maxResults=50
)
response = request.execute()


while response:
    # Extract videoIds from the current page and add them to videoids 
    for item in response['items']:
        video_id = item['snippet']['resourceId']['videoId']
        video_title = item['snippet']['title']
        videotitles.append(video_title)
        videoids .append(video_id)
    
    # Check if there are more pages of results
    if 'nextPageToken' in response:
        next_page_token = response['nextPageToken']
        # Make a new request for the next page of results
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId="LM",
            maxResults=50,  # You can adjust this number based on your needs
            pageToken=next_page_token
        )
        response = request.execute()
    else:
        # No more pages, exit the loop
        break



print(response['pageInfo']['totalResults']) #total

df2 = pd.DataFrame({'Video ID': videoids, 'Video Title': videotitles})

df2.to_csv(r"C:/Users/milan/Downloads/randoms/ytd/justincase.csv", index = False )

print("dataframe created and deployed to local")





'''chunks'''
def chunk_list(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

chunk_size = 100
output_directory = r"C:/Users/milan/Downloads/randoms/ytd/chunks/"

# Ensure the output directory exists, create it if not
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Use the chunk_list function to break down videoids into smaller chunks
chunked_videoids = list(chunk_list(videoids, chunk_size))

# Iterate through chunks and write each chunk as a separate text file
for i, chunk in enumerate(chunked_videoids, 1):
    # Define a filename for each chunk (e.g., chunk_1.txt, chunk_2.txt, etc.)
    filename = os.path.join(output_directory, f"chunk_{i}.txt")
    
    # Build the content of the chunk as a single string
    chunk_content = "\n".join(chunk)
    
    # Write the entire chunk to the file
    with open(filename, "w") as file:
        file.write(chunk_content)

print("All chunks written to files.")
''' Youtube DL Downloading '''




print("downloading began")
# Define the youtube_dl_template
youtube_dl_template = "youtube-dl -f 140 --embed-thumbnail -x --audio-format mp3 --audio-quality 320k ytsearch:{}"

# Iterate through chunks and download videos sequentially
for i, chunk in enumerate(chunked_videoids, 1):
    print(f"Downloading videos for Chunk {i}...")
    for video_id in chunk:
        youtube_dl_command = youtube_dl_template.format(video_id)
        subprocess.run(youtube_dl_command, shell=True)
    
    print(f"Completed downloading videos for Chunk {i}.")



print("All chunks completed.")

''' getting specific playlist




url = "https://www.youtube.com/watch?v=mJ5k6udvyec"

video_url = url+str(dic["items"][i]["snippet"]
                            ['resourceId']['videoId'])

request = youtube.playlistItems().list(
    part="snippet",
    playlistId="PLbS4hbq5VWHlwjohbYcboqMsmwto02o27"
)
response = request.execute()

print(response)
getting everything not just music


request = youtube.channels().list(part="contentDetails", mine=True)
response = request.execute()
liked_playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["likes"]


request = youtube.playlistItems().list(
    part="snippet",
    playlistId=liked_playlist_id
)
response = request.execute()

print(response)

'''































'''

import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import pandas as pd
import subprocess


def fetch_youtube_playlist_data(client_secrets_file, playlist_id, max_results=50):
    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"

    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)

    credentials = flow.run_local_server(port=8080)

    youtube = googleapiclient.discovery.build(api_service_name,
                                              api_version,
                                              credentials=credentials)

    def fetch_page(page_token=None):
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=max_results,
            pageToken=page_token
        )
        return request.execute()

    page_token = None
    videoid = []
    videotitles = []

    while True:
        response = fetch_page(page_token)
        
        for item in response['items']:
            video_id = item['snippet']['resourceId']['videoId']
            video_title = item['snippet']['title']
            videotitles.append(video_title)
            videoid.append(video_id)

        if 'nextPageToken' in response:
            page_token = response['nextPageToken']
        else:
            break

        df2 = pd.DataFrame({'Video ID': videoid, 'Video Title': videotitles})


    return videoid, videotitles, df2




def downloadshit(videoid):

    youtube_dl_template = "youtube-dl -f 140 --embed-thumbnail -x --audio-format mp3 --audio-quality 320k ytsearch:{}"
    for video_id in zip(videoid):
        youtube_dl_command = youtube_dl_template.format(video_id)
        subprocess.run(youtube_dl_command, shell=True)

'''