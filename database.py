import sqlite3, json, random
from pathlib import Path
import pandas as pd
DB_PATH = Path(__file__).parent / "data" / "asha_copilot.db"

def conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row

    # Enable foreign key relationships
    c.execute("PRAGMA foreign_keys = ON")

    return c

def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS beneficiaries(id TEXT PRIMARY KEY,name TEXT,village TEXT,age INTEGER,category TEXT,due_date TEXT);
        CREATE TABLE IF NOT EXISTS visits(id INTEGER PRIMARY KEY AUTOINCREMENT,beneficiary_id TEXT,visit_date TEXT,pregnancy_months INTEGER,bp_sys INTEGER,bp_dia INTEGER,weight REAL,symptoms TEXT,notes TEXT,risk_flags TEXT,sync_status TEXT DEFAULT 'pending');
        CREATE TABLE IF NOT EXISTS followups(id INTEGER PRIMARY KEY AUTOINCREMENT,beneficiary_id TEXT,task TEXT,due_date TEXT,status TEXT DEFAULT 'open');
        """)

def seed_demo_data():
    with conn() as c:
        if c.execute("SELECT COUNT(*) FROM beneficiaries").fetchone()[0]: return
        people=[
        ("B001","Lakshmi","Mallapura",24,"Pregnant","2026-12-12"),
        ("B002","Rekha","Kolarahatti",27,"Pregnant","2026-12-28"),
        ("B003","Sujatha","Mallapura",22,"Pregnant","2027-01-10"),
        ("B004","Anita","Doddanahalli",29,"Mother",""),
        ("B005","Meena","Kolarahatti",25,"Pregnant","2027-02-02"),
        ("B006","Savitha","Doddanahalli",31,"Mother",""),
        ("B007","Geetha","Mallapura",23,"Pregnant","2027-01-21"),
        ("B008","Kavya","Kolarahatti",26,"Mother","")]
        c.executemany("INSERT INTO beneficiaries VALUES(?,?,?,?,?,?)",people)
        tasks=[("B001","ANC check-up","2026-11-18"),("B002","Follow-up call","2026-11-18"),("B004","Child immunisation follow-up","2026-11-19"),("B005","ANC check-up","2026-11-20"),("B007","Home follow-up","2026-11-21")]
        c.executemany("INSERT INTO followups(beneficiary_id,task,due_date) VALUES(?,?,?)",tasks)
        visits=[
        ("B001","2026-11-15",7,145,92,58.0,["headache","swelling"],"Synthetic demo visit: headache and swelling; BP recorded.", "Same-day PHC review prompt: elevated BP with symptom(s) reported.","pending"),
        ("B002","2026-11-14",6,0,0,54.0,["fever"],"Synthetic demo visit: fever reported.", "", "pending"),
        ("B003","2026-11-13",5,118,76,52.0,[],"Synthetic demo visit: routine follow-up.", "", "synced")]
        c.executemany("""INSERT INTO visits(beneficiary_id,visit_date,pregnancy_months,bp_sys,bp_dia,weight,symptoms,notes,risk_flags,sync_status) VALUES(?,?,?,?,?,?,?,?,?,?)""",
        [(a,b,d,e,f,g,json.dumps(h),i,j,k) for a,b,d,e,f,g,h,i,j,k in visits])

def get_beneficiaries():
    with conn() as c: return pd.read_sql_query("SELECT * FROM beneficiaries ORDER BY village,name",c)


def get_visits():
    with conn() as c:
        df = pd.read_sql_query("""
            SELECT
                v.id,
                v.beneficiary_id,
                v.visit_date,
                b.name,
                b.village,
                v.pregnancy_months,
                v.bp_sys,
                v.bp_dia,
                v.weight,
                v.symptoms,
                v.notes,
                v.risk_flags,
                v.sync_status
            FROM visits v
            JOIN beneficiaries b ON b.id = v.beneficiary_id
            ORDER BY v.visit_date DESC, v.id DESC
        """, c)

    if not df.empty:
        df["symptoms"] = df["symptoms"].apply(
            lambda x: ", ".join(json.loads(x or "[]"))
        )

    return df



def save_visit(person_id, visit_date, months, sys, dia, weight, symptoms, notes, flags):

    # Store missing measurements as NULL instead of zero
    sys = None if sys in (None, 0) else sys
    dia = None if dia in (None, 0) else dia
    weight = None if weight in (None, 0, 0.0) else weight

    with conn() as c:
        c.execute("""
            INSERT INTO visits(
                beneficiary_id,
                visit_date,
                pregnancy_months,
                bp_sys,
                bp_dia,
                weight,
                symptoms,
                notes,
                risk_flags,
                sync_status
            )
            VALUES(?,?,?,?,?,?,?,?,?,'pending')
        """, (
            person_id,
            visit_date,
            months,
            sys,
            dia,
            weight,
            json.dumps(symptoms),
            notes,
            "\n".join(flags)
        ))


def get_todos():
    with conn() as c:
        return pd.read_sql_query("""SELECT f.id,b.name,b.village,f.task,f.due_date FROM followups f JOIN beneficiaries b ON b.id=f.beneficiary_id WHERE f.status='open' ORDER BY f.due_date""",c)

def mark_followup_done(task_id):
    with conn() as c: c.execute("UPDATE followups SET status='done' WHERE id=?",(task_id,))

def get_dashboard_data():
    with conn() as c:
        return {"beneficiaries":c.execute("SELECT COUNT(*) FROM beneficiaries").fetchone()[0],
                "visits":c.execute("SELECT COUNT(*) FROM visits").fetchone()[0],
                "open_flags":c.execute("SELECT COUNT(*) FROM visits WHERE risk_flags != ''").fetchone()[0],
                "pending_sync":c.execute("SELECT COUNT(*) FROM visits WHERE sync_status='pending'").fetchone()[0]}

def sync_pending():
    with conn() as c:
        cur=c.execute("UPDATE visits SET sync_status='synced' WHERE sync_status='pending'")
        return cur.rowcount

def add_beneficiary(person_id, name, village, age, category, due_date):
    with conn() as c:
        c.execute("""
            INSERT INTO beneficiaries
            (id, name, village, age, category, due_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (person_id, name, village, age, category, due_date))

def update_beneficiary(person_id, name, village, age, category, due_date):
    with conn() as c:
        c.execute("""
            UPDATE beneficiaries
            SET name = ?,
                village = ?,
                age = ?,
                category = ?,
                due_date = ?
            WHERE id = ?
        """, (
            name,
            village,
            age,
            category,
            due_date,
            person_id
        ))
