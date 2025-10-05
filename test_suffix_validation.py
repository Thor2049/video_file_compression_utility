#!/usr/bin/env python3
"""
Test script to verify suffix validation logic
"""

import re

def is_valid_suffix(filename):
    """
    Check if filename has valid suffix pattern.
    Pattern: 1-2 spaces followed by 'xx' or 'XX' before extension
    Supports: .mp4, .mkv, .avi, .wmv, .mpg
    Examples: "file xx.mp4", "file  XX.mkv", "video  xx.avi"
    """
    pattern = r'[\s]{1,2}[xX]{2}\.(mp4|mkv|avi|wmv|mpg)$'
    return bool(re.search(pattern, filename))


# Test cases
test_files = [
    # Valid files (should return True)
    ("video xx.mp4", True),
    ("video  xx.mp4", True),
    ("video XX.mp4", True),
    ("video  XX.mp4", True),
    ("movie xx.mkv", True),
    ("movie  XX.mkv", True),
    ("clip xx.avi", True),
    ("clip  xx.wmv", True),
    ("my video xx.mp4", True),
    ("my_video  XX.mkv", True),
    
    # Invalid files (should return False)
    ("video.mp4", False),
    ("video.mkv", False),
    ("videoxx.mp4", False),  # No space
    ("video   xx.mp4", False),  # 3 spaces (too many)
    ("video x.mp4", False),  # Only one 'x'
    ("video xxx.mp4", False),  # Three 'x's
    ("video Xx.mp4", False),  # Mixed case
    ("video xX.mp4", False),  # Mixed case
    ("video xx.txt", False),  # Wrong extension
    ("video xx.mov", False),  # Unsupported extension
]

print("Testing suffix validation logic...\n")
print("=" * 70)

passed = 0
failed = 0

for filename, expected in test_files:
    result = is_valid_suffix(filename)
    status = "✓ PASS" if result == expected else "✗ FAIL"
    
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"{status} | '{filename}' | Expected: {expected}, Got: {result}")

print("=" * 70)
print(f"\nTest Results: {passed} passed, {failed} failed out of {len(test_files)} tests")

if failed == 0:
    print("✓ All tests passed!")
else:
    print(f"✗ {failed} test(s) failed!")
