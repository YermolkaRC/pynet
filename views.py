from functools import wraps
from flask import session, Blueprint, render_template, request, jsonify, redirect, url_for
import requests

views = Blueprint(__name__, 'views')

def ensure_logged_in(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('views.home'))
        return fn(*args, **kwargs)
    return wrapper

@views.route('/')
def home():
    return render_template('index.html')

@views.route('/register')
def register():
    return render_template('register.html')

@views.route('/<username>/posts')
@ensure_logged_in
def userbyname(username):
    data = requests.get(f'http://localhost:5000/api/{username}/posts').json()
    posts = []
    for post in data:
        posts.append(f"{post['post_name']}: {post['post_text']}")

    return render_template('posts.html', username=username, data=posts)

@views.route('/post')
@ensure_logged_in
def newpost():
    return render_template('newpost.html')

@views.route('/users/<username>')
def userpage(username):
    try:
        r = requests.get(f'http://localhost:5000/api/getnamefromid/{int(username)}').json()
        sameuser = int(username) == session['user_id']
        return render_template('userpage.html', name=r['name'], sameuser=sameuser)
    except ValueError:
        return render_template('userpage.html', name=username)

@views.route('/users/<username>/subscriptions')
@ensure_logged_in
def getsubs(username):
    try:
        id = int(username)
        name = requests.get(f'http://localhost:5000/api/getnamefromid/{id}').json()['name']
    except ValueError:
        name = username
        id = requests.get(f'http://localhost:5000/api/getidfromname/{username}').json()['id']

    
    subs = requests.get(f'http://localhost:5000/api/{id}/friends').json()
    sub_names = []
    for sub in subs:
        sub_name = requests.get(f"http://localhost:5000/api/getnamefromid/{sub['to_user']}").json()['name']
        sub_names.append(sub_name)

    return render_template('subscriptions.html', subs=sub_names, username=name)