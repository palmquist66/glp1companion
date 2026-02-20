# Diabetic360 - Project Kanban

## Columns
- 🧠 **To Do** (You)
- ⚙️ **In Progress** (AI / You)
- ✅ **Done**
- 🤖 **Future Bot Tasks**

---

## To Do (You Decide)

### 🔴 P0 - Week 2: Foundation (This Week)

| Priority | Task | Due | Notes |
|----------|------|-----|-------|
| 🔴 P0 | Initialize Streamlit project | Week 2 | ✅ Done | `app/app.py` |
| 🔴 P0 | Set up SQLite database | Week 2 | ✅ Done | Implemented in app.py |
| 🔴 P0 | Build user auth (sign up/login) | Week 2 | ✅ Done | Implemented in app.py |
| 🔴 P0 | Create dashboard UI | Week 2 | ✅ Done | Implemented in app.py |
| 🔴 P0 | Deploy to Streamlit Cloud | Week 2 | ✅ Done | share.streamlit.io |
| 🔴 P0 | Choose domain name | Week 2 | ✅ Done | glp1companion.io | DNS on Namecheap → Cloudflare (redirect to Streamlit URL) |

| Domain setup issue | 2026-02-20 | Streamlit Cloud free tier doesn't support custom domains natively. Solution: Cloudflare redirect rule (301) from glp1companion.io → Streamlit URL |
| 🔴 P0 | Define GLP-1 medication list | Week 1 | ✅ Done | `glp1-medications.md` |

### 🟡 P1 - Week 3: Core Features

| Priority | Task | Due | Notes |
|----------|------|-----|-------|
| 🟡 P1 | Add glucose logging | Week 3 | ✅ Done | Implemented in app.py |
| 🟡 P1 | Add weight tracking | Week 3 | ✅ Done | Implemented in app.py |
| 🟡 P1 | Add GLP-1 medication tracker | Week 3 | ✅ Done | Implemented in app.py |
| 🟡 P1 | Add side effects log | Week 3 | ✅ Done | Implemented in app.py |
| 🟡 P1 | Add food logging (basic) | Week 3 | ✅ Done | Implemented in app.py |
| 🟡 P1 | Set up Stripe account | Week 3 | Todo | For payments |
| 🟡 P1 | Add AI Chat Interface | Week 3 | ✅ Done | Oakley built, deployed |
| 🟡 P1 | Add Proactive Insights | Week 3 | Todo | Auto-alerts, patterns |

### 🔌 P1 - Data Integration (The Agent Advantage)

| Priority | Task | Due | Notes |
|----------|------|-----|-------|
| 🟡 P1 | **Apple Health Sync** | Week 3 | Auto-import glucose, weight from iPhone |
| 🟡 P1 | **Google Fit Sync** | Week 3 | Auto-import activity, weight from Android |
| 🟡 P1 | **Bluetooth Device Sync** | Week 3 | Connect to glucose monitors, smart scales |
| 🟡 P1 | **Voice Logging** | Week 4 | "Hey GLP1, log my glucose 120" |
| 🟡 P1 | **Photo Food Logging** | Week 4 | Snap a pic, AI logs carbs |

### 🟢 P2 - Week 4: Polish + Launch

| Priority | Task | Due | Notes |
|----------|------|-----|-------|
| 🟢 P2 | Add insights engine (basic) | Week 4 | Todo | |
| 🟢 P2 | Add PDF export | Week 4 | Todo | For doctor visits |
| 🟢 P2 | Build landing page | Week 4 | Todo | |
| 🟢 P2 | Launch on Product Hunt | Week 4 | Todo | |
| 🟢 P2 | Post to Reddit/Facebook/Twitter | Week 4 | Todo | |
| 🟢 P2 | Start waitlist → first sales | Week 4 | Todo | |

### 📢 P0 - Research & Validation (Ongoing)

| Priority | Task | Due | Notes |
|----------|------|-----|-------|
| 🟢 P2 | Interview 5 diabetics | Week 1 | Todo | Research validation |
| 🟢 P2 | Join Reddit/Facebook groups | Week 1 | Todo | For launch |

---

## In Progress

*(No tasks currently in progress)*

---

## Done

| Task | Completed | Notes |
|------|-----------|-------|
| Micro-niche positioning | 2026-02-17 | GLP-1 + Type 2 focus |
| Target customer analysis | 2026-02-17 | Age 40-65, on GLP-1 |
| Pricing tiers | 2026-02-17 | Free / $12.99 / $29.99 |
| Time allocation model | 2026-02-17 | AI-powered 10-hr week |
| MVP Spec Document | 2026-02-17 | `mvp-spec.md` |
| 90-Day Plan | 2026-02-17 | Survival plan in mvp-spec.md |
| Streamlit project setup | 2026-02-18 | `app/app.py` |
| Domain name | 2026-02-18 | glp1companion.io | DNS configured on Namecheap |
| SQLite database | 2026-02-18 | Implemented in app.py |
| User auth | 2026-02-18 | Sign up/login in app.py |
| Dashboard UI | 2026-02-18 | Implemented in app.py |
| Glucose logging | 2026-02-18 | Implemented in app.py |
| Weight tracking | 2026-02-18 | Implemented in app.py |
| GLP-1 medication tracker | 2026-02-18 | Implemented in app.py |
| Side effects log | 2026-02-18 | Implemented in app.py |
| Food logging | 2026-02-18 | Implemented in app.py |
| GLP-1 medication list | 2026-02-17 | `glp1-medications.md` |
| Rename app to GLP1Companion | 2026-02-18 | Oakley built, deployed |
| Add AI Chat Interface | 2026-02-18 | deployed |
 Oakley built,| Deploy to Streamlit Cloud | 2026-02-18 | share.streamlit.io | (Automate Later)

| Task | Bot Solution |
|------|--------------|
| Logo design | AI image generator (Midjourney/DALL-E) |
| App icon | AI image generator |
| Landing page | AI (v0.dev, Framer AI) |
| Beta tester outreach | AI agent DMs |
| Customer support | AI chatbot |

---

## Legend

| Symbol | Meaning |
|--------|---------|
| 🔴 P0 | Must do this week |
| 🟡 P1 | This month |
| 🟢 P2 | When time permits |
| 📢 | Research/Validation |
| 👤 | Tasks you must do |
| 🤖 | AI can help with |

---

## How to Update

```
1. Add new task → Top of "To Do"
2. Start working → Move to "In Progress" (Owner: You/AI)
3. Complete → Move to "Done" + date
4. Automate → Move to "Future Bot Tasks"
```
