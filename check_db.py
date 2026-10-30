from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        info = conn.execute(text("""
            SELECT
                DATABASE() AS database_name,
                @@hostname AS mysql_host,
                @@port AS mysql_port,
                CURRENT_USER() AS mysql_account
        """)).mappings().one()

        count = conn.execute(
            text("SELECT COUNT(*) FROM activity_logs")
        ).scalar_one()

        print("Flask database connection:", dict(info))
        print("Flask activity log count:", count)

        rows = conn.execute(text("""
            SELECT log_id, action, created_at
            FROM activity_logs
            ORDER BY log_id DESC
            LIMIT 10
        """)).fetchall()

        print("Latest activity records:")
        for row in rows:
            print(tuple(row))