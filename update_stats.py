import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

import yaml

THEME_FILE = "stats-styles.yml"


class Theme:
    def __init__(self, theme_file=None):
        with open(theme_file or THEME_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.colors = data["colors"]
        self.fonts = data.get("fonts", {})
        self.borderRadius = data.get("borderRadius", 20)
        self.emojis = data.get("emojis", {})
        self.animation = data.get("animation", {})

    def get(self, key, default=None):
        keys = key.split(".")
        val = self.colors
        for k in keys:
            val = val.get(k, {})
        return val if val else default


def print_section(title):
    print(f"\n{'='*50}")
    print(f" {title}")
    print('='*50)


def fetch_wakatime_stats(api_key):
    print("\n📊 Fetching WakaTime Stats...")
    
    url = f"https://wakatime.com/api/v1/users/current/all_time_since_today?api_key={api_key}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())
            if "data" in data:
                print(f"\n ✓ Total Coding Time: {data['data'].get('text', 'N/A')}")
                return data["data"]
    except Exception as e:
        print(f" ✗ Error: {e}")
    return None


def fetch_wakatime_details(api_key):
    print("\n🌐 Fetching WakaTime Details (Languages, Editors, Categories)...")
    
    ranges = [
        ("Last 7 Days", "last_7_days"),
        ("Last 30 Days", "last_30_days"),
    ]
    
    for display_name, range_type in ranges:
        print(f"  Trying {display_name}...")
        url = f"https://wakatime.com/api/v1/users/current/stats?api_key={api_key}&range={range_type}"
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Python WakaTime Client')
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode())
                if "data" in data and data["data"]:
                    stats_data = data["data"]
                    
                    languages = stats_data.get("languages", [])[:10]
                    editors = stats_data.get("editors", [])[:5]
                    categories = stats_data.get("categories", [])[:5]
                    operating_systems = stats_data.get("operating_systems", [])[:3]
                    
                    print(f"   ✓ Found from {display_name}:")
                    print(f"     • {len(languages)} languages")
                    print(f"     • {len(editors)} editors")
                    print(f"     • {len(categories)} categories")
                    print(f"     • {len(operating_systems)} operating systems")
                    
                    print(f"\n   Top Languages:")
                    for lang in languages[:5]:
                        print(f"     • {lang.get('name', 'Unknown')}: {lang.get('text', 'N/A')} ({lang.get('percent', 0):.1f}%)")
                    
                    print(f"\n   Top Editors:")
                    for editor in editors[:3]:
                        print(f"     • {editor.get('name', 'Unknown')}: {editor.get('text', 'N/A')} ({editor.get('percent', 0):.1f}%)")
                    
                    return {
                        "languages": languages,
                        "editors": editors,
                        "categories": categories,
                        "operating_systems": operating_systems,
                        "total_seconds": stats_data.get("total_seconds", 0),
                        "daily_average": stats_data.get("daily_average", 0),
                        "human_readable_total": stats_data.get("human_readable_total", "N/A"),
                        "human_readable_daily_average": stats_data.get("human_readable_daily_average", "N/A"),
                        "human_readable_range": stats_data.get("human_readable_range", display_name),
                        "range": range_type
                    }
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"   ✗ API endpoint not found (may require Premium)")
            else:
                print(f"   ✗ HTTP {e.code}")
        except Exception as e:
            print(f"   ✗ {e}")
            continue
    
    print("   ✗ No data available")
    return None


def fetch_github_user(token, username):
    print("\n👤 Fetching GitHub User Info...")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"https://api.github.com/users/{username}"
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            
            created = data.get("created_at", "")[:10]
            updated = data.get("updated_at", "")[:10]
            days = "N/A"
            if created:
                created_dt = datetime.strptime(created, "%Y-%m-%d")
                days = (datetime.now() - created_dt).days
                years = days // 365
            
            print(f"\n### [1] 用户信息")
            print(f"| 项目 | 内容 |")
            print(f"|-----|------|")
            print(f"| 用户名 | {data.get('login', 'N/A')} |")
            print(f"| 用户ID | {data.get('id', 'N/A')} |")
            print(f"| 账号创建时间 | {created} (大约{years}年前加入 GitHub) |")
            print(f"| 最后更新 | {updated} |")
            print(f"| 公开仓库数 | {data.get('public_repos', 0)} 个 |")
            print(f"| 粉丝数 | {data.get('followers', 0)} |")
            print(f"| 关注数 | {data.get('following', 0)} |")
            print(f"| 所在地 | {data.get('location', 'N/A')} |")
            print(f"| 个人简介 | {data.get('bio', 'N/A')} |")
            
            return data
    except Exception as e:
        print(f" ✗ Error: {e}")
        return None


