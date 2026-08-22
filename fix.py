with open("app/admin/routes.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if "def check_admin_session(f):" in line:
        skip = True
    if skip and "return decorated_function" in line:
        skip = False
        continue
    if not skip:
        new_lines.append(line)

content = "".join(new_lines)
content = content.replace('return jsonify({"error": "Unauthorized"}), 401', 'return jsonify({"error": "غير مصرح لك بالوصول"}), 401')
content = content.replace('        token = session.get("csrf_token")\n', '')
with open("app/admin/routes.py", "w") as f:
    f.write(content)
