I want to populate the AnalystFunctionsUser postgreSQL table with data from my s3 bucket. I only want to include these columns from the s3 csv: 

columns = USER_NAME,USER_EMAIL,LAST_ACTIVITY,ANALYST_FUNCTIONS,NON_ANALYST_FUNCTIONS,ANALYST_PCT,ANALYST_USER_FLAG,ANALYST_THRESHOLD,ANALYST_ACTIONS_PER_DAY,ANALYST_ACTIONS_PER_ACTIVE_DAYS,ACTIVE_DAYS




AnalystFunctionsUser is defined in my psql.py file


#psql.py
import sqlalchemy as db
from sqlalchemy import (
    create_engine,
    MetaData,
    Column,
    BigInteger,
    Text,
    DateTime,
    UniqueConstraint,
    ForeignKey,
    func,
    text,
    Index,
    String,
    Float,
    Integer
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from services.v0.credentials.tokens import AtlassianToken
import socket
from prettiprint import ConsoleUtils
import os

# Initialize print utility
cu = ConsoleUtils(theme="dark", verbosity=2)

cloudapp_env = os.environ.get("CLOUDAPP_ENV")

# creating connection to postegresql db
cu.header("Connecting to PostgreSQL")
cu.key_value("Hostname", socket.gethostname())
if cloudapp_env == "development":
    print("Dev environment'")
    db_name = "SpotfireDB"
    app = "psql-dev"
    user = "atlassian-bot.dev"
    schema = "license-dev"
elif "atlassian-api" in socket.gethostname().lower():  # case‑insensitive check
    print("Hostname contains 'atlassian-api'")
    db_name = "SpotfireDB"
    app = "psql"
    user = "atlassian-bot"
    schema = "license"
elif "vscode" in socket.gethostname().lower():
    print("Hostname contains 'vscode'")
    db_name = "SpotfireDB"
    app = "psql-dev"
    user = "atlassian-bot.dev"
    schema = "license-dev"
elif "desktop" in socket.gethostname().lower():
    print("Hostname contains 'desktop'")
    db_name = "SpotfireDBNova"
    app = "psql"
    user = "atlassian-bot"
    schema = "license"
else:
    db_name = "SpotfireDB"
    app = "psql-dev"
    user = "atlassian-bot.dev"
    schema = "license-dev"
    print("Unknown Hostname, using Dev")

password = AtlassianToken(app).getCreds()

vars_to_show = {
        "DB": db_name,
        "Schema": schema,
        "Password": cu.mask_secret(password, keep=3),
        "User": user,
    }
cu.dictionary(vars_to_show, expand=False)

engine = create_engine(
    f"postgresql+psycopg2://{user}:{password}@psqldb-k-kashmiryclust-kkashmiry0641.dbuser:5432/{db_name}"
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base(metadata=MetaData(schema=schema))

class AnalystFunctionsUser(Base):
    __tablename__ = "analyst_functions_users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    USER_NAME = Column(String)
    USER_EMAIL = Column(String)
    LAST_ACTIVITY = Column(DateTime)
    ANALYST_FUNCTIONS = Column(Integer)  # Assuming this is a JSON array
    NON_ANALYST_FUNCTIONS = Column(Integer)  # Assuming this is a JSON array
    ANALYST_PCT = Column(Float)
    ANALYST_USER_FLAG = Column(Integer)
    ANALYST_THRESHOLD = Column(Float)
    ANALYST_ACTIONS_PER_DAY = Column(Float)
    ANALYST_ACTIONS_PER_ACTIVE_DAYS = Column(Float)
    ACTIVE_DAYS = Column(Integer)
    
    
session = SessionLocal()

# following line will create Base classes as tables, if they already exist nothing changes
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



I want to run test.py and populate the postgreSQL table with the data from the csv... below is my current test.py file that shows how I get the csv data. I need code on how to populate the DB



#test.py
from io import BytesIO
import pandas as pd
from s2cloudapi import s3api as s3
from databases.psql import (
    Base,
    engine,
    AnalystFunctionsUser,
    session,
    cu
)
from sqlalchemy import text


def read_csv_from_bucket(bucket: str, key: str) -> pd.DataFrame:
    """
    Read a CSV object from S3 and return a pandas DataFrame.
    """
    boto_object = s3.get_object(bucket=bucket, key=key)
    csv_bytes = boto_object["Body"].read()
    df = pd.read_csv(BytesIO(csv_bytes))
    return df


def main():
    S3_BUCKET = "spotfire-admin"
    S3_KEY = "analyst-functions-users.csv"

    try:
        # Read CSV from S3
        cu.header("Reading CSV from S3")
        df = read_csv_from_bucket(bucket=S3_BUCKET, key=S3_KEY)
        cu.key_value("Rows read", len(df))
        cu.key_value("Columns", df.columns.tolist())

        # Upload to PostgreSQL
        cu.header("Uploading to PostgreSQL")
        
    except Exception as e:
        cu.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()
