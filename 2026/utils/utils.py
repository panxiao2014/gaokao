import cv2
import numpy as np
import re
import os
import json
import requests
import sys
import time

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
# 处理单张图片的页眉和页脚
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

    # 强制以PNG格式保存，确保无损，为后续去水印等步骤提供精确像素值
    out_path_png = os.path.splitext(output_path)[0] + ".png"

    success, encoded_img = cv2.imencode(".png", cropped)

    if not success:
        raise Exception("保存失败")

    encoded_img.tofile(out_path_png)

    print(f"保存: {out_path_png}")


# =========================================================
# 处理页眉页脚目录
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


# =========================================================
# 计算一列中最长的连续黑色像素段长度
# =========================================================
def max_consecutive_black_col(col):
    """计算一列中最长的连续黑色像素段长度"""
    max_len, cur = 0, 0
    for px in col:
        if px == 0:
            cur += 1
            max_len = max(max_len, cur)
        else:
            cur = 0
    return max_len


# =========================================================
# 查找分栏竖线
# =========================================================
def find_column_dividers(binary_img):
    """
    自左向右扫描全图，找到所有竖向分栏线。

    判断标准：该列最长连续黑色像素段超过图片高度的 90%。
    将相邻列（间距 <= 3px）合并为一组，返回每组右边界 x 坐标列表。
    """

    h, w = binary_img.shape
    threshold = h * 0.9

    candidates = []

    for x in range(w):
        if max_consecutive_black_col(binary_img[:, x]) > threshold:
            candidates.append(x)

    if not candidates:
        return []

    # 将相邻列合并成竖线组
    groups = []
    group = [candidates[0]]

    for x in candidates[1:]:
        if x - group[-1] <= 3:
            group.append(x)
        else:
            groups.append(group)
            group = [x]

    groups.append(group)

    # 每组取右边界 x 坐标
    return [g[-1] for g in groups]


# =========================================================
# 对单张图片进行分栏并保存
# =========================================================
def split_columns_crop(input_path, output_dir):

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
    # 灰度化 + 自适应二值化
    # =====================================================

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        25,
        15
    )

    # =====================================================
    # 查找分栏竖线
    # =====================================================

    dividers = find_column_dividers(binary)

    if len(dividers) != 2:
        raise Exception(f"预期找到2条分栏线，实际找到{len(dividers)}条")

    x1, x2 = dividers

    # =====================================================
    # 按竖线位置切出三栏
    # 竖线本身（宽约2px）不纳入任何一栏
    # =====================================================

    regions = [
        (0,      x1 - 1),   # 第一栏：竖线1左侧
        (x1 + 1, x2 - 1),   # 第二栏：两竖线之间
        (x2 + 1, w - 1),    # 第三栏：竖线2右侧
    ]

    stem = os.path.splitext(os.path.basename(input_path))[0]

    for i, (left, right) in enumerate(regions, start=1):

        col_img = img[:, left:right + 1]

        # 强制以PNG格式保存，确保无损
        out_path = os.path.join(output_dir, f"{stem}_{i:02d}.png")

        success, encoded = cv2.imencode(".png", col_img)

        if not success:
            raise Exception(f"保存第{i}栏失败")

        encoded.tofile(out_path)

        print(f"  保存: {out_path}")


