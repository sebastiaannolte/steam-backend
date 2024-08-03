
# from app.updategames import update_games
# from app import app
# with app.app_context():
#     update_games()

import logging
import os
logging.info("Games updated")
print("Games updated")
from dotenv import load_dotenv
load_dotenv()

print(os.environ['APP_PORT'])

print("Games updated")
