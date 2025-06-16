import streamlit as st
import random
import re
import tempfile
from datetime import date
from openai import OpenAI

# ------------------ USER SESSION STATE INIT ----------------------
st.set_page_config(page_title="Deutsch Gamified Chat", layout="centered")
st.session_state.setdefault("student_code", "test123")
st.session_state.setdefault("student_name", "Felix")
st.session_state.setdefault("step", 5)
st.session_state.setdefault("a2_intro_shown", False)
st.session_state.setdefault("a2_correct_count", 0)
st.session_state.setdefault("a2_streak", 0)
st.session_state.setdefault("daily_usage", {})
st.session_state.setdefault("messages", [])
st.session_state.setdefault("turn_count", 0)
st.session_state.setdefault("custom_chat_level", "A2")
st.session_state.setdefault("selected_mode", "Eigenes Thema/Frage (Custom Topic Chat)")

# -------------- GAMIFICATION HELPERS --------------------------
def get_avatar_stage(correct_count):
    if correct_count >= 10:
        return "🦸‍♂️"
    elif correct_count >= 5:
        return "🙂"
    elif correct_count >= 1:
        return "👶"
    else:
        return "❓"

def get_avatar_label(correct_count):
    if correct_count >= 10:
        return "Deutsch-Held"
    elif correct_count >= 5:
        return "Fortgeschritten"
    elif correct_count >= 1:
        return "Anfänger"
    else:
        return "Los geht's!"

def get_badge(count):
    if count >= 10:
        return "🥇 Deutsch-Meister!"
    elif count >= 5:
        return "🏅 Toller Fortschritt!"
    elif count >= 1:
        return "🎈 Du bist gestartet!"
    else:
        return ""

def update_streak(last_correct):
    if last_correct:
        st.session_state["a2_streak"] += 1
    else:
        st.session_state["a2_streak"] = 0

# -------------- ADVANCED FEEDBACK FORMATTER -----------------
def show_formatted_ai_reply(content):
    encouragements = [
        "🌟 Sehr gut!", "👍 Klasse gemacht!", "✅ Super!", "💡 Gut geantwortet!", "🎉 Weiter so!"
    ]
    trophy = "🏆"
    lines = content.split("\n")
    encouragement_used = False

    for line in lines:
        if re.search(r"(Du hast jetzt \d+ richtige Antworten!|Great! No correction needed!|Your German is correct!|Das war richtig)", line):
            st.markdown(f"<span style='color:#198754;font-weight:bold;font-size:1.15em'>"
                        f"{random.choice(encouragements)} {trophy} {line}</span>", unsafe_allow_html=True)
            encouragement_used = True
        elif "Correction:" in line:
            correction = line.split("Correction:", 1)[1].strip()
            arrow_match = re.match(r"(.*)→(.*)", correction)
            if arrow_match:
                before = arrow_match.group(1).strip()
                after = arrow_match.group(2).strip()
                st.markdown(
                    f"<span style='color:#e74c3c;font-weight:bold;'>"
                    f"✏️ Correction: <s>{before}</s> ➡️ <b>{after}</b>"
                    f"</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<span style='color:#e74c3c;font-weight:bold;'>✏️ Correction: {correction}</span>",
                    unsafe_allow_html=True
                )
        elif "Grammar Tip:" in line:
            tip = line.split("Grammar Tip:", 1)[1].strip()
            st.markdown(
                f"<span style='color:#2471a3;font-weight:bold;'>📚 Grammar Tip: {tip}</span>",
                unsafe_allow_html=True
            )
        elif "Reflexion:" in line:
            reflection = line.split("Reflexion:", 1)[1].strip()
            st.markdown(
                f"<span style='color:#f39c12;font-weight:bold;'>🤔 Reflexion: {reflection}</span>",
                unsafe_allow_html=True
            )
        elif re.search(r"(Nächste Frage:|Next question:|Frage:)", line):
            st.markdown(
                f"<span style='color:#33691e;font-weight:bold;'>➡️ {line}</span>",
                unsafe_allow_html=True
            )
        else:
            if not encouragement_used and (re.match(r"(Super|Klasse|Gut|Toll|Sehr gut)", line)):
                st.markdown(
                    f"<span style='color:#228be6;font-weight:bold;'>{random.choice(encouragements)}</span>",
                    unsafe_allow_html=True
                )
                encouragement_used = True
            st.markdown(line)

