import json, subprocess
from collections import Counter
from pathlib import Path

QUERY = """query { viewer { repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
  nodes { languages(first: 20) { edges { size node { name } } } } } } }"""
MARKUP = {"HTML", "CSS", "SCSS", "Dockerfile", "Makefile"}
THEMES = {
    "light": {"fg": "#1f2328", "muted": "#656d76", "accent": "#0a7ea4"},
    "dark": {"fg": "#e6edf3", "muted": "#8d96a0", "accent": "#58c4f5"},
}
OPACITY = [1, .72, .5, .34, .22, .12]
W, BAR_Y, BAR_H, GAP = 440, 8, 6, 3

out = json.loads(subprocess.run(["gh", "api", "graphql", "-f", f"query={QUERY}"],
                                capture_output=True, text=True, check=True).stdout)
sizes = Counter()
for repo in out["data"]["viewer"]["repositories"]["nodes"]:
    for e in repo["languages"]["edges"]:
        if e["node"]["name"] not in MARKUP:
            sizes[e["node"]["name"]] += e["size"]

total = sum(sizes.values())
top = sizes.most_common(5)
langs = [(n, s / total) for n, s in top] + [("Other", 1 - sum(s for _, s in top) / total)]

for theme, c in THEMES.items():
    bars, legend, x, lx = [], [], 0.0, 0
    for (name, share), op in zip(langs, OPACITY):
        w = max(share * (W - GAP * (len(langs) - 1)), 2)
        bars.append(f'<rect x="{x:.1f}" y="{BAR_Y}" width="{w:.1f}" height="{BAR_H}" rx="3" fill="{c["accent"]}" fill-opacity="{op}"/>')
        x += w + GAP
        if name == "Other":
            continue
        label = f"{name} {share * 100:.0f}%"
        legend.append(f'<circle cx="{lx + 4}" cy="38" r="3.5" fill="{c["accent"]}" fill-opacity="{op}"/>'
                      f'<text x="{lx + 12}" y="42">{label}</text>')
        lx += 12 + len(label) * 6.6 + 12
    Path(__file__).parent.parent.joinpath("assets", f"langs-{theme}.svg").write_text(f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 50" width="{W}" height="50" role="img" aria-label="Languages: {', '.join(f'{n} {s * 100:.0f}%' for n, s in langs)}">
  <style>
    text {{ fill: {c["muted"]}; font: 11px ui-monospace, "SF Mono", Menlo, Consolas, monospace; }}
    .bar {{ transform-origin: left; animation: grow .6s cubic-bezier(.6,0,.2,1) .15s both; }}
    .legend {{ animation: fade .35s .45s both; }}
    @keyframes grow {{ from {{ transform: scaleX(0); }} }}
    @keyframes fade {{ from {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  </style>
  <g class="bar">{''.join(bars)}</g>
  <g class="legend">{''.join(legend)}</g>
</svg>
""", encoding="utf-8")

print(", ".join(f"{n} {s * 100:.1f}%" for n, s in langs))
