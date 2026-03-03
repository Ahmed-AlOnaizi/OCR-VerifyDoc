from app.database import SessionLocal
from app.models.user import User

SAMPLE_USERS = [
    {
        "name": "Ahmad Al-Sabah",
        "phone": "+965-5551-0001",
        "email": "ahmad@example.com",
    },
    {
        "name": "فاطمة الراشد",
        "phone": "+965-5551-0002",
        "email": "fatima@example.com",
    },
    {
        "name": "Mohammed Al-Mutairi",
        "phone": "+965-5551-0003",
        "email": "mohammed@example.com",
    },
]


def seed_users():
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return
        for data in SAMPLE_USERS:
            db.add(User(**data))
        db.commit()
    finally:
        db.close()
