#!/usr/bin/env python3
"""Generate a 12-month SVG candlestick chart of GitHub commit contributions.

Each month is divided into consecutive 7-day buckets (1–7, 8–14, etc.).
For a month's candle: O = first bucket, H = max bucket, L = min bucket,
C = last bucket. Labels are the SUM of that month's commit contributions.

GitHub's GraphQL ``totalCommitContributions`` is the source. These are
GitHub-recognized commits, not all commits on all branches. With the
repository-scoped GITHUB_TOKEN, private contributions may be unavailable.

No third-party Python packages required.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request
from xml.sax.saxutils import escape

API = "https://api.github.com/graphql"


@dataclass(frozen=True)
class Month:
    year: int
    month: int
    buckets: tuple[int, ...]
    partial: bool = False

    @property
    def label(self) -> str:
        return date(self.year, self.month, 1).strftime("%b '%y")

    @property
    def total(self) -> int:
        return sum(self.buckets)

    @property
    def ohlc(self) -> tuple[int, int, int, int]:
        if not self.buckets:
            return (0, 0, 0, 0)
        return (self.buckets[0], max(self.buckets), min(self.buckets), self.buckets[-1])


def rolling_months(today: date, count: int = 12) -> list[tuple[int, int]]:
    idx = today.year * 12 + today.month - 1
    return [((idx - i) // 12, (idx - i) % 12 + 1) for i in range(count - 1, -1, -1)]


def month_segments(year: int, month: int, today: date) -> list[tuple[date, date]]:
    first = date(year, month, 1)
    last = min(date(year, month, calendar.monthrange(year, month)[1]), today)
    if first > last:
        return []
    segments = []
    start_day = 1
    while start_day <= last.day:
        a = date(year, month, start_day)
        b = date(year, month, min(start_day + 6, last.day))
        segments.append((a, b))
        start_day += 7
    return segments


def query_month(token: str, login: str, segments: list[tuple[date, date]]) -> tuple[int, ...]:
    # User-supplied login is provided only through a GraphQL variable.
    fields = []
    for k, (start, end) in enumerate(segments):
        frm = f"{start.isoformat()}T00:00:00Z"
        to = f"{end.isoformat()}T23:59:59Z"
        fields.append(f'w{k}: contributionsCollection(from:"{frm}",to:"{to}") {{ totalCommitContributions }}')
    query = 'query($login: String!) { user(login: $login) { ' + ' '.join(fields) + ' } }'
    body = json.dumps({'query': query, 'variables': {'login': login}}).encode('utf-8')

    for attempt in range(3):
        req = urllib.request.Request(
            API, data=body, method='POST',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/vnd.github+json',
                'User-Agent': 'BryanGitHubMonthlyCommits/1.0',
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=35) as response:
                payload = json.load(response)
            if payload.get('errors'):
                raise RuntimeError(f"GitHub GraphQL errors: {payload['errors']}")
            user = payload.get('data', {}).get('user')
            if user is None:
                raise RuntimeError(f'GitHub user not found: {login}')
            values = tuple(int(user[f'w{k}']['totalCommitContributions']) for k in range(len(segments)))
            if any(v < 0 for v in values):
                raise RuntimeError('GitHub returned a negative commit count')
            return values
        except urllib.error.HTTPError as exc:
            if attempt == 2 or exc.code not in (429, 500, 502, 503, 504):
                raise RuntimeError(f'GitHub API HTTP {exc.code}: {exc.read(300)!r}') from exc
            time.sleep(2 ** (attempt + 1))
        except urllib.error.URLError as exc:
            if attempt == 2:
                raise RuntimeError(f'GitHub API connection error: {exc}') from exc
            time.sleep(2 ** (attempt + 1))
    raise AssertionError('Unreachable')


def fetch_months(token: str, login: str, today: date) -> list[Month]:
    result = []
    for year, month in rolling_months(today):
        segments = month_segments(year, month, today)
        vals = query_month(token, login, segments)
        item = Month(year, month, vals, partial=(year, month) == (today.year, today.month))
        print(f'{item.label}: {item.total} commits across {len(vals)} periods', flush=True)
        result.append(item)
    return result


def nice_axis_max(hi: int) -> tuple[int, int]:
    if hi <= 4:
        return 4, 1
    raw = hi / 4
    exponent = 10 ** math.floor(math.log10(raw))
    step = next(x * exponent for x in (1, 2, 2.5, 5, 10) if x * exponent >= raw)
    step = max(1, math.ceil(step))
    return 4 * step, step


def svg_chart(months: list[Month], login: str, updated: date) -> str:
    if len(months) != 12:
        raise ValueError('Expected exactly 12 months')
    W, H = 1200, 575
    left, right, top, bottom = 112, 1125, 183, 447
    plot_w = right - left
    step_x = plot_w / 12
    peak = max((m.ohlc[1] for m in months), default=0)
    ymax, tick = nice_axis_max(peak)
    Y = lambda v: bottom - (v / ymax) * (bottom - top)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
        '<title id="title">Monthly GitHub commit candlesticks</title>',
        f'<desc id="desc">Twelve months of GitHub-recognized commits for {escape(login)}. Each monthly candle summarizes 7-day period counts, and each number above a candle is its monthly total.</desc>',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#07111e"/><stop offset="1" stop-color="#102b31"/></linearGradient></defs>',
        '<rect width="1200" height="575" rx="14" fill="url(#bg)"/>',
        '<rect x="1" y="1" width="1198" height="573" rx="13" fill="none" stroke="#29444f"/>',
        '<g font-family="Arial, Helvetica, sans-serif">',
        '<text x="40" y="57" font-size="27" font-weight="700" fill="#ecf7f5">Monthly Coding Activity</text>',
        '<text x="40" y="82" font-size="14" fill="#9bb7bb">GitHub commits  ·  monthly candles based on 7-day activity</text>',
        f'<text x="1161" y="58" text-anchor="end" font-size="22" font-weight="700" fill="#5eead4">{sum(m.total for m in months):,} commits</text>',
        '<text x="1161" y="81" text-anchor="end" font-size="12" fill="#9bb7bb">last 12 months</text>',
        '<text x="40" y="135" font-size="12" fill="#9bb7bb">MONTHLY TOTAL</text>',
        '<text x="40" y="159" font-size="11" fill="#7099a1">commits / 7 days</text>',
    ]
    for value in range(0, ymax + 1, tick):
        yy = Y(value)
        parts.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{right}" y2="{yy:.1f}" stroke="#3e6370" stroke-opacity="0.40" stroke-width="1" stroke-dasharray="4 6"/>')
        parts.append(f'<text x="{left-22}" y="{yy+4:.1f}" text-anchor="end" font-size="12" fill="#86aab2">{value}</text>')
    for i, m in enumerate(months):
        xx = left + (i + .5) * step_x
        o, high, low, c = m.ohlc
        color = '#2dd4a7' if c > o else '#ff7b8b' if c < o else '#74c5de'
        if m.partial:
            parts.append(f'<rect x="{left+i*step_x+2:.1f}" y="{top-12}" width="{step_x-4:.1f}" height="{bottom-top+31}" rx="6" fill="#256363" fill-opacity="0.13"/>')
        total_label = f'{m.total:,}' + ('*' if m.partial else '')
        parts.append(f'<text x="{xx:.1f}" y="135" text-anchor="middle" font-size="16" font-weight="700" fill="#e5f5f3">{total_label}</text>')
        parts.append(f'<line x1="{xx:.1f}" y1="{Y(high):.2f}" x2="{xx:.1f}" y2="{Y(low):.2f}" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>')
        h = max(4.5, abs(Y(c) - Y(o)))
        y_body = (Y(o) + Y(c)) / 2 - h/2 if abs(Y(c)-Y(o)) < 4.5 else min(Y(o),Y(c))
        parts.append(f'<rect x="{xx-11:.1f}" y="{y_body:.2f}" width="22" height="{h:.2f}" rx="2.5" fill="{color}"/>')
        parts.append(f'<text x="{xx:.1f}" y="483" text-anchor="middle" font-size="12" fill="#b9d3d6">{escape(m.label)}</text>')
        parts.append(f'<title>{escape(m.label)}: {m.total} commits total | first period {o}, highest {high}, lowest {low}, last period {c}{" | month to date" if m.partial else ""}</title>')
    parts.extend([
        '<line x1="40" y1="513" x2="1160" y2="513" stroke="#315560"/>',
        '<rect x="43" y="531" width="11" height="11" rx="2" fill="#2dd4a7"/>',
        '<text x="62" y="541" font-size="12" fill="#a8c8cc">Last period &gt; first</text>',
        '<rect x="230" y="531" width="11" height="11" rx="2" fill="#ff7b8b"/>',
        '<text x="249" y="541" font-size="12" fill="#a8c8cc">Last period &lt; first</text>',
        '<rect x="420" y="531" width="11" height="11" rx="2" fill="#74c5de"/>',
        '<text x="439" y="541" font-size="12" fill="#a8c8cc">No change</text>',
        '<text x="1160" y="541" text-anchor="end" font-size="11" fill="#8aadb2">* Current month to date  ·  Updated '+escape(updated.isoformat())+'</text>',
        '</g></svg>',
    ])
    return '\n'.join(parts) + '\n'


def main() -> None:
    token = os.getenv('GH_TOKEN') or os.getenv('GITHUB_TOKEN')
    login = os.getenv('GH_USER', 'BryanGilbert-T')
    if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?', login):
        raise SystemExit('Invalid GitHub login')
    if not token:
        raise SystemExit('GITHUB_TOKEN is missing; run via GitHub Actions or provide a token')
    now = datetime.now(timezone.utc).date()
    months = fetch_months(token, login, now)
    svg = svg_chart(months, login, now)
    dest = Path(__file__).resolve().parents[1] / 'assets' / 'candles.svg'
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Only overwrite the chart after all API calls have succeeded.
    tmp = dest.with_suffix('.svg.tmp')
    tmp.write_text(svg, encoding='utf-8')
    tmp.replace(dest)
    print('Wrote', dest)


if __name__ == '__main__':
    main()
