import os

expected_paths = [
    'app.py',
    'requirements.txt',
    'templates/index.html',
    'app/__init__.py',
    'app/config.py',
    'app/routes.py',
]

print("\n✅ Checking FaceCrypt-Cloud project structure...\n")

all_ok = True

for path in expected_paths:
    if os.path.exists(path):
        print(f"✔️ FOUND: {path}")
    else:
        print(f"❌ MISSING: {path}")
        all_ok = False

if all_ok:
    print("\n🎯 Your project structure looks correct! ✅")
else:
    print("\n⚠️ There are missing or misplaced files. Please fix them.")
