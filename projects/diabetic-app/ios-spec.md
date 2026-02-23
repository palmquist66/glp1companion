# GLP1Companion iOS App Specification

## Project Overview
- **Project Name:** GLP1Companion iOS
- **Type:** Native iOS Health Tracking App
- **Goal:** Provide a native mobile experience for GLP-1 and diabetes tracking with Apple Health integration

---

## Core Features

### 1. Authentication
- Email/password login (sync with web app)
- Biometric login (Face ID/Touch ID)
- Secure token storage in Keychain

### 2. Health Tracking
- **Glucose Logging** - Manual entry + from Apple Health
- **Weight Logging** - Manual entry + from Apple Health
- **Food Logging** - Photo capture + manual entry
- **Medication Tracking** - GLP-1 and other diabetes meds
- **Exercise Tracking** - From Apple Health

### 3. Apple Health Integration (Native!)
- Read: Glucose, Weight, Steps, Sleep, Exercise
- Write: Activity data
- Background sync for automatic updates

### 4. AI Features
- Food photo analysis (using Anthropic API)
- Proactive health insights
- Chat with AI assistant

### 5. Dashboard
- Today's metrics at a glance
- Trends and charts
- Quick-add buttons

### 6. Settings
- Profile management
- Notification preferences
- Dark/Light mode
- Data export

---

## Technical Stack

- **Framework:** Flutter (cross-platform, faster development)
- **Backend:** Existing PostgreSQL API + Streamlit for AI
- **State Management:** Riverpod or Provider
- **Local Storage:** SQLite for offline, synced to cloud
- **Health Data:** HealthKit framework

---

## Development Phases

### Phase 1: Foundation (Week 1-2)
- Project setup
- Authentication flow
- Basic UI structure
- Navigation

### Phase 2: Core Features (Week 2-3)
- Glucose tracking
- Weight tracking
- Medication logging
- Dashboard

### Phase 3: Apple Health (Week 3-4)
- HealthKit integration
- Background sync
- Data import

### Phase 4: AI & Polish (Week 4)
- Food photo AI
- Chat feature
- Push notifications
- App Store prep

---

## Estimated Timeline: 4-6 weeks

---

## Cost Estimate
- Apple Developer Account: $99/year
- Hosting: $0-20/month (existing backend)
- API calls: Pay-as-you-go for Anthropic

---

## Next Steps
1. Confirm Flutter as preferred framework
2. Set up Apple Developer account
3. Create Flutter project
4. Start with Phase 1
