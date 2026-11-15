# Setup: automated monthly commit candlesticks

This bundle replaces the **previous weekly candle generator** with a true monthly view based on GitHub-recognized commit contributions.

## Install

1. Open your **public profile repository**: <https://github.com/BryanGilbert-T/BryanGilbert-T>.
2. Upload the **contents** of this folder to the root of the repository, maintaining folders: `README.md`, `assets/`, `scripts/`, `.github/workflows/`. **Replace** the existing files with matching names. Do not upload the ZIP itself as the README.
3. Go to **Settings → Actions → General → Workflow permissions**. Allow the workflow to have **Read and write permissions**, if your repository's settings require it. The workflow also declares `contents: write`.
4. Go to **Actions → Update monthly GitHub commit candles → Run workflow** and run it on `main`.
5. Open the workflow run and confirm it completed successfully. After it commits `assets/candles.svg`, the new chart will appear on your GitHub profile.
6. Daily GitHub Actions schedules will maintain it automatically. GitHub may delay or sometimes skip scheduled runs; re-run manually when needed.

The generated chart intentionally begins with an **"Awaiting first update"** placeholder, not fake contributions. It is replaced by real data only after the first successful run.

## Chart math

Each month is split into 7-day periods: days 1–7, 8–14, 15–21, 22–28, and 29–end, if applicable. The current month ends on today's date in UTC. The graph uses the *GitHub GraphQL API* `totalCommitContributions` for each period.

- **Open:** first period's commit count.
- **Close:** last period's commit count.
- **High:** highest period count.
- **Low:** lowest period count.
- **Number above candle:** sum of the month's period counts.
- **Y-axis:** commits per period, not the monthly total.
- **Green:** close > open; **red:** close < open; **blue:** equal.

This keeps real OHLC semantics without inventing price-like data. GitHub recognizes a subset of commits (such as those on default branches); the repository-scoped `GITHUB_TOKEN` typically only sees public activity. If your GitHub email isn't linked to commits or you only work in private repos, counts may look lower than expected. If GraphQL fails, the generator exits and does not overwrite a previously successful chart.

## Files

- `README.md` — personal profile, with nontechnical section names and chart.
- `assets/banner.svg` — decorative personal header, independent of the live chart.
- `assets/candles.svg` — initially a labelled placeholder, then auto-generated.
- `scripts/generate_candles.py` — Python 3.12+, standard library only.
- `.github/workflows/candles.yml` — scheduled and manually runnable GitHub Action.

*No personal access token, third-party bot, or paid service required for public GitHub contribution data.*