def fetch_github_repos(token, username):
    print(f"\n### [2] 可访问的仓库")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
    
    total_stars = 0
    total_forks = 0
    repos = []
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            
            print("\n 最近更新的仓库包括：\n")
            for repo in data[:10]:
                lang = repo.get("language") or "N/A"
                desc = (repo.get("description") or "No description")[:50]
                print(f" - {username}/{repo.get('name')} [{repo.get('visibility')}] - {desc}")
                print(f"   ⭐ {repo.get('stargazers_count', 0)} | 🍴 {repo.get('forks_count', 0)} | 💻 {lang}")
                
                total_stars += repo.get("stargazers_count", 0)
                total_forks += repo.get("forks_count", 0)
                repos.append(repo)
            
            if len(data) > 10:
                print(f"\n ... 还有 {len(data) - 10} 个更多仓库")
            
            print(f"\n 📊 总计: ⭐ {total_stars} stars | 🍴 {total_forks} forks")
            
            return repos, total_stars, total_forks
    except Exception as e:
        print(f" ✗ Error: {e}")
        return [], 0, 0


def fetch_github_orgs(token, username):
    print(f"\n### [3] 所属组织")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"https://api.github.com/users/{username}/orgs"
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            
            for org in data:
                print(f" - {org.get('login')} - {org.get('description', '')[:50]}")
            
            return data
    except Exception as e:
        print(f" ✗ Error: {e}")
        return []


def fetch_github_events(token, username):
    print(f"\n### [4] 最近的公开活动")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"https://api.github.com/users/{username}/events?per_page=20"
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            
            push_events = [e for e in data if e.get('type') == 'PushEvent']
            for event in push_events[:5]:
                commits = event.get('payload', {}).get('commits', [])
                repo = event.get('repo', {}).get('name', 'N/A')
                date = event.get('created_at', '')[:10]
                print(f" - 推送代码到 {repo} ({date})")
                for commit in commits[:2]:
                    print(f"   💬 {commit.get('message', '')[:60]}")
            
            return data
    except Exception as e:
        print(f" ✗ Error: {e}")
        return []


def fetch_github_starred(token, username):
    print(f"\n### [6] Starred 仓库")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"https://api.github.com/users/{username}/starred?per_page=10"
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            
            print(f"\n 最近 Star 了 {len(data)} 个项目：")
            for repo in data[:10]:
                print(f" - {repo.get('full_name')} ⭐{repo.get('stargazers_count', 0)}")
            
            return data
    except Exception as e:
        print(f" ✗ Error: {e}")
        return []


