# get functionality working from command line before making website
# this is where i am going to do the actual data science stuff, s
# raed in the input, read csv data into datafrmae
# do the rec. sys. parts (ML)
import cleanData     # my module that helps me get song data
import pandas as pd
from sklearn import preprocessing
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
import re
from lyricsgenius import Genius
from langdetect import detect
import random
import os
from dotenv import load_dotenv

# setup genius for lyrics
load_dotenv()
genius_id= os.getenv('GENIUS_ID')
genius = Genius(genius_id)

# extracts audio features from my dataset and from the input song
def processData(songFeatures):

    # read dataset and drop duplicate songs
    musicData = pd.read_csv('musicData.csv')
    musicData = musicData.drop_duplicates(subset=['name','artists'])

    # extract needed features from df's
    musicData = musicData.loc[:,['danceability','energy','key','loudness','mode','speechiness',\
                              'acousticness','instrumentalness','liveness','valence','tempo','time_signature']]
    songFeatures = songFeatures.loc[:,['danceability','energy','key','loudness','mode','speechiness',\
                              'acousticness','instrumentalness','liveness','valence','tempo','time_signature']]
    
    # scale features to 0-1 range
    scaler = preprocessing.MinMaxScaler()
    scaler.fit(musicData)                           # fit scaler based on musicData

    musicDataScaled = scaler.transform(musicData)
    musicData = pd.DataFrame(musicDataScaled,columns=musicData.columns)

    # need to scale this one song feature as well
    songFeaturesScaled = scaler.transform(songFeatures)
    songFeatures = pd.DataFrame(songFeaturesScaled,columns=songFeatures.columns)

    return (musicData,songFeatures)

# gets similarity between input song and songs in my dataset
def getSimilarity(musicData,songFeatures):

    # here i will use cosine similarity to calculate the similarity between input song and other songs in my data
    
    # loop through each row in dataframe to get its similarity with input songFeatures
    similarities = cosine_similarity(musicData.values,songFeatures.values.reshape(1,-1))
    return similarities

# gets top 10 recommendations based on hybrid recommendation system
def getRecommendations(similarities,name):

    musicData = pd.read_csv('musicData.csv')
    musicData = musicData.drop_duplicates(subset=['name','artists'])
    musicData['similarities'] = similarities

    # remove the song that is the same song from list
    musicData = musicData[musicData['name'] != name]

    # get top 75 recommendations based on similarity scores
    topSongs = musicData.nlargest(75,'similarities')
     
    # calculate weighted popularity of the top 75 songs
    weightedPopularity = []
    for idx, row in topSongs.iterrows():

        weightedPopularity.append(getWeightedPopularity(row['release_date']))

    topSongs['weightedPopularity'] = weightedPopularity

    # send the top 50 recommendations to filter by language (default english & spanish recs)
    topSongs = topSongs.nlargest(50,'weightedPopularity')
    topSongs = filterByLanguage(topSongs)
  
    # now pick the final 10 recs by sorting by weighted popularity
    top10 = topSongs.nlargest(10,'weightedPopularity')

    return top10

# calculate weighted popularity given a release date of a song
def getWeightedPopularity(releaseDate):
    
    # check if release date in proper form
    if re.match(r'^\d{4}-\d{2}-\d{2}',releaseDate):
        releaseDate = datetime.strptime(releaseDate,'%Y-%m-%d')
    elif re.match(r'^\d{4}-\d{2}',releaseDate):
        releaseDate = datetime.strptime(releaseDate,'%Y-%m')
    elif re.match(r'^\d{4}',releaseDate):
        releaseDate = datetime.strptime(releaseDate,'%Y')

    timeDifference = datetime.now() - releaseDate

    return (1 / (timeDifference.days+1))

