from flask import Flask, redirect, render_template, \
    request, url_for, make_response
from src import database, utils
import json

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

COMMENT_RESP = {
    "COMMENT_NOT_PROVIED": {
        "comment_created": False, "code": 400,
        "response_message": "You need to comment something!"
    },
    "COMMENT_CREATED": {
        "comment_created": True, "code": 201,
        "response_message": "Your comment was successfully created"
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
            self.db.cursor.execute(sql_cmd, args)
        if commit:
            self.db.db_connection.commit()
        return self.db.cursor.fetchall()

    def authenticate(self, username: str, password: str):
        # TODO FIX USERNAME ENTANGLEMENT (messy variable names)
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
        token = utils.generate_token(self.secret_key, username=displayname, 
                                     user_id=self.get_user(username=username))
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
        token = utils.generate_token(self.secret_key, username=username, 
                                     user_id=self.get_user(username=username))
        return AUTH_RESP["ACCOUNT_CREATED"] | {"token": token}
    
    def add_post(self, title: str, content: str, description: str, language: str, publisher_id: int):
        if not content:
            return POST_RESP["CODE_NOT_PROVIDED"]
        
        if not title:
            title = "Naming variables is not my thing"

        url_path = utils.str2url(title)
        self.db_exec(self.cmds["create"]["post"], 
                     title, content, description, language, 
                     publisher_id, commit=True)
        post_id = self.db_exec("SELECT LAST_INSERT_ID()")[0][0]
        return POST_RESP["POST_CREATED"] | {"post_id": post_id, "post_name": url_path}
    
    def add_comment(self, content: str, publisher_id: int, post_id: int, parent_id: int):
        if not content:
            return COMMENT_RESP["COMMENT_NOT_PROVIED"]
        
        self.db_exec(self.cmds["create"]["comment"], 
                     content, publisher_id, 
                     post_id, parent_id, commit=True)
        
        return COMMENT_RESP["COMMENT_CREATED"]
    
    def add_vote(self, new_value: int, voter_id: int, post_id: int, comment_id: int):
        if comment_id == 0:
            old_value = self.db_exec(self.cmds["fetch"]["vote_on_post"],
                                    voter_id, post_id)
            increment = new_value

            if old_value:
                old_value = old_value[0][0]
                self.db_exec(self.cmds["delete"]["post_vote"], 
                            voter_id, post_id, commit=True)
                if old_value != new_value:
                    increment += new_value
                elif old_value == new_value:
                    increment = -new_value

            # Create new vote record if first vote or switch
            if old_value != new_value:
                self.db_exec(self.cmds["create"]["post_vote"], new_value,
                            voter_id, post_id, commit=True)

            # Update vote value on post
            self.db_exec(self.cmds["update"]["post_votes_value"], 
                         increment, post_id, commit=True)
        else:
            old_value = self.db_exec(self.cmds["fetch"]["vote_on_comment"],
                                    voter_id, post_id, comment_id)
            increment = new_value

            if old_value:
                old_value = old_value[0][0]
                self.db_exec(self.cmds["delete"]["comment_vote"], 
                            voter_id, post_id, comment_id, commit=True)
                if old_value != new_value:
                    increment += new_value
                elif old_value == new_value:
                    increment = -new_value

            # Create new vote record if first vote or switch
            if old_value != new_value:
                self.db_exec(self.cmds["create"]["comment_vote"], new_value,
                            voter_id, post_id, comment_id,commit=True)

            # Update vote value on comment
            self.db_exec(self.cmds["update"]["comment_votes_value"], 
                         increment, post_id, comment_id, commit=True)
    
    def get_user(self, user_id: int = None, username: str = None):
        """
        ### Description

        Get either the user's id (column id in database) or their username
        using the respective values

        ### Use

        Generally used for template rendering:
        
        <p class="publisher-name">{{ id2username( post["publisher_id"] ) }}</p>\n
                                                            ^^^^^^^^^^^^^^^^
        In the example above 'id2username' is the relevant method as it has
        been renamed by the 'context_processor'.
        """
        if user_id:
            user = self.db_exec(self.cmds["fetch"]["user_name"], user_id)
            return user[0][0] if user else "User deleted"
        elif username:
            user = self.db_exec(self.cmds["fetch"]["user_id"], username)
            return user[0][0] if user else None
        
    def has_voted(self, user_id: int, test_value: int, post_id: int, comment_id: int = 0):
        """
        ### Description
        Used in templates to retrieve the css styling class 'voted'. This value
        will be provied if the user has pressed the appropriate voting button.

        ### Use
        Should only be used to style voting buttons if they have been clicked on.
        
        <i data-feather="arrow-up" class="{{ has_voted(user_id, 1, post['id']) }}"></i>\n
                                                                      ^^^^^^^^^^^^^^^^^
        """
        if not user_id:
            return ""
        if comment_id == 0:
            value = self.db_exec(self.cmds["fetch"]["vote_on_post"], 
                                 user_id, post_id)
        else:
            value = self.db_exec(self.cmds["fetch"]["vote_on_comment"], 
                                 user_id, post_id, comment_id)
        if not value:
            return ""
        return "voted" if test_value == value[0][0] else ""

app = Flask(__name__)
app.config["SECRET_KEY"] = "thoy"

server = Server(app.secret_key)

# The (W)eb (S)erver (G)ateway (I)nterface
@app.route("/")
def home():
    session = utils.get_session(request, app.secret_key)
    result = server.db_exec(server.cmds["fetch"]["recent_posts"], 10)
    posts = utils.sql_result_to_dict(result, server.db.models["post"]["columns"])
    return render_template("home.html", **(session | {"posts": posts}))

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
                               session["user_id"])
        if resp["post_created"]:
            return redirect(url_for("post", 
                                    post_id=resp["post_id"], 
                                    post_name=resp["post_name"]))
        return render_template("submit.html", **resp), resp["code"]
    return render_template("submit.html", **session)

@app.route("/comments/<int:post_id>", methods=["POST", "GET"])
@app.route("/comments/<int:post_id>/<post_name>", methods=["POST", "GET"])
def post(post_id, post_name=None):
    session = utils.get_session(request, app.secret_key)

    # Handle 404
    result = server.db_exec(server.cmds["fetch"]["post"], post_id)
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

    result = server.db_exec(server.cmds["fetch"]["post_comments"], post_id, 10)
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

# @app.route("/user/<username>")
# def user_profile(username):
#     return render_template("<p>You are on %s's profile</p>" % username)

@app.context_processor
def template_context():
    return {
        "id2username": server.get_user,
        "has_voted": server.has_voted
    }


if __name__ == "__main__":
    app.run(debug=True)