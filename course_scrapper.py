import requests
import re
import json
import pandas as pd


def diagnose(content: str):
    """Print helpful clues when the main pattern finds nothing."""
    print("\n--- DIAGNOSTICS ---")
    print(f"File size: {len(content):,} characters")

    for needle in ['"course_name"', '"course_id"', "course_name", "require_documents",
                   "course_duration", '\\"course_name\\"']:
        count = content.count(needle)
        print(f'Occurrences of {needle!r}: {count}')

    # Show a small window of context around the first hit of "course_name"
    for needle in ['"course_name"', '\\"course_name\\"']:
        idx = content.find(needle)
        if idx != -1:
            start = max(0, idx - 80)
            end = idx + 200
            print(f"\nContext around {needle!r} (chars {start}-{end}):")
            print(content[start:end])
            break
    else:
        print("\n'course_name' not found anywhere in the file at all.")
        print("This is likely a DIFFERENT page/site than the one this script")
        print("was built for — the data may be loaded via a separate API call")
        print("(check the browser's Network tab for an XHR/fetch request that")
        print("returns JSON), rather than being embedded directly in the HTML.")
    print("--- END DIAGNOSTICS ---\n")


def extract_courses(content: str) -> list[dict]:
#     with open(html_path, encoding="utf-8") as f:
#         content = f.read()

    # Try a few patterns, in order, in case quotes are escaped differently
    # (e.g. \"course\": instead of "course":) depending on how the HTML
    # was saved/exported.
    patterns = [
        r'"course":(\{.*?\}),"package_id"',      # normal quotes
        r'\\"course\\":(\{.*?\}),\\"package_id\\"',  # backslash-escaped quotes
        r'"course_name"\s*:\s*"[^"]*".*?"require_documents"\s*:\s*"[^"]*"',  # loose fallback
    ]

    raw_matches = []
    for pat in patterns:
        raw_matches = re.findall(pat, content, flags=re.DOTALL)
        if raw_matches:
            break

    if not raw_matches:
        diagnose(content)
        raise ValueError(
            "No course objects found with any known pattern. See diagnostics "
            "above — you likely need a different extraction pattern for this "
            "page, or the data loads via a separate API call."
        )

    seen = {}
    for raw in raw_matches:
        # Unescape backslash-escaped quotes if present, then parse
        cleaned = raw.replace('\\"', '"')
        try:
            obj = json.loads(cleaned)
        except json.JSONDecodeError:
            continue
        seen[obj.get("course_id", obj.get("course_name"))] = obj

    if not seen:
        raise ValueError(
            "Found candidate matches but couldn't parse any as valid JSON. "
            "The structure may differ from what this script expects."
        )

    courses = sorted(seen.values(), key=lambda c: c.get("course_showing_order", 0))
    return courses


def to_dataframe(courses: list[dict]) -> pd.DataFrame:
    rows = []
    for c in courses:
        batches = c.get("batches", [])
        batch_dates = "; ".join(
            f"{b.get('start_date')} to {b.get('end_date')}" for b in batches
        )
        rows.append({
            "course_id": c.get("course_id"),
            "course_code": c.get("course_code"),
            "course_name": c.get("course_name"),
            "required_documents": c.get("require_documents"),
            "duration": c.get("course_duration"),
            "fee": c.get("course_fee"),
            "total_seats": c.get("total_seats"),
            "remain_seats": c.get("remain_seats"),
            "batch_dates": batch_dates,
            "num_batches": len(batches),
        })
    return pd.DataFrame(rows)

def get_course_data(url: str):
#     url = "https://seiedutrust.com/our-courses/kolkata"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers)
        print(response.status_code)
    except Exception as e:
        print(e)
        return {}

    html_data = response.text
    
    if(response.status_code == 200):
        courses = extract_courses(html_data)
        print(f"Found {len(courses)} unique courses.")
        return courses
    else:
        return {}