"""
Routes and views for the flask application.
"""

from flask import (
    render_template,
    flash,
    redirect,
    request,
    session,
    url_for,
    current_app
)
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required
import uuid
import msal

from FlaskWebProject import app, db
from FlaskWebProject.models import User, Post
from FlaskWebProject.forms import LoginForm, PostForm
from config import Config


# -----------------------------
# HOME PAGE
# -----------------------------
@app.route("/")
@app.route("/home")
@login_required
def home():
    posts = Post.query.all()
    return render_template("index.html", title="Home Page", posts=posts)


# -----------------------------
# NEW POST
# -----------------------------
@app.route("/new_post", methods=["GET", "POST"])
@login_required
def new_post():
    form = PostForm(request.form)
    imageSourceUrl = (
        f"https://{current_app.config['BLOB_ACCOUNT']}.blob.core.windows.net/"
        f"{current_app.config['BLOB_CONTAINER']}/"
    )

    if form.validate_on_submit():
        post = Post()
        post.save_changes(form, request.files.get("image_path"), current_user.id, new=True)
        return redirect(url_for("home"))

    return render_template(
        "post.html",
        title="Create Post",
        form=form,
        imageSource=imageSourceUrl
    )


# -----------------------------
# EDIT POST
# -----------------------------
@app.route("/post/<int:id>", methods=["GET", "POST"])
@login_required
def post(id):
    post_obj = Post.query.get_or_404(id)
    form = PostForm(formdata=request.form, obj=post_obj)
    imageSourceUrl = (
        f"https://{current_app.config['BLOB_ACCOUNT']}.blob.core.windows.net/"
        f"{current_app.config['BLOB_CONTAINER']}/"
    )

    if form.validate_on_submit():
        post_obj.save_changes(
            form,
            request.files.get("image_path"),
            current_user.id
        )
        return redirect(url_for("home"))

    return render_template(
        "post.html",
        title="Edit Post",
        form=form,
        imageSource=imageSourceUrl
    )


# -----------------------------
# LOGIN
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        # WRONG CREDENTIALS
        if user is None or not user.check_password(password):
            current_app.logger.info(f"Invalid login attempt for user: {username}")
            flash("Invalid username or password")
            return redirect(url_for("login"))

        # CORRECT LOGIN
        login_user(user, remember=form.remember_me.data)
        current_app.logger.info(f"{username} logged in successfully")
        next_page = request.args.get("next")

        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("home")

        return redirect(next_page)

    # Generate Microsoft OAuth Login URL
    session["state"] = str(uuid.uuid4())
    auth_url = _build_auth_url(
        scopes=Config.SCOPE,
        state=session["state"]
    )

    return render_template("login.html", title="Sign In", form=form, auth_url=auth_url)


# -----------------------------
# MICROSOFT AUTH CALLBACK
# -----------------------------
@app.route(Config.REDIRECT_PATH)
def authorized():
    if request.args.get("state") != session.get("state"):
        return redirect(url_for("home"))

    if "error" in request.args:
        return render_template("auth_error.html", result=request.args)

    if request.args.get("code"):
        cache = _load_cache()
        msal_app = _build_msal_app(cache)

        result = msal_app.acquire_token_by_authorization_code(
            request.args["code"],
            scopes=Config.SCOPE,
            redirect_uri=url_for("authorized", _external=True, _scheme="https")
        )

        if "error" in result:
            return render_template("auth_error.html", result=result)

        session["user"] = result.get("id_token_claims", {})

        admin = User.query.filter_by(username="admin").first()
        if admin:
            login_user(admin)
            current_app.logger.info("admin logged in successfully via MS login")

        _save_cache(cache)

    return redirect(url_for("home"))


# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():
    if current_user.is_authenticated:
        current_app.logger.info(f"{current_user.username} logged out")

    logout_user()

    if session.get("user"):
        session.clear()
        return redirect(
            Config.AUTHORITY + "/oauth2/v2.0/logout"
            + "?post_logout_redirect_uri="
            + url_for("login", _external=True)
        )

    return redirect(url_for("login"))


# -----------------------------
# MSAL HELPERS
# -----------------------------
def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache


def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()


def _build_msal_app(cache=None):
    return msal.ConfidentialClientApplication(
        Config.CLIENT_ID,
        authority=Config.AUTHORITY,
        client_credential=Config.CLIENT_SECRET,
        token_cache=cache
    )


def _build_auth_url(scopes=None, state=None):
    msal_app = _build_msal_app()
    redirect_uri = url_for("authorized", _external=True, _scheme="https")
    return msal_app.get_authorization_request_url(
        scopes or [],
        state=state,
        redirect_uri=redirect_uri
    )
