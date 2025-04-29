import re
import json
from itertools import count

# --- Tokenizer ---
def tokenize(expr):
    expr = re.sub(r'\(can be concurrent\)', '', expr, flags=re.IGNORECASE)
    expr = re.sub(r'\{.*?\}', '', expr)

    expr = re.sub(r'\b(C-|B|A|D|F)\s*or\s*better\b', '', expr, flags=re.IGNORECASE)
    expr = re.sub(r'\b(C-|B|A|D|F)\b', '', expr, flags=re.IGNORECASE)
    expr = re.sub(r'\bor better\b', '', expr, flags=re.IGNORECASE)

    expr = re.sub(r'\b([A-Z]{2,4})\s+(\d{3}[A-Z]{0,2})\b', r'\1_\2', expr)

    expr = re.sub(r'([(),;.])', r' \1 ', expr)

    tokens = expr.split()
    return [t.replace('_', ' ') for t in tokens if t.strip() and t != '.']

# --- Parser ---
def parse_expr(tokens, index=0):
    elements = []
    current = []
    current_op = None
    groups = []
    depth = 0

    while index < len(tokens):
        token = tokens[index]

        if token == '(':
            depth += 1
            index, sub_expr = parse_expr(tokens, index + 1)
            current.append(sub_expr)
        elif token == ')':
            depth -= 1
            break
        elif token.lower() == 'or':
            current_op = 'or'
        elif token == ';':
            if current:
                if current_op == 'or' and len(current) > 1:
                    groups.append({'or': current})
                else:
                    groups.append(current[0])
                current = []
            current_op = None
        elif token == ',':
            if current_op == 'or' and len(current) > 1:
                groups.append({'or': current})
                current = []
            current_op = 'and'
        else:
            current.append(token)

        index += 1

    if current:
        if current_op == 'or' and len(current) > 1:
            groups.append({'or': current})
        elif current_op == 'and' and len(current) > 1:
            groups.append({'and': current})
        else:
            groups.extend(current)

    if len(groups) == 1:
        return index, groups[0]
    else:
        return index, {'and': groups}

# --- Top-level parser ---
def parse(tokens):
    if not tokens:
        return 0, {}  # Empty input protection

    groups = []
    current = []
    depth = 0

    for token in tokens:
        if token == '(':
            depth += 1
        elif token == ')':
            depth -= 1

        if token == ';' and depth == 0:
            if current:
                groups.append(current)
                current = []
        else:
            current.append(token)

    if current:
        groups.append(current)

    parsed_groups = []
    for group in groups:
        _, parsed = parse_expr(group)
        parsed_groups.append(parsed)

    if not parsed_groups:
        return 0, {}  # More protection

    return 0, {'and': parsed_groups} if len(parsed_groups) > 1 else parsed_groups[0]

# --- Label Generator ---
def part_label_gen():
    counter = count(1)
    while True:
        yield f"Part {next(counter)}"

# --- JSON Builder ---
def build_json(tree, label_gen):
    if isinstance(tree, list):
        return {
            "type": "and",
            "parts": [build_json(i, label_gen) for i in tree]
        }
    if isinstance(tree, str):
        return {
            "label": next(label_gen),
            "type": "single",
            "course": tree
        }
    if isinstance(tree, dict):
        if not tree:  # Empty dict case
            return {
                "label": next(label_gen),
                "type": "none",
                "note": "No prerequisites"
            }
        op, items = next(iter(tree.items()))
        if op == 'or' and all(isinstance(i, str) for i in items):
            return {
                "label": next(label_gen),
                "type": "or",
                "courses": items
            }
        return {
            "type": op,
            "parts": [build_json(i, label_gen) for i in items]
        }

# --- Integration method ---
def parse_prereq_json(course_codes, prereq_texts):
    all_output = {}
    for course_code, expr in zip(course_codes, prereq_texts):
        tokens = tokenize(expr)
        if not tokens:
            all_output[course_code] = {
                "label": "Part 1",
                "type": "none",
                "note": "No prerequisites"
            }
            continue
        _, parsed = parse(tokens)
        label_gen = part_label_gen()
        json_data = build_json(parsed, label_gen)
        all_output[course_code] = json_data
    return all_output

# --- Example to test ---
def main():
    course_codes = ["ECS 017"]
    prereq_texts = [""]

    output = parse_prereq_json(course_codes, prereq_texts)

    with open("parsed_prereqs.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\u2705 Prerequisite structure saved to parsed_prereqs.json")

if __name__ == "__main__":
    main()
