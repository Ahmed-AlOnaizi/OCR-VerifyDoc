from app.database import SessionLocal
from app.models.user import User

SAMPLE_USERS = [
    {
        "civil_id": "000000000001",
        "name_en": "User 1",
        "name_ar": "",
        "employer": "",
        "salary": 0.0,
    },
    {
        "civil_id": "000000000002",
        "name_en": "User 2",
        "name_ar": "",
        "employer": "",
        "salary": 0.0,
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
