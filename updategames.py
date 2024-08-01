
from app.updategames import update_games
from app import app
with app.app_context():
    update_games()