def fetch_token_info(token):
    print("\n🔐 Token 权限信息...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    url = "https://api.github.com/user"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            
            print(f"\n### [7] Token 权限范围")
            print("| 权限 | 说明 |")
            print("|-----|------|")
            print("| repo | 完全控制私有仓库 |")
            print("| repo:status | 访问提交状态 |")
            print("| public_repo | 访问公开仓库 |")
            print("| workflow | 更新 GitHub Action 工作流 |")
            
            print(f"\n✓ Token 有效 - 关联用户: {data.get('login')}")
            return True
    except urllib.error.HTTPError as e:
        print(f" ✗ Token 可能无效: {e.code}")
        return False
    except Exception as e:
        print(f" ✗ Error: {e}")
        return False


def generate_combined_svg(waka_data, waka_details, gh_user, gh_repos, gh_orgs, theme, output_file):
    target_seconds = 36000000
    
    waka_seconds = waka_data.get("total_seconds", 0) if waka_data else 0
    waka_text = waka_data.get("text", "0 hrs") if waka_data else "N/A"
    waka_progress = waka_seconds / target_seconds * 100
    waka_remaining = (target_seconds - waka_seconds) / 3600
    
    daily_avg_seconds = waka_details.get("daily_average", 0) if waka_details else 0
    daily_avg_text = waka_details.get("human_readable_daily_average", "N/A") if waka_details else "N/A"
    range_text = waka_details.get("human_readable_range", "Last 30 Days") if waka_details else "N/A"
    
    bg_start = theme.get("background.start", "#FFF8F0")
    bg_end = theme.get("background.end", "#FFEFEB")
    text_primary = theme.get("text.primary", "#5D4E6D")
    text_secondary = theme.get("text.secondary", "#8B7B8B")
    text_accent = theme.get("text.accent", "#FF8FA3")
    text_highlight = theme.get("text.highlight", "#FF6B9D")
    milestone_color = theme.get("milestone", "#FFD93D")
    progress_bg = theme.get("progressBg", "#E8D5D5")
    divider_color = theme.get("divider", "#E0D0D0")
    glow_color = theme.get("glow", "#FFB6C1")
    font = theme.fonts.get("primary", "Arial, sans-serif")
    title_font = theme.fonts.get("title", "Arial, sans-serif")
    radius = theme.borderRadius
    
    emojis = theme.colors.get("emojis", {})
    title_emoji = emojis.get("title", "🌸")
    progress_emoji = emojis.get("progress", "🎀")
    lang_emoji = emojis.get("languages", "💖")
    remaining_emoji = emojis.get("remaining", "✨")
    milestone_emoji = emojis.get("milestone", "⭐")
    
    username = gh_user.get("login", "N/A") if gh_user else "N/A"
    name = gh_user.get("name", username) if gh_user else username
    public_repos = gh_user.get("public_repos", 0) if gh_user else 0
    followers = gh_user.get("followers", 0) if gh_user else 0
    following = gh_user.get("following", 0) if gh_user else 0
    bio = gh_user.get("bio", "") if gh_user else ""
    location = gh_user.get("location", "Melbourne") if gh_user else "Melbourne"
    created_at = gh_user.get("created_at", "")[:10] if gh_user else ""
    
    total_stars = sum(r.get("stargazers_count", 0) for r in gh_repos)
    total_forks = sum(r.get("forks_count", 0) for r in gh_repos)
    
    repo_languages = {}
    for repo in gh_repos[:10]:
        lang = repo.get("language")
        if lang:
            repo_languages[lang] = repo_languages.get(lang, 0) + 1
    
    card_bg = theme.get("cardBg", "#FFFFFF")
    card_border = theme.get("cardBorder", "#FFE4E1")
    
    lang_colors = ["#FFB6C1", "#98D8C8", "#FFD1DC", "#FFE4B5", "#DDA0DD", "#87CEEB", "#F0E68C", "#B0E0E6"]
    editor_colors = ["#FF8FA3", "#98D8C8", "#FFD93D"]
    
    sections = []
    y_offset = 80
    
    particles = theme.colors.get("particles", ["#FFB6C1", "#FFD1DC", "#FFC0CB"])
    particle_svg = ""
    for i, color in enumerate(particles):
        x = 50 + (i * 150)
        y = 25 + (i % 3) * 15
        particle_svg += f'<circle cx="{x}" cy="{y}" r="3" fill="{color}" opacity="0.6"/>'
    
    if waka_data or waka_details:
        languages = waka_details.get("languages", []) if waka_details else []
        editors = waka_details.get("editors", []) if waka_details else []
        categories = waka_details.get("categories", []) if waka_details else []
        
        lang_section = ""
        if languages:
            lang_y = 0
            for i, lang in enumerate(languages[:5]):
                name_l = lang.get("name", "Unknown")[:12]
                percent = lang.get("percent", 0)
                time_text = lang.get("text", "N/A")
                bar_width = min(percent * 2.8, 220)
                color = lang_colors[i % len(lang_colors)]
                lang_section += f'''<g>
<rect x="30" y="{lang_y}" width="{bar_width}" height="18" rx="6" fill="{color}"/>
<text x="40" y="{lang_y + 13}" fill="{text_primary}" font-family="{font}" font-size="10" font-weight="bold">{name_l}</text>
<text x="245" y="{lang_y + 13}" text-anchor="end" fill="{text_secondary}" font-family="{font}" font-size="9">{time_text}</text>
<text x="{30 + bar_width + 5}" y="{lang_y + 13}" fill="{text_accent}" font-family="{font}" font-size="8">{percent:.1f}%</text>
</g>'''
                lang_y += 24
        
        editor_section = ""
        if editors:
            editor_y = 0
            for i, editor in enumerate(editors[:3]):
                name_e = editor.get("name", "Unknown")[:12]
                percent = editor.get("percent", 0)
                bar_width = min(percent * 2.0, 160)
                color = editor_colors[i % len(editor_colors)]
                editor_section += f'''<g>
<rect x="440" y="{editor_y}" width="{bar_width}" height="16" rx="5" fill="{color}"/>
<text x="450" y="{editor_y + 12}" fill="{text_primary}" font-family="{font}" font-size="10" font-weight="bold">{name_e}</text>
<text x="600" y="{editor_y + 12}" text-anchor="end" fill="{text_secondary}" font-family="{font}" font-size="9">{percent:.1f}%</text>
</g>'''
                editor_y += 22
        
        waka_card_height = 260
        progress_bar_width = 380
        progress_fill = min(waka_progress * 3.8, progress_bar_width)
        
        sections.append(f'''<g>
<rect x="20" y="{y_offset}" width="760" height="{waka_card_height}" rx="20" fill="{card_bg}" stroke="{card_border}" stroke-width="1.5"/>
<rect x="20" y="{y_offset}" width="760" height="50" rx="20" fill="url(#headerGradient)" opacity="0.15"/>
<rect x="20" y="{y_offset + 30}" width="760" height="20" fill="{card_bg}"/>

  <text x="40" y="{y_offset + 32}" fill="{text_secondary}" font-family="{font}" font-size="12">{title_emoji} WakaTime Coding Stats</text>
  <text x="760" y="{y_offset + 32}" text-anchor="end" fill="{text_secondary}" font-family="{font}" font-size="10">{range_text}</text>
  
  <text x="40" y="{y_offset + 70}" fill="{text_primary}" font-family="{title_font}" font-size="36" font-weight="bold">{waka_text}</text>
  <text x="40" y="{y_offset + 95}" fill="{text_accent}" font-family="{font}" font-size="11">{progress_emoji} Daily Avg: {daily_avg_text}</text>
  
  <rect x="40" y="{y_offset + 110}" width="{progress_bar_width}" height="14" rx="7" fill="{progress_bg}"/>
  <rect x="40" y="{y_offset + 110}" width="{progress_fill}" height="14" rx="7" fill="url(#progressGradient)"/>
  <text x="{40 + progress_bar_width + 10}" y="{y_offset + 122}" fill="{text_highlight}" font-family="{font}" font-size="14" font-weight="bold">{waka_progress:.1f}%</text>
  <text x="40" y="{y_offset + 145}" fill="{text_secondary}" font-family="{font}" font-size="10">{remaining_emoji} {int(waka_remaining):,} hours to 10k hour goal</text>
  
  <line x1="400" y1="{y_offset + 160}" x2="400" y2="{y_offset + waka_card_height - 20}" stroke="{divider_color}" stroke-width="1" stroke-dasharray="6,4"/>
  
  <text x="40" y="{y_offset + 170}" fill="{text_secondary}" font-family="{font}" font-size="11">{lang_emoji} Top Languages</text>
  {lang_section}
  <text x="440" y="{y_offset + 170}" fill="{text_secondary}" font-family="{font}" font-size="11">⌨️ Top Editors</text>
  {editor_section}
  
  <g transform="translate({700}, {y_offset + 180})">
    <circle cx="0" cy="0" r="30" fill="{milestone_color}" opacity="0.3"/>
    <text x="0" y="5" text-anchor="middle" fill="{text_primary}" font-family="{font}" font-size="24">{milestone_emoji}</text>
  </g>
</g>''')
        y_offset += waka_card_height + 25
    
    gh_card_height = 140
    sections.append(f'''<g>
<rect x="20" y="{y_offset}" width="760" height="{gh_card_height}" rx="20" fill="{card_bg}" stroke="{card_border}" stroke-width="1.5"/>
<rect x="20" y="{y_offset}" width="760" height="50" rx="20" fill="url(#ghHeaderGradient)" opacity="0.1"/>
<rect x="20" y="{y_offset + 30}" width="760" height="20" fill="{card_bg}"/>

  <circle cx="70" cy="{y_offset + 85}" r="35" fill="url(#avatarGradient)" stroke="{card_border}" stroke-width="2"/>
  <text x="70" y="{y_offset + 90}" text-anchor="middle" fill="{text_primary}" font-family="{title_font}" font-size="20" font-weight="bold">{name[0].upper() if name else '?'}</text>

  <text x="120" y="{y_offset + 50}" fill="{text_primary}" font-family="{title_font}" font-size="18" font-weight="bold">@{username}</text>
  <text x="120" y="{y_offset + 72}" fill="{text_secondary}" font-family="{font}" font-size="11">{bio[:45] if bio else 'Dropping commits, chugging coffee...'}</text>
  <text x="120" y="{y_offset + 90}" fill="{text_accent}" font-family="{font}" font-size="10">📍 {location} • 📅 Joined {created_at}</text>
  
  <g transform="translate(550, {y_offset + 45})">
    <rect x="0" y="0" width="90" height="50" rx="10" fill="{lang_colors[0]}" opacity="0.2"/>
    <text x="45" y="18" text-anchor="middle" fill="{text_primary}" font-family="{title_font}" font-size="18" font-weight="bold">{public_repos}</text>
    <text x="45" y="35" text-anchor="middle" fill="{text_secondary}" font-family="{font}" font-size="9">Repos</text>
  </g>
  <g transform="translate(650, {y_offset + 45})">
    <rect x="0" y="0" width="90" height="50" rx="10" fill="{lang_colors[1]}" opacity="0.2"/>
    <text x="45" y="18" text-anchor="middle" fill="{text_primary}" font-family="{title_font}" font-size="18" font-weight="bold">{followers}</text>
    <text x="45" y="35" text-anchor="middle" fill="{text_secondary}" font-family="{font}" font-size="9">Followers</text>
  </g>
  
  <line x1="40" y1="{y_offset + 105}" x2="760" y2="{y_offset + 105}" stroke="{divider_color}" stroke-width="0.5" stroke-dasharray="4,2"/>
  
  <text x="40" y="{y_offset + 122}" fill="{text_secondary}" font-family="{font}" font-size="11">⭐ {total_stars} Stars</text>
  <text x="140" y="{y_offset + 122}" fill="{text_secondary}" font-family="{font}" font-size="11">🍴 {total_forks} Forks</text>
  <text x="250" y="{y_offset + 122}" fill="{text_secondary}" font-family="{font}" font-size="11">👤 {following} Following</text>
  
  <text x="760" y="{y_offset + 122}" text-anchor="end" fill="{text_accent}" font-family="{font}" font-size="9">Updated Daily {remaining_emoji}</text>
</g>''')
    y_offset += gh_card_height + 25
    
    svg_height = y_offset + 20
    
    svg = f'''<svg width="800" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{bg_start};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{bg_end};stop-opacity:1" />
    </linearGradient>
    <linearGradient id="headerGradient" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{theme.get('progressBar.start', '#FFB6C1')}" />
      <stop offset="100%" style="stop-color:{theme.get('progressBar.end', '#FFD1DC')}" />
    </linearGradient>
    <linearGradient id="ghHeaderGradient" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{lang_colors[1]}" />
      <stop offset="100%" style="stop-color:{lang_colors[2]}" />
    </linearGradient>
    <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{theme.get('progressBar.start', '#FFB6C1')}" />
      <stop offset="50%" style="stop-color:{theme.get('progressBar.middle', '#FFC0CB')}" />
      <stop offset="100%" style="stop-color:{theme.get('progressBar.end', '#FFD1DC')}" />
    </linearGradient>
    <linearGradient id="avatarGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{theme.get('progressBar.start', '#FFB6C1')}" />
      <stop offset="100%" style="stop-color:{theme.get('progressBar.end', '#FFD1DC')}" />
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <rect width="800" height="{svg_height}" fill="url(#bgGradient)" rx="{radius}"/>
  
  {particle_svg}
  
  <text x="400" y="25" text-anchor="middle" fill="{text_primary}" font-family="{title_font}" font-size="14" font-weight="bold">{title_emoji} Welcome to My World {title_emoji}</text>
  
  {chr(10).join(sections)}
  
  <text x="400" y="{svg_height - 8}" text-anchor="middle" fill="{text_accent}" font-family="{font}" font-size="9">{title_emoji} Generated with Python {title_emoji}</text>
</svg>'''
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"\n✅ Generated: {output_file}")


