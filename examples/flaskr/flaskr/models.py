from datetime import datetime
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from flask import url_for
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from alchemical import Model


class User(Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]

    @property
    def password(self):
        raise RuntimeError('Cannot get user passwords!')

    @password.setter
    def password(self, value):
        """Store the password as a hash for security."""
        self.password_hash = generate_password_hash(value)

    def check_password(self, value):
        return check_password_hash(self.password_hash, value)


class Post(Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey(User.id))
    created: Mapped[datetime] = mapped_column(
        server_default=func.current_timestamp())
    title: Mapped[str]
    body: Mapped[str]

    # User object backed by author_id
    # lazy="joined" means the user is returned with the post in one query
    author = relationship(User, lazy="joined", backref="posts")

    @property
    def update_url(self):
        return url_for("blog.update", id=self.id)

    @property
    def delete_url(self):
        return url_for("blog.delete", id=self.id)
