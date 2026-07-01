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


@app.route("/", methods=["GET"])
def homepage():
    posts = requests.get(
        f"{BASE_API_URL}/posts/",
    ).json()

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
            data["username"] = response.json().get("username")

    return render_template(
        "index.html",
        posts=posts,
        urls=URLS,
        data=data,
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
            return render_template(
                "login.html",
                urls=URLS,
                message=True
            )

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
    print("enter signout")
    redirect_page = request.form.get("redirected_from") or url_for(
        "homepage", urls=URLS
    )
    response = make_response(redirect(redirect_page))
    response.set_cookie("token", "", expires=0)
    return response


with app.test_request_context():
    URLS = {
        **{
            endpoint: url_for(endpoint, _external=True)
            for endpoint in ("login", "homepage", "signup", "signout")
        },
        "redirected_from": "/",
    }
