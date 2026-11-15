# Installing your GitHub Profile README

1. Create a **public** GitHub repository named exactly `BryanGilbert-T` under your account, if it doesn't exist yet.
2. Upload the files in this bundle **with their folders intact** into that repository's **root**, using Git on your computer (or GitHub's web upload). Keep `README.md`, `assets/`, `scripts/` and `.github/workflows/`.
3. Your profile banner, featured projects, and initial chart placeholder should appear on `github.com/BryanGilbert-T` immediately after the commit.
4. For the live contribution chart, open **repository Settings → Actions → General → Workflow permissions** and enable **Read and write permissions**. Save.
5. Open **Actions → Update contribution candlesticks → Run workflow**. When it succeeds, `assets/candles.svg` is updated with your actual weekly contributions.
6. The workflow is scheduled to refresh daily. If organization/repo settings prohibit workflow writes, it will not update until permissions are fixed.

The chart generator uses the GitHub GraphQL API with the built-in Actions token and uses no third-party Python packages. A green candle indicates more contributions than the previous week, not financial performance.

**Note:** GitHub may show the markdown and SVGs differently on mobile, and external badges/icons from `shields.io` and `skillicons.dev` require those providers to remain reachable.
