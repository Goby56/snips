from flask import Flask, redirect, render_template, \
    request, url_for, make_response
from src import utils, server

import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", default="thoy")

server = server.Server(app.secret_key)

# The (W)eb (S)erver (G)ateway (I)nterface
@app.route("/")
def home():
    session = utils.get_session(request, app.secret_key)
    result = server.db.read.recent_posts(10)
    posts = utils.sql_result_to_dict(result, server.db.models["post"]["columns"])
    return render_template("home.html", **(session | {"posts": posts}))

@app.route("/share/", methods=["POST", "GET"])
def share():
    session = utils.get_session(request, app.secret_key)
    if not session["authorized"]:
        # Redirect to login and when logged in 
        # redirect again to share
        return redirect(url_for("login", redirect_to="share"))
    if request.method == "POST":
        resp = server.add_post(request.form["title"],
                               request.form["snippet"],
                               request.form["description"],
                               request.form["language"],
                               session["user_id"])
        if resp["post_created"]:
            return redirect(url_for("post", 
                                    post_id=resp["post_id"], 
                                    post_name=resp["post_name"]))
        return render_template("submit.html", **resp), resp["code"]
    return render_template("submit.html", **session)

@app.route("/comments/<int:post_id>")
@app.route("/comments/<int:post_id>/<post_name>")
def post(post_id, post_name=None):
    session = utils.get_session(request, app.secret_key)

    # Handle 404
    result = server.db.read.post(post_id)
    if not result:
        if post_name:
            title = post_name.replace("-", " ")
            error = f"The post '{title}' does not exist."
        else:
            error = f"The post you're looking for does not exist."
        return render_template("404.html", message=error), 404
    
    post = utils.sql_result_to_dict(result, server.db.models["post"]["columns"])[0]
    
    url_title = utils.str2url(post["title"])
    if post_name != url_title:
        return redirect(url_for("post", 
                                post_id=post["id"], 
                                post_name=url_title))

    result = server.db.read.post_comments(post_id, 10)
    comments = utils.sql_result_to_dict(result, server.db.models["comment"]["columns"])

    return render_template("post.html", post=post, comments=comments, **session)

@app.route("/comment/<int:post_id>/<int:comment_id>", methods=["POST"])
def comment(post_id, comment_id):
    session = utils.get_session(request, app.secret_key)
    if not session["authorized"]:
        return redirect(url_for("login", 
                                redirect_to="post", 
                                redirect_args={"post_id": post_id}))
    resp = server.add_comment(request.form["comment"], 
                                session["user_id"],
                                post_id, comment_id)
    return redirect(url_for("post", post_id=post_id))

# TODO MAYBE AUTO CHECK IF USER HAS ALREADY VOTED PURELY WITH SQL
# +REMEMBERS WHERE USER WAS (SCROLLS DOWN TO CORRECT POST/COMMENT)
@app.route("/upvote/<int:post_id>/<int:comment_id>")
@app.route("/downvote/<int:post_id>/<int:comment_id>")
def vote(post_id, comment_id):
    print(comment_id)
    session = utils.get_session(request, app.secret_key)
    if not session["authorized"]:
        return redirect(url_for("login"))
    increment = 1 if "upvote" in request.path else -1
    resp = server.add_vote(increment, session["user_id"],
                           post_id, comment_id)
    # TODO DO NOT REDIRECT TO POST IF ON HOME PAGE
    return redirect(url_for("post", post_id=post_id))
    
# TODO GENERALIZED FORM ROUTE (login & register is very similar)
@app.route("/login/", methods=["POST", "GET"])
def login():
    session = utils.get_session(request, app.secret_key)
    endpoint = request.args.get("redirect_to", "home")
    endpoint_args = request.args.get("redirect_args", {})
    if request.method == "POST":
        resp = server.authenticate(request.form["username"], 
                                   request.form["password"])
        if resp["authorized"]:
            response = make_response(redirect(url_for(endpoint, *endpoint_args)))
            response.set_cookie("token", resp["token"])
            return response

        return render_template("login.html", **resp), resp["code"]
    return render_template("login.html", **(session | {"redirect_to": endpoint}))

@app.route("/register/", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        resp = server.register(request.form["username"], 
                               request.form["password"],
                               request.form["passverify"])
        if resp["authorized"]:
            response = make_response(redirect(url_for("home")))
            response.set_cookie("token", resp["token"])
            return response
        return render_template("register.html", **resp), resp["code"]

    return render_template("register.html")

@app.route("/logout/", methods=["POST"])
def logout():
    response = make_response(redirect(url_for("home")))
    response.set_cookie("token", utils.generate_token(app.secret_key, invalid=True))
    return response

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html", message=error), 404

@app.context_processor
def template_context():
    return {
        "id2username": server.get_user,
        "has_voted": server.has_voted
    }