import os
from datetime import datetime, timedelta
from functools import wraps

import requests
from dotenv import load_dotenv
from flask import Flask, abort, redirect, render_template, request, url_for
from flask.helpers import make_response
from flask_wtf.csrf import CSRFProtect

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FRONTEND_SECRET")

csrf = CSRFProtect(app)

BASE_API_URL = os.getenv("API_TRUSTED_ORIGINS", "").split(" ")[0]
app.config["SERVER_NAME"] = "localhost:5000"
EXPIRE_TIME = datetime.now() + timedelta(minutes=15)


def auth_required(f):
    """
    Decorator for endpoints which requires authentication.
    Works through external API.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        with app.app_context():
            token = request.cookies.get("token")
            response = requests.post(
                f"{BASE_API_URL}/auth/verify/", json={"token": token}
            )

            if response.status_code != 200:
                return render_template(
                    "login.html",
                    urls=URLS,
                )

        return f(*args, **kwargs)

    return wrapper


def get_current_user_data(request):
    """
    Checks whether the user is authorized. If they are it returns a
    username.
    """

    data = {"is_authorized": False}

    if request.cookies.get("token"):
        token = request.cookies.get("token")
        response = requests.get(
            f"{BASE_API_URL}/users/me/",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

        if response.status_code == 200:
            data["is_authorized"] = True

            response_data = response.json()
            data["username"] = response_data.get("username")
            data["liked_posts"] = response_data.get("liked_posts")

    return data


@app.route("/", methods=["GET"])
def homepage():
    posts = requests.get(
        f"{BASE_API_URL}/posts/",
    ).json()

    return render_template(
        "index.html",
        posts=posts,
        urls=URLS,
        data=get_current_user_data(request),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        creds = dict(request.form)
        api_response = requests.post(
            f"{BASE_API_URL}/auth/token/",
            json={"username": creds["username"], "password": creds["password"]},
        )

        if api_response.status_code == 200:
            token = api_response.json()["access"]

            redirect_page = request.form.get("redirected_from") or "/"
            response = make_response(redirect(redirect_page))
            response.set_cookie("token", token, expires=EXPIRE_TIME, httponly=True)

            return response
        else:
            return render_template("login.html", urls=URLS, message=True)

    return render_template(
        "login.html",
        urls=URLS,
    )


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        creds = dict(request.form)
        api_response = requests.post(
            f"{BASE_API_URL}/auth/register/",
            json={"username": creds["username"], "password": creds["password"]},
        )

        if api_response.status_code == 401:
            message = api_response.json().get("message")
            zipped_message = zip(message.keys(), message.values())
            parsed_message = [
                [field, [e for e in errors]] for field, errors in zipped_message
            ]

            return render_template(
                "signup.html",
                urls=URLS,
                message=parsed_message,
                previous_username=creds["username"],
            )

        token = api_response.json()["access"]
        expire_time = datetime.now() + timedelta(minutes=15)

        response = make_response(redirect("/"))
        response.set_cookie("token", token, expires=expire_time, httponly=True)

        return response
    else:
        return render_template(
            "signup.html",
            urls=URLS,
        )


@app.route("/signout", methods=["POST"])
@auth_required
def signout():
    redirect_page = request.form.get("redirected_from") or url_for(
        "homepage", urls=URLS
    )
    response = make_response(redirect(redirect_page))
    response.set_cookie("token", "", expires=0)
    return response


@app.route("/users/profile/<username>", methods=["GET"])
def profile(username):
    data = get_current_user_data(request)
    response = requests.get(f"{BASE_API_URL}/users/profile/{username}/")
    posts = []

    if response.status_code == 404:
        profile_data = {"username": username, "not_found": True}
    else:
        profile_data = response.json()
        posts = requests.get(f"{BASE_API_URL}/users/{username}/posts/").json()

    return render_template(
        "profile.html",
        urls=URLS,
        data=data,
        profile_data=profile_data,
        posts=posts,
    )


@app.route("/users/me", methods=["GET"])
@auth_required
def current_profile():
    data = get_current_user_data(request)
    return redirect(url_for("profile", username=data["username"]))


@app.route("/posts/create", methods=["POST"])
@auth_required
def create_post():
    if request.method == "POST":
        response = requests.post(
            f"{BASE_API_URL}/posts/",
            json={
                "content": request.form.get("content"),
            },
            headers={
                "Authorization": f"Bearer {request.cookies.get("token")}",
           }
        )

    return redirect(URLS["homepage"])


@app.route("/posts/delete", methods=["POST"])
def delete_post():
    redirect_page = request.form.get("redirected_from") or url_for(
        "homepage", urls=URLS
    )
    requests.delete(
        f"{BASE_API_URL}/posts/{request.form.get("post_id")}/",
        headers={
            "Authorization": f"Bearer {request.cookies.get("token")}",
        },
    )
    return redirect(redirect_page)


@app.route("/posts/like", methods=["POST"])
@auth_required
def like_post():
    redirect_page = request.form.get("redirected_from") or url_for(
        "homepage", urls=URLS
    )

    if request.form.get("is_liked") == "True":
        requests.delete(
            f"{BASE_API_URL}/posts/{request.form.get('post_id')}/like/",
            headers={
                "Authorization": f"Bearer {request.cookies.get("token")}",
            },
        )
    else:
        requests.post(
            f"{BASE_API_URL}/posts/{request.form.get('post_id')}/like/",
            headers={
                "Authorization": f"Bearer {request.cookies.get("token")}",
            },
        )

    return redirect(redirect_page)



with app.test_request_context():
    URLS = {
        **{
            endpoint: url_for(endpoint, _external=True)
            for endpoint in (
                "login",
                "homepage",
                "signup",
                "signout",
                "current_profile",
                "create_post",
                "delete_post",
                "like_post",
            )
        },
        "profile": url_for("profile", username="username", _external=True),
        "redirected_from": "/",
    }
