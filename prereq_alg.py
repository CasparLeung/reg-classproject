import re
import os
import pandas as pd
import logging

#when the text is (ECS 032B or ECS 036C);(MAT 135A and STA 035C) or (MAT 136A and STA 036C)
#the output:
#group,condition,course,related_group,prereq
#1,or,ECS 032B,N/A,STS 101
#1,or,ECS 036C,N/A,STS 101
#2,or,MAT 135A,N/A,STS 101
#3,or,MAT 136A,2,STS 101
# need to make a group_condition
#what if the text is (ECS 032B or ECS 036C);((MAT 135A and STA 035C) or (MAT 136A and STA 036C)) or xxx
#what if the text is (ECS 032B or ECS 036C);(MAT 135A and (xxx or xxx)) or (MAT 136A and (xxx or xxx))

#test ENG 180 f, EME 115 , ARE 100A? s
# Configure logging with force=True to avoid conflicts
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)


def break_down_prereq_text(text):
    segments = split_top_level_semicolons(text)
    groups = {}
    group_id = 1

    for seg in segments:
        seg = seg.strip().rstrip('.')  # Remove trailing period
        if not seg:
            continue

        seg = remove_all_balanced_parentheses(seg)

        if is_complex_parenthetical(seg):
            expr = remove_outer_parens(seg)
            subgroups = split_by_top_level_or(expr)

            for subgroup in subgroups:
                sg, group_id = parse_comma_and_or_block(remove_outer_parens(subgroup.strip()), group_id)
                groups[group_id] = sg
                group_id += 1
        else:
            sg, group_id = parse_comma_and_or_block(seg, group_id)
            groups[group_id] = sg
            group_id += 1

    return {"groups": groups}

def split_top_level_semicolons(text):
    return [p.strip() for p in text.split(';') if p.strip()]

def is_complex_parenthetical(seg):
    return '(' in seg and ')' in seg and ' or ' in seg.lower()

def remove_all_balanced_parentheses(expr):
    s = expr.strip()
    while True:
        new_s = remove_one_balanced_layer(s)
        if new_s == s:
            return s
        s = new_s

def remove_one_balanced_layer(s):
    s = s.strip()
    if not (s.startswith('(') and s.endswith(')')):
        return s
    inside = s[1:-1].strip()
    if is_balanced(inside):
        return inside
    return s

def is_balanced(t):
    level = 0
    for c in t:
        if c == '(':
            level += 1
        elif c == ')':
            level -= 1
            if level < 0:
                return False
    return (level == 0)

def remove_outer_parens(expr):
    s = expr.strip()
    while s.startswith('(') and s.endswith(')') and parens_match_entire(s):
        s = s[1:-1].strip()
    return s

def parens_match_entire(s):
    level = 0
    for i, c in enumerate(s):
        if c == '(':
            level += 1
        elif c == ')':
            level -= 1
            if level == 0 and i < len(s) - 1:
                return False
    return (level == 0)

def split_by_top_level_or(expr):
    parts = []
    level = 0
    start = 0
    i = 0
    expr_len = len(expr)
    while i < expr_len:
        c = expr[i]
        if c == '(':
            level += 1
        elif c == ')':
            level -= 1

        if level == 0 and expr[i:i+3].lower() == ' or' and (i == 0 or expr[i-1].isspace()):
            part = expr[start:i].strip()
            if part:
                parts.append(part)
            i += 3
            while i < expr_len and expr[i].isspace():
                i += 1
            start = i
        else:
            i += 1
    if start < expr_len:
        part = expr[start:].strip()
        if part:
            parts.append(part)
    return parts

def split_top_level_comma(expr):
    parts = []
    level = 0
    start = 0
    i = 0
    while i < len(expr):
        c = expr[i]
        if c == '(':
            level += 1
        elif c == ')':
            level -= 1
        elif c == ',' and level == 0:
            chunk = expr[start:i].strip()
            if chunk:
                parts.append(chunk)
            i += 1
            while i < len(expr) and expr[i].isspace():
                i += 1
            start = i
            continue
        i += 1
    if start < len(expr):
        chunk = expr[start:].strip()
        if chunk:
            parts.append(chunk)
    return parts

