import contextlib
import datetime
import os
from pathlib import Path

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_alembic import Alembic

DEV_SECRET_KEY = "PLEASE MAKE ME LONG AND UNIQUE"
DEFAULT_YAP_EXPIRE_IN = {
    "31 days": datetime.timedelta(days=31),
    "7 days": datetime.timedelta(days=7),
    "1 day": datetime.timedelta(days=1),
    "6 hours": datetime.timedelta(hours=6),
    "1 hour": datetime.timedelta(hours=1),
    "30 minutes": datetime.timedelta(minutes=30),
}

db = SQLAlchemy()


def create_app(extra_app_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=DEV_SECRET_KEY,
        SQLALCHEMY_DATABASE_URI=f'sqlite:///{(Path(app.instance_path) / "yap.sqlite").absolute().as_posix()}',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        ALEMBIC_CONTEXT={"render_as_batch": True},
        YAP_EXPIRE_IN=DEFAULT_YAP_EXPIRE_IN,
        YAP_PASTE_RATE_LIMIT=datetime.timedelta(seconds=30),
        YAP_NUM_REVERSE_PROXIES=0,
    )
    app.config.from_pyfile("config.py", silent=True)
    if extra_app_config:
        app.config.from_mapping(extra_app_config)

    if app.config["SECRET_KEY"] == DEV_SECRET_KEY and not (app.debug or app.testing):
        raise RuntimeError("Please set SECRET_KEY")

    with contextlib.suppress(OSError):
        os.makedirs(app.instance_path)

    db.init_app(app)
    alembic = Alembic()
    alembic.init_app(app)

    from yap import paste

    app.register_blueprint(paste.bp)

    return app
