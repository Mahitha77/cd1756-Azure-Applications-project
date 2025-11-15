"""
Routes and views for the flask application.
"""
from datetime import datetime
import uuid
import msal

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

from config import Config
from FlaskWebProject import db
from FlaskWebProject.forms import LoginForm, PostForm
from flask_login import current_user, login_user, logout_user, login_required
from FlaskWebProject.models import User, Post


@app.route('/')
@app.route('/home')
@login_required
def home():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template(
        'index.html',
        title='Home Page',
        posts=posts
    )


@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm(request.form)

    imageSourceUrl = (
        'https://'
        + current_app.config.get('BLOB_ACCOUNT', '')
        + '.blob.core.windows.net/'
        + current_app.config.get('BLOB_CONTAINER', '')
        + '/'
    )

    if form.validate_on_submit():
        post = Post()
        post.save_changes(form, request.files.get('image_path'), current_user.id, new=True)
        return redirect(url_for('home'))

    return render_template(
        'post.html',
        title='Create Post',
        imageSource=imageSourceUrl,
        form=form
    )


@app.route('/post/<int:id>', methods=['GET', 'POST'])
@login_required
def post(id):
    post_obj = Post.query.get_or_404(int(id))
    form = PostForm(formdata=request.form, obj=post_obj)

    imageSourceUrl = (
        'https://'
        + current_app.config.get('BLOB_ACCOUNT', '')
        + '.blob.core.windows.net/'
        + current_app.config.get('BLOB_CONTAINER', '')
        + '/'
    )

    if form.validate_on_submit():
        post_obj.save_changes(form, request.files.get('image_path'), current_user.id)
        return redirect(url_for('home'))

    return render_template(
        'post.html',
        title='Edit Post',
        imageSource=imageSourceUrl,
        form=form
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        # Invalid login -> log the attempt
        if user is None or not user.check_password(password):
            current_app.logger.info(f"Invalid login attempt for user: {username}")
            flash('Invalid username or password')
            return redirect(url_for('login'))

        # Successful login -> log success
        login_user(user, remember=form.remember_me.data)
        current_app.logger.info(f"{username} logged in successfully")

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)

    # prepare MSAL auth url for MS login
    session["state"] = str(uuid.uuid4())
    auth_url = _build_auth_url(scopes=Config.SCOPE, state=session["state"])
    return render_template('login.html', title='Sign In', form=form, auth_url=auth_url)


@app.route(Config.REDIRECT_PATH)  # Must match Redirect URI in Azure AD
def authorized():
    # Validate state (protection against CSRF)
    if request.args.get('state') != session.get("state"):
        current_app.logger.warning("State mismatch detected in MS login.")
        return redirect(url_for("home"))

    # Handle login errors (if any)
    if "error" in request.args:
        current_app.logger.error(f"MS Login error: {request.args.get('error_description')}")
        return render_template("auth_error.html", result=request.args)

    # Handle successful auth code returned
    if request.args.get('code'):
        cache = _load_cache()
        msal_app = _build_msal_app(cache=cache)

        try:
            result = msal_app.acquire_token_by_authorization_code(
                request.args['code'],
                scopes=Config.SCOPE,
                redirect_uri=url_for("authorized", _external=True, _scheme='https')
            )
        except Exception as e:
            current_app.logger.error(f"MSAL authorization code exchange failed: {e}")
            return render_template("auth_error.html", result={"error": str(e)})

        if not result:
            current_app.logger.error("MS Login failed: No token received.")
            return render_template("auth_error.html", result={"error": "No token received."})

        if "error" in result:
            current_app.logger.warning(f"MS Login error: {result.get('error_description', 'Unknown error')}")
            return render_template("auth_error.html", result=result)

        # Success: store user info
        session["user"] = result.get("id_token_claims", {})
        current_app.logger.info(f"MS Login success: {session['user'].get('name', 'Unknown User')}")

        # Log in as admin (per your app design)
        user = User.query.filter_by(username="admin").first()
        if user:
            login_user(user)
            current_app.logger.info("Admin logged in successfully via MS Login.")
        else:
            current_app.logger.error("Admin user not found in database.")
            return render_template("auth_error.html", result={"error": "Admin user not found"})

        _save_cache(cache)

    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    if hasattr(current_user, "username") and current_user.is_authenticated:
        current_app.logger.info(f"{current_user.username} logged out.")
    else:
        current_app.logger.info("Anonymous user logged out or session ended.")

    logout_user()

    if session.get("user"):  # Used MS Login
        current_app.logger.info("MS user session cleared and redirected to Microsoft logout.")
        session.clear()
        return redirect(
            Config.AUTHORITY + "/oauth2/v2.0/logout" +
            "?post_logout_redirect_uri=" + url_for("login", _external=True)
        )

    return redirect(url_for('login'))


# -------------------------
# MSAL helper functions
# -------------------------
def _load_cache():
    """Load token cache from session if it exists."""
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        try:
            cache.deserialize(session["token_cache"])
        except Exception:
            current_app.logger.warning("Failed to deserialize token cache.")
    return cache


def _save_cache(cache):
    """Persist token cache back to session if changed."""
    if getattr(cache, "has_state_changed", False):
        session["token_cache"] = cache.serialize()


def _build_msal_app(cache=None, authority=None):
    """Return a ConfidentialClientApplication instance from MSAL."""
    return msal.ConfidentialClientApplication(
        client_id=Config.CLIENT_ID,
        authority=authority or Config.AUTHORITY,
        client_credential=Config.CLIENT_SECRET,
        token_cache=cache
    )


def _build_auth_url(authority=None, scopes=None, state=None):
    msal_app = _build_msal_app(authority=authority)
    redirect_uri = url_for("authorized", _external=True, _scheme='https')
    current_app.logger.info(f"Redirecting to Microsoft with redirect_uri={redirect_uri}")
    return msal_app.get_authorization_request_url(
        scopes or [],
        state=state,
        redirect_uri=redirect_uri
    )
