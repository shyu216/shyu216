#!/usr/bin/env python3
"""
Draw Interesting Object - 优化版程序员打字动画SVG
画布: 60x30，人物居中，暖色调
"""
import random

def generate_code_particles():
    """生成飞出的代码粒子 - 限制在画布内"""
    particles = []
    symbols = [
        "&lt;/&gt;",
        "::",
        "[]",
        "&lt;&lt;",
        "int",
        "func",
        "let",
        "const",
        "new",
        "try",
        "catch",
        "()",
        "fn",
        "*",
        "yield",
        "void",
        "async",
        "&lt;&gt;",
        "{}",
        "=&gt;",
        ":=",
        "&amp;",
        "||",
        "!",
        "@",
    ]

    colors = ["#58a6ff", "#7ee787", "#ffa657", "#d2a8ff"]

    random.shuffle(symbols)

    for i, symbol in enumerate(symbols):
        # 左右两侧都向外发散
        x = 38 if i % 2 == 0 else 16
        y = 6 + (i * 3) % 10
        end_x = 10 if i % 2 == 0 else -10
        end_y = -2 + (i % 3) * 4

        duration = random.gauss(mu=2, sigma=0.3)
        duration = max(0, min(5, duration))

        delay = random.gauss(mu=6, sigma=3)
        delay = max(0.0, min(20, delay))

        particles.append(f'''    <g opacity="0">
      <text x="{x}" y="{y}" fill="{colors[i % len(colors)]}" font-size="2.5" font-family="monospace" font-weight="bold">{symbol}</text>
      <animate attributeName="opacity" values="0; 0.8; 0" dur="{duration}s" begin="{delay}s" repeatCount="indefinite"/>
      <animateTransform attributeName="transform" type="translate" values="0 0; {end_x} {end_y}" dur="{duration}s" begin="{delay}s" repeatCount="indefinite"/>
    </g>''')

    return '\n'.join(particles)

def generate_brain_waves():
    """删除脑电波"""
    return ''

def generate_typing_hands():
    """生成双手打字动画 - 暖黄色"""
    return '''    <!-- Left hand typing -->
    <g>
      <line x1="22" y1="22" x2="18" y2="25" stroke="#f4a460" stroke-width="2" stroke-linecap="round">
        <animate attributeName="y2" values="25; 23; 25" dur="0.2s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"/>
        <animate attributeName="x2" values="18; 17; 18" dur="0.2s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"/>
      </line>
      <circle cx="17" cy="26" r="2" fill="#ffdbac">
        <animate attributeName="cy" values="26; 24; 26" dur="0.2s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"/>
        <animate attributeName="cx" values="17; 16; 17" dur="0.2s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"/>
      </circle>
    </g>
    <!-- Right hand typing -->
    <g>
      <line x1="34" y1="22" x2="38" y2="25" stroke="#f4a460" stroke-width="2" stroke-linecap="round">
        <animate attributeName="y2" values="25; 23; 25" dur="0.2s" begin="0.05s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"/>
        <animate attributeName="x2" values="38; 39; 38" dur="0.2s" begin="0.05s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"/>
      </line>
      <circle cx="39" cy="26" r="2" fill="#ffdbac">
        <animate attributeName="cy" values="26; 24; 26" dur="0.2s" begin="0.05s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"/>
        <animate attributeName="cx" values="39; 40; 39" dur="0.2s" begin="0.05s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"/>
      </circle>
    </g>'''

def generate_screen_code():
    """生成屏幕上的代码动画"""
    lines = []
    colors = ["#7ee787", "#ffa657", "#d2a8ff", "#79c0ff"]

    for i in range(4):
        y = 4 + i * 2.5
        base_width = 22 + i * 2
        color = colors[i % len(colors)]
        dur = 0.6 + i * 0.1
        begin = i * 0.08

        lines.append(f'''        <line x1="21" y1="{y}" x2="{base_width}" y2="{y}" stroke="{color}" stroke-width="1.2">
          <animate attributeName="x2" values="{base_width}; {base_width + 6}; {base_width}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>
          <animate attributeName="opacity" values="0.7; 1; 0.7" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>
        </line>''')

    return '\n'.join(lines)

