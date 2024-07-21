from flask import Flask, request, render_template, redirect, url_for

# setup app
app = Flask(__name__)


# directs user to the home page of the website
@app.route('/',methods=['GET','POST'])
def home():

    return render_template('index.html')



if __name__ == '__main__':

    # start up website
    app.run(debug=True)
