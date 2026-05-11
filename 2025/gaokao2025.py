import os
import requests
from PIL import Image
from time import sleep
import cv2
import numpy as np
import re

# 保存目录
SAVE_DIR = "01.raw.gif"

# 创建目录
os.makedirs(SAVE_DIR, exist_ok=True)

# 在SAVE_DIR下分别创建"历史类"和"物理类"子目录
HISTORY_DIR = os.path.join(SAVE_DIR, "history")
PHYSICS_DIR = os.path.join(SAVE_DIR, "physics")
os.makedirs(HISTORY_DIR, exist_ok=True)
os.makedirs(PHYSICS_DIR, exist_ok=True)

# 请求头（模拟浏览器）
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    )
}

# 总页数
TOTAL_PAGES_HISTORY = 140
TOTAL_PAGES_PHYSICS = 232

# 下载历史类
for i in range(1, TOTAL_PAGES_HISTORY + 1):
    # 图片 URL
    url = f"https://plan.sceea.cn/img/wk/wk%20({i}).gif"

    # 本地文件名
    filename = os.path.join(HISTORY_DIR, f"history_2025_{i:03d}.gif")

    # 如果文件已存在，则跳过
    if os.path.exists(filename):
        print(f"跳过已存在的文件: {filename}")
        continue

    try:
        print(f"下载 {i}...")

        response = requests.get(url, headers=headers, timeout=20)

        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)

            print(f"保存: {filename}")

        else:
            print(f"下载失败页面 {i}, 状态={response.status_code}")

    except Exception as e:
        print(f"下载页面 {i} 时出错: {e}")

    # 防止请求过快
    sleep(0.2)

# 下载物理类
for i in range(1, TOTAL_PAGES_PHYSICS + 1):
    # 图片 URL
    url = f"https://plan.sceea.cn/img/lk/lk%20({i}).gif"

    # 本地文件名
    filename = os.path.join(PHYSICS_DIR, f"physics_2025_{i:03d}.gif")

    # 如果文件已存在，则跳过
    if os.path.exists(filename):
        print(f"跳过已存在的文件: {filename}")
        continue

    try:
        print(f"下载 {i}...")

        response = requests.get(url, headers=headers, timeout=20)

        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)

            print(f"保存: {filename}")

        else:
            print(f"下载失败页面 {i}, 状态={response.status_code}")

    except Exception as e:
        print(f"下载页面 {i} 时出错: {e}")

    # 防止请求过快
    sleep(0.2)

# 将gif转换成png格式

PNG_DIR = "02.png.format"

# 创建目录
os.makedirs(PNG_DIR, exist_ok=True)

PNG_HISTORY_DIR = os.path.join(PNG_DIR, "history")
PNG_PHYSICS_DIR = os.path.join(PNG_DIR, "physics")
os.makedirs(PNG_HISTORY_DIR, exist_ok=True)
os.makedirs(PNG_PHYSICS_DIR, exist_ok=True)

# 遍历HISTORY_DIR中的所有gif文件并转换成png格式
for gif_filename in os.listdir(HISTORY_DIR):
    # 只处理 gif 文件
    if not gif_filename.lower().endswith(".gif"):
        continue

    # 输出 png 文件名
    png_filename = os.path.splitext(gif_filename)[0] + ".png"
    png_path = os.path.join(PNG_HISTORY_DIR, png_filename)

    # 如果 PNG 已存在，则跳过
    if os.path.exists(png_path):
        print(f"跳过已存在的文件: {png_path}")
        continue

    try:
        print(f"转换: {gif_filename}")
        with Image.open(os.path.join(HISTORY_DIR, gif_filename)) as img:
            rgb_img = img.convert("RGB")
            rgb_img.save(png_path, "PNG")

        print(f"保存: {png_path}")
    except Exception as e:
        print(f"转换 {gif_filename} 时出错: {e}")

# 遍历PHYSICS_DIR中的所有gif文件并转换成png格式
for gif_filename in os.listdir(PHYSICS_DIR):
    # 只处理 gif 文件
    if not gif_filename.lower().endswith(".gif"):
        continue

    # 输出 png 文件名
    png_filename = os.path.splitext(gif_filename)[0] + ".png"
    png_path = os.path.join(PNG_PHYSICS_DIR, png_filename)

    # 如果 PNG 已存在，则跳过
    if os.path.exists(png_path):
        print(f"跳过已存在的文件: {png_path}")
        continue

    try:
        print(f"转换: {gif_filename}")
        with Image.open(os.path.join(PHYSICS_DIR, gif_filename)) as img:
            rgb_img = img.convert("RGB")
            rgb_img.save(png_path, "PNG")

        print(f"保存: {png_path}")
    except Exception as e:
        print(f"转换 {gif_filename} 时出错: {e}")

# =========================
# 去页眉和页脚
# =========================
CROP_ROOT_DIR = "03.no.header.footer"

CROP_HISTORY_DIR = os.path.join(CROP_ROOT_DIR, "history")
CROP_PHYSICS_DIR = os.path.join(CROP_ROOT_DIR, "physics")

os.makedirs(CROP_HISTORY_DIR, exist_ok=True)
os.makedirs(CROP_PHYSICS_DIR, exist_ok=True)

# 记录处理失败的文件
failed_files = []

