from datetime import datetime
from uuid import uuid4

from flask import Blueprint, request, flash, redirect, url_for, render_template, current_app

from yap import db
from yap.models import Paste


UNTITLED_FILE = "Untitled"

bp = Blueprint("paste", __name__)


def is_expire_in_valid(expire_in):
    return expire_in in current_app.config["YAP_EXPIRE_IN"]


@bp.route("/", methods=("GET", "POST"))
def create():
    if request.method == "POST":
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
                author_ip=request.remote_addr,  # TODO.md what about proxies?
            )
            db.session.add(paste)
            db.session.commit()

            return redirect(url_for("paste.show", uuid=uuid))

    return render_template(
        "paste/create.html",
        visibility_options=[x.name for x in Paste.Visibility],
        expiration_options=current_app.config["YAP_EXPIRE_IN"],
        filename_placeholder=UNTITLED_FILE,
    )


@bp.route("/paste/<uuid>", methods=("GET",))
def show(uuid):
    paste = Paste.query.filter_by(uuid=uuid).first_or_404()

    return render_template("paste/show.html", paste=paste)
