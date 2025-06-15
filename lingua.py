# ===============================
#         STAGE 1: IMPORTS, CONSTANTS, ALL TOPIC LISTS, PROMPT BANK
# ===============================

import os
import random
from datetime import date

import pandas as pd
import streamlit as st
from openai import OpenAI

# --- App constants ---
CODES_FILE = "student_codes.csv"
DAILY_LIMIT = 25
MAX_TURNS = 6

# ---------- A1 ----------
A1_TEIL1_KEYWORDS = ["Name", "Alter", "Land", "Wohnort", "Sprachen", "Beruf", "Hobby"]
A1_TEIL1_FOLLOWUP = [
    "Wie buchstabieren Sie Ihren Namen?",
    "Sind Sie verheiratet? (Ja/Nein)",
    "Wie alt ist Ihre Mutter?",
    "Haben Sie Geschwister?",
    "Welche Sprachen sprechen Sie?",
    "Was machen Sie gern in Ihrer Freizeit?"
]
A1_VOCAB_TEIL2 = [
    ("Geschäft", "schließen"), ("Uhr", "Uhrzeit"), ("Arbeit", "Kollege"),
    ("Hausaufgabe", "machen"), ("Küche", "kochen"), ("Freizeit", "lesen"),
    ("Telefon", "anrufen"), ("Reise", "Hotel"), ("Auto", "fahren"),
    ("Einkaufen", "Obst"), ("Schule", "Lehrer"), ("Geburtstag", "Geschenk"),
    ("Essen", "Frühstück"), ("Arzt", "Termin"), ("Zug", "Abfahrt"),
    ("Wetter", "Regen"), ("Buch", "lesen"), ("Computer", "E-Mail"),
    ("Kind", "spielen"), ("Wochenende", "Plan"), ("Bank", "Geld"),
    ("Sport", "laufen"), ("Abend", "Fernsehen"), ("Freunde", "Besuch"),
    ("Bahn", "Fahrkarte"), ("Straße", "Stau"), ("Essen gehen", "Restaurant"),
    ("Hund", "Futter"), ("Familie", "Kinder"), ("Post", "Brief"),
    ("Nachbarn", "laut"), ("Kleid", "kaufen"), ("Büro", "Chef"),
    ("Urlaub", "Strand"), ("Kino", "Film"), ("Internet", "Seite"),
    ("Bus", "Abfahrt"), ("Arztpraxis", "Wartezeit"), ("Kuchen", "backen"),
    ("Park", "spazieren"), ("Bäckerei", "Brötchen"), ("Geldautomat", "Karte"),
    ("Buchladen", "Roman"), ("Fernseher", "Programm"), ("Tasche", "vergessen"),
    ("Stadtplan", "finden"), ("Ticket", "bezahlen"), ("Zahnarzt", "Schmerzen"),
    ("Museum", "Öffnungszeiten"), ("Handy", "Akku leer"),
]
A1_BITTEN_PROMPTS = [
    "Radio anmachen", "Fenster zumachen", "Licht anschalten", "Tür aufmachen",
    "Tisch sauber machen", "Hausaufgaben schicken", "Buch bringen",
    "Handy ausmachen", "Stuhl nehmen", "Wasser holen", "Fenster öffnen",
    "Musik leiser machen", "Tafel sauber wischen", "Kaffee kochen",
    "Deutsch üben", "Auto waschen", "Kind abholen", "Tisch decken",
    "Termin machen", "Nachricht schreiben",
]

