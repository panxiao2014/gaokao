import os
import requests
from PIL import Image
from time import sleep
from utils.utils import process_header_footer_directory, split_columns_directory, ocr_process, single_json_process, json_data_cleaning


# 所有原始和处理后的文件都放在这个根目录下
ROOT_PIC_DIR = "/mnt/c/_temp/2026_高考_四川"

# 保存目录
SAVE_DIR = "01.raw.png"

# 创建目录
os.makedirs(os.path.join(ROOT_PIC_DIR, SAVE_DIR), exist_ok=True)

# 在SAVE_DIR下分别创建"历史类"和"物理类"子目录
HISTORY_DIR = os.path.join(ROOT_PIC_DIR, SAVE_DIR, "history")
PHYSICS_DIR = os.path.join(ROOT_PIC_DIR, SAVE_DIR, "physics")
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
TOTAL_PAGES_HISTORY = 160
TOTAL_PAGES_PHYSICS = 248

print("01. 开始下载...")
print(f"历史类总页数: {TOTAL_PAGES_HISTORY}")
print(f"物理类总页数: {TOTAL_PAGES_PHYSICS}")
print("=========================\n\n")

# 下载历史类
for i in range(1, TOTAL_PAGES_HISTORY + 1):
    # 图片 URL
    url = f"https://plan.sceea.cn/img/ls/tu/ls%20({i}).png"

    # 本地文件名
    filename = os.path.join(HISTORY_DIR, f"history_2026_{i:03d}.png")

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
    url = f"https://plan.sceea.cn/img/wl/tu/wl%20({i}).png"

    # 本地文件名
    filename = os.path.join(PHYSICS_DIR, f"physics_2026_{i:03d}.png")

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



# # =========================
# # 去页眉和页脚
# # =========================
CROP_ROOT_DIR = "02.no.header.footer"

CROP_HISTORY_DIR = os.path.join(ROOT_PIC_DIR, CROP_ROOT_DIR, "history")
CROP_PHYSICS_DIR = os.path.join(ROOT_PIC_DIR, CROP_ROOT_DIR, "physics")

os.makedirs(CROP_HISTORY_DIR, exist_ok=True)
os.makedirs(CROP_PHYSICS_DIR, exist_ok=True)

# 记录处理失败的文件
failed_files = []



print("02. 开始去页眉页脚...")
print("=========================\n\n")

# =========================================================
# 开始处理：历史类
# =========================================================

process_header_footer_directory(
    HISTORY_DIR,
    CROP_HISTORY_DIR,
    "history_2026",
    5,
    159,
    failed_files
)


# =========================================================
# 开始处理：物理类
# =========================================================

process_header_footer_directory(
    PHYSICS_DIR,
    CROP_PHYSICS_DIR,
    "physics_2026",
    5,
    247,
    failed_files
)


# =========================================================
# 输出失败文件
# =========================================================

print()
print("无法处理的文件:")

if failed_files:

    for filename in failed_files:
        print(filename)

else:

    print("无")


# # =========================
# # 分栏处理
# =========================
SPLIT_ROOT_DIR = "03.split.column"

SPLIT_HISTORY_DIR = os.path.join(ROOT_PIC_DIR, SPLIT_ROOT_DIR, "history")
SPLIT_PHYSICS_DIR = os.path.join(ROOT_PIC_DIR, SPLIT_ROOT_DIR, "physics")

os.makedirs(SPLIT_HISTORY_DIR, exist_ok=True)
os.makedirs(SPLIT_PHYSICS_DIR, exist_ok=True)

# 记录处理失败的文件
split_failed_files = []

print("04. 开始分栏处理...")
print("=========================\n\n")

# =========================================================
# 开始处理：历史类
# =========================================================
split_columns_directory(
    CROP_HISTORY_DIR,
    SPLIT_HISTORY_DIR,
    "history_2026",
    5,
    159,
    split_failed_files
)

# =========================================================
# 开始处理：物理类
# =========================================================
split_columns_directory(
    CROP_PHYSICS_DIR,
    SPLIT_PHYSICS_DIR,
    "physics_2026",
    5,
    204,
    split_failed_files
)

# =========================================================
# 输出失败文件
# =========================================================
print("分栏无法处理的文件:")

if split_failed_files:
    for filename in split_failed_files:
        print(filename)

else:
    print("无")


# # ============================================
# # OCR处理,使用Paddle OCR云服务
# # ============================================
OCR_ROOT_DIR = "05.ocr.result"

OCR_HISTORY_DIR = os.path.join(ROOT_PIC_DIR, OCR_ROOT_DIR, "history")
OCR_PHYSICS_DIR = os.path.join(ROOT_PIC_DIR, OCR_ROOT_DIR, "physics")

os.makedirs(OCR_HISTORY_DIR, exist_ok=True)
os.makedirs(OCR_PHYSICS_DIR, exist_ok=True)

# 记录处理失败的文件
ocr_failed_files = []

print("05. 开始OCR处理...")
print("=========================\n\n")

ocr_process(
    SPLIT_HISTORY_DIR,
    OCR_HISTORY_DIR,
    ocr_failed_files
)

ocr_process(
    SPLIT_PHYSICS_DIR,
    OCR_PHYSICS_DIR,
    ocr_failed_files
)

# =========================================================
# 输出失败文件
# =========================================================
print("OCR无法处理的文件:")

if ocr_failed_files:
    for filename in ocr_failed_files:
        print(filename)

else:
    print("无")


# # ============================================
# # 合并json文件
# # ============================================
SINGLE_JSON_ROOT_DIR = "06.single.result"

SINGLE_JSON_HISTORY_DIR = os.path.join(ROOT_PIC_DIR, SINGLE_JSON_ROOT_DIR, "history")
SINGLE_JSON_PHYSICS_DIR = os.path.join(ROOT_PIC_DIR, SINGLE_JSON_ROOT_DIR, "physics")

os.makedirs(SINGLE_JSON_HISTORY_DIR, exist_ok=True)
os.makedirs(SINGLE_JSON_PHYSICS_DIR, exist_ok=True)

single_json_process(OCR_HISTORY_DIR, SINGLE_JSON_HISTORY_DIR, "history.json")
single_json_process(OCR_PHYSICS_DIR, SINGLE_JSON_PHYSICS_DIR, "physics.json")


# # ============================================
# # 清洗json数据
# # ============================================
JSON_CLEAN_ROOT_DIR = "07.json.clean"

JSON_CLEAN_HISTORY_DIR = os.path.join(ROOT_PIC_DIR, JSON_CLEAN_ROOT_DIR, "history")
JSON_CLEAN_PHYSICS_DIR = os.path.join(ROOT_PIC_DIR, JSON_CLEAN_ROOT_DIR, "physics")

os.makedirs(JSON_CLEAN_HISTORY_DIR, exist_ok=True)
os.makedirs(JSON_CLEAN_PHYSICS_DIR, exist_ok=True)

json_data_cleaning(
    SINGLE_JSON_HISTORY_DIR,
    JSON_CLEAN_HISTORY_DIR
)

json_data_cleaning(
    SINGLE_JSON_PHYSICS_DIR,
    JSON_CLEAN_PHYSICS_DIR
)