def generate_coffee_steam():
    """生成咖啡热气动画"""
    return '''    <!-- Coffee cup with steam -->
    <g transform="translate(45, 24)">
      <rect x="0" y="0" width="4" height="5" rx="0.8" fill="#ffa657" opacity="0.9"/>
      <path d="M 4 1 Q 5.5 1, 5.5 2.5 Q 5.5 4.5, 4 4.25" stroke="#ffa657" stroke-width="0.8" fill="none" opacity="0.9"/>
      <g opacity="0">
        <circle cx="1" cy="-0.5" r="0.6" fill="#8b949e" opacity="0.5"/>
        <animate attributeName="opacity" values="0; 0.5; 0" dur="2s" repeatCount="indefinite"/>
        <animateTransform attributeName="transform" type="translate" values="0 0; 0.5 -3" dur="2s" repeatCount="indefinite"/>
      </g>
      <g opacity="0">
        <circle cx="2.5" cy="-1" r="0.5" fill="#8b949e" opacity="0.4"/>
        <animate attributeName="opacity" values="0; 0.4; 0" dur="2.5s" begin="0.8s" repeatCount="indefinite"/>
        <animateTransform attributeName="transform" type="translate" values="0 0; -0.3 -3.5" dur="2.5s" begin="0.8s" repeatCount="indefinite"/>
      </g>
    </g>'''

def generate_keyboard():
    """生成键盘造型 - 放在人前"""
    return '''    <!-- Keyboard in front of person -->
    <g transform="translate(15, 26)">
      <!-- Keyboard base -->
      <rect x="0" y="0" width="26" height="4" rx="1" fill="#30363d" stroke="#484f58" stroke-width="0.5"/>
      <!-- Space bar (现在在上方) -->
      <rect x="6" y="0.8" width="10" height="1.2" rx="0.3" fill="#21262d"/>
      <!-- Keys (现在在下方) -->
      <rect x="1.5" y="2.5" width="2" height="1.2" rx="0.3" fill="#21262d"/>
      <rect x="4" y="2.5" width="2" height="1.2" rx="0.3" fill="#21262d"/>
      <rect x="6.5" y="2.5" width="2" height="1.2" rx="0.3" fill="#21262d"/>
      <rect x="9" y="2.5" width="2" height="1.2" rx="0.3" fill="#21262d"/>
      <rect x="11.5" y="2.5" width="2" height="1.2" rx="0.3" fill="#21262d"/>
      <rect x="14" y="2.5" width="2" height="1.2" rx="0.3" fill="#21262d"/>
      <rect x="16.5" y="2.5" width="2" height="1.2" rx="0.3" fill="#21262d"/>
      <rect x="19" y="2.5" width="2" height="1.2" rx="0.3" fill="#21262d"/>
      <rect x="21.5" y="2.5" width="2" height="1.2" rx="0.3" fill="#21262d"/>
      <!-- Key press glow -->
      <ellipse cx="13" cy="2" rx="10" ry="1.5" fill="#58a6ff" opacity="0">
        <animate attributeName="opacity" values="0; 0.2; 0" dur="0.15s" repeatCount="indefinite"/>
      </ellipse>
    </g>'''

def generate_face_expression():
    """简化面部表情 - 暖黄色，带嘴巴动画"""
    # 暖色调主题色
    FACE_COLOR = "#ffdbac"        # 脸部肤色
    MOUTH_STROKE = "#a0452e"      # 暖棕色描边
    MOUTH_FILL_DARK = "#a0452e"   # 暖红色（嘴巴内部）
    MOUTH_FILL_MID = "#a0452e"    # 中暖棕色填充
    return f'''    <!-- Face - warm skin tone -->
    <circle cx="28" cy="18" r="6" fill="#ffdbac"/>
    <!-- Simple eyes -->
    <circle cx="25.5" cy="17" r="1.2" fill="#333"/>
    <circle cx="30.5" cy="17" r="1.2" fill="#333"/>
    <!-- Eye shine -->
    <circle cx="25.8" cy="16.7" r="0.4" fill="#fff" opacity="0.8"/>
    <circle cx="30.8" cy="16.7" r="0.4" fill="#fff" opacity="0.8"/>
    <!-- Animated mouth: smile -> dot -> circle(O) -> dot -> smile -->
    <g>
      <!-- Mouth shape (curve or circle) -->
      <path stroke="{MOUTH_STROKE}" stroke-width="0.8" fill="none" stroke-linecap="round">
        <!-- 核心路径动画：微笑→缩点→小圆→大圆→小圆→缩点→微笑 -->
        <animate attributeName="d"
          values="
            M 25 20.5 Q 28 23, 31 20.5;
            M 28 21.5 Q 28 21.5, 28 21.5;
            M 28 21 A 0.5 0.5 0 1 1 28 22 A 0.5 0.5 0 1 1 28 21;
            M 28 20.5 A 1 1 0 1 1 28 22.5 A 1 1 0 1 1 28 20.5;
            M 28 21 A 0.5 0.5 0 1 1 28 22 A 0.5 0.5 0 1 1 28 21;
            M 28 21.5 Q 28 21.5, 28 21.5;
            M 25 20.5 Q 28 23, 31 20.5"
          dur="6s"
          repeatCount="indefinite"
          calcMode="spline"
          keyTimes="0;0.45;0.45;0.5;0.6;0.6;1"
          keySplines="0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1"/>

        <!-- 填充动画：微笑时脸部肤色填充（凹陷效果），变圆时暖棕色实心（嘴巴内部） -->
        <animate attributeName="fill"
          values="{FACE_COLOR};{FACE_COLOR};{MOUTH_FILL_MID};{MOUTH_FILL_DARK};{MOUTH_FILL_MID};{FACE_COLOR};{FACE_COLOR}"
          dur="6s"
          repeatCount="indefinite"
          keyTimes="0;0.45;0.45;0.5;0.6;0.6;1"/>

        <!-- 描边动画：微笑时有暖棕色描边，变圆时隐藏描边 -->
        <animate attributeName="stroke"
          values="{MOUTH_STROKE};{MOUTH_STROKE};none;none;none;{MOUTH_STROKE};{MOUTH_STROKE}"
          dur="6s"
          repeatCount="indefinite"
          keyTimes="0;0.45;0.45;0.5;0.6;0.6;1"/>
      </path>
    </g>'''

