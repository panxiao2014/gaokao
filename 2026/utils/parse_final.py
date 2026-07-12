import re
import sys

MD_FILE = '/mnt/user-data/uploads/2026_四川_物理类.md'

def fix_specialty_code(code):
    if code and code[0] == 'O':
        return '0' + code[1:]
    return code

def parse_location(loc_str):
    if not loc_str:
        return '', ''
    s = loc_str.strip()
    for direct in ['北京市', '上海市', '天津市', '重庆市']:
        if s == direct or s.startswith(direct):
            return direct, direct
    m = re.match(r'(.+?(?:省|自治区|特别行政区))(.+)?', s)
    if m:
        return m.group(1), (m.group(2) or '').strip()
    return s, ''

def parse_school_header(line):
    # Matches last (...) or （...） as location
    m = re.match(
        r'\*\*(\d{4})\s+(.+?)(?:（|【|\()([^（）()\[\]【】]+?)(?:）|】|\))\*\*\s*$',
        line.strip()
    )
    if m:
        code = m.group(1)
        name = m.group(2).strip().rstrip(' ')
        loc = m.group(3).strip()
        province, city = parse_location(loc)
        return code, name, province, city
    return None

def parse_group_header(line):
    m = re.match(
        r'\*\*专业组\s*(\d{3})\s*(?:[（(]再选科目[：:]([^）)]+)[）)])?\*\*\s*(\d+)?\s*$',
        line.strip()
    )
    if m:
        return m.group(1), (m.group(2) or '').strip(), m.group(3) or ''
    return None

def parse_specialty_line(line):
    m = re.match(r'^([A-Z0-9]{2})\s{2,}(.+)$', line.strip())
    if not m:
        return None
    raw_code = m.group(1)
    rest = m.group(2).strip()
    code = fix_specialty_code(raw_code)
    
    spec_note = ''
    
    # Try bracket [专业备注:...]
    bm = re.search(r'[【\[]专业备注[：:](.+?)[】\]]', rest, re.DOTALL)
    if bm:
        spec_note = bm.group(1).strip()
        rest = (rest[:bm.start()] + rest[bm.end():]).strip()
    else:
        # Try (专业备注:...) with balanced parens
        pm = re.search(r'[（(]专业备注[：:]', rest)
        if pm:
            start = pm.start()
            depth = 0
            end_idx = -1
            for j in range(start, len(rest)):
                if rest[j] in '（(':
                    depth += 1
                elif rest[j] in '）)':
                    depth -= 1
                    if depth == 0:
                        end_idx = j
                        break
            if end_idx >= 0:
                spec_note = rest[pm.end():end_idx].strip()
                rest = (rest[:start] + rest[end_idx+1:]).strip()
    
    plan = ''
    fee = ''
    name = rest
    
    # Parse trailing PLAN and FEE
    m2 = re.search(r'\s+(\d+)\s+(免费|待定|\d{3,6})\s*$', name)
    if m2:
        plan = m2.group(1)
        fee = m2.group(2)
        name = name[:m2.start()].strip()
    else:
        m3 = re.search(r'\s+(\d+)?\s*(免费|待定)\s*$', name)
        if m3:
            plan = m3.group(1) or ''
            fee = m3.group(2)
            name = name[:m3.start()].strip()
        else:
            m4 = re.search(r'\s+(\d+)\s*$', name)
            if m4:
                val = m4.group(1)
                if int(val) > 200:
                    fee = val
                else:
                    plan = val
                name = name[:m4.start()].strip()
    
    return code, name.strip(), spec_note.strip(), plan.strip(), fee.strip()


REAL_H3_RE = re.compile(
    r'^### \d+[．.]'
)

