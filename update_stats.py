import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

import yaml

# Import the SVG generator
try:
    from draw_interesting_object import generate_svg as generate_coding_character
except ImportError:
    # Fallback: try with hyphenated name
    import importlib.util
    spec = importlib.util.spec_from_file_location("draw_interesting_object", "draw-interesting-object.py")
    draw_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(draw_module)
    generate_coding_character = draw_module.generate_svg

THEME_FILE = "stats-styles.yml"
ABOUT_FILE = "about-me.yml"
OUTPUT_FILE = "update_stats.output"
ENV_FILE = ".env"


def load_env_file(env_path=ENV_FILE):
    """Load environment variables from .env file if it exists"""
    if not os.path.exists(env_path):
        return

    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key and value:
                    os.environ.setdefault(key, value)


class Theme:
    def __init__(self, theme_file=None):
        with open(theme_file or THEME_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.colors = data.get("colors", {})
        self.fonts = data.get("fonts", {})
        self.borderRadius = data.get("borderRadius", 20)
        self.topLanguages = data.get("topLanguages", [])
        self.langColors = data.get("langColors", {})
        self.editorColors = data.get("editorColors", ["#D2691E", "#CD853F", "#DEB887"])
        self.animation = data.get("animation", {})
        self.canvas = data.get("canvas", {"width": 600, "height": 200})

    def get(self, key, default=None):
        keys = key.split(".")
        val = self.colors
        for k in keys:
            val = val.get(k, {})
        return val if val else default


class AboutMe:
    def __init__(self, about_file=None):
        with open(about_file or ABOUT_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.profile = data.get("profile", {})
        self.username = self.profile.get("username", "shyu216")
        self.display_name = self.profile.get("display_name", self.username)
        self.bio = self.profile.get("bio", {})
        self.github_joined = self.profile.get("github_joined", "2021-02-25")
        self.location = self.profile.get("location", "Melbourne")
        self.goal = self.profile.get("goal", {})
        self.target_hours = self.goal.get("target_hours", 10000)
        self.links = self.profile.get("links", {})

    def get_bio(self, lang="en"):
        return self.bio.get(lang, self.bio.get("en", ""))

    def get_github_years(self):
        try:
            joined = datetime.strptime(self.github_joined, "%Y-%m-%d")
            days = (datetime.now() - joined).days
            return days // 365
        except:
            return 4


class OutputRedirector:
    def __init__(self, output_file):
        self.output_file = output_file
        self.terminal = sys.stdout
        self.log = []

    def write(self, message):
        self.terminal.write(message)
        self.log.append(message)

    def flush(self):
        self.terminal.flush()

    def __enter__(self):
        sys.stdout = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.terminal
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write("".join(self.log))





def fetch_wakatime_stats(api_key):
    print("\n📊 Fetching WakaTime Stats...")

    url = f"https://wakatime.com/api/v1/users/current/all_time_since_today?api_key={api_key}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())
            if "data" in data:
                print(f"\n ✓ Total Coding Time: {data['data'].get('text', 'N/A')}")
                return data["data"]
    except urllib.error.HTTPError as e:
        print(f" ✗ HTTP Error {e.code}: {e.reason}")
        return None
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
                    
                    for lang in languages[:10]:
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
    except urllib.error.HTTPError as e:
        print(f" ✗ HTTP Error {e.code}: {e.reason}")
        return None
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
    except urllib.error.HTTPError as e:
        print(f" ✗ HTTP Error {e.code}: {e.reason}")
        return [], 0, 0
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
        print(f" ✗ Token 可能无效: HTTP {e.code}")
        return False
    except Exception as e:
        print(f" ✗ Error: {e}")
        return False


def generate_svg(waka_data, waka_details, gh_user, gh_repos, about_me, theme, output_file):
    """生成粗野主义风格 - 横向/竖向自适应布局"""

    if theme is None:
        print("   ⚠️ Theme is None, creating default theme")
        theme = type('Theme', (), {
            'colors': {},
            'fonts': {},
            'borderRadius': 20,
            'topLanguages': [],
            'langColors': {},
            'editorColors': ["#D2691E", "#CD853F", "#DEB887"],
            'animation': {},
            'canvas': {"width": 600, "height": 200},
            'get': lambda self, key, default=None: default
        })()

    if about_me is None:
        print("   ⚠️ AboutMe is None, creating default profile")
        about_me = type('AboutMe', (), {
            'username': 'shyu216',
            'display_name': 'shyu216',
            'bio': {},
            'github_joined': '2021-02-25',
            'location': 'Melbourne',
            'goal': {},
            'target_hours': 10000,
            'links': {},
            'get_bio': lambda self, lang="en": "",
            'get_github_years': lambda self: 4
        })()

    canvas_width = theme.canvas.get("width", 600)
    canvas_height = theme.canvas.get("height", 200)

    is_horizontal = canvas_width > canvas_height

    if is_horizontal:
        return generate_horizontal_svg(waka_data, waka_details, gh_user, gh_repos, about_me, theme, output_file)
    else:
        return generate_vertical_svg(waka_data, waka_details, gh_user, gh_repos, about_me, theme, output_file)


def generate_horizontal_svg(waka_data, waka_details, gh_user, gh_repos, about_me, theme, output_file):
    """横向横幅布局 - 可爱波普风格"""
    canvas_width = theme.canvas.get("width", 600)
    canvas_height = theme.canvas.get("height", 200)
    margin = 15

    waka_seconds = waka_data.get("total_seconds", 0) if waka_data else 0
    waka_text = waka_data.get("text", "0 hrs") if waka_data else "N/A"
    waka_progress = min(waka_seconds / (about_me.target_hours * 3600) * 100, 100)

    bg_start = theme.get("background.start", "#FFE5F1")
    bg_end = theme.get("background.end", "#E8F9FF")
    text_primary = theme.get("text.primary", "#5D4E6D")
    text_secondary = theme.get("text.secondary", "#8B7BA8")
    text_muted = theme.get("text.muted", "#B8A9C9")
    accent_main = theme.get("accent.main", "#FF85A2")
    accent_sec = theme.get("accent.secondary", "#7DD3FC")
    accent_ter = theme.get("accent.tertiary", "#FCD34D")
    accent_pink = theme.get("accent.pink", "#FF9EBB")
    accent_purple = theme.get("accent.purple", "#B088F9")
    accent_mint = theme.get("accent.mint", "#6EE7B7")
    card_bg = theme.get("card.bg", "#FFFFFF")
    card_border = theme.get("card.border", "#F0D9E8")

    radius = theme.borderRadius

    font_round = theme.fonts.get("round", "Nunito, sans-serif")
    font_title = theme.fonts.get("title", "Fredoka One, cursive")
    font_display = theme.fonts.get("display", "Fredoka One, cursive")

    username = gh_user.get("login", about_me.username) if gh_user else about_me.username
    public_repos = gh_user.get("public_repos", 0) if gh_user else 0
    followers = gh_user.get("followers", 0) if gh_user else 0
    total_stars = sum(r.get("stargazers_count", 0) for r in gh_repos)

    languages = waka_details.get("languages", []) if waka_details else []
    selected_langs = []
    lang_dict = {lang.get("name"): lang for lang in languages}
    for target in theme.topLanguages:
        if target in lang_dict:
            selected_langs.append(lang_dict[target])

    sections = []

    sections.append(f'''
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{bg_start}"/>
      <stop offset="100%" style="stop-color:{bg_end}"/>
    </linearGradient>
    <linearGradient id="progressShine" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#fff" stop-opacity="0"/>
      <stop offset="50%" stop-color="#fff" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.1"/>
    </filter>
    <pattern id="dots" width="12" height="12" patternUnits="userSpaceOnUse">
      <circle cx="6" cy="6" r="1.5" fill="{text_muted}" opacity="0.3"/>
    </pattern>
    <clipPath id="bgClip">
      <rect width="{canvas_width}" height="{canvas_height}" rx="{radius}"/>
    </clipPath>
  </defs>

  <rect width="{canvas_width}" height="{canvas_height}" fill="url(#bgGrad)" rx="{radius}"/>
    <rect width="{canvas_width}" height="{canvas_height}" fill="url(#dots)" rx="{radius}"/>

  <g clip-path="url(#bgClip)">
    <circle cx="30" cy="25" r="8" fill="{accent_pink}" opacity="0.6"/>
    <circle cx="50" cy="40" r="5" fill="{accent_sec}" opacity="0.5"/>
    <circle cx="25" cy="170" r="6" fill="{accent_ter}" opacity="0.5"/>
    <circle cx="570" cy="30" r="7" fill="{accent_purple}" opacity="0.5"/>
    <circle cx="580" cy="160" r="9" fill="{accent_mint}" opacity="0.4"/>
    <circle cx="550" cy="50" r="4" fill="{accent_main}" opacity="0.6"/>

    <polygon points="560,20 563,28 572,28 565,34 568,42 560,37 552,42 555,34 548,28 557,28" 
             fill="{accent_ter}" opacity="0.7"/>
    <polygon points="45,160 47,166 54,166 49,170 51,176 45,172 39,176 41,170 36,166 43,166" 
             fill="{accent_main}" opacity="0.6"/>
    <polygon points="520,175 522,181 529,181 524,185 526,191 520,187 514,191 516,185 511,181 518,181" 
             fill="{accent_sec}" opacity="0.6"/>
  </g>''')

    card_w = 140
    card_h = canvas_height - margin * 2
    card_x = margin
    card_y = margin

    sections.append(f'''
  <g class="identity-card">
    <rect x="{card_x}" y="{card_y}" width="{card_w}" height="{card_h}" 
          fill="{card_bg}" stroke="{card_border}" stroke-width="2" rx="{radius}" filter="url(#softShadow)"/>
    <text x="{card_x + card_w/2}" y="{card_y + 30}" text-anchor="middle" 
          fill="{text_primary}" font-family="{font_display}" font-size="22" font-weight="bold">
      {username[:8].upper()}
    </text>
    <text x="{card_x + card_w/2}" y="{card_y + 48}" text-anchor="middle" 
          fill="{accent_main}" font-family="{font_round}" font-size="9">
      {about_me.goal.get('title', '')}
    </text>
    <text x="{card_x + card_w/2}" y="{card_y + 62}" text-anchor="middle" 
          fill="{text_secondary}" font-family="{font_round}" font-size="8">
      {waka_text}
    </text>
    <rect x="{card_x + 10}" y="{card_y + 75}" width="{card_w - 20}" height="8" rx="4" 
          fill="{card_border}" opacity="0.3"/>
    <g>
      <defs>
        <clipPath id="progressClip_{card_x}">
          <rect x="{card_x + 10}" y="{card_y + 75}" width="0" height="8" rx="4">
            <animate attributeName="width" from="0" to="{(card_w - 20) * waka_progress / 100}" dur="1.5s" 
                     fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
          </rect>
        </clipPath>
      </defs>
      <rect x="{card_x + 10}" y="{card_y + 75}" width="{card_w - 20}" height="8" rx="4" 
            fill="{accent_sec}" clip-path="url(#progressClip_{card_x})"/>
      {'' if waka_progress == 0 else f'''
      <rect x="{card_x + 10 - 40}" y="{card_y + 75}" width="40" height="8" rx="4" 
            fill="url(#progressShine)" opacity="0" clip-path="url(#progressClip_{card_x})">
        <animate attributeName="opacity" values="0; 0.6" dur="0.3s" begin="1.6s" fill="freeze"/>
        <animate attributeName="x" 
                 values="{card_x + 10 - 40}; {card_x + 10 + max(0, (card_w - 20) * waka_progress / 100)}" 
                 dur="3s" begin="1.6s" repeatCount="indefinite" 
                 calcMode="spline" keySplines="0.25 0.1 0.25 1"/>
      </rect>
      '''}
    </g>
    <text x="{card_x + card_w/2}" y="{card_y + 95}" text-anchor="middle" 
          fill="{text_muted}" font-family="{font_round}" font-size="7">
      {waka_progress:.1f}% COMPLETE ✨
    </text>
    <!-- Coding Character - Generated from draw-interesting-object -->
    <g transform="translate({card_x + card_w/2 - 50}, {card_y + 102})">
      {generate_coding_character(is_modular=True, width=100, height=50, top_padding=4)}
    </g>
  </g>''')

    stats_x = card_x + card_w + 20
    stats = [
        {"label": "REPOS", "value": str(public_repos), "color": accent_sec},
        {"label": "STARS", "value": str(total_stars), "color": accent_ter},
        {"label": "FOLLOWERS", "value": str(followers), "color": accent_main},
    ]

    stat_w = 70
    for i, stat in enumerate(stats):
        sx = stats_x + i * (stat_w + 10)
        sections.append(f'''
  <g class="stat-{stat['label'].lower()}">
    <rect x="{sx}" y="{card_y}" width="{stat_w}" height="{card_h}" 
          fill="{card_bg}" stroke="{stat['color']}" stroke-width="2" rx="{radius}" filter="url(#softShadow)"/>
    <text x="{sx + stat_w/2}" y="{card_y + card_h/2 - 5}" text-anchor="middle" 
          fill="{stat['color']}" font-family="{font_display}" font-size="20" font-weight="bold">
      {stat['value']}
    </text>
    <text x="{sx + stat_w/2}" y="{card_y + card_h/2 + 12}" text-anchor="middle" 
          fill="{text_muted}" font-family="{font_round}" font-size="7">
      {stat['label']}
    </text>
  </g>''')

    lang_x = stats_x + len(stats) * (stat_w + 10) + 20
    lang_w = canvas_width - lang_x - margin

    sections.append(f'''
  <g class="languages">
    <line x1="{lang_x}" y1="{card_y}" x2="{lang_x}" y2="{card_y + card_h}" 
          stroke="{card_border}" stroke-width="2"/>
    <text x="{lang_x + 10}" y="{card_y + 20}" fill="{text_primary}" font-family="{font_title}" font-size="10">
      LANGUAGES ✨
    </text>''')

    bar_max_w = lang_w - 20
    bar_h = 14
    bar_y = card_y + 38

    for i, lang in enumerate(selected_langs[:4]):
        lang_color = theme.langColors.get(lang.get("name"), theme.editorColors[i % len(theme.editorColors)])
        percent = lang.get("percent", 0)
        bar_w = max(percent / 100 * bar_max_w, 10)
        lang_name = lang.get('name', '')
        
        min_bar_for_text = 45
        if bar_w >= min_bar_for_text:
            text_inside = True
            text_x = lang_x + 14
            text_color = "#FFFFFF"
        else:
            text_inside = False
            text_x = lang_x + bar_w + 14
            text_color = lang_color

        sections.append(f'''
    <rect x="{lang_x + 10}" y="{bar_y + i * 28}" width="{bar_w}" height="{bar_h}" 
          rx="7" fill="{lang_color}" opacity="0.8"/>
    <text x="{text_x}" y="{bar_y + i * 28 + 10}" fill="{text_color}" 
          font-family="{font_round}" font-size="7" font-weight="bold">
      {lang_name}
    </text>
    <text x="{lang_x + bar_max_w + 5}" y="{bar_y + i * 28 + 10}" fill="{text_muted}" 
          font-family="{font_round}" font-size="7">
      {percent:.0f}%
    </text>''')

    sections.append('  </g>')

    now = datetime.now().strftime("%Y-%m-%d")
    sections.append(f'''
  <text x="{canvas_width - margin}" y="{canvas_height - 8}" text-anchor="end" 
        fill="{text_muted}" font-family="{font_round}" font-size="10" font-style="italic">
    last update: {now}
  </text>''')

    svg = f'''<svg width="{canvas_width}" height="{canvas_height}" viewBox="0 0 {canvas_width} {canvas_height}" 
     xmlns="http://www.w3.org/2000/svg">
{chr(10).join(sections)}
</svg>'''

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"\n✅ Generated: {output_file}")

# Legacy, not used, await optimising
def generate_vertical_svg(waka_data, waka_details, gh_user, gh_repos, about_me, theme, output_file):
    """竖向方形/肖像布局 - 中心发散"""
    canvas_size = theme.canvas.get("width", 600)
    center = canvas_size / 2
    
    margin = 15

    waka_seconds = waka_data.get("total_seconds", 0) if waka_data else 0
    waka_text = waka_data.get("text", "0 hrs") if waka_data else "N/A"
    waka_progress = min(waka_seconds / (about_me.target_hours * 3600) * 100, 100)

    bg_start = theme.get("background.start", "#0D0D0D")
    bg_end = theme.get("background.end", "#1A1A1A")
    text_primary = theme.get("text.primary", "#FFFFFF")
    text_secondary = theme.get("text.secondary", "#B0B0B0")
    text_muted = theme.get("text.muted", "#666666")
    accent_main = theme.get("accent.main", "#FF3E00")
    accent_sec = theme.get("accent.secondary", "#00FF88")
    accent_ter = theme.get("accent.tertiary", "#FFEE00")
    card_bg = theme.get("card.bg", "#141414")
    card_border = theme.get("card.border", "#333333")

    font_mono = theme.fonts.get("primary", "Courier New, monospace")
    font_title = theme.fonts.get("title", "Arial Black, sans-serif")
    font_display = theme.fonts.get("display", "Impact, sans-serif")

    username = gh_user.get("login", about_me.username) if gh_user else about_me.username
    public_repos = gh_user.get("public_repos", 0) if gh_user else 0
    followers = gh_user.get("followers", 0) if gh_user else 0
    total_stars = sum(r.get("stargazers_count", 0) for r in gh_repos)

    languages = waka_details.get("languages", []) if waka_details else []
    selected_langs = []
    lang_dict = {lang.get("name"): lang for lang in languages}
    for target in theme.topLanguages:
        if target in lang_dict:
            selected_langs.append(lang_dict[target])

    sections = []

    sections.append(f'''
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{bg_start}"/>
      <stop offset="100%" style="stop-color:{bg_end}"/>
    </linearGradient>
    <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="{card_border}" stroke-width="0.5" opacity="0.3"/>
    </pattern>
    <pattern id="dots" width="8" height="8" patternUnits="userSpaceOnUse">
      <circle cx="4" cy="4" r="1" fill="{text_muted}" opacity="0.2"/>
    </pattern>
  </defs>

  <rect width="{canvas_size}" height="{canvas_size}" fill="url(#bgGrad)"/>
  <rect width="{canvas_size}" height="{canvas_size}" fill="url(#grid)"/>
  <rect width="{canvas_size}" height="{canvas_size}" fill="url(#dots)"/>

  <rect x="0" y="0" width="8" height="{canvas_size}" fill="{accent_main}"/>
  <rect x="{canvas_size-4}" y="0" width="4" height="{canvas_size}" fill="{accent_sec}"/>
  <rect x="0" y="{canvas_size-6}" width="{canvas_size}" height="6" fill="{accent_ter}"/>''')

    sections.append(f'''
   <g class="center-identity">
     <rect x="{center - 80}" y="{center - 80}" width="160" height="160" 
           fill="none" stroke="{accent_main}" stroke-width="3" transform="rotate(15 {center} {center})"/>
     <rect x="{center - 75}" y="{center - 75}" width="150" height="150" 
           fill="{card_bg}" stroke="{card_border}" stroke-width="2"/>
     <text x="{center}" y="{center - 10}" text-anchor="middle" 
           fill="{text_primary}" font-family="{font_display}" font-size="36" font-weight="bold">
       {username[:8].upper()}
     </text>
     <text x="{center}" y="{center + 20}" text-anchor="middle" 
           fill="{accent_main}" font-family="{font_mono}" font-size="11">
       {about_me.goal.get('title', '10K HOURS')}
     </text>
     <text x="{center}" y="{center + 40}" text-anchor="middle" 
           fill="{text_secondary}" font-family="{font_mono}" font-size="10">
       {waka_text}
     </text>
   </g>

   <rect x="40" y="40" width="60" height="60" fill="none" stroke="{accent_sec}" stroke-width="1" opacity="0.4"/>
   <rect x="{canvas_size-100}" y="{canvas_size-100}" width="60" height="60" fill="none" stroke="{accent_ter}" stroke-width="1" opacity="0.4"/>
   <polygon points="{canvas_size-50},50 {canvas_size-30},50 {canvas_size-50},70" fill="{accent_main}" opacity="0.6"/>
   <polygon points="50,{canvas_size-50} 70,{canvas_size-50} 50,{canvas_size-30}" fill="{accent_sec}" opacity="0.6"/>''')

    stats_data = [
        {"label": "REPOS", "value": str(public_repos), "color": accent_sec},
        {"label": "STARS", "value": str(total_stars), "color": accent_ter},
        {"label": "FOLLOWERS", "value": str(followers), "color": accent_main},
        {"label": "PROGRESS", "value": f"{waka_progress:.0f}%", "color": accent_sec},
    ]

    positions = [
        (center + 140, center - 140),
        (center + 140, center + 140),
        (center - 140, center + 140),
        (center - 140, center - 140),
    ]

    for i, stat in enumerate(stats_data):
        x, y = positions[i]
        sections.append(f'''
    <line x1="{center}" y1="{center}" x2="{x}" y2="{y}" 
          stroke="{stat['color']}" stroke-width="1" stroke-dasharray="4,4" opacity="0.5"/>
    <g class="stat-{stat['label'].lower()}">
      <text x="{x}" y="{y}" text-anchor="middle" 
            fill="{stat['color']}" font-family="{font_display}" font-size="28" font-weight="bold">
        {stat['value']}
      </text>
      <text x="{x}" y="{y + 18}" text-anchor="middle" 
            fill="{text_muted}" font-family="{font_mono}" font-size="9">
        {stat['label']}
      </text>
    </g>''')

    lang_y = canvas_size - 80
    sections.append(f'''
  <g class="languages">
    <line x1="30" y1="{lang_y - 15}" x2="{canvas_size - 30}" y2="{lang_y - 15}" 
          stroke="{card_border}" stroke-width="2"/>
    <text x="30" y="{lang_y - 25}" fill="{text_primary}" font-family="{font_title}" font-size="12">
      LANGUAGES
    </text>''')

    bar_start_x = 30
    bar_width = (canvas_size - 60) / max(len(selected_langs), 1)
    max_bar_height = 25

    for i, lang in enumerate(selected_langs[:5]):
        lang_color = theme.langColors.get(lang.get("name"), theme.editorColors[i % len(theme.editorColors)])
        percent = lang.get("percent", 0)
        bar_h = max(percent / 100 * max_bar_height, 4)

        sections.append(f'''
      <rect x="{bar_start_x + i * bar_width + 2}" y="{lang_y}" 
            width="{bar_width - 4}" height="{bar_h}" fill="{lang_color}"/>
      <text x="{bar_start_x + i * bar_width + bar_width/2}" y="{lang_y - 4}" 
            text-anchor="middle" fill="{text_secondary}" font-family="{font_mono}" font-size="7">
        {lang.get('name', '')[:6]}
      </text>''')

    sections.append('  </g>')

    now = datetime.now().strftime("%Y-%m-%d")
    sections.append(f'''
  <text x="{canvas_size - margin}" y="{canvas_size - 12}" text-anchor="end" 
        fill="{text_muted}" font-family="{font_mono}" font-size="10" font-style="italic">
    last update: {now}
  </text>''')

    svg = f'''<svg width="{canvas_size}" height="{canvas_size}" viewBox="0 0 {canvas_size} {canvas_size}" 
     xmlns="http://www.w3.org/2000/svg">
{chr(10).join(sections)}
</svg>'''

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"\n✅ Generated: {output_file}")


