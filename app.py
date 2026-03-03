"""
GLP1Companion - Type 2 Diabetes + GLP-1 Tracking App
Streamlit MVP
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import hashlib
import re
import anthropic
import base64
from app.pdf_export import generate_health_report

# Medication lists for dropdowns
GLP1_MEDICATIONS = [
    "Mounjaro (tirzepatide)",
    "Ozempic (semaglutide)",
    "Wegovy (semaglutide)",
    "Zepbound (tirzepatide)",
    "Trulicity (dulaglutide)",
    "Victoza (liraglutide)",
    "Saxenda (liraglutide)",
    "Rybelsus (semaglutide - oral)",
    "Bydureon (exenatide)",
    "Other"
]

GLP1_DOSAGES = [
    "2.5mg", "5mg", "7.5mg", "10mg", "12.5mg", "15mg",
    "0.25mg", "0.5mg", "1mg", "2mg", "2.4mg",
    "0.75mg", "1.5mg", "3mg", "4.5mg",
    "0.6mg", "1.2mg", "1.8mg",
    "3mg (daily)", "7mg (daily)", "14mg (daily)",
    "Other"
]

DIABETES_MEDICATIONS = [
    "Metformin",
    "Glipizide",
    "Glyburide",
    "Januvia (sitagliptin)",
    "Invokana (canagliflozin)",
    "Farxiga (dapagliflozin)",
    "Jardiance (empagliflozin)",
    "Janumet",
    "Glucotrol",
    "Precose",
    "Other"
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def safe_int(value, default=0):
    """Safely convert a value to integer, handling None, strings, floats, etc."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


# =============================================================================
# DATABASE SETUP
# =============================================================================
# Use PostgreSQL on Render (production) or SQLite (local development)
import os

# Check if PostgreSQL URL is in environment (Streamlit Cloud secrets)
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///t2sync.db")

if DATABASE_URL.startswith("postgresql"):
    # PostgreSQL on Render
    engine = create_engine(DATABASE_URL)
else:
    # SQLite for local development
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String)
    diabetes_type = Column(String, default="Type 2")
    glp1_medication = Column(String)
    glp1_dosage = Column(String)
    other_diabetes_med = Column(String)  # Other diabetes medications
    target_glucose_min = Column(Integer, default=80)
    target_glucose_max = Column(Integer, default=130)
    goal_weight = Column(Float)
    start_date = Column(DateTime, default=datetime.now)
    
    glucose_logs = relationship("GlucoseLog", back_populates="user")
    weight_logs = relationship("WeightLog", back_populates="user")
    food_logs = relationship("FoodLog", back_populates="user")
    medication_logs = relationship("MedicationLog", back_populates="user")
    side_effects = relationship("SideEffect", back_populates="user")

class GlucoseLog(Base):
    __tablename__ = "glucose_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    value = Column(Integer, nullable=False)
    context = Column(String)  # fasting, before_meal, after_meal, bedtime
    notes = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    user = relationship("User", back_populates="glucose_logs")

class WeightLog(Base):
    __tablename__ = "weight_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    user = relationship("User", back_populates="weight_logs")

class FoodLog(Base):
    __tablename__ = "food_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    carbs = Column(Float)
    meal_type = Column(String)  # breakfast, lunch, dinner, snack
    notes = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    user = relationship("User", back_populates="food_logs")

class MedicationLog(Base):
    __tablename__ = "medication_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    medication = Column(String, nullable=False)
    dosage = Column(String)
    taken = Column(Integer, default=0)  # 0 = no, 1 = yes
    timestamp = Column(DateTime, default=datetime.now)
    user = relationship("User", back_populates="medication_logs")

class SideEffect(Base):
    __tablename__ = "side_effects"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symptom = Column(String, nullable=False)
    severity = Column(String)  # mild, moderate, severe
    notes = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    user = relationship("User", back_populates="side_effects")

# Feature 1: Medication History - stores previous med+dose combinations for quick add
class MedicationHistory(Base):
    __tablename__ = "medication_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    medication = Column(String, nullable=False)
    dosage = Column(String)
    last_used = Column(DateTime, default=datetime.now)
    use_count = Column(Integer, default=1)

# Feature 2: Medication Reminders - stores reminder preferences for each med
class MedicationReminder(Base):
    __tablename__ = "medication_reminders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    medication = Column(String, nullable=False)
    dosage = Column(String)
    reminder_day = Column(Integer)  # onday, 0=M6=Sunday
    reminder_time = Column(String)  # Store as "HH:MM" format
    is_active = Column(Integer, default=1)  # 1=active, 0=inactive
    last_reminder_sent = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)

# Create tables
Base.metadata.create_all(engine)

# Database migration - add missing columns and tables
try:
    from sqlalchemy import text
    with engine.connect() as conn:
        # Add other_diabetes_med column if it doesn't exist
        conn.execute(text("ALTER TABLE users ADD COLUMN other_diabetes_med TEXT"))
        conn.commit()
except:
    pass  # Column might already exist

# Create new tables if they don't exist (for Feature 1 & 2)
from sqlalchemy import inspect
inspector = inspect(engine)
existing_tables = inspector.get_table_names()

if "medication_history" not in existing_tables:
    Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

# =============================================================================
# AUTH HELPERS
# =============================================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password, hashed):
    return hash_password(password) == hashed

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="GLP1Companion",
    page_icon="💉",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit header and toolbar
