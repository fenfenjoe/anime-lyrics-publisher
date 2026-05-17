import subprocess, sys

result = subprocess.run(
    [sys.executable, 'workbuddy_automation.py', 'daily-publish'],
    capture_output=True,
    encoding='utf-8',
    errors='replace',
    cwd=r'c:\Users\Admin\WorkBuddy\Claw\anime-lyrics-publisher'
)

with open(r'c:\Users\Admin\WorkBuddy\Claw\anime-lyrics-publisher\data\publish_log.txt', 'w', encoding='utf-8') as f:
    f.write("STDOUT:\n")
    f.write(result.stdout or "(empty)")
    f.write("\nSTDERR:\n")
    f.write(result.stderr or "(empty)")
    f.write(f"\nEXIT CODE: {result.returncode}\n")

print("publish done, exit code:", result.returncode)
