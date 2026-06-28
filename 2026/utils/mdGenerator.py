# 由json数据生成md文件。该代码由claude生成。
# 使用方法：python mdGenerator.py source_json_file dest_md_file
# 例如：python mdGenerator.py /mnt/c/_temp/2026_高考_四川/08.json.manual/physics/2026.sichuan.physics.json /mnt/c/_temp/2026_高考_四川/09.md/physics/2026.sichuan.physics.md

import sys, json, re

# Now I understand:
# "38" at line 654 = COUNT for major 21英语 (which spans 652-653)
# "29" at line 657 = COUNT for major 31历史学 (line 656)
# These are pure-digit 2-char "codes" that are COUNTS, not major codes
# They appear AFTER a major line (where count is expected)

# The issue with is_major_code_only: "29", "38" are valid COUNTS
# But when used as MAJOR_CODE they cause problems

# Fix strategy:
# In the token pipeline, "29" and similar pure-digit 2-char strings:
# - If they're is_count() -> mark as COUNT
# - Only mark as MAJOR_CODE if they contain at least one letter

# BUT: major codes CAN be pure digits like "01", "04", "29", "91"!
# The difference: "29" after a MAJOR (expecting count) = COUNT
# "29" after a FEE or at start of entry = MAJOR_CODE

# Better fix: Don't handle MAJOR_CODE separately. Instead:
# In the merge phase, when we see an OTHER that is 2 chars [0-9A-Za-z],
# and the NEXT token is an OTHER with Chinese text,
# merge them as a MAJOR

# Let me take a different approach:
# Pre-merge step: for any 2-char alphanum alone, if followed by Chinese OTHER, merge

if len(sys.argv) < 3:
    print("请提供至少两个参数")
    print("用法: python mdGenerator.py source_json_file dest_md_file")
    sys.exit(1)

source_json_file = sys.argv[1]
dest_md_file = sys.argv[2]

with open(source_json_file) as f:
    data = json.load(f)
texts = data.get('rec_texts', [])

def is_school_line(s):
    return bool(re.match(r'^\d{4}\s?[\u4e00-\u9fff]', s))

def is_group_line(s):
    return bool(re.match(r'^专业组\d{3}', s))

def is_major_line(s):
    return bool(re.match(r'^[0-9A-Za-z]{2}\s?[\u4e00-\u9fff（\[\(]', s))

def is_remark_school(s):
    return s.startswith('院校备注')

def is_remark_group(s):
    return s.startswith('专业组备注')

def is_fee(s):
    return bool(re.match(r'^\d{4,6}$', s)) or s in ['免费', '待定']

def is_count(s):
    return bool(re.match(r'^\d{1,3}$', s)) and int(s) < 500

def is_section_header(s):
    return bool(
        re.match(r'^[一二三四五六七八九十][、，,．.]', s) or
        re.match(r'^\([一二三四五六七八九十]\)', s) or
        re.match(r'^\d+[．.](?!\d)', s) or
        re.match(r'^\(\d+\)', s)
    )

def is_noise(s):
    if not s:
        return True
    if re.match(r'^[−Δ∞☆・≥≤×]+$', s):
        return True
    if '院校代号' in s:
        return True
    if re.match(r'^(?:计划|收费|计划收费)$', s):
        return True
    if re.match(r'^特别提醒', s):
        return True
    return False

def extract_trailing_count_fee(text):
    m = re.search(r'([）\)\]]|[\u4e00-\u9fff])\s*(\d+)$', text)
    if not m:
        return text, None, None
    digits = m.group(2)
    base = text[:m.start(1)+1].strip()
    if len(digits) <= 3:
        if int(digits) < 500:
            return base, digits, None
        return text, None, None
    if len(digits) == 4:
        if int(digits) >= 1000:
            return base, None, digits
        return text, None, None
    if len(digits) == 5:
        if int(digits) >= 10000:
            return base, None, digits
        count_part, fee_part = digits[0], digits[1:]
        if int(count_part) > 0 and int(fee_part) >= 1000:
            return base, count_part, fee_part
        return base, None, digits
    if len(digits) == 6:
        if int(digits[:1]) > 0 and int(digits[1:]) >= 10000:
            return base, digits[:1], digits[1:]
        if int(digits[:2]) < 500 and int(digits[2:]) >= 1000:
            return base, digits[:2], digits[2:]
    return text, None, None

