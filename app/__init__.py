import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
)
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from sqlalchemy import (
    create_engine,
)

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

DATABASE_URI = "postgresql+psycopg2://{dbuser}:{dbpass}@{dbhost}/{dbname}".format(
    dbuser=os.environ["DB_USER"],
    dbpass=os.environ["DB_PASS"],
    dbhost=os.environ["DB_HOST"],
    dbname=os.environ["DB_NAME"],
)
app.config.update(
    SQLALCHEMY_DATABASE_URI=DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)
engine = create_engine(DATABASE_URI)

CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)
# engine = ""
ma = Marshmallow(app)
db = SQLAlchemy(app)

from app import routes

# Import for migration
from app.models import User, Votes, Games

migrate = Migrate()
with app.app_context():
    db.create_all()
    db.session.commit()