st.markdown("""
<style>
    header {visibility: hidden !important; display: none !important;}
    .stApp > header {display: none !important;}
    div[data-testid="stHeader"] {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    div[data-testid="stMainMenu"] {display: none !important;}
    header[data-testid="stHeader"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# MOBILE CHART CONFIG - CSS-based solution
# =============================================================================
# This CSS disables chart interactions on mobile viewports
# Charts become static (no zoom/pan/hover) on small screens

# Add CSS for mobile chart interactivity disabling
st.markdown("""
<style>
    /* Disable plotly chart interactions on mobile */
    @media (max-width: 768px) {
        /* Disable zoom and pan */
        .plotly.js-plotly-plot .plotly .modebar {
            display: none !important;
        }
        
        /* Make charts static by disabling pointer events on certain elements */
        .js-plotly-plot .plotly .cursor-pointer,
        .js-plotly-plot .plotly .cursor-crosshair,
        .js-plotly-plot .plotly .cursor-move {
            cursor: default !important;
        }
        
        /* Disable hover effects */
        .js-plotly-plot .plotly .hoverlayer .hovertext {
            visibility: hidden !important;
        }
        
        /* Make the entire chart container non-interactive */
        .js-plotly-plot {
            pointer-events: none !important;
        }
        
        /* Re-enable tooltips but make them static */
        .js-plotly-plot .plotly .hoverlayer {
            pointer-events: none !important;
        }
    }
</style>
""", unsafe_allow_html=True)


def get_chart_config():
    """Get Plotly chart config - charts are made static via CSS on mobile"""
    # Always use minimal modebar - actual interactivity disabled via CSS on mobile
    return {
        'displayModeBar': False,
        'scrollZoom': False,  # Disable scroll zoom
        'editable': False,
    }


def get_chart_layout_kwargs():
    """Get additional layout kwargs to reduce interactivity"""
    # Return layout options that reduce interactivity
    return {
        # These help reduce accidental interactions
    }

# Custom CSS for dark theme
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stApp {
        background-color: #0e1117;
    }
    .metric-card {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        color: #10b981;
    }
    .metric-label {
        font-size: 14px;
        color: #94a3b8;
    }
    /* Mobile sidebar improvements */
    @media (max-width: 768px) {
        [data-testid="stSidebar"] {
            width: 200px !important;
            max-width: 60vw !important;
        }
        /* Make forms scrollable on mobile */
        .stForm {
            overflow-y: auto;
            max-height: 60vh;
            padding-bottom: 20px;
        }
        /* Fix keyboard blocking inputs */
        input[type="text"], 
        input[type="password"],
        input[type="number"],
        select {
            font-size: 16px !important;
        }
        /* Prevent keyboard from hiding input */
        .stTextInput > div > div > input {
            padding-bottom: 50px !important;
        }
        /* Make page scrollable */
        .main .block-container {
            padding-bottom: 100px !important;
        }
        /* Ensure form content is visible above keyboard */
        div[data-testid="stForm"] {
            position: relative;
            z-index: 100;
        }
    }
            top: 5px;
            left: 5px;
            z-index: 999;
        }
        /* Hide main content when sidebar is open on mobile */
        section[data-testid="stMain"] {
            margin-left: 0 !important;
        }
    }
    /* Auto-close sidebar after selection on mobile */
    .stRadio > div {
        gap: 5px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE - Initialize with proper type checking
# =============================================================================
# Initialize with defaults - use setdefault for safety
st.session_state.setdefault("user_id", None)
st.session_state.setdefault("user_name", None)
st.session_state.setdefault("chat_messages", [])
st.session_state.setdefault("show_signup", False)
st.session_state.setdefault("show_reset", False)

# Force proper type if somehow corrupted (fixes str assignment error)
if not isinstance(st.session_state.get("chat_messages"), list):
    st.session_state.chat_messages = []

# =============================================================================
# AUTH PAGES
# =============================================================================
def login_page():
    st.title("🔐 GLP1Companion Login")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            db = Session()
            user = db.query(User).filter(User.email == email.lower()).first()
            
            if not user:
                db.close()
                st.error("Account not found. Please sign up.")
                return
            
            if check_password(password, user.password_hash):
                st.session_state.user_id = user.id
                st.session_state.user_name = user.name
                db.close()
                st.rerun()
            else:
                db.close()
                st.error("Invalid password. Use 'Forgot Password' to reset.")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Don't have an account? Sign up"):
            st.session_state.show_signup = True
            st.rerun()
    with col2:
        if st.button("Forgot Password?"):
            st.session_state.show_reset = True
            st.rerun()


def reset_password_page():
    st.title("🔑 Reset Password")
    
    with st.form("reset_form"):
        email = st.text_input("Your Email")
        new_password = st.text_input("New Password", type="password")
        confirm = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Reset Password"):
            if new_password != confirm:
                st.error("Passwords don't match")
            elif not email or not new_password:
                st.error("Email and password required")
            else:
                db = Session()
                user = db.query(User).filter(User.email == email.lower()).first()
                
                if user:
                    user.password_hash = hash_password(new_password)
                    db.commit()
                    db.close()
                    st.success("Password reset! Please login with your new password.")
                    st.session_state.show_reset = False
                    st.rerun()
                else:
                    db.close()
                    st.error("Email not found")
    
    st.markdown("---")
    if st.button("Back to Login"):
        st.session_state.show_reset = False
        st.rerun()


def signup_page():
    st.title("🚀 GLP1Companion - Create Account")
    
    with st.form("signup_form"):
        name = st.text_input("Your Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        
        # Diabetes medications (optional for now)
        st.markdown("### Diabetes Medications")
        st.markdown("**GLP-1 Medications**")
        glp1_med = st.selectbox("GLP-1 Medication", 
            ["", "Mounjaro (tirzepatide)", "Zepbound (tirzepatide)",
             "Ozempic (semaglutide)", "Wegovy (semaglutide)",
             "Trulicity (dulaglutide)", "Bydureon (exenatide)",
             "Victoza (liraglutide)", "Saxenda (liraglutide)",
             "Rybelsus (semaglutide)", "Other GLP-1"])
        
        st.markdown("**Other Diabetes Medications**")
        other_med = st.selectbox("Other Diabetes Meds (optional)", 
            ["", "Metformin (Glucophage)", "Metformin ER",
             "Glipizide", "Glyburide", "Glimepiride",
             "Jardiance (empagliflozin)", "Invokana (canagliflozin)", 
             "Farxiga (dapagliflozin)",
             "Januvia (sitagliptin)", "Tradjenta (linagliptin)",
             "Actos (pioglitazone)",
             "Prandin (repaglinide)",
             "Lantus (insulin glargine)", "Novolog (insulin aspart)",
             "Humalog (insulin lispro)", "Toujeo", "Tresiba",
             "Other Insulin", "Other Diabetes Medication"])
        glp1_dosage = st.text_input("Dosage (e.g., 5mg)", key="dosage")
        
        submit = st.form_submit_button("Create Account")
        
        if submit:
            if password != confirm:
                st.error("Passwords don't match")
            elif not email or not password:
                st.error("Email and password required")
            else:
                db = Session()
                existing = db.query(User).filter(User.email == email.lower()).first()
                if existing:
                    st.error("Email already exists")
                else:
                    user = User(
                        email=email.lower(),
                        password_hash=hash_password(password),
                        name=name,
                        glp1_medication=glp1_med,
                        glp1_dosage=glp1_dosage,
                        other_diabetes_med=other_med
                    )
                    db.add(user)
                    db.commit()
                    db.close()
                    st.success("Account created! Please login.")
                    st.session_state.show_signup = False
                    st.rerun()
                db.close()
    
    st.markdown("---")
    if st.button("Already have an account? Login"):
        st.session_state.show_signup = False
        st.rerun()

# =============================================================================
# DASHBOARD
# =============================================================================
def dashboard():
    st.title(f"📊 Welcome back, {st.session_state.user_name}!")
    
    db = Session()
    user = db.query(User).filter(User.id == st.session_state.user_id).first()
    
    # Get today's data
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    
    # Glucose today
    glucose_today = db.query(GlucoseLog).filter(
        GlucoseLog.user_id == st.session_state.user_id,
        GlucoseLog.timestamp >= today_start
    ).all()
    
    # Weight today
    weight_today = db.query(WeightLog).filter(
        WeightLog.user_id == st.session_state.user_id,
        WeightLog.timestamp >= today_start
    ).all()
    
    # Food today
    food_today = db.query(FoodLog).filter(
        FoodLog.user_id == st.session_state.user_id,
        FoodLog.timestamp >= today_start
    ).all()
    
    # Medication today
    meds = db.query(MedicationLog).filter(
        MedicationLog.user_id == st.session_state.user_id
    ).order_by(MedicationLog.timestamp.desc()).limit(5).all()
    
    db.close()
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if glucose_today:
            latest = glucose_today[-1].value
            color = "🟢" if latest <= 130 else "🟡" if latest <= 180 else "🔴"
            st.metric("Glucose", f"{latest} mg/dL", delta=color)
        else:
            st.metric("Glucose", "--", delta="No reading")
    
    with col2:
        if weight_today:
            latest = weight_today[-1].value
            st.metric("Weight", f"{latest} lbs")
        else:
            st.metric("Weight", "--", delta="No reading")
    
    with col3:
        st.metric("Meals Logged", len(food_today))
    
    with col4:
        st.metric("GLP-1", user.glp1_medication or "Not set")
    
    st.markdown("---")
    
    # Quick actions
    st.subheader("⚡ Quick Log")
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.info("💉 Go to Glucose tab to log")
    
    with c2:
        st.info("⚖️ Go to Weight tab to log")
    
    with c3:
        st.info("🍎 Go to Food tab to log")
    
    with c4:
        st.info("💊 Go to Medication tab to log")
    
    # Recent activity
    st.markdown("---")
    st.subheader("📝 Recent Activity")
    
    if glucose_today or weight_today or food_today:
        activities = []
        
        for g in glucose_today:
            activities.append({"time": g.timestamp, "type": "💉 Glucose", "value": f"{g.value} mg/dL"})
        for w in weight_today:
            activities.append({"time": w.timestamp, "type": "⚖️ Weight", "value": f"{w.value} lbs"})
        for f in food_today:
            activities.append({"time": f.timestamp, "type": "🍎 Food", "value": f"{f.name} ({f.carbs}g carbs)"})
        
        activities.sort(key=lambda x: x["time"], reverse=True)
        
        for a in activities[:5]:
            st.write(f"{a['time'].strftime('%I:%M %p')} - {a['type']}: {a['value']}")
    else:
        st.info("No activity today. Start logging!")
    
    # GLP-1 streak
    if user.glp1_medication:
        st.markdown("---")
        st.success(f"💉 You're on {user.glp1_medication} {user.glp1_dosage or ''} - Keep tracking!")

# =============================================================================
# GLUCOSE PAGE
# =============================================================================
def glucose_page():
    st.title("💉 Glucose Tracking")
    
    # Log form
    with st.form("glucose_form"):
        col1, col2 = st.columns(2)
        with col1:
            value = st.number_input("Glucose (mg/dL)", min_value=0, max_value=600, value=120)
        with col2:
            context = st.selectbox("Context", ["Fasting", "Before Meal", "After Meal", "Bedtime"])
        notes = st.text_area("Notes (optional)")
        
        if st.form_submit_button("Log Glucose"):
            db = Session()
            log = GlucoseLog(
                user_id=st.session_state.user_id,
                value=value,
                context=context.lower().replace(" ", "_"),
                notes=notes
            )
            db.add(log)
            db.commit()
            db.close()
            st.session_state.glucose_saved = True
            st.success("✅ Glucose logged!")
            st.rerun()
    
    # Show success message if just saved
    if st.session_state.get("glucose_saved"):
        st.session_state.glucose_saved = False
        st.info("✅ Glucose saved!")
    
    # Show history
    st.markdown("---")
    st.subheader("📊 History")
    
    db = Session()
    logs = db.query(GlucoseLog).filter(
        GlucoseLog.user_id == st.session_state.user_id
    ).order_by(GlucoseLog.timestamp.desc()).limit(30).all()
    db.close()
    
    if logs:
        data = []
        for log in logs:
            data.append({
                "Time": pd.to_datetime(log.timestamp),
                "Glucose": log.value,
                "Context": log.context
            })
        
        df = pd.DataFrame(data)
        df = df.sort_values("Time")  # Ensure sorted by time
        
        # Chart
        fig = px.line(df, x="Time", y="Glucose", title="Glucose Trend (All Readings)", 
                     markers=True, color_discrete_sequence=["#10b981"])
        fig.update_xaxes(title_text="Time")
        fig.update_yaxes(title_text="Glucose (mg/dL)")
        fig.add_hline(y=130, line_dash="dash", line_color="yellow", annotation=dict(text="Target Max"))
        fig.add_hline(y=80, line_dash="dash", line_color="green", annotation=dict(text="Target Min"))
        st.plotly_chart(fig, use_container_width=True, config=get_chart_config())
        
        # Table with formatted time
        st.subheader("📊 All Readings")
        table_df = df.copy()
        table_df['Time'] = table_df['Time'].dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(table_df, use_container_width=True)
    else:
        st.info("No glucose logs yet")

# =============================================================================
# WEIGHT PAGE
# =============================================================================
def weight_page():
    st.title("⚖️ Weight Tracking")
    
    with st.form("weight_form"):
        value = st.number_input("Weight (lbs)", min_value=50.0, max_value=500.0, value=180.0, step=0.1)
        
        if st.form_submit_button("Log Weight"):
            db = Session()
            log = WeightLog(user_id=st.session_state.user_id, value=value)
            db.add(log)
            db.commit()
            db.close()
            st.session_state.weight_saved = True
            st.success("✅ Weight logged!")
            st.rerun()
    
    # Show success message if just saved
    if st.session_state.get("weight_saved"):
        st.session_state.weight_saved = False
        st.info("✅ Weight saved!")
    
    st.markdown("---")
    st.subheader("📊 History")
    
    db = Session()
    logs = db.query(WeightLog).filter(
        WeightLog.user_id == st.session_state.user_id
    ).order_by(WeightLog.timestamp.desc()).limit(30).all()
    
    user = db.query(User).filter(User.id == st.session_state.user_id).first()
    goal = user.goal_weight if user else None
    db.close()
    
    if logs:
        data = []
        for log in logs:
            data.append({"Date": pd.to_datetime(log.timestamp), "Weight": log.value})
        
        df = pd.DataFrame(data)
        df = df.sort_values("Date")  # Ensure sorted by date
        
        # Aggregate to one reading per day (latest of the day)
        df['DateOnly'] = df['Date'].dt.date
        df = df.groupby('DateOnly').last().reset_index()
        df['Date'] = pd.to_datetime(df['DateOnly'])
        
        fig = px.line(df, x="Date", y="Weight", title="Weight Trend (Daily)", 
                     markers=True, color_discrete_sequence=["#10b981"])
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Weight (lbs)")
        if goal:
            fig.add_hline(y=goal, line_dash="dash", line_color="blue", annotation=dict(text=f"Goal: {goal}"))
        st.plotly_chart(fig, use_container_width=True, config=get_chart_config())
        
        # Show daily summary table
        st.subheader("📅 Daily Readings")
        table_df = df[['Date', 'Weight']].copy()
        table_df['Date'] = table_df['Date'].dt.strftime('%Y-%m-%d')
        table_df['Weight'] = table_df['Weight'].round(1)
        st.dataframe(table_df, use_container_width=True)
        
        if len(df) > 0:
            latest = df.iloc[-1]['Weight']
            if len(df) > 1:
                change = latest - df.iloc[-2]['Weight']
                st.metric("Latest", f"{latest} lbs", delta=f"{change:.1f} lbs")
            else:
                st.metric("Latest", f"{latest} lbs")
    else:
        st.info("No weight logs yet")

# =============================================================================
# FOOD PAGE
# =============================================================================
def food_page():
    st.title("🍎 Food Logging")
    
    # Photo food logging with AI
    st.subheader("📸 Snap & AI Log")
    
    # Check if we should show camera
    if "show_camera" not in st.session_state:
        st.session_state.show_camera = True
    
    if st.session_state.show_camera:
        # Camera input for photo
        uploaded_file = st.camera_input("Take a photo of your food")
    
    # Session state for AI analysis results
    if "ai_food_analysis" not in st.session_state:
        st.session_state.ai_food_analysis = None
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Your meal", use_container_width=True)
        
        # AI Analyze button
        if st.button("🤖 Analyze Food with AI"):
            with st.spinner("AI is analyzing your food..."):
                try:
                    # Convert image to base64
                    import base64
                    image_bytes = uploaded_file.getvalue()
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                    
                    # Detect image type
                    image_type = uploaded_file.type if uploaded_file.type else "image/jpeg"
                    
                    # Call Anthropic Claude Vision API
                    import anthropic
                    
                    # Get API key from secrets or settings
                    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
                    if not api_key:
                        st.error("Add ANTHROPIC_API_KEY to Streamlit secrets!")
                        st.stop()
                    
                    client = anthropic.Anthropic(api_key=api_key)
                    
                    message = client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=300,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": image_type,
                                            "data": image_base64
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": """Describe this food in detail. Estimate the calories, carbohydrates (in grams), fat (in grams), and protein (in grams). Respond in this exact format:
FOOD: [name of food]
CALORIES: [number]
CARBS: [number]
FAT: [number]
PROTEIN: [number]"""
                                    }
                                ]
                            }
                        ]
                    )
                    
                    ai_text = message.content[0].text
                    st.write("Debug AI response:", ai_text)  # Debug - remove later
                    
                    # Parse the response - more robust parsing
                    food_name = ""
                    carbs = 0
                    calories = 0
                    fat = 0
                    protein = 0
                    notes = ""
                    
                    # Try to find each field - more flexible regex
                    import re
                    
                    # FOOD - look for "FOOD:" or just take first line
                    food_match = re.search(r'FOOD:\s*(.+?)(?:\n|CALORIES|$)', ai_text, re.IGNORECASE)
                    if food_match:
                        food_name = food_match.group(1).strip()
                    else:
                        # Try first line as food name
                        lines = ai_text.strip().split('\n')
                        if lines:
                            food_name = lines[0].strip()
                    
                    # CALORIES - look for "Calories: X" or "CALORIES: X" with various formats
                    cal_match = re.search(r'(?:CALORIES|calories| Calories).*?(\d+)', ai_text, re.IGNORECASE)
                    if cal_match:
                        calories = int(cal_match.group(1))
                    
                    # CARBS - look for "Carbs: Xg" or "CARBS: X"
                    carb_match = re.search(r'(?:CARBS|carbs| Carbs).*?(\d+)', ai_text, re.IGNORECASE)
                    if carb_match:
                        carbs = int(carb_match.group(1))
                    
                    # FAT
                    fat_match = re.search(r'(?:FAT|fat| Fat).*?(\d+)', ai_text, re.IGNORECASE)
                    if fat_match:
                        fat = int(fat_match.group(1))
                    
                    # PROTEIN
                    prot_match = re.search(r'(?:PROTEIN|protein| Protein).*?(\d+)', ai_text, re.IGNORECASE)
                    if prot_match:
                        protein = int(prot_match.group(1))
                    
                    st.session_state.ai_food_analysis = {
                        "food_name": food_name,
                        "carbs": carbs,
                        "calories": calories,
                        "fat": fat,
                        "protein": protein,
                        "notes": notes,
                        "raw": ai_text
                    }
                    st.success(f"✅ AI detected: {food_name} (~{calories} cal, {carbs}g carbs, {fat}g fat, {protein}g protein)")
                except Exception as e:
                    st.error(f"AI Error: {e}")
        
        # Show AI analysis results
        if st.session_state.ai_food_analysis:
            analysis = st.session_state.ai_food_analysis
            st.info(f"🤖 AI: {analysis['food_name']} ({analysis.get('calories', 0)} cal, {analysis['carbs']}g carbs, {analysis.get('fat', 0)}g fat, {analysis.get('protein', 0)}g protein)")
        
        # Form to confirm/log
        with st.form("photo_food_form"):
            st.markdown("**Confirm or edit:**")
            col1, col2 = st.columns(2)
            with col1:
                # Pre-fill with AI analysis if available (with defensive type checking)
                default_name = st.session_state.ai_food_analysis.get("food_name", "") if st.session_state.ai_food_analysis else ""
                default_carbs = safe_int(st.session_state.ai_food_analysis.get("carbs", 0)) if st.session_state.ai_food_analysis else 0
                default_cal = safe_int(st.session_state.ai_food_analysis.get("calories", 0)) if st.session_state.ai_food_analysis else 0
                default_prot = safe_int(st.session_state.ai_food_analysis.get("protein", 0)) if st.session_state.ai_food_analysis else 0
                default_fat = safe_int(st.session_state.ai_food_analysis.get("fat", 0)) if st.session_state.ai_food_analysis else 0
                
                food_name = st.text_input("Food Name", value=default_name, placeholder="e.g., Grilled chicken salad")
                estimated_carbs = st.number_input("Carbs (g)", min_value=0, value=default_carbs, step=1)
                calories = st.number_input("Calories", min_value=0, value=default_cal, step=10)
            with col2:
                meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
                protein = st.number_input("Protein (g)", min_value=0, value=default_prot, step=5)
                fat = st.number_input("Fat (g)", min_value=0, value=default_fat, step=5)
            notes = st.text_area("Notes", placeholder="Any additional details...")
            
            if st.form_submit_button("✅ Log Food"):
                # Build nutrition summary
                nutrition_info = f"📸 AI | Cal: {calories} | C: {estimated_carbs}g | P: {protein}g | F: {fat}g"
                if notes:
                    nutrition_info += f" | {notes}"
                
                db = Session()
                log = FoodLog(
                    user_id=st.session_state.user_id,
                    name=food_name,
                    carbs=estimated_carbs,
                    meal_type=meal_type.lower(),
                    notes=nutrition_info
                )
                db.add(log)
                db.commit()
                db.close()
                st.session_state.ai_food_analysis = None
                st.success(f"✅ Logged: {food_name} ({calories} cal, {estimated_carbs}g carbs, {protein}g protein, {fat}g fat)")
                
                # Show option to add another
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📸 Log Another Food", key="log_another_food"):
                        st.session_state.show_camera = True
                        st.session_state.ai_food_analysis = None
                        st.rerun()
                with col2:
                    if st.button("🏠 Go to Dashboard", key="go_to_dash_food"):
                        st.session_state.current_tab = "dashboard"
                        st.rerun()
        
        if st.button("🗑️ Clear / Start Over", key="clear_food_btn"):
            st.session_state.ai_food_analysis = None
            st.session_state.show_camera = True
            st.rerun()
    
    st.markdown("---")
    
    # Voice food logging with AI
    st.subheader("🎤 Voice Log")
    st.write("Say what you ate — AI will find the nutrition info")
    
    # Audio input for voice
    audio_value = st.audio_input("Tap to record what you ate")
    
    if audio_value is not None:
        st.audio(audio_value, format="audio/wav")
        
        if st.button("🤖 Analyze Voice with AI", key="analyze_voice_btn"):
            with st.spinner("AI is analyzing your voice..."):
                try:
                    import anthropic
                    import base64
                    
                    # Get audio bytes
                    audio_bytes = audio_value.getvalue()
                    
                    # Get API key from secrets
                    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
                    if not api_key:
                        st.error("Add ANTHROPIC_API_KEY to Streamlit secrets!")
                        st.stop()
                    
                    client = anthropic.Anthropic(api_key=api_key)
                    
                    # Convert audio to base64 for API
                    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                    
                    # Use Claude to transcribe and extract nutrition
                    message = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=500,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "audio",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "audio/wav",
                                            "data": audio_base64
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": """Listen to this voice note about food. First, transcribe what the person says. Then, estimate the nutritional content for what they describe.

Respond in this exact format:
TRANSCRIPT: [what they said]
FOOD: [name of food or meal]
CALORIES: [estimated calories]
CARBS: [carbs in grams]
FAT: [fat in grams]
PROTEIN: [protein in grams]

If they mention multiple items, list them all and estimate total nutrition."""
                                    }
                                ]
                            }
                        ]
                    )
                    
                    ai_text = message.content[0].text
                    
                    # Parse the response
                    food_name = ""
                    carbs = 0
                    calories = 0
                    fat = 0
                    protein = 0
                    transcript = ""
                    
                    # Extract transcript
                    trans_match = re.search(r'TRANSCRIPT:\s*(.+?)(?:\nFOOD:|$)', ai_text, re.IGNORECASE | re.DOTALL)
                    if trans_match:
                        transcript = trans_match.group(1).strip()
                    
                    # FOOD
                    food_match = re.search(r'FOOD:\s*(.+?)(?:\nCALORIES:|$)', ai_text, re.IGNORECASE | re.DOTALL)
                    if food_match:
                        food_name = food_match.group(1).strip()
                    
                    # CALORIES
                    cal_match = re.search(r'CALORIES:\s*(\d+)', ai_text, re.IGNORECASE)
                    if cal_match:
                        calories = int(cal_match.group(1))
                    
                    # CARBS
                    carb_match = re.search(r'CARBS:\s*(\d+)', ai_text, re.IGNORECASE)
                    if carb_match:
                        carbs = int(carb_match.group(1))
                    
                    # FAT
                    fat_match = re.search(r'FAT:\s*(\d+)', ai_text, re.IGNORECASE)
                    if fat_match:
                        fat = int(fat_match.group(1))
                    
                    # PROTEIN
                    prot_match = re.search(r'PROTEIN:\s*(\d+)', ai_text, re.IGNORECASE)
                    if prot_match:
                        protein = int(prot_match.group(1))
                    
                    # Store in session state for the form
                    st.session_state.voice_food_analysis = {
                        "food_name": food_name,
                        "carbs": carbs,
                        "calories": calories,
                        "fat": fat,
                        "protein": protein,
                        "transcript": transcript
                    }
                    st.success(f"✅ AI detected: {food_name} (~{calories} cal, {carbs}g carbs)")
                    
                except Exception as e:
                    st.error(f"AI Error: {e}")
    
    # Initialize form session state for voice food
    if "voice_form_submitted" not in st.session_state:
        st.session_state.voice_form_submitted = False
    
    # Show voice analysis results and form
    if "voice_food_analysis" in st.session_state and st.session_state.voice_food_analysis:
        analysis = st.session_state.voice_food_analysis
        st.info(f"🤖 AI: {analysis['food_name']} ({analysis.get('calories', 0)} cal, {analysis['carbs']}g carbs, {analysis.get('fat', 0)}g fat, {analysis.get('protein', 0)}g protein)")
        
        # Use session state for form values to handle dynamic defaults
        if not st.session_state.voice_form_submitted:
            st.session_state.voice_food_name = analysis.get("food_name", "")
            st.session_state.voice_food_carbs = analysis.get("carbs", 0)
            st.session_state.voice_food_calories = analysis.get("calories", 0)
            st.session_state.voice_food_protein = analysis.get("protein", 0)
            st.session_state.voice_food_fat = analysis.get("fat", 0)
        
        with st.form("voice_food_form"):
            st.markdown("**Confirm or edit:**")
            col1, col2 = st.columns(2)
            with col1:
                food_name = st.text_input("Food Name", value=st.session_state.get("voice_food_name", ""))
                estimated_carbs = st.number_input("Carbs (g)", min_value=0, value=int(st.session_state.get("voice_food_carbs", 0)), step=1)
                calories = st.number_input("Calories", min_value=0, value=int(st.session_state.get("voice_food_calories", 0)), step=10)
            with col2:
                meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
                protein = st.number_input("Protein (g)", min_value=0, value=int(st.session_state.get("voice_food_protein", 0)), step=5)
                fat = st.number_input("Fat (g)", min_value=0, value=int(st.session_state.get("voice_food_fat", 0)), step=5)
            
            notes = st.text_area("Notes", value="🎤 Voice logged")
            
            if st.form_submit_button("✅ Log Food"):
                # Validate
                if not food_name.strip():
                    st.error("Please enter a food name")
                else:
                    nutrition_info = f"🎤 Voice | Cal: {calories} | C: {estimated_carbs}g | P: {protein}g | F: {fat}g"
                    
                    db = Session()
                    log = FoodLog(
                        user_id=st.session_state.user_id,
                        name=food_name,
                        carbs=estimated_carbs,
                        meal_type=meal_type.lower(),
                        notes=nutrition_info
                    )
                    db.add(log)
                    db.commit()
                    db.close()
                    st.session_state.voice_food_analysis = None
                    st.session_state.voice_form_submitted = False
                    st.success(f"✅ Logged: {food_name} ({calories} cal, {estimated_carbs}g carbs)")
                    st.rerun()
        
        if st.button("Clear"):
            st.session_state.voice_food_analysis = None
            st.session_state.voice_form_submitted = False
            st.rerun()
    
    st.markdown("---")
    
    # Recipe ingredients nutrition calculator
    st.subheader("🧂 Recipe Calculator")
    st.write("Enter ingredients manually, by voice, or snap/ upload a photo")
    
    # Initialize recipe ingredients session state
    if "recipe_ingredients" not in st.session_state:
        st.session_state.recipe_ingredients = ""
    
    # Option 1: Photo of recipe/ingredients (camera or upload)
    st.markdown("**📸 Option 1: Upload or snap recipe photo**")
    
    # Two columns: upload and camera
    col1, col2 = st.columns(2)
    with col1:
        # File uploader for screenshots/downloads
        uploaded_recipe = st.file_uploader("Upload recipe screenshot", type=["png", "jpg", "jpeg"])
    with col2:
        # Camera input
        recipe_photo = st.camera_input("Or snap a photo")
    
    # Use whichever was provided
    recipe_image = uploaded_recipe or recipe_photo
    
    if recipe_image is not None:
        st.image(recipe_image, caption="Recipe photo", use_container_width=True)
        
        if st.button("🤖 Extract Ingredients from Photo", key="extract_recipe_photo_btn"):
            with st.spinner("AI is reading the recipe..."):
                try:
                    import base64
                    import anthropic
                    
                    image_bytes = recipe_image.getvalue()
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                    
                    # Detect image type
                    image_type = recipe_image.type if recipe_image.type else "image/jpeg"
                    if "png" in recipe_image.name.lower() if recipe_image.name else False:
                        image_type = "image/png"
                    
                    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
                    if not api_key:
                        st.error("Add ANTHROPIC_API_KEY to Streamlit secrets!")
                        st.stop()
                    
                    client = anthropic.Anthropic(api_key=api_key)
                    
                    message = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=500,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": image_type,
                                            "data": image_base64
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": """Extract all ingredients from this recipe. List each ingredient on a new line in this format:
[quantity] [unit] [ingredient]

Example:
200g chicken breast
100g white rice
50g broccoli
1 tbsp olive oil

If it's a nutrition label, extract all the information."""
                                    }
                                ]
                            }
                        ]
                    )
                    
                    extracted = message.content[0].text
                    st.session_state.recipe_ingredients = extracted
                    st.success("✅ Ingredients extracted!")
                    st.text_area("Extracted ingredients:", value=extracted, height=150, key="extracted_view")
                    
                except Exception as e:
                    st.error(f"AI Error: {e}")
    
    # Option 2: Voice input for ingredients
    st.markdown("**🎤 Option 2: Voice ingredients**")
    voice_ingredients = st.audio_input("Tap to dict ingredients")
    
    if voice_ingredients is not None:
        st.audio(voice_ingredients, format="audio/wav")
        
        if st.button("🤖 Transcribe Ingredients", key="transcribe_recipe_btn"):
            with st.spinner("AI is transcribing..."):
                try:
                    import anthropic
                    import base64
                    
                    audio_bytes = voice_ingredients.getvalue()
                    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                    
                    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
                    if not api_key:
                        st.error("Add ANTHROPIC_API_KEY to Streamlit secrets!")
                        st.stop()
                    
                    client = anthropic.Anthropic(api_key=api_key)
                    
                    message = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=400,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "audio",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "audio/wav",
                                            "data": audio_base64
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": """Listen to this voice note about recipe ingredients. Transcribe what ingredients are mentioned.

