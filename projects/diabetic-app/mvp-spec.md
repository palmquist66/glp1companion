# Diabetic360 - MVP Specification

## Product Name: Diabetic360
**Tagline:** Type 2 Diabetes + GLP-1 Tracking — All in One Place

**Positioning:** The only app built for Type 2 diabetics on Mounjaro, Ozempic, or Wegovy who want to see the full picture: glucose, weight, food, and side effects.

**Platform:** Web app (Streamlit) — fastest path to launch

---

## Target Customer

| Primary | Secondary |
|---------|-----------|
| Type 2 diabetic on GLP-1 medication (Mounjaro/Ozempic/Wegovy) | Their caregivers (adult children) |
| Age 40-65 | Age 30-50 (caregivers) |
| Income: Middle-upper class | Willing to pay $10/mo |
| Pain: No single app tracks glucose + weight + food + side effects | Pain: Can't remotely monitor parent |

---

## MVP Features (Weeks 2-4)

### Priority 1: Core Experience (Must Have)

#### 1. Daily Dashboard
- Today's glucose reading
- Today's weight
- Today's meals logged
- Medications taken
- Quick-add buttons: +Glucose, +Weight, +Food, +Meds

#### 2. Glucose Tracking
- Manual entry: glucose level (mg/dL), time, context (fasting, before meal, after meal, bedtime)
- Color coding: Green (80-130), Yellow (131-180), Red (>180)
- Daily trend mini-chart (last 24 hours)
- Weekly average

#### 3. Weight Tracking
- Daily weight entry (lbs/kg)
- Trend chart over time
- Goal weight setting
- Difference from starting weight

#### 4. GLP-1 Medication Tracker
- Medication name (Mounjaro, Ozempic, Wegovy, other)
- Dosage
- Injection day/time
- Streak counter: "You've taken 12 consecutive doses"
- Side effects log (nausea, fatigue, etc.)

#### 5. Food Logging
- Quick-add: Meal name, carbs (grams)
- Food search (pre-built database)
- Meal type: Breakfast, Lunch, Dinner, Snack
- Optional photo

#### 6. Side Effects Tracker
- Pre-built list: Nausea, Fatigue, Headache, Dizziness, Injection site pain, Other
- Severity: Mild, Moderate, Severe
- Correlation prompt: "Did this occur after your last injection?"

---

### Priority 2: Insights (The "Wow" Factor)

#### 7. Basic Insights Engine
- "Your glucose averages 20 points lower on days you exercise"
- "You've experienced nausea 3x this week — consider taking with food"
- "Weight trend: -3 lbs this month"
- "Streak: 4 weeks of consistent GLP-1 tracking!"

---

### Priority 3: Export (Doctor Visits)

#### 8. PDF Report Generator
- One-click PDF with: glucose summary, weight trend, medication log, side effects summary
- Date range selector
- Print-ready for doctor appointments

---

## Data Model

### User Profile
```
- Email, password
- Name
- Diabetes type: Type 2
- GLP-1 medication: (Mounjaro/Ozempic/Wegovy/Other)
- Dosage
- Target glucose range (default: 80-130)
- Goal weight
- Start date (for tracking journey)
```

### Glucose Entry
```
- Value (mg/dL)
- Timestamp
- Context: Fasting, Before Meal, After Meal, Bedtime
- Notes (optional)
```

### Weight Entry
```
- Value (lbs)
- Timestamp
```

### GLP-1 Log Entry
```
- Medication name
- Dosage
- Timestamp
- Side effects (array)
- Severity (Mild/Moderate/Severe)
```

### Food Entry
```
- Name
- Carbs (grams)
- Meal type
- Timestamp
```

---

## User Flow

```
Day 1:
1. Sign up (email)
2. Select GLP-1 medication
3. Set target glucose range
4. Set goal weight
5. See empty dashboard

Daily Use (2 minutes):
1. Open app → Dashboard
2. Log weight (morning)
3. Log glucose (after meal)
4. Log GLP-1 injection (weekly/bi-weekly)
5. See insights
```

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Frontend | Streamlit (Python) |
| Database | SQLite (MVP), PostgreSQL (scale) |
| Auth | Streamlit auth |
| Hosting | Streamlit Cloud (free) |
| Payments | Stripe |

