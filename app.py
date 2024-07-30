# this module will be used to run the frontend of the app
from flask import Flask, request, render_template, redirect, url_for,session
import recsys   # my module to do the recommendatoins

# setup app
app = Flask(__name__)


# directs user to the home page of the website
@app.route('/',methods=['GET','POST'])
def home():

    error = ''

    # user submitting a form
    if request.method == 'POST':

        # read in user entered data
        songInfo = request.form['song']
        entryType = request.form['entry']

        # song could not be found (invalid format)
        if entryType == 'songEn' and songInfo.find('-')==-1:
            error = 'Invalid format. Please enter in form "Song Name - Artist"'

        # no error 
        if error == '':
            session['songInfo'] = songInfo
            session['entryType'] = entryType
            return redirect('/results')


    return render_template('index.html',error=error)

@app.route('/discover',methods=['GET','POST'])
def discover():

    # get top 6 trending artists, and top 10 trending songs
    trendingArtists, trendingSongs = recsys.trendingSongs()

    for song in trendingSongs:
        # put artists names ino one list
        artists = ", ".join(song['artists']) 
        song['artists'] = artists

    # for links in html
    urls = []
    for artist in trendingArtists:
        urls.append('https://open.spotify.com/artist/'+(artist['uri'][15:]))
    
    return render_template('discover.html',artists=trendingArtists,songs=trendingSongs, urls=urls)

@app.route('/results',methods=['GET','POST'])
def results():
    # retrieve the variables about song information from user input
    choice = session.get('entryType',None)
    songInfo = session.get('songInfo',None)
    
    # now we can actually perform the recommendations
    recs = recsys.mainFunction(choice,songInfo)

    # convert dataframe to dict
    recs = recs[['name','artists','duration_ms']]
    recs = recs.to_dict('records')
   
    
    for rec in recs:

        # change duration ot mins:secs
        mins = int((int(rec['duration_ms'])/1000)//60)  
        secs = int((int(rec['duration_ms'])/1000)%60)       
        secs = str(secs).zfill(2)                       # format time
        rec['duration_ms'] = str(mins) + ':' + str(secs)

        # put artists names ino one list
        artists = rec['artists']
        artists = artists.replace('[','')
        artists = artists.replace(']','')
        artists = artists.replace("'","")
        rec['artists'] = artists

    # get cover of input song if not playilst
    cover = ''
    if choice != 'playlist':
        cover = recsys.getCover(songInfo)

    # get input song name and aritst
    name, artist = recsys.getInfo(choice,songInfo)

    return render_template('results.html',recs=recs, cover=cover,name=name,artist=artist)

if __name__ == '__main__':

    # start up website
    app.secret_key = '..'   # for sessions
    app.run(debug=True)
