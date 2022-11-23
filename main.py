from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

API_KEY="12af70bb2fff7acd39f888db27beca8b"
MOVIE_URL="https://api.themoviedb.org/3/search/movie"
MOVIE_BY_ID="https://api.themoviedb.org/3/movie/"
MOVIE_DB_IMAGE_URL="https://image.tmdb.org/t/p/w500"
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

##CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
# Optional: But it will silence the deprecation warning in the console.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


##CREATE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer,nullable=False )
    description = db.Column(db.String(2000), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(2000), nullable=False)
    img_url = db.Column(db.String(200), nullable=False)

db.create_all()

@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    amount = len(all_movies)
    for movie in all_movies:
        movie.ranking = amount
        amount -=1
    return render_template("index.html", movies=all_movies)


class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)

@app.route("/delete", methods=["GET"])
def delete():
    if request.method != "POST":
        id = request.args.get('id', default=1, type=int)
        movie_id = id
        movie_to_delete = Movie.query.get(movie_id)
        db.session.delete(movie_to_delete)
        db.session.commit()
        return redirect(url_for('home'))


class AddMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add movie")

@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = AddMovieForm()
    if  request.method == "POST":
        movie_params ={
            "api_key":API_KEY,
            "query":form.title.data,
        }
        response = requests.get(MOVIE_URL, params=movie_params)
        response.raise_for_status()
        movie_data = response.json()
        # for movie in movie_data["results"]:
        #     print (movie)
        return render_template("add.html", movie_list=movie_data["results"], form=form)
    if request.args.get('go')=="1":
        new_movie_all = ()
        movie_params = {
            "api_key": API_KEY,
            # "id": request.args.get('movie'),
        }
        url=MOVIE_BY_ID + str(request.args.get('movie'),)
        response = requests.get(url, params=movie_params)
        response.raise_for_status()
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"],
            rating=data["vote_average"],
            review="none",
            ranking=5,
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("add.html", form=form)

if __name__ == '__main__':
    app.run(debug=True)
