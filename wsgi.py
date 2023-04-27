from flask import Flask, render_template
from database import Database

db = Database()

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/share/")
def share_snippet():
    return render_template("submit.html")

# @app.route("/user/<username>")
# def user_profile(username):
#     return render_template("<p>You are on %s's profile</p>" % username)

# @app.route("/post/<int:post_id>")
# def post(post_id):
#     return render_template("<p>This is post number %s</p>" % post_id)


if __name__ == "__main__":
    app.run(debug=True)