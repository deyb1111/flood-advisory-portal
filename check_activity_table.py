import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError(
        "DATABASE_URL is not configured. Set it in the project's .env file "
        "and run this script from the project root."
    )

engine = create_engine(database_url)

with engine.connect() as conn:

    # 1. Check database connection
    print("Database Information:")

    info = conn.execute(text("""
        SELECT
            DATABASE() AS database_name,
            @@hostname AS mysql_host,
            @@port AS mysql_port,
            CURRENT_USER() AS mysql_account,
            @@version AS mysql_version,
            @@datadir AS data_directory
    """)).mappings().one()

    print(dict(info))

    # 2. Check table definition
    result = conn.execute(
        text("SHOW CREATE TABLE activity_logs")
    )

    print("\nTable Definition:")
    print(result.fetchone()[1])

    # 3. Check record count
    count = conn.execute(
        text("SELECT COUNT(*) FROM activity_logs")
    ).scalar_one()

    print("\nActivity Log Count:", count)

    # 4. Check transaction isolation
    try:
        isolation = conn.execute(
            text("SELECT @@tx_isolation")
        ).scalar_one()

        print("Transaction Isolation:", isolation)

    except Exception as e:
        print("Could not retrieve transaction isolation:", e)

    # 5. Display all activity log records
    result = conn.execute(text("""
        SELECT *
        FROM activity_logs
        ORDER BY log_id DESC
    """))

    print("\nActivity Log Records:")

    for row in result.mappings():
        print(dict(row))

    # 6. Check database version and directory
    print("\nDatabase Verification:")

    print(
        conn.execute(
            text("SELECT @@version, @@datadir, DATABASE()")
        ).fetchone()
    )

    # 7. Check fully qualified table count
    print(
        "Qualified Table Count:",
        conn.execute(
            text("""
                SELECT COUNT(*)
                FROM bantay_daan_pasig.activity_logs
            """)
        ).scalar_one()
    )

engine.dispose()
