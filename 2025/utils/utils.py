import cv2
import numpy as np
import re
import os

def max_consecutive_black(row):
    """计算一行中最长的连续黑色像素段长度"""
    max_len, cur = 0, 0
    for px in row:
        if px == 0:
            cur += 1
            max_len = max(max_len, cur)
        else:
            cur = 0
    return max_len


# =========================================================
# 查找页眉线
# =========================================================
def find_header_line(binary_img):
    """
    在图片顶部 1/4 区域内寻找页眉线。

    判断标准：该行最长连续黑色像素段超过图片宽度的 1/2。

    如果检测到多组满足条件的线段，取最后一组的最后一行
    （页眉通常由上下两条紧邻的线组成，取最下方那条作为裁切起点）。
    """
    h, w = binary_img.shape
    search_height = h // 4

    # 收集所有满足条件的行
    candidate_rows = []
    for y in range(search_height):
        if max_consecutive_black(binary_img[y]) > w * 0.5:
            candidate_rows.append(y)

    if not candidate_rows:
        return None

    # 将相邻行（间距 <= 3px）合并成线段组
    groups = []
    group = [candidate_rows[0]]
    for y in candidate_rows[1:]:
        if y - group[-1] <= 3:
            group.append(y)
        else:
            groups.append(group)
            group = [y]
    groups.append(group)

    # 取最后一组的最后一行
    return groups[-1][-1]

# =========================================================
# 查找页脚线
# =========================================================
def find_footer_line(binary_img):
    """
    在底部 1/16 区域自下而上寻找页脚线。

    规则：
    横线长度超过图片宽度 3/4
    """

    h, w = binary_img.shape

    search_top = h - (h // 16)

    candidate_lines = []

    for y in range(h - 1, search_top, -1):

        row = binary_img[y]

        black_pixels = np.sum(row == 0)

        # 页脚线要求更长
        if black_pixels > w * 0.75:
            candidate_lines.append(y)

    # 没找到页脚线
    if not candidate_lines:
        return None

    # 合并相邻行
    merged = []

    start = candidate_lines[0]
    prev = candidate_lines[0]

    for y in candidate_lines[1:]:

        if abs(y - prev) <= 3:
            prev = y

        else:
            merged.append((start + prev) // 2)

            start = y
            prev = y

    merged.append((start + prev) // 2)

    # 自下而上第一条
    return merged[0]


# =========================================================
# 处理单张图片
# =========================================================

def process_header_footer_crop(input_path, output_path):

    print(f"处理: {input_path}")

    # =====================================================
    # 读取图片（支持中文路径）
    # =====================================================

    img = cv2.imdecode(
        np.fromfile(input_path, dtype=np.uint8),
        cv2.IMREAD_COLOR
    )

    if img is None:
        raise Exception("无法读取图片")

    h, w = img.shape[:2]

    # =====================================================
    # 灰度化
    # =====================================================

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # =====================================================
    # 自适应二值化
    # =====================================================

    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        25,
        15
    )

    # =====================================================
    # 查找页眉线
    # =====================================================

    header_line = find_header_line(binary)

    if header_line is None:
        raise Exception("未找到页眉线")

    # 从页眉线下方开始裁切
    crop_top = header_line + 5

    # =====================================================
    # 查找页脚线
    # =====================================================

    footer_line = find_footer_line(binary)

    # 默认保留到底部
    crop_bottom = h

    # 找到页脚线
    if footer_line is not None:

        # 从页脚线上方结束
        crop_bottom = footer_line - 5

    # =====================================================
    # 安全检查
    # =====================================================

    if crop_bottom <= crop_top:
        raise Exception("裁切区域异常")

    crop_height = crop_bottom - crop_top

    if crop_height < h * 0.3:
        raise Exception("裁切区域过小")

    # =====================================================
    # 裁切
    # =====================================================

    cropped = img[crop_top:crop_bottom, :]

    # =====================================================
    # 保存（支持中文路径）
    # =====================================================

    ext = os.path.splitext(output_path)[1]

    success, encoded_img = cv2.imencode(ext, cropped)

    if not success:
        raise Exception("保存失败")

    encoded_img.tofile(output_path)

    print(f"保存: {output_path}")


# =========================================================
# 处理目录
# =========================================================

def process_header_footer_directory(
    input_dir,
    output_dir,
    prefix,
    start_num,
    end_num,
    failed_files
):

    pattern = re.compile(
        rf"{prefix}_(\d+)\.png"
    )

    for filename in os.listdir(input_dir):

        match = pattern.match(filename)

        if not match:
            continue

        num = int(match.group(1))

        # =================================================
        # 只处理指定范围
        # =================================================

        if num < start_num or num > end_num:
            continue

        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        # =================================================
        # 已存在则跳过
        # =================================================

        if os.path.exists(output_path):

            print(f"跳过已存在文件: {output_path}")

            continue

        # =================================================
        # 开始处理
        # =================================================

        try:

            process_header_footer_crop(
                input_path,
                output_path
            )

        except Exception as e:

            print(f"处理失败: {filename} -> {e}")

            failed_files.append(filename)