# Pre-process: join split major entries in the raw text list
# Strategy: go through texts, and when we see a line that is 2-char alphanum
# followed by Chinese text (not a major/school/group line), merge them
processed = []
i = 0
while i < len(texts):
    s = texts[i].strip()
    i += 1
    if not s:
        continue
    
    # Check if this is a 2-char code alone
    if re.match(r'^[0-9A-Za-z]{2}$', s) and not is_fee(s) and not is_count(s):
        # Peek ahead: is next non-empty line Chinese text (not a structured line)?
        j = i
        while j < len(texts) and not texts[j].strip():
            j += 1
        if j < len(texts):
            nxt = texts[j].strip()
            if (nxt and re.search(r'^[\u4e00-\u9fff（\[\(]', nxt) and
                not is_school_line(nxt) and not is_group_line(nxt) and
                not is_major_line(nxt) and not is_remark_school(nxt)):
                # Merge: s + nxt = full major line
                processed.append(s + nxt)
                i = j + 1
                continue
    
    processed.append(s)

print(f"After pre-processing: {len(processed)} lines (was {len(texts)})")

# Now build tokens from processed
tokens = []
for s in processed:
    if is_noise(s):
        continue
    if is_section_header(s):
        tokens.append(('SECTION', s))
    elif is_school_line(s):
        tokens.append(('SCHOOL', s))
    elif is_group_line(s):
        tokens.append(('GROUP', s))
    elif is_major_line(s):
        tokens.append(('MAJOR', s))
    elif is_remark_school(s):
        tokens.append(('REM_SCHOOL', s))
    elif is_remark_group(s):
        tokens.append(('REM_GROUP', s))
    elif is_fee(s):
        tokens.append(('FEE', s))
    elif is_count(s):
        tokens.append(('COUNT', s))
    else:
        tokens.append(('OTHER', s))

# Merge continuation
merged = []
for tok_type, tok_text in tokens:
    if not merged:
        merged.append([tok_type, tok_text])
        continue
    prev_type = merged[-1][0]
    if tok_type == 'OTHER':
        if re.match(r'^\d{4}\s[\u4e00-\u9fff]', tok_text):
            merged.append(['SCHOOL', tok_text])
        elif prev_type in ('MAJOR', 'REM_SCHOOL', 'REM_GROUP'):
            merged[-1][1] += tok_text
        elif prev_type == 'SCHOOL' and not re.search(r'[）\)]\s*$', merged[-1][1]):
            merged[-1][1] += tok_text
        elif len(tok_text) > 8:
            merged.append([tok_type, tok_text])
    else:
        merged.append([tok_type, tok_text])

from collections import Counter
print(Counter(t for t,_ in merged))

def parse_major_text(text):
    m = re.match(r'^([0-9A-Za-z]{2})\s?(.*)', text, re.DOTALL)
    if not m:
        return '??', text, '', ''
    code = m.group(1)
    rest = m.group(2).strip()
    clean, cnt, fee = extract_trailing_count_fee(rest)
    return code, clean, cnt or '', fee or ''

def parse_school_text(text):
    m = re.match(r'^(\d{4})\s?(.*)', text)
    if m:
        return m.group(1), m.group(2).strip()
    return '????', text

# Generate MD
output_lines = []
current_major_data = None
expect_group_count = False
expect_major_count = False
expect_major_fee = False

def flush_major(output_lines, md):
    if md is None:
        return
    code = md['code']
    name = md['name']
    cnt = md.get('count', '')
    fee = md.get('fee', '')
    line = f"{code}    {name}"
    if cnt: line += f"    {cnt}"
    if fee: line += f"    {fee}"
    output_lines.append(f"\n{line}\n")