# ---------- A2 ----------
A2_TEIL1_THEMEN = [
    "Wohnort", "Tagesablauf", "Freizeit", "Sprachen", "Essen & Trinken", "Haustiere",
    "Lieblingsmonat", "Jahreszeit", "Sport", "Kleidung (Sommer)", "Familie", "Beruf",
    "Hobbys", "Feiertage", "Reisen", "Lieblingsessen", "Schule", "Wetter", "Auto oder Fahrrad", "Perfekter Tag"
]
A2_TEIL2_PRESENTATION = [
    "Was machen Sie mit Ihrem Geld?",
    "Was machen Sie am Wochenende?",
    "Wie verbringen Sie Ihren Urlaub?",
    "Wie oft gehen Sie einkaufen und was kaufen Sie?",
    "Was für Musik hören Sie gern?",
    "Wie feiern Sie Ihren Geburtstag?",
    "Welche Verkehrsmittel nutzen Sie?",
    "Wie bleiben Sie gesund?",
    "Was machen Sie gern mit Ihrer Familie?",
    "Wie sieht Ihr Traumhaus aus?",
    "Welche Filme oder Serien mögen Sie?",
    "Wie oft gehen Sie ins Restaurant?",
    "Was ist Ihr Lieblingsfeiertag?",
    "Was machen Sie morgens als Erstes?",
    "Wie lange schlafen Sie normalerweise?",
    "Welche Hobbys hatten Sie als Kind?",
    "Machen Sie lieber Urlaub am Meer oder in den Bergen?",
    "Wie sieht Ihr Lieblingszimmer aus?",
    "Was ist Ihr Lieblingsgeschäft?",
    "Wie sieht ein perfekter Tag für Sie aus?"
]
A2_TEIL3_DISKUSSION = [
    "Zusammen ins Kino gehen", "Ein Café besuchen", "Gemeinsam einkaufen gehen",
    "Ein Picknick im Park organisieren", "Eine Fahrradtour planen",
    "Zusammen in die Stadt gehen", "Einen Ausflug ins Schwimmbad machen",
    "Eine Party organisieren", "Zusammen Abendessen gehen",
    "Gemeinsam einen Freund/eine Freundin besuchen", "Zusammen ins Museum gehen",
    "Einen Spaziergang im Park machen", "Ein Konzert besuchen",
    "Zusammen eine Ausstellung besuchen", "Einen Wochenendausflug planen",
    "Ein Theaterstück ansehen", "Ein neues Restaurant ausprobieren",
    "Einen Kochabend organisieren", "Einen Sportevent besuchen", "Eine Wanderung machen"
]

# ---------- B1 ----------
B1_TEIL1_THEMEN = [
    "Mithilfe beim Sommerfest", "Eine Reise nach Köln planen",
    "Überraschungsparty organisieren", "Kulturelles Ereignis (Konzert, Ausstellung) planen",
    "Museumsbesuch organisieren"
]
B1_TEIL2_THEMEN = [
    "Ausbildung", "Auslandsaufenthalt", "Behinderten-Sport", "Berufstätige Eltern",
    "Berufswahl", "Bio-Essen", "Chatten", "Computer für jeden Kursraum",
    "Das Internet", "Einkaufen in Einkaufszentren", "Einkaufen im Internet", "Extremsport", "Facebook",
    "Fertigessen", "Freiwillige Arbeit", "Freundschaft", "Gebrauchte Kleidung",
    "Getrennter Unterricht für Jungen und Mädchen", "Haushalt", "Haustiere", "Heiraten",
    "Hotel Mama", "Ich bin reich genug", "Informationen im Internet", "Kinder und Fernsehen",
    "Kinder und Handys", "Kinos sterben", "Kreditkarten", "Leben auf dem Land oder in der Stadt",
    "Makeup für Kinder", "Marken-Kleidung", "Mode", "Musikinstrument lernen",
    "Musik im Zeitalter des Internets", "Rauchen", "Reisen", "Schokolade macht glücklich",
    "Sport treiben", "Sprachenlernen", "Sprachenlernen mit dem Internet",
    "Stadtzentrum ohne Autos", "Studenten und Arbeit in den Ferien", "Studium", "Tattoos",
    "Teilzeitarbeit", "Unsere Idole", "Umweltschutz", "Vegetarische Ernährung", "Zeitungslesen"
]
B1_TEIL3_THEMEN = [
    "Fragen stellen zu einer Präsentation", "Positives Feedback geben",
    "Etwas überraschend finden oder planen", "Weitere Details erfragen"
]