List each ingredient on a new line in this format:
[quantity] [unit] [ingredient]

Example:
200g chicken breast
100g white rice
50g broccoli"""
                                    }
                                ]
                            }
                        ]
                    )
                    
                    transcribed = message.content[0].text
                    st.session_state.recipe_ingredients = transcribed
                    st.success("✅ Ingredients transcribed!")
                    st.text_area("Transcribed ingredients:", value=transcribed, height=150, key="transcribed_view")
                    
                except Exception as e:
                    st.error(f"AI Error: {e}")
    
    # Option 3: Manual entry
    st.markdown("**✏️ Option 3: Manual entry**")
    
    # Initialize recipe servings session state
    if "recipe_servings" not in st.session_state:
        st.session_state.recipe_servings = 4
    
    with st.form("recipe_form"):
        ingredients_text = st.text_area("List ingredients (one per line)", 
            value=st.session_state.recipe_ingredients,
            placeholder="e.g.:\n200g chicken breast\n100g rice\n50g broccoli\n1 tbsp olive oil",
            height=150)
        
        # NEW: Ask for servings BEFORE calculating
        recipe_servings = st.number_input("How many servings does this recipe make?", 
            min_value=1, max_value=50, value=st.session_state.recipe_servings, step=1)
        st.session_state.recipe_servings = recipe_servings
        
        if st.form_submit_button("🤖 Calculate Nutrition"):
            if not ingredients_text.strip():
                st.warning("Please enter some ingredients")
            else:
                with st.spinner("AI is calculating nutrition..."):
                    try:
                        import re
                        import anthropic
                        
                        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
                        if not api_key:
                            st.error("Add ANTHROPIC_API_KEY to Streamlit secrets!")
                            st.stop()
                        
                        client = anthropic.Anthropic(api_key=api_key)
                        
                        message = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=400,
                            messages=[
                                {
                                    "role": "user",
                                    "content": f"""Calculate the total nutritional content for this recipe:

{ingredients_text}

Respond in this exact format with TOTALS at the top, then breakdown:
TOTAL CALORIES: [number]
TOTAL CARBS: [number]g
TOTAL FAT: [number]g
TOTAL PROTEIN: [number]g

BREAKDOWN:
- [ingredient 1]: [calories] cal, [carbs]g carbs, [fat]g fat, [protein]g protein
- [ingredient 2]: ...

