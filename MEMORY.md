# MEMORY.md - Long-Term Notes

## Team Structure (Feb 22, 2026)

**AI Automation Business:**
- **COO** - Me (Riles) - orchestrate and coordinate
- **Starks** - Research agent (subagent) - research market gaps
- **Oakley** - Build agent (subagent) - build features and projects

**James' Interests for Projects:**
1. 🏈 Sports - Fantasy sports AI, injury predictions
2. 🏥 Health/Diabetes - GLP-1 tracking (GLP1Companion)
3. 🍔 Food - Nutrition tracking, recipe AI
4. 💻 Tech - Automation tools

**Current Projects:**
- GLP1Companion - Diabetes/GLP-1 tracking web app

**Revenue Goal:** $300k/year passive income

---

## Cron Job Configuration

**Lesson learned (Feb 18, 2026):** When setting up cron jobs with `delivery.mode: "announce"`, always deliver to a Discord **channel** (not DMs). Isolated cron sessions can post to channels but cannot send DMs.

Format: `"to": "channel:1473726102060138577"` (channel ID from right-click → Copy Channel ID)

James's morning brief job was failing for 4 days before we noticed. The isolated session can't send DMs — need to deliver to a channel instead.

## Project Notes

- **Kanban:** Keep `projects/diabetic-app/kanban.md` and `kanban.html` in sync when updating tasks
- **HTML kanban:** Located at `projects/diabetic-app/kanban.html` — auto-refreshes every 30 seconds

## Streamlit Custom Domains

**Lesson learned (Feb 20, 2026):** Streamlit Community Cloud free tier does NOT support custom domains natively (no "Custom domains" setting in app settings). 

**Solution:** Use Cloudflare redirect:
1. Set up Cloudflare DNS with nameservers at Namecheap
2. Create a Cloudflare Redirect Rule (301) from domain → Streamlit app URL
3. Works, but users see the Streamlit URL in browser address bar

**Alternative (if native domain needed):** Deploy to Render.com or Railway (both free, proper custom domain support)
