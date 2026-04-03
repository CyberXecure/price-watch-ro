import os

API_TITLE = os.getenv("API_TITLE", "Chilipir API")
PRICE_FAIRNESS_MARGIN = 0.05
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./price_tracker_freshful.db")