# =========================================================
# 对目录内所有图片进行分栏处理
# =========================================================
def split_columns_directory(
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

    for filename in sorted(os.listdir(input_dir)):

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

        stem = os.path.splitext(filename)[0]
        ext  = os.path.splitext(filename)[1]

        # =================================================
        # 三个分栏输出文件都已存在则跳过
        # =================================================

        all_exist = all(
            os.path.exists(os.path.join(output_dir, f"{stem}_{i:02d}{ext}"))
            for i in range(1, 4)
        )

        if all_exist:
            print(f"跳过已存在文件: {filename}")
            continue

        # =================================================
        # 开始处理
        # =================================================

        try:

            split_columns_crop(input_path, output_dir)

        except Exception as e:

            print(f"处理失败: {filename} -> {e}")

            failed_files.append(filename)





#调用paddleocr API接口进行ocr识别，并保存结果
JOB_URL = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
MODEL = "PP-OCRv5"
with open("token/paddle.txt", "r") as f:
    TOKEN = f.read().strip()

headers = {
    "Authorization": f"bearer {TOKEN}",
}

optional_payload = {
    "markdownIgnoreLabels": [],
    "useDocOrientationClassify": False,
    "useDocUnwarping": False,
    "useTextlineOrientation": False,
    "textDetLimitType": "min",
    "textDetLimitSideLen": 64,
    "textDetThresh": 0.3,
    "textDetBoxThresh": 0.52,
    "textDetUnclipRatio": 1.5,
    "textRecScoreThresh": 0,
    "parseLanguage": "default"
}

post_data = {
    "model": MODEL,
    "optionalPayload": json.dumps(optional_payload)
}

def ocr_process(
    input_dir,
    output_dir,
    failed_files
):

    for filename in sorted(os.listdir(input_dir)):

        input_path = os.path.join(input_dir, filename)

        #提取filename中的文件名部分，并生成同名的json文件名：
        stem = os.path.splitext(filename)[0]
        json_filename = stem + ".json"
        output_path = os.path.join(output_dir, json_filename)

        print(f"处理: {input_path}")

        # =================================================
        # 已存在则跳过
        # =================================================
        if os.path.exists(output_path):

            print(f"跳过已存在文件: {output_path}")

            continue

        # =================================================
        # 开始处理
        # =================================================
        with open(input_path, "rb") as f:
            files = {"file": f}
            job_response = requests.post(JOB_URL, headers=headers, data=post_data, files=files)

        if job_response.status_code != 200:
            print(f"提交失败: {filename} -> {job_response.text}")
            failed_files.append(filename)
            continue

        assert job_response.status_code == 200
        jobId = job_response.json()["data"]["jobId"]

        jsonl_url = ""
        while True:
            job_result_response = requests.get(f"{JOB_URL}/{jobId}", headers=headers)
            if job_result_response.status_code != 200:
                print(f"查询结果失败: {filename} -> {job_result_response.text}")
                failed_files.append(filename)
                break

            state = job_result_response.json()["data"]["state"]
            if state == 'pending':
                print("The current status of the job is pending")
            elif state == 'running':
                try:
                    total_pages = job_result_response.json()['data']['extractProgress']['totalPages']
                    extracted_pages = job_result_response.json()['data']['extractProgress']['extractedPages']
                except KeyError:
                    print("The current status of the job is running...")
            elif state == 'done':
                jsonl_url = job_result_response.json()['data']['resultUrl']['jsonUrl']
                break
            elif state == "failed":
                error_msg = job_result_response.json()['data']['errorMsg']
                print(f"Job failed, failure reason：{error_msg}")
                failed_files.append(filename)
                break

            time.sleep(5)

        if jsonl_url:
            jsonl_response = requests.get(jsonl_url)
            if jsonl_response.status_code != 200:
                print(f"下载结果失败: {filename} -> {jsonl_response.text}")
                failed_files.append(filename)
                continue

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(jsonl_response.text)

            print(f"保存: {output_path}")



def single_json_process(
    input_path,
    output_path,
    markdown_filename
):
    #如果markdown_filename已经存在于output_path中，则跳过
    if os.path.exists(os.path.join(output_path, markdown_filename)):
        print(f"跳过已存在文件: {markdown_filename}")
        return
    
    #读取所有json文件中的"rec_texts"部分。该字段值为一个数组，每个元素是识别到的文本行。将所有文件中的文本行合并成一个数组，保存在markdown_filename的"rec_texts"字段中。最终生成一个新的json文件，包含一个字段"rec_texts"，其值为合并后的文本行数组。
    all_rec_texts = []
    for filename in sorted(os.listdir(input_path)):

        if not filename.endswith(".json"):
            continue

        input_path_full = os.path.join(input_path, filename)

        with open(input_path_full, "r", encoding="utf-8") as f:
            jsonl_data = f.read()

        # 解析jsonl数据并提取rec_texts
        try:
            data = json.loads(jsonl_data)

            #找到json数据中的"rec_texts"字段，并将其值（一个数组）添加到all_rec_texts中
            ocr_results = data.get('result', {}).get('ocrResults', [])
            if ocr_results:
                pruned_result = ocr_results[0].get('prunedResult', {})
                rec_texts = pruned_result.get('rec_texts')
                if rec_texts is not None:
                    all_rec_texts.extend(rec_texts)
                else:
                    print(f"文件 {filename} 中找不到 rec_texts 字段")
            else:
                print(f"文件 {filename} 中没有 ocrResults")
        except json.JSONDecodeError:
            print(f"无法解析文件: {filename}")

    # 保存合并后的文本行到markdown_filename
    output_markdown_path = os.path.join(output_path, markdown_filename)
    with open(output_markdown_path, "w", encoding="utf-8") as f:
        json.dump({"rec_texts": all_rec_texts}, f, ensure_ascii=False, indent=4)

    print(f"保存: {output_markdown_path}")



def json_data_cleaning(
    input_path,
    output_path
):
    #找到input_path目录下的json文件并读取，该目录下应该只有一个json文件：
    json_files = [f for f in os.listdir(input_path) if f.endswith(".json")]

    if not json_files:
        print(f"在 {input_path} 中未找到 JSON 文件")
        return

    if len(json_files) > 1:
        print(f"在 {input_path} 中发现多个 JSON 文件，将处理第一个: {json_files[0]}")
    
    json_file = json_files[0]
    input_json_path = os.path.join(input_path, json_file)

    # 读取并清洗 JSON 数据
    with open(input_json_path, "r", encoding="utf-8") as f:
        original_data = json.load(f)

    # 定义替换规则的二元组列表
    replacement_rules = [
        ("商校", "高校"),
        ("尘", "生"),
        ("达致", "达到"),
        ("师范尘", "师范生"),
        ("男尘", "男生"),
        ("备油", "备注"),
        ("色自", "色盲"),
        ("色白", "色盲"),
        ("色宜", "色盲"),
        ("色宣", "色盲"),
        ("售自", "色盲"),
        ("色直色", "色盲色弱"),
        ("色（自色调", "色盲色弱"),
        ("您色强", "色弱"),
        ("色强", "色弱"),
        ("色烟", "色弱"),
        ("色窗", "色盲"),
        ("色盲色调", "色盲色弱"),
        ("色色盲", "色盲"),
        ("（州校区）", "（广州校区）"),
        ("动没", "动漫"),
        ("低丁", "低于"),
        ("高丁", "高于"),
        ("裸跟", "裸眼"),
        ("明品", "明显"),
        ("日矫正", "且矫正"),
        ("基江校区", "綦江校区"),
        ("古商县", "古蔺县"),
        ("德阳市什市", "德阳市什邡市"),
        ("喀仕", "喀什"),
        ("白治区", "自治区"),
        ("□", "口"),
        ("白动化", "自动化"),
        ("白动", "自动"),
        ("白主", "自主"),
        ("白治", "自治"),
        ("白贡市", "自贡市"),
        ("白资市", "自贡市"),
        ("葫产岛", "葫芦岛"),
        ("卢州市", "泸州市"),
        ("荣具", "荣县"),
        ("中新棱区", "阜新校区"),
        ("马尾棱区", "马尾校区"),
        ("4LV]中医学", "4L[V]中医学"),
        ("基丁", "基于"),
        ("出外合作", "中外合作"),
        ("中外命作", "中外合作"),
        ("外命作", "中外合作"),
        ("股体健全", "肢体健全"),
        ("弱弱", "弱"),
        ("交义班", "交叉班"),
        ("智赞", "智慧"),
        ("玉程", "工程"),
        ("及基白", "及其自动化"),
        ("及基", "及其"),
        ("专项计划（甘孜州>", "专项计划<甘孜州>"),
        ("专项计划甘孜州>", "专项计划<甘孜州>"),
        ("专项计划甘孜州)", "专项计划<甘孜州>"),
        ("专计划甘州>", "专项计划<甘孜州>"),
        ("专计冰甘孜州>", "专项计划<甘孜州>"),
        ("专项计划阿坝州>", "专项计划<阿坝州>"),
        ("专项计划（阿坝州>", "专项计划<阿坝州>"),
        ("安市武胜", "广安市武胜"),
        ("遂校区", "遂宁校区"),
        ("宜宾市琪县", "宜宾市珙县"),
        ("股体", "肢体"),
        ("不子录取", "不予录取"),
        ("专业备注不子录取", "专业备注：色盲不予录取"),
        ("专业备注食不子录取", "专业备注：色盲不予录取"),
        ("专业备注不子录取", "专业备注：色弱不予录取"),
        ("十学位", "士学位"),
        ("白愿", "自愿"),
        ("白然", "自然"),
        ("白强", "自强"),
        ("白由", "自由"),
        ("白行", "自行"),
        ("机器人工程、白", "机器人工程、自"),
        ("电气工程及其白", "电气工程及其自"),
        ("机械电子工程、白", "机械电子工程、自"),
        ("机器人工程、白", "机器人工程、自"),
        ("集成电路学院白", "集成电路学院自"),
        ("机械设计制造及其白", "机械设计制造及其自"),
        ("数字经济、白", "数字经济、自"),
        ("包含专业：白", "包含专业：自"),
        ("西班牙语、白", "西班牙语、日"),
        ("白去", "白云"),
        ("火学", "大学"),
        ("火一", "大一"),
        ("火二", "大二"),
        ("火三", "大三"),
        ("火四", "大四"),
        ("大丁", "大于")
    ]

    # 定义需要删除的元素列表（精确匹配）
    elements_to_remove = [
        "招生考试报",
        "生考试报",
        "性考试报",
        "考试报",
        "考试据",
        "试报",
        "生考试据",
        "试据",
        "式据",
        "治生考试报",
        "铭生考试报",
        "星考试报",
        "主考试报",
        "名生考试报",
        "超生考试报",
        "本考试报",
        "招步考试报",
        "姓考试报",
        "理考试报",
        "福",
        "拍",
        "瓶",
    ]

    # 深拷贝原始数据，避免修改原数据
    cleaned_data = json.loads(json.dumps(original_data)) if isinstance(original_data, dict) else original_data

    # 遍历并清理 rec_texts 数组
    if "rec_texts" in cleaned_data:
        cleaned_texts = []
        for text in cleaned_data["rec_texts"]:
            # 检查是否需要删除该元素（精确匹配）
            if text in elements_to_remove:
                continue  # 跳过该元素，不加入新数组
            
            # 对需要保留的文本进行替换操作
            if isinstance(text, str):
                for old_word, new_word in replacement_rules:
                    text = text.replace(old_word, new_word)
                cleaned_texts.append(text)
            else:
                cleaned_texts.append(text)
        
        cleaned_data["rec_texts"] = cleaned_texts
    
    # 保存清洗后的 JSON 数据
    output_json_path = os.path.join(output_path, json_file)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=4)
        print(f"保存: {output_json_path}")