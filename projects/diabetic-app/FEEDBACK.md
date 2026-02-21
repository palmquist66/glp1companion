# GLP1Companion Feedback System

## 📥 How to Add Feedback

**Quick add** - Just message Riles with:
- Bug: "Bug: [what happened]"
- Suggestion: "Suggestion: [what you'd like]"
- Comment: "Thought: [your thoughts]"

Or message in Discord feedback channel: https://discord.com/channels/793267235975462982/1474819544395813095

Or edit this file directly.

---

## 📋 Incoming Feedback (Unreviewed)

### New This Session
- [ ] (2026-02-20) Mobile sidebar covers almost whole screen → Made narrower & auto-close
- [ ] (2026-02-20) Login not persisting - users must recreate account

### From Users (To Be Triaged)
*Add user feedback here when reported*
- (2026-02-21) Weight chart shows random numbers instead of dates | Bug | 🔴 High | Medium | ✅ Fixed
- (2026-02-21) **UI Design** - Overall look needs improvement (3/3 users said this) | UX | 🔴 High | Medium | Need design brainstorming |
- (2026-02-21) **Mobile UX** - Sidebar menu covers too much and doesn't close on selection | UX | 🔴 High | Easy | ✅ Fixed
- (2026-02-21) **Mobile UX** - Keyboard pops up and blocks dropdown selection on signup | Bug | 🟡 Medium | Easy | ✅ Fixed
- (2026-02-21) No confirmation shown when logging glucose/weight/food | Bug | 🟡 Medium | Easy | ✅ Fixed
- (2026-02-21) Glucose chart time shows seconds - just show hh:mm | Bug | 🟢 Low | Easy |
- (2026-02-21) Chart zoom/pan not needed - simplify to static view | UX | 🟢 Low | Easy |
- (2026-02-21) **UI Redesign** - Replace sidebar with 4 main sections along bottom: Dashboard, AI Insights/Chat, Medications, Health Tracking | UX | 🟡 Medium | Medium |
- (2026-02-21) **Medication Tab** - Add dropdown for medications if user takes more than one, plus dropdown for suggested dosages | Feature | 🟡 Medium | Easy |
- (2026-02-21) Quick log buttons on dashboard don't work | Bug | 🔴 High | Easy | ✅ Fixed
- (2026-02-21) Morning brief cron job runs but doesn't deliver to Discord | Bug | 🔴 High | Medium |
- (2026-02-21) **AI Food Photo** - Identifies food but returns zeros for carbs/calories/protein | Bug | 🔴 High | Easy |
- (2026-02-21) After AI food photo analysis, no clear way to add another photo | UX | 🟡 Medium | Easy |

---

## 🔄 To Review & Prioritize

| # | Date | Feedback | Category | Severity | Effort | Status |
|---|------|----------|----------|----------|--------|--------|
| 1 | 2026-02-20 | Login doesn't work - user created new account multiple times | Bug | 🔴 High | Medium | Investigating |
| 2 | 2026-02-21 | Add welcome email | Feature | 🟡 Medium | Hard | Pending |
| 3 | - | [Pending review] | | | | |

---

## ✅ Completed & Actioned

| Date | Feedback | Action Taken |
|------|----------|--------------|
| 2026-02-20 | Navigation emojis too small | Switched to sidebar with text labels |
| 2026-02-20 | Want more nutrients from food photos | Added calories, fat, protein tracking |
| 2026-02-20 | Want to scan nutrition labels | AI now reads labels |
| 2026-02-20 | Domain not working | Cloudflare redirect solution |

---

## 📊 Prioritization Framework

### Severity (Impact on Users)
- 🔴 **Critical**: App crashes, data loss, users can't use
- 🟠 **High**: Major feature broken, frequent annoyance
- 🟡 **Medium**: Some users affected, workaround exists
- 🟢 **Low**: Minor cosmetic or rare edge case

### Effort (Time to Fix)
- **Easy**: < 30 min (small tweak, copy change)
- **Medium**: 1-2 hours (moderate feature work)
- **Hard**: 4+ hours (big feature, architecture change)

### Priority Matrix
```
        Low Effort    High Effort
High    DO FIRST     SCHEDULE
Severity
Low     QUICK WIN    BACKLOG
```

---

## 🤖 Riles' Review (AI Assistant)

Every session, Riles will:
1. Check this file for new feedback
2. Categorize and rank by severity + effort
3. Present top 3 prioritized items
4. Ask which to tackle

---

## 📈 Feedback Stats (Auto-updated)

- Total bugs fixed: 3
- Features added from feedback: 5
- Open critical issues: 1

*Last reviewed: 2026-02-20*
