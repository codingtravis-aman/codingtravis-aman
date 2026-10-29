#!/usr/bin/env python3
"""Generate assets/stats.svg from the public GitHub REST API (no external deps)."""
import datetime
import json
import os
import sys
import urllib.request
from xml.sax.saxutils import escape

USER = os.environ.get("GITHUB_USER", "codingtravis-aman")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "stats.svg")
HIDE = {"HTML", "CSS", "SCSS", "Jupyter Notebook", "Makefile"}
COLORS = {
    "Python": "#4B8BBE", "JavaScript": "#F7DF1E", "TypeScript": "#3178C6",
    "Dart": "#00B4AB", "C++": "#F34B7D", "C": "#9CA3AF", "C#": "#178600",
    "Java": "#B07219", "Kotlin": "#A97BFF", "Swift": "#F05138", "PHP": "#8892BF",
    "Go": "#00ADD8", "Rust": "#DEA584", "Shell": "#89E051", "PLpgSQL": "#336791",
    "Ruby": "#CC342D", "Lua": "#6C7BFF",
}
FALLBACK = ["#22D3EE", "#A78BFA", "#34D399", "#F472B6", "#FBBF24"]


def api(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-readme-stats",
    })
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    user = api("https://api.github.com/users/" + USER)
    repos, page = [], 1
    while True:
        chunk = api("https://api.github.com/users/%s/repos?per_page=100&type=owner&page=%d" % (USER, page))
        repos += chunk
        if len(chunk) < 100:
            break
        page += 1

    own = [r for r in repos if not r["fork"]]
    stars = sum(r["stargazers_count"] for r in own)
    forks = sum(r["forks_count"] for r in own)

    langs = {}
    for r in own[:40]:
        try:
            for name, size in api(r["languages_url"]).items():
                if name not in HIDE:
                    langs[name] = langs.get(name, 0) + size
        except Exception as exc:  # skip a repo, keep going
            print("skip", r["name"], exc, file=sys.stderr)

    total = sum(langs.values())
    top = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:5]

    tiles = [
        (str(user["public_repos"]), "PUBLIC REPOS"),
        (str(stars), "STARS EARNED"),
        (str(forks), "FORKS"),
        (str(user["followers"]), "FOLLOWERS"),
    ]

    parts = []
    parts.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 290" width="1000" height="290" role="img" aria-label="GitHub live snapshot">')
    parts.append('''<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0B0F2A"/><stop offset="1" stop-color="#111B3A"/></linearGradient>
<linearGradient id="ac" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22D3EE"/><stop offset="1" stop-color="#A78BFA"/></linearGradient>
<clipPath id="bar"><rect x="40" y="185" width="920" height="14" rx="7"/></clipPath>
<clipPath id="card"><rect width="1000" height="290" rx="22"/></clipPath>
<linearGradient id="sh" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22D3EE" stop-opacity="0"/><stop offset=".5" stop-color="#22D3EE" stop-opacity=".10"/><stop offset="1" stop-color="#22D3EE" stop-opacity="0"/></linearGradient>
</defs>
<rect width="1000" height="290" rx="22" fill="url(#bg)"/>
<rect x="1" y="1" width="998" height="288" rx="21" fill="none" stroke="#22D3EE" stroke-opacity=".3"/>''')
    mono = "font-family=\"'Fira Code','SFMono-Regular',Consolas,'Courier New',monospace\""
    sans = "font-family=\"'Segoe UI','Helvetica Neue',Arial,sans-serif\""
    parts.append('<text x="40" y="40" %s font-size="14" letter-spacing="3" fill="#22D3EE">GITHUB // LIVE SNAPSHOT</text>' % mono)
    parts.append('<circle cx="330" cy="35" r="4" fill="#34D399"><animate attributeName="opacity" values="1;.2;1" dur="1.4s" repeatCount="indefinite"/></circle>')
    parts.append('<text x="960" y="40" text-anchor="end" %s font-size="14" fill="#A5F3FC">@%s</text>' % (mono, escape(USER)))

    for i, (val, label) in enumerate(tiles):
        x = 40 + i * 235
        parts.append('<g><rect x="%d" y="60" width="215" height="95" rx="14" fill="#111827" stroke="#1F2937"/>' % x)
        parts.append('<text x="%d" y="112" text-anchor="middle" %s font-size="38" font-weight="800" fill="url(#ac)">%s</text>' % (x + 107, sans, escape(val)))
        parts.append('<text x="%d" y="138" text-anchor="middle" %s font-size="12" letter-spacing="2" fill="#94A3B8">%s</text>' % (x + 107, sans, label))
        parts.append('<rect x="%d" y="60" width="215" height="95" rx="14" fill="none" stroke="#22D3EE"><animate attributeName="stroke-opacity" values="0;.5;0" dur="3.2s" begin="%.1fs" repeatCount="indefinite"/></rect>' % (x, i * 0.4))
        parts.append('<animate attributeName="opacity" from="0" to="1" dur="0.8s" begin="%.1fs" fill="freeze"/></g>' % (i * 0.15))

    parts.append('<text x="40" y="176" %s font-size="12" letter-spacing="2" fill="#94A3B8">TOP LANGUAGES (BY CODE)</text>' % sans)
    parts.append('<rect x="40" y="185" width="920" height="14" rx="7" fill="#1F2937"/>')

    if top and total:
        x = 40.0
        parts.append('<g clip-path="url(#bar)">')
        for i, (name, size) in enumerate(top):
            w = size / total * 920
            color = COLORS.get(name, FALLBACK[i % len(FALLBACK)])
            parts.append('<rect x="%.1f" y="185" width="%.1f" height="14" fill="%s"><animate attributeName="width" from="0" to="%.1f" dur="1.2s" fill="freeze"/></rect>' % (x, w, color, w))
            x += w
        parts.append('</g>')
        for i, (name, size) in enumerate(top):
            color = COLORS.get(name, FALLBACK[i % len(FALLBACK)])
            lx = 40 + i * 184
            parts.append('<circle cx="%d" cy="235" r="5" fill="%s"/>' % (lx + 5, color))
            parts.append('<text x="%d" y="240" %s font-size="14" fill="#E0F2FE">%s <tspan fill="#94A3B8">%.1f%%</tspan></text>' % (lx + 16, sans, escape(name), size / total * 100))
    else:
        parts.append('<text x="40" y="238" %s font-size="14" fill="#94A3B8">No language data yet</text>' % sans)

    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    parts.append('<text x="960" y="274" text-anchor="end" %s font-size="11" fill="#6B7280">auto-updated daily by GitHub Actions · %s UTC</text>' % (mono, today))
    parts.append('<g clip-path="url(#card)"><rect x="-200" y="0" width="200" height="290" fill="url(#sh)"><animate attributeName="x" values="-200;1000" dur="5s" repeatCount="indefinite"/></rect></g>')
    parts.append('</svg>')

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print("wrote", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
