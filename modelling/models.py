import pandas as pd
from scipy import spatial
import pymongo
from bson.objectid import ObjectId
import webbrowser

client = pymongo.MongoClient()

db = client.get_database('music_project')

user_preferences = db.preferences

def read_dataset(user_id):
    df = pd.read_csv('SPOTIFY_DATASET_FINAL.csv')

    allow_explicit = user_preferences.find_one({"_id": ObjectId(user_id)})

    if (allow_explicit['allow_explicit'] == 'F'):
        df = df[df['explicit'] == 0]

    df = df[['danceability',
        'energy',
        'loudness',
        'mode',
        'speechiness',
        'acousticness',
        'instrumentalness',
        'liveness',
        'valence',
        'tempo',
        'name',
        'id']]

    return get_recommendations(df, user_id)

def get_recommendations(df, user_id):
    max_cosine_value = -1

    last_song_features = get_song_features(user_id)

    top_r = []

    for index, row in df.iterrows():
        dataset_features = [
            row['danceability'],
            row['energy'],
            row['loudness'],
            row['mode'],
            row['speechiness'],
            row['acousticness'],
            row['instrumentalness'],
            row['liveness'],
            row['valence'],
            row['tempo']
        ]

        result = 1 - spatial.distance.cosine(dataset_features, last_song_features[0])

        if (result > max_cosine_value and result != 1):
            max_cosine_value = result
            song_name = row['name']
            song_id = row['id']

            data = {
                'Song name': song_name,
                'Id': song_id,
                'Similarity': max_cosine_value,
            }

            top_r.append(data)

    df3 = pd.DataFrame(top_r)
    df3 = df3.sort_values(by=['Similarity'], ascending=False)
    results = df3.iloc[:9, :3]

    song_names = []
    song_ids = []

    for index, row in results.iterrows():
        song_names.append(row['Song name'])
        song_ids.append(row['Id'])

    return {
        'Song Names': song_names,
        'Song Ids': song_ids
    }

def get_song_features(user_id):
    last_song_id = db.features.find({"user_id": ObjectId(user_id)}).sort("_id", pymongo.DESCENDING)

    last_song_features = []

    for song in last_song_id:
        last_song_features.append([
            song['danceability'],
            song['energy'],
            song['loudness'],
            song['mode'],
            song['speechiness'],
            song['acousticness'],
            song['instrumentalness'],
            song['liveness'],
            song['valence'],
            song['tempo']
        ])

        return last_song_features

def analyze():
    webbrowser.open('http://localhost:8888/notebooks/Analysis.ipynb')
    return '<h2> Analysis Notebook Opened </h2>'

def visualize():
    webbrowser.open('https://public.tableau.com/app/profile/krishna6909/viz/MusicForYou/Dashboard1?publish=yes')
    return '<h2> Tableau Dashboards Opened </h2>'

# Other algorithms that we tried

def NMF():
    webbrowser.open('http://localhost:8888/notebooks/NMF.ipynb')
    return '<h2> NMF Notebook Opened </h2>'