# =========================
# 检测长横线
# =========================
def detect_horizontal_lines(binary_img):
    h, w = binary_img.shape

    candidate_lines = []

    for y in range(h):
        row = binary_img[y]

        black_pixels = np.sum(row == 0)

        # 长横线判断
        if black_pixels > w * 0.30:
            candidate_lines.append(y)

    # 合并邻近横线
    merged = []

    if candidate_lines:
        start = candidate_lines[0]
        prev = candidate_lines[0]

        for y in candidate_lines[1:]:
            if y - prev <= 3:
                prev = y
            else:
                merged.append((start + prev) // 2)
                start = y
                prev = y

        merged.append((start + prev) // 2)

    return merged

# =========================
# 检测三栏结构
# =========================
def has_three_columns(binary_region):
    h, w = binary_region.shape

    projection = np.sum(binary_region == 0, axis=0)

    # 平滑
    kernel = np.ones(15) / 15
    projection = np.convolve(projection, kernel, mode="same")

    threshold = np.max(projection) * 0.35

    mask = projection > threshold

    segments = []

    in_seg = False
    start = 0

    for i, val in enumerate(mask):
        if val and not in_seg:
            start = i
            in_seg = True

        elif not val and in_seg:
            end = i

            if end - start > w * 0.08:
                segments.append((start, end))

            in_seg = False

    if in_seg:
        end = w - 1

        if end - start > w * 0.08:
            segments.append((start, end))

    return len(segments) >= 3

# =========================
# 找正文顶部
# =========================
def find_content_top(binary_img, lines):
    h, w = binary_img.shape

    for y in lines:
        region_top = y + 10
        region_bottom = min(h, y + int(h * 0.12))

        if region_bottom <= region_top:
            continue

        region = binary_img[region_top:region_bottom, :]

        if has_three_columns(region):
            return y + 5

    return None

# =========================
# 找正文底部
# =========================
def find_content_bottom(binary_img, lines, content_top):
    h, w = binary_img.shape

    bottom_lines = [
        y for y in lines
        if y > content_top + h * 0.3
    ]

    if not bottom_lines:
        return h

    for y in reversed(bottom_lines):
        region_top = max(0, y - int(h * 0.08))
        region_bottom = y - 5

        if region_bottom <= region_top:
            continue

        region = binary_img[region_top:region_bottom, :]

        if has_three_columns(region):
            return y - 5

    return h

# =========================
# 处理单张图片
# =========================
def process_crop(input_path, output_path):
    print(f"处理: {input_path}")

    img = cv2.imread(input_path)

    if img is None:
        raise Exception("无法读取图片")

    h, w = img.shape[:2]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 二值化
    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        25,
        15
    )

    lines = detect_horizontal_lines(binary)

    if not lines:
        raise Exception("未检测到横线")

    content_top = find_content_top(binary, lines)

    if content_top is None:
        raise Exception("未找到正文顶部")

    content_bottom = find_content_bottom(
        binary,
        lines,
        content_top
    )

    if content_bottom <= content_top:
        raise Exception("正文区域异常")

    # 裁切
    cropped = img[content_top:content_bottom, :]

    # 安全检查
    crop_h = content_bottom - content_top

    if crop_h < h * 0.3:
        raise Exception("裁切区域过小")

    cv2.imwrite(output_path, cropped)

    print(f"保存: {output_path}")

# =========================
# 处理目录
# =========================
def process_directory(
    input_dir,
    output_dir,
    prefix,
    start_num,
    end_num
):
    pattern = re.compile(rf"{prefix}_(\d+)\.png")

    for filename in os.listdir(input_dir):

        match = pattern.match(filename)

        if not match:
            continue

        num = int(match.group(1))

        # 只处理指定范围
        if num < start_num or num > end_num:
            continue

        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        # 已存在则跳过
        if os.path.exists(output_path):
            print(f"跳过已存在文件: {output_path}")
            continue

        try:
            process_crop(input_path, output_path)

        except Exception as e:
            print(f"处理失败: {filename} -> {e}")
            failed_files.append(filename)


# =========================
# 处理目录
# =========================
def process_directory(
    input_dir,
    output_dir,
    prefix,
    start_num,
    end_num
):
    pattern = re.compile(rf"{prefix}_(\d+)\.png")

    for filename in os.listdir(input_dir):

        match = pattern.match(filename)

        if not match:
            continue

        num = int(match.group(1))

        # 只处理指定范围
        if num < start_num or num > end_num:
            continue

        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        # 已存在则跳过
        if os.path.exists(output_path):
            print(f"跳过已存在文件: {output_path}")
            continue

        try:
            process_crop(input_path, output_path)

        except Exception as e:
            print(f"处理失败: {filename} -> {e}")
            failed_files.append(filename)

# =========================
# 开始处理
# =========================

# 历史类
process_directory(
    PNG_HISTORY_DIR,
    CROP_HISTORY_DIR,
    "历史类招生2025",
    5,
    138
)

# 物理类
process_directory(
    PNG_PHYSICS_DIR,
    CROP_PHYSICS_DIR,
    "物理类招生2025",
    5,
    230
)

# =========================
# 输出失败文件
# =========================

print("\n========================")
print("处理失败文件")
print("========================")

if failed_files:
    for f in failed_files:
        print(f)

else:
    print("无")