# ----------- AI SYSTEM PROMPT BUILDER FOR A2 -----------------
def build_a2_system_prompt(topic, is_intro, student_name, turn_count, correct_count):
    if is_intro:
        return (
            f"Hallo {student_name}! Heute sprechen wir über das Thema: {topic}.\n"
            "1. Give a few useful keywords or phrases for the topic (in German).\n"
            "2. Give 1-2 short, easy example sentences about the topic.\n"
            "3. In one English sentence, say what can be said in a simple conversation about this topic.\n"
            "4. Then ask ONE easy, factual question about the student's experience with the topic (in German).\n"
            "Always use the student's name for encouragement, and begin with a positive phrase (e.g. Sehr gut, NAME!)."
            "\nAfter this intro, do not repeat the keywords or examples again."
            "\nFor all following turns, just respond to the student's last answer, correct (bold any changed words), give a simple grammar tip (in English, if needed), and ask ONE factual question. Encourage the student by name after each answer (e.g. Klasse, Felix!). After each correct answer, say: 'Du hast jetzt X richtige Antworten!'."
            "\nEvery 5 turns, add: Reflexion: Welche Frage war für dich am einfachsten? Gab es etwas Schwieriges?"
        )
    else:
        reflection = ""
        if turn_count % 5 == 0 and turn_count != 0:
            reflection = (
                f"\nReflexion: Welche Frage war für dich am einfachsten? Gab es etwas Schwieriges?"
            )
        return (
            f"Du bist Herr Felix, ein unterstützender A2-Deutschkurslehrer. Das Thema ist: {topic}.\n"
            "Antworte nicht mehr mit Keywords oder Beispielen!\n"
            f"- Antworte immer zuerst freundlich mit dem Namen des Schülers ({student_name}) und einem positiven Satz (z.B. Super, Felix!).\n"
            "- Correction: (wenn nötig, markiere das geänderte Wort in **fett**)\n"
            "- Grammar Tip: (auf Englisch, falls nötig, sonst: Your German is correct!)\n"
            f"- Sage nach jeder richtigen Antwort: 'Du hast jetzt {correct_count} richtige Antworten!'\n"
            "- Stelle EINE weitere einfache, faktische Folgefrage zum Thema (auf Deutsch, nur eine Frage pro Runde).\n"
            f"{reflection}"
        )

# -------------------- AVATAR & GAMIFICATION UI -------------------
correct = st.session_state.get("a2_correct_count", 0)
avatar = get_avatar_stage(correct)
avatar_label = get_avatar_label(correct)
total_questions = 10

col1, col2 = st.columns([1, 3])
with col1:
    st.markdown(
        f"<div style='font-size:3em;text-align:center;'>{avatar}</div>"
        f"<div style='text-align:center;font-size:1.1em;'>{avatar_label}</div>",
        unsafe_allow_html=True
    )
with col2:
    st.progress(correct / total_questions, text=f"{correct}/{total_questions} richtige Antworten")

badge = get_badge(correct)
if badge:
    st.markdown(f"<div style='font-size:1.3em;font-weight:bold;color:#b38807'>{badge}</div>", unsafe_allow_html=True)
if correct in [5, 10]:
    st.balloons()
    st.markdown(
        f"<span style='font-size:1.2em;color:#db7500;'>🎉 Dein Avatar ist aufgestiegen: {avatar}!</span>",
        unsafe_allow_html=True
    )

if st.session_state["a2_streak"] > 1:
    st.markdown(f"<span style='font-size:1.15em;color:#00a86b;'>🔥 Streak: {st.session_state['a2_streak']} richtige Antworten hintereinander!</span>", unsafe_allow_html=True)

