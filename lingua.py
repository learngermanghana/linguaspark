import streamlit as st
from openai import OpenAI
import io
import re
import requests
from datetime import datetime
import pandas as pd
import uuid

# --- Secure API key ---
api_key = st.secrets.get("general", {}).get("OPENAI_API_KEY")
if not api_key:
    st.error("❌ API key not found. Add it to .streamlit/secrets.toml under [general]")
    st.stop()
client = OpenAI(api_key=api_key)

# --- Page setup ---
st.set_page_config(
    page_title="Falowen – Your AI Conversation Partner",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit logo, hamburger, and footer
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .st-emotion-cache-zq5wmm {display:none;}
    </style>
""", unsafe_allow_html=True)

# --- CSV helpers ---
students_file = "students.csv"
trials_file = "trials.csv"
usage_file = "usage.csv"

def save_paid_df(df):
    df.to_csv(students_file, index=False)

def save_trials_df(df):
    df.to_csv(trials_file, index=False)

# --- Load CSV files with fallback ---
try:
    paid_df = pd.read_csv(students_file)
except FileNotFoundError:
    paid_df = pd.DataFrame(columns=["code", "expiry"])

try:
    trials_df = pd.read_csv(trials_file)
except FileNotFoundError:
    trials_df = pd.DataFrame(columns=["email", "trial_code", "created"])

try:
    usage_df = pd.read_csv(usage_file, parse_dates=["date"])
except FileNotFoundError:
    usage_df = pd.DataFrame(columns=["user_key", "date", "trial_count", "daily_count"])

# --- Paystack Integration ---

def create_paystack_payment(email, amount, currency="GHS"):
    """
    Initialize a Paystack payment. Amount is in Ghana cedis (GHS).
    The returned link lets user pay with card or mobile money.
    """
    PAYSTACK_SECRET_KEY = st.secrets.get("general", {}).get("PAYSTACK_SECRET_KEY")
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    # Paystack expects amount in pesewas (i.e., GHS 20 = 2000)
    data = {
        "email": email,
        "amount": int(amount * 100),
        "currency": currency,
        "channels": ["card", "mobile_money"],
        "callback_url": "https://your-app-url.com/payment-success"  # Replace with your real site URL
    }
    r = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers)
    if r.ok:
        return r.json()["data"]["authorization_url"]
    else:
        st.error("Paystack payment link creation failed: " + r.text)
        return None

def verify_paystack_payment(reference):
    """
    Verify payment after user completes Paystack payment.
    Get the `reference` from Paystack (from callback URL or user).
    Returns True if payment was successful.
    """
    PAYSTACK_SECRET_KEY = st.secrets.get("general", {}).get("PAYSTACK_SECRET_KEY")
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    resp = requests.get(url, headers=headers)
    if resp.ok:
        status = resp.json()["data"]["status"]
        return status == "success"
    else:
        return False

# --- Navigation ---
mode = st.sidebar.radio("Navigate", ["Practice", "Teacher Dashboard", "Pay & Subscribe"])

# --- Teacher Dashboard (Add, Edit, Delete Codes) ---
if mode == "Teacher Dashboard":
    pwd = st.text_input("🔐 Teacher Password:", type="password")
    if pwd == st.secrets.get("TEACHER_PASSWORD", "admin123"):
        st.subheader("🧑‍🏫 Manage Paid Codes")
        
        # Add New Paid Code
        with st.form("add_paid_code_form"):
            col1, col2 = st.columns([2, 2])
            new_code = col1.text_input("New Paid Code")
            new_expiry = col2.date_input("Expiry Date", value=datetime.now())
            add_btn = st.form_submit_button("➕ Add Paid Code")
            if add_btn and new_code and new_code not in paid_df["code"].tolist():
                paid_df.loc[len(paid_df)] = [new_code, new_expiry]
                save_paid_df(paid_df)
                st.success(f"Added paid code {new_code}")
                st.experimental_rerun()
        
        # Edit/Delete Paid Codes
        for idx, row in paid_df.iterrows():
            col1, col2, col3, col4 = st.columns([3, 3, 1, 1])
            col1.text_input(f"Code_{idx}", value=row['code'], key=f"pc_code_{idx}", disabled=True)
            new_expiry = col2.date_input(f"Expiry_{idx}", value=pd.to_datetime(row['expiry']), key=f"pc_exp_{idx}")
            edit_btn = col3.button("💾", key=f"pc_save_{idx}")
            del_btn = col4.button("🗑️", key=f"pc_del_{idx}")
            if edit_btn:
                paid_df.at[idx, "expiry"] = new_expiry
                save_paid_df(paid_df)
                st.success(f"Updated expiry for {row['code']}")
                st.experimental_rerun()
            if del_btn:
                paid_df = paid_df.drop(idx).reset_index(drop=True)
                save_paid_df(paid_df)
                st.success(f"Deleted code {row['code']}")
                st.experimental_rerun()
        
        st.markdown("---")
        st.subheader("🎫 Manage Trial Codes")
        
        # Add New Trial Code
        with st.form("add_trial_code_form"):
            col1, col2 = st.columns([3, 2])
            new_email = col1.text_input("New Trial Email")
            add_trial_btn = col2.form_submit_button("Issue Trial Code")
            if add_trial_btn and new_email:
                code_val = uuid.uuid4().hex[:8]
                trials_df.loc[len(trials_df)] = [new_email, code_val, datetime.now()]
                save_trials_df(trials_df)
                st.success(f"Issued trial code {code_val}")
                st.experimental_rerun()

        # Edit/Delete Trial Codes
        for idx, row in trials_df.iterrows():
            col1, col2, col3, col4 = st.columns([4, 3, 1, 1])
            new_email = col1.text_input(f"TrialEmail_{idx}", value=row['email'], key=f"tc_email_{idx}")
            col2.text_input(f"TrialCode_{idx}", value=row['trial_code'], key=f"tc_code_{idx}", disabled=True)
            edit_btn = col3.button("💾", key=f"tc_save_{idx}")
            del_btn = col4.button("🗑️", key=f"tc_del_{idx}")
            if edit_btn:
                trials_df.at[idx, "email"] = new_email
                save_trials_df(trials_df)
                st.success(f"Updated trial email for {row['trial_code']}")
                st.experimental_rerun()
            if del_btn:
                trials_df = trials_df.drop(idx).reset_index(drop=True)
                save_trials_df(trials_df)
                st.success(f"Deleted trial code {row['trial_code']}")
                st.experimental_rerun()
    else:
        st.info("Enter correct teacher password.")
    st.stop()

# --- Pay & Subscribe (with Paystack) ---
if mode == "Pay & Subscribe":
    st.subheader("💳 Subscribe for Full Access (Card & Mobile Money)")
    st.info(
        "Payments are handled securely by Paystack. "
        "You can use VISA/Mastercard or Mobile Money (MTN, Vodafone, AirtelTigo)."
    )
    st.markdown("""
    **Test Mode:**  
    - Use test email and any of Paystack's [test cards](https://paystack.com/docs/payments/test/#test-cards) or [test mobile money numbers](https://paystack.com/docs/payments/test/#mobile-money).  
    - Real mode: switch your API key to `sk_live_...` and update callback URL.  
    - After payment, contact us with your transaction reference or email for quick activation.
    """)
    email = st.text_input("Your Email for Payment")
    amount = st.number_input("Amount (GHS)", min_value=1, value=50)
    if st.button("Pay with Paystack"):
        pay_url = create_paystack_payment(email, amount)
        if pay_url:
            st.markdown(f"[👉 Click here to pay securely with Paystack]({pay_url})", unsafe_allow_html=True)
            st.success("After payment, note your reference or email for activation.")

    st.markdown("---")
    st.markdown("#### Verify Your Payment (optional, for admins/users)")
    reference = st.text_input("Enter Paystack Payment Reference")
    if st.button("Verify Payment"):
        if reference:
            if verify_paystack_payment(reference):
                st.success("✅ Payment successful! You can now be granted access.")
            else:
                st.error("❌ Payment not found or not successful.")

# --- Practice Mode ---
if mode == "Practice":
    paid_codes = paid_df["code"].tolist()
    access_code = st.text_input("Enter your paid or trial code:")
    if not access_code:
        st.info("Please enter your code. If you don't have one, request a trial code below.")
        email_req = st.text_input("Email for trial code")
        if email_req and st.button("Request Trial Code"):
            existing = trials_df[trials_df["email"] == email_req]
            if existing.empty:
                new_code = uuid.uuid4().hex[:8]
                trials_df.loc[len(trials_df)] = [email_req, new_code, datetime.now()]
                save_trials_df(trials_df)
                st.success(f"Your trial code: {new_code}")
            else:
                st.success(f"Your existing trial code: {existing['trial_code'].iloc[0]}")
        st.stop()

    if access_code in paid_codes:
        trial_mode = False
    elif access_code in trials_df["trial_code"].tolist():
        trial_mode = True
    else:
        st.error("Invalid code.")
        st.stop()

    # --- Usage tracking ---
    today = datetime.now().date()
    mask = (usage_df["user_key"] == access_code) & (usage_df["date"] == pd.Timestamp(today))
    if not mask.any():
        usage_df.loc[len(usage_df)] = [access_code, pd.Timestamp(today), 0, 0]
        mask = (usage_df["user_key"] == access_code) & (usage_df["date"] == pd.Timestamp(today))
    row_idx = usage_df[mask].index[0]
    trial_count = int(usage_df.at[row_idx, "trial_count"])
    daily_count = int(usage_df.at[row_idx, "daily_count"])
    if trial_mode and trial_count >= 5:
        st.error("🔒 Your 5-message trial has ended.")
        st.stop()
    if not trial_mode and daily_count >= 30:
        st.warning("🚫 Daily limit reached.")
        st.stop()

    # Increment usage
    def increment_usage(is_trial: bool):
        if is_trial:
            usage_df.at[row_idx, "trial_count"] += 1
        else:
            usage_df.at[row_idx, "daily_count"] += 1
        usage_df.to_csv(usage_file, index=False)

    # --- Settings ---
    with st.expander("⚙️ Settings", expanded=True):
        language = st.selectbox("Language", ["German", "French", "English"])
        level = st.selectbox("Level", ["A1", "A2", "B1", "B2", "C1"])

    # Determine display name
    if trial_mode:
        row = trials_df[trials_df["trial_code"] == access_code]
        display = row["email"].values[0].split("@")[0].replace('.', ' ').title() if not row.empty else "Learner"
    else:
        display = "Student"

    # --- Mobile-Optimized Welcome Banner (custom font, dark text, modern style) ---
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@700;900&display=swap');
        .custom-banner {{
            font-family: 'Nunito Sans', Arial, sans-serif !important;
            color: #153354 !important;
            background: #e6f0fa !important;
            padding: 12px 6px;
            border-radius: 12px;
            width: 100%;
            max-width: 600px;
            margin: 0 auto 18px auto;
            font-size: 1.08em;
            text-align: center;
            box-sizing: border-box;
            word-break: break-word;
            line-height: 1.6;
            font-weight: 700;
            box-shadow: 0 2px 8px rgba(20,60,120,0.04);
        }}
        @media only screen and (max-width: 600px) {{
            .custom-banner {{
                font-size: 0.97em !important;
                padding: 8px 3px !important;
                line-height: 1.3;
            }}
        }}
        </style>
        <div class="custom-banner">
            👋 <span style='font-weight:900'>{display}</span> – Practice your <b>{level} {language}</b>!<br>
            <span style='font-size:0.98em;font-weight:600;'>Start chatting below. 💬</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Chat Interface ---
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    for msg in st.session_state['messages']:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    user_input = st.chat_input("💬 Type your message here...")
    if user_input:
        increment_usage(trial_mode)
        st.session_state['messages'].append({'role': 'user', 'content': user_input})
        st.chat_message('user').markdown(user_input)

        # AI conversation response
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'system', 'content': f"You are a {level} {language} tutor."}, *st.session_state['messages']]
        )
        ai_reply = response.choices[0].message.content
        st.session_state['messages'].append({'role': 'assistant', 'content': ai_reply})
        st.chat_message('assistant').markdown(ai_reply)

        # --- GRAMMAR CHECK ---
        if language in ["German", "French", "English"]:
            grammar_prompt = (
                f"You are a helpful {language} teacher. "
                f"Check the following sentence for grammar, spelling, and phrasing errors. "
                f"Give the corrected sentence and a short explanation. "
                f"Sentence: {user_input}"
            )
            grammar_response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{"role": "system", "content": grammar_prompt}],
                max_tokens=120
            )
            grammar_reply = grammar_response.choices[0].message.content.strip()
            st.info(f"📝 **Grammar Correction:**\n{grammar_reply}")
