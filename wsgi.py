from flask import Flask, redirect, render_template, \
    request, url_for, make_response
from src import database, utils
import json

# Authorization respone
AUTH_RESP = {
    "INSUFFICENT_DETAILS": {
        "authorized": False, "code": 400, 
        "message": "Username or password missing"
    },
    "INCORRECT_DETAILS": {
        "authorized": False, "code": 401, 
        "message": "Username or password is incorrect"
    },
    "USERNAME_TAKEN": {
        "authorized": False, "code": 409, 
        "message": "Username unavailable"
    },
    "ACCOUNT_CREATED": {
        "authorized": True, "code": 201, 
        "message": "Account created"
    },
    "LOGIN_SUCCESSFUL": {
        "authorized": True, "code": 200, 
        "message": "Login successful"
    },
    "TOKEN_ACCEPTED": {
        "authorized": True, "code": 200,
        "message": "Session restored"
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
            self.db.cursor.execute(sql_cmd % args)
        if commit:
            self.db.db_connection.commit()
        return list(self.db.cursor)

    def authenticate(self, username: str, password: str):
        if not username or not password:
            return AUTH_RESP["INSUFFICENT_DETAILS"]
        
        result = self.db_exec(self.cmds["fetch"]["user_auth"], username.lower())
        if not result:
            return AUTH_RESP["INCORRECT_DETAILS"]
        
        username, displayname, hashed_password = result[0]
        if not utils.verify_password(password, hashed_password):
            return AUTH_RESP["INCORRECT_DETAILS"]
        
        # TODO ALTER TABLE (last_login)
        token = utils.generate_token(displayname, self.secret_key)
        return AUTH_RESP["LOGIN_SUCCESSFUL"] | {"token": token}
        
    def register(self, username: str, password: str):
        if not username or not password:
            return AUTH_RESP["INSUFFICENT_DETAILS"]

        user = self.db_exec(self.cmds["fetch"]["user_auth"], username.lower())
        if user:
            return AUTH_RESP["USERNAME_TAKEN"]
        
        hashed_pass = utils.hash_password(password) # salt encoded
        self.db_exec(self.cmds["create"]["user"], 
                              username.lower(), username, hashed_pass, 
                              commit=True)
        token = utils.generate_token(username, self.secret_key)
        return AUTH_RESP["ACCOUNT_CREATED"] | {"token": token}

app = Flask(__name__)
app.config["SECRET_KEY"] = "thoy"

server = Server(app.secret_key)

# The (W)eb (S)erver (G)ateway (I)nterface
@app.route("/")
def home():
    session = utils.get_session(request, app.secret_key)
    return render_template("home.html", **session)

@app.route("/share/", methods=["POST", "GET"])
def share_snippet():
    session = utils.get_session(request, app.secret_key)
    if request.method == "POST":
        # Redirect to /comments/postid
        return request.form
    return render_template("submit.html", **session)

# TODO GENERALIZED FORM ROUTE (login & register is very similar)
@app.route("/login/", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        resp = server.authenticate(request.form["username"], 
                                   request.form["password"])
        if resp["authorized"]:
            response = make_response(redirect(url_for("home")))
            response.set_cookie("token", resp["token"])
            return response

        return render_template("login.html", **resp), resp["code"]

    return render_template("login.html")

@app.route("/register/", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        resp = server.register(request.form["username"], 
                               request.form["password"])
        if resp["authorized"]:
            response = make_response(redirect(url_for("home")))
            response.set_cookie("token", resp["token"])
            return response
        return render_template("register.html", **resp), resp["code"]

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