Use standard nutritional data. Estimate portion sizes if not specified."""
                                }
                            ]
                        )
                        
                        ai_text = message.content[0].text
                        st.markdown("### 📊 Nutrition Results")
                        st.write(ai_text)
                        
                        # Parse for quick summary
                        cal_match = re.search(r'TOTAL CALORIES:\s*(\d+)', ai_text, re.IGNORECASE)
                        carb_match = re.search(r'TOTAL CARBS:\s*(\d+)', ai_text, re.IGNORECASE)
                        fat_match = re.search(r'TOTAL FAT:\s*(\d+)', ai_text, re.IGNORECASE)
                        prot_match = re.search(r'TOTAL PROTEIN:\s*(\d+)', ai_text, re.IGNORECASE)
                        
                        if cal_match:
                            total_cal = int(cal_match.group(1))
                            total_carbs = int(carb_match.group(1)) if carb_match else 0
                            total_fat = int(fat_match.group(1)) if fat_match else 0
                            total_protein = int(prot_match.group(1)) if prot_match else 0
                            
                            # Calculate per-serving nutrition
                            servings = recipe_servings
                            per_serving_cal = round(total_cal / servings)
                            per_serving_carbs = round(total_carbs / servings)
                            per_serving_fat = round(total_fat / servings)
                            per_serving_protein = round(total_protein / servings)
                            
                            st.session_state.recipe_nutrition = {
                                "total_calories": total_cal,
                                "total_carbs": total_carbs,
                                "total_fat": total_fat,
                                "total_protein": total_protein,
                                "servings": servings,
                                "per_serving_calories": per_serving_cal,
                                "per_serving_carbs": per_serving_carbs,
                                "per_serving_fat": per_serving_fat,
                                "per_serving_protein": per_serving_protein,
                                "raw": ai_text
                            }
                            
                    except Exception as e:
                        st.error(f"AI Error: {e}")
    
    # Initialize recipe form session state
    if "recipe_form_submitted" not in st.session_state:
        st.session_state.recipe_form_submitted = False
    
    # Option to log recipe as meal
    if "recipe_nutrition" in st.session_state and st.session_state.recipe_nutrition:
        nutrition = st.session_state.recipe_nutrition
        # Show both total and per-serving
        st.info(f"📊 Recipe Total: {nutrition['total_calories']} cal | {nutrition['total_carbs']}g carbs | {nutrition['total_fat']}g fat | {nutrition['total_protein']}g protein")
        st.success(f"🍽️ Per Serving ({nutrition['servings']} servings): {nutrition['per_serving_calories']} cal | {nutrition['per_serving_carbs']}g carbs | {nutrition['per_serving_fat']}g fat | {nutrition['per_serving_protein']}g protein")
        
        with st.form("log_recipe_form"):
            recipe_name = st.text_input("Recipe Name", placeholder="e.g., Homemade Chicken Stir Fry")
            meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
            
            # NEW: Ask how many servings eaten
            servings_eaten = st.number_input("How many servings did you eat?", 
                min_value=0.5, max_value=float(nutrition['servings'] * 2), value=1.0, step=0.5)
            
            # Calculate nutrition based on servings eaten
            logged_cal = round(nutrition['per_serving_calories'] * servings_eaten)
            logged_carbs = round(nutrition['per_serving_carbs'] * servings_eaten)
            logged_fat = round(nutrition['per_serving_fat'] * servings_eaten)
            logged_protein = round(nutrition['per_serving_protein'] * servings_eaten)
            
            st.markdown(f"**📝 Logging:** {servings_eaten} serving(s) = {logged_cal} cal | {logged_carbs}g carbs | {logged_fat}g fat | {logged_protein}g protein")
            
            if st.form_submit_button("✅ Log Recipe"):
                # Validate
                if not recipe_name.strip():
                    st.error("Please enter a recipe name")
                else:
                    db = Session()
                    log = FoodLog(
                        user_id=st.session_state.user_id,
                        name=recipe_name,
                        carbs=logged_carbs,
                        meal_type=meal_type.lower(),
                        notes=f"🧂 Recipe ({servings_eaten}/{nutrition['servings']} servings) | Cal: {logged_cal} | C: {logged_carbs}g | P: {logged_protein}g | F: {logged_fat}g"
                    )
                    db.add(log)
                    db.commit()
                    db.close()
                    del st.session_state.recipe_nutrition
                    st.session_state.recipe_form_submitted = False
                    st.success(f"✅ Logged: {recipe_name} ({logged_cal} cal)")
                    st.rerun()
        
        if st.button("Clear Recipe"):
            del st.session_state.recipe_nutrition
            st.session_state.recipe_form_submitted = False
            st.rerun()
    
    st.markdown("---")
    
    # Manual food logging
    st.subheader("✏️ Manual Entry")
    
    with st.form("food_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Food Name")
            carbs = st.number_input("Carbs (g)", min_value=0.0, value=0.0, step=1.0)
        with col2:
            meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
        notes = st.text_area("Notes")
        
        if st.form_submit_button("Log Food"):
            # Validate
            if not name.strip():
                st.error("Please enter a food name")
            else:
                db = Session()
                log = FoodLog(
                    user_id=st.session_state.user_id,
                    name=name,
                    carbs=carbs,
                    meal_type=meal_type.lower(),
                    notes=notes
                )
                db.add(log)
                db.commit()
                db.close()
                st.session_state.food_saved = True
                st.success("✅ Food logged!")
                st.rerun()
    
    # Show success message if just saved
    if st.session_state.get("food_saved"):
        st.session_state.food_saved = False
        st.info("✅ Food saved!")
    
    st.markdown("---")
    st.subheader("📝 Today's Food")
    
    # Initialize session state for edit/delete actions
    if "delete_food_id" not in st.session_state:
        st.session_state.delete_food_id = None
    if "edit_food_id" not in st.session_state:
        st.session_state.edit_food_id = None
    
    db = Session()
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    
    logs = db.query(FoodLog).filter(
        FoodLog.user_id == st.session_state.user_id,
        FoodLog.timestamp >= today_start
    ).order_by(FoodLog.timestamp.desc()).all()
    
    # Handle delete confirmation
    if st.session_state.delete_food_id:
        log_to_delete = db.query(FoodLog).filter(FoodLog.id == st.session_state.delete_food_id).first()
        if log_to_delete:
            st.warning(f"🗑️ Delete **{log_to_delete.name}** ({log_to_delete.carbs}g carbs)?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Delete", key="confirm_delete"):
                    db.delete(log_to_delete)
                    db.commit()
                    st.success("✅ Entry deleted!")
                    st.session_state.delete_food_id = None
                    db.close()
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key="cancel_delete"):
                    st.session_state.delete_food_id = None
                    db.close()
                    st.rerun()
        else:
            st.session_state.delete_food_id = None
            db.close()
            st.rerun()
    
    # Handle edit form
    if st.session_state.edit_food_id:
        log_to_edit = db.query(FoodLog).filter(FoodLog.id == st.session_state.edit_food_id).first()
        if log_to_edit:
            with st.expander("✏️ Edit Food Entry", expanded=True):
                with st.form(f"edit_food_form_{log_to_edit.id}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_name = st.text_input("Food Name", value=log_to_edit.name)
                        edit_carbs = st.number_input("Carbs (g)", min_value=0.0, value=float(log_to_edit.carbs or 0), step=1.0)
                    with col2:
                        edit_meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"], 
                            index=["breakfast", "lunch", "dinner", "snack"].index(log_to_edit.meal_type) if log_to_edit.meal_type in ["breakfast", "lunch", "dinner", "snack"] else 0)
                    edit_notes = st.text_area("Notes", value=log_to_edit.notes or "")
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.form_submit_button("💾 Save Changes"):
                            log_to_edit.name = edit_name
                            log_to_edit.carbs = edit_carbs
                            log_to_edit.meal_type = edit_meal_type.lower()
                            log_to_edit.notes = edit_notes
                            db.commit()
                            st.success("✅ Entry updated!")
                            st.session_state.edit_food_id = None
                            db.close()
                            st.rerun()
                    with col_cancel:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.edit_food_id = None
                            db.close()
                            st.rerun()
        else:
            st.session_state.edit_food_id = None
            db.close()
            st.rerun()
    
    if logs:
        total_carbs = sum(log.carbs or 0 for log in logs)
        st.metric("Total Carbs Today", f"{total_carbs}g")
        
        # Display each food entry with edit and delete buttons
        for log in logs:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                with col1:
                    st.write(f"**{log.name}**")
                with col2:
                    st.caption(f"🕐 {log.timestamp.strftime('%I:%M %p')} • {log.meal_type}: {log.carbs}g carbs")
                with col3:
                    if st.button("✏️", key=f"edit_{log.id}", help="Edit entry"):
                        st.session_state.edit_food_id = log.id
                        st.rerun()
                with col4:
                    if st.button("🗑️", key=f"delete_{log.id}", help="Delete entry"):
                        st.session_state.delete_food_id = log.id
                        st.rerun()
                if log.notes:
                    st.caption(f"📝 {log.notes}")
                st.divider()
    else:
        st.info("No food logged today")
    
    db.close()

# =============================================================================
# MEDICATION PAGE
# =============================================================================
def medication_page():
    st.title("💊 Medications")
    
    db = Session()
    user = db.query(User).filter(User.id == st.session_state.user_id).first()
    
    # Current meds display
    col1, col2 = st.columns(2)
    with col1:
        if user.glp1_medication:
            st.metric("💉 GLP-1", user.glp1_medication, user.glp1_dosage)
        else:
            st.metric("💉 GLP-1", "Not set")
    with col2:
        if user.other_diabetes_med:
            st.metric("💊 Diabetes", user.other_diabetes_med)
        else:
            st.metric("💊 Diabetes", "Not set")
    
    st.markdown("---")
    
    # ============== SET MEDICATIONS ==============
    with st.expander("⚙️ Set Your Medications", expanded=True):
        with st.form("set_meds_form"):
            col1, col2 = st.columns(2)
            with col1:
                # Handle case where saved med isn't in list
                glp1_default = 0
                if user.glp1_medication and user.glp1_medication in GLP1_MEDICATIONS:
                    glp1_default = GLP1_MEDICATIONS.index(user.glp1_medication) + 1
                glp1 = st.selectbox("💉 GLP-1", [""] + GLP1_MEDICATIONS, index=glp1_default)
            with col2:
                glp1_dose_default = 0
                if user.glp1_dosage and user.glp1_dosage in GLP1_DOSAGES:
                    glp1_dose_default = GLP1_DOSAGES.index(user.glp1_dosage) + 1
                glp1_dose = st.selectbox("Dosage", [""] + GLP1_DOSAGES, index=glp1_dose_default)
            
            col3, col4 = st.columns(2)
            with col3:
                other_default = 0
                if user.other_diabetes_med and user.other_diabetes_med in DIABETES_MEDICATIONS:
                    other_default = DIABETES_MEDICATIONS.index(user.other_diabetes_med) + 1
                other_med = st.selectbox("💊 Other Diabetes", [""] + DIABETES_MEDICATIONS, index=other_default)
            with col4:
                other_dose = st.text_input("Other Dosage", value="")
            
            if st.form_submit_button("💾 Save"):
                user.glp1_medication = glp1 if glp1 else None
                user.glp1_dosage = glp1_dose if glp1_dose else None
                user.other_diabetes_med = other_med if other_med else None
                db.commit()
                st.success("✅ Saved!")
                st.rerun()
    
    st.markdown("---")
    
    # ============== FEATURE 1: QUICK ADD ==============
    st.subheader("⚡ Quick Add")
    
    # Get user's medication history (previous med+dose combinations)
    med_history = db.query(MedicationHistory).filter(
        MedicationHistory.user_id == st.session_state.user_id
    ).order_by(MedicationHistory.last_used.desc()).limit(10).all()
    
    # Also include user's current saved medications
    quick_add_options = []
    if user.glp1_medication:
        quick_add_options.append({
            "medication": user.glp1_medication,
            "dosage": user.glp1_dosage,
            "source": "Current GLP-1"
        })
    if user.other_diabetes_med:
        quick_add_options.append({
            "medication": user.other_diabetes_med,
            "dosage": user.other_diabetes_med,
            "source": "Current Diabetes Med"
        })
    
    # Add from history
    for h in med_history:
        existing = any(o["medication"] == h.medication and o.get("dosage") == h.dosage for o in quick_add_options)
        if not existing:
            quick_add_options.append({
                "medication": h.medication,
                "dosage": h.dosage,
                "source": f"Previous (used {h.use_count}x)"
            })
    
    if quick_add_options:
        # Create display options for the selectbox
        display_options = ["➕ Add New Medication..."]
        for opt in quick_add_options:
            dose_str = f" - {opt['dosage']}" if opt.get('dosage') else ""
            display_options.append(f"{opt['medication']}{dose_str} ({opt['source']})")
        
        # Quick add section
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_quick = st.selectbox("Select from previous medications", display_options, key="quick_select")
        with col2:
            st.write("")  # spacer
            st.write("")  # spacer
            if st.button("✅ Quick Log", key="quick_log_btn"):
                if selected_quick != "➕ Add New Medication...":
                    # Parse the selected option
                    selected_idx = display_options.index(selected_quick) - 1
                    opt = quick_add_options[selected_idx]
                    
                    # Log the medication
                    log = MedicationLog(
                        user_id=st.session_state.user_id,
                        medication=opt["medication"],
                        dosage=opt.get("dosage"),
                        taken=1
                    )
                    db.add(log)
                    
                    # Update or create history entry
                    existing_hist = db.query(MedicationHistory).filter(
                        MedicationHistory.user_id == st.session_state.user_id,
                        MedicationHistory.medication == opt["medication"],
                        MedicationHistory.dosage == opt.get("dosage")
                    ).first()
                    
                    if existing_hist:
                        existing_hist.last_used = datetime.now()
                        existing_hist.use_count += 1
                    else:
                        hist = MedicationHistory(
                            user_id=st.session_state.user_id,
                            medication=opt["medication"],
                            dosage=opt.get("dosage"),
                            last_used=datetime.now(),
                            use_count=1
                        )
                        db.add(hist)
                    
                    db.commit()
                    st.success(f"✅ Logged {opt['medication']}!")
                    st.rerun()
        
        # Quick add ALL at once - for users taking 3-4 meds together
        st.markdown("---")
        st.markdown("**Or log ALL your daily medications at once:**")
        
        # Show toggle options for each med
        cols = st.columns(len(quick_add_options)) if quick_add_options else st.columns(1)
        
        meds_to_log_all = []
        for i, opt in enumerate(quick_add_options):
            with cols[i % len(cols)]:
                dose_str = f" - {opt['dosage']}" if opt.get('dosage') else ""
                checked = st.checkbox(f"{opt['medication']}{dose_str}", value=True, key=f"log_all_{i}")
                if checked:
                    meds_to_log_all.append(opt)
        
        if meds_to_log_all and st.button("📝 Log All Selected", key="log_all_btn"):
            for opt in meds_to_log_all:
                log = MedicationLog(
                    user_id=st.session_state.user_id,
                    medication=opt["medication"],
                    dosage=opt.get("dosage"),
                    taken=1
                )
                db.add(log)
                
                # Update history
                existing_hist = db.query(MedicationHistory).filter(
                    MedicationHistory.user_id == st.session_state.user_id,
                    MedicationHistory.medication == opt["medication"],
                    MedicationHistory.dosage == opt.get("dosage")
                ).first()
                
                if existing_hist:
                    existing_hist.last_used = datetime.now()
                    existing_hist.use_count += 1
                else:
                    hist = MedicationHistory(
                        user_id=st.session_state.user_id,
                        medication=opt["medication"],
                        dosage=opt.get("dosage"),
                        last_used=datetime.now(),
                        use_count=1
                    )
                    db.add(hist)
            
            db.commit()
            logged_names = ", ".join([m["medication"] for m in meds_to_log_all])
            st.success(f"✅ Logged all: {logged_names}")
            st.rerun()
    else:
        st.info("Set your medications above to enable quick add")
    
    st.markdown("---")
    
    # ============== FEATURE 2: MEDICATION REMINDERS ==============
    st.subheader("⏰ Medication Reminders")
    
    # Get existing reminders
    reminders = db.query(MedicationReminder).filter(
        MedicationReminder.user_id == st.session_state.user_id
    ).all()
    
    # Calculate and show next dose for GLP-1 (weekly medications)
    if user.glp1_medication:
        # Get last GLP-1 log
        last_glp1 = db.query(MedicationLog).filter(
            MedicationLog.user_id == st.session_state.user_id,
            MedicationLog.medication.like(f"%{user.glp1_medication.split()[0]}%"),
            MedicationLog.taken == 1
        ).order_by(MedicationLog.timestamp.desc()).first()
        
        if last_glp1:
            # GLP-1 is typically weekly
            next_dose = last_glp1.timestamp + timedelta(days=7)
            days_until = (next_dose - datetime.now()).days
            
            if days_until >= 0:
                st.info(f"💉 **Next dose of {user.glp1_medication}:** {next_dose.strftime('%A, %b %d at %I:%M %p')} ({days_until} days)")
            else:
                st.warning(f"💉 **Due for {user.glp1_medication}!** Last dose was {abs(days_until)} days ago")
        else:
            st.info(f"💉 Log your first dose of {user.glp1_medication} to track your schedule")
    
    # Show active reminders
    if reminders:
        st.markdown("**Your active reminders:**")
        for rem in reminders:
            if rem.is_active:
                day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                day_str = day_names[rem.reminder_day] if rem.reminder_day is not None else "Not set"
                time_str = rem.reminder_time or "Not set"
                st.write(f"📅 **{rem.medication}** - {day_str} at {time_str}")
    else:
        st.info("No reminders set. Add one below!")
    
    # Add/Edit reminder form
    with st.expander("➕ Set Medication Reminder"):
        with st.form("reminder_form"):
            # Select medication for reminder
            reminder_med = st.selectbox("Medication", 
                [user.glp1_medication, user.other_diabetes_med] if user.glp1_medication or user.other_diabetes_med else [""])
            
            reminder_dose = st.text_input("Dosage (optional)", placeholder="e.g., 5mg")
            
            col1, col2 = st.columns(2)
            with col1:
                reminder_day = st.selectbox("Day of Week", 
                    list(range(7)), 
                    format_func=lambda x: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][x],
                    index=0)
            with col2:
                reminder_time = st.time_input("Time", value=None)
            
            # Determine if GLP-1 (weekly) or daily med
            is_weekly = st.checkbox("Weekly medication (like Ozempic, Wegovy, Mounjaro)", value=True)
            
            if st.form_submit_button("🔔 Set Reminder"):
                if reminder_med:
                    # Check if reminder already exists
                    existing_reminder = db.query(MedicationReminder).filter(
                        MedicationReminder.user_id == st.session_state.user_id,
                        MedicationReminder.medication == reminder_med
                    ).first()
                    
                    if existing_reminder:
                        # Update existing
                        existing_reminder.reminder_day = reminder_day
                        existing_reminder.reminder_time = reminder_time.strftime("%H:%M") if reminder_time else None
                        existing_reminder.is_active = 1
                    else:
                        # Create new
                        new_reminder = MedicationReminder(
                            user_id=st.session_state.user_id,
                            medication=reminder_med,
                            dosage=reminder_dose,
                            reminder_day=reminder_day,
                            reminder_time=reminder_time.strftime("%H:%M") if reminder_time else None,
                            is_active=1
                        )
                        db.add(new_reminder)
                    
                    db.commit()
                    freq = "weekly" if is_weekly else "daily"
                    st.success(f"✅ Reminder set for {reminder_med} ({freq}) on {['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][reminder_day]} at {reminder_time.strftime('%I:%M %p') if reminder_time else 'N/A'}!")
                    st.rerun()
                else:
                    st.warning("Please select a medication first")
    
    # Show option to delete reminders
    if reminders:
        with st.expander("🗑️ Manage Reminders"):
            for rem in reminders:
                col1, col2 = st.columns([3, 1])
                with col1:
                    day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                    day_str = day_names[rem.reminder_day] if rem.reminder_day is not None else "Not set"
                    time_str = rem.reminder_time or "Not set"
                    status = "✅ Active" if rem.is_active else "❌ Inactive"
                    st.write(f"{rem.medication} - {day_str} at {time_str} ({status})")
                with col2:
                    if st.button("Delete", key=f"del_rem_{rem.id}"):
                        db.delete(rem)
                        db.commit()
                        st.rerun()
    
    st.markdown("---")
    
    # ============== LOG DOSE (Standard) ==============
    st.subheader("✅ Log Today's Dose (Manual)")
    
    # Build user's med list
    user_meds = []
    if user.glp1_medication:
        user_meds.append(f"💉 {user.glp1_medication}")
    if user.other_diabetes_med:
        user_meds.append(f"💊 {user.other_diabetes_med}")
    
    if not user_meds:
        st.warning("Set medications above first!")
    else:
        with st.form("log_dose_form"):
            col1, col2 = st.columns(2)
            with col1:
                log_med = st.selectbox("Medication", user_meds)
            with col2:
                log_dose = st.text_input("Dosage", placeholder="e.g., 5mg")
            
            taken = st.checkbox("Taken today", value=True)
            
            if st.form_submit_button("📝 Log"):
                med_name = log_med.replace("💉 ", "").replace("💊 ", "")
                log = MedicationLog(
                    user_id=st.session_state.user_id,
                    medication=med_name,
                    dosage=log_dose if log_dose else user.glp1_dosage,
                    taken=1 if taken else 0
                )
                db.add(log)
                
                # Update medication history
                existing_hist = db.query(MedicationHistory).filter(
                    MedicationHistory.user_id == st.session_state.user_id,
                    MedicationHistory.medication == med_name
                ).first()
                
                if existing_hist:
                    existing_hist.last_used = datetime.now()
                    existing_hist.use_count += 1
                else:
                    hist = MedicationHistory(
                        user_id=st.session_state.user_id,
                        medication=med_name,
                        dosage=log_dose if log_dose else user.glp1_dosage,
                        last_used=datetime.now(),
                        use_count=1
                    )
                    db.add(hist)
                
                db.commit()
                st.success(f"✅ Logged {med_name}!")
                st.rerun()
    
    # History
    st.markdown("---")
    st.subheader("📝 Recent History")
    
    logs = db.query(MedicationLog).filter(
        MedicationLog.user_id == st.session_state.user_id
    ).order_by(MedicationLog.timestamp.desc()).limit(14).all()
    db.close()
    
    if logs:
        for log in logs:
            status = "✅" if log.taken else "⏳"
            st.write(f"{status} {log.timestamp.strftime('%m/%d')} - {log.medication} {log.dosage or ''}")
    else:
        st.info("No logs yet")
        st.info("No medication logs yet")

# =============================================================================
# SIDE EFFECTS PAGE
# =============================================================================
def side_effects_page():
    st.title("🤢 Side Effects Tracker")
    
    with st.form("side_effect_form"):
        symptom = st.selectbox("Symptom", [
            "Nausea", "Diarrhea", "Constipation", "Stomach Pain", 
            "Headache", "Fatigue", "Dizziness", "Burping",
            "Injection Site Reaction", "Reduced Appetite", "Indigestion", "Other"
        ])
        severity = st.select_slider("Severity", options=["Mild", "Moderate", "Severe"])
        notes = st.text_area("Notes")
        
        if st.form_submit_button("Log Side Effect"):
            db = Session()
            effect = SideEffect(
                user_id=st.session_state.user_id,
                symptom=symptom,
                severity=severity.lower(),
                notes=notes
            )
            db.add(effect)
            db.commit()
            db.close()
            st.session_state.sideeffect_saved = True
            st.success("✅ Side effect logged!")
            st.rerun()
    
    # Show success message if just saved
    if st.session_state.get("sideeffect_saved"):
        st.session_state.sideeffect_saved = False
        st.info("✅ Side effect saved!")
    
    st.markdown("---")
    st.subheader("📝 Recent Side Effects")
    
    db = Session()
    effects = db.query(SideEffect).filter(
        SideEffect.user_id == st.session_state.user_id
    ).order_by(SideEffect.timestamp.desc()).limit(20).all()
    db.close()
    
    if effects:
        for effect in effects:
            sev_icon = "🟢" if effect.severity == "mild" else "🟡" if effect.severity == "moderate" else "🔴"
            st.write(f"{sev_icon} {effect.timestamp.strftime('%Y-%m-%d')} - {effect.symptom} ({effect.severity})")
    else:
        st.info("No side effects logged")

# =============================================================================
# SETTINGS PAGE
# =============================================================================
def settings_page():
    st.title("⚙️ Settings")
    
    db = Session()
    user = db.query(User).filter(User.id == st.session_state.user_id).first()
    
    with st.form("settings_form"):
        name = st.text_input("Name", value=user.name or "")
        
        st.markdown("**GLP-1 Medication**")
        glp1_med = st.selectbox("GLP-1", 
            ["", "Mounjaro (tirzepatide)", "Zepbound (tirzepatide)",
             "Ozempic (semaglutide)", "Wegovy (semaglutide)",
             "Trulicity (dulaglutide)", "Bydureon (exenatide)",
             "Victoza (liraglutide)", "Saxenda (liraglutide)",
             "Rybelsus (semaglutide)", "Other GLP-1"],
            index=0)
        
        st.markdown("**Other Diabetes Meds**")
        other_med = st.selectbox("Other Meds", 
            ["", "Metformin (Glucophage)", "Metformin ER",
             "Glipizide", "Glyburide", "Glimepiride",
             "Jardiance (empagliflozin)", "Invokana (canagliflozin)", 
             "Farxiga (dapagliflozin)",
             "Januvia (sitagliptin)", "Tradjenta (linagliptin)",
             "Actos (pioglitazone)",
             "Prandin (repaglinide)",
             "Lantus (insulin glargine)", "Novolog (insulin aspart)",
             "Humalog (insulin lispro)", "Toujeo", "Tresiba",
             "Other Insulin", "Other Diabetes Medication"],
            index=0)
        
        glp1_dosage = st.text_input("GLP-1 Dosage", value=user.glp1_dosage or "")
        
        st.markdown("### Targets")
        col1, col2 = st.columns(2)
        with col1:
            target_min = st.number_input("Target Glucose Min", value=user.target_glucose_min or 80)
        with col2:
            target_max = st.number_input("Target Glucose Max", value=user.target_glucose_max or 130)
        
        goal_weight = st.number_input("Goal Weight (lbs)", value=user.goal_weight or 170.0, step=0.1)
        
        if st.form_submit_button("Save Settings"):
            user.name = name
            user.glp1_medication = glp1_med
            user.glp1_dosage = glp1_dosage
            user.other_diabetes_med = other_med
            user.target_glucose_min = target_min
            user.target_glucose_max = target_max
            user.goal_weight = goal_weight
            db.commit()
            st.success("Settings saved!")
            st.session_state.user_name = name
        db.close()
    
    # ========== PDF EXPORT SECTION ==========
    st.markdown("---")
    st.subheader("📄 Export Health Report")
    st.write("Generate a PDF report of your health data for doctor visits")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        date_range = st.selectbox("Date Range", 
            [("7", "Last 7 days"), ("14", "Last 14 days"), 
             ("30", "Last 30 days"), ("60", "Last 60 days"), 
             ("90", "Last 90 days")],
            index=2,
            format_func=lambda x: x[1])
    
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        generate_btn = st.button("📥 Generate PDF Report", type="primary")
    
    if generate_btn:
        with st.spinner("Generating PDF report..."):
            try:
                db = Session()
                user = db.query(User).filter(User.id == st.session_state.user_id).first()
                
                # Validate user object and required fields
                if not user:
                    db.close()
                    st.error("❌ User account not found. Please log out and log back in.")
                    st.stop()
                
                # Check for missing required fields and provide defaults
                if not user.name:
                    st.warning("⚠️ Your profile is missing a name. The report will show 'Not provided'.")
                if not user.diabetes_type:
                    user.diabetes_type = "Type 2"  # Default
                
                # Get date range
                days = int(date_range[0])
                start_date = datetime.now() - timedelta(days=days)
                
                # Fetch all data
                glucose_logs = db.query(GlucoseLog).filter(
                    GlucoseLog.user_id == st.session_state.user_id,
                    GlucoseLog.timestamp >= start_date
                ).order_by(GlucoseLog.timestamp.desc()).all()
                
                weight_logs = db.query(WeightLog).filter(
                    WeightLog.user_id == st.session_state.user_id,
                    WeightLog.timestamp >= start_date
                ).order_by(WeightLog.timestamp.desc()).all()
                
                medication_logs = db.query(MedicationLog).filter(
                    MedicationLog.user_id == st.session_state.user_id,
                    MedicationLog.timestamp >= start_date
                ).order_by(MedicationLog.timestamp.desc()).all()
                
                side_effects = db.query(SideEffect).filter(
                    SideEffect.user_id == st.session_state.user_id,
                    SideEffect.timestamp >= start_date
                ).order_by(SideEffect.timestamp.desc()).all()
                
                db.close()
                
                # Validate data and warn about empty datasets
                data_warnings = []
                if not glucose_logs:
                    data_warnings.append("No glucose logs found in the selected period")
                if not weight_logs:
                    data_warnings.append("No weight logs found in the selected period")
                if not medication_logs:
                    data_warnings.append("No medication logs found in the selected period")
                if not side_effects:
                    data_warnings.append("No side effects reported in the selected period")
                
                # Show warnings if no data found
                if data_warnings:
                    with st.expander("⚠️ Data Warnings - Click to see"):
                        for warning in data_warnings:
                            st.write(f"• {warning}")
                        st.info("💡 Tip: Log some data before generating a report for more useful results.")
                
                # Generate PDF
                try:
                    pdf_bytes = generate_health_report(
                        user=user,
                        glucose_logs=glucose_logs,
                        weight_logs=weight_logs,
                        medication_logs=medication_logs,
                        side_effects=side_effects,
                        date_range_days=days
                    )
                except Exception as pdf_error:
                    st.error(f"❌ Failed to generate PDF: {pdf_error}")
                    import traceback
                    st.code(traceback.format_exc())
                    st.stop()
                
                # Create filename
                filename = f"GLP1Companion_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
                
                # Show success message
                st.success("✅ Report generated successfully!")
                
                # Show download button
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_bytes.getvalue(),
                    file_name=filename,
                    mime="application/pdf"
                )
                
                # Show summary
                with st.expander("📋 Report Summary"):
                    st.write(f"**Date Range:** Last {days} days")
                    st.write(f"**Glucose Readings:** {len(glucose_logs)}")
                    st.write(f"**Weight Readings:** {len(weight_logs)}")
                    st.write(f"**Medication Logs:** {len(medication_logs)}")
                    st.write(f"**Side Effects:** {len(side_effects)}")
                    
            except Exception as e:
                st.error(f"❌ Error generating report: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    st.markdown("---")
    st.subheader("⭐ Upgrade to Pro")
    
    st.markdown("""
    **GLP1Companion Pro** - $9.99/month
    
    - ✅ Unlimited data history
    - ✅ AI-powered health insights
    - ✅ PDF export for doctor visits
    - ✅ Proactive medication reminders
    - ✅ All future Pro features
    """)
    
    # Stripe payment link
    stripe_link = "https://buy.stripe.com/test_fZu7sNctp0TVedb7PE8g000"
    st.markdown(f"[**Click here to upgrade to Pro →**]({stripe_link})")
    
    st.markdown("---")
    st.subheader("🔐 Account")
    if st.button("Logout"):
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.rerun()

# =============================================================================
# AI CHAT PAGE
# =============================================================================
def get_user_context():
    """Get user's health data for AI context"""
    db = Session()
    
    # User info
    user = db.query(User).filter(User.id == st.session_state.user_id).first()
    
    # Recent glucose (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    glucose_logs = db.query(GlucoseLog).filter(
        GlucoseLog.user_id == st.session_state.user_id,
        GlucoseLog.timestamp >= week_ago
    ).order_by(GlucoseLog.timestamp.desc()).all()
    
    # Recent weight (last 30 days)
    month_ago = datetime.now() - timedelta(days=30)
    weight_logs = db.query(WeightLog).filter(
        WeightLog.user_id == st.session_state.user_id,
        WeightLog.timestamp >= month_ago
    ).order_by(WeightLog.timestamp.desc()).all()
    
    # Current medications
    med_logs = db.query(MedicationLog).filter(
        MedicationLog.user_id == st.session_state.user_id
    ).order_by(MedicationLog.timestamp.desc()).limit(10).all()
    
    # Recent side effects
    side_effects = db.query(SideEffect).filter(
        SideEffect.user_id == st.session_state.user_id,
        SideEffect.timestamp >= month_ago
    ).order_by(SideEffect.timestamp.desc()).all()
    
    # Recent food logs
    food_logs = db.query(FoodLog).filter(
        FoodLog.user_id == st.session_state.user_id,
        FoodLog.timestamp >= week_ago
    ).order_by(FoodLog.timestamp.desc()).limit(20).all()
    
    db.close()
    
    # Build context string
    context = f"""User: {user.name or 'User'}
Diabetes Type: {user.diabetes_type or 'Type 2'}
GLP-1 Medication: {user.glp1_medication or 'Not set'} {user.glp1_dosage or ''}
Other Diabetes Meds: {user.other_diabetes_med or 'Not set'}
Target Glucose: {user.target_glucose_min}-{user.target_glucose_max} mg/dL
Goal Weight: {user.goal_weight or 'Not set'} lbs

RECENT GLUCOSE READINGS (last 7 days):
"""
    if glucose_logs:
        for g in glucose_logs[:10]:
            context += f"- {g.timestamp.strftime('%Y-%m-%d %I:%M %p')}: {g.value} mg/dL ({g.context})\n"
    else:
        context += "No glucose readings in the past week.\n"
    
    context += "\nRECENT WEIGHT (last 30 days):\n"
    if weight_logs:
        for w in weight_logs[:5]:
            context += f"- {w.timestamp.strftime('%Y-%m-%d')}: {w.value} lbs\n"
    else:
        context += "No weight readings in the past month.\n"
    
    context += "\nGLP-1 MEDICATION LOG:\n"
    if med_logs:
        for m in med_logs[:5]:
            context += f"- {m.timestamp.strftime('%Y-%m-%d')}: {m.medication} {m.dosage or ''} {'✅ Taken' if m.taken else '⏳ Not taken'}\n"
    else:
        context += "No medication logs.\n"
    
    context += "\nRECENT SIDE EFFECTS (last 30 days):\n"
    if side_effects:
        for s in side_effects[:10]:
            context += f"- {s.timestamp.strftime('%Y-%m-%d')}: {s.symptom} ({s.severity})\n"
    else:
        context += "No side effects logged.\n"
    
    context += "\nRECENT FOOD LOGS (last 7 days):\n"
    if food_logs:
        for f in food_logs[:10]:
            context += f"- {f.timestamp.strftime('%Y-%m-%d %I:%M %p')}: {f.name} ({f.carbs}g carbs, {f.meal_type})\n"
    else:
        context += "No food logs in the past week.\n"
    
    return context


