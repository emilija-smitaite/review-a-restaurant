import os
from flask import (
    Flask, flash, render_template, redirect,
    request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/all_reviews")
def all_reviews():
    reviews = list(mongo.db.reviews.find())
    return render_template("all_reviews.html", reviews=reviews)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        #check if username already exists
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already taken.")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "email": request.form.get("email").lower(),
            "password": generate_password_hash(request.form.get("password"))  
        }
        mongo.db.users.insert_one(register)

        # put the new user into "session" cookie
        session["user"] = request.form.get("username").lower()
        flash("Registered Successfully!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in the database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hatched password matches what the user has input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(
                            request.form.get("username")))
                    return redirect(url_for(
                        "my_reviews", username=session["user"]))

            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/my_reviews/<username>", methods=["GET", "POST"])
def my_reviews(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        reviews = list(mongo.db.reviews.find())
        return render_template("my_reviews.html", username=username,
            reviews=reviews)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.clear()
    return redirect(url_for("login"))


@app.route("/add_review", methods=["GET", "POST"])
def add_review():
    if request.method == "POST":
        review = {
            "restaurant_name": request.form.get("restaurant_name"),
            "score": request.form.get("score"),
            "review_text": request.form.get("review_text"),
            "posted_by": session["user"]
        }
        mongo.db.reviews.insert_one(review)
        flash("Review submitted!")
        return redirect(url_for("all_reviews"))
    restaurants = mongo.db.restaurants.find().sort("restaurant_name", 1)
    return render_template("add_review.html", restaurants=restaurants)


@app.route("/edit_review/<review_id>", methods=["GET", "POST"])
def edit_review(review_id):
    if request.method == "POST":
        submit = {
            "restaurant_name": request.form.get("restaurant_name"),
            "score": request.form.get("score"),
            "review_text": request.form.get("review_text"),
            "posted_by": session["user"]
        }
        mongo.db.reviews.replace_one({"_id": ObjectId(review_id)}, submit)
        flash("Review Successfully Updated!")
        return redirect(url_for("all_reviews"))

    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    restaurants = mongo.db.restaurants.find().sort("restaurant_name", 1)
    return render_template("edit_review.html", review=review,
        restaurants=restaurants)


@app.route("/delete_review/<review_id>")
def delete_review(review_id):
    mongo.db.reviews.delete_one({"_id": ObjectId(review_id)})
    flash("Review Successfully Deleted!")
    return redirect(url_for("all_reviews"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