---

## Pricing

| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | Basic logging, 7-day history, no insights |
| Pro | $9.99/mo | Unlimited history, insights, PDF export, all features |

**Rationale:** GLP-1 users spend $1K/mo on medication. $10/mo is trivial for full tracking.

---

## Competitive Differentiation

| Competitor | Focus | Diabetic360 Advantage |
|------------|-------|----------------------|
| MySugr | Type 1, gamified | Type 2 + GLP-1 specific |
| Glucose Buddy | General diabetes | GLP-1 focus, weight tracking |
| Dexcom | Glucose only | Full picture (food + weight + meds) |
| Ozempic support groups | Community | Actual tracking app, not just chat |
| Apple Health | General health | Diabetes-first design |

---

## Launch Channels

| Channel | Approach |
|---------|----------|
| Reddit | r/diabetes, r/Mounjaro, r/Ozempic, r/type2diabetes — value-first posts |
| Facebook Groups | Mounjaro/Ozempic support groups — engagement first |
| Twitter | #Mounjaro, #Ozempic, #GLP1 — engage before pitch |
| Product Hunt | Launch Day 1 |
| Hacker News | If technical angle resonates |

---

## 90-Day Milestones

| Week | Goal | Revenue |
|------|------|---------|
| 4 | Launch | $0 (validate) |
| 8 | 10 paying | $100/mo |
| 12 | 30-50 paying | $300-500/mo |

**Path to $7K:** 700+ paying users OR add Family plan OR insurance contracts (Q3+)

---

## Week-by-Week Build Tasks

### Week 2: Foundation
- [ ] Initialize Streamlit project
- [ ] Set up SQLite database
- [ ] Build user auth (sign up / login)
- [ ] Create dashboard UI
- [ ] Deploy to Streamlit Cloud (test)

### Week 3: Core Features
- [ ] Add glucose logging
- [ ] Add weight tracking
- [ ] Add GLP-1 medication tracker
- [ ] Add side effects log
- [ ] Add food logging (basic)

### Week 4: Polish + Launch
- [ ] Add insights engine (basic)
- [ ] Add PDF export
- [ ] Set up Stripe payments
- [ ] Build landing page
- [ ] Launch on Product Hunt
- [ ] Post to Reddit/Facebook/Twitter
- [ ] Start waitlist → first sales

---

## Risk Mitigation

| Risk | Signal | Fix |
|------|--------|-----|
| No traction | 0 signups Week 3 | Change headline, post more, interview non-signups |
| High churn | Users leave after 1 week | Add insights, make it "addictive" |
| Feature creep | Trying to build everything | Cut to 5 features max |
| Burnout | Dreading the work | Cut scope, launch ugly |

---

## Budget Allocation ($500)

| Item | Cost |
|------|------|
| Domain (.com) | $12 |
| Streamlit Cloud (pro) | $0-14/mo |
| Stripe fees | 2.9% + 30¢ |
| Initial ads (test) | $50 |
| Fiverr help | $100 |
| Contingency | $324 |

---

## Why This Wins

1. **You're the user** — authentic, real testimonials
2. **GLP-1 wave is just starting** — 2026 is the inflection point
3. **No direct competitor** — apps either do diabetes OR weight, never both + GLP-1
4. **You can ship fast** — Streamlit in 2 weeks vs Flutter in 2 months
5. **Emotional purchase** — users are invested in their health journey

---

## V2: API Integrations (The Differentiator)

**Vision:** Pull data from all health apps into one dashboard.

| Integration | Timeline | Priority |
|-------------|----------|----------|
| Apple Health (iOS) | Month 3-4 | 1 |
| Fitbit | Month 4-5 | 2 |
| Google Fit | Month 4-5 | 3 |
| Dexcom G7 | Month 6+ | 4 (enterprise API) |
| Withings (scale/BP) | Month 5-6 | 5 |

**Why this wins:** Anyone can manual log. Seeing glucose + weight + food + exercise from ALL sources in ONE PLACE — that's the product.

---

## V3: Advanced Features (Year 2)

- AI-powered insights ("Your glucose spikes 2hrs after pizza")
- Caregiver mode (remote monitoring)
- Insurance integration (doctor prescriptions)
- A1C prediction
- GLP-1 dosage optimization suggestions
