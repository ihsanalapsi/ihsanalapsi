#!/usr/bin/env python3
"""Daily refresh of this profile, run by .github/workflows/profile.yml.

1. assets/terminal.svg: a terminal that types `whoami`, `cat now.txt` and
   `gh stats`, with this account's live numbers (GitHub GraphQL).
2. README.md, between the ARTICLES markers: the five latest articles from
   https://ihsanalapsi.dev/feed.xml, each with its English title and link
   (the article's own `?lang=en` page).

Standard library only. GITHUB_TOKEN is read from the environment for the
GraphQL call; without it the numbers come from the public REST API and the
contributions count is left out.
"""
import base64
import datetime
import email.utils
import html
import json
import os
import pathlib
import re
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
USER = "ihsanalapsi"
FEED = "https://ihsanalapsi.dev/feed.xml"
ARTICLES = 5

DEEP, PANEL2, RED, HI = "#100C0D", "#17120F", "#E90507", "#FF3B45"
W74, W45, LINE = "rgba(255,255,255,.74)", "rgba(255,255,255,.45)", "rgba(240,237,226,.12)"


def fetch(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": f"{USER}-profile", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read()


# --- Numbers -----------------------------------------------------------------

def numbers():
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        query = """query($login:String!){user(login:$login){
          followers{totalCount}
          repositories(ownerAffiliations:OWNER,privacy:PUBLIC,first:100){totalCount nodes{stargazerCount}}
          contributionsCollection{contributionCalendar{totalContributions}}}}"""
        body = json.dumps({"query": query, "variables": {"login": USER}}).encode()
        data = json.loads(fetch("https://api.github.com/graphql", body, {"Authorization": f"bearer {token}"}))["data"]["user"]
        repos = data["repositories"]
        return {
            "repos": repos["totalCount"],
            "stars": sum(n["stargazerCount"] for n in repos["nodes"]),
            "followers": data["followers"]["totalCount"],
            "contributions": data["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        }
    user = json.loads(fetch(f"https://api.github.com/users/{USER}"))
    repos = json.loads(fetch(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner"))
    return {"repos": user["public_repos"], "stars": sum(r["stargazers_count"] for r in repos),
            "followers": user["followers"], "contributions": None}


# --- Terminal card -------------------------------------------------------------

SIZE = 21          # font size
CHAR = SIZE * 0.6  # Geist Mono advance: 600/1000 em
PAD = 44
LINE_H = 34
TYPE = 0.055       # seconds per typed character


def text_run(x, y, parts):
    """parts: [(text, fill)]; returns the <text> and the run's width."""
    spans = "".join(f'<tspan fill="{fill}">{html.escape(t)}</tspan>' for t, fill in parts)
    width = sum(len(t) for t, _ in parts) * CHAR
    return f'<text x="{x:.1f}" y="{y}" xml:space="preserve">{spans}</text>', width


def terminal(n, today):
    prompt = [("ihsan@orbit", HI), (" ~ % ", W45)]
    prompt_w = sum(len(t) for t, _ in prompt) * CHAR
    stats = [("public repos ", W45), (str(n["repos"]), "#fff"), ("   stars ", W45), (str(n["stars"]), "#fff"),
             ("   followers ", W45), (str(n["followers"]), "#fff")]
    if n["contributions"] is not None:
        stats += [("   contributions (last year) ", W45), (f'{n["contributions"]:,}', "#fff")]
    script = [
        ("cmd", "whoami"),
        ("out", [("Ihsan Alapsi", "#fff"), (" · Software Engineer & Penetration Tester · Istanbul", W74)]),
        ("cmd", "cat now.txt"),
        ("out", [("build   ", HI), ("web and mobile products".ljust(36), W74), ("SyMarket, Dietly", "#fff")]),
        ("out", [("break   ", HI), ("penetration tests and hardening".ljust(36), W74), ("Muhassan", "#fff")]),
        ("out", [("write   ", HI), ("practical guides for developers".ljust(36), W74), ("ihsanalapsi.dev", "#fff")]),
        # Security research: a private HackerOne program, so the company stays unnamed.
        ("cmd", "cat findings.txt"),
        ("out", [("high 7.2    ", HI), ("subdomain takeover via a dangling DNS record", "#fff")]),
        ("out", [("            private bug bounty program on HackerOne · triaged · fixed · rewarded", W74)]),
        ("cmd", "gh stats ihsanalapsi"),
        ("out", stats),
        ("end", None),
    ]
    rows, keyframes, t, y = [], [], 0.5, 44 + 18
    for i, (kind, value) in enumerate(script):
        if kind == "cmd" and i:
            y += 12  # a little air before each new command
        y += LINE_H
        if kind in ("cmd", "end"):
            prompt_svg, _ = text_run(PAD, y, prompt)
            if kind == "end":
                rows.append(f'<g class="ln" style="animation-delay:{t:.2f}s">{prompt_svg}'
                            f'<rect class="cursor" x="{PAD + prompt_w:.1f}" y="{y - SIZE + 3}" width="{CHAR:.1f}" height="{SIZE + 2}" fill="{RED}"/></g>')
                break
            cmd_svg, cmd_w = text_run(PAD + prompt_w, y, [(value, "#fff")])
            dur = len(value) * TYPE
            keyframes.append(f"@keyframes k{i}{{to{{transform:translateX({cmd_w + 2:.1f}px)}}}}")
            rows.append(f'<g class="ln" style="animation-delay:{t:.2f}s">{prompt_svg}{cmd_svg}'
                        f'<rect class="cover" x="{PAD + prompt_w - 1:.1f}" y="{y - SIZE}" width="{cmd_w + 4:.1f}" height="{SIZE + 9}" fill="{PANEL2}" '
                        f'style="animation:k{i} {dur:.2f}s steps({len(value)}) {t + 0.25:.2f}s forwards"/></g>')
            t += 0.25 + dur + 0.25
        else:
            out_svg, _ = text_run(PAD, y, value)
            rows.append(f'<g class="ln" style="animation-delay:{t:.2f}s">{out_svg}</g>')
            t += 0.12
        if kind == "out" and i + 1 < len(script) and script[i + 1][0] != "out":
            t += 0.45  # read time after an output block
    w, h = 1280, y + 40
    font = base64.b64encode((ROOT / "assets/fonts/GeistMono-Variable.woff2").read_bytes()).decode()
    # No date in the card: it only changes (and gets committed) when a number does.
    title = "ihsan@orbit: ~"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Terminal. whoami: Ihsan Alapsi, Software Engineer and Penetration Tester, Istanbul. Builds web and mobile products (SyMarket, Dietly), runs penetration tests and hardening (Muhassan), writes practical guides for developers (ihsanalapsi.dev). GitHub: {n["repos"]} public repos, {n["stars"]} stars, {n["followers"]} followers.">
<style>@font-face{{font-family:"Geist Mono";src:url(data:font/woff2;base64,{font}) format("woff2");font-weight:100 900}}
text{{font:400 {SIZE}px "Geist Mono",ui-monospace,Menlo,Consolas,monospace}}
.title{{font-size:14px;letter-spacing:.04em}}
.ln{{opacity:0;animation:show 0s linear forwards}}
.cursor{{animation:blink 1.1s steps(2,start) infinite}}
@keyframes show{{to{{opacity:1}}}}
@keyframes blink{{to{{visibility:hidden}}}}
{"".join(keyframes)}
@media (prefers-reduced-motion: reduce){{.ln{{animation:none;opacity:1}}.cover{{display:none}}.cursor{{animation:none}}}}</style>
<defs><radialGradient id="wine" cx="88%" cy="0%" r="70%"><stop offset="0" stop-color="#470C17" stop-opacity=".45"/><stop offset="1" stop-color="#470C17" stop-opacity="0"/></radialGradient></defs>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="18" fill="{PANEL2}" stroke="{LINE}"/>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="18" fill="url(#wine)"/>
<path d="M .5 44 H {w - .5}" stroke="{LINE}"/>
<circle cx="28" cy="22" r="6.5" fill="{RED}"/><circle cx="50" cy="22" r="6.5" fill="rgba(240,237,226,.18)"/><circle cx="72" cy="22" r="6.5" fill="rgba(240,237,226,.18)"/>
<text class="title" x="{w / 2}" y="27" text-anchor="middle" fill="{W45}">{html.escape(title)}</text>
{"".join(rows)}
</svg>
'''


# --- Latest articles -------------------------------------------------------------

def articles():
    root = ET.fromstring(fetch(FEED))
    lines = []
    for item in root.iter("item"):
        if len(lines) == ARTICLES:
            break
        link = item.findtext("link")
        title = item.findtext("title")
        url_en = f"{link}?lang=en"
        try:
            page = fetch(url_en).decode("utf-8", "replace")
            match = re.search(r'<meta property="og:title" content="([^"]+)"', page)
            if match and 'lang="en"' in page[:3000]:
                title, link = html.unescape(match.group(1)), url_en
        except OSError:
            pass  # keep the feed's own title and link
        date = email.utils.parsedate_to_datetime(item.findtext("pubDate"))
        safe = title.replace("[", "(").replace("]", ")")
        lines.append(f"- [{safe}]({link}) · {date:%b} {date.day}, {date.year}")
    return "\n".join(lines)


def replace_block(text, name, body):
    start, end = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(text):
        raise SystemExit(f"README is missing the {name} markers")
    return pattern.sub(lambda _: f"{start}\n{body}\n{end}", text)


def main():
    today = datetime.date.today().isoformat()
    (ROOT / "assets/terminal.svg").write_text(terminal(numbers(), today))
    readme = ROOT / "README.md"
    readme.write_text(replace_block(readme.read_text(), "ARTICLES", articles()))
    print("terminal.svg and README articles updated", today)


if __name__ == "__main__":
    main()
