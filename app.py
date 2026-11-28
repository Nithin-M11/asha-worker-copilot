import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from pathlib import Path
from database import (
    init_db,
    seed_demo_data,
    save_visit,
    get_beneficiaries,
    get_visits,
    get_todos,
    mark_followup_done,
    get_dashboard_data,
    sync_pending,
    add_beneficiary,
    update_beneficiary
)
from engine import extract_visit, assess_risk, SYMPTOMS

st.set_page_config(page_title="ASHA Worker Copilot", page_icon="🩺", layout="wide")
init_db()
seed_demo_data()

st.markdown("""
<style>
.block-container {padding-top: 1.3rem; max-width: 1200px;}
.hero {padding: 1.2rem 1.5rem; border-radius: 16px; background: linear-gradient(110deg,#e7f5f1,#edf3ff);}
.hero h1 {margin:0; color:#143b55;}
.small-note {color:#536878; font-size:.9rem;}
div[data-testid="stMetric"] {background:#f6f9fb;padding:12px;border-radius:12px;border:1px solid #e6edf2;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🩺 ASHA Worker Copilot</h1><p>Voice-first visit records • Offline-first demo • Transparent risk flags</p></div>', unsafe_allow_html=True)
st.caption("Prototype only • Uses synthetic demo records • Flags and refers; does not diagnose or prescribe.")

page = st.sidebar.radio("Navigate", ["Overview", "Record a visit", "Beneficiaries", "Daily to-do", "PHC dashboard", "Sync & export", "About & safety"])

if page == "Overview":
    data = get_dashboard_data()
    a,b,c,d = st.columns(4)
    a.metric("Beneficiaries", data["beneficiaries"])
    b.metric("Visits recorded", data["visits"])
    c.metric("Open risk flags", data["open_flags"])
    d.metric("Pending sync", data["pending_sync"])
    st.subheader("Recent visit records")
    recent = get_visits().head(8)
    if recent.empty: st.info("No visits recorded yet.")
    else: st.dataframe(recent, use_container_width=True, hide_index=True)
    st.info("Start with **Record a visit**. Use the sample voice-note text to test extraction, then review every field before saving.")


elif page == "Record a visit":
    st.subheader("Capture a home-visit note")

    people = get_beneficiaries()

    if people.empty:
        st.warning("No beneficiaries registered. Please register a beneficiary first.")
        st.stop()

    options = {
        f'{r["name"]} · {r["village"]} · {r["id"]}': r["id"]
        for _, r in people.iterrows()
    }

    selected = st.selectbox("Beneficiary", list(options.keys()))

    st.markdown("**1. Add a voice note**")

    audio = st.audio_input("Record after the visit (optional)")

    if "pending_transcript" in st.session_state:
        st.session_state["visit_transcript"] = st.session_state.pop("pending_transcript")

    transcript = st.text_area(
        "Transcript / visit note",
        placeholder="Example: Lakshmi is 7 months pregnant. She has headache and swelling in feet. BP 145 over 92. Weight 58 kg.",
        height=110,
        key="visit_transcript"
    )

    if audio:
        st.caption("Audio captured in this browser.")

        if st.button("Transcribe audio with local Whisper"):
            try:
                audio_path = Path("data") / "latest_visit_audio.wav"
                audio_path.write_bytes(audio.getvalue())

                import whisper
                model = whisper.load_model("base")
                result = model.transcribe(str(audio_path), fp16=False)

                st.session_state["pending_transcript"] = result.get("text", "").strip()

                st.success("Transcription complete.")
                st.rerun()

            except Exception as e:
                st.error(f"Whisper could not run: {e}. Install openai-whisper and FFmpeg, or enter the transcript manually.")

    if st.button("Extract fields from note", type="primary"):
        st.session_state["extracted"] = extract_visit(transcript)
        st.session_state["raw_note"] = transcript

    extracted = st.session_state.get("extracted", {})

    if extracted:
        st.markdown("**2. Review and correct extracted fields**")
        st.caption("Automatic extraction is only a draft. Confirm every field before saving.")

        with st.form("confirm_visit"):
            name = st.text_input(
                "Name",
                value=people.loc[
                    people.id == options[selected], "name"
                ].iloc[0]
            )

            pregnancy_months = st.number_input(
                "Pregnancy month (0 if not applicable)",
                0, 10, int(extracted.get("pregnancy_months") or 0)
            )

            bp_sys = st.number_input(
                "Systolic BP (mmHg; 0 if not recorded)",
                0, 250, int(extracted.get("bp_sys") or 0)
            )

            bp_dia = st.number_input(
                "Diastolic BP (mmHg; 0 if not recorded)",
                0, 160, int(extracted.get("bp_dia") or 0)
            )

            weight = st.number_input(
                "Weight (kg; 0 if not recorded)",
                0.0, 200.0,
                float(extracted.get("weight") or 0.0),
                step=0.5
            )

            symptoms = st.multiselect(
                "Symptoms (tap to select if speech extraction missed them)",
                SYMPTOMS,
                default=extracted.get("symptoms", [])
            )

            days_since = st.number_input(
                "Days since last ANC check-up",
                0, 365,
                int(extracted.get("days_since_last_anc") or 0)
            )

            notes = st.text_area(
                "Visit notes",
                value=st.session_state.get("raw_note", "")
            )

            visit_date = st.date_input("Visit date", date.today())

            submitted = st.form_submit_button(
                "Confirm & save visit",
                type="primary"
            )

            if submitted:
                person_id = options[selected]

                flags = assess_risk({
                    "bp_sys": bp_sys,
                    "bp_dia": bp_dia,
                    "symptoms": symptoms,
                    "days_since_last_anc": days_since,
                    "pregnancy_months": pregnancy_months
                })

                save_visit(
                    person_id,
                    visit_date.isoformat(),
                    pregnancy_months,
                    bp_sys,
                    bp_dia,
                    weight,
                    symptoms,
                    notes,
                    flags
                )

                st.session_state.pop("extracted", None)
                st.session_state.pop("raw_note", None)
                st.session_state.pop("visit_transcript", None)
                st.session_state.pop("pending_transcript", None)

                st.success("Visit saved locally. Review any flags with the appropriate health professional.")

                if flags:
                    for f in flags:
                        st.warning(f)
                else:
                    st.info("No prototype rule was triggered. This does not mean the person is medically clear.")

                st.rerun()


elif page == "Beneficiaries":
    df = get_beneficiaries()
    
    st.subheader("Register a New Beneficiary")

    with st.form("beneficiary_form"):

        person_id = st.text_input("Beneficiary ID")
        name = st.text_input("Full Name")
        village = st.text_input("Village")

        age = st.number_input(
            "Age",
            min_value=1,
            max_value=120,
            value=25
        )

        category = st.selectbox(
            "Category",
            ["Pregnant", "Mother", "Child"]
        )

        due_date = st.date_input("Expected Due Date")

        submitted = st.form_submit_button("Register Beneficiary")

        if submitted:

            person_id = person_id.strip()
            name = name.strip()
            village = village.strip()

            if not person_id or not name or not village:
                st.error("Please fill in all required fields.")

            elif not df.empty and df["id"].astype(str).str.casefold().eq(person_id.casefold()).any():
                st.error("This Beneficiary ID already exists. Please use a different ID.")

            else:
                try:
                    add_beneficiary(
                        person_id,
                        name,
                        village,
                        int(age),
                        category,
                        due_date.isoformat() if category == "Pregnant" else ""
                    )

                    st.success("Beneficiary registered successfully!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Unable to register beneficiary: {e}")

    
    st.subheader("Edit Beneficiary Details")

    if not df.empty:
        selected_id = st.selectbox(
            "Select Beneficiary ID to edit",
            df["id"].tolist(),
            key="edit_beneficiary_id"
        )

        selected = df[df["id"] == selected_id].iloc[0]

        with st.form("edit_beneficiary_form"):
            edit_name = st.text_input("Full Name", value=selected["name"])
            edit_village = st.text_input("Village", value=selected["village"])
            edit_age = st.number_input(
                "Age", min_value=1, max_value=120,
                value=int(selected["age"])
            )

            categories = ["Pregnant", "Mother", "Child"]
            edit_category = st.selectbox(
                "Category",
                categories,
                index=categories.index(selected["category"])
            )

            existing_date = selected["due_date"]
            default_date = (
                date.fromisoformat(existing_date)
                if existing_date else date.today()
            )

            edit_due_date = st.date_input(
                "Expected Due Date",
                value=default_date
            )

            update_button = st.form_submit_button("Update Beneficiary")

            if update_button:
                if not edit_name.strip() or not edit_village.strip():
                    st.error("Name and village are required.")
                else:
                    update_beneficiary(
                        selected_id,
                        edit_name.strip(),
                        edit_village.strip(),
                        int(edit_age),
                        edit_category,
                        edit_due_date.isoformat() if edit_category == "Pregnant" else ""
                    )
                    st.success("Beneficiary updated successfully!")
                    st.rerun()

    st.subheader("Individual Beneficiary Details")

    if not df.empty:

        details_id = st.selectbox(
            "Select a beneficiary to view details",
            df["id"].tolist(),
            key="details_beneficiary_id"
        )

        person = df[df["id"] == details_id].iloc[0]

        col1, col2, col3 = st.columns(3)

        col1.write("**Beneficiary ID**")
        col1.write(person["id"])

        col2.write("**Full Name**")
        col2.write(person["name"])

        col3.write("**Age**")
        col3.write(person["age"])

        col1, col2, col3 = st.columns(3)

        col1.write("**Village**")
        col1.write(person["village"])

        col2.write("**Category**")
        col2.write(person["category"])

        col3.write("**Expected Due Date**")
        col3.write(person["due_date"] if person["due_date"] else "Not applicable")

        st.markdown("#### Visit History")

        visits_df = get_visits()

        beneficiary_visits = visits_df[
            visits_df["beneficiary_id"].astype(str) == str(details_id)
        ]

        if not beneficiary_visits.empty:

            st.dataframe(
                beneficiary_visits,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("No visit records available for this beneficiary.")

    st.subheader("Beneficiary register")

    

    if not df.empty:
        st.subheader("Beneficiary Overview")

        total = len(df)
        pregnant = (df["category"] == "Pregnant").sum()
        mothers = (df["category"] == "Mother").sum()
        children = (df["category"] == "Child").sum()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Beneficiaries", total)
        col2.metric("Pregnant Women", pregnant)
        col3.metric("Mothers", mothers)
        col4.metric("Children", children)

        # Search by ID or name
        search = st.text_input(
            "Search by Beneficiary ID or Name",
            placeholder="Enter ID or name..."
        )

        # Filter options
        col1, col2 = st.columns(2)

        with col1:
            villages = ["All"] + sorted(
                df["village"].dropna().astype(str).unique().tolist()
            )

            selected_village = st.selectbox(
                "Filter by Village",
                villages
            )

        with col2:
            categories = ["All"] + sorted(
                df["category"].dropna().astype(str).unique().tolist()
            )

            selected_category = st.selectbox(
                "Filter by Category",
                categories
            )

        # Apply search
        filtered_df = df.copy()

        if search.strip():
            search_mask = (
                filtered_df["id"].astype(str).str.contains(
                    search.strip(), case=False, na=False, regex=False
                )
                |
                filtered_df["name"].astype(str).str.contains(
                    search.strip(), case=False, na=False, regex=False
                )
            )
            filtered_df = filtered_df[search_mask]

        # Apply village filter
        if selected_village != "All":
            filtered_df = filtered_df[
                filtered_df["village"] == selected_village
            ]

        # Apply category filter
        if selected_category != "All":
            filtered_df = filtered_df[
                filtered_df["category"] == selected_category
            ]

        st.write(f"Showing {len(filtered_df)} beneficiaries")

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No beneficiaries registered yet.")

    st.caption("All names and records are fictional sample data.")


    
    

elif page == "Daily to-do":
    st.subheader("Daily follow-up list")
    todos = get_todos()
    if todos.empty: st.success("No open follow-ups in the demo database.")
    else:
        for _, row in todos.iterrows():
            cols = st.columns([3,2,2,1])
            cols[0].write(f"**{row['name']}** · {row['village']}")
            cols[1].write(row["task"])
            cols[2].write(row["due_date"])
            if cols[3].button("Done", key=f"done{row['id']}"):
                mark_followup_done(int(row["id"])); st.rerun()

elif page == "PHC dashboard":
    st.subheader("Supervisor / PHC view")
    visits = get_visits()
    if visits.empty: st.info("No visits yet.")
    else:
        flagged = visits[visits["risk_flags"].fillna("") != ""]
        x,y = st.columns(2)
        x.metric("Flagged visits", len(flagged))
        y.metric("Total recorded visits", len(visits))
        st.markdown("**Cases requiring review**")
        if flagged.empty: st.success("No rule-triggered flags in recorded visits.")
        else: st.dataframe(flagged[["visit_date","name","village","risk_flags","sync_status"]],use_container_width=True,hide_index=True)
        st.markdown("**Visits by village**")
        counts = visits.groupby("village").size().rename("visits")
        st.bar_chart(counts)
        st.download_button("Download dashboard CSV", visits.to_csv(index=False), "asha_visits.csv", "text/csv")

elif page == "Sync & export":
    st.subheader("Offline-first sync demonstration")
    st.write("Records are written to the local SQLite database first. The button below simulates uploading pending records by marking them as synced in this demo database. It does not connect to a real PHC server.")
    pending = get_visits()
    pending_count = int((pending["sync_status"]=="pending").sum()) if not pending.empty else 0
    st.metric("Records waiting to sync", pending_count)
    if st.button("Sync pending records", type="primary", disabled=(pending_count==0)):
        count = sync_pending()
        st.success(f"Demo sync complete: {count} record(s) marked as synced.")
        st.rerun()
    df = get_visits()
    if not df.empty:
        st.download_button("Export all visits as CSV",df.to_csv(index=False),"asha_visits_export.csv","text/csv")

else:
    st.subheader("Prototype scope and safety")
    st.markdown("""
- **Voice-first:** browser audio capture; optional local Whisper transcription.
- **Extraction:** keyword matching and regular expressions for symptoms, BP, weight and pregnancy month.
- **Local storage:** SQLite database, saved on this device.
- **Risk flags:** simple, visible Python rules intended only to demonstrate workflow.
- **Follow-ups:** sample due tasks and a daily list.
- **PHC dashboard:** rule-triggered cases and village-level visit counts.
- **Sync:** simulated status change only; no remote server is configured.

**Important clinical limitation:** The included thresholds and rules are illustrative software-demo logic, not validated clinical decision support. They have not been reviewed or approved by a doctor/ANM and must not be used to make care decisions. A real pilot requires current Ministry of Health guidance, review by qualified clinicians, privacy/security controls, informed consent, role-based access, encryption, audit logs and field testing. Never enter real patient information in this prototype.
""")