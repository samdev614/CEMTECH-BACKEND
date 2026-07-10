"""
Run once to create or refresh the admin user:
  python seed.py
"""

from app.utils.create_admin import create_admin


if __name__ == "__main__":
    create_admin()
