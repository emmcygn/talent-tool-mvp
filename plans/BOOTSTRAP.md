# Pre-Flight Checklist

Run this checklist **before Task 01** to ensure the environment is ready. Both agents should verify these items at the start of their first session.

---

## 1. Environment

- [ ] Python 3.12+ installed: `python --version`
- [ ] Node.js 20+ installed: `node --version`
- [ ] npm available: `npm --version`
- [ ] Git initialized: `git branch --show-current`
- [ ] pip available: `pip --version`

## 2. Directory Structure

- [ ] Plans directory exists: `ls plans/agent-a/ plans/agent-b/`
- [ ] Tasks directory exists: `ls tasks/`

## 3. Permissions (Claude Code)

Set permissions so agents don't block on every tool call:

```
/permissions add Bash(*) Edit(*) Write(*) Read(*) Glob(*) Grep(*)
```

## 4. Communication Files

- [ ] `plans/STATE.md` — has agent sections with `not_started` rows
- [ ] `plans/HANDOFF.md` — exists and is empty (ready for entries)
- [ ] `plans/ISSUES.md` — exists and is empty
- [ ] `tasks/lessons.md` — exists and is empty

## 5. Environment Variables

Create `.env` in project root (both agents reference this):

```bash
# Supabase (local dev defaults)
SUPABASE_URL=http://localhost:54321
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU

# OpenAI
OPENAI_API_KEY=sk-...

# Frontend
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 6. Smoke Test

After Task 01 completes for both agents:

```bash
# Agent A
cd backend && pip install -r requirements.txt && python -m pytest -v

# Agent B
cd frontend && npm install && npm run build
```

---

## Recovery Mode

If resuming after a crash:

1. Run this checklist to verify environment
2. `cat plans/STATE.md` — find your last completed task
3. `cat plans/ISSUES.md` — check for issues assigned to you
4. `cat plans/HANDOFF.md` — catch up on deliverables
5. `cat tasks/lessons.md` — load corrections
6. `git log --oneline -10` — verify recent commits
7. Resume from the next `not_started` task
