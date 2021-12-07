from flask import render_template, url_for, redirect, session
import pymongo
import bcrypt
from modelling import models
from app import get_bearer_token
import requests

client = pymongo.MongoClient()

db = client.get_database('music_project')

user_records = db.users
user_preferences = db.preferences
user_history = db.history
user_features = db.features

def fetch_songs(items):
    songs = []

    for item in items:
        album_id = item['album']['id']
        album_name = item['album']['name']
        album_number_of_tracks = item['album']['total_tracks']
        album_image_url = item['album']['images'][0]['url']

        preview_url = item['preview_url']
        song_name = item['name']
        is_explicit = item['explicit']
        song_popularity = item['popularity']
        song_id = item['id']

        artist_id = item['artists'][0]['id']
        artist_name = item['artists'][0]['name']

        song_data = {
            'album_id': album_id,
            'album_name': album_name,
            'album_number_of_tracks': album_number_of_tracks,
            'album_image_url': album_image_url,
            'preview_url': preview_url,
            'song_name': song_name,
            'is_explicit': is_explicit,
            'song_popularity': song_popularity,
            'artist_id': artist_id,
            'artist_name': artist_name,
            'song_id': song_id
        }

        songs.append(song_data)

    return songs

def login(request):
    email = request.form.get("email")
    password = request.form.get("password")

    email_found = user_records.find_one({"email": email})

    if email_found:
        email_val = email_found['email']
        password_check = email_found['password']

        if bcrypt.checkpw(password.encode('utf-8'), password_check):
            session["email"] = email_val
            return redirect(url_for('logged_in'))
        else:
            if "email" in session:
                return redirect(url_for("logged_in"))
            message = 'Wrong password'
            return render_template('login.html', message=message)
    else:
        message = 'Email not found'
        return render_template('login.html', message=message)

def register(request):
    user = request.form.get("fullname")
    email = request.form.get("email")
    phone_number = request.form.get("phone_number")
    password1 = request.form.get("password1")
    password2 = request.form.get("password2")

    user_found = user_records.find_one({"name": user})
    email_found = user_records.find_one({"email": email})

    if user_found:
        message = 'There is already a user by that name'
        return render_template('index.html', message=message)
    if email_found:
        message = 'This email already exists in database'
        return render_template('index.html', message=message)
    if password1 != password2:
        message = 'Passwords should match!!'
        return render_template('index.html', message=message)
    else:
        hashed = bcrypt.hashpw(password2.encode('utf-8'), bcrypt.gensalt())
        user_input = {'name': user, 'email': email, 'phone_number': phone_number, 'password': hashed}
        user_records.insert_one(user_input)
        user_data = user_records.find_one({"email": email})
        new_email = user_data['email']
        session['email'] = new_email
        return render_template('preferences.html', email=new_email)

def save_preferences(request):
    country = request.form.get('country')
    genre = request.form.get('genre')
    age = request.form.get('age')
    location = request.form.get('location')
    artist = request.form.get('artist')

    user_found = user_records.find_one({"email": session['email']})
    user_id = user_found['_id']
    user_preferences_input = {'_id': user_id, 'country': country, 'genre': genre, 'age': age, 'location': location, 'artist': artist}
    user_preferences.insert_one(user_preferences_input)

def save_features(feaures):
    user_found = user_records.find_one({"email": session['email']})
    user_id = user_found['_id']

    user_features_input = {
        'user_id': user_id,
        'danceability': feaures['danceability'],
        'energy': feaures['energy'],
        'key': feaures['key'],
        'loudness': feaures['loudness'],
        'mode': feaures['mode'],
        'speechiness': feaures['speechiness'],
        'acousticness': feaures['acousticness'],
        'instrumentalness': feaures['instrumentalness'],
        'liveness': feaures['liveness'],
        'valence': feaures['valence'],
        'tempo': feaures['tempo'],
        'type': feaures['type'],
        'song_id': feaures['id'],
        'duration_ms': feaures['duration_ms'],
        'time_signature': feaures['time_signature']
    }
    user_features.insert_one(user_features_input)

def get_songs():
    user_found = user_records.find_one({"email": session['email']})
    user_id = user_found['_id']

    recommendations_data = models.read_dataset(user_id)
    song_names = recommendations_data['Song Names']
    song_ids = recommendations_data['Song Ids']

    recommendations = []

    for song_id in range(len(song_ids)):
        search_url = 'https://api.spotify.com/v1/tracks/' + song_ids[song_id]

        params = {
            'type': 'track',
            'market': 'US'
        }

        headers = {"Authorization": "Bearer " + get_bearer_token()}

        r = requests.get(search_url, params=params, headers=headers)
        items = r.json()

        preview_url = items['preview_url']
        image = items['album']['images'][0]['url']

        recommendation = {
            'song_name': song_names[song_id],
            'song_id': song_ids[song_id],
            'preview_url': preview_url,
            'image': image
        }

        recommendations.append(recommendation)

    return render_template('discover.html', songs = recommendations)


