# -*- coding: utf-8 -*-
import subprocess, sys, os

os.chdir(r'c:\Users\Admin\WorkBuddy\Claw\anime-lyrics-publisher')
env = os.environ.copy()
env['PYTHONIOENCODING'] = 'utf-8'

r = subprocess.run(
    [sys.executable, 'workbuddy_automation.py', 'daily-prepare'],
    capture_output=True,
    env=env
)

out = r.stdout.decode('utf-8', errors='replace')
err = r.stderr.decode('utf-8', errors='replace')

with open('daily_prepare_out.txt', 'w', encoding='utf-8') as f:
    f.write(out)
    f.write(err)

print("returncode:", r.returncode)
print("written to daily_prepare_out.txt")
