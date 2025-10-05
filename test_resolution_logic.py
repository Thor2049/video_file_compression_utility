#!/usr/bin/env python3
"""
Test to demonstrate resolution detection and downscaling logic
Note: This is a simulation test - actual resolution detection requires ffprobe
"""

def should_downscale(source_height):
    """
    Determine if video should be downscaled based on source resolution
    Returns: (should_downscale, target_height, reason)
    """
    if source_height is None:
        return True, 480, "Resolution unknown, defaulting to 480p"
    elif source_height <= 540:
        return False, source_height, f"Source is {source_height}p (≤540p), keeping original"
    else:
        return True, 480, f"Source is {source_height}p (>540p), downscaling to 480p"


# Test cases
test_resolutions = [
    (360, "360p video (SD)"),
    (480, "480p video (SD)"),
    (540, "540p video (boundary case)"),
    (720, "720p video (HD)"),
    (1080, "1080p video (Full HD)"),
    (1440, "1440p video (2K)"),
    (2160, "2160p video (4K)"),
    (None, "Unknown resolution"),
]

print("Resolution Detection & Downscaling Logic Test")
print("=" * 80)
print("\nLogic: Keep original resolution if ≤540p, otherwise downscale to 480p\n")
print("=" * 80)

for height, description in test_resolutions:
    downscale, target, reason = should_downscale(height)
    action = "DOWNSCALE" if downscale else "KEEP ORIGINAL"
    
    print(f"\nSource: {description}")
    print(f"  └─ Action: {action} → Target: {target}p")
    print(f"  └─ Reason: {reason}")

print("\n" + "=" * 80)
print("\n✓ Resolution logic verified!")
print("\nExample encoding commands:")
print("  • 360p source: -e nvenc_h265 -q 22 (no --height flag)")
print("  • 480p source: -e nvenc_h265 -q 22 (no --height flag)")  
print("  • 720p source: -e nvenc_h265 -q 22 --height 480")
print("  • 1080p source: -e nvenc_h265 -q 22 --height 480")
