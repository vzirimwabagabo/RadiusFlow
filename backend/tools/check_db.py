"""Quick DB connectivity check used during debugging."""
from sqlalchemy import text
from database import engine


def main():
    try:
        with engine.connect() as conn:
            print("DB: connected")
            try:
                res = conn.execute(text("SELECT 1")).scalar()
                print("SELECT 1 ->", res)
            except Exception as e:
                print("SELECT 1 failed:", e)
            # Try a lightweight schema check
            try:
                cnt = conn.execute(text("SELECT count(*) FROM radcheck LIMIT 1")).scalar()
                print("radcheck count (sample):", cnt)
            except Exception as e:
                print("radcheck query failed (table may not exist or access denied):", e)
    except Exception as e:
        print("DB connection failed:", e)


if __name__ == '__main__':
    main()
