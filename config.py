
import os
from dotenv import load_dotenv

load_dotenv()

# JWT settings
JWTALGO = os.getenv("JWTALGO")
JWTSECRETKEY = os.getenv("JWTSECRETKEY")

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL")