#original
#def parse_comma_and_or_block(expr, group_id):
    blocks = split_top_level_comma(expr)
    result = []
    increment_group = False
    previous_group = None  

    for i, blk in enumerate(blocks):
        # Remove "or better" from the block
        blk = re.sub(r'\s+or\s+better', '', blk, flags=re.IGNORECASE).strip()
        print(f"Cleaned blk: {blk}")  # Debugging statement

        # Split by "or" after cleaning
        or_parts = re.split(r'\s+or\s+', blk)
        is_or_condition = len(or_parts) > 1  #???

        for j, part in enumerate(or_parts):
            original_part = part.strip()  
            part = original_part.strip('()')  

            logging.info(f"Processing part: {original_part}")
            if increment_group:
                group_id += 1
                increment_group = False

            if part:
                condition = "or" if is_or_condition else "and"  

                if ',' in part:
                    comma_parts = split_top_level_comma(part)
                    for k, sub_part in enumerate(comma_parts):
                        sub_part = sub_part.strip()
                        sub_condition = "and" if k > 0 else condition
                        result.append({
                            "course": sub_part,
                            "condition": sub_condition,
                            "group": group_id,
                            "related_group": previous_group if previous_group is not None else "N/A"
                        })
                else:
                    result.append({
                        "course": part,
                        "condition": condition,
                        "group": group_id,
                        "related_group": previous_group if previous_group is not None else "N/A"
                    })

                if original_part.endswith(')'):  
                    previous_group = group_id  
                    increment_group = True  

    return result, group_id  

def parse_comma_and_or_block(expr, group_id):
    """
    Parses a block of prerequisites containing "and", "or", and commas,
    ensuring conditions are assigned correctly based on parentheses context.
    """
    blocks = split_top_level_comma(expr)  # Split the expression by top-level commas
    result = []
    increment_group = False
    previous_group = None

    for i, blk in enumerate(blocks):
        # Remove "or better" from the block
        blk = re.sub(r'\s+or\s+better', '', blk, flags=re.IGNORECASE).strip()
        logging.info(f"Processing block: {blk}")

        # Split by "or" after cleaning
        or_parts = re.split(r'\s+or\s+', blk)
        is_or_condition = len(or_parts) > 1  # True if the block contains "or"

        for j, part in enumerate(or_parts):
            original_part = part.strip()
            part = original_part.strip('()')  # Remove surrounding parentheses for clarity
            logging.info(f"Processing part: {original_part}")

            if increment_group:
                group_id += 1
                increment_group = False

            if part:
                condition = "or" if is_or_condition else "and"  

                if ',' in part:  # Handle comma-separated lists (implies "and")
                    comma_parts = split_top_level_comma(part)
                    for sub_part in comma_parts:
                        sub_part = sub_part.strip()
                        sub_condition = (
                            "and" if original_part.startswith('(') and original_part.endswith(')') else 
                            ("and" if sub_part == comma_parts[-1] else "or")
                            )
                        result.append({
                            "course": sub_part,
                            "condition": sub_condition,
                            "group": group_id,
                            "related_group": previous_group if previous_group is not None else "N/A",
                            "group_condition": condition if previous_group else "N/A"
                        })
                else:  # Single course or nested part without commas
                    result.append({
                        "course": part,
                        "condition": condition,
                        "group": group_id,
                        "related_group": previous_group if previous_group is not None else "N/A",
                        "group_condition": condition if previous_group else "N/A"
                    })

                # If this part ends with a parenthesis, it might indicate a nested group
                if original_part.endswith(')'):
                    previous_group = group_id
                    increment_group = True

    return result, group_id


def sanitize_course(course):
    # Adjusted regex to stop discarding text after the course code
    match = re.search(r'\b([A-Z]{3}\s\d{3}[A-Z]{0,2})\b', course)
    #original re.match(r'^([A-Z]{3}\s\d{3}[A-Z]{0,2})', course)
    if match:
        # Return the full course with the description intact
        return match.group(1)
    return None

# original
# def flatten_breakdown(breakdown_dict, prereq=""):
    groups = breakdown_dict.get("groups", {})
    rows = []

    if not groups:  # Add the condition to handle empty groups
        rows.append(["1", "NA", prereq, "N/A", prereq])  # Fixed to match the expected output

    for g_id, courses in groups.items():
        for course_entry in courses:
            logging.info(f"course_entry: {course_entry}")
            sanitized_course = sanitize_course(course_entry["course"])
            if sanitized_course:
                rows.append([
                    course_entry["group"],
                    course_entry["condition"],
                    sanitized_course,
                    course_entry["related_group"],
                    prereq
                ])
    return rows

