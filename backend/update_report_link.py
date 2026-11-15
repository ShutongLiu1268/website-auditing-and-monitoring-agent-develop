"""
Update report to make screenshot clickable
"""
import re
from pathlib import Path

# Read the report
report_file = Path("C:/Users/Shutong_Liu/OneDrive - Dell Technologies/Desktop/website-auditing-and-monitoring-agent-develop/backend/analysis_report_20261115_104712.md")

with open(report_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace screenshot line with clickable link
content = re.sub(
    r'\|\|\| \*\*Screenshot\*\* \| ([^|]+) \|',
    r'||| **Screenshot** | [\1](\1) |',
    content
)

# Write back
with open(report_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Updated {report_file} with clickable screenshot link")
