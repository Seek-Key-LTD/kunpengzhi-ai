"""
螺旋谱渲染测试 — 验证八席位根音坐标
输出：spiral_test.png
"""

import math
import sys
import os

# 确保能找到 core 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.seats import SEATS, ROOT_OFFSET, PENTATONIC_DEGREES

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("需要 Pillow: pip install Pillow")
    sys.exit(1)

# ── 参数 ──
IMG_SIZE = 2000
CX = CY = IMG_SIZE // 2
MAX_RADIUS = IMG_SIZE * 0.42
LOOPS = 8
NOTES_PER_LOOP = 12
DEGREES_PER_NOTE = 360 / NOTES_PER_LOOP

COLORS = [
    "#ff6b35", "#35c87d", "#7b68ee", "#ffd700",
    "#ff4757", "#1e90ff", "#ff69b4", "#00fa9a",
]


def degree_to_xy(deg: float, r: float) -> tuple:
    rad = math.radians(deg)
    return CX + math.cos(rad) * r, CY + math.sin(rad) * r


def main():
    img = Image.new("RGBA", (IMG_SIZE, IMG_SIZE), (10, 10, 15, 255))
    draw = ImageDraw.Draw(img)
    font_small = ImageFont.load_default()
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 22)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 30)
    except (IOError, OSError):
        font_large = font_title = font_small

    # 标题
    draw.text((CX, 40), "螺线谱 · 八席位拓扑验证", fill="#e0d9c8", font=font_title, anchor="mt")

    # 外圈八卦符号
    for i, (seat_id, seat) in enumerate(SEATS.items()):
        a = (i / 8) * 2 * math.pi - math.pi / 2
        r = MAX_RADIUS + 50
        x, y = CX + math.cos(a) * r, CY + math.sin(a) * r
        color = COLORS[i % len(COLORS)]
        draw.text((x, y), seat["gua"], fill=color + "cc",
                  font=font_large, anchor="mm")
        # 席位名称
        draw.text((x, y + 30), f"{seat['note']} · {seat['name']}",
                  fill=color + "88", font=font_small, anchor="mm")

    # 所有8个根音的螺旋骨架
    for seat_idx, (seat_id, seat) in enumerate(SEATS.items()):
        root_offset = ROOT_OFFSET[seat["note"]]
        color = COLORS[seat_idx % len(COLORS)]

        # 五声音阶辐射线
        for pen_idx in PENTATONIC_DEGREES[seat["note"]]:
            deg = root_offset * DEGREES_PER_NOTE + pen_idx * DEGREES_PER_NOTE
            rad = math.radians(deg)
            for loop in range(1, LOOPS + 1):
                r = (loop / LOOPS) * MAX_RADIUS
                x1, y1 = degree_to_xy(deg - 1, r)
                x2, y2 = degree_to_xy(deg + 1, r)
                draw.line([(x1, y1), (x2, y2)], fill=color + "80", width=1)

    # 测试粒子点：每个根音的五声音阶位置
    for seat_idx, (seat_id, seat) in enumerate(SEATS.items()):
        root_offset = ROOT_OFFSET[seat["note"]]
        color = COLORS[seat_idx % len(COLORS)]
        for pen_idx in PENTATONIC_DEGREES[seat["note"]]:
            base_deg = root_offset * DEGREES_PER_NOTE + pen_idx * DEGREES_PER_NOTE
            for loop in range(0, LOOPS + 1):
                deg = base_deg + loop * 360
                r = (loop / LOOPS) * MAX_RADIUS
                x, y = degree_to_xy(deg, r)
                size = 5 if loop % 2 == 0 else 3
                draw.ellipse([x - size, y - size, x + size, y + size],
                             fill=color + "aa", outline=color)

    # 中心圆
    draw.ellipse([CX - 20, CY - 20, CX + 20, CY + 20],
                 fill=(30, 30, 50, 255), outline="#e0d9c8", width=2)

    # 图例
    legend_x = 50
    legend_y = IMG_SIZE - 50 - len(SEATS) * 30
    draw.text((legend_x, legend_y - 40), "席位图例：", fill="#e0d9c8",
              font=font_small, anchor="lt")
    for i, (seat_id, seat) in enumerate(SEATS.items()):
        color = COLORS[i % len(COLORS)]
        y = legend_y + i * 30
        draw.ellipse([legend_x, y, legend_x + 12, y + 12],
                     fill=color + "cc")
        draw.text((legend_x + 20, y + 2),
                  f"{seat['gua']} {seat['note']:>3} · {seat['name']:<5}  {seat['frequency']:>6.2f}Hz  {'正' if seat['role'].value == 'pro' else '反'}方 {seat['trigram']}",
                  fill=color + "cc", font=font_small, anchor="lt")

    # 参数信息
    params = (
        f"LOOPS={LOOPS} | NOTES/LOOP={NOTES_PER_LOOP} | "
        f"5音阶(宫商角徵羽)={PENTATONIC_DEGREES[SEATS['seat_1']['note']]}"
    )
    draw.text((CX, IMG_SIZE - 20), params, fill="#555",
              font=font_small, anchor="mb")

    output_path = os.path.join(os.path.dirname(__file__), "spiral_test.png")
    img.save(output_path)
    print(f"✅ 螺旋谱测试图已保存: {output_path}")
    print(f"   尺寸: {IMG_SIZE}x{IMG_SIZE}")
    print(f"   席位: {len(SEATS)}")
    print(f"   每个席位: {len(PENTATONIC_DEGREES[SEATS['seat_1']['note']])} 音阶")
    print(f"   螺旋圈数: {LOOPS}")


if __name__ == "__main__":
    main()