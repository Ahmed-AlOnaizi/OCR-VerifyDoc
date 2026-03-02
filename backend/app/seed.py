from app.database import SessionLocal
from app.models.user import User

SAMPLE_USERS = [
    {
        "civil_id": "281234567890",
        "name_en": "Ahmad Al-Sabah",
        "name_ar": "أحمد الصباح",
        "employer": "Kuwait Petroleum Corporation",
        "salary": 1500.0,
    },
    {
        "civil_id": "290987654321",
        "name_en": "Fatima Al-Rashid",
        "name_ar": "فاطمة الراشد",
        "employer": "National Bank of Kuwait",
        "salary": 2200.0,
    },
    {
        "civil_id": "300112233445",
        "name_en": "Mohammed Al-Mutairi",
        "name_ar": "محمد المطيري",
        "employer": "Zain Telecom",
        "salary": 1800.0,
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