def generate_ai_response(user_message, user_context):
    """Generate AI response based on user message and context"""
    # Simple rule-based responses for demonstration
    # In production, you'd integrate with an actual LLM API
    
    user_message_lower = user_message.lower()
    
    # GLP-1 medication questions
    if any(word in user_message_lower for word in ["glp-1", "ozempic", "mounjaro", "wegovy", "zepbound", "medication", "dosage"]):
        return """I'm not a doctor, but I can share some general information about GLP-1 medications:

**Common GLP-1 Medications:**
- Ozempic (semaglutide) - once weekly injection
- Mounjaro (tirzepatide) - once weekly injection  
- Wegovy (semaglutide) - once weekly for weight loss
- Zepbound (tirzepatide) - once weekly for weight loss
- Rybelsus (semaglutide) - daily oral tablet

**General Tips:**
- Take your medication at the same time each week
- Stay hydrated to help reduce side effects
- Eat smaller meals to minimize nausea
- Contact your healthcare provider with any concerns

Remember to always follow your doctor's prescribed dosage and instructions!"""
    
    # Glucose questions
    elif any(word in user_message_lower for word in ["glucose", "blood sugar", "sugar"]):
        avg_glucose = "your recent readings"
        if user_context:
            # Extract average from context if available
            return """Great question about glucose! Here's what I know:

**General Glucose Guidelines:**
- Fasting: 80-130 mg/dL is typical target
- After meals (2 hours): Below 180 mg/dL is generally recommended
- Your personal targets may differ - check with your doctor!

**Tips for Managing Glucose:**
- Pair carbohydrates with protein and healthy fats
- Stay active after meals
- Monitor your glucose regularly
- Stay hydrated

Based on your logged data, you can track your patterns in the Glucose tab. If you see consistent highs or lows, definitely talk to your healthcare provider!"""
    
    # Weight questions
    elif any(word in user_message_lower for word in ["weight", "lose", "loss"]):
        return """Weight management is an important part of your journey! Here are some general tips:

**Healthy Weight Loss Tips:**
- Aim for 1-2 lbs per week (gradual is sustainable!)
- Focus on protein and fiber to feel full
- Stay hydrated - sometimes thirst is mistaken for hunger
- Get regular movement, even short walks help
- Prioritize sleep (7-9 hours)

**GLP-1 Benefits:**
Many GLP-1 medications can help with weight loss by:
- Reducing appetite
- Slowing digestion
- Helping you feel full longer

Keep tracking your weight in the app to see your progress over time!"""
    
    # Side effects questions
    elif any(word in user_message_lower for word in ["nausea", "side effect", "sick", "diarrhea", "constipation", "headache"]):
        return """Common GLP-1 side effects include:

**Most Common:**
- Nausea (usually improves over time)
- Diarrhea or constipation
- Stomach pain
- Headache
- Fatigue

**Tips to Minimize Side Effects:**
- Start with small meals
- Avoid fatty/fried foods initially
- Stay hydrated
- Don't lie down after eating
- Ginger tea or candies can help with nausea

**When to Contact Your Doctor:**
- Severe or persistent symptoms
- Signs of dehydration
- Any allergic reactions

Your side effect history is tracked in the app - bring this information to your appointments!"""
    
    # Food/nutrition questions
    elif any(word in user_message_lower for word in ["food", "eat", "meal", "carb", "carbs", "diet", "nutrition"]):
        return """Great question about nutrition! Here's some guidance:

**General Carb Guidelines:**
- Everyone's needs differ, but 45-60g carbs per meal is common
- Focus on complex carbs (whole grains, vegetables)
- Pair carbs with protein and healthy fats

**GLP-1 Friendly Foods:**
- Lean proteins (chicken,- Non fish, tofu)
-starchy vegetables
- Whole grains in moderation
- Healthy fats (avocado, nuts, olive oil)

**Foods to Limit:**
- Sugary drinks and desserts
- Highly processed foods
- Large portions

Track your meals in the Food tab to see how different foods affect you!"""
    
    # Exercise/activity questions
    elif any(word in user_message_lower for word in ["exercise", "workout", "activity", "walk", "move"]):
        return """Movement is great for managing diabetes! Here's some guidance:

**General Recommendations:**
- Aim for 150 minutes of moderate activity per week
- Include strength training 2-3 times/week
- Even short walks after meals help glucose control

**Tips:**
- Start slowly if you're new to exercise
- Stay hydrated
- Check glucose before and after exercise
- Have a snack ready if needed

**Safety:**
- Talk to your doctor before starting new exercise routines
- Stop if you feel dizzy or unwell

Find activities you enjoy - walking, swimming, dancing, yoga!"""
    
    # Greeting
    elif any(word in user_message_lower for word in ["hello", "hi", "hey", "help"]):
        return f"""Hello! 👋 I'm your GLP-1 Health Assistant!

I can help you with:
- Questions about your GLP-1 medication
- Understanding your glucose readings
- Weight management tips
- Managing side effects
- Nutrition and exercise guidance
- General diabetes health questions

Feel free to ask me anything! I have access to your recent health data to give you more personalized insights.

What would you like to know today?"""
    
    # Default helpful response
    else:
        return """I'd be happy to help you with your GLP-1 journey! Here are some things I can assist with:

📊 **Your Data:** I can analyze your glucose, weight, and medication logs
💊 **Medications:** Questions about GLP-1 drugs like Ozempic, Mounjaro, Wegovy
🤢 **Side Effects:** Tips for managing nausea and other common effects
🍎 **Nutrition:** Food and carb guidance
⚖️ **Weight:** Tips for healthy weight management
🏃 **Exercise:** Activity recommendations
💉 **Glucose:** Understanding your readings

What would you like to know more about? Just ask!"""


