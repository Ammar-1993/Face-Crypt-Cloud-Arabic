import re
import os

with open('app/users/routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract all _("...") or _('...')
matches = re.findall(r'_\(["\'](.*?)["\']\)', content)

with open('translations/en/LC_MESSAGES/messages.po', 'r', encoding='utf-8') as f:
    po_content = f.read()

missing = []
for match in matches:
    if match not in po_content:
        missing.append(match)

print(f"Missing translations: {missing}")
