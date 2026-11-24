
import random
from datetime import date, timedelta

from database import init_db, conn

# Sample synthetic data
names = [
    "Ananya", "Lakshmi", "Priya", "Kavya", "Divya",
    "Meena", "Geetha", "Asha", "Pooja", "Suma",
    "Ravi", "Arun", "Kiran", "Manoj", "Rahul",
    "Sneha", "Nisha", "Deepa", "Rani", "Swathi"
]

villages = [
    "Hoskote", "Nandagudi", "Sulibele", "Jadigenahalli",
    "Anugondanahalli", "Samethanahalli", "Budigere",
    "Muthsandra", "Kambalipura", "Shivanapura"
]

categories = ["Pregnant", "Mother", "Child"]

def generate_beneficiaries():
    init_db()

    with conn() as c:
        existing = c.execute(
            "SELECT id FROM beneficiaries"
        ).fetchall()

        existing_ids = {row["id"] for row in existing}
        total = len(existing_ids)

        print("Existing beneficiaries:", total)

        next_id = 1
        added = 0

        while total < 200:
            person_id = f"B{next_id:03d}"
            next_id += 1

            if person_id in existing_ids:
                continue

            category = random.choice(categories)

            if category == "Pregnant":
                age = random.randint(18, 40)
                due_date = (
                    date.today() + timedelta(days=random.randint(1, 250))
                ).isoformat()
            elif category == "Mother":
                age = random.randint(19, 45)
                due_date = ""
            else:
                age = random.randint(1, 5)
                due_date = ""

            c.execute("""
                INSERT INTO beneficiaries
                (id, name, village, age, category, due_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                person_id,
                random.choice(names),
                random.choice(villages),
                age,
                category,
                due_date
            ))

            existing_ids.add(person_id)
            total += 1
            added += 1

        print("New beneficiaries added:", added)
        print("Total beneficiaries now:", total)


if __name__ == "__main__":
    generate_beneficiaries()
