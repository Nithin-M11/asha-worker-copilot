import re

SYMPTOMS = ["headache","swelling","bleeding","blurred vision","fever","severe abdominal pain","reduced fetal movement","convulsions","breathlessness","vomiting"]

def extract_visit(text):
    t = (text or "").lower()
    found = [s for s in SYMPTOMS if s in t]
    month = re.search(r"(\d{1,2})\s*(?:month|months|maas|maasa)", t)
    bp = re.search(r"(?:bp|blood pressure)\s*(?:is|of|:)?\s*(\d{2,3})\s*(?:over|/|by)\s*(\d{2,3})", t)
    if not bp:
        bp = re.search(r"\b(\d{2,3})\s*/\s*(\d{2,3})\b", t)
    weight = re.search(r"(\d{2,3}(?:\.\d+)?)\s*(?:kg|kgs|kilograms?)\b", t)
    days = re.search(r"(\d{1,3})\s*days?\s*(?:since|from)\s*(?:last|previous)", t)
    return {
        "pregnancy_months": int(month.group(1)) if month else 0,
        "bp_sys": int(bp.group(1)) if bp else 0,
        "bp_dia": int(bp.group(2)) if bp else 0,
        "weight": float(weight.group(1)) if weight else 0.0,
        "symptoms": found,
        "days_since_last_anc": int(days.group(1)) if days else 0
    }

def assess_risk(record):
    """Illustrative demonstration rules only; not clinically validated."""
    flags=[]
    symptoms=set(record.get("symptoms") or [])
    sys=int(record.get("bp_sys") or 0); dia=int(record.get("bp_dia") or 0)
    if "bleeding" in symptoms:
        flags.append("Urgent referral prompt: bleeding reported — contact the appropriate health facility immediately.")
    if (sys >= 140 or dia >= 90) and ({"headache","swelling","blurred vision"} & symptoms):
        flags.append("Same-day PHC review prompt: elevated BP with symptom(s) reported.")
    if "convulsions" in symptoms:
        flags.append("Emergency referral prompt: convulsions reported — seek emergency medical care.")
    if "severe abdominal pain" in symptoms:
        flags.append("Prompt clinical review: severe abdominal pain reported.")
    if int(record.get("days_since_last_anc") or 0) > 35:
        flags.append("Follow-up reminder: more than 35 days since last ANC check-up (demo threshold).")
    return flags