# -------------------- MAIN CHAT LOGIC -------------------------
if st.session_state["step"] == 5:
    today_str = str(date.today())
    student_code = st.session_state["student_code"]
    usage_key = f"{student_code}_{today_str}"
    st.session_state["daily_usage"].setdefault(usage_key, 0)

    st.info(
        f"Student code: `{student_code}` | "
        f"Today's practice: {st.session_state['daily_usage'][usage_key]}/25 | "
        f"Korrekte Antworten: {st.session_state['a2_correct_count']}"
    )

    # -- Input methods --
    typed = st.chat_input("💬 Was ist dein Thema oder deine Antwort? (z.B. Wochenende)", key="stage5_typed_input")
    user_input = typed if typed else None

    session_ended = st.session_state["turn_count"] >= total_questions
    used_today = st.session_state["daily_usage"][usage_key]

    if user_input and not session_ended:
        if used_today >= total_questions:
            st.warning(
                "Du hast heute dein Übungslimit erreicht. Komm morgen wieder oder kontaktiere deinen Lehrer!"
            )
        else:
            st.session_state["messages"].append({"role": "user", "content": user_input})
            st.session_state["turn_count"] += 1
            st.session_state["daily_usage"][usage_key] += 1

            with st.chat_message("assistant", avatar="🧑‍🏫"):
                st.markdown("<i>Herr Felix is typing ...</i>", unsafe_allow_html=True)
            # --- AI PROMPT LOGIC ---
            lvl = st.session_state.get("custom_chat_level", "A2")
            topic_msg = ""
            for msg in st.session_state["messages"]:
                if msg["role"] == "user":
                    topic_msg = msg["content"].strip()
                    break
            if lvl == "A2":
                is_intro = not st.session_state["a2_intro_shown"]
                ai_system_prompt = build_a2_system_prompt(
                    topic_msg,
                    is_intro,
                    st.session_state["student_name"],
                    st.session_state["turn_count"],
                    st.session_state["a2_correct_count"]
                )
                if is_intro:
                    st.session_state["a2_intro_shown"] = True

            # ---- REAL OPENAI CALL ----
            client = OpenAI(api_key=st.secrets["general"]["OPENAI_API_KEY"])
            try:
                conversation = [
                    {"role": "system", "content": ai_system_prompt},
                    st.session_state["messages"][-1]
                ]
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=conversation
                )
                ai_reply = resp.choices[0].message.content
            except Exception as e:
                ai_reply = "Sorry, there was a problem generating a response."
                st.error(str(e))

            last_correct = (
                "Great! No correction needed!" in ai_reply or
                "Your German is correct" in ai_reply or
                "Das war richtig" in ai_reply
            )
            update_streak(last_correct)
            if last_correct:
                st.session_state["a2_correct_count"] += 1

            st.session_state["messages"].append(
                {"role": "assistant", "content": ai_reply}
            )

    # --- Chat display loop ---
    for msg in st.session_state["messages"]:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🧑‍🏫"):
                st.markdown(
                    f"<span style='color:#33691e;font-weight:bold'>🧑‍🏫 Herr Felix:</span>",
                    unsafe_allow_html=True
                )
                show_formatted_ai_reply(msg["content"])
        else:
            with st.chat_message("user"):
                st.markdown(f"🗣️ {msg['content']}")

    # --- Navigation buttons ---
    def reset_to_prev():
        st.session_state.update({
            "step": 5,
            "messages": [],
            "turn_count": 0,
            "a2_intro_shown": False,
            "a2_correct_count": 0,
            "a2_streak": 0
        })

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Neustarten", key="stage5_back"):
            reset_to_prev()
    with col2:
        if session_ended and st.button("✅ Fertig! (Zusammenfassung)", key="stage5_summary"):
            st.success("Du hast das heutige Übungsziel erreicht! Super gemacht! 🎉")
