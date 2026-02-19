"""
generate_icons.py - Creates PWA icons for CliniCall
Run: python generate_icons.py
Requires: Pillow (pip install pillow)
"""
import math

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
    from PIL import Image, ImageDraw

def draw_icon(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle - dark charcoal
    margin = size * 0.04
    draw.ellipse([margin, margin, size - margin, size - margin], fill=(28, 28, 30, 255))

    # Green pulse/phone symbol
    cx, cy = size / 2, size / 2
    s = size * 0.28  # scale

    # Draw a simplified phone handset shape in white
    lw = max(2, size // 30)

    # Phone body (rounded rectangle)
    px0, py0 = cx - s * 0.55, cy - s * 0.7
    px1, py1 = cx + s * 0.55, cy + s * 0.7
    draw.rounded_rectangle([px0, py0, px1, py1], radius=s * 0.25, fill=None, outline=(52, 199, 89, 255), width=lw)

    # Small screen area
    sx0, sy0 = cx - s * 0.3, cy - s * 0.4
    sx1, sy1 = cx + s * 0.3, cy + s * 0.1
    draw.rounded_rectangle([sx0, sy0, sx1, sy1], radius=s * 0.1, fill=(52, 199, 89, 180))

    # Home button circle
    hcx, hcy, hr = cx, cy + s * 0.5, s * 0.12
    draw.ellipse([hcx - hr, hcy - hr, hcx + hr, hcy + hr], outline=(52, 199, 89, 255), width=lw)

    # White "AI" text in center
    text_size = max(10, size // 8)
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("arial.ttf", text_size)
    except Exception:
        font = ImageFont.load_default()

    text = "AI"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw / 2, cy - s * 0.2 - th / 2), text, fill=(255, 255, 255, 255), font=font)

    return img

output_dir = "app/static"

for size, name in [(192, "icon-192.png"), (512, "icon-512.png")]:
    icon = draw_icon(size)
    path = f"{output_dir}/{name}"
    icon.save(path, "PNG")
    print(f"Created {path} ({size}x{size})")

print("\nDone! Icons saved to app/static/")
