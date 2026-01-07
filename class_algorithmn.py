

# =============================================================
# UC DAVIS PASS-1 AWARE COURSE SCHEDULER
# (Standalone – no external CSV needed)
# =============================================================

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

PASS1_TOTAL_DAYS = 12
UNITS_PER_COURSE = 4
MAX_COURSES_PER_SEMESTER = 4

# ─────────────────────────────────────────────────────────────
# EMBEDDED COURSE FILL DATA
# None  -> does NOT fill during Pass 1
# Int N -> fills on Pass 1 day N
# ─────────────────────────────────────────────────────────────
import csv

#COURSE_TRACKER_CSV = (
#    "C:/Users/PC4/OneDrive/Desktop/reg classproject/course_open_tracker.csv"
#)
COURSE_FILL_DAYS = {
    # Math / ECS bottlenecks
    "MAT 021A": None,
    "MAT 021B": None,
    "ECS 032A": None,
    "ECS 032AV": None,
    "ECS 036A": None,
    "ECS 036B": None,

    # Statistics sequence
    "STA 013": None,
    "STA 013Y": None,
    "STA 032": None,
    "STA 035A": None,
    "STA 035B": None,
    "STA 035C": None,

    # Writing / GE
    "UWP 101": 3,
    "GE HUM": None,
}

# ─────────────────────────────────────────────────────────────
# PREREQUISITE STRUCTURE
# ─────────────────────────────────────────────────────────────

prerequisites = {
    "STA 035B": {
        "type": "and",
        "parts": [
            {
                "type": "or",
                "parts": [
                    {
                        "type": "and",
                        "parts": [
                            {"type": "or", "courses": ["STA 013", "STA 013Y"]},
                            {"type": "or", "courses": ["ECS 032A", "ECS 032AV"]}
                        ]
                    },
                    {"type": "single", "course": "STA 032"},
                    {"type": "single", "course": "STA 035A"},
                    {"type": "single", "course": "STA 100"}
                ]
            },
            {"type": "or", "courses": ["MAT 021B"]}
        ]
    },
    "STA 035C": {
        "type": "and",
        "parts": [
            {"type": "single", "course": "STA 035B"},
            {"type": "or", "courses": ["MAT 021B"]}
        ]
    }
}

# ─────────────────────────────────────────────────────────────
# PASS 1 DAY ESTIMATOR (DYNAMIC)
# ─────────────────────────────────────────────────────────────

def estimate_pass1_day(total_units):
    if total_units >= 135:
        return 3      # senior
    elif total_units >= 90:
        return 6      # junior
    elif total_units >= 45:
        return 9      # sophomore
    else:
        return 11     # freshman

# ─────────────────────────────────────────────────────────────
# COURSE AVAILABILITY
# ─────────────────────────────────────────────────────────────

def course_available(course, pass1_day):
    d = COURSE_FILL_DAYS.get(course)
    return d is None or d >= pass1_day

# ─────────────────────────────────────────────────────────────
# PREREQUISITE RESOLUTION
# ─────────────────────────────────────────────────────────────

def resolve_prereq(node, completed):
    if node["type"] == "single":
        return set() if node["course"] in completed else {node["course"]}

    if node["type"] == "or":
        best = None
        for opt in node.get("courses", []) + node.get("parts", []):
            needed = {opt} if isinstance(opt, str) else resolve_prereq(opt, completed)
            if best is None or len(needed) < len(best):
                best = needed
        return best or set()

    if node["type"] == "and":
        req = set()
        for part in node.get("courses", []) + node.get("parts", []):
            req |= {part} if isinstance(part, str) else resolve_prereq(part, completed)
        return req

    return set()

def collect_all_courses(prereqs):
    courses = set(prereqs.keys())
    for p in prereqs.values():
        stack = [p]
        while stack:
            n = stack.pop()
            if n["type"] == "single":
                courses.add(n["course"])
            else:
                stack.extend(n.get("parts", []))
                courses.update(n.get("courses", []))
    return courses

# ─────────────────────────────────────────────────────────────
# SCHEDULER CORE
# ─────────────────────────────────────────────────────────────

def build_schedule(start_units):
    all_courses = collect_all_courses(prerequisites)
    completed = set()
    remaining = set(all_courses)
    total_units = start_units
    semester = 1
    plan = []

    while remaining:
        pass1_day = estimate_pass1_day(total_units)
        available = []

        for c in sorted(remaining):
            if not course_available(c, pass1_day):
                continue

            if c not in prerequisites:
                available.append(c)
            else:
                needed = resolve_prereq(prerequisites[c], completed)
                if needed.issubset(completed):
                    available.append(c)
                else:
                    for n in needed:
                        if n in remaining and course_available(n, pass1_day):
                            available.append(n)

        if not available:
            raise RuntimeError(
                f"No feasible courses (semester {semester}, Pass 1 day {pass1_day})"
            )

        taking = available[:MAX_COURSES_PER_SEMESTER]

        plan.append({
            "semester": semester,
            "units_before": total_units,
            "pass1_day": pass1_day,
            "courses": taking
        })

        completed |= set(taking)
        remaining -= set(taking)
        total_units += len(taking) * UNITS_PER_COURSE
        semester += 1

    return plan

# ─────────────────────────────────────────────────────────────
# RUN DEMO
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    schedule = build_schedule(start_units=32)

    for s in schedule:
        print(f"\nSemester {s['semester']}")
        print(f"  Units before: {s['units_before']}")
        print(f"  Pass 1 day:   {s['pass1_day']}")
        for c in s["courses"]:
            print(f"   - {c}")
