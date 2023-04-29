from flask import Flask, redirect, render_template, request, url_for
from database import Database
import jwt, datetime

db = Database("snips")

app = Flask(__name__)
app.config["SECRET_KEY"] = "thoy"

def generate_token(**kwargs):
    kwargs["exp"] = datetime.datetime.utcnow() + datetime.timedelta(seconds=20)
    return jwt.encode(kwargs, app.config["SECRET_KEY"])

# The (W)eb (S)erver (G)ateway (I)nterface
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/share/", methods=["POST", "GET"])
def share_snippet():
    if request.method == "POST":
        print(request.form)
        # Redirect to /comments/postid
        return request.form
    return render_template("submit.html")

@app.route("/login/", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username and password:
            print(username, password)
            # Test password and username through database
            # Redirect to home page if successful 
            # return redirect(url_for("home"))

            return generate_token(username=username)
        
    return render_template("login.html")

@app.route("/register/", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        print(username, password)

    return render_template("register.html")

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html", message=error), 404

# @app.route("/user/<username>")
# def user_profile(username):
#     return render_template("<p>You are on %s's profile</p>" % username)

# @app.route("/post/<int:post_id>")
# def post(post_id):
#     return render_template("<p>This is post number %s</p>" % post_id)


if __name__ == "__main__":
    app.run(debug=True)