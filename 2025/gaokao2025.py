import os
import requests
from PIL import Image
from time import sleep

# 保存目录
SAVE_DIR = "原始gif"

# 创建目录
os.makedirs(SAVE_DIR, exist_ok=True)

# 在SAVE_DIR下分别创建"历史类"和"物理类"子目录
HISTORY_DIR = os.path.join(SAVE_DIR, "历史类")
PHYSICS_DIR = os.path.join(SAVE_DIR, "物理类")
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
    filename = os.path.join(HISTORY_DIR, f"历史类招生2025_{i:03d}.gif")

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
    filename = os.path.join(PHYSICS_DIR, f"物理类招生2025_{i:03d}.gif")

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

PNG_DIR = "PNG格式"

# 创建目录
os.makedirs(PNG_DIR, exist_ok=True)

PNG_HISTORY_DIR = os.path.join(PNG_DIR, "历史类")
PNG_PHYSICS_DIR = os.path.join(PNG_DIR, "物理类")
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