import os
import re
import requests
from datetime import datetime

TOKEN    = os.environ['GITHUB_TOKEN']
USERNAME = 'charlesms1246'
README   = 'Readme.md'

HEADERS = {
    'Authorization': f'token {TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
}

def get_repos():
    repos, page = [], 1
    while True:
        r = requests.get(
            f'https://api.github.com/users/{USERNAME}/repos',
            headers=HEADERS,
            params={'per_page': 100, 'page': page, 'type': 'owner'},
        )
        data = r.json()
        if not isinstance(data, list) or not data:
            break
        repos.extend(repo['full_name'] for repo in data if not repo.get('fork'))
        if len(data) < 100:
            break
        page += 1
    return repos

def get_commit_hours(repos):
    slots = {'Morning': 0, 'Daytime': 0, 'Evening': 0, 'Night': 0}
    for repo in repos:
        page = 1
        while True:
            r = requests.get(
                f'https://api.github.com/repos/{repo}/commits',
                headers=HEADERS,
                params={'author': USERNAME, 'per_page': 100, 'page': page},
            )
            if r.status_code != 200:
                break
            commits = r.json()
            if not isinstance(commits, list) or not commits:
                break
            for commit in commits:
                try:
                    date_str = commit['commit']['author']['date']
                    hour = datetime.fromisoformat(date_str.replace('Z', '+00:00')).hour
                    if 5 <= hour < 12:
                        slots['Morning'] += 1
                    elif 12 <= hour < 18:
                        slots['Daytime'] += 1
                    elif 18 <= hour < 22:
                        slots['Evening'] += 1
                    else:
                        slots['Night'] += 1
                except Exception:
                    continue
            if len(commits) < 100:
                break
            page += 1
    return slots

def bar(count, total, length=12):
    filled = round((count / total) * length) if total else 0
    return '█' * filled + '░' * (length - filled)

def build_block(slots):
    total = sum(slots.values()) or 1
    rows = [
        ('🌞', 'Morning',  slots['Morning']),
        ('🌆', 'Daytime',  slots['Daytime']),
        ('🌃', 'Evening',  slots['Evening']),
        ('🌙', 'Night',    slots['Night']),
    ]
    lines = []
    for emoji, label, count in rows:
        pct = (count / total) * 100
        lines.append(f'  {emoji} {label:<9} {count:>4} commits  {bar(count, total)}  {pct:.2f}%')
    return '\n'.join(lines)

def update_readme(block):
    with open(README, 'r', encoding='utf-8') as f:
        content = f.read()

    inner = (
        '\n  <pre style="background:#0E0B22;border:1px solid #2D1F5E;'
        'padding:12px;display:inline-block;text-align:left;">\n'
        + block
        + '</pre>\n  '
    )
    new_content = re.sub(
        r'(<!--START_SECTION:productive_time-->).*?(<!--END_SECTION:productive_time-->)',
        r'\g<1>' + inner + r'\g<2>',
        content,
        flags=re.DOTALL,
    )

    with open(README, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('README updated.')

if __name__ == '__main__':
    print('Fetching repos...')
    repos = get_repos()
    print(f'Found {len(repos)} repos. Fetching commits...')
    slots = get_commit_hours(repos)
    print(f'Slots: {slots}')
    block = build_block(slots)
    print(block)
    update_readme(block)