def main():
    waka_key = os.environ.get("WAKATIME_API_KEY")
    gh_token = os.environ.get("GH_TOKEN")
    username = os.environ.get("GITHUB_USERNAME") or "shyu216"
    
    print("\n" + "="*50)
    print(" 🚀 Stats Generator")
    print("="*50)
    
    waka_data = None
    waka_details = None
    
    if waka_key:
        waka_data = fetch_wakatime_stats(waka_key)
        if waka_data:
            waka_details = fetch_wakatime_details(waka_key)
    else:
        print("\n⚠️ WAKATIME_API_KEY not set, skipping WakaTime")
    
    gh_user = None
    gh_repos = []
    gh_orgs = []
    
    if gh_token:
        print_section("GitHub Token 信息查询结果")
        
        fetch_token_info(gh_token)
        gh_user = fetch_github_user(gh_token, username)
        
        if gh_user:
            gh_repos, _, _ = fetch_github_repos(gh_token, username)
            gh_orgs = fetch_github_orgs(gh_token, username)
            fetch_github_events(gh_token, username)
            fetch_github_starred(gh_token, username)
    else:
        print("\n⚠️ GH_TOKEN not set, skipping GitHub")
    
    theme = Theme(THEME_FILE)
    generate_combined_svg(waka_data, waka_details, gh_user, gh_repos, gh_orgs, theme, "stats.svg")
    
    print("\n" + "="*50)
    print(" ✅ All Done!")
    print("="*50 + "\n")


if __name__ == "__main__":
    with OutputRedirector(OUTPUT_FILE):
        main()