def generate_body():
    """生成身体部分 - 删除蓝色"""
    return ''

def generate_screen():
    """生成电脑屏幕"""
    return f'''    <!-- Computer Screen -->
    <defs>
      <filter id="screenGlow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="1.5" result="blur"/>
        <feMerge>
          <feMergeNode in="blur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
    </defs>
    <rect x="18" y="0" width="20" height="14" rx="2" fill="#161b22" stroke="#30363d" stroke-width="1" filter="url(#screenGlow)"/>
    <!-- Screen inner -->
    <rect x="19.5" y="1" width="17" height="11" rx="1" fill="#0d1117"/>
    <!-- Code lines container -->
    <g clip-path="url(#screenClipCode)">
      <defs>
        <clipPath id="screenClipCode">
          <rect x="20" y="1.5" width="16" height="10" rx="0.5"/>
        </clipPath>
      </defs>
{generate_screen_code()}
    </g>
    <!-- Screen reflection -->
    <path d="M 19.5 1 L 25 1 L 22 12 L 19.5 12 Z" fill="#f0f6fc" opacity="0.03"/>'''

def generate_svg(is_modular=False, width=60, height=30, top_padding=0):
    """生成完整的SVG
    
    Args:
        is_modular: 是否为模块化模式（用于嵌入其他SVG）
        width: SVG宽度
        height: SVG高度
        top_padding: 顶部padding（用于防止glow效果被截断）
    """
    if is_modular:
        # 模块化模式：使用辅助函数拼凑
        viewbox_h = 30 + top_padding
        svg_height = height + (top_padding * height / 30)
        
        # 生成屏幕（带glow filter）
        screen_content = generate_screen_code()
        screen_svg = f'''    <defs>
      <filter id="screenGlow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="1.5" result="blur"/>
        <feMerge>
          <feMergeNode in="blur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
    </defs>
    <rect x="18" y="0" width="20" height="14" rx="2" fill="#161b22" stroke="#30363d" stroke-width="1" filter="url(#screenGlow)"/>
    <rect x="19.5" y="1" width="17" height="11" rx="1" fill="#0d1117"/>
    <g clip-path="url(#screenClipCode)">
      <defs>
        <clipPath id="screenClipCode">
          <rect x="20" y="1.5" width="16" height="10" rx="0.5"/>
        </clipPath>
      </defs>
{screen_content}
    </g>'''
        
        return f'''<svg viewBox="0 0 60 {viewbox_h}" width="{width}" height="{svg_height}">
  <g id="coding-character" transform="translate(0, {top_padding})">
{screen_svg}

    <!-- Flying code particles -->
{generate_code_particles()}

    <!-- Brain waves -->
{generate_brain_waves()}

    <!-- Face -->
{generate_face_expression()}

    <!-- Body -->
{generate_body()}

    <!-- Keyboard -->
{generate_keyboard()}

    <!-- Hands typing -->
{generate_typing_hands()}

    <!-- Coffee -->
{generate_coffee_steam()}
  </g>
</svg>'''
    
    # 独立文件模式
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 30" width="60" height="30">
  <!-- Main character group - centered -->
  <g id="coding-character">
{generate_screen()}

    <!-- Flying code particles -->
{generate_code_particles()}

    <!-- Brain waves -->
{generate_brain_waves()}

    <!-- Face -->
{generate_face_expression()}

    <!-- Body -->
{generate_body()}

    <!-- Keyboard -->
{generate_keyboard()}

    <!-- Hands typing -->
{generate_typing_hands()}

    <!-- Coffee -->
{generate_coffee_steam()}
  </g>
</svg>'''

    return svg_content

def main():
    """主函数"""
    svg = generate_svg()

    with open('interesting-object.svg', 'w', encoding='utf-8') as f:
        f.write(svg)

    print("✅ Generated interesting-object.svg successfully!")
    print(f"📄 File size: {len(svg)} bytes")

if __name__ == '__main__':
    main()