def flatten_breakdown(breakdown_dict, prereq=""):
    """
    Flattens the parsed prerequisite breakdown into rows suitable for saving to a CSV file.
    Ensures correct group_condition propagation for nested groups.
    """
    groups = breakdown_dict.get("groups", {})
    rows = []

    if not groups:  # Handle empty groups
        rows.append(["NA", "NA", prereq, "N/A", prereq, "N/A"])

    # Pass 1: Initialize group_conditions
    group_conditions = {}
    for g_id, courses in groups.items():
        if all(course["related_group"] == "N/A" for course in courses):
            # Standalone group: No inherited group_condition
            group_conditions[g_id] = "N/A"
        else:
            # Use the initial group_condition from parsing
            group_conditions[g_id] = courses[0].get("group_condition", "N/A")

    # Debug: Output initial group conditions
    print(f"Initial group_conditions: {group_conditions}")

    # Pass 2: Propagate group_conditions for nested groups
    for g_id, courses in groups.items():
        for course_entry in courses:
            if course_entry["related_group"] != "N/A":
                parent_group = int(course_entry["related_group"])
                if parent_group in group_conditions:
                    # Inherit group_condition from the parent group
                    group_conditions[g_id] = group_conditions[parent_group]

    # Debug: Output propagated group conditions
    print(f"Propagated group_conditions: {group_conditions}")

    # Pass 3: Generate rows for output
    for g_id, courses in groups.items():
        for course_entry in courses:
            group_condition = group_conditions.get(g_id, "N/A")
            sanitized_course = sanitize_course(course_entry["course"])
            if sanitized_course:
                rows.append([
                    course_entry["group"],         # Column 1: group
                    course_entry["condition"],     # Column 2: condition
                    sanitized_course,              # Column 3: course
                    course_entry["related_group"], # Column 4: related_group
                    prereq,                        # Column 5: prereq
                    group_condition                # Column 6: group_condition
                ])
    return rows


def save_breakdown_to_csv(breakdown_dict, csv_filename="prereqs.csv", prereq=""):
    rows = flatten_breakdown(breakdown_dict, prereq)
    if not rows:
        logging.warning("No valid rows to save to CSV. Adding placeholder row with 'NA'.")
        rows = [["NA", "NA", prereq, "N/A", prereq, "NA"]]  # Adjust to include group

    # Include group in the column headers
    df = pd.DataFrame(rows, columns=["group", "condition", "course", "related_group", "prereq", "group_condition"])

    directory = os.path.dirname(os.path.abspath(csv_filename))
    os.makedirs(directory, exist_ok=True)

    # Overwrite or create the file with headers always
    if not os.path.exists(csv_filename):
        df.to_csv(csv_filename, mode='w', header=True, index=False)
        logging.info(f"File created with headers: {csv_filename}")
    else:
        # Append without headers if the file exists
        df.to_csv(csv_filename, mode='a', header=False, index=False)
        logging.info(f"Appended data to: {csv_filename}")

if __name__ == "__main__":
    course_codes = [ "ARE 100A"   
    ]
    output_file = r"C:\\Users\\PC4\\OneDrive\\Desktop\\reg classproject\\prereq.csv"
    for course_code in course_codes:
        prereq_text =  "(ECN 001A C- or better or ECN 001AY C- or better or ECN 001AV C- or better); (ECN 001B C- or better or ECN 001BV C- or better); ((MAT 016A C- or better, MAT 016B C- or better, MAT 016C C- or better) or (MAT 017A C- or better, MAT 017B C- or better) or (MAT 021A C- or better, MAT 021B C- or better))."

        #        #"MAT 021C; ((MAT 022A or MAT 027A or BIS 027A, MAT 108) or MAT 067))."
        if prereq_text:
            breakdown = break_down_prereq_text(prereq_text)
            save_breakdown_to_csv(breakdown, csv_filename=output_file, prereq=course_code)
            print(f"Prerequisites for {course_code} have been saved successfully.")
        else:
            prereq_text = ""
            breakdown = break_down_prereq_text(prereq_text)
            save_breakdown_to_csv(breakdown, csv_filename=output_file, prereq=course_code)

    # Close the browser after all courses have been processed

    print(f"All course prerequisites have been saved to {output_file}.")

