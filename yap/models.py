import datetime
import enum

from yap import db


class Paste(db.Model):
    class Visibility(enum.Enum):
        hidden = "Hidden"
        public = "Public"

    uuid = db.Column(db.Text, primary_key=True, nullable=False)
    filename = db.Column(db.Text, nullable=False)
    contents = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=datetime.timezone.utc), default=datetime.datetime.utcnow, nullable=False,
    )
    visibility = db.Column(db.Enum(Visibility), nullable=False)
    expire_at = db.Column(db.DateTime, nullable=False)
    author_ip = db.Column(db.Text, nullable=False)
