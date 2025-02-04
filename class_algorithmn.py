import pandas as pd

# Load the CSV file
data = pd.read_csv('C:/Users/PC4/OneDrive/Desktop/reg classproject/prereq.csv')

# Build a prerequisite mapping with grouping logic
group_dict = {}
for index, row in data.iterrows():
    group = row['group']
    condition = row['condition']
    course = row['course']
    prereq = row['prereq']
    related_group = row['related_group']

    # Group mapping
    if prereq not in group_dict:
        group_dict[prereq] = {}
    if group not in group_dict[prereq]:
        group_dict[prereq][group] = {"condition": condition, "courses": []}
    group_dict[prereq][group]["courses"].append(course)

# Check if a prerequisite is satisfied with related group handling
def check_related_groups(prereq, group_dict, course_codes):
    if prereq not in group_dict:
        return True  # Prerequisite is not defined, assume it's satisfied

    all_groups_satisfied = True
    missing_courses = []

    for group, details in group_dict[prereq].items():
        condition = details["condition"]
        courses = details["courses"]

        if condition == "and":
            # All courses in the group must be satisfied
            unsatisfied = [course for course in courses if course not in course_codes]
            if unsatisfied:
                missing_courses.append({"condition": "and", "missing": unsatisfied})
                all_groups_satisfied = False
        elif condition == "or":
            # At least one course in the group must be satisfied
            if any(course in course_codes for course in courses):
                return True  # Stop as soon as one "or" group is satisfied
            else:
                missing_courses.append({"condition": "or", "missing": courses})
                all_groups_satisfied = False

    # Return results based on evaluation
    return True if all_groups_satisfied else missing_courses

# Evaluate the prerequisites for all courses in the `prereq` column
course_codes = ["ECS 010","ECS 030",
    
]
#"ECS 017","ECS 032A","ECS 032B","MAT 021A","MAT 021B","MAT 021C","MAT 022A",
#    "STA 035A","STA 035B","STA 035C","ECS 116","ECS 117","ECS 119","STA 108",
#    "STA 141A","STA 131A","MAT 170","MAT 168","MAT 167","STS 101"

prereqs_to_check = data['prereq'].unique()
for prereq in prereqs_to_check:
    if prereq != "N/A":  # Skip invalid prereqs
        result = check_related_groups(prereq, group_dict, course_codes)
        if result is True:
            print(f"{prereq}: Prerequisite satisfied.")
        else:
            print(f"{prereq}: Missing prerequisites:")
            for item in result:
                print(f"  - Condition: {item['condition']}, Missing: {', '.join(item['missing'])}")
