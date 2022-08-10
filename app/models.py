""" DB """
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    BigInteger,
    func,
    Boolean,
)
from sqlalchemy.orm import declarative_base, relationship
from flask_login import UserMixin
from app import app, db, ma

Base = declarative_base()


class Games(db.Model):
    """Games model

    Args:
        db (Model): model
    """

    __tablename__ = "games"
    app_id = Column(Integer, primary_key=True)
    name = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    votes = relationship("Votes", backref="games", passive_deletes=True)

    @staticmethod
    def update_or_create(data):
        """update or create a game

        Args:
            data (Object): Object with type, appid and name
        """
        game = Games.query.get(data["appid"])

        if game is None:
            new_game = Games()
            new_game.app_id = data["appid"]
            new_game.name = data["name"]
            db.session.add(new_game)
            db.session.commit()
        else:
            game.name = data["name"]
            db.session.commit()


class User(db.Model, UserMixin):
    """User model

    Args:
        db (Model): model
    """

    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    steam_id = Column(String(100), unique=True)
    nickname = Column(String(1000))
    is_admin = Column(Boolean, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    votes = relationship("Votes", backref="user", passive_deletes=True)

    @staticmethod
    def get_or_create(steam_id):
        """Return the user or create a new one based on the steam_id

        Args:
            steam_id (Integer): Steam ID

        Returns:
            User: User model
        """
        user = User.query.filter_by(steam_id=steam_id).first()
        if user is None:
            user = User()
            user.steam_id = steam_id
            db.session.add(user)
        return user


class Votes(db.Model):
    """Votes model

    Args:
        db (Model): model
    """

    __tablename__ = "votes"
    __table_args__ = (
        db.UniqueConstraint("app_id", "user_id", name="unique_votes_app_id_user_id"),
    )
    id = Column(Integer, primary_key=True)
    app_id = Column(
        Integer, ForeignKey("games.app_id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        BigInteger, ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    vote = Column(Integer, nullable=False)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @staticmethod
    def update_or_create(data):
        """Update the user if already voted otherwise create a vote.
        If the vote is the same, delete it

        Args:
            data (Object): Object with type, app_id and user_id
        """
        vote = (
            Votes.query.filter_by(user_id=data["user_id"])
            .filter_by(app_id=data["app_id"])
            .first()
        )

        if vote is None:
            new_vote = Votes()
            new_vote.vote = data["type"]
            new_vote.app_id = data["app_id"]
            new_vote.user_id = data["user_id"]
            db.session.add(new_vote)
            db.session.commit()
        else:
            if vote.deleted:
                vote.vote = data["type"]
                vote.deleted = False
                db.session.commit()
            elif vote.vote == data["type"]:
                vote.deleted = True
                db.session.commit()
            else:
                vote.vote = data["type"]
                vote.deleted = False
                db.session.commit()


class GameSchema(ma.SQLAlchemyAutoSchema):
    """Schema to return output as JSON"""

    class Meta:
        """Games model"""

        model = Games


class UserSchema(ma.SQLAlchemyAutoSchema):
    """Schema to return output as JSOn"""

    class Meta:
        """User model"""

        model = User


class VotesSchema(ma.SQLAlchemyAutoSchema):
    """Schema to return output as JSOn"""

    class Meta:
        """Votes model"""

        model = Votes
