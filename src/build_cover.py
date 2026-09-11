from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "release" / "dataset-cover-image.png"
QA_CARD = ROOT / "qa" / "cover-card-preview.png"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf"),
        Path(r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def centered_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fnt, fill) -> None:
    box = draw.textbbox((0, 0), text, font=fnt)
    width = box[2] - box[0]
    draw.text((xy[0] - width / 2, xy[1]), text, font=fnt, fill=fill)


def main() -> None:
    width, height = 560, 280
    image = Image.new("RGB", (width, height), (10, 28, 48))
    px = image.load()
    # Subtle vertical gradient: dark technical blue -> lighter road-horizon blue.
    for y in range(height):
        t = y / (height - 1)
        r = int(10 + 17 * t)
        g = int(28 + 33 * t)
        b = int(48 + 40 * t)
        for x in range(width):
            px[x, y] = (r, g, b)

    draw = ImageDraw.Draw(image)
    white = (242, 247, 250)
    muted = (168, 194, 211)
    cyan = (79, 198, 220)
    cyan2 = (35, 139, 174)
    amber = (232, 176, 83)

    # Nonessential side context: data/trend motifs. These may be cropped on cards.
    for i, h in enumerate([18, 34, 24, 52, 42, 68]):
        x = 18 + i * 17
        draw.rounded_rectangle((x, 230 - h, x + 9, 230), radius=2, fill=(24, 82, 111))
    trend = [(18, 164), (42, 151), (67, 157), (92, 137), (116, 145), (137, 122)]
    draw.line(trend, fill=cyan2, width=3)
    for x, y in trend:
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=cyan)

    # Right-side compact feature labels.
    small = font(11, bold=True)
    for idx, label in enumerate(["ROAD", "WEATHER", "SEVERITY", "TEXT"]):
        y = 91 + idx * 31
        draw.rounded_rectangle((438, y, 540, y + 22), radius=11, outline=(66, 119, 147), width=1)
        centered_text(draw, (489, y + 4), label, small, muted)

    # Center 280x280 crop-safe square is x=140..420. Keep the key subject here.
    # Sensor/radar rings around a top-down vehicle.
    cx, cy = 280, 150
    for radius, alpha_color in [(82, (28, 91, 118)), (64, (35, 117, 146)), (47, (49, 151, 177))]:
        draw.arc((cx - radius, cy - radius, cx + radius, cy + radius), 205, 335, fill=alpha_color, width=2)
        draw.arc((cx - radius, cy - radius, cx + radius, cy + radius), 25, 155, fill=alpha_color, width=2)

    # Lane geometry behind the vehicle.
    draw.polygon([(238, 280), (259, 173), (301, 173), (322, 280)], fill=(16, 42, 61))
    draw.line((260, 280, 273, 176), fill=(131, 166, 184), width=2)
    draw.line((300, 176, 313, 280), fill=(131, 166, 184), width=2)
    for y in range(192, 270, 24):
        draw.rounded_rectangle((277, y, 283, y + 12), radius=2, fill=(219, 230, 235))

    # Simplified top-down sensor vehicle.
    draw.rounded_rectangle((252, 101, 308, 190), radius=17, fill=(224, 236, 241), outline=white, width=2)
    draw.rounded_rectangle((259, 115, 301, 145), radius=8, fill=(38, 78, 99))
    draw.rounded_rectangle((259, 151, 301, 174), radius=7, fill=(30, 62, 80))
    draw.rectangle((247, 119, 253, 139), fill=(67, 98, 113))
    draw.rectangle((307, 119, 313, 139), fill=(67, 98, 113))
    draw.rectangle((247, 154, 253, 175), fill=(67, 98, 113))
    draw.rectangle((307, 154, 313, 175), fill=(67, 98, 113))
    draw.ellipse((273, 90, 287, 104), fill=cyan, outline=white, width=1)

    # Key crop-safe title labels.
    title = font(23, bold=True)
    sub = font(14, bold=True)
    centered_text(draw, (280, 18), "NHTSA SGO", title, white)
    centered_text(draw, (280, 50), "ADS + LEVEL 2 ADAS", sub, cyan)
    centered_text(draw, (280, 216), "CRASH REPORTS", sub, white)
    centered_text(draw, (280, 238), "CURRENT REGIME", small, amber)

    # Tiny provenance words on the full header, intentionally noncritical.
    tiny = font(10)
    draw.text((16, 251), "OFFICIAL PUBLIC DATA", font=tiny, fill=muted)
    right = "VEHICLES · CONDITIONS · NARRATIVES"
    rbox = draw.textbbox((0, 0), right, font=tiny)
    draw.text((544 - (rbox[2] - rbox[0]), 251), right, font=tiny, fill=muted)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT, format="PNG", optimize=True)
    # Exact Kaggle card crop: x=140..420, y=0..280.
    card = image.crop((140, 0, 420, 280))
    card.save(QA_CARD, format="PNG", optimize=True)
    print(f"wrote {OUT} {image.size}")
    print(f"wrote {QA_CARD} {card.size}")


if __name__ == "__main__":
    main()
