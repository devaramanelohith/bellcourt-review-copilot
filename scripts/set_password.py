"""Set or reset a login.  python scripts/set_password.py <username> <role: nurse|physician|intake|auditor> "<display name>"
Prompts for the password and stores only a salted PBKDF2 hash in copilot/users.json."""
import os, sys, json, getpass, secrets, hashlib
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "copilot", "users.json")
user, role, name = sys.argv[1].lower(), sys.argv[2], sys.argv[3]; assert role in ("nurse", "physician", "intake", "auditor")
pw = getpass.getpass("New password: "); salt = secrets.token_hex(16); users = json.load(open(p))
users[user] = dict(name=name, role=role, salt=salt, hash=hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000).hex())
json.dump(users, open(p, "w"), indent=1); print("saved", user)
