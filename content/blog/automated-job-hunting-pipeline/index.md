---
title: "Automating Your Job Search with Python and GitHub Actions"
date: 2026-06-03T22:00:08+02:00
draft: false
description: "How to build a nightly job hunting pipeline using JobSpy, sentence-transformers, Groq, and GitHub Actions — at zero additional cost."
summary: "A walkthrough of hunter-agent: a fully automated pipeline that scrapes Indeed nightly, scores listings against your CV using local embeddings, and generates tailored CVs and cover letters for every strong match."
featureAsset: "background.png"
tags: []
categories: []
---

# Automating Your Job Search with Python and GitHub Actions

Job hunting is repetitive by nature. The same sites, the same searches, the same copy-pasting of CV content into slightly different cover letters. Most of that work is mechanical and a reasonable candidate for automation — not to replace the judgment involved in applying, but to remove the friction so you can focus on the parts that actually matter.

This post walks through the architecture of a nightly job hunting pipeline built entirely with open-source tools and free-tier services. The pipeline scrapes Indeed for relevant roles, scores each listing against a reference CV using local sentence embeddings, and generates a tailored CV and cover letter for every strong match. It runs automatically every night on GitHub Actions and commits results back to the repository.

---

## Architecture

The pipeline has four stages that run in sequence:

```
scraper  →  matcher  →  generator  →  notifier
```

