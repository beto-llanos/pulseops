# Next steps for Beto

Everything is built and pushed. Three things left for you to do (~15 min total).

---

## 1. Deploy to Streamlit Community Cloud (5 min)

1. Go to **https://share.streamlit.io**
2. Sign in with GitHub (`beto-llanos`)
3. Click **"New app"**
4. Fill in:
   - Repository: `beto-llanos/pulseops`
   - Branch: `main`
   - Main file path: `streamlit_app.py`
   - App URL (optional): `pulseops` -> gives you `https://pulseops.streamlit.app`
5. Click **"Deploy"**

That's it. Boots in ~2 min on synthetic data, no secrets needed for the demo.

**Optional** (only if you want live Claude scoring during the demo): in Streamlit Cloud go to **App > Settings > Secrets** and paste:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

The dashboard works without it (heuristic fallback), but with the key the Repetition Detector page shows "Live Claude integration active."

---

## 2. Capture screenshots for Devpost (3 min)

Open the deployed app and take 6 screenshots, in this order:

1. **Home page** - the "Top 5 Money Drains" with the big `$793,190 Annual recoverable spend` KPI
2. **Meeting Cost Radar** - bar chart + most-expensive-meetings table
3. **Dev Flow Analyzer** - the wait-time histogram and reviewer load
4. **SaaS Utilization Audit** - the green-to-red horizontal bar chart
5. **Repetition Detector** - the cost-vs-automation-score scatter
6. **Architecture page** - the ASCII pipeline diagram

Use **Win + Shift + S** (Windows snip), crop to roughly 3:2 ratio. Upload all 6 to the Devpost image gallery.

---

## 3. Record the demo video (3 min total length)

Use **Loom** or **OBS** in screen-record mode. Script below — read it as you click through the deployed app.

### Script (~2:45 spoken)

> **[0:00 – 0:15]** Open home page.
> "Every quarter, finance walks into a review meeting and asks 'where did all the money go?' By the time the spreadsheet has the answer, it's been bleeding for weeks. PulseOps shows you the answer live."

> **[0:15 – 0:30]** Point at the headline KPI.
> "I connected this demo workspace 5 minutes ago. PulseOps found seven hundred and ninety three thousand dollars in annual recoverable spend across four detection engines."

> **[0:30 – 0:55]** Scroll down to Top 5 Money Drains.
> "Every finding has a dollar amount, a confidence score, and a specific fix. The number-one drain right now: a recurring 'Q3 planning offsite prep' meeting that's cost the company a hundred and eighty thousand dollars a year and produces no recorded action items most of the time."

> **[0:55 – 1:20]** Click into **Meeting Cost Radar**.
> "Each meeting is priced from attendee salaries, role, and duration. The 14-day spend chart shows our company burning between two and four thousand dollars per day on meetings. Roughly forty percent of that has no tracked outcome — that's our recoverable pile."

> **[1:20 – 1:45]** Click into **Dev Flow Analyzer**.
> "Same idea on the engineering side. Pull requests sitting blocked over 48 hours get costed by the author's salary times wait time times productivity-loss multiplier. We can see Ana Reyes's PRs are waiting 96 hours for first review — that's $129K a year of senior engineering time on the floor."

> **[1:45 – 2:10]** Click into **SaaS Utilization Audit**.
> "PulseOps cross-references billing against actual login activity. Sketch has eleven percent utilization while Figma covers the same category — that's a duplicate tool. Confluence is at twenty seven percent — we have ghost seats. Total recoverable here: thousands per month."

> **[2:10 – 2:30]** Click into **Repetition Detector**.
> "And the fourth engine uses Claude to read ticket and PR histories, find manual workflows that repeat, and score them for automation potential. Each row is a candidate. The Y-axis is cost, the X-axis is how automatable Claude thinks it is — the upper-right is where you start."

> **[2:30 – 2:45]** Back to home, hover the Telegram digest preview.
> "Every Monday at 9am the team gets this digest in Telegram, ranked by recoverable spend. No new tool to log into. PulseOps. Built with Claude. Deployable today."

### After recording

1. Upload to YouTube as **Unlisted** (not Public, not Private)
2. Title: `PulseOps - Internal Tools Hackathon Demo`
3. Copy the YouTube URL into the Devpost "Video demo link" field

---

## 4. Final Devpost fields to paste

**"Try it out" links:**
- Label: `Live demo`, URL: `https://pulseops.streamlit.app` (or whatever URL Streamlit gives you)
- Label: `Source code`, URL: `https://github.com/beto-llanos/pulseops`

**Built with tags** (already prepared earlier in chat):
`python` `streamlit` `plotly` `pandas` `anthropic` `claude` `claude-api` `google-calendar-api` `github-api` `jira-api` `telegram-bot-api` `sqlite` `docker` `docker-compose` `oauth2` `rest-api`

---

## If something breaks

- **Streamlit deploy fails:** the most common cause is a typo in `requirements.txt`. The current file is known-good.
- **Locally:** `pip install -r requirements.txt && streamlit run streamlit_app.py`
- **Numbers look weird:** `pulseops/mock_data.py` has the SEED constant and `salary_bands.py` has the role multipliers. Tweak there.

You're good. Go win this thing.
