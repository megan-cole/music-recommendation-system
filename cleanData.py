# this file is going to be for extracting the data and performing data pre processing
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import os
from dotenv import load_dotenv

# setup
scope = "user-library-read"
load_dotenv()

client_id= os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,client_secret=client_secret,redirect_uri="http://localhost:3000",scope=scope))

# this will get the track info given a song name and artist
def getTrackInfo(name='', artist='',uri=None):

    if not uri:
        song = name + ' - ' + artist
        # search for the song and get URI
        results = sp.search(q=song,type='track',limit=1)
        uri = results['tracks']['items'][0]['uri']

    # get info about the track and audio features
    track_info = sp.track(uri)
    featuresAudio = sp.audio_features(uri)[0]

    features = {}

    # extract all the needed features in the order of the previously downloaded dataset
    features['id'] = track_info['id']
    features['name'] = track_info['name']  # track name
    features['popularity'] = track_info['popularity']  # track popularity
    features['duration_ms'] = featuresAudio['duration_ms']
    features['explicit'] = track_info['explicit']  # if a track is explicit or not
    features['artists'] = [track_info['artists'][i]['name'] for i in range(len(track_info['artists']))]
    features['id_artists'] = [track_info['artists'][i]['id'] for i in range(len(track_info['artists']))]
    features['release_date'] = track_info['album']['release_date'] # release date of song
    features['danceability'] = featuresAudio['danceability']
    features['energy'] = featuresAudio['energy']
    features['key'] = featuresAudio['key']
    features['loudness'] = featuresAudio['loudness']
    features['mode'] = featuresAudio['mode']
    features['speechiness'] = featuresAudio['speechiness']
    features['acousticness'] = featuresAudio['acousticness']
    features['instrumentalness'] = featuresAudio['instrumentalness']
    features['liveness'] = featuresAudio['liveness']
    features['valence'] = featuresAudio['valence']
    features['tempo'] = featuresAudio['tempo']
    features['time_signature'] = featuresAudio['time_signature']

    # convert to dataframe
    return pd.DataFrame.from_dict([features])

    # add to e nd of downloaded tracks data set (append mode)
    #df.to_csv('tracks.csv',index=False, header=False, mode='a')

# check for duplicates and any missing values
def dataCleaning():

    # read in data from all songs into dataframe
    df = pd.read_csv('tracks.csv')

    # if any duplicates are found, just drop them
    df.drop_duplicates(inplace=True)

    # check if there are any missing values and 
    print(df.isnull().sum())

    # because only 71 missing values were found for name, we just choose to drop them (large amnts of data otherwise and can't impute name)
    df.dropna(inplace=True)

    # now i need to find if any columns have mixed types
    for column in df.columns:
        print(column,':',pd.api.types.infer_dtype(df[column]))

    
    # convert the rows where explicit is still listed as true or false to 1 or 0
    for index, row in df.iterrows():
        
        # convert the values to 1 and 0 
        if row['explicit'] != 1 and row['explicit'] != 0:
            if row['explicit'] == 'False':
                df.loc[index,'explicit'] = 0
            else:
                df.loc[index,'explicit'] = 1
        
    # now i need to find if any columns have mixed types
    for column in df.columns:
        print(column,':',pd.api.types.infer_dtype(df[column]))

    # now convert this data frame to the final CSV file needed for the ML
    df.to_csv('musicData.csv')

def getTracksFromPlaylist(playlistID):

    playlist = sp.playlist(playlistID)
    tracks = playlist['tracks']['items']
    trackURIs = []
    
    # loop through all the tracks
    for track in tracks:
        trackURIs.append(track['track']['uri'])

    return trackURIs

def cleanCSV():

    df = pd.read_csv('musicData.csv')
    filter = df['artists'].str.contains('Workout')
    df = df[~filter]
    filter = df['name'].str.contains('Workout')
    df = df[~filter]
    filter = df['name'].str.contains('7 Years')
    df = df[~filter]
    df.to_csv('musicData.csv') 

if __name__ == '__main__':

    newSongs = pd.read_csv('data.csv')

    newSongs = newSongs.to_dict()
    df = pd.DataFrame()

    # loop through each song in my data
    for i in range(2499,2545):

        # get track info for each song
        df2 = getTrackInfo(newSongs['Name'][i],newSongs['Artist'][i])
        df = pd.concat([df,df2],ignore_index=True)  # concat to data frame of all songs


    # add to end of downloaded tracks data set (append mode)
    df.to_csv('tracks.csv',index=False, header=False, mode='a')

