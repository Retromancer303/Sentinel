# Database initialisation script — creates all tables defined in models.py.
# Run this once before starting the app for the first time:
#   python -m app.db.init_db

from app.db.database import engine
from app.db.models import Base

# Create any tables that don't already exist. This is safe to run multiple times.
Base.metadata.create_all(bind=engine)

print("Database tables created.")