# MEMORY.md - Long-Term Notes

## Team Structure (Feb 24, 2026)

**AI Automation Business:**
- **Riles** (me) - orchestrator, coordinates everything
- **Starks** - Research agent - finds market gaps, opportunities
- **Oakley** - Build agent - builds features and projects
- **Mason** - Test/Validation agent - runs tests, validates output, generates screenshots
- **Patrick** - Marketing agent (future) - handles releases, announcements

**Future agents to consider:**
- **Patrick** (marketing) - releases, social posts, customer comms

---

## Development Workflow (IMPORTANT)

1. **Starks** researches → sends ideas to Riles
2. **Riles** ranks by cost, size, difficulty → presents to James
3. **James** gives approval to build
4. **Oakley** builds
5. **Mason** tests/validates → runs tests, checks output, generates screenshots
6. **Riles** reviews code first → makes changes/improvements
7. **James** reviews locally → gives go/no-go
8. **Test locally** → confirm working
9. **Push to production**

### Task Registry (.clawdbot/active-tasks.json)

Each agent task is tracked in a JSON registry for visibility and auto-monitoring:

```json
{
  "id": "feat-custom-templates",
  "agent": "oakley",
  "description": "Custom email templates feature",
  "branch": "feat/custom-templates",
  "status": "running|done|failed",
  "startedAt": 1740268800000,
  "completedAt": null,
  "pr": null,
  "notifyOnComplete": true
}
```

**Definition of Done:**
- PR created
- Branch synced to main (no merge conflicts)
- CI passing (lint, types, unit tests)
- Mason (tester) validation passed
- Screenshots included (if UI changes)

### Cron Monitoring

A cron job runs every 10 minutes to:
- Check if agent sessions are alive
- Check for open PRs on tracked branches
- Check CI status
- Auto-respawn failed agents (max 3 attempts)
- Only alert if human attention needed

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
