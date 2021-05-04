import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
import json
# import urllib.request
import bs4 as bs
import spacy

#TMDB
from tmdbv3api import TMDb
from tmdbv3api import Movie

tmdb = TMDb()
tmdb.api_key = 'd05215f55a79e472a5b0d00d1ec80d70'

def create_similarity():
    # creating a count matrix
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(data['comb'])
    # creating a similarity score matrix
    similarity = cosine_similarity(count_matrix)
    return data,similarity

def rcmd(m):
    m = m.lower()
    try:
        data.head()
        similarity.shape
    except:
        data, similarity = create_similarity()
    if m not in data['movie_title'].unique():
        return('Sorry! The movie you requested is not in our database. Please check the spelling or try with some other movies')
    else:
        i = data.loc[data['movie_title']==m].index[0]
        lst = list(enumerate(similarity[i]))
        lst = sorted(lst, key = lambda x:x[1] ,reverse=True)
        lst = lst[1:11] # excluding first item since it is the requested movie itself
        l = []
        for i in range(len(lst)):
            a = lst[i][0]
            l.append(data['movie_title'][a])
        return l

def get_response(movie):
	return {
	'Movie name': movie,
	'Director': list(data[data['movie_title'] == movie]['director_name'])[0], 
	'Genere': list(data[data['movie_title'] == movie]['genres'])[0], 
	'Actors': [list(data[data['movie_title'] == movie]['actor_1_name'])[0], list(data[data['movie_title'] == movie]['actor_2_name'])[0], list(data[data['movie_title'] == movie]['actor_3_name'])[0]]
	}

def review_sentiment_analysis(input_data : str):
    load_model = spacy.load("model_artifacts")
    parsed_text = load_model(input_data)
    if parsed_text.cats["pos"] > parsed_text.cats["neg"]:
        prediction = "Positive"
        score = parsed_text.cats["pos"]
    else:
        prediction = "Negative"
        score = parsed_text.cats["neg"]
    return {'review': input_data , 'predicted sentiment' :prediction ,'predicted score': score}

def review_analysis(imdb_id: str):
    sauce = requests.get('https://www.imdb.com/title/{}/reviews?ref_=tt_ov_rt'.format(imdb_id)).content
    soup = bs.BeautifulSoup(sauce,'lxml')
    soup_result = soup.find_all("div",{"class":"text show-more__control"})
    review_list=list()
    for reviews in soup_result:
        if reviews.string:
            review_list.append(review_sentiment_analysis(str(reviews.string)))
    return review_list

data = pd.read_csv('processed_data.csv')
app = Flask(__name__)

@app.route("/", methods=['GET'])
@app.route("/home", methods=['GET'])
def home():
	return render_template('index.html')

@app.route("/recommend", methods=['GET'])
def recommend():
    input_movie = request.args.get('name')

    tmdb_movie = Movie()
    result = tmdb_movie.search(input_movie.upper())

    movie_id = result[0].id
    movie_name = result[0].title

    response = requests.get('https://api.themoviedb.org/3/movie/{}?api_key={}'.format(movie_id,tmdb.api_key))
    data_json = response.json()
    imdb_id = data_json['imdb_id']
    poster = data_json['poster_path']

    response = {
    'Sentiment': review_analysis(imdb_id),
    'Poster': 'https://image.tmdb.org/t/p/original{}'.format(poster),
    'Requested Movie': get_response(input_movie), 
    'Recommendations': []
    }

    rec_movie = rcmd(input_movie)
    for movie in rec_movie:
        response['Recommendations'].append(get_response(movie)) 

    return jsonify(response)


if __name__ == "__main__":
	app.run(debug=True)