def is_real_h3(line):
    # A heading is "real" if it starts with "### N." or "### N．"
    # and represents a section (not corrupted content)
    # Key heuristic: real headings are SHORT or match known patterns
    if not REAL_H3_RE.match(line):
        return False
    # If the heading contains certain keywords that appear in specialty names or notes, it's corrupted
    text_after = re.sub(r'^### \d+[．.]\s*', '', line)
    # Known real section names
    real_sections = [
        '国家专项计划', '高校专项计划', 'A段', 'B段', '定向培养军士', '公安', '司法',
        '航海类', '普通类高职', '高水平运动队', '少数民族', '省属高校', '加授',
        '原"少数民族', '省属', '非本地',
    ]
    for rs in real_sections:
        if text_after.startswith(rs):
            return True
    # If text_after is very long, it's corrupted
    if len(text_after) > 30:
        return False
    return True

def load_and_preprocess(filepath):
    with open(filepath, encoding='utf-8') as f:
        raw_lines = f.read().split('\n')
    
    lines = []
    for raw in raw_lines:
        stripped = raw.strip()
        if stripped.startswith('### ') and not is_real_h3(stripped):
            if lines:
                lines[-1] = lines[-1] + stripped[4:]
        else:
            lines.append(stripped)
    
    return lines


def parse_all(lines):
    records = []
    
    batch = ''
    category = ''
    subcategory = ''
    school_code = ''
    school_name = ''
    school_note = ''
    province = ''
    city = ''
    group_no = ''
    group_note = ''
    reselect = ''
    group_total = ''
    current_specs = []
    
    def flush():
        for spec in current_specs:
            records.append({
                'batch': batch,
                'category': category,
                'subcategory': subcategory,
                'school_code': school_code,
                'school_name': school_name,
                'school_note': school_note,
                'province': province,
                'city': city,
                'group_no': group_no,
                'group_note': group_note,
                'reselect': reselect,
                'group_total': group_total,
                'spec_code': spec['code'],
                'spec_name': spec['name'],
                'spec_plan': spec['plan'],
                'spec_fee': spec['fee'],
                'spec_note': spec['note'],
            })
        current_specs.clear()
    
    for line in lines:
        if not line:
            continue
        
        if line.startswith('## '):
            flush()
            batch = line[3:].strip()
            category = subcategory = ''
            school_code = school_name = school_note = province = city = ''
            group_no = group_note = reselect = group_total = ''
            continue
        
        if line.startswith('### '):
            flush()
            category = line[4:].strip()
            subcategory = ''
            school_code = school_name = school_note = province = city = ''
            group_no = group_note = reselect = group_total = ''
            continue
        
        if line.startswith('#### '):
            flush()
            subcategory = line[5:].strip()
            school_code = school_name = school_note = province = city = ''
            group_no = group_note = reselect = group_total = ''
            continue
        
        if line.startswith('**'):
            # Check for 院校备注
            am = re.match(r'\*\*院校备注[：:]\*?\*?\s*(.*)', line)
            if am:
                flush()
                note = am.group(1).rstrip('*').strip()
                school_note = note
                continue
            
            # Check for 专业组备注
            gm = re.match(r'\*\*专业组备注[：:]\*?\*?\s*(.*)', line)
            if gm:
                note = gm.group(1).rstrip('*').strip()
                group_note = note
                continue
            
            # School header
            sh = parse_school_header(line)
            if sh:
                flush()
                school_code, school_name, province, city = sh
                school_note = ''
                group_no = reselect = group_total = group_note = ''
                continue
            
            # Group header
            gh = parse_group_header(line)
            if gh:
                flush()
                group_no, reselect, group_total = gh
                group_note = ''
                continue
            
            continue
        
        # Specialty line
        spec = parse_specialty_line(line)
        if spec:
            code, name, note, plan, fee = spec
            current_specs.append({'code': code, 'name': name, 'note': note, 'plan': plan, 'fee': fee})
    
    flush()
    return records


def main():
    print("Loading...", file=sys.stderr)
    lines = load_and_preprocess(MD_FILE)
    print("Parsing...", file=sys.stderr)
    records = parse_all(lines)
    print(f"Total: {len(records)}", file=sys.stderr)
    from collections import Counter
    for b, c in Counter(r['batch'] for r in records).items():
        print(f"  {b}: {c}", file=sys.stderr)
    return records

if __name__ == '__main__':
    import json
    records = main()
    # Show sample
    for r in records[:2]:
        print(json.dumps(r, ensure_ascii=False, indent=2))