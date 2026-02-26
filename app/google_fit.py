# Google Fit OAuth Configuration
# Add these to your Streamlit secrets

GOOGLE_CLIENT_ID = "1021511969744-pjoet0qke3do86jmhpu42l9e450ilv56.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"

# OAuth scopes for Google Fit
GOOGLE_FIT_SCOPES = [
    "https://www.googleapis.com/auth/fitness.body.read",
    "https://www.googleapis.com/auth/fitness.body.write",
    "https://www.googleapis.com/auth/fitness.nutrition.read",
    "https://www.googleapis.com/auth/fitness.nutrition.write",
    "https://www.googleapis.com/auth/fitness.activity.read",
]

# Redirect URI
REDIRECT_URI = "https://share.streamlit.io/oauth/callback"
