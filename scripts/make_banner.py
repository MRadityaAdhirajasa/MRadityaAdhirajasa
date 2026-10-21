"""Render the bento dark-neon profile banner from a GraphQL dump (see .github/workflows/banner.yml).
Usage: python -I make_banner.py gh.json out.svg"""
import collections, json, sys
from datetime import date
from xml.sax.saxutils import escape

CYAN, MAGENTA = '#22D3EE', '#E879F9'
BG, CARD, BORDER, TEXT, SUB, MUTED = '#07080D', '#10131C', '#1C2030', '#E6EAF2', '#9AA3B5', '#7D8699'
SCALE = ['#1A1E29', '#0F4C5A', '#178FA6', CYAN, MAGENTA]
LEVEL = {'NONE': 0, 'FIRST_QUARTILE': 1, 'SECOND_QUARTILE': 2, 'THIRD_QUARTILE': 3, 'FOURTH_QUARTILE': 4}
LANG_COLORS = [CYAN, '#FB923C', '#A3E635', '#60A5FA', MAGENTA]
SANS = "'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "Consolas, 'SFMono-Regular', Menlo, monospace"

NAME = 'M Raditya Adhirajasa'
TOPICS = ['Data & AI', 'RAG', 'LLM evaluation', 'CoT distillation']


def text(x, y, s, size, fill=TEXT, weight=400, family=SANS, anchor='start'):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}">{escape(str(s))}</text>')


def card(x, y, w, h, fill=CARD, stroke=BORDER):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="{fill}" stroke="{stroke}"/>'


def languages(repos, top=5):
    sizes = collections.Counter()
    for r in repos:
        if not r['isFork']:
            for e in r['languages']['edges']:
                sizes[e['node']['name']] += e['size']
    total = sum(sizes.values())
    out = [(n, s * 100 / total, LANG_COLORS[i]) for i, (n, s) in enumerate(sizes.most_common(top))]
    out.append(('Other', 100 - sum(p for _, p, _ in out), '#94A3B8'))
    return out


def render(v):
    c = v['contributionsCollection']
    cal = c['contributionCalendar']
    days = [d for w in cal['weeks'] for d in w['contributionDays']]
    W, H, P, G = 1200, 454, 24, 16
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
         f'aria-labelledby="t"><title id="t">{escape(NAME)}: {cal["totalContributions"]} contributions in the last year</title>',
         f'<rect width="{W}" height="{H}" rx="28" fill="{BG}"/>']

    # hero
    o += [card(P, P, 560, 150), text(P + 28, P + 56, NAME, 30, weight=700),
          text(P + 28, P + 84, '@' + v['login'], 15, SUB, family=MONO)]
    x = P + 28
    for t in TOPICS:
        w = int(len(t) * 7.6) + 26
        o += [f'<rect x="{x}" y="{P + 104}" width="{w}" height="26" rx="13" fill="none" stroke="#2A3043"/>',
              text(x + w / 2, P + 121, t, 13, '#C7CEDB', anchor='middle')]
        x += w + 8

    # stat tiles
    stats = [('Contributions', cal['totalContributions'], 'last 12 months'),
             ('Commits', c['totalCommitContributions'], 'last 12 months'),
             ('Repos created', c['totalRepositoryContributions'], 'last 12 months'),
             ('Public repos', v['repositories']['totalCount'], 'all time')]
    tw = (W - P - (P + 560 + G) - 3 * G) // 4
    for i, (label, val, sub) in enumerate(stats):
        tx = P + 560 + G + i * (tw + G)
        hot = i == 0
        fg, lc = ('#04141A', '#04141A') if hot else (TEXT, SUB)
        o += [card(tx, P, tw, 150, CYAN if hot else CARD, CYAN if hot else BORDER),
              text(tx + 20, P + 34, label.upper(), 11, lc, 600),
              text(tx + 20, P + 100, f'{val:,}', 36, fg, 600, MONO),
              text(tx + 20, P + 128, sub, 12, lc)]

    # contribution graph
    y0 = P + 150 + G
    cw = 872
    o += [card(P, y0, cw, 240),
          text(P + 24, y0 + 38, f'{cal["totalContributions"]}', 18, CYAN, 700, MONO),
          text(P + 24 + len(str(cal['totalContributions'])) * 11 + 8, y0 + 38, 'contributions in the last year', 18, weight=700)]
    gx, gy, cell, step = P + 60, y0 + 76, 12, 15
    seen = set()
    for i, d in enumerate(days):
        col, row = i // 7, d['weekday']
        dt = date.fromisoformat(d['date'])
        if dt.day <= 7 and row == 0 and dt.month not in seen and col < 51:
            seen.add(dt.month)
            o.append(text(gx + col * step, gy - 8, dt.strftime('%b'), 11, MUTED))
        o.append(f'<rect x="{gx + col * step}" y="{gy + row * step}" width="{cell}" height="{cell}" rx="3" '
                 f'fill="{SCALE[LEVEL[d["contributionLevel"]]]}"/>')
    for row, lbl in ((1, 'Mon'), (3, 'Wed'), (5, 'Fri')):
        o.append(text(P + 24, gy + row * step + 10, lbl, 11, MUTED))
    ly = gy + 7 * step + 18
    lx = P + cw - 24 - 5 * step - 36
    o.append(text(lx - 8, ly + 10, 'Less', 11, MUTED, anchor='end'))
    for i, col in enumerate(SCALE):
        o.append(f'<rect x="{lx + i * step}" y="{ly}" width="{cell}" height="{cell}" rx="3" fill="{col}"/>')
    o.append(text(lx + 5 * step + 4, ly + 10, 'More', 11, MUTED))

    # languages
    lx0, lw = P + cw + G, W - P - (P + cw + G)
    o += [card(lx0, y0, lw, 240), text(lx0 + 24, y0 + 38, 'Top languages', 18, weight=700)]
    langs = languages(v['repositories']['nodes'])
    bx, bw = lx0 + 24, lw - 48
    o.append(f'<clipPath id="bar"><rect x="{bx}" y="{y0 + 56}" width="{bw}" height="10" rx="5"/></clipPath><g clip-path="url(#bar)">')
    for name, pct, col in langs:
        seg = bw * pct / 100
        o.append(f'<rect x="{bx:.1f}" y="{y0 + 56}" width="{max(seg - 2, 1):.1f}" height="10" fill="{col}"/>')
        bx += seg
    o.append('</g>')
    for i, (name, pct, col) in enumerate(langs):
        ry = y0 + 96 + i * 23
        o += [f'<circle cx="{lx0 + 29}" cy="{ry - 4}" r="5" fill="{col}"/>',
              text(lx0 + 42, ry, name, 13),
              text(lx0 + lw - 24, ry, f'{pct:.1f}%', 13, SUB, family=MONO, anchor='end')]

    o.append('</svg>')
    return '\n'.join(o)


if __name__ == '__main__':
    data = json.load(open(sys.argv[1], encoding='utf-8'))['data']
    v = data.get('user') or data['viewer']
    svg = render(v)
    assert svg.count('<svg') == 1 and svg.endswith('</svg>')
    open(sys.argv[2], 'w', encoding='utf-8').write(svg)
    print('wrote', sys.argv[2], len(svg), 'bytes')
