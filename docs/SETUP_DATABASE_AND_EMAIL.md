# Connect the database (Supabase) and email (Gmail)

The app runs without either. Without Supabase, new cases, decisions and letters are kept in a temporary file that a serverless host can wipe at any time. Without Gmail, letters can be viewed and downloaded but not emailed.

## 1. Supabase (about 5 minutes)

1. Create a project at https://supabase.com (free tier is enough).
2. Open **SQL Editor**, paste this, and run it:

```sql
create table if not exists copilot_store (
  kind text not null,
  id text not null,
  data jsonb not null,
  updated_at timestamptz not null default now(),
  primary key (kind, id)
);
alter table copilot_store enable row level security;  -- no public policies: only the server's service key can read or write
```

3. Open **Project Settings, API**. Copy the **Project URL** and the **service_role** key (keep this key secret; it is only ever used on the server).
4. Add both to Vercel and redeploy:

```bash
vercel env add SUPABASE_URL production
vercel env add SUPABASE_SERVICE_KEY production
vercel --prod --yes
```

The sidebar chip changes from "Local store" to "Supabase". For local runs, put the same two values in `.env`.

What is stored: one row per case (`kind = case`), per decision letter (`letter`) and per audit entry (`audit`). The 30 sample cases come from the repository and are only written to the database once someone acts on them.

## 2. Gmail (about 3 minutes)

1. On the Google account that will send the demo letters, turn on 2-Step Verification.
2. Go to https://myaccount.google.com/apppasswords and create an app password (16 characters).
3. Add three variables to Vercel and redeploy:

```bash
vercel env add GMAIL_USER production            # the full Gmail address
vercel env add GMAIL_APP_PASSWORD production    # the 16-character app password
vercel env add LETTER_TO_EMAIL production       # where every demo letter is delivered (your own address)
vercel --prod --yes
```

The sidebar chip changes to "Email on". Every letter is delivered to `LETTER_TO_EMAIL` with the PDF attached and the subject prefixed `[DEMO]`. The app never emails the address of a patient or provider in the data.
