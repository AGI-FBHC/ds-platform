"""
Seed script to create an initial test user.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import SessionLocal
from app.models.user import User
from app.utils.password import get_password_hash


def create_user():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "test@lab.com").first()
        if existing:
            print("Test user already exists!")
            return

        user = User(
            email="test@lab.com",
            password_hash=get_password_hash("test123"),
            nickname="Test User",
            is_active=True
        )
        db.add(user)
        db.commit()
        print("Test user created successfully!")
        print("Email: test@lab.com")
        print("Password: test123")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_user()