# ---------- B2 ----------
B2_TEIL1_THEMEN = [
    "Mediennutzung", "Globalisierung", "Kulturelle Vielfalt", "Umweltschutz", "Technologischer Fortschritt",
    "Arbeitswelt", "Mobilität", "Gesundheitswesen", "Familienmodelle", "Bildungssysteme",
    "Ehrenamtliches Engagement", "Migration", "Integration", "Freizeitgestaltung", "Konsumgesellschaft",
    "Tourismus", "Digitalisierung", "Soziale Netzwerke", "Berufswahl", "Ernährungstrends",
    "Sport und Gesellschaft", "Kunst und Kultur", "Recht und Gerechtigkeit", "Wissenschaft und Forschung",
    "Klimawandel", "Wohnen in der Stadt", "Traditionen und Feste", "Gleichberechtigung"
]
B2_TEIL2_PRESENTATION = [
    "Diskutiere Vor- und Nachteile der Digitalisierung.",
    "Beschreibe eine Erfahrung mit interkultureller Kommunikation.",
    "Erkläre die Bedeutung nachhaltiger Lebensweise.",
    "Erörtere Chancen und Risiken von sozialen Netzwerken.",
    "Präsentiere Argumente für und gegen Fast Fashion.",
    "Stelle dar, wie sich Mobilität auf den Alltag auswirkt.",
    "Diskutiere Auswirkungen des Klimawandels auf die Gesellschaft.",
    "Präsentiere Vorteile von Homeoffice.",
    "Stelle einen aktuellen Ernährungstrend vor.",
    "Erkläre die Rolle ehrenamtlicher Arbeit.",
    "Beschreibe das Bildungssystem in deinem Land.",
    "Präsentiere deine Meinung zum Thema Integration.",
    "Diskutiere, wie Digitalisierung die Arbeitswelt verändert.",
    "Erörtere die Bedeutung von Gleichberechtigung.",
    "Beschreibe Vor- und Nachteile von Tourismus.",
    "Präsentiere einen Trend in Kunst oder Kultur.",
    "Diskutiere, warum Sport wichtig für die Gesellschaft ist.",
    "Beschreibe Traditionen und Feste in deinem Land.",
    "Erkläre die Rolle von Medien in der heutigen Zeit.",
    "Stelle Möglichkeiten vor, umweltfreundlich zu leben.",
    "Diskutiere Herausforderungen im Gesundheitswesen.",
    "Erkläre, wie politische Partizipation gefördert werden kann.",
    "Präsentiere eine berühmte Persönlichkeit aus Wissenschaft oder Forschung.",
    "Diskutiere das Thema Konsumverhalten.",
    "Erörtere das Thema Wohnen in der Stadt.",
    "Beschreibe ein Beispiel für soziale Gerechtigkeit.",
    "Diskutiere aktuelle Entwicklungen in der Kunstwelt.",
    "Beschreibe die Bedeutung von Familie heute."
]
B2_TEIL3_ARGUMENTATION = [
    "Argumentieren Sie für oder gegen das Homeoffice.",
    "Diskutieren Sie die Auswirkungen des Klimawandels auf die Gesellschaft.",
    "Sollten alle Schüler eine Schuluniform tragen?",
    "Ist eine vegetarische Ernährung besser für die Umwelt?",
    "Sind soziale Netzwerke Fluch oder Segen?",
    "Sollte das Autofahren in Großstädten eingeschränkt werden?",
    "Brauchen wir mehr Frauen in Führungspositionen?",
    "Ist das Ehrenamt in Gefahr?",
    "Sollte man schon in der Schule Programmieren lernen?",
    "Sind traditionelle Familienmodelle überholt?",
    "Ist Fast Fashion ein Problem?",
    "Braucht jede Stadt ein Fahrradverleihsystem?",
    "Sollte Plastiktüten verboten werden?",
    "Darf man Kunstwerke digitalisieren und frei zugänglich machen?",
    "Ist Tourismus gut für die Wirtschaft?",
    "Braucht man für Erfolg ein Studium?",
    "Sind Noten in der Schule wichtig?",
    "Sollten Haustiere in Mietwohnungen erlaubt sein?",
    "Sollte der Sonntag ein Ruhetag bleiben?",
    "Ist vegetarisches Leben gesünder?",
    "Sollte das Recht auf Homeoffice gesetzlich garantiert sein?",
    "Sind große Sportereignisse sinnvoll?",
    "Darf Werbung für ungesunde Lebensmittel verboten werden?",
    "Sollte es mehr Bürgerbeteiligung in der Politik geben?",
    "Ist Fernsehen heute noch zeitgemäß?",
    "Sollten Einwegprodukte verboten werden?",
    "Ist das Leben auf dem Land besser als in der Stadt?",
    "Sollte Wissenschaft besser finanziert werden?"
]

