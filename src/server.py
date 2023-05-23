import json

from src import database, utils

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
    """
    ### Description
    The `Server` class handles common interactions with the wsgi (Web Server Gateway Interface)
    such as authentication, publishing and voting. These interactions are pre-defined in the
    `commands.json` file and are exposed with the `cmds` variable

    ### Use
    Provide the secret key that is associated with the flask app. 
    This key will be used to create JWT (Json Web Tokens) which
    is then given to a authenticated user to authenticate them
    in the future.

    """
    def __init__(self, secret_key) -> None:
        self.db = database.Database("snips")
        self.secret_key = secret_key

    def db_exec(self, sql_cmd: str, *args, commit = False):
        """
        ### Description

        Makes the execution of SQL commands to the database easier.

        `:param sql_cmd:` The SQL command as a string

        `:param *args:` Values that should be inserted into the command

        `:param commit:` Wheter or not to commit the changes made to the database

        ### Use

        ##### Examples:

        Fetch user authentication details:
        ```
        result = self.db_exec(self.cmds["read"]["user_auth"], username.lower())
        ```

        Update last login of user:
        ```
        self.db_exec(self.cmds["update"]["user_last_login"], 
                     username.lower(), commit=True)
        ```
        Here commit has to be true in order to make sure the changes are saved
        """
        if len(args) < 1:
            self.db.cursor.execute(sql_cmd)
        else:
            self.db.cursor.execute(sql_cmd, args)
        if commit:
            self.db.connection.commit()
        return self.db.cursor.fetchall()

    def authenticate(self, username: str, password: str):
        """
        ### Description

        Logs in the user if:
        1. A username and password has been provided
        2. The user exists
        3. The password provided match the hash found in the database

        Updates the last login timestamp in the database.

        Returns a JWT (Json Web Token) for authentication as specified in these 
        functions :func:`utils.generate_token`, :func:`utils.validate_token`
        """
        if not username or not password:
            return AUTH_RESP["INSUFFICENT_DETAILS"]
        
        result = self.db.read.user_auth(username.lower())
        if not result:
            return AUTH_RESP["INCORRECT_DETAILS"]
        
        username, displayname, hashed_password = result[0]
        if not utils.verify_password(password, hashed_password):
            return AUTH_RESP["INCORRECT_DETAILS"]
        
        self.db.update.user_last_login(username.lower(), commit=True)
        token = utils.generate_token(self.secret_key, username=displayname, 
                                     user_id=self.get_user(username=username))
        return AUTH_RESP["LOGIN_SUCCESSFUL"] | {"token": token}
        
    def register(self, username: str, password: str, passverify: str):
        """
        ### Description

        Creates a user in the database if:
        1. A username and password has been provided
        2. The passwords provided match
        3. The username has not been taken
        
        Only a hashed version of the password gets stored in the database.
        The hashing algorithm is bcrypt and is done in :func:`utils.hash_password`

        Returns a JWT (Json Web Token) for authentication as specified in these 
        functions :func:`utils.generate_token`, :func:`utils.validate_token`
        """

        if not username or not password:
            return AUTH_RESP["INSUFFICENT_DETAILS"]
        
        if password != passverify:
            return AUTH_RESP["PASSWORDS_DOES_NOT_MATCH"]

        user = self.db.read.user_auth(username.lower())
        if user:
            return AUTH_RESP["USERNAME_TAKEN"]
        
        hashed_pass = utils.hash_password(password) # salt encoded
        self.db.create.user(username.lower(), username, hashed_pass, commit=True)
        token = utils.generate_token(self.secret_key, username=username, 
                                     user_id=self.get_user(username=username))
        return AUTH_RESP["ACCOUNT_CREATED"] | {"token": token}
    
    def add_post(self, title: str, content: str, description: str, language: str, publisher_id: int):
        """
        ### Description

        Adds a post to the database where atleast the content of the
        post has to be provided.

        `:param title:` Can be left empty, will resort to default title

        `:param content:` Must be provided, should be some kind of code snippet

        `:param description:` Not really in use nor fully supported as of yet

        `:param language:` Can be any of the supported HLJS languages, auto for auto detection

        `:param publisher_id:` user_id of the publisher
        """
        if not content:
            return POST_RESP["CODE_NOT_PROVIDED"]
        
        if not title:
            title = "Naming variables is not my thing"

        url_path = utils.str2url(title)
        self.db.create.post(title, content, description, 
                            language, publisher_id, commit=True)
        post_id = self.db_exec("SELECT LAST_INSERT_ID()")[0][0]
        return POST_RESP["POST_CREATED"] | {"post_id": post_id, "post_name": url_path}
    
    def add_comment(self, content: str, publisher_id: int, post_id: int, parent_id: int):
        """
        ### Description

        Used for adding comments on both posts and comments (nested comments). Nested comments
        is possible and has been implemented in the database but for the moment there is no
        way to comment on a comment on the website.

        `:param content:` The body of text that should be added

        `:param publisher_id:` user_id of the commenter

        `:param post_id:` The id of the post that the comment should be placed on

        `:param parent_id:` Location of where this comment should be placed. 
        A value of 0 (None) refers to a top level comment on the post, every other 
        positive integer refers to a specific comment on that post.

        ### Use

        As of now, only top level comments are supported.
        ```
        add_comment('Nice code!', user_id, 4, 0)
        ```
        This adds a top level comment on post with id 4. 0 should actually be Null.
        """
        if not content:
            return COMMENT_RESP["COMMENT_NOT_PROVIED"]
        
        self.db.create.comment(content, publisher_id, post_id, None, commit=True)
        # Set parent_id to None as it has a foreign key restraint where it
        # has to reference a comment id. 
        
        return COMMENT_RESP["COMMENT_CREATED"]
    
    def add_vote(self, new_value: int, voter_id: int, post_id: int, comment_id: int):
        """
        ### Description

        This method provides a way to up- and downvote both posts and comments.

        `:param new_value:` +1 for upvotes, -1 for downvotes

        `:param voter_id:` user_id of the one who is voting

        `:param post_id:` id of the post that the vote concerns 
        (even this has to be provided to vote on a comment as 
        every comment is associated with a post)

        `:param comment_id:` 0 to vote on post itself and any positive integer refers to the comment

        ### Use

        To upvote on post with post_id=3:
        ```
        add_vote(1, user_id, 3, 0)
        ```

        To downvote comment with comment_id=2 on post with post_id=6:
        ```
        add_vote(-1, user_id, 6, 2)
        ```
        """
        if comment_id == 0:
            old_value = self.db.read.vote_on_post(voter_id, post_id)
            increment = new_value

            if old_value:
                old_value = old_value[0][0]
                self.db.delete.post_vote(voter_id, post_id, commit=True)
                if old_value != new_value:
                    increment += new_value
                elif old_value == new_value:
                    increment = -new_value

            # Create new vote record if first vote or switch
            if old_value != new_value:
                self.db.create.post_vote(new_value, voter_id, 
                                         post_id, commit=True)

            # Update vote value on post
            self.db.update.post_votes_value(increment, post_id, commit=True)
        else:
            old_value = self.db.read.vote_on_comment(voter_id, post_id, comment_id)
            increment = new_value

            if old_value:
                old_value = old_value[0][0]
                self.db.delete.comment_vote(voter_id, post_id, 
                                            comment_id, commit=True)
                if old_value != new_value:
                    increment += new_value
                elif old_value == new_value:
                    increment = -new_value

            # Create new vote record if first vote or switch
            if old_value != new_value:
                self.db.create.comment_vote(new_value, voter_id, post_id, 
                                            comment_id, commit=True)

            # Update vote value on comment
            self.db.update.comment_votes_value(increment, post_id, 
                                               comment_id, commit=True)
    
    def get_user(self, user_id: int = None, username: str = None):
        """
        ### Description

        Get either the user's id (column id in database) or their username
        using the respective values

        ### Use

        Generally used for template rendering:
        ```html
        <p class="publisher-name">{{ id2username( post["publisher_id"] ) }}</p>\n
                                                  ^^^^^^^^^^^^^^^^^^^^
        ```
        In the example above the method has been renamed to `id2username` 
        by the :func:`context_processor`.
        """
        if user_id:
            user = self.db.read.user_name(user_id)
            return user[0][0] if user else "User deleted"
        elif username:
            user = self.db.read.user_id(username)
            return user[0][0] if user else None
        
    def has_voted(self, user_id: int, test_value: int, post_id: int, comment_id: int = 0):
        """
        ### Description
        Used in templates to retrieve the css styling class 'voted'. This value
        will be provied if the user has pressed the appropriate voting button.

        ### Use
        Should only be used to style voting buttons if they have been clicked on.
        ```html
        <i data-feather="arrow-up" class="{{ has_voted(user_id, 1, post['id']) }}"></i>
                                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        ```
        """
        if not user_id:
            return ""
        if comment_id == 0:
            value = self.db.read.vote_on_post(user_id, post_id)
        else:
            value = self.db.read.vote_on_comment(user_id, post_id, comment_id)
        if not value:
            return ""
        return "voted" if test_value == value[0][0] else ""