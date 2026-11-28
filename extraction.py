
import re


def extract_visit_details(text):
    original_text = text.strip()
    text = original_text.lower()

    details = {
        "patient_name": None,
        "age": None,
        "pregnancy_months": None,
        "bp_sys": None,
        "bp_dia": None,
        "weight": None,
        "symptoms": [],
        "notes": original_text
    }

    # Extract patient name
    name_match = re.search(
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+patient\b",
        original_text
    )
    if name_match:
        details["patient_name"] = name_match.group(1)

    # Extract age
    age_match = re.search(
        r"\b(?:age\s*)?(\d{1,3})\s*(?:years?|yrs?)\b|\b(\d{1,3})\s+age\b",
        text
    )
    if age_match:
        details["age"] = int(age_match.group(1) or age_match.group(2))

    # Extract pregnancy month
    month_match = re.search(r"(\d{1,2})\s*(?:month|months)\b", text)
    if month_match:
        details["pregnancy_months"] = int(month_match.group(1))

    # Extract blood pressure
    bp_match = re.search(
    r"\b(\d{2,3})\s*(?:/|over)\s*(\d{2,3})\b",
    text
    )
    if bp_match:
        details["bp_sys"] = int(bp_match.group(1))
        details["bp_dia"] = int(bp_match.group(2))

    # Extract weight
    weight_match = re.search(r"(\d{2,3}(?:\.\d+)?)\s*kg\b", text)
    if weight_match:
        details["weight"] = float(weight_match.group(1))

    # Extract symptoms
    symptom_keywords = [
        "fever", "headache", "vomiting",
        "swelling", "cough", "weakness",
        "dizziness", "pain"
    ]

    for symptom in symptom_keywords:
        if symptom in text:
            details["symptoms"].append(symptom)

    return details


if __name__ == "__main__":
    sample = "Nirmala patient 52 age Having fever"
    print(extract_visit_details(sample))
