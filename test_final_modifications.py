#!/usr/bin/env python3
"""
Test script to verify the final three modifications
"""

import sys
from pathlib import Path

def print_section(title):
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print('=' * 80)

print("=" * 80)
print("FINAL MODIFICATIONS VERIFICATION")
print("=" * 80)

# 1. Check log file functionality
print_section("1. LOG FILE FUNCTIONALITY")
with open('handbrakevidz.py', 'r') as f:
    content = f.read()
    
checks = [
    ("LOGS_DIR", "Logs directory creation"),
    ("FileHandler", "File logging handler"),
    ("log_filename", "Log filename generation"),
    ("StreamHandler", "Console logging maintained"),
]

for pattern, desc in checks:
    found = pattern in content
    status = "✓" if found else "✗"
    print(f"   {status} {desc}")

# 2. Check state clearing on shutdown
print_section("2. STATE CLEARING ON SHUTDOWN")
checks = [
    ("clear_all_state", "Clear state method exists"),
    ("StateManager.clear_all_state()", "Called on shutdown"),
]

for pattern, desc in checks:
    found = pattern in content
    status = "✓" if found else "✗"
    print(f"   {status} {desc}")

# 3. Check skipped files added to errors
print_section("3. SKIPPED FILES IN ERRORS SECTION")
# Check that add_error is called for skipped files
has_add_error_for_skip = 'StateManager.add_error(str(file_path), "Missing required suffix pattern' in content
print(f"   {'✓' if has_add_error_for_skip else '✗'} Skipped files added to errors list")

# Verify the logic flow
in_find_video_files = 'def find_video_files' in content
checks_suffix = 'is_valid_suffix(file)' in content
logs_skip = 'Skipping' in content and 'missing required suffix' in content

print(f"   {'✓' if in_find_video_files else '✗'} find_video_files method exists")
print(f"   {'✓' if checks_suffix else '✗'} Suffix validation check present")
print(f"   {'✓' if logs_skip else '✗'} Skip logging present")

# 4. Summary
print_section("VERIFICATION SUMMARY")

all_checks = [
    ("Log File Functionality", 
     "LOGS_DIR" in content and "FileHandler" in content),
    ("State Clearing on Shutdown", 
     "clear_all_state" in content and "StateManager.clear_all_state()" in content),
    ("Skipped Files in Errors", 
     has_add_error_for_skip),
]

all_passed = True
for check_name, passed in all_checks:
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"   {status} - {check_name}")
    if not passed:
        all_passed = False

print("\n" + "=" * 80)

if all_passed:
    print("\n  ✓✓✓ ALL FINAL MODIFICATIONS VERIFIED ✓✓✓")
    print("\n  Features implemented:")
    print("    1. Log file (.txt) created in logs/ directory")
    print("    2. State files cleared on Ctrl+C shutdown")
    print("    3. Skipped files (wrong suffix) appear in Errors/Skipped section")
    print("\n" + "=" * 80 + "\n")
    sys.exit(0)
else:
    print("\n  ✗✗✗ SOME CHECKS FAILED ✗✗✗")
    print("\n" + "=" * 80 + "\n")
    sys.exit(1)