# ---------- C1 ----------
C1_TEIL1_THEMEN = [
    "Arbeitswelt der Zukunft", "Künstliche Intelligenz", "Ethik in der Wissenschaft", "Migration",
    "Umwelt- und Klimapolitik", "Globalisierung", "Chancengleichheit", "Digitalisierung und Datenschutz",
    "Gesellschaftlicher Wandel", "Demografischer Wandel", "Gender und Diversität", "Bildungsgerechtigkeit",
    "Fake News und Medienkompetenz", "Internationale Beziehungen", "Nachhaltige Entwicklung",
    "Kulturelle Identität", "Literatur und Gesellschaft", "Innovation und Unternehmertum",
    "Gesundheitssysteme im internationalen Vergleich", "Lebenslanges Lernen", "Wissenschaftskommunikation",
    "Soziale Ungleichheit", "Kritische Medienanalyse", "Populismus und Demokratie",
    "Werte in der modernen Gesellschaft", "Wirtschaftsethik", "Interkulturelle Kommunikation",
    "Forschungsethik", "Urbanisierung"
]
C1_TEIL2_PRESENTATION = [
    "Halten Sie einen Vortrag über Chancen und Risiken von Social Media.",
    "Diskutieren Sie ethische Fragen der Genforschung.",
    "Analysieren Sie die Rolle von Migration in modernen Gesellschaften.",
    "Präsentieren Sie einen aktuellen Trend in der Arbeitswelt.",
    "Erörtern Sie die Herausforderungen der Digitalisierung im Alltag.",
    "Diskutieren Sie die Bedeutung von Nachhaltigkeit in Unternehmen.",
    "Reflektieren Sie die Auswirkungen des demografischen Wandels.",
    "Erklären Sie die Bedeutung von Medienkompetenz.",
    "Präsentieren Sie die Rolle von Kunst und Literatur für die Gesellschaft.",
    "Erörtern Sie das Thema Wertewandel.",
    "Stellen Sie Herausforderungen im Bildungssystem dar.",
    "Diskutieren Sie globale Probleme des Gesundheitssystems.",
    "Präsentieren Sie einen wissenschaftlichen Durchbruch.",
    "Reflektieren Sie über interkulturelle Kommunikation.",
    "Erörtern Sie aktuelle Herausforderungen in der internationalen Politik.",
    "Analysieren Sie die Wirkung von Fake News.",
    "Diskutieren Sie Populismus und Demokratie.",
    "Präsentieren Sie Lösungsansätze für soziale Ungleichheit.",
    "Erörtern Sie Innovation und Unternehmertum.",
    "Diskutieren Sie Chancen und Risiken künstlicher Intelligenz.",
    "Reflektieren Sie den Einfluss von Urbanisierung.",
    "Analysieren Sie den Zusammenhang zwischen Wirtschaft und Ethik.",
    "Diskutieren Sie Forschungsethik am Beispiel eines konkreten Falls.",
    "Erörtern Sie den Wert lebenslangen Lernens.",
    "Präsentieren Sie den Wandel kultureller Identität.",
    "Diskutieren Sie internationale Zusammenarbeit beim Klimaschutz.",
    "Analysieren Sie gesellschaftliche Herausforderungen durch Digitalisierung.",
    "Präsentieren Sie einen aktuellen gesellschaftlichen Diskurs."
]
C1_TEIL3_DISKUSSION = [
    "Reflektieren Sie über die Verantwortung von Wissenschaftlern.",
    "Diskutieren Sie über die Bedeutung lebenslangen Lernens.",
    "Sollte künstliche Intelligenz reguliert werden?",
    "Sind Quotenregelungen sinnvoll?",
    "Welche Bedeutung hat Literatur heute?",
    "Brauchen wir mehr politische Bildung an Schulen?",
    "Wie kann Nachhaltigkeit im Alltag umgesetzt werden?",
    "Welche Rolle spielt Diversität in Unternehmen?",
    "Sollten Fake News strafbar sein?",
    "Sind Grenzen der Meinungsfreiheit notwendig?",
    "Welche Herausforderungen bringt die Globalisierung?",
    "Ist Populismus eine Gefahr für Demokratien?",
    "Wie kann Forschungsethik sichergestellt werden?",
    "Sollten Unternehmen mehr Verantwortung für die Gesellschaft übernehmen?",
    "Wie wichtig ist internationale Zusammenarbeit für den Klimaschutz?",
    "Welche Risiken birgt Digitalisierung für die Privatsphäre?",
    "Wie kann soziale Ungleichheit bekämpft werden?",
    "Sollten ältere Menschen länger arbeiten dürfen?",
    "Welche Rolle spielt kulturelle Identität in der Globalisierung?",
    "Ist Urbanisierung eine Chance oder ein Problem?",
    "Wie kann man Innovation fördern?",
    "Sind traditionelle Medien noch relevant?",
    "Wie können Werte in der Gesellschaft gestärkt werden?",
    "Sollte Wissenschaft für alle zugänglich sein?",
    "Wie kann man gesellschaftlichen Wandel gestalten?",
    "Ist lebenslanges Lernen eine Pflicht?",
    "Wie kann Demokratie im digitalen Zeitalter gesichert werden?",
    "Welche Bedeutung hat Forschung für die Zukunft?"
]

