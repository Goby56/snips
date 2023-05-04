from ctypes import util
from email import message
from urllib import response
from flask import Flask, redirect, render_template, \
    request, url_for, make_response
from src import database, utils
import json, urllib.parse

# Authorization respone
AUTH_RESP = {
    "INSUFFICENT_DETAILS": {
        "authorized": False, "code": 400, 
        "response_message": "Username or password missing"
    },
    "PASSWORDS_DOES_NOT_MATCH": {
        "authorized": False, "code": 400,
        "response_message": "Passwords needs to match"
    },
    "INCORRECT_DETAILS": {
        "authorized": False, "code": 401, 
        "response_message": "Username or password is incorrect"
    },
    "USERNAME_TAKEN": {
        "authorized": False, "code": 409, 
        "response_message": "Username unavailable"
    },
    "ACCOUNT_CREATED": {
        "authorized": True, "code": 201, 
        "response_message": "Account created"
    },
    "LOGIN_SUCCESSFUL": {
        "authorized": True, "code": 200, 
        "response_message": "Login successful"
    },
    "TOKEN_ACCEPTED": {
        "authorized": True, "code": 200,
        "response_message": "Session restored"
    }
}

POST_RESP = {
    "CODE_NOT_PROVIDED": {
        "post_created": False, "code": 400,
        "response_message": "You need to post something!"
    },
    "POST_CREATED": {
        "post_created": True, "code": 201,
        "response_message": "Your post was successfully created"
    }
}

class Server:
    def __init__(self, secret_key) -> None:
        self.db = database.Database("snips")
        self.secret_key = secret_key
        with open("./db/commands.json", "r") as f:
            self.cmds = json.load(f)

    def db_exec(self, sql_cmd: str, *args, commit = False):
        if len(args) < 1:
            self.db.cursor.execute(sql_cmd)
        else:
            # self.db.cursor.execute(sql_cmd, args) causes unbalanced quotations when logging in
            # self.db.cursor.execute(sql_cmd % args) causes unbalanced quotations when posting
            # wtf
            self.db.cursor.execute(sql_cmd, args)
        if commit:
            self.db.db_connection.commit()
        return self.db.cursor.fetchall()

    def authenticate(self, username: str, password: str):
        if not username or not password:
            return AUTH_RESP["INSUFFICENT_DETAILS"]
        
        result = self.db_exec(self.cmds["fetch"]["user_auth"], username.lower())
        if not result:
            return AUTH_RESP["INCORRECT_DETAILS"]
        
        username, displayname, hashed_password = result[0]
        if not utils.verify_password(password, hashed_password):
            return AUTH_RESP["INCORRECT_DETAILS"]
        
        self.db_exec(self.cmds["update"]["user_last_login"], 
                     username.lower(), commit=True)
        token = utils.generate_token(displayname, self.secret_key)
        return AUTH_RESP["LOGIN_SUCCESSFUL"] | {"token": token}
        
    def register(self, username: str, password: str, passverify: str):
        if not username or not password:
            return AUTH_RESP["INSUFFICENT_DETAILS"]
        
        if password != passverify:
            return AUTH_RESP["PASSWORDS_DOES_NOT_MATCH"]

        user = self.db_exec(self.cmds["fetch"]["user_auth"], username.lower())
        if user:
            return AUTH_RESP["USERNAME_TAKEN"]
        
        hashed_pass = utils.hash_password(password) # salt encoded
        self.db_exec(self.cmds["create"]["user"], 
                              username.lower(), username, hashed_pass, 
                              commit=True)
        token = utils.generate_token(username, self.secret_key)
        return AUTH_RESP["ACCOUNT_CREATED"] | {"token": token}
    
    def add_post(self, title: str, content: str, description: str, language: str, publisher_name: str):
        if not content:
            return POST_RESP["CODE_NOT_PROVIDED"]
        publisher_id = self.db_exec(self.cmds["fetch"]["user_id"], 
                                    publisher_name.lower())[0][0]
        if not title:
            title = "Naming variables is not my thing"

        url_path = utils.str2url(title)
        self.db_exec(self.cmds["create"]["post"], 
                     title, content, description, language, 
                     publisher_id, commit=True)
        post_id = self.db_exec("SELECT LAST_INSERT_ID()")[0][0]
        return POST_RESP["POST_CREATED"] | {"post_id": post_id, "post_name": url_path}

app = Flask(__name__)
app.config["SECRET_KEY"] = "thoy"

server = Server(app.secret_key)

# The (W)eb (S)erver (G)ateway (I)nterface
@app.route("/")
def home():
    session = utils.get_session(request, app.secret_key)
    return render_template("home.html", **session)

@app.route("/share/", methods=["POST", "GET"])
def share():
    session = utils.get_session(request, app.secret_key)
    if not session["authorized"]:
        # Redirect to share when logged in
        return redirect(url_for("login", redirect_to="share"))
    if request.method == "POST":
        resp = server.add_post(request.form["title"],
                               request.form["snippet"],
                               request.form["description"],
                               request.form["language"],
                               session["user"])
        if resp["post_created"]:
            return redirect(url_for("post_comments", 
                                    post_id=resp["post_id"], 
                                    post_name=resp["post_name"]))
        return render_template("submit.html", **resp), resp["code"]
    return render_template("submit.html", **session)

@app.route("/comments/<int:post_id>", methods=["POST", "GET"])
@app.route("/comments/<int:post_id>/<post_name>", methods=["POST", "GET"])
def post_comments(post_id, post_name=None):
    result = server.db_exec(server.cmds["fetch"]["post"], post_id)
    if not result:
        if post_name:
            title = post_name.replace("-", " ")
            error = f"The post '{title}' does not exist."
        else:
            error = f"The post you're looking for does not exist."
        return render_template("404.html", message=error), 404
    
    post_id, title, code, desc, prog_lang, publisher_id, votes, pub_date = result[0]
    
    url_title = utils.str2url(title)
    if post_name != url_title:
        return redirect(url_for("post_comments", 
                                post_id=post_id, 
                                post_name=url_title))
    publisher = server.db_exec(server.cmds["fetch"]["user_name"], publisher_id)
    if not publisher:
        publisher = "User deleted"
    return render_template("post.html", title=title, 
                           snippet=code, description=desc, 
                           prog_lang=prog_lang, publisher=publisher[0][0], 
                           votes=votes, pub_date=pub_date)
    

# TODO GENERALIZED FORM ROUTE (login & register is very similar)
@app.route("/login/", methods=["POST", "GET"])
def login():
    session = utils.get_session(request, app.secret_key)
    endpoint = request.args.get("redirect_to", "home")
    if request.method == "POST":
        resp = server.authenticate(request.form["username"], 
                                   request.form["password"])
        if resp["authorized"]:
            response = make_response(redirect(url_for(endpoint)))
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

@app.route("/logout/")
def logout():
    response = make_response(redirect(url_for("home")))
    response.set_cookie("token", utils.generate_token("", app.secret_key, True))
    return response

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html", message=error), 404

# @app.route("/user/<username>")
# def user_profile(username):
#     return render_template("<p>You are on %s's profile</p>" % username)


if __name__ == "__main__":
    app.run(debug=True)