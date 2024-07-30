# this file is going to be for extracting the data and performing data pre processing
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import os
from dotenv import load_dotenv
from langdetect import detect
from lyricsgenius import Genius

# setup
scope = "user-library-read"
load_dotenv()

client_id= os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,client_secret=client_secret,redirect_uri="http://localhost:3000",scope=scope))
genius_id= os.getenv('GENIUS_ID')
genius = Genius(genius_id)

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

# add language based on title to dataset
def addLanguages():

    df = pd.read_csv('musicData.csv')
    results = []

    # i will use lyricsgenius to grab the lyrics for songs, then use langdetect to detect the language
    for idx, row in df.iterrows():

        try:
            results.append(detect(row['name']))
        except:
            # search for each song lyrics and detect the language if couldn't detect based on title
           # song = genius.search_song(row['artists'],row['name'])

           # if not song:
            results.append('n/a')
         #   else:
             #   results.append(detect(song.lyrics))


    df['lang'] = results
    

    df.to_csv('musicData2.csv')

def getTrending():

    # search for top 50 songs global
    results = sp.search(q='Top 50 - Global' ,type='playlist',limit=1)
    playlistID = results['playlists']['items'][0]['uri']

    # get the track uri's for all 50 tracks
    tracks = getTracksFromPlaylist(playlistID)

    top = pd.DataFrame()

    # get the cover, name, and artist, and id
    for track in tracks:

        df = getTrackInfo(uri=track)
        top = pd.concat([top,df],ignore_index=True)

    
    top = top.loc[:,['id','name','artists']]

    # get top 10 trending songs
    top10 = top[:10]
    top10 = top10.to_dict('records')
    
    # now get trending artists by searching for artists with most occurrences in tracks
    artists = {}
    for idx, row in top.iterrows():

        artists[row['artists'][0]] = 1 + artists.get(row['artists'][0],0)
    
    sortedArtists = dict(sorted(artists.items(),key = lambda x: x[1],reverse=True))
    
    # get top 6 artists
    artists = []
    for key, value in sortedArtists.items():
        artists.append(key)
        if len(artists)==6:
            break

    # get artist name, id, and cover img
    artistList = []
    for artist in artists:

        res = sp.search(q=artist,type='artist',limit=1)

        features = {}
        features['uri'] = res['artists']['items'][0]['uri']
        features['name'] = res['artists']['items'][0]['name']
        features['cover'] = res['artists']['items'][0]['images'][0]['url']
        artistList.append(features)
    
        
    return (artistList, top10)

# get cover of a song
def getCover(song):

    results = sp.search(q=song,type='track',limit=1)
    return results['tracks']['items'][0]['album']['images'][0]['url']


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