# ------- Prompt bank -------
PROMPT_BANK = {
    "A1": {
        "Teil 1": lambda: "Bitte beantworten Sie: " + ", ".join(A1_TEIL1_KEYWORDS) + ".\n" + random.choice(A1_TEIL1_FOLLOWUP),
        "Teil 2": lambda: f"Stellen Sie eine Frage und antworten Sie zum Thema: {random.choice(A1_VOCAB_TEIL2)[0]} – {random.choice(A1_VOCAB_TEIL2)[1]}.",
        "Teil 3": lambda: f"Formulieren Sie eine höfliche Bitte: {random.choice(A1_BITTEN_PROMPTS)}."
    },
    "A2": {
        "Teil 1": lambda: f"Bitte sprechen Sie über: {random.choice(A2_TEIL1_THEMEN)}.",
        "Teil 2": lambda: random.choice(A2_TEIL2_PRESENTATION),
        "Teil 3": lambda: f"Planen Sie gemeinsam: {random.choice(A2_TEIL3_DISKUSSION)}."
    },
    "B1": {
        "Teil 1": lambda: f"Planen Sie gemeinsam: {random.choice(B1_TEIL1_THEMEN)}.",
        "Teil 2": lambda: f"Präsentieren oder diskutieren Sie das Thema: {random.choice(B1_TEIL2_THEMEN)}.",
        "Teil 3": lambda: f"{random.choice(B1_TEIL3_THEMEN)}."
    },
    "B2": {
        "Teil 1": lambda: f"Diskutieren Sie das Thema: {random.choice(B2_TEIL1_THEMEN)}.",
        "Teil 2": lambda: random.choice(B2_TEIL2_PRESENTATION),
        "Teil 3": lambda: random.choice(B2_TEIL3_ARGUMENTATION)
    },
    "C1": {
        "Teil 1": lambda: f"Analysieren Sie das Thema: {random.choice(C1_TEIL1_THEMEN)}.",
        "Teil 2": lambda: random.choice(C1_TEIL2_PRESENTATION),
        "Teil 3": lambda: random.choice(C1_TEIL3_DISKUSSION)
    }
}

LEVEL_TEIL_OPTIONS = {
    "A1": ["Teil 1", "Teil 2", "Teil 3"],
    "A2": ["Teil 1", "Teil 2", "Teil 3"],
    "B1": ["Teil 1", "Teil 2", "Teil 3"],
    "B2": ["Teil 1", "Teil 2", "Teil 3"],
    "C1": ["Teil 1", "Teil 2", "Teil 3"]
}

# ===============================
#         STAGE 2: Helper Functions and UI Setup
# ===============================

def load_codes():
    if os.path.exists(CODES_FILE):
        df = pd.read_csv(CODES_FILE)
        if "code" not in df.columns:
            df = pd.DataFrame(columns=["code"])
        df["code"] = df["code"].astype(str).str.strip().str.lower()
    else:
        df = pd.DataFrame(columns=["code"])
    return df

def safe_rerun():
    try:
        st.experimental_rerun()
    except Exception:
        pass

