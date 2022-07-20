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
    """Reads reviews collection"""
    reviews = list(mongo.db.reviews.find())
    return render_template("all_reviews.html", reviews=reviews)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Inserts register dict to db as new doc in users collection"""
    if request.method == "POST":
        # check if username already exists
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
        return redirect(url_for("add_review", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Checks hatched password matches what the user has input"""
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
    """Returns reviews that have matching username key"""
    # grab the session user's username from db
    un = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        reviews = list(mongo.db.reviews.find())
        return render_template("my_reviews.html", username=un, reviews=reviews)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    """Removes user from session cookies"""
    flash("You have been logged out")
    session.clear()
    return redirect(url_for("login"))


@app.route("/add_review", methods=["GET", "POST"])
def add_review():
    """Inserts review dictionary in to reviews collection"""
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
    """Updates document in reviews collection """
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
    rest = mongo.db.restaurants.find().sort("restaurant_name", 1)
    return render_template("edit_review.html", review=review, restaurants=rest)


@app.route("/delete_review/<review_id>")
def delete_review(review_id):
    """Deletes document in reviews collection"""
    mongo.db.reviews.delete_one({"_id": ObjectId(review_id)})
    flash("Review Successfully Deleted!")
    return redirect(url_for("all_reviews"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