def main():
    """主函数 - 按流水线逻辑组织"""

    # 首先尝试从 .env 文件加载环境变量（本地开发时使用）
    load_env_file()

    # 获取环境变量
    waka_key = os.environ.get("WAKATIME_API_KEY")
    gh_token = os.environ.get("GH_TOKEN")
    username = os.environ.get("GITHUB_USERNAME") or "shyu216"

    print("\n" + "="*50)
    print(" 🚀 Stats Generator")
    print("="*50)

    # ========== Stage 1: 获取远程数据 ==========
    print("\n📡 Stage 1: Fetching remote data...")

    # 检查 Token 是否存在
    if not waka_key and not gh_token:
        print("\n⚠️ Warning: No API tokens configured. Using mock data.")
        waka_data = None
        gh_user = None
    else:
        # 获取 WakaTime 数据
        waka_data = None
        waka_details = None

        if waka_key:
            waka_data = fetch_wakatime_stats(waka_key)
            if waka_data is None:
                print("\n⚠️ Warning: Failed to fetch WakaTime data, using mock data")
            else:
                waka_details = fetch_wakatime_details(waka_key)
                if waka_details is None:
                    print("\n⚠️ Warning: Failed to fetch WakaTime details, using basic data")
        else:
            print("\n⚠️ WAKATIME_API_KEY not set, skipping WakaTime")

        # 获取 GitHub 数据
        gh_user = None
        gh_repos = []
        gh_orgs = []

        if gh_token:
            print("\n🔐 Checking GitHub Token...")

            if not fetch_token_info(gh_token):
                print("\n⚠️ Warning: Invalid GitHub token, using mock data")
            else:
                gh_user = fetch_github_user(gh_token, username)
                if gh_user is None:
                    print(f"\n⚠️ Warning: Failed to fetch GitHub user for '{username}', using mock data")
                else:
                    gh_repos, _, _ = fetch_github_repos(gh_token, username)
                    gh_orgs = fetch_github_orgs(gh_token, username)
                    fetch_github_events(gh_token, username)
                    fetch_github_starred(gh_token, username)
        else:
            print("\n⚠️ GH_TOKEN not set, skipping GitHub")

    # ========== Stage 2: 加载本地配置 ==========
    print("\n📂 Stage 2: Loading local configurations...")

    try:
        theme = Theme(THEME_FILE)
        print(f"   ✓ Loaded theme: {THEME_FILE}")
    except FileNotFoundError:
        print(f"\n⚠️ Warning: Theme file not found: {THEME_FILE}, using default theme")
        theme = None
    except Exception as e:
        print(f"\n⚠️ Warning: Failed to load theme: {e}, using default theme")
        theme = None

    try:
        about_me = AboutMe(ABOUT_FILE)
        print(f"   ✓ Loaded profile: {ABOUT_FILE}")
    except FileNotFoundError:
        print(f"\n⚠️ Warning: Profile file not found: {ABOUT_FILE}, using default profile")
        about_me = None
    except Exception as e:
        print(f"\n⚠️ Warning: Failed to load profile: {e}, using default profile")
        about_me = None

    # ========== Stage 3: 生成 SVG ==========
    print("\n🎨 Stage 3: Generating SVG...")

    generate_svg(waka_data, waka_details, gh_user, gh_repos, about_me, theme, "stats.svg")

    print("\n" + "="*50)
    print(" ✅ All Done!")
    print("="*50 + "\n")


if __name__ == "__main__":
    with OutputRedirector(OUTPUT_FILE):
        main()