for tok_type, tok_text in merged:
    if tok_type == 'SECTION':
        flush_major(output_lines, current_major_data)
        current_major_data = None
        text = tok_text.strip()
        if re.match(r'^[一二三][、，,．.]', text):
            output_lines.append(f"\n# {text}\n")
        elif re.match(r'^\([一二三四五六七八九十]\)', text):
            output_lines.append(f"\n## {text}\n")
        elif re.match(r'^\d+[．.]', text):
            output_lines.append(f"\n### {text}\n")
        elif re.match(r'^\(\d+\)', text):
            output_lines.append(f"\n#### {text}\n")
        expect_group_count = False
        expect_major_count = False
        expect_major_fee = False
    elif tok_type == 'SCHOOL':
        flush_major(output_lines, current_major_data)
        current_major_data = None
        expect_major_count = False
        expect_major_fee = False
        code, name = parse_school_text(tok_text)
        output_lines.append(f"\n**{code} {name}**\n")
    elif tok_type == 'GROUP':
        flush_major(output_lines, current_major_data)
        current_major_data = None
        expect_major_count = False
        expect_major_fee = False
        output_lines.append(f"\n**{tok_text}**")
        expect_group_count = True
    elif tok_type == 'COUNT':
        if expect_group_count:
            output_lines.append(f"    {tok_text}\n")
            expect_group_count = False
        elif expect_major_count and current_major_data:
            current_major_data['count'] = tok_text
            expect_major_count = False
            expect_major_fee = True
    elif tok_type == 'FEE':
        if expect_group_count:
            output_lines.append(f"\n")
            expect_group_count = False
        if current_major_data and not current_major_data.get('fee'):
            current_major_data['fee'] = tok_text
            flush_major(output_lines, current_major_data)
            current_major_data = None
            expect_major_fee = False
            expect_major_count = False
    elif tok_type == 'MAJOR':
        flush_major(output_lines, current_major_data)
        if expect_group_count:
            output_lines.append(f"\n")
            expect_group_count = False
        code, name, cnt, fee = parse_major_text(tok_text)
        current_major_data = {'code': code, 'name': name, 'count': cnt, 'fee': fee}
        if cnt and fee:
            flush_major(output_lines, current_major_data)
            current_major_data = None
            expect_major_count = False
            expect_major_fee = False
        elif cnt:
            expect_major_count = False
            expect_major_fee = True
        else:
            expect_major_count = True
            expect_major_fee = False
    elif tok_type in ('REM_SCHOOL', 'REM_GROUP'):
        flush_major(output_lines, current_major_data)
        current_major_data = None
        expect_group_count = False
        expect_major_count = False
        expect_major_fee = False
        label = '院校备注：' if tok_type == 'REM_SCHOOL' else '专业组备注：'
        body = tok_text[4:].lstrip('：:').strip() if tok_type == 'REM_SCHOOL' else tok_text[5:].lstrip('：:').strip()
        output_lines.append(f"\n**{label}** {body}\n")

flush_major(output_lines, current_major_data)

output = ''.join(output_lines)

# Fix missing first school
old = "### 1．国家专项计划\n\n**专业组101（再选科目：思想政治）**"
new = "### 1．国家专项计划\n\n**(待确定) (待确定)**\n\n**专业组101（再选科目：思想政治）**"
output = output.replace(old, new, 1)

with open(dest_md_file, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"\nOutput: {len(output)} chars, {output.count(chr(10))} lines")

# Verify 西南大学
idx = output.find('**0056 西南大学(重庆市)**')
print("\n=== 西南大学 ===")
print(output[idx:idx+600])

# Verify 北京大学
idx2 = output.find('**0001 北京大学(北京市）**')
print("\n=== 北京大学 (普通类) ===")
print(output[idx2:idx2+500])