# take the top 75 recommendations, and filter them by language (english and spanish only first)
def filterByLanguage(recommendations):

    '''
    results = []

    # i will use lyricsgenius to grab the lyrics for songs, then use langdetect to detect the language
    for idx, row in recommendations.iterrows():

        # search for each song lyrics and detect the language
        song = genius.search_song(row['artists'],row['name'])

        # if song not found, try to detect based on title
        if not song:
            results.append(detect(row['name']))
        else:
            results.append(detect(song.lyrics))

    recommendations['lang'] = results
    
    # filter based on english/spanish
    recommendations = recommendations.query('lang=="es" or lang=="en"')
    '''
    return recommendations.query('lang=="es" or lang=="en"')

def mainFunction(choice,songInput,main=False):
    cover = ''      # album cover

    if choice == 'songEn':

        if main:
            songInput = input('\nEnter song title - artist name (e.g. Vampire - Dominic Fike): ')
            # check input format
            while not songInput.find('-'):

                print('invalid entry. please try again')
                songInput = input('Enter song title - artist name (e.g. Vampire - Dominic Fike)')
        name, artist = songInput.split('-')

        # get all the matching features of this song similar to my data file
        songFeatures = cleanData.getTrackInfo(name.strip(),artist.strip())  

    elif choice == 'playlist':

        if main:
            playlistID = input('Enter Spotify Playlist Link: ')
        else:
            playlistID = songInput

        # get songs from playlist to base off of
        trackIDs = cleanData.getTracksFromPlaylist(playlistID)

        # extract just 50 of these songs frmo playist randomly
        if len(trackIDs) > 50:
            trackIDs = random.choices(trackIDs,k=50)
 
        # get features for each song in playlist
        songFeatures = pd.DataFrame()
        for track in trackIDs:
            songFeatures = pd.concat([songFeatures,cleanData.getTrackInfo(uri=track)])

        # get average stats of songs in their playlist
        songFeatures = songFeatures.loc[:,['explicit','danceability','energy','key','loudness','mode','speechiness',\
                              'acousticness','instrumentalness','liveness','valence','tempo','time_signature']]
        songFeatures = songFeatures.mean()
        songFeatures = pd.DataFrame([songFeatures])
        songFeatures.loc[0,'explicit'] = 1 if (songFeatures.loc[0,'explicit']>0.5) else 0
        name = ''
    elif choice == 'songLink':

        if main:
            songID = input('\nEnter Song Link: ')
        else:
            songID = songInput
        songFeatures = cleanData.getTrackInfo(uri=songID)
        name = songFeatures.loc[0,'name']
    
    songFeatures.loc[0,'explicit'] = 1 if (songFeatures.loc[0,'explicit']=='True') else 0

    # load data and extract features
    musicData, songFeatures = processData(songFeatures)
  
    # now i need to use ML model to get the cosine similarity
    similarities = getSimilarity(musicData,songFeatures)

    # get final song recommendations
    return getRecommendations(similarities,name.strip())

# get song name and artist formatted
def getInfo(entry, songInfo):
    name = ''
    artist = ''

    if entry=='songLink':
        songFeatures = cleanData.getTrackInfo(uri=songInfo)
        name = songFeatures.loc[0,'name']
        artist = songFeatures.loc[0,'artists']
    elif entry=='songEn':
        name, artist = songInfo.split('-')

    return (name, artist)

# gets top 10 trending songs rn
def trendingSongs():

    artistList, topSongs = cleanData.getTrending()
    return (artistList, topSongs)


def getCover(song):

    return cleanData.getCover(song)

if __name__ == '__main__':

    # read in song and artist name
    print('-----------------------------\n\tInput Options')
    print('1. Song Name - Artist\n2. Spotify Playlist Link\n3. Spotify Song Link\n')
    print('-----------------------------\n')
    choice = int(input('Enter 1, 2, or 3: '))

    if choice == 1:
        choice = 'songEn'
    elif choice == 2:
        choice = 'playlist'
    else:
        choice = 'songLink'

    mainFunction(choice,main=True)