''' db/database.py — MongoDB connection setup.

HOW THE CONNECTION WORKS:
  1. load_dotenv() reads the .env file and injects MONGO_URI into the environment.
  2. MongoClient opens a connection pool to the Atlas cluster — once at startup.
  3. mongo_client["bank_db"] is the database handle — a pointer to our database.
     No network call happens here; it's just saying "when I make a query, use bank_db."
  4. get_mongo_db() returns that handle to anyone who needs it (the repositories).

WHY A CONNECTION POOL?
  MongoClient manages multiple connections internally. Each request gets a
  connection from the pool instead of opening a new TCP connection every time.
  This is why MongoClient is created once at module load — not once per request.
'''
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Read .env file and load its variables into os.environ.
# This must run before os.getenv() or the variable won't be found.
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI is not set. Copy .env.example to .env and fill in your Atlas connection string."
    )

# The connection to the MongoDB cluster — created once, reused for every request.
# serverSelectionTimeoutMS limits how long we wait to discover the cluster on startup.
# If the URI is wrong or the cluster is unreachable, you get a clear error immediately.
mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

# The database handle — equivalent to picking which database to talk to.
# All collections (users, accounts, transactions, counters) live under bank_db.
mongo_db = mongo_client["bank_db"]


def get_mongo_db():
    ''' Return the bank_db database handle.

    Repositories call this in their __init__ to get a reference to the database.
    Since mongo_db is a module-level object, this always returns the same instance —
    there is nothing to open or close per request. '''
    return mongo_db