def setup_ui_and_state():
    st.set_page_config(
        page_title="Falowen – Your AI Conversation Partner",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    st.markdown(
        """
        <div style='display:flex;align-items:center;gap:18px;margin-bottom:22px;'>
            <img src='https://cdn-icons-png.flaticon.com/512/6815/6815043.png' width='54' style='border-radius:50%;border:2.5px solid #51a8d2;box-shadow:0 2px 8px #cbe7fb;'/>
            <div>
                <span style='font-size:2.1rem;font-weight:bold;color:#17617a;letter-spacing:2px;'>Falowen</span><br>
                <span style='font-size:1.08rem;color:#268049;'>Your personal German speaking coach (Sir Felix)</span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )
    for var, default in [
        ("step", 1), ("student_code", ""), ("user_level", ""), ("daily_usage", {}),
        ("messages", []), ("corrections", []), ("turn_count", 0)
    ]:
        if var not in st.session_state:
            st.session_state[var] = default
# ===============================
#         STAGE 3: Student Login, Level, Mode Selection
# ===============================

def stage_3_login_and_mode():
    # ------ Step 1: Student Login + Level ------
    if st.session_state["step"] == 1:
        st.title("Student Login")
        code = st.text_input("🔑 Enter your student code to begin:")
        level = st.selectbox("Select your level:", ["A1", "A2", "B1", "B2", "C1"])
        if st.button("Next ➡️", key="stage1_next"):
            code_clean = code.strip().lower()
            df_codes = load_codes()
            if code_clean in df_codes["code"].dropna().tolist():
                st.session_state["student_code"] = code_clean
                st.session_state["user_level"] = level
                st.session_state["step"] = 2
            else:
                st.error("This code is not recognized. Please check with your tutor.")

    # ------ Step 2: Welcome ------
    elif st.session_state["step"] == 2:
        st.success(f"**Welcome! Level: {st.session_state['user_level']}**")
        st.markdown(
            "<h2 style='font-weight:bold;margin-bottom:0.5em'>🧑‍🏫 Welcome to Falowen – Your German Coach, Sir Felix!</h2>",
            unsafe_allow_html=True,
        )
        st.info(
            """
            🎤 **This is your German speaking and exam practice app.**
            Every session, imagine you are in the exam hall—get real questions, feedback, and tips!
            **Select your practice mode on the next page.**
            """, icon="💡"
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", key="stage2_back"):
                st.session_state["step"] = 1
        with col2:
            if st.button("Next ➡️", key="stage2_next"):
                st.session_state["step"] = 3

    # ------ Step 3: Mode Selection ------
    elif st.session_state["step"] == 3:
        st.header("Wie möchtest du üben? (How would you like to practice?)")
        user_level = st.session_state.get("user_level", "A1")
        # Only Exam Mode for A1, full options for higher
        if user_level == "A1":
            mode_options = ["Geführte Prüfungssimulation (Exam Mode)"]
        else:
            mode_options = [
                "Geführte Prüfungssimulation (Exam Mode)",
                "Eigenes Thema/Frage (Custom Chat)",
                "Präsentationstraining (Presentation Practice)"
            ]
        mode = st.radio(
            "Choose your practice mode:",
            mode_options,
            index=0,
            key="mode_selector"
        )
        st.session_state["selected_mode"] = mode

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", key="stage3_back"):
                st.session_state["step"] = 2
        with col2:
            if st.button("Next ➡️", key="stage3_next"):
                st.session_state["messages"] = []
                st.session_state["turn_count"] = 0
                st.session_state["corrections"] = []
                if mode == "Geführte Prüfungssimulation (Exam Mode)":
                    st.session_state["step"] = 4
                elif mode == "Eigenes Thema/Frage (Custom Chat)":
                    st.session_state["step"] = 5
                elif mode == "Präsentationstraining (Presentation Practice)":
                    st.session_state["step"] = 7
# ===============================
#         STAGE 4: Exam Part Selection & AI Prompt
# ===============================

def stage_4_exam_part():
    if st.session_state["step"] != 4:
        return

    user_level = st.session_state.get("user_level", "A1")
    st.header("Prüfungsteil wählen / Choose exam part")
    teil = st.selectbox(
        "Welchen Teil möchtest du üben?",
        LEVEL_TEIL_OPTIONS[user_level],
        key="exam_teil_select"
    )
    st.session_state["selected_teil"] = teil

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", key="stage4_back"):
            st.session_state["step"] = 3
    with col2:
        if st.button("Start Chat ➡️", key="stage4_start"):
            # Let AI start with the right prompt!
            prompt = PROMPT_BANK[user_level][teil]()
            st.session_state["messages"] = [{"role": "assistant", "content": prompt}]
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
            st.session_state["step"] = 5

def stage_5_chat():
    if st.session_state.get("step") != 5:
        return

    # Current level and exam part
    user_level = st.session_state.get("user_level", "A1")
    teil = st.session_state.get("selected_teil", "Teil 1")

    # Show instructions and allow switching part
    st.markdown(f"**Current Level:** {user_level}  |  **Current Part:** {teil}")
    new_teil = st.selectbox(
        "Change exam part (Teil):",
        LEVEL_TEIL_OPTIONS[user_level],
        index=LEVEL_TEIL_OPTIONS[user_level].index(teil)
    )
    if new_teil != teil:
        st.session_state["selected_teil"] = new_teil
        # Reset for new part
        prompt = PROMPT_BANK[user_level][new_teil]()
        st.session_state["messages"] = [{"role": "assistant", "content": prompt}]
        st.session_state["turn_count"] = 0
        return

    # Usage tracking
    today_str = str(date.today())
    student_code = st.session_state["student_code"]
    usage_key = f"{student_code}_{today_str}"
    st.session_state.setdefault("daily_usage", {})
    st.session_state["daily_usage"].setdefault(usage_key, 0)

    # Initialize first AI prompt if needed
    if not st.session_state.get("messages"):
        prompt = PROMPT_BANK[user_level][teil]()
        st.session_state["messages"] = [{"role": "assistant", "content": prompt}]

    # Display usage info
    st.markdown(
        f"<div style='margin-bottom:0.5em'>"
        f"<span style='background:#bee3f8;border-radius:0.5em;padding:0.3em 0.8em;'>"
        f"Student code: <b>{student_code}</b>  |  Today's practice: {st.session_state['daily_usage'][usage_key]}/{DAILY_LIMIT}"
        f"</span></div>", unsafe_allow_html=True
    )

    # Render chat history
    for msg in st.session_state["messages"]:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                st.markdown(f"**Sir Felix:** {msg['content']}")
        else:
            with st.chat_message("user", avatar="🧑"):
                st.markdown(f"**Student:** {msg['content']}")

    # English instruction
    st.markdown("Please answer the question above in German. You will receive corrections and tips in English.")

    # User input via chat_input
    user_input = st.chat_input("Type your reply here...")
    if user_input:
        # Append user message
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.session_state["turn_count"] += 1
        st.session_state["daily_usage"][usage_key] += 1

        # AI reply
        with st.spinner("Sir Felix is typing..."):
            system_prompt = (
                f"You are Sir Felix, a German teacher and exam coach. "
                f"The student is level {user_level}, part {teil}. "
                "Adapt your reply to the level. Always correct and explain in English."
            )
            conversation = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            try:
                client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
                resp = client.chat.completions.create(
                    model="gpt-4o", messages=conversation
                )
                ai_reply = resp.choices[0].message.content
            except Exception as e:
                ai_reply = "Sorry, there was a problem generating a response."
                st.error(str(e))
        # Append AI response
        st.session_state["messages"].append({"role": "assistant", "content": ai_reply})

    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Part Selection"):
            st.session_state["step"] = 4
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            return
    with col2:
        if st.session_state["turn_count"] >= MAX_TURNS and st.button("Finish Session"):
            st.session_state["step"] = 6
            return


# ===============================
#         STAGE 6: Session Summary & Restart
# ===============================

def stage_6_summary():
    if st.session_state.get("step") != 6:
        return
    st.title("🎉 Congratulations!")
    st.markdown(
        "<h3 style='color:#33691e;'>Session completed!</h3>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"**You completed {st.session_state['turn_count']} turns.**<br>"
        "Start again or choose another mode?",
        unsafe_allow_html=True
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔁 Start New Session", key="stage6_restart"):
            st.session_state["step"] = 1
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []
            st.session_state["custom_topic"] = ""
    with col2:
        if st.button("⬅️ Back to Mode Selection", key="stage6_back"):
            st.session_state["step"] = 3
            st.session_state["messages"] = []
            st.session_state["turn_count"] = 0
            st.session_state["corrections"] = []

# ===============================
#         STAGE 7: Custom Chat Mode
# ===============================

def stage_7_custom_chat():
    if st.session_state.get("step") != 5:
        return

    user_level = st.session_state.get("user_level", "A2")
    today_str = str(date.today())
    student_code = st.session_state["student_code"]
    usage_key = f"{student_code}_{today_str}"
    st.session_state.setdefault("daily_usage", {})
    st.session_state["daily_usage"].setdefault(usage_key, 0)

    st.markdown(
        f"<div style='margin-bottom:0.5em'>"
        f"<span style='background:#bee3f8;border-radius:0.5em;padding:0.3em 0.8em;'>"
        f"Student code: <b>{student_code}</b> &nbsp; | &nbsp; Today's practice: {st.session_state['daily_usage'][usage_key]}/{DAILY_LIMIT}"
        f"</span></div>",
        unsafe_allow_html=True
    )

    # Start with a greeting if no chat yet
    if not st.session_state["messages"]:
        st.session_state["messages"] = [{
            "role": "assistant",
            "content": f"Hallo! 👋 Was möchtest du heute üben? Schreib ein Thema oder stelle eine Frage ({user_level}-Niveau)."
        }]

    def render_chat():
        for msg in st.session_state["messages"]:
            if msg["role"] == "assistant":
                with st.chat_message("assistant", avatar="🧑‍🏫"):
                    st.markdown(f"<b>Sir Felix</b><br>{msg['content']}", unsafe_allow_html=True)
            else:
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(f"<b>Student</b><br>{msg['content']}", unsafe_allow_html=True)

    render_chat()

    with st.form("custom_chat_form", clear_on_submit=True):
        user_input = st.text_area("Deine Antwort oder Frage...", height=70)
        submitted = st.form_submit_button("Senden")

    if submitted and user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.session_state["turn_count"] += 1
        st.session_state["daily_usage"][usage_key] += 1

        with st.spinner("Sir Felix is typing..."):
            system_prompt = (
                f"You are Sir Felix, a German teacher. "
                f"The student's level is {user_level}. "
                "This is custom conversation/practice mode. "
                "Give helpful, adaptive answers and always explain corrections in ENGLISH. "
                "Encourage more speaking and keep questions interesting for the student's level."
            )
            conversation = [
                {"role": "system", "content": system_prompt},
                st.session_state["messages"][-1]
            ]
            try:
                client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=conversation
                )
                ai_reply = resp.choices[0].message.content
            except Exception as e:
                ai_reply = "Sorry, there was a problem generating a response."
                st.error(str(e))
            st.session_state["messages"].append({"role": "assistant", "content": ai_reply})
            st.experimental_rerun()

    if st.button("⬅️ Zurück zum Menü", key="stage7custom_back"):
        st.session_state["step"] = 3
        st.session_state["messages"] = []
        st.session_state["turn_count"] = 0
        st.session_state["corrections"] = []
        st.experimental_rerun()

# ===============================
#         STAGE 8: Presentation Practice Mode
# ===============================

def stage_8_presentation():
    if st.session_state.get("step") != 7:
        return

    user_level = st.session_state.get("user_level", "B1")
    st.header("Präsentationstraining / Presentation Practice")

    if "presentation_topic" not in st.session_state or not st.session_state["presentation_topic"]:
        topic = st.text_input("Gib dein Präsentationsthema ein oder wähle eines (optional):")
        if st.button("Start Practice"):
            st.session_state["presentation_topic"] = topic if topic else f"Mein Alltag"
            # AI starts
            st.session_state["messages"] = [{
                "role": "assistant",
                "content": f"Bitte beginne deine Präsentation zum Thema: {st.session_state['presentation_topic']}"
            }]
            st.session_state["turn_count"] = 0
            st.experimental_rerun()
        if st.button("⬅️ Zurück zum Menü", key="stage8pres_back"):
            st.session_state["step"] = 3
            st.session_state["presentation_topic"] = ""
            st.session_state["messages"] = []
            st.experimental_rerun()
        return

    # Chat Loop
    def render_chat():
        for msg in st.session_state["messages"]:
            if msg["role"] == "assistant":
                with st.chat_message("assistant", avatar="🧑‍🏫"):
                    st.markdown(f"<b>Sir Felix</b><br>{msg['content']}", unsafe_allow_html=True)
            else:
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(f"<b>Student</b><br>{msg['content']}", unsafe_allow_html=True)

    render_chat()

    with st.form("presentation_form", clear_on_submit=True):
        user_input = st.text_area("Dein Präsentationsbeitrag...", height=70)
        submitted = st.form_submit_button("Senden")

    if submitted and user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.session_state["turn_count"] += 1

        with st.spinner("Sir Felix is typing..."):
            system_prompt = (
                f"You are Sir Felix, a German teacher. "
                f"The student's level is {user_level}. "
                "This is presentation mode. "
                "Give feedback, corrections (in ENGLISH), and encourage longer answers."
            )
            conversation = [
                {"role": "system", "content": system_prompt},
                st.session_state["messages"][-1]
            ]
            try:
                client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=conversation
                )
                ai_reply = resp.choices[0].message.content
            except Exception as e:
                ai_reply = "Sorry, there was a problem generating a response."
                st.error(str(e))
            st.session_state["messages"].append({"role": "assistant", "content": ai_reply})
            st.experimental_rerun()

    st.markdown(f"**Takes completed:** {st.session_state['turn_count']}/12")
    if st.button("⬅️ Zurück zum Menü", key="stage8pres_back2"):
        st.session_state["step"] = 3
        st.session_state["presentation_topic"] = ""
        st.session_state["messages"] = []
        st.experimental_rerun()

# ===============================
#         MAIN APP RUNNER
# ===============================

setup_ui_and_state()
stage_3_login_and_mode()
stage_4_exam_part()
if st.session_state.get("step") == 5 and st.session_state.get("selected_mode") == "Eigenes Thema/Frage (Custom Chat)":
    stage_7_custom_chat()
elif st.session_state.get("step") == 7:
    stage_8_presentation()
else:
    stage_5_chat()
stage_6_summary()
