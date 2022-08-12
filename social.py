#from crypt import methods
import json
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from hashlib import blake2b #Store password as f'blake2b${salt}${hashed_string}'
import secrets
import os
from views import views
from flask import session, Blueprint, render_template, request, jsonify, redirect, url_for
from functools import wraps

api = Blueprint(__name__, 'api')

# Init app
app = Flask(__name__)
app.register_blueprint(views, url_prefix='/')
basedir = os.path.abspath(os.path.dirname(__file__))

# DB config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_BINDS'] = {
    'users' : 'sqlite:///' + os.path.join(basedir, 'users.db'),
    'posts' : 'sqlite:///' + os.path.join(basedir, 'posts.db'),
    'friends': 'sqlite:///' + os.path.join(basedir, 'friends.db')
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'I love Programming'

# Init DB
db = SQLAlchemy(app)
# Init MA
ma = Marshmallow(app)

class Post(db.Model):
    __bind_key__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer)
    post_text = db.Column(db.String(255))
    post_name = db.Column(db.String(50))

    def __init__(self, author_id, post_name, post_text):
        self.author_id = author_id
        self.post_text = post_text
        self.post_name = post_name

class User(db.Model):
    __bind_key__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(60))
    user_info = db.Column(db.String(255))

    #subscriptions = db.Column(db.)
    # MAYBE MAKE A FRIEND CONNECTION INTO ITS OWN CLASS?
    # To get "Friends" search friends.db for all entries with key "user.id"
    # To get user posts search posts.db for all entries published by user.id

    def __init__(self, username, password, name, user_info):
        self.name = name
        self.password = password
        self.username = username
        self.user_info = user_info

class Subscription(db.Model):
    __bind_key__ = 'friends'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    to_user = db.Column(db.Integer)

    def __init__(self, user_id, to_user):
        self.user_id = user_id
        self.to_user = to_user



def check_password(username, password):
    #Store password as f'blake2b${salt}${hashed_string}'
    user = User.query.filter_by(username=username).first()
    _data = user.password.split('$')
    _fn = _data[0]
    _salt = _data[1]
    _hash = _data[2]

    if _fn == 'blake2b':
        password_to_check = hash_password(password, _salt).split('$')[2]
        return _hash == password_to_check
    else:
        return False

def hash_password(password, salt = None):
    bsalt = salt if salt is not None else secrets.token_hex(8)
    bpass = bytes(password, 'UTF-8')
    btb = blake2b(salt=bytes(bsalt, 'UTF-8'))
    btb.update(bpass)
    hashedpass = btb.hexdigest()
    return f'blake2b${bsalt}${hashedpass}'

@api.route('/')
def apihome():
    return {'msg': 'askdjfbajksdfaksldnf'}

# Create a user
@api.route('/register', methods=['GET', 'POST'])
def register():
    name = request.json['name']
    username = request.json['username']
    password = hash_password(request.json['password'])
    user_info = request.json['user_info']

    if User.query.filter_by(username=username) is None:
        new_user = User(username, password, name, user_info)

        db.session.add(new_user)
        db.session.commit()

        return user_schema.jsonify(new_user)
    else:
        return {'msg': f'User with {username=} already exists.'}

# Try to Log In
@api.route('/login', methods=['GET', 'POST'])
def login():
    username = request.json['username']
    password = request.json['password']

    # Need to implement cookies (authorization token)
    try: 
        if check_password(username, password):
            session['user_id'] = User.query.filter_by(username=username).first().id
            return {}, 200
        else:
            return {}, 400
    except AttributeError:
        return {}, 400

# Create a Post
@api.route('/post', methods=['POST'])
def new_post():
    author_id = request.json['user_id']
    post_name = request.json['post_name']
    post_text = request.json['post_text']

    _post = Post(author_id, post_name, post_text)

    db.session.add(_post)
    db.session.commit()

    return post_schema.jsonify(_post)

# Create a Post WITH logging in
@api.route('/postwithlogin', methods=['POST'])
def postwithlogin():
    post_name = request.json['post_name']
    post_text = request.json['post_text']
    author_id = session['user_id']

    _post = Post(author_id, post_name, post_text)

    db.session.add(_post)
    db.session.commit()

    return post_schema.jsonify(_post)

# Get a Post by ID
@api.route('/post/<id>', methods=['GET'])
def get_post(id):
    post = Post.query.get(id)
    return post_schema.jsonify(post)

# Get all Posts by user
@api.route('/<user_id>/posts', methods=['GET'])
def get_posts_by_user(user_id):
    try:
        int(user_id)
        posts = Post.query.filter_by(author_id=user_id)
        return posts_schema.jsonify(posts)
    except ValueError:
        return get_posts_by_username(user_id)
    

def get_posts_by_username(username):
    user_id = User.query.filter_by(username=username).first().id
    posts = Post.query.filter_by(author_id=user_id)
    return posts_schema.jsonify(posts)

# Get uesrname from userID
@api.route('/getnamefromid/<id>')
def getnamefromid(id):
    name = User.query.get(id).username
    return {'name': name}

@api.route('/getidfromname/<name>')
def getidfromname(name):
    id = User.query.filter_by(username=name).first().id
    return {'id': id}

# Add a Sub
@api.route('/<to_user>/subscribe', methods=['GET', 'POST'])
def sub_to_user(to_user):
    id = request.json['user_id']
    # First check if that's a new sub
    if Subscription.query.filter_by(user_id=id, to_user=to_user).first() is None:
        _sub = Subscription(id, to_user)

        db.session.add(_sub)
        db.session.commit()

        return sub_schema.jsonify(_sub)
    else:
        return {'msg': 'Already subscribed'}

# Get all Subs
@api.route('/<user_id>/friends', methods=['GET'])
def get_all_subs(user_id):
    _subs = Subscription.query.filter_by(user_id=user_id)

    return subs_schema.jsonify(_subs)

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'password', 'name', 'user_info')

class PostSchema(ma.Schema):
    class Meta:
        fields = ('id', 'author_id', 'post_name', 'post_text')

class SubscriptionSchema(ma.Schema):
    class Meta:
        fields = ('user_id', 'to_user')

# Init User Schema's
user_schema = UserSchema()
users_schema = UserSchema(many=True)
# Init Post Schema's
post_schema = PostSchema()
posts_schema = PostSchema(many=True)
#Init Sub Schema's
sub_schema = SubscriptionSchema()
subs_schema = SubscriptionSchema(many=True)

if __name__ == '__main__':
    app.register_blueprint(api, url_prefix='/api')
    app.run(debug=True)