# =============================================================================
# PROACTIVE INSIGHTS
# =============================================================================
def get_proactive_insights():
    """Generate proactive insights based on user's health data"""
    db = Session()
    user = db.query(User).filter(User.id == st.session_state.user_id).first()
    
    insights = []
    warnings = []
    
    now = datetime.now()
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # 1. Glucose alerts
    glucose_logs = db.query(GlucoseLog).filter(
        GlucoseLog.user_id == st.session_state.user_id,
        GlucoseLog.timestamp >= week_ago
    ).all()
    
    if glucose_logs:
        highs = [g.value for g in glucose_logs if g.value > 180]
        lows = [g.value for g in glucose_logs if g.value < 70]
        
        if len(highs) > len(glucose_logs) * 0.3:
            warnings.append(f"⚠️ High glucose detected: {len(highs)} readings over 180 mg/dL this week")
        if lows:
            warnings.append(f"⚠️ Low glucose detected: {len(lows)} readings under 70 mg/dL")
        
        avg_glucose = sum(g.value for g in glucose_logs) / len(glucose_logs)
        if avg_glucose > user.target_glucose_max:
            insights.append(f"📈 Average glucose ({avg_glucose:.0f}) is above your target ({user.target_glucose_max})")
        elif avg_glucose < user.target_glucose_min:
            insights.append(f"📉 Average glucose ({avg_glucose:.0f}) is below your target ({user.target_glucose_min})")
        else:
            insights.append(f"✅ Average glucose ({avg_glucose:.0f}) is within your target range")
    
    # 2. Weight trends
    weight_logs = db.query(WeightLog).filter(
        WeightLog.user_id == st.session_state.user_id,
        WeightLog.timestamp >= month_ago
    ).order_by(WeightLog.timestamp.desc()).all()
    
    if len(weight_logs) >= 2:
        latest_weight = weight_logs[0].value
        oldest_weight = weight_logs[-1].value
        change = latest_weight - oldest_weight
        
        if change < -2:
            insights.append(f"⚖️ Great progress! You've lost {abs(change):.1f} lbs this month")
        elif change > 2:
            insights.append(f"📊 Weight increased by {change:.1f} lbs this month")
        
        if user.goal_weight and latest_weight <= user.goal_weight:
            insights.append("🎉 Congratulations! You've reached your goal weight!")
    
    # 3. Medication reminders
    med_logs = db.query(MedicationLog).filter(
        MedicationLog.user_id == st.session_state.user_id,
        MedicationLog.timestamp >= week_ago
    ).all()
    
    if not med_logs:
        warnings.append("💊 No GLP-1 medication logged this week")
    else:
        last_med = med_logs[0]
        if last_med.taken == 0:
            warnings.append("⏰ GLP-1 not marked as taken yet")
    
    # 4. Side effect patterns
    side_effects = db.query(SideEffect).filter(
        SideEffect.user_id == st.session_state.user_id,
        SideEffect.timestamp >= week_ago
    ).all()
    
    if side_effects:
        symptom_count = {}
        for s in side_effects:
            symptom_count[s.symptom] = symptom_count.get(s.symptom, 0) + 1
        
        for symptom, count in symptom_count.items():
            if count >= 3:
                warnings.append(f"🤢 '{symptom}' logged {count}x this week - consider talking to your doctor")
    
    # 5. Food logging
    food_logs = db.query(FoodLog).filter(
        FoodLog.user_id == st.session_state.user_id,
        FoodLog.timestamp >= today_start
    ).all()
    
    if len(food_logs) == 0:
        insights.append("🍎 No food logged today - helps to track meals for better insights")
    
    # Streak info
    total_glucose = db.query(GlucoseLog).filter(
        GlucoseLog.user_id == st.session_state.user_id
    ).count()
    total_weight = db.query(WeightLog).filter(
        WeightLog.user_id == st.session_state.user_id
    ).count()
    
    if total_glucose > 0:
        insights.append(f"💪 You've logged {total_glucose} glucose readings total!")
    
    db.close()
    
    return warnings, insights


# DEEP AI INSIGHTS AGENT
# =============================================================================
def get_deep_ai_insights(days=30):
    """Generate deep AI-powered insights with correlations"""
    import anthropic
    
    db = Session()
    user = db.query(User).filter(User.id == st.session_state.user_id).first()
    
    now = datetime.now()
    start_date = now - timedelta(days=days)
    
    # Gather all data
    glucose_logs = db.query(GlucoseLog).filter(
        GlucoseLog.user_id == st.session_state.user_id,
        GlucoseLog.timestamp >= start_date
    ).order_by(GlucoseLog.timestamp).all()
    
    weight_logs = db.query(WeightLog).filter(
        WeightLog.user_id == st.session_state.user_id,
        WeightLog.timestamp >= start_date
    ).order_by(WeightLog.timestamp).all()
    
    food_logs = db.query(FoodLog).filter(
        FoodLog.user_id == st.session_state.user_id,
        FoodLog.timestamp >= start_date
    ).order_by(FoodLog.timestamp).all()
    
    med_logs = db.query(MedicationLog).filter(
        MedicationLog.user_id == st.session_state.user_id,
        MedicationLog.timestamp >= start_date
    ).order_by(MedicationLog.timestamp).all()
    
    side_effects = db.query(SideEffect).filter(
        SideEffect.user_id == st.session_state.user_id,
        SideEffect.timestamp >= start_date
    ).order_by(SideEffect.timestamp).all()
    
    # Build data summary
    data_summary = f"""
USER PROFILE:
- GLP-1 Medication: {user.glp1_medication or 'Not set'}
- Dosage: {user.glp1_dosage or 'Not set'}
- Diabetes Type: {user.diabetes_type}
- Goal Weight: {user.goal_weight or 'Not set'} lbs
- Glucose Target Range: {user.target_glucose_min}-{user.target_glucose_max} mg/dL

GLUCOSE DATA ({len(glucose_logs)} readings):
"""
    
    if glucose_logs:
        glucose_values = [g.value for g in glucose_logs]
        data_summary += f"- Average: {sum(glucose_values)/len(glucose_values):.0f} mg/dL\n"
        data_summary += f"- Min: {min(glucose_values)}, Max: {max(glucose_values)}\n"
        data_summary += f"- High (>180): {len([v for v in glucose_values if v > 180])}, Low (<70): {len([v for v in glucose_values if v < 70])}\n"
    else:
        data_summary += "- No readings\n"
    
    data_summary += f"""
WEIGHT DATA ({len(weight_logs)} readings):
"""
    if weight_logs:
        weights = [w.value for w in weight_logs]
        data_summary += f"- Current: {weights[-1]:.1f} lbs, Start: {weights[0]:.1f} lbs\n"
        data_summary += f"- Change: {weights[-1] - weights[0]:.1f} lbs\n"
    else:
        data_summary += "- No readings\n"
    
    data_summary += f"""
MEDICATION LOGS ({len(med_logs)} entries):
"""
    if med_logs:
        for m in med_logs[-5:]:
            data_summary += f"- {m.timestamp.strftime('%Y-%m-%d')}: {m.medication} {'✓' if m.taken else '✗'}\n"
    else:
        data_summary += "- No logs\n"
    
    data_summary += f"""
SIDE EFFECTS ({len(side_effects)} entries):
"""
    if side_effects:
        symptoms = {}
        for s in side_effects:
            symptoms[s.symptom] = symptoms.get(s.symptom, 0) + 1
        for symptom, count in sorted(symptoms.items(), key=lambda x: -x[1])[:5]:
            data_summary += f"- {symptom}: {count} times\n"
    else:
        data_summary += "- No side effects logged\n"
    
    data_summary += f"""
FOOD LOGS ({len(food_logs)} entries):
"""
    if food_logs:
        total_carbs = sum(f.carbs or 0 for f in food_logs)
        data_summary += f"- Total carbs logged: {total_carbs}g\n"
        meal_types = {}
        for f in food_logs:
            meal_types[f.meal_type] = meal_types.get(f.meal_type, 0) + 1
        data_summary += f"- Meals: {meal_types}\n"
    else:
        data_summary += "- No food logged\n"
    
    db.close()
    
    # Send to AI for deep analysis
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return "Add ANTHROPIC_API_KEY to Streamlit secrets!"
        
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = f"""You are an expert diabetes and GLP-1 health analyst. Analyze this user's data from the past {days} days and find correlations and insights.

Focus on:
1. **GLP-1 specific patterns** - How does their medication timing affect glucose/weight/side effects?
2. **Food-glucose correlations** - What foods seem to spike their glucose?
3. **Side effect triggers** - Any patterns between meals, meds, and side effects?
4. **Weight loss patterns** - What's working, what's not?
5. **Actionable recommendations** - Specific suggestions based on their data

User Data:
{data_summary}

Respond with a detailed analysis in these sections:
## 🔍 Key Patterns Found
## 💊 GLP-1 Insights
## 🍎 Food Insights  
## 🤢 Side Effect Patterns
## ⚖️ Weight Trends
## ✅ Actionable Recommendations

Be specific with numbers and dates. If you don't have enough data, say so."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text
        
    except Exception as e:
        return f"Error generating insights: {e}"


def insights_page():
    st.title("💡 Proactive Insights")
    
    st.markdown("""
    These insights are generated based on your health data. 
    *Always consult your healthcare provider for medical advice.*
    """)
    
    warnings, insights = get_proactive_insights()
    
    # Warnings (alerts)
    if warnings:
        st.subheader("⚠️ Alerts")
        for warning in warnings:
            st.warning(warning)
    
    # Insights (positive/info)
    if insights:
        st.subheader("💡 Insights")
        for insight in insights:
            st.info(insight)
    
    if not warnings and not insights:
        st.info("Start logging your health data to receive personalized insights!")
    
    # Deep AI Analysis Section
    st.markdown("---")
    st.subheader("🤖 Deep AI Analysis")
    st.markdown("Get advanced insights with AI-powered correlation analysis of your GLP-1 medication, glucose, food, and side effects.")
    
    # Select time range
    col1, col2 = st.columns([2, 1])
    with col1:
        analysis_days = st.selectbox("Analysis period", [7, 14, 30, 60, 90], index=2, 
                                     format_func=lambda x: f"Last {x} days")
    with col2:
        analyze_btn = st.button("🔍 Analyze My Data", type="primary")
    
    if analyze_btn:
        with st.spinner(f"Analyzing your last {analysis_days} days of data..."):
            deep_insights = get_deep_ai_insights(days=analysis_days)
            st.session_state.deep_insights = deep_insights
            st.session_state.deep_insights_days = analysis_days
    
    # Display deep insights if available
    if "deep_insights" in st.session_state and st.session_state.get("deep_insights_days") == analysis_days:
        st.markdown("---")
        st.markdown(st.session_state.deep_insights)
        
        if st.button("🔄 Re-analyze"):
            del st.session_state.deep_insights
            st.rerun()
    
    # Manual refresh
    st.markdown("---")
    if st.button("🔄 Refresh Basic Insights"):
        st.rerun()


# =============================================================================
# GOOGLE FIT SYNC
# =============================================================================
def google_fit_sync_page():
    st.title("📱 Google Fit Sync")
    
    st.markdown("""
    Connect your Google Fit account to automatically import your health data!
    This includes glucose readings, weight, and activity data.
    """)
    
    # OAuth config
    CLIENT_ID = "1021511969744-pjoet0qke3do86jmhpu42l9e450ilv56.apps.googleusercontent.com"
    CLIENT_SECRET = "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"
    REDIRECT_URI = "https://share.streamlit.io/oauth/callback"
    
    SCOPES = [
        "https://www.googleapis.com/auth/fitness.body.read",
        "https://www.googleapis.com/auth/fitness.body.write",
        "https://www.googleapis.com/auth/fitness.activity.read",
        "https://www.googleapis.com/auth/fitness.nutrition.read",
        "https://www.googleapis.com/auth/fitness.nutrition.write",
        "https://www.googleapis.com/auth/fitness.sleep.read",
    ]
    
    # Build authorization URL
    import urllib.parse
    auth_params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(auth_params)
    
    # Check for OAuth callback in query params
    query_params = st.query_params
    
    if "code" in query_params:
        # OAuth callback - exchange code for tokens
        code = query_params["code"]
        
        with st.spinner("Connecting to Google Fit..."):
            # Exchange code for tokens
            import requests
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
            }
            
            try:
                token_response = requests.post(token_url, data=token_data)
                tokens = token_response.json()
                
                if "access_token" in tokens:
                    st.session_state.google_fit_connected = True
                    st.session_state.google_tokens = tokens
                    st.success("✅ Google Fit connected successfully!")
                    
                    # Clear the query params
                    st.query_params.clear()
                else:
                    st.error("Failed to connect: " + str(tokens))
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Show connection status
    if st.session_state.get("google_fit_connected"):
        st.success("✅ Google Fit is connected!")
        
        if st.button("🔄 Sync Data from Google Fit"):
            with st.spinner("Syncing data..."):
                sync_google_fit()
                st.success("Data synced!")
        
        if st.button("Disconnect Google Fit"):
            st.session_state.google_fit_connected = False
            st.session_state.google_tokens = None
            st.rerun()
    else:
        st.markdown(f"""
        ### Connect Google Fit
        
        Click the button below to authorize GLP1Companion to read your Google Fit data.
        
        [{'🔗 Connect Google Fit'}]({auth_url})
        
        *This will open Google's login page. After authorizing, you'll be redirected back to the app.*
        """)


def sync_google_fit():
    """Sync data from Google Fit to the app"""
    if not st.session_state.get("google_tokens"):
        st.error("Please connect Google Fit first!")
        return
    
    tokens = st.session_state.google_tokens
    access_token = tokens.get("access_token")
    
    import requests
    db = Session()
    
    now = datetime.now()
    start_time = int((now - timedelta(days=30)).timestamp() * 1000000000)
    end_time = int(now.timestamp() * 1000000000)
    
    fit_url = "https://fitness.googleapis.com/fitness/v1/users/me/datasets:aggregate"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    sync_results = []
    
    try:
        # 1. WEIGHT
        weight_payload = {
            "aggregateBy": [{
                "dataTypeName": "com.google.body.measurement.weight",
                "dataSourceId": "derived:com.google.weight:com.google.android.gms:estimated_weight"
            }],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": start_time,
            "endTimeMillis": end_time,
        }
        
        weight_response = requests.post(fit_url, json=weight_payload, headers=headers)
        if weight_response.status_code == 200:
            weight_data = weight_response.json()
            imported = 0
            for bucket in weight_data.get("bucket", []):
                for dataset in bucket.get("dataset", []):
                    for point in dataset.get("point", []):
                        weight_value = point.get("value", [{}])[0].get("fpVal")
                        if weight_value:
                            weight_lbs = weight_value * 2.20462
                            timestamp = int(point.get("startTimeMillis", 0)) / 1000
                            log_time = datetime.fromtimestamp(timestamp)
                            
                            existing = db.query(WeightLog).filter(
                                WeightLog.user_id == st.session_state.user_id,
                                WeightLog.timestamp >= log_time - timedelta(hours=1),
                                WeightLog.timestamp <= log_time + timedelta(hours=1)
                            ).first()
                            
                            if not existing:
                                log = WeightLog(
                                    user_id=st.session_state.user_id,
                                    value=round(weight_lbs, 1),
                                    timestamp=log_time
                                )
                                db.add(log)
                                imported += 1
            
            if imported > 0:
                db.commit()
                sync_results.append(f"✅ Weight: {imported} readings imported")
        
        # 2. STEPS
        steps_payload = {
            "aggregateBy": [{
                "dataTypeName": "com.google.step_count.delta",
                "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
            }],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": start_time,
            "endTimeMillis": end_time,
        }
        
        steps_response = requests.post(fit_url, json=steps_payload, headers=headers)
        if steps_response.status_code == 200:
            steps_data = steps_response.json()
            total_steps = 0
            for bucket in steps_data.get("bucket", []):
                for dataset in bucket.get("dataset", []):
                    for point in dataset.get("point", []):
                        steps = point.get("value", [{}])[0].get("intVal", 0)
                        total_steps += steps
            
            if total_steps > 0:
                sync_results.append(f"🚶 Steps (last 30 days): {total_steps:,}")
        
        # 3. DISTANCE
        distance_payload = {
            "aggregateBy": [{
                "dataTypeName": "com.google.distance.delta",
                "dataSourceId": "derived:com.google.distance.delta:com.google.android.gms:estimated_distance"
            }],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": start_time,
            "endTimeMillis": end_time,
        }
        
        distance_response = requests.post(fit_url, json=distance_payload, headers=headers)
        if distance_response.status_code == 200:
            distance_data = distance_response.json()
            total_distance = 0
            for bucket in distance_data.get("bucket", []):
                for dataset in bucket.get("dataset", []):
                    for point in dataset.get("point", []):
                        meters = point.get("value", [{}])[0].get("fpVal", 0)
                        total_distance += meters
            
            if total_distance > 0:
                miles = total_distance / 1609.34
                sync_results.append(f"📍 Distance (last 30 days): {miles:.1f} miles")
        
        # 4. CALORIES
        calories_payload = {
            "aggregateBy": [{
                "dataTypeName": "com.google.calories.expended",
                "dataSourceId": "derived:com.google.calories.expended:com.google.android.gms:estimated_calories_expended"
            }],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": start_time,
            "endTimeMillis": end_time,
        }
        
        calories_response = requests.post(fit_url, json=calories_payload, headers=headers)
        if calories_response.status_code == 200:
            calories_data = calories_response.json()
            total_calories = 0
            for bucket in calories_data.get("bucket", []):
                for dataset in bucket.get("dataset", []):
                    for point in dataset.get("point", []):
                        cal = point.get("value", [{}])[0].get("fpVal", 0)
                        total_calories += cal
            
            if total_calories > 0:
                sync_results.append(f"🔥 Calories burned (last 30 days): {total_calories:,.0f}")
        
        # 5. SLEEP
        sleep_payload = {
            "aggregateBy": [{
                "dataTypeName": "com.google.sleep.segment",
                "dataSourceId": "derived:com.google.sleep.segment:com.google.android.gms:sleep"
            }],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": start_time,
            "endTimeMillis": end_time,
        }
        
        sleep_response = requests.post(fit_url, json=sleep_payload, headers=headers)
        if sleep_response.status_code == 200:
            sleep_data = sleep_response.json()
            total_sleep_minutes = 0
            sleep_days = 0
            for bucket in sleep_data.get("bucket", []):
                for dataset in bucket.get("dataset", []):
                    for point in dataset.get("point", []):
                        start = int(point.get("startTimeNanos", 0)) / 60000000000
                        end = int(point.get("endTimeNanos", 0)) / 60000000000
                        duration = end - start
                        if duration > 0:
                            total_sleep_minutes += duration
                            sleep_days += 1
            
            if total_sleep_minutes > 0:
                avg_hours = (total_sleep_minutes / max(sleep_days, 1)) / 60
                sync_results.append(f"😴 Avg sleep: {avg_hours:.1f} hours/night")
        
        # 6. ACTIVITY (types like walking, running, cycling)
        activity_payload = {
            "aggregateBy": [{
                "dataTypeName": "com.google.activity_summary",
                "dataSourceId": "derived:com.google.activity_summary:com.google.android.gms:aggregates"
            }],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": start_time,
            "endTimeMillis": end_time,
        }
        
        # Show results
        if sync_results:
            for result in sync_results:
                st.success(result)
        else:
            st.info("No data found in Google Fit. Make sure you wear your device!")
    
    except Exception as e:
        st.error(f"Error syncing: {e}")
    
    db.close()


# =============================================================================
# DEXCOM CSV IMPORT
# =============================================================================
def dexcom_import_page():
    st.title("📥 Import Dexcom Data")
    
    st.markdown("""
    Upload your Dexcom Clarity CSV export to import glucose readings into the app.
    
    **Expected CSV format:**
    - Column: `Timestamp (YYYY-MM-DDThh:mm:ss)` (ISO format with 'T')
    - Column: `Glucose Value (mg/dL)`
    - Column: `Event Type` - only rows with Event Type = "EGV" are imported
    
    *Note: Download your data from Dexcom Clarity → Reports → Export Data*
    """)
    
    # Initialize session state for import
    if "dexcom_preview" not in st.session_state:
        st.session_state.dexcom_preview = None
    if "dexcom_data" not in st.session_state:
        st.session_state.dexcom_data = None
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a Dexcom CSV file",
        type=["csv"],
        help="Upload your Dexcom Clarity export CSV file"
    )
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            st.subheader("📄 File Preview")
            st.write(f"**Total rows in file:** {len(df)}")
            
            # Display raw data columns
            st.write(f"**Columns found:** {', '.join(df.columns.tolist())}")
            
            # Parse Dexcom CSV - find the right columns
            timestamp_col = None
            glucose_col = None
            event_type_col = None
            
            # Dexcom Clarity column names (exact format from export)
            timestamp_options = ['Timestamp (YYYY-MM-DDThh:mm:ss)', 'Timestamp']
            glucose_options = ['Glucose Value (mg/dL)', 'Glucose mg/dL', 'Glucose', 'Sensor Glucose (mg/dL)']
            event_type_options = ['Event Type']
            
            for col in df.columns:
                if not timestamp_col and col in timestamp_options:
                    timestamp_col = col
                if not glucose_col and col in glucose_options:
                    glucose_col = col
                if not event_type_col and col in event_type_options:
                    event_type_col = col
            
            # Check if required columns found
            errors = []
            if not timestamp_col:
                errors.append("❌ Could not find Timestamp column. Expected: 'Timestamp (YYYY-MM-DDThh:mm:ss)' or 'Timestamp'")
            if not glucose_col:
                errors.append("❌ Could not find Glucose column. Expected: 'Glucose Value (mg/dL)' or 'Glucose mg/dL'")
            
            if errors:
                for err in errors:
                    st.error(err)
                st.info("💡 Tip: Your CSV may have a different format. Check the column names in your file.")
                return
            
            # Filter for EGV (Estimated Glucose Value) rows only if Event Type column exists
            if event_type_col:
                df = df[df[event_type_col] == 'EGV'].copy()
                st.info(f"📋 Filtered to {len(df)} EGV rows (excluding metadata)")
            
            # Parse the data
            parsed_data = []
            for idx, row in df.iterrows():
                try:
                    # Parse ISO timestamp (format: 2026-01-27T08:22:28)
                    ts_str = str(row[timestamp_col]).strip()
                    ts = pd.to_datetime(ts_str, format='ISO8601', errors='coerce')
                    
                    # Handle if ISO parsing fails, try other common formats
                    if pd.isna(ts):
                        ts = pd.to_datetime(ts_str, errors='coerce')
                    
                    if pd.isna(ts):
                        continue  # Skip rows with invalid timestamps
                    
                    # Parse glucose value
                    glucose_val = row[glucose_col]
                    
                    # Handle different data types
                    if pd.isna(glucose_val) or str(glucose_val).strip() == '':
                        continue  # Skip empty rows
                    
                    glucose_val = int(float(glucose_val))
                    
                    # Validate glucose range
                    if glucose_val < 20 or glucose_val > 600:
                        continue  # Skip invalid values
                    
                    parsed_data.append({
                        'timestamp': ts,
                        'glucose': glucose_val
                    })
                except Exception as e:
                    # Skip problematic rows
                    continue
            
            if not parsed_data:
                st.error("❌ No valid glucose data found in the file.")
                return
            
            # Show preview
            preview_df = pd.DataFrame(parsed_data[:10])
            preview_df['timestamp'] = preview_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
            
            st.subheader("👀 Data Preview (first 10 rows)")
            st.dataframe(preview_df, use_container_width=True)
            
            # Show statistics
            st.subheader("📊 Import Summary")
            
            dates = [d['timestamp'] for d in parsed_data]
            min_date = min(dates)
            max_date = max(dates)
            glucose_values = [d['glucose'] for d in parsed_data]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Valid Rows Found", len(parsed_data))
            with col2:
                st.metric("Date Range", f"{min_date.strftime('%m/%d')} - {max_date.strftime('%m/%d')}")
            with col3:
                st.metric("Avg Glucose", f"{sum(glucose_values)/len(glucose_values):.0f} mg/dL")
            
            # Check for existing data in the date range
            db = Session()
            
            # Find overlapping timestamps
            existing_count = 0
            duplicate_timestamps = []
            
            for record in parsed_data:
                existing = db.query(GlucoseLog).filter(
                    GlucoseLog.user_id == st.session_state.user_id,
                    GlucoseLog.timestamp >= record['timestamp'] - timedelta(minutes=2),
                    GlucoseLog.timestamp <= record['timestamp'] + timedelta(minutes=2)
                ).first()
                
                if existing:
                    existing_count += 1
                    duplicate_timestamps.append(record['timestamp'])
            
            db.close()
            
            if existing_count > 0:
                st.warning(f"⚠️ Found {existing_count} readings that may already exist (within 2 minutes of existing data)")
            
            # Import button - use key to avoid form conflicts
            st.markdown("---")
            
            if st.button("✅ Import Data", type="primary", key="import_dexcom_data_btn"):
                db = Session()
                imported_count = 0
                skipped_count = 0
                
                for record in parsed_data:
                    try:
                        # Check for duplicate (within 2 minutes)
                        existing = db.query(GlucoseLog).filter(
                            GlucoseLog.user_id == st.session_state.user_id,
                            GlucoseLog.timestamp >= record['timestamp'] - timedelta(minutes=2),
                            GlucoseLog.timestamp <= record['timestamp'] + timedelta(minutes=2)
                        ).first()
                        
                        if existing:
                            skipped_count += 1
                            continue
                        
                        # Determine context based on time of day
                        hour = record['timestamp'].hour
                        if hour < 10:
                            context = 'fasting'
                        elif hour < 12:
                            context = 'before_meal'
                        elif hour < 17:
                            context = 'after_meal'
                        else:
                            context = 'bedtime'
                        
                        # Build notes for import
                        notes = "Imported from Dexcom Clarity"
                        
                        log = GlucoseLog(
                            user_id=st.session_state.user_id,
                            value=record['glucose'],
                            context=context,
                            notes=notes,
                            timestamp=record['timestamp']
                        )
                        db.add(log)
                        imported_count += 1
                        
                    except Exception as e:
                        skipped_count += 1
                        continue
                
                db.commit()
                db.close()
                
                # Show results
                st.success(f"✅ Successfully imported {imported_count} glucose readings!")
                
                if skipped_count > 0:
                    st.info(f"ℹ️ Skipped {skipped_count} duplicate readings")
                
                # Show date range of imported data
                if imported_count > 0:
                    st.success(f"📅 Data range: {min_date.strftime('%Y-%m-%d %I:%M %p')} to {max_date.strftime('%Y-%m-%d %I:%M %p')}")
                
                # Clear session state
                st.session_state.dexcom_preview = None
                st.session_state.dexcom_data = None
                
                # Offer to view imported data
                if st.button("📊 Go to Glucose Page", key="go_to_glucose_btn"):
                    st.switch_page("glucose")
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.info("Please make sure your file is a valid CSV format.")
    
    # Instructions
    st.markdown("---")
    with st.expander("📋 How to export from Dexcom Clarity"):
        st.markdown("""
        1. Log in to **Dexcom Clarity** (clarity.dexcom.com)
        2. Click on **Reports** in the left menu
        3. Select your date range (or choose "All Time")
        4. Click **Export** button
        5. Save the CSV file
        6. Upload the file here
        """)


def ai_chat_page():
    st.title("🤖 AI Health Assistant")
    
    st.markdown("""
    Welcome to your personal GLP-1 Health Assistant! Ask me anything about:
    - Your GLP-1 medication
    - Managing side effects
    - Nutrition and diet
    - Exercise recommendations
    - Understanding your glucose readings
    
    *Note: I'm an AI assistant, not a doctor. Always consult your healthcare provider for medical advice.*
    """)
    
    # Get user context
    user_context = get_user_context()
    
    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your GLP-1 journey..."):
        # Add user message to chat
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = generate_ai_response(prompt, user_context)
            st.markdown(response)
        
        # Add assistant message to chat
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
    
    # Clear chat button
    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_messages = []
        st.rerun()
    
    # Use columns for quick question buttons
    col1, col2, col3 = st.columns(3)
    
    # Use a unique key for each button to prevent double-firing
    with col1:
        if st.button("🍎 What foods should I eat?", key="quick_food"):
            # Add messages for this quick question
            question = "What foods should I eat on GLP-1?"
            st.session_state.chat_messages = st.session_state.get("chat_messages", [])
            st.session_state.chat_messages.append({"role": "user", "content": question})
            response = generate_ai_response(question, user_context)
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col2:
        if st.button("🤢 How to manage nausea?", key="quick_nausea"):
            question = "How to manage nausea?"
            st.session_state.chat_messages = st.session_state.get("chat_messages", [])
            st.session_state.chat_messages.append({"role": "user", "content": question})
            response = generate_ai_response(question, user_context)
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col3:
        if st.button("📊 Explain my glucose data", key="quick_glucose"):
            question = "Explain my glucose data"
            st.session_state.chat_messages = st.session_state.get("chat_messages", [])
            st.session_state.chat_messages.append({"role": "user", "content": question})
            response = generate_ai_response(question, user_context)
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            st.rerun()


# =============================================================================
# MAIN APP
# =============================================================================
def main():
    # Check if user is logged in
    if st.session_state.user_id is None:
        if "show_signup" not in st.session_state:
            st.session_state.show_signup = False
        if "show_reset" not in st.session_state:
            st.session_state.show_reset = False
        
        if st.session_state.show_reset:
            reset_password_page()
        elif st.session_state.show_signup:
            signup_page()
        else:
            login_page()
    else:
        # Top tab navigation
        st.markdown("---")
        tab_dashboard, tab_ai, tab_health, tab_medication, tab_settings = st.tabs([
            "📊 Dashboard", 
            "🤖 AI Chat", 
            "💪 Health", 
            "💊 Medication",
            "⚙️ Settings"
        ])
        
        with tab_dashboard:
            dashboard()
        
        with tab_ai:
            ai_chat_page()
            st.markdown("---")
            insights_page()
        
        with tab_health:
            weight_page()
            st.markdown("---")
            glucose_page()
            st.markdown("---")
            food_page()
        
        with tab_medication:
            medication_page()
            st.markdown("---")
            side_effects_page()
            st.markdown("---")
            dexcom_import_page()
            st.markdown("---")
            google_fit_sync_page()
        
        with tab_settings:
            settings_page()
            st.markdown("---")
            admin_page()

            admin_page()

# =============================================================================
# ADMIN PAGE
# =============================================================================
def admin_page():
    """Admin page showing user statistics and data overview."""
    st.title("🔧 Admin Dashboard")
    st.markdown("Overview of all users and their data.")
    
    db_session = Session()
    
    try:
        # Get total user count
        total_users = db_session.query(User).count()
        
        # Get all users
        users = db_session.query(User).all()
        
        # Get log counts
        glucose_count = db_session.query(GlucoseLog).count()
        weight_count = db_session.query(WeightLog).count()
        food_count = db_session.query(FoodLog).count()
        medication_count = db_session.query(MedicationLog).count()
        side_effect_count = db_session.query(SideEffect).count()
        
        # Display stats in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Users", total_users)
        
        with col2:
            st.metric("Total Glucose Logs", glucose_count)
            
        with col3:
            st.metric("Total Weight Logs", weight_count)
        
        col4, col5, col6 = st.columns(3)
        
        with col4:
            st.metric("Total Food Logs", food_count)
            
        with col5:
            st.metric("Total Medication Logs", medication_count)
            
        with col6:
            st.metric("Total Side Effects", side_effect_count)
        
        st.markdown("---")
        
        # User list
        st.subheader("👥 Registered Users")
        
        if users:
            user_data = []
            for user in users:
                # Count logs per user
                user_glucose = db_session.query(GlucoseLog).filter(GlucoseLog.user_id == user.id).count()
                user_weight = db_session.query(WeightLog).filter(WeightLog.user_id == user.id).count()
                user_food = db_session.query(FoodLog).filter(FoodLog.user_id == user.id).count()
                
                user_data.append({
                    "Email": user.email,
                    "Name": user.name or "N/A",
                    "GLP1 Medication": user.glp1_medication or "N/A",
                    "Dosage": user.glp1_dosage or "N/A",
                    "Start Date": user.start_date.strftime("%Y-%m-%d") if user.start_date else "N/A",
                    "Glucose Logs": user_glucose,
                    "Weight Logs": user_weight,
                    "Food Logs": user_food
                })
            
            df_users = pd.DataFrame(user_data)
            st.dataframe(df_users, use_container_width=True, hide_index=True)
        else:
            st.info("No users registered yet.")
            
    finally:
        db_session.close()

if __name__ == "__main__":
    main()
