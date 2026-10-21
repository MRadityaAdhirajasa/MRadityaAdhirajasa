"""Render the dark-neon stats + languages cards from a GraphQL dump (see .github/workflows/banner.yml).
Usage: python -I make_banner.py gh.json out.svg"""
import collections, json, sys
from xml.sax.saxutils import escape

CYAN, MAGENTA = '#22D3EE', '#E879F9'
CARD, BORDER, TEXT, SUB = '#10131C', '#1C2030', '#E6EAF2', '#9AA3B5'
LANG_COLORS = [CYAN, MAGENTA, '#FB923C', '#A3E635', '#60A5FA', '#FBBF24', '#A78BFA', '#94A3B8']
SANS = "'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "Consolas, 'SFMono-Regular', Menlo, monospace"
# 24px stroke icons
ICONS = {
    'star': 'M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8-6.2-3.2-6.2 3.2L7 14.2 2 9.3l6.9-1z',
    'commit': 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM2 12h6M16 12h6',
    'pr': 'M6 3a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM6 7v14M18 17a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM18 17V9a3 3 0 0 0-3-3h-4M13 3l-2 3 2 3',
    'issue': 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zM12 7v6M12 16.5v.5',
    'repo': 'M4 19.5V5a2 2 0 0 1 2-2h14v16H6.5A2.5 2.5 0 0 0 4 21.5',
}


def text(x, y, s, size, fill=TEXT, weight=400, family=SANS, anchor='start'):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}">{escape(str(s))}</text>')


def card(x, y, w, h):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{CARD}" stroke="{CYAN}" stroke-opacity=".45"/>'


def icon(name, x, y, color=CYAN):
    return (f'<path transform="translate({x} {y}) scale(.75)" d="{ICONS[name]}" fill="none" stroke="{color}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')


def languages(repos, top=7):
    sizes = collections.Counter()
    for r in repos:
        if not r['isFork']:
            for e in r['languages']['edges']:
                sizes[e['node']['name']] += e['size']
    total = sum(sizes.values())
    out = [(n, s * 100 / total, LANG_COLORS[i]) for i, (n, s) in enumerate(sizes.most_common(top))]
    out.append(('Other', 100 - sum(p for _, p, _ in out), LANG_COLORS[-1]))
    return out


def render(v):
    c = v['contributionsCollection']
    repos = v['repositories']['nodes']
    W, H, CW = 1200, 232, 592
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">'
         f'<title id="t">GitHub stats and most used languages for {escape(v["login"])}</title>']

    # stats card
    o += [card(1, 1, CW - 2, H - 2), text(28, 46, 'GitHub Stats', 20, CYAN, 600)]
    rows = [('star', 'Total stars', sum(r['stargazerCount'] for r in repos)),
            ('commit', 'Commits (last year)', c['totalCommitContributions']),
            ('pr', 'Total pull requests', v['pullRequests']['totalCount']),
            ('issue', 'Total issues', v['issues']['totalCount']),
            ('repo', 'Contributed to', v['repositoriesContributedTo']['totalCount'])]
    for i, (ic, label, val) in enumerate(rows):
        y = 84 + i * 30
        o += [icon(ic, 28, y - 14), text(56, y, label, 15, weight=600), text(280, y, f'{val:,}', 15, weight=600, family=MONO)]
    cx, cy, r = 470, 128, 58
    o += [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{BORDER}" stroke-width="10"/>',
          f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{CYAN}" stroke-width="10" stroke-dasharray="{r * 4.2:.0f} 999" '
          f'stroke-linecap="round" transform="rotate(-90 {cx} {cy})"/>',
          f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{MAGENTA}" stroke-width="10" stroke-dasharray="0 {r * 4.4:.0f} {r * 1.6:.0f} 999" '
          f'stroke-linecap="round" transform="rotate(-90 {cx} {cy})"/>',
          text(cx, cy + 6, f'{c["contributionCalendar"]["totalContributions"]:,}', 30, TEXT, 700, MONO, 'middle'),
          text(cx, cy + 28, 'contributions', 12, SUB, anchor='middle')]

    # languages card
    x0 = CW + 16
    o += [card(x0 + 1, 1, CW - 2, H - 2), text(x0 + 28, 46, 'Most Used Languages', 20, CYAN, 600)]
    langs = languages(repos)
    bx, bw = x0 + 28, CW - 56
    o.append(f'<clipPath id="bar"><rect x="{bx}" y="66" width="{bw}" height="10" rx="5"/></clipPath><g clip-path="url(#bar)">')
    for _, pct, col in langs:
        seg = bw * pct / 100
        o.append(f'<rect x="{bx:.1f}" y="66" width="{max(seg - 2, 1):.1f}" height="10" fill="{col}"/>')
        bx += seg
    o.append('</g>')
    for i, (name, pct, col) in enumerate(langs):
        lx, ly = x0 + 28 + (i // 4) * 272, 112 + (i % 4) * 30
        o += [f'<circle cx="{lx + 6}" cy="{ly - 5}" r="6" fill="{col}"/>',
              text(lx + 20, ly, name, 14, TEXT),
              text(lx + 250, ly, f'{pct:.1f}%', 14, SUB, family=MONO, anchor='end')]

    o.append('</svg>')
    return '\n'.join(o)


if __name__ == '__main__':
    data = json.load(open(sys.argv[1], encoding='utf-8'))['data']
    v = data.get('user') or data['viewer']
    svg = render(v)
    assert svg.count('<svg') == 1 and svg.endswith('</svg>')
    open(sys.argv[2], 'w', encoding='utf-8').write(svg)
    print('wrote', sys.argv[2], len(svg), 'bytes')