**Scraper** fetches job listings from Indeed using [JobSpy](https://github.com/speedyapply/JobSpy), a Python library that handles Indeed's session management cleanly without requiring an API key. Multiple search queries run per night across different keyword combinations and locations. Results are deduplicated by URL across all queries before being passed to the matcher.

**Matcher** scores each job against a concise reference profile — a short summary of target skills and domains — using `all-MiniLM-L6-v2` from sentence-transformers. Cosine similarity between the job embedding and the reference embedding produces a score between 0 and 1. Jobs scoring above a configurable threshold pass to the generator.

**Generator** calls [Groq](https://console.groq.com) — a free inference API — running Llama 3.3 70B to produce two documents per match: a tailored CV that reorders, rephrases, and emphasises the most relevant experience, and a concise cover letter. Documents are skipped if they already exist, preventing redundant API calls on subsequent runs.

**Notifier** writes a dated Markdown summary showing every scored job, its similarity score, location, and links to generated documents. Summaries older than a configurable number of days are automatically deleted.

---

## Setting Up the Configuration

All pipeline parameters live in a single `config.yaml` file. This keeps every tunable value in one place — no hunting through code to change a search term or adjust the threshold.

```yaml
scraper:
  queries:
    - query: "C++ embedded systems engineer"
      location: "München, Germany"
    - query: "robotics software engineer"
      location: "München, Germany"
  results_wanted: 20
  hours_old: 24
  country_indeed: "germany"
  distance_miles: 22

matcher:
  threshold: 0.45
  model: "all-MiniLM-L6-v2"

generator:
  model: "llama-3.3-70b-versatile"
  enabled: true

output:
  directory: "output"
```

The `threshold` value is the most important parameter to tune. A value of 0.45 captures a broad set of relevant roles. Raise it toward 0.60 if too many irrelevant jobs are passing through. The `hours_old` setting keeps results fresh for a nightly run — 24 hours ensures only new postings are processed.

---

## Scraping with JobSpy

JobSpy provides a single function call to fetch job listings across multiple sources. Here is the essential constructor for scraping Indeed:

```python
from jobspy import scrape_jobs

df = scrape_jobs(
    site_name=["indeed"],
    search_term="C++ embedded engineer",
    location="München, Germany",
    distance=22,
    results_wanted=20,
    hours_old=24,
    country_indeed="germany",
)
```

JobSpy returns a pandas DataFrame where each row is one job listing. Relevant columns include `title`, `company`, `location`, `description`, and `job_url`. The `description` column is what the matcher embeds — Indeed returns full job descriptions, which gives the similarity scoring meaningful signal to work with.

One practical note: JobSpy works reliably from residential IPs. GitHub Actions uses datacenter IPs which some job boards treat differently. Testing locally first before relying on the cloud runner is advisable.

---

## Matching with Sentence Transformers

The matcher loads the embedding model once at startup and reuses it across all jobs. The core of the matching logic is straightforward:

```python
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

model = SentenceTransformer("all-MiniLM-L6-v2")

reference_embedding = model.encode(reference_text, convert_to_tensor=True)
job_embedding = model.encode(job_text, convert_to_tensor=True)

score = float(cos_sim(reference_embedding, job_embedding).item())
```

Two things worth knowing before building this:

**Token limit.** `all-MiniLM-L6-v2` has a 256-token limit. A full CV exceeds this and gets silently truncated. Use a concise 200-300 word reference profile covering target roles, core skills, and domain experience instead of the full document. This is one of the less obvious constraints that significantly affects matching quality.

**Model availability.** HuggingFace downloads are blocked from GitHub Actions runners. The cleanest solution is to download the model locally, commit it to the repository using Git LFS, and load it from disk at runtime. The model is approximately 90MB — well within GitHub's free LFS quota.

---

## Generating Documents with Groq

### Getting a Groq API Key

Groq offers a generous free tier with no credit card required:

- Sign up at [console.groq.com](https://console.groq.com) using your email or Google account
- Navigate to **API Keys** in the left sidebar
- Click **Create API Key**, give it a descriptive name, and copy it immediately — it is shown only once
- Store it securely in a password manager before closing the dialog

### Calling the API

Groq's API is OpenAI-compatible, so the standard `openai` Python library works directly with it. Only the `base_url` and `api_key` differ:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="your_groq_api_key",
)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": your_prompt}],
    max_tokens=2000,
    temperature=0.3,
)

content = response.choices[0].message.content
```

A low `temperature` of 0.3 keeps the output consistent and factual — appropriate for CV writing where accuracy matters more than creativity.

---

## Automating with GitHub Actions

### Storing the API Key Securely

API keys must never appear in code or configuration files committed to a repository. GitHub Actions Secrets handle this cleanly:

1. Go to your repository on GitHub
2. Navigate to **Settings → Secrets and variables → Actions**
3. Click **New repository secret**
4. Name it `GROQ_API_KEY` and paste the key as the value

The secret is encrypted and never visible again after saving. In the workflow file it is referenced as `${{ secrets.GROQ_API_KEY }}` and injected as an environment variable at runtime.

### Scheduling the Nightly Run

GitHub Actions uses standard cron syntax for scheduling. A workflow that runs every night at 22:00 UTC and can also be triggered manually looks like this:

```yaml
on:
  schedule:
    - cron: "0 22 * * *"
  workflow_dispatch:
```

The `workflow_dispatch` trigger adds a **Run workflow** button in the Actions tab, useful for testing without waiting for the scheduled time.

The key environment variable injection in the workflow step looks like this:

```yaml
- name: Run hunter pipeline
  env:
    GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
  run: python -m hunter
```

---

## Running Cost

Zero beyond existing subscriptions. JobSpy is open source. The embedding model runs from the repository. Groq's free tier provides 100,000 tokens per day on Llama 3.3 70B. GitHub Actions free tier handles the scheduling. Git LFS on a free GitHub account covers the model storage.

The main constraint is Groq's daily token budget. It works well for low-volume nightly automation but will hit limits if tested heavily during the day before a scheduled run. For higher volume use cases, a paid tier or an alternative provider such as Cerebras or Google AI Studio would be more appropriate.

---

## Where to Take This Further

A few directions worth exploring once the core pipeline is stable:

- **Additional job sources** — JobSpy supports LinkedIn alongside Indeed. LinkedIn descriptions require an extra fetch per listing but provide richer matching signal.
- **Improved matching** — Models with higher token limits such as BGE-M3 can embed a full CV directly, removing the need for a separate reference profile.
- **PDF generation** — Converting the Markdown output to a formatted PDF removes the remaining manual step before sending an application.
- **Notification** — A simple email or messaging integration when new matches are found avoids checking the repository manually each morning.

---

*Photo by <a href="https://unsplash.com/@coopery?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Mohamed Nohassi</a> on <a href="https://unsplash.com/photos/a-group-of-white-robots-sitting-on-top-of-laptops-2iUrK025cec?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>*
