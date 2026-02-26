# GLP1Companion - Google Sheets Email Setup

## Quick Start

### Step 1: Create a Google Sheet
1. Go to sheets.google.com
2. Create a new sheet named "GLP1Companion Waitlist"
3. Add headers in row 1:
   - A1: `Timestamp`
   - B1: `Email`
   - C1: `Source`
4. Copy the Sheet ID from the URL (between `/d/` and `/edit`)

### Step 2: Create Google Apps Script
1. Go to script.google.com
2. Click "New Project"
3. Copy the code from `Code.gs` and paste it
4. Replace `YOUR_SHEET_ID_HERE` with your Sheet ID
5. Click Deploy > New deployment
6. Select "Web app"
7. Fill in:
   - Description: "GLP1Companion Email API"
   - Execute as: "Me"
   - Who has access: "Anyone"
8. Click Deploy
9. Copy the Web App URL

### Step 3: Update Landing Page
Replace `YOUR_GOOGLE_SCRIPT_URL` in `index.html` with your Web App URL.

## Testing
After deployment, test by submitting the form on the landing page. Emails should appear in your Google Sheet.
