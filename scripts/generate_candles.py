#!/usr/bin/env python3
"""Render GitHub contribution counts as a candlestick-inspired SVG.

No third-party Python packages required. This visualizes *contributions*,
not financial prices: a candle's open is the prior week's total and its
close is the current week's total. No fictional intraperiod wicks are drawn.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from xml.sax.saxutils import escape

QUERY = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""


def fetch_weeks(token: str, username: str) -> list[tuple[str, int]]:
    payload = json.dumps({"query": QUERY, "variables": {"username": username}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "BryanGilbert-T-profile-chart",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.load(response)
    if data.get("errors"):
        raise RuntimeError("GitHub GraphQL failed: " + str(data["errors"]))
    user = data.get("data", {}).get("user")
    if not user:
        raise RuntimeError("GitHub GraphQL returned no user")
    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    totals = []
    for week in weeks:
        days = week.get("contributionDays", [])
        if days:
            totals.append((days[0]["date"], sum(int(d["contributionCount"]) for d in days)))
    return totals


def render(weeks: list[tuple[str, int]], username: str) -> str:
    weeks = weeks[-32:]
    if len(weeks) < 2:
        raise ValueError("At least two weeks are needed")
    W, H = 1200, 340
    plot_left, plot_right = 58, 1134
    top, bottom = 105, 240
    vol_top, vol_bottom = 256, 295
    maximum = max(1, *(value for _, value in weeks))
    y = lambda value: bottom - (value / maximum) * (bottom - top)
    slot = (plot_right - plot_left) / (len(weeks) - 1)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Weekly GitHub contribution candles for {escape(username)}">',
        '<rect width="1200" height="340" rx="12" fill="#09111D"/>',
        '<rect x="1" y="1" width="1198" height="338" rx="12" fill="none" stroke="#27515B"/>',
        '<g font-family="Arial,Helvetica,sans-serif">',
        '<text x="34" y="45" font-size="23" fill="#E2F6F1" font-weight="700">GITHUB / CONTRIBUTION CANDLES</text>',
        f'<text x="34" y="69" font-size="13" fill="#8CB3B5">{escape(username)}  ·  rolling 32 weeks  ·  open = prior week, close = current week</text>',
        f'<text x="1162" y="51" text-anchor="end" font-size="17" fill="#5EEAD4" font-weight="700">{weeks[-1][1]} / week</text>',
        '<text x="1162" y="71" text-anchor="end" font-size="12" fill="#89A7A8">latest contributions</text>',
    ]
    for frac in (0, .25, .5, .75, 1):
        yy = y(maximum * frac)
        parts.append(f'<line x1="{plot_left-10}" y1="{yy:.1f}" x2="{plot_right+10}" y2="{yy:.1f}" stroke="#305465" stroke-width="1" stroke-dasharray="4 6" opacity=".65"/>')
        parts.append(f'<text x="{plot_right+18}" y="{yy+4:.1f}" font-size="11" fill="#8AA5AA">{round(maximum*frac)}</text>')
    for i in range(1, len(weeks)):
        current = weeks[i][1]
        previous = weeks[i - 1][1]
        xx = plot_left + slot * i
        rising = current >= previous
        color = "#30D8AD" if rising else "#FF7285"
        high, low = max(current, previous), min(current, previous)
        y1, y2 = y(high), y(low)
        parts.append(f'<line x1="{xx:.1f}" y1="{y1:.1f}" x2="{xx:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="2"/>')
        parts.append(f'<rect x="{xx-6:.1f}" y="{y1:.1f}" width="12" height="{max(2.5,y2-y1):.1f}" rx="1.5" fill="{color}"/>')
        vh = (current / maximum) * (vol_bottom - vol_top)
        parts.append(f'<rect x="{xx-6:.1f}" y="{vol_bottom-vh:.1f}" width="12" height="{max(1,vh):.1f}" rx="1" fill="{color}" opacity=".45"/>')
        if i in (1, 8, 16, 24, len(weeks)-1):
            parts.append(f'<text x="{xx:.1f}" y="314" text-anchor="middle" font-size="10" fill="#789CA2">{escape(weeks[i][0][5:])}</text>')
    parts.extend([
        '<text x="58" y="330" font-size="10" fill="#7C9AA1">WEEKLY CONTRIBUTIONS</text>',
        '<text x="1134" y="330" text-anchor="end" font-size="10" fill="#7C9AA1">Green = more than previous week   ·   Red = fewer</text>',
        '</g></svg>',
    ])
    return "\n".join(parts) + "\n"


def main() -> None:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    username = os.environ.get("GH_USER") or "BryanGilbert-T"
    if not token:
        raise SystemExit("Missing GH_TOKEN or GITHUB_TOKEN environment variable")
    svg = render(fetch_weeks(token, username), username)
    dest = Path(__file__).resolve().parent.parent / "assets" / "candles.svg"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(svg, encoding="utf-8")
    print(f"Wrote {dest}")


if __name__ == "__main__":
    main()
