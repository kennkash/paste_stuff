from io import BytesIO
import math
import pandas as pd
from s2cloudapi import s3api as s3
from databases.psql import (
    AnalystFunctionsUser,
    session,
    cu,
)
from sqlalchemy import text


COLUMNS = [
    "USER_NAME",
    "USER_EMAIL",
    "LAST_ACTIVITY",
    "ANALYST_FUNCTIONS",
    "NON_ANALYST_FUNCTIONS",
    "ANALYST_PCT",
    "ANALYST_USER_FLAG",
    "ANALYST_THRESHOLD",
    "ANALYST_ACTIONS_PER_DAY",
    "ANALYST_ACTIONS_PER_ACTIVE_DAYS",
    "ACTIVE_DAYS",
]


def read_csv_from_bucket(bucket: str, key: str) -> pd.DataFrame:
    """Read a CSV object from S3 and return a pandas DataFrame."""
    boto_object = s3.get_object(bucket=bucket, key=key)
    csv_bytes = boto_object["Body"].read()
    return pd.read_csv(BytesIO(csv_bytes))


def _coerce_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    # Keep only requested columns (and fail loudly if missing)
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    df = df[COLUMNS].copy()

    # Datetime conversion
    df["LAST_ACTIVITY"] = pd.to_datetime(df["LAST_ACTIVITY"], errors="coerce", utc=False)

    # Numeric coercions (safe even if already numeric)
    int_cols = ["ANALYST_FUNCTIONS", "NON_ANALYST_FUNCTIONS", "ANALYST_USER_FLAG", "ACTIVE_DAYS"]
    float_cols = ["ANALYST_PCT", "ANALYST_THRESHOLD", "ANALYST_ACTIONS_PER_DAY", "ANALYST_ACTIONS_PER_ACTIVE_DAYS"]

    for c in int_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")  # nullable integer

    for c in float_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Normalize empty strings to NA for string cols
    for c in ["USER_NAME", "USER_EMAIL"]:
        df[c] = df[c].astype("string")
        df.loc[df[c].str.strip() == "", c] = pd.NA

    return df


def _df_to_mappings(df: pd.DataFrame) -> list[dict]:
    """
    Convert DataFrame rows -> list of dicts, converting pandas NA/NaN to None,
    and pandas Timestamp to python datetime.
    """
    records = df.to_dict(orient="records")
    cleaned = []

    for r in records:
        row = {}
        for k, v in r.items():
            # pandas NA
            if v is pd.NA:
                row[k] = None
                continue

            # NaN / inf
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                row[k] = None
                continue

            # pandas Timestamp -> python datetime
            if isinstance(v, pd.Timestamp):
                row[k] = None if pd.isna(v) else v.to_pydatetime()
                continue

            # pandas nullable int -> python int
            # (covers numpy / pandas scalars too)
            try:
                if hasattr(v, "item"):
                    v = v.item()
            except Exception:
                pass

            row[k] = v
        cleaned.append(row)

    return cleaned


def bulk_insert_analyst_users(df: pd.DataFrame, truncate_first: bool = True, chunk_size: int = 5000) -> None:
    df = _coerce_and_clean(df)
    mappings = _df_to_mappings(df)

    cu.key_value("Rows to insert", len(mappings))

    try:
        if truncate_first:
            cu.key_value("Action", "TRUNCATE analyst_functions_users (restart identity)")
            # Table lives in your configured schema from psql.py (license / license-dev)
            # Using unqualified name is fine because your Base metadata schema sets search_path effectively,
            # but being explicit is safer:
            # session.execute(text('TRUNCATE TABLE "license-dev".analyst_functions_users RESTART IDENTITY'))
            session.execute(text('TRUNCATE TABLE analyst_functions_users RESTART IDENTITY'))

        # Insert in chunks
        for i in range(0, len(mappings), chunk_size):
            chunk = mappings[i : i + chunk_size]
            session.bulk_insert_mappings(AnalystFunctionsUser, chunk)
            cu.key_value("Inserted", f"{min(i + chunk_size, len(mappings))}/{len(mappings)}")

        session.commit()
        cu.success("Upload complete")

    except Exception as e:
        session.rollback()
        cu.error(f"Upload failed, rolled back: {e}")
        raise


def main():
    S3_BUCKET = "spotfire-admin"
    S3_KEY = "analyst-functions-users.csv"

    try:
        cu.header("Reading CSV from S3")
        df = read_csv_from_bucket(bucket=S3_BUCKET, key=S3_KEY)
        cu.key_value("Rows read", len(df))
        cu.key_value("Columns (raw)", df.columns.tolist())

        cu.header("Uploading to PostgreSQL")
        bulk_insert_analyst_users(df, truncate_first=True, chunk_size=5000)

        # quick sanity check
        cu.header("Sanity check")
        count = session.execute(text("SELECT COUNT(*) FROM analyst_functions_users")).scalar()
        cu.key_value("Rows in table", count)

    except Exception as e:
        cu.error(f"An error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    main()
