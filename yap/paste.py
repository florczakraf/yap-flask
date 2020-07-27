import http
from datetime import datetime
from uuid import uuid4

from flask import Blueprint, request, flash, redirect, url_for, render_template, current_app, Response, abort

from yap import db
from yap.models import Paste


UNTITLED_FILE = "Untitled"

bp = Blueprint("paste", __name__)


def is_expire_in_valid(expire_in):
    return expire_in in current_app.config["YAP_EXPIRE_IN"]


def get_latest_pastes(n):
    return (
        Paste.query.filter(Paste.expire_at > datetime.utcnow(), Paste.visibility == "public")
        .order_by(Paste.created_at.desc())
        .limit(n)
        .all()
    )


def get_ip_from_request():
    num_reverse_proxies = current_app.config["YAP_NUM_REVERSE_PROXIES"]

    if num_reverse_proxies:
        return request.headers["X-Forwarded-For"].split()[-num_reverse_proxies]

    return request.remote_addr


def check_paste_rate_limit():
    rate_limit = current_app.config["YAP_PASTE_RATE_LIMIT"]
    last_paste = Paste.query.filter_by(author_ip=get_ip_from_request()).order_by(Paste.created_at.desc()).first()

    if last_paste and last_paste.created_at + rate_limit > datetime.utcnow():
        retry_after = last_paste.created_at + rate_limit - datetime.utcnow()
        response = Response(status=http.HTTPStatus.TOO_MANY_REQUESTS, headers={"Retry-After": retry_after.seconds})
        abort(response)


@bp.route("/", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        check_paste_rate_limit()

        filename = request.form["filename"] or UNTITLED_FILE
        contents = request.form["contents"]
        visibility = request.form["visibility"]
        expire_in = request.form["expire_in"]
        expire_at = None
        error = False

        if not all((filename, contents, visibility, expire_in)):
            flash("Please fill all the required fields.")
            error = True

        if is_expire_in_valid(expire_in):
            expire_at = datetime.utcnow() + current_app.config["YAP_EXPIRE_IN"][expire_in]
        else:
            flash("Expiration date is not in a valid range.")
            error = True

        try:
            visibility = Paste.Visibility[visibility]
        except KeyError:
            flash("Invalid visibility level.")
            error = True

        if not error:
            uuid = uuid4().hex
            paste = Paste(
                uuid=uuid,
                filename=filename,
                contents=contents,
                visibility=visibility,
                expire_at=expire_at,
                author_ip=get_ip_from_request(),
            )
            db.session.add(paste)
            db.session.commit()

            return redirect(url_for("paste.show", uuid=uuid))

    return render_template(
        "paste/create.html",
        visibility_options=[x.name for x in Paste.Visibility],
        expiration_options=current_app.config["YAP_EXPIRE_IN"],
        filename_placeholder=UNTITLED_FILE,
        latest_pastes=get_latest_pastes(5),
    )


def get_paste_or_404(uuid):
    paste = Paste.query.filter_by(uuid=uuid).first_or_404()

    if paste.expire_at < datetime.utcnow():
        abort(404)

    return paste


@bp.route("/paste/<uuid>", methods=("GET",))
def show(uuid):
    return render_template("paste/show.html", paste=get_paste_or_404(uuid))


@bp.route("/paste/<uuid>/raw", methods=("GET",))
def raw_show(uuid):
    paste = get_paste_or_404(uuid)

    return Response(paste.contents, mimetype="application/octet-stream")
