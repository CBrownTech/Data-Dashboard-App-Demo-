"""Create the BigQuery dataset and tables this app expects.

Run once after configuring .env:  python setup_bigquery.py

Idempotent: uses CREATE TABLE IF NOT EXISTS, so re-running is safe and will not
drop existing data. Pass --drop to recreate tables from scratch (destructive).
"""
import argparse

from google.cloud import bigquery

from db.database import DATASET, PROJECT, get_client, table

# DDL for every table, keyed by table name. Schema mirrors the document shapes
# the repositories read and write.
TABLE_SCHEMAS = {
    "users": """
        user_id INT64, name STRING, email STRING, password_hash STRING,
        is_admin BOOL, role STRING, nonprofit_id INT64,
        is_deleted BOOL, deleted_at TIMESTAMP, created_at TIMESTAMP
    """,
    "nonprofits": """
        nonprofit_id INT64, name STRING, slug STRING, mission STRING, location STRING,
        reference_code STRING, source_code STRING, is_active BOOL, created_at TIMESTAMP
    """,
    "donors": """
        donor_id INT64, nonprofit_id INT64, name STRING, email STRING,
        donation_amount FLOAT64, created_at TIMESTAMP
    """,
    "programs": """
        program_id INT64, nonprofit_id INT64, name STRING, status STRING,
        participants INT64, budget FLOAT64, created_at TIMESTAMP
    """,
    "nonprofit_metrics": """
        nonprofit_id INT64, updated_at TIMESTAMP,
        donor_count INT64, total_donations FLOAT64, active_volunteers INT64, volunteer_hours INT64,
        funding_goal FLOAT64, funding_raised FLOAT64, grants_received FLOAT64,
        email_opens_current INT64, email_opens_previous INT64, highest_donation FLOAT64,
        biggest_donor_name STRING, email_opens_change INT64, email_opens_change_pct FLOAT64,
        p2p_messages_sent INT64, p2p_responses INT64, p2p_opt_outs INT64, p2p_response_rate FLOAT64,
        call_hours FLOAT64, calls_made INT64, contacts_reached INT64, call_avg_duration_minutes FLOAT64,
        email_donations FLOAT64, email_donation_count INT64, p2p_donations FLOAT64, p2p_donation_count INT64,
        call_donations FLOAT64, call_donation_count INT64
    """,
    "nonprofit_weekly_metrics": """
        nonprofit_id INT64, week_start DATE,
        email_opens INT64, p2p_messages_sent INT64, p2p_responses INT64, p2p_opt_outs INT64,
        call_hours FLOAT64, calls_made INT64, contacts_reached INT64,
        donations_total FLOAT64, email_donations FLOAT64, p2p_donations FLOAT64, call_donations FLOAT64,
        donor_count INT64, active_volunteers INT64, volunteer_hours INT64, funding_raised FLOAT64
    """,
}


def ensure_dataset(client):
    dataset_id = f"{PROJECT}.{DATASET}"
    client.create_dataset(bigquery.Dataset(dataset_id), exists_ok=True)
    print(f"Dataset ready: {dataset_id}")


def create_tables(client, drop=False):
    for name, columns in TABLE_SCHEMAS.items():
        if drop:
            client.query(f"DROP TABLE IF EXISTS {table(name)}").result()
        client.query(f"CREATE TABLE IF NOT EXISTS {table(name)} ({columns})").result()
        print(f"  Table ready: {name}")


def main():
    parser = argparse.ArgumentParser(description="Create BigQuery dataset and tables.")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop and recreate tables (destructive — deletes all rows).",
    )
    args = parser.parse_args()

    client = get_client()
    ensure_dataset(client)
    create_tables(client, drop=args.drop)
    print("BigQuery setup complete.")


if __name__ == "__main__":
    main()
