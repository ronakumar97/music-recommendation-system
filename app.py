from flask import Flask, render_template, request, url_for, redirect, session
import pymongo
import requests
from datetime import datetime
import processing
import webbrowser

app = Flask(__name__)
app.secret_key = "AI-PROJECT"
client = pymongo.MongoClient()

db = client.get_database('music_project')

user_records = db.users
user_preferences = db.preferences
user_history = db.history

@app.route("/", methods=['GET', 'POST'])
def login():
    message = 'Please login to your account'
    if "email" in session:
        return redirect(url_for("logged_in"))

    if request.method == "POST":
        return processing.login(request)

    return render_template('login.html', message=message)

@app.route("/register", methods=['GET', 'POST'])
def index():
    if "email" in session:
        return redirect(url_for("logged_in"))

    if request.method == "POST":
        return processing.register(request)

    return render_template('index.html')

@app.route("/register/preferences", methods=['GET', 'POST'])
def save_preferences():
    if request.method == "POST":
        processing.save_preferences(request)

    return render_template('logged_in.html')

@app.route('/logged_in')
def logged_in():
    if "email" in session:
        email = session["email"]
        return render_template('logged_in.html', email=email)
    else:
        return redirect(url_for("login"))

@app.route("/logout", methods=["POST", "GET"])
def logout():
    if "email" in session:
        session.pop("email", None)
        return render_template("logout.html")
    else:
        return render_template('index.html')

@app.route("/search_music", methods=["GET", "POST"])
def search_music():
    if(request.method == "POST"):
        song_name = request.form.get('song_name')
        user_found = user_records.find_one({"email": session['email']})
        user_id = user_found['_id']
        last_song_played_information = {'user_id': user_id, 'last_song_played': song_name, 'timestamp': datetime.now()}
        user_history.insert_one(last_song_played_information)

        search_url = 'https://api.spotify.com/v1/search'

        params = {
            'q': song_name,
            'type': 'track',
            'limit': 9,
            'market': 'US'
        }

        headers = {"Authorization": "Bearer " + get_bearer_token()}

        r = requests.get(search_url, params=params, headers=headers)
        items = r.json()['tracks']['items']

        songs = processing.fetch_songs(items)

    return render_template('logged_in.html', songs = songs)

@app.route("/discover", methods=['GET', 'POST'])
def discover():
    return processing.get_songs()

@app.route("/store_features", methods=["GET", "POST"])
def store_features():
    if (request.method == "POST"):
        webbrowser.open(request.form.get('preview_url'))

        feature_url = 'https://api.spotify.com/v1/audio-features/'+ request.form.get('song_id')
        headers = {"Authorization": "Bearer " + get_bearer_token()}
        r = requests.get(feature_url, headers=headers)
        processing.save_features(r.json())

    return '<h1> Playing Song..... </h1>'

def get_bearer_token():
    token_url = 'https://accounts.spotify.com/api/token'
    params = {
        'grant_type': 'client_credentials'
    }

    headers = {"Authorization": "Basic MjlkOTFkYWU4NGFkNGVkOGI5M2E4MzRiMGNkZDA5YjQ6OTAwNGNmM2E0YzZkNDVmYmE5OGQ0MTM4ZDk5ZDE4NjE=",
               "Content-Type" : "application/x-www-form-urlencoded"}

    r = requests.post(token_url, params=params, headers=headers)
    token = r.json()['access_token']
    return token

if __name__ == "__main__":
    app.run(debug=True)