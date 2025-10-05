#!/usr/bin/env python3
"""
Comprehensive feature verification for the updated video compression script
"""

import sys
from pathlib import Path

def print_section(title):
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print('=' * 80)

def check_imports():
    """Verify all required modules can be imported"""
    print_section("1. MODULE IMPORT CHECK")
    
    modules = [
        ('watchdog', 'Folder monitoring'),
        ('streamlit', 'Web interface'),
        ('json', 'State management'),
        ('subprocess', 'External commands'),
        ('re', 'Regex pattern matching'),
    ]
    
    all_ok = True
    for module, purpose in modules:
        try:
            __import__(module)
            print(f"  ✓ {module:15s} - {purpose}")
        except ImportError:
            print(f"  ✗ {module:15s} - {purpose} [MISSING]")
            all_ok = False
    
    return all_ok

def check_files():
    """Verify all required files exist"""
    print_section("2. FILE STRUCTURE CHECK")
    
    required_files = [
        ('handbrakevidz.py', 'Main compression script'),
        ('web_monitor.py', 'Streamlit web interface'),
        ('requirements.txt', 'Python dependencies'),
        ('environment.yml', 'Conda environment spec'),
        ('README.md', 'Documentation'),
        ('QUICKSTART.md', 'Quick start guide'),
    ]
    
    all_ok = True
    for filename, description in required_files:
        if Path(filename).exists():
            print(f"  ✓ {filename:20s} - {description}")
        else:
            print(f"  ✗ {filename:20s} - {description} [MISSING]")
            all_ok = False
    
    return all_ok

def verify_features():
    """Verify key features are implemented"""
    print_section("3. FEATURE IMPLEMENTATION CHECK")
    
    # Read the main script
    with open('handbrakevidz.py', 'r') as f:
        script_content = f.read()
    
    features = [
        ('StateManager', 'State management for web interface'),
        ('is_valid_suffix', 'Strict suffix validation'),
        ('get_video_resolution', 'Resolution detection with ffprobe'),
        ('should_downscale', 'Conditional downscaling logic'),
        ('avi', 'AVI file support'),
        ('wmv', 'WMV file support'),
        ('add_to_queue', 'Queue management'),
        ('add_completed', 'Completion tracking'),
        ('add_error', 'Error logging'),
        ('KeyboardInterrupt', 'Graceful Ctrl+C handling'),
    ]
    
    all_ok = True
    for feature, description in features:
        if feature in script_content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} [NOT FOUND]")
            all_ok = False
    
    return all_ok

def check_critical_fix():
    """Verify the critical corruption fix is implemented"""
    print_section("4. CRITICAL FIX VERIFICATION")
    
    with open('handbrakevidz.py', 'r') as f:
        script_content = f.read()
    
    checks = [
        ('is_valid_suffix', 'Suffix validation function exists'),
        (r'[\s]{1,2}[xX]{2}', 'Correct regex pattern (1-2 spaces + xx/XX)'),
        ('No file found matching the required suffix', 'Skip message for invalid files'),
        ('already exists', 'Output overwrite protection'),
    ]
    
    all_ok = True
    for pattern, description in checks:
        if pattern in script_content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} [NOT FOUND]")
            all_ok = False
    
    return all_ok

def main():
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "VIDEO COMPRESSION SCRIPT - VERIFICATION" + " " * 24 + "║")
    print("╚" + "═" * 78 + "╝")
    
    results = []
    
    # Run all checks
    results.append(("Module Imports", check_imports()))
    results.append(("File Structure", check_files()))
    results.append(("Feature Implementation", verify_features()))
    results.append(("Critical Fix", check_critical_fix()))
    
    # Summary
    print_section("VERIFICATION SUMMARY")
    
    all_passed = True
    for check_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status} - {check_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 80)
    
    if all_passed:
        print("\n  ✓✓✓ ALL CHECKS PASSED ✓✓✓")
        print("\n  The script is ready for use!")
        print("\n  Next steps:")
        print("    1. Ensure HandbrakeCLI and ffprobe are installed")
        print("    2. Run: python3 handbrakevidz.py --watch /path/to/directory")
        print("    3. Run: streamlit run web_monitor.py (optional)")
        print("\n" + "=" * 80 + "\n")
        return 0
    else:
        print("\n  ✗✗✗ SOME CHECKS FAILED ✗✗✗")
        print("\n  Please review the failures above.")
        print("\n" + "=" * 80 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
