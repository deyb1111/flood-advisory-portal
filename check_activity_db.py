from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Configured database:", db.engine.url.database)
    print("Configured host:", db.engine.url.host)
    print("Configured port:", db.engine.url.port)

    with db.engine.connect() as conn:
        info = conn.execute(text("""
            SELECT
                DATABASE() AS database_name,
                @@hostname AS mysql_host,
                @@port AS mysql_port,
                CURRENT_USER() AS mysql_account,
                CONNECTION_ID() AS connection_id
        """)).mappings().one()

        count = conn.execute(
            text("SELECT COUNT(*) FROM activity_logs")
        ).scalar_one()

        print("Actual MySQL connection:", dict(info))
        print("Activity log count:", count)

        rows = conn.execute(text("""
            SELECT log_id, action, created_at
            FROM activity_logs
            ORDER BY log_id DESC
            LIMIT 10
        """)).fetchall()

        print("Latest activity records:")
        for row in rows:
            print(tuple(row))