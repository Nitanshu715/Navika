# Run this to check if your .env is being read correctly
# Save as check_env.py in D:\finance_ai\ and run: python check_env.py

from dotenv import load_dotenv
import os

load_dotenv()

print("=== ENV CHECK ===")
keys = ["GEMINI_API_KEY", "GMAIL_USER", "GMAIL_APP_PASSWORD", 
        "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "APP_URL"]

for k in keys:
    v = os.getenv(k, "")
    if v:
        # Show first/last 4 chars only for security
        if len(v) > 10:
            display = v[:4] + "..." + v[-4:]
        else:
            display = "SET (short value)"
        print(f"  {k:30} = {display}")
    else:
        print(f"  {k:30} = *** NOT SET / EMPTY ***")

print()
print(".env file location check:")
import pathlib
env_files = [
    pathlib.Path("D:/finance_ai/.env"),
    pathlib.Path(".env"),
]
for f in env_files:
    exists = f.exists()
    print(f"  {f}: {'EXISTS ✓' if exists else 'NOT FOUND ✗'}")
    if exists:
        print(f"  Contents preview:")
        for line in f.read_text().splitlines()[:10]:
            if "=" in line and not line.startswith("#"):
                k = line.split("=")[0].strip()
                print(f"    {k} = [value present]")