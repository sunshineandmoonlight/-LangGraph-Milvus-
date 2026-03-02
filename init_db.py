"""
Database initialization script
Run this to create all database tables and demo user
"""
from app.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.session import ChatSession
import bcrypt


def get_password_hash_fixed(password: str) -> str:
    """加密密码 - 使用合法的 rounds 值"""
    salt = bcrypt.gensalt(rounds=4)  # rounds 最小值为 4
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def init_db():
    """Create all tables and demo user"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

    # Create demo user
    db = SessionLocal()
    try:
        # Check if demo user exists
        existing_user = db.query(User).filter(User.email == "demo@enterprise.ai").first()
        if not existing_user:
            demo_user = User(
                email="demo@enterprise.ai",
                username="demo",
                full_name="Demo User",
                hashed_password=get_password_hash_fixed("demo123"),
                is_active=True,
                is_admin=False,
                api_quota=1000,
                api_used=0
            )
            db.add(demo_user)
            db.commit()
            print("Demo user created: demo@enterprise.ai / demo123")
        else:
            print("Demo user already exists")

    except Exception as e:
        print(f"Error creating demo user: {e}")
        db.rollback()
    finally:
        db.close()

    print("Database initialization complete!")


if __name__ == "__main__":
    init_db()
