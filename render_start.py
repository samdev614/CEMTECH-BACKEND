import argparse
import os
import socket
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).resolve().parent
REVISION_DIR = ROOT / "alembic" / "versions"


def get_db_url():
    from app.core.config import settings

    db_url = settings.DATABASE_URL
    if not db_url:
        raise RuntimeError("DATABASE_URL is not configured.")
    return db_url


def validate_db_host(db_url):
    parsed = urlparse(db_url)
    host = parsed.hostname

    if not host:
        raise RuntimeError("DATABASE_URL is missing a hostname.")

    port = parsed.port or 5432
    try:
        socket.getaddrinfo(host, port)
    except socket.gaierror as exc:
        raise RuntimeError(
            f"DATABASE_URL host '{host}' could not be resolved. "
            "If this is a Render internal Postgres URL, the web service and database "
            "must be in the same region/account and able to use the private network. "
            "Otherwise update the service to use the database's external URL."
        ) from exc


def get_local_revisions():
    return {p.stem.split("_", 1)[0] for p in REVISION_DIR.glob("*.py")}


def run_alembic(args):
    cmd = [sys.executable, "-m", "alembic"] + args
    print("Running:", " ".join(cmd), flush=True)
    try:
        subprocess.check_call(cmd, cwd=str(ROOT))
    except subprocess.CalledProcessError as e:
        print(f"Alembic command failed with exit code {e.returncode}", file=sys.stderr, flush=True)
        raise


def retrieve_db_revision(engine):
    inspector = inspect(engine)
    if not inspector.has_table("alembic_version"):
        return None

    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        rows = [row[0] for row in result]
        if not rows:
            return None
        if len(rows) > 1:
            raise RuntimeError(f"Multiple alembic_version rows found: {rows}")
        return rows[0]


def has_user_tables(engine):
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return [t for t in tables if t != "alembic_version"]


def clear_stale_revision(engine):
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM alembic_version"))
        conn.commit()


def upgrade_database(engine):
    current_rev = retrieve_db_revision(engine)
    local_revisions = get_local_revisions()

    if current_rev is None:
        print("No alembic_version row found. Running alembic upgrade head.")
        run_alembic(["upgrade", "head"])
        return

    if current_rev in local_revisions:
        print(f"Database revision {current_rev} exists locally. Running alembic upgrade head.")
        run_alembic(["upgrade", "head"])
        return

    user_tables = has_user_tables(engine)
    if user_tables:
        raise RuntimeError(
            f"Database contains a stale Alembic revision '{current_rev}' and user tables {user_tables}. "
            "Please manually fix alembic_version or migrate the database schema."
        )

    print(
        f"Stale Alembic revision '{current_rev}' found, but no user tables exist. "
        "Clearing alembic_version and running alembic upgrade head."
    )
    clear_stale_revision(engine)
    run_alembic(["upgrade", "head"])


def parse_args():
    parser = argparse.ArgumentParser(description="Run Alembic migrations and start the app.")
    parser.add_argument("--check", action="store_true", help="Validate DB revision and local migrations without starting the app.")
    return parser.parse_args()


def main():
    try:
        args = parse_args()
        db_url = get_db_url()
        validate_db_host(db_url)
        import app.models # noqa: F401
        engine = create_engine(db_url)

        if args.check:
            current_rev = retrieve_db_revision(engine)
            local_revisions = get_local_revisions()
            print(f"DATABASE_URL={db_url}")
            print(f"current revision={current_rev}")
            print(f"local revisions={sorted(local_revisions)}")
            if current_rev and current_rev not in local_revisions:
                print("WARNING: database revision is not present in local migrations.")
            print("render_start.py check completed.")
            return

        upgrade_database(engine)
        port = os.environ.get("PORT", "8000")
        os.execvp(
            sys.executable,
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port],
        )
    except Exception as e:
        print(f"ERROR in render_start.py: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
