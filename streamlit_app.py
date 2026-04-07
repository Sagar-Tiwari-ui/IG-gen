import streamlit as st
import tempfile
import os
import json
import sys
from pathlib import Path

# ── Dependency guard ──────────────────────────────────────────────────────────
def _check_deps():
    errors = []
    try:
        import moviepy.editor  # noqa: F401
    except ModuleNotFoundError:
        try:
            import moviepy  # noqa: F401
            errors.append(
                "**MoviePy v2.x detected** — `moviepy.editor` was removed in v2.\n\n"
                "Fix your `requirements.txt`:\n```\nmoviepy==1.0.3\nimageio==2.25.1\ndecorator==4.4.2\n```\n\n"
                "Then redeploy / restart the app."
            )
        except ModuleNotFoundError:
            errors.append("**MoviePy not found.** Add `moviepy==1.0.3` to `requirements.txt`.")
    try:
        import imageio_ffmpeg  # noqa: F401
    except ModuleNotFoundError:
        errors.append("**imageio-ffmpeg not found.** Add `imageio-ffmpeg==0.4.9` to `requirements.txt`.")
    try:
        from PIL import Image  # noqa: F401
    except ModuleNotFoundError:
        errors.append("**Pillow not found.** Add `Pillow>=10.3.0` to `requirements.txt`.")
    return errors

_dep_errors = _check_deps()

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Reels Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --bg: #0a0a0f;
    --surface: #13131a;
    --surface2: #1c1c27;
    --accent: #ff3b6e;
    --accent2: #ff8c42;
    --text: #f0eeff;
    --muted: #6e6a8a;
    --border: #2a2a3d;
    --success: #2af598;
    --radius: 14px;
}

html, body, [data-testid="stApp"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif;
}

/* Hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* Hero header */
.hero {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    background: radial-gradient(ellipse 80% 60% at 50% -20%, rgba(255,59,110,0.18) 0%, transparent 70%);
}
.hero h1 {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 3rem;
    letter-spacing: -1px;
    background: linear-gradient(135deg, #ff3b6e 0%, #ff8c42 50%, #f0eeff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.3rem;
}
.hero p {
    color: var(--muted);
    font-size: 1.05rem;
    margin: 0;
}

/* Cards */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 1.2rem;
}
.card-title {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--accent);
    margin: 0 0 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Effect row badge */
.effect-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 30px;
    padding: 0.3rem 0.8rem;
    font-size: 0.82rem;
    color: var(--text);
    margin: 0.2rem;
}
.effect-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--accent);
    flex-shrink: 0;
}

/* Watermark preview */
.wm-preview {
    position: relative;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    height: 80px;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding-top: 10px;
    overflow: hidden;
}
.wm-text {
    font-family: 'Syne', sans-serif;
    font-size: 0.9rem;
    letter-spacing: 3px;
    opacity: 0.25;
    color: white;
    text-transform: uppercase;
}

/* Streamlit widget overrides */
[data-testid="stSelectbox"] > div > div,
[data-testid="stTextInput"] > div > div > input,
[data-testid="stNumberInput"] input,
[data-testid="stSlider"] {
    background: var(--surface2) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    border-radius: 10px !important;
}
[data-testid="stSelectbox"] > div > div { color: var(--text) !important; }

div[data-testid="stButton"] > button {
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
div[data-testid="stButton"] > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(255,59,110,0.25) !important;
}
.primary-btn > div > button {
    background: linear-gradient(135deg, #ff3b6e, #ff8c42) !important;
    color: white !important;
    border: none !important;
    padding: 0.6rem 2rem !important;
}
.stProgress > div > div { background: linear-gradient(90deg, #ff3b6e, #ff8c42) !important; }

/* Divider */
.divider { border-top: 1px solid var(--border); margin: 1.2rem 0; }

/* Metric chips */
.metric-row { display: flex; gap: 0.8rem; margin-bottom: 1rem; flex-wrap: wrap; }
.metric-chip {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.4rem 0.9rem;
    font-size: 0.8rem;
    color: var(--muted);
}
.metric-chip span { color: var(--text); font-weight: 600; margin-left: 0.3rem; }

/* Info / warning boxes */
.info-box {
    background: rgba(42,245,152,0.07);
    border: 1px solid rgba(42,245,152,0.25);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    font-size: 0.88rem;
    color: var(--success);
    margin: 0.8rem 0;
}
.warn-box {
    background: rgba(255,140,66,0.08);
    border: 1px solid rgba(255,140,66,0.3);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    font-size: 0.88rem;
    color: var(--accent2);
    margin: 0.8rem 0;
}

label, .stCheckbox span, [data-testid="stMarkdownContainer"] p {
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
if "effects" not in st.session_state:
    st.session_state.effects = []
if "processing" not in st.session_state:
    st.session_state.processing = False
if "output_path" not in st.session_state:
    st.session_state.output_path = None

# ── Effect definitions ────────────────────────────────────────────────────────
EFFECTS_LIBRARY = {
    "🌈 Color & Tone": {
        "Vibrance Boost": "Increases color saturation and warmth — great for lifestyle content",
        "Cinematic Teal-Orange": "Hollywood-style teal shadows + warm highlights",
        "Black & White": "Convert to monochrome with contrast preservation",
        "Faded Film": "Lifts blacks for a vintage, faded look",
        "Neon Glow": "Amplifies bright areas with electric color halos",
        "Duotone": "Two-color gradient overlay (choose colors in settings)",
        "Golden Hour": "Warm amber overlay mimicking sunset light",
        "Cool Matte": "Desaturated cool-toned matte grade",
    },
    "✨ Light & Blur": {
        "Lens Blur (Bokeh)": "Gaussian background blur with in-focus subject center",
        "Motion Blur": "Horizontal smear effect — good for fast cuts",
        "Glitch": "RGB channel offset with scanline artifacts",
        "Vignette": "Darkens edges to draw focus to center",
        "Bloom / Halation": "Glowing soft halo around highlights",
        "Light Leak": "Warm streak overlay as if from a film camera",
        "Lens Flare": "Subtle anamorphic horizontal flare",
    },
    "🎞 Retro & Film": {
        "VHS Tape": "Scan lines, color bleeding, tape noise",
        "Super 8mm": "Grain, flicker, burnt-edge vignette",
        "Analog Grain": "Fine film-like noise overlay",
        "CRT Screen": "Pixel grid + phosphor glow",
        "Lo-Fi Dither": "Reduces to limited color palette with dithering",
    },
    "🌊 Distortion": {
        "Wave Ripple": "Sinusoidal warp across the frame",
        "Zoom Pulse": "Rhythmic in-out zoom (beats per second option)",
        "Mirror / Kaleidoscope": "Symmetry axis mirroring",
        "Fish Eye": "Wide-angle barrel distortion",
        "Prism Shift": "Chromatic aberration with edge fringing",
    },
    "🔤 Text & Overlays": {
        "Subtitle Burn-in": "Adds text at a set timestamp with custom font",
        "Timestamp": "Overlays a clock / date at corner",
        "Lower Third": "News-style name / caption bar at bottom",
        "Sticker Overlay": "PNG sticker placed at coordinates",
    },
    "⚡ Transitions (clip boundary)": {
        "Hard Cut": "No transition — instant switch",
        "Cross Dissolve": "Smooth opacity fade between clips",
        "Whip Pan": "Fast horizontal blur wipe",
        "Zoom In/Out Cut": "Zooms in then cuts on next clip",
        "Flash White": "Brief white frame at cut point",
        "Glitch Transition": "RGB-split stutter at the cut",
    },
}

FLAT_EFFECTS = {}
for cat, effects in EFFECTS_LIBRARY.items():
    for name, desc in effects.items():
        FLAT_EFFECTS[name] = {"category": cat, "description": desc}

EFFECT_NAMES_BY_CAT = {}
for cat, effects in EFFECTS_LIBRARY.items():
    EFFECT_NAMES_BY_CAT[cat] = list(effects.keys())

ALL_EFFECT_NAMES = list(FLAT_EFFECTS.keys())

# ── Helpers ───────────────────────────────────────────────────────────────────
def format_time(seconds):
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"

def get_video_duration(path):
    """Return duration in seconds using moviepy."""
    try:
        from moviepy.editor import VideoFileClip
        with VideoFileClip(path) as clip:
            return clip.duration
    except Exception:
        return None

def apply_effects_and_export(input_path, output_path, effects_list, watermark_text,
                               wm_opacity, wm_font_size, trim_start, trim_end):
    """
    Core processing pipeline using MoviePy + PIL / numpy.
    Returns (success: bool, message: str)
    """
    try:
        import numpy as np
        from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, ColorClip
        from moviepy.video.fx.all import (
            blackwhite, lum_contrast, colorx, crop, fadein, fadeout,
            resize, rotate, even_size
        )

        # ── Universal frame sanitiser ─────────────────────────────────────
        # moviepy fx (blackwhite, colorx, fadein…) can emit float64 frames.
        # PIL / imageio require uint8. Wrap every fl_image call with this.
        def u8(frame):
            """Convert any numeric frame to uint8 [0-255], ensure 3-channel RGB."""
            arr = np.asarray(frame)
            if arr.dtype == np.float64 or arr.dtype == np.float32:
                # float frames from moviepy are in [0, 1] OR [0, 255] — normalise both
                if arr.max() <= 1.0:
                    arr = arr * 255.0
                arr = np.clip(arr, 0, 255)
            arr = arr.astype(np.uint8)
            # Drop alpha channel if present
            if arr.ndim == 3 and arr.shape[2] == 4:
                arr = arr[:, :, :3]
            return arr

        def safe(fn):
            """Wrap an fl_image function so its output is always uint8 RGB."""
            def wrapped(frame):
                return u8(fn(u8(frame)))
            return wrapped

        # Force the raw clip frames to uint8 immediately after load
        clip = VideoFileClip(input_path).subclip(trim_start, trim_end)
        clip = clip.fl_image(u8)
        w, h = clip.size

        # ── Apply each effect ─────────────────────────────────────────────
        for eff in effects_list:
            name = eff["name"]
            t_start = eff["start"]
            t_end   = eff["end"]
            duration = t_end - t_start

            # Color & Tone
            if name == "Black & White":
                clip = blackwhite(clip)
                clip = clip.fl_image(u8)   # blackwhite returns float

            elif name == "Vibrance Boost":
                clip = colorx(clip, 1.4)
                clip = clip.fl_image(u8)   # colorx returns float

            elif name == "Cinematic Teal-Orange":
                def teal_orange(frame):
                    img = frame.astype(np.float32)
                    img[:,:,0] = np.clip(img[:,:,0] * 1.15, 0, 255)
                    img[:,:,2] = np.clip(img[:,:,2] * 0.85, 0, 255)
                    return img.astype(np.uint8)
                clip = clip.fl_image(safe(teal_orange))

            elif name == "Faded Film":
                def faded(frame):
                    return np.clip(frame.astype(np.float32) * 0.85 + 30, 0, 255).astype(np.uint8)
                clip = clip.fl_image(safe(faded))

            elif name == "Golden Hour":
                def golden(frame):
                    img = frame.astype(np.float32)
                    img[:,:,0] = np.clip(img[:,:,0] * 1.2, 0, 255)
                    img[:,:,1] = np.clip(img[:,:,1] * 1.05, 0, 255)
                    img[:,:,2] = np.clip(img[:,:,2] * 0.75, 0, 255)
                    return img.astype(np.uint8)
                clip = clip.fl_image(safe(golden))

            elif name == "Cool Matte":
                def cool(frame):
                    img = frame.astype(np.float32)
                    img[:,:,2] = np.clip(img[:,:,2] * 1.15 + 10, 0, 255)
                    img[:,:,0] = np.clip(img[:,:,0] * 0.88, 0, 255)
                    return np.clip(img * 0.9 + 15, 0, 255).astype(np.uint8)
                clip = clip.fl_image(safe(cool))

            elif name == "Neon Glow":
                def neon_glow(frame):
                    from PIL import Image, ImageFilter, ImageChops
                    img = Image.fromarray(frame)
                    glow = img.filter(ImageFilter.GaussianBlur(radius=8))
                    result = ImageChops.add(img, glow, scale=1.5, offset=0)
                    return np.array(result).astype(np.uint8)
                clip = clip.fl_image(safe(neon_glow))

            elif name == "Duotone":
                def duotone(frame):
                    gray = np.mean(frame, axis=2, keepdims=True)
                    color1 = np.array([255, 60, 110], dtype=np.float32)
                    color2 = np.array([30, 20, 80],  dtype=np.float32)
                    t = gray / 255.0
                    result = (1 - t) * color2 + t * color1
                    return np.clip(result, 0, 255).astype(np.uint8)
                clip = clip.fl_image(safe(duotone))

            # Blur
            elif name == "Lens Blur (Bokeh)":
                def bokeh(frame):
                    from PIL import Image, ImageFilter, ImageDraw
                    img = Image.fromarray(frame)
                    blurred = img.filter(ImageFilter.GaussianBlur(radius=6))
                    mask = Image.new("L", img.size, 0)
                    draw = ImageDraw.Draw(mask)
                    cx, cy = img.size[0]//2, img.size[1]//2
                    r = min(cx, cy) // 2
                    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=255)
                    mask = mask.filter(ImageFilter.GaussianBlur(radius=40))
                    result = Image.composite(img, blurred, mask)
                    return np.array(result).astype(np.uint8)
                clip = clip.fl_image(safe(bokeh))

            elif name == "Motion Blur":
                def motion_blur(frame):
                    from PIL import Image, ImageFilter
                    img = Image.fromarray(frame)
                    return np.array(img.filter(ImageFilter.SMOOTH_MORE)).astype(np.uint8)
                clip = clip.fl_image(safe(motion_blur))

            elif name == "Vignette":
                def vignette(frame):
                    rows, cols = frame.shape[:2]
                    X, Y = np.meshgrid(np.linspace(-1, 1, cols), np.linspace(-1, 1, rows))
                    mask = 1 - np.clip(X**2 + Y**2, 0, 1) ** 0.6
                    return np.clip(frame * mask[:,:,np.newaxis], 0, 255).astype(np.uint8)
                clip = clip.fl_image(safe(vignette))

            elif name == "Bloom / Halation":
                def bloom(frame):
                    from PIL import Image, ImageFilter, ImageChops
                    img = Image.fromarray(frame)
                    bright = img.point(lambda p: p * 1.5)
                    glow = bright.filter(ImageFilter.GaussianBlur(radius=12))
                    result = ImageChops.screen(img, glow)
                    return np.array(result).astype(np.uint8)
                clip = clip.fl_image(safe(bloom))

            elif name == "Light Leak":
                def light_leak(frame):
                    h, w = frame.shape[:2]
                    leak = np.zeros_like(frame, dtype=np.float32)
                    leak[:, :w//3, 0] = 80
                    leak[:, :w//3, 1] = 40
                    result = np.clip(frame.astype(np.float32) + leak, 0, 255)
                    return result.astype(np.uint8)
                clip = clip.fl_image(safe(light_leak))

            elif name == "Lens Flare":
                def lens_flare(frame):
                    h, w = frame.shape[:2]
                    result = frame.astype(np.float32).copy()
                    cy = h // 2
                    streak = np.zeros((h, w, 3), dtype=np.float32)
                    streak[cy-2:cy+2, :, :] = [120, 100, 60]
                    result = np.clip(result + streak * 0.4, 0, 255)
                    return result.astype(np.uint8)
                clip = clip.fl_image(safe(lens_flare))

            # Retro
            elif name == "Analog Grain":
                def grain(frame):
                    noise = np.random.randint(-18, 18, frame.shape, dtype=np.int16)
                    return np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
                clip = clip.fl_image(safe(grain))

            elif name == "VHS Tape":
                def vhs(frame):
                    f = frame.copy()
                    f[::2, :, :] = np.clip(f[::2, :, :].astype(np.int16) - 20, 0, 255).astype(np.uint8)
                    r = f[:,:,0].copy()
                    f[:,2:,0] = r[:,:-2]
                    noise = np.random.randint(-8, 8, f.shape, dtype=np.int16)
                    return np.clip(f.astype(np.int16) + noise, 0, 255).astype(np.uint8)
                clip = clip.fl_image(safe(vhs))

            elif name == "Super 8mm":
                def super8(frame):
                    noise = np.random.randint(-25, 25, frame.shape, dtype=np.int16)
                    f = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
                    rows, cols = f.shape[:2]
                    X, Y = np.meshgrid(np.linspace(-1, 1, cols), np.linspace(-1, 1, rows))
                    vign = 1 - np.clip((X**2 + Y**2) * 1.2, 0, 1)
                    return np.clip(f * vign[:,:,np.newaxis], 0, 255).astype(np.uint8)
                clip = clip.fl_image(safe(super8))

            elif name == "CRT Screen":
                def crt(frame):
                    f = frame.copy()
                    f[::3, :, :] = np.clip(f[::3, :, :].astype(np.int16) - 40, 0, 255).astype(np.uint8)
                    return f
                clip = clip.fl_image(safe(crt))

            elif name == "Lo-Fi Dither":
                def lofi(frame):
                    reduced = (frame // 64) * 64
                    return reduced.astype(np.uint8)
                clip = clip.fl_image(safe(lofi))

            # Distortion
            elif name == "Prism Shift":
                def prism(frame):
                    result = frame.copy().astype(np.uint8)
                    shift = 5
                    result[:, shift:, 0] = frame[:, :-shift, 0]
                    result[:, :-shift, 2] = frame[:, shift:, 2]
                    return result
                clip = clip.fl_image(safe(prism))

            elif name == "Glitch":
                def glitch(frame):
                    result = frame.copy()
                    num_glitch = np.random.randint(3, 8)
                    fh = frame.shape[0]
                    for _ in range(num_glitch):
                        y = np.random.randint(0, max(1, fh - 10))
                        ht = np.random.randint(2, 10)
                        shift = np.random.randint(-20, 20)
                        result[y:y+ht, :, :] = np.roll(result[y:y+ht, :, :], shift, axis=1)
                    return result.astype(np.uint8)
                clip = clip.fl_image(safe(glitch))

            elif name == "Fish Eye":
                def fisheye(frame):
                    from PIL import Image
                    img = Image.fromarray(frame)
                    w2, h2 = img.size
                    # Simple barrel distortion via resize trick
                    inner = img.resize((int(w2*0.85), int(h2*0.85)), Image.LANCZOS)
                    canvas = Image.new("RGB", (w2, h2), (0,0,0))
                    ox = (w2 - inner.width) // 2
                    oy = (h2 - inner.height) // 2
                    canvas.paste(inner, (ox, oy))
                    return np.array(canvas).astype(np.uint8)
                clip = clip.fl_image(safe(fisheye))

            elif name == "Mirror / Kaleidoscope":
                def mirror(frame):
                    half = frame[:, :frame.shape[1]//2, :]
                    return np.concatenate([half, half[:, ::-1, :]], axis=1).astype(np.uint8)
                clip = clip.fl_image(safe(mirror))

            elif name == "Wave Ripple":
                def wave(frame):
                    from PIL import Image
                    img = Image.fromarray(frame)
                    w2, h2 = img.size
                    result = np.array(img).copy()
                    for row in range(h2):
                        shift = int(8 * np.sin(2 * np.pi * row / 30))
                        result[row] = np.roll(frame[row], shift, axis=0)
                    return result.astype(np.uint8)
                clip = clip.fl_image(safe(wave))

            # Transitions
            elif name == "Cross Dissolve":
                clip = fadein(clip, duration=min(0.5, duration / 2))
                clip = fadeout(clip, duration=min(0.5, duration / 2))
                clip = clip.fl_image(u8)

            elif name == "Flash White":
                def flash(get_frame, t):
                    frame = u8(get_frame(t))
                    if t < 0.1:
                        alpha = 1 - t / 0.1
                        frame = np.clip(frame.astype(np.float32) + alpha * 255, 0, 255).astype(np.uint8)
                    return frame
                clip = clip.fl(flash)

            elif name == "Zoom In/Out Cut":
                def zoom_pulse(get_frame, t):
                    frame = u8(get_frame(t))
                    scale = 1.0 + 0.05 * np.sin(2 * np.pi * t / max(duration, 0.1))
                    from PIL import Image
                    img = Image.fromarray(frame)
                    w2, h2 = img.size
                    nw, nh = int(w2 * scale), int(h2 * scale)
                    resized = img.resize((nw, nh), Image.LANCZOS)
                    ox, oy = (nw - w2) // 2, (nh - h2) // 2
                    cropped = resized.crop((ox, oy, ox + w2, oy + h2))
                    return np.array(cropped).astype(np.uint8)
                clip = clip.fl(zoom_pulse)

            # Subtitle burn-in
            elif name == "Subtitle Burn-in":
                subtitle_text = eff.get("subtitle_text", "Sample subtitle")
                sub_op = wm_opacity / 100.0
                def sub_frame(frame):
                    from PIL import Image, ImageDraw, ImageFont
                    frame = u8(frame)
                    img = Image.fromarray(frame).convert("RGBA")
                    overlay = Image.new("RGBA", img.size, (0,0,0,0))
                    draw = ImageDraw.Draw(overlay)
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                    except Exception:
                        font = ImageFont.load_default()
                    bbox = draw.textbbox((0,0), subtitle_text, font=font)
                    tw = bbox[2] - bbox[0]
                    x = (img.width - tw) // 2
                    y = img.height - 70
                    # Shadow
                    draw.text((x+2, y+2), subtitle_text, font=font, fill=(0,0,0,180))
                    draw.text((x, y), subtitle_text, font=font, fill=(255,255,255,230))
                    combined = Image.alpha_composite(img, overlay).convert("RGB")
                    return np.array(combined).astype(np.uint8)
                clip = clip.fl_image(safe(sub_frame))

        # ── Watermark ─────────────────────────────────────────────────────────
        if watermark_text.strip():
            wm = watermark_text
            op = wm_opacity / 100.0
            fs = wm_font_size
            def wm_frame(frame):
                from PIL import Image, ImageDraw, ImageFont
                frame = u8(frame)
                img = Image.fromarray(frame).convert("RGBA")
                overlay = Image.new("RGBA", img.size, (0,0,0,0))
                draw = ImageDraw.Draw(overlay)
                font = None
                for font_path in [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
                ]:
                    try:
                        font = ImageFont.truetype(font_path, fs)
                        break
                    except Exception:
                        continue
                if font is None:
                    font = ImageFont.load_default()
                bbox = draw.textbbox((0,0), wm, font=font)
                tw = bbox[2] - bbox[0]
                x = (img.width - tw) // 2
                y = int(img.height * 0.03)
                draw.text((x, y), wm, font=font, fill=(255, 255, 255, int(255 * op)))
                combined = Image.alpha_composite(img, overlay).convert("RGB")
                return np.array(combined).astype(np.uint8)
            clip = clip.fl_image(safe(wm_frame))

        # ── Final uint8 pass + export ─────────────────────────────────────
        clip = clip.fl_image(u8)   # belt-and-braces: ensure uint8 going into encoder
        clip = even_size(clip)
        clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=output_path + "_tmp_audio.m4a",
            remove_temp=True,
            logger=None,
            preset="ultrafast",
            ffmpeg_params=["-crf", "23", "-pix_fmt", "yuv420p"],
        )
        clip.close()
        return True, "Export successful"
    except Exception as e:
        import traceback
        return False, f"{e}\n\n{traceback.format_exc()}"


# ══════════════════════════════════════════════════════════════════════════════
#  UI
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="hero">
  <h1>🎬 Reels Studio</h1>
  <p>Professional Instagram Reels editor — effects, grades &amp; watermarks in seconds</p>
</div>
""", unsafe_allow_html=True)

# Show dependency errors and stop early
if _dep_errors:
    for err in _dep_errors:
        st.error(err)
    st.warning(
        "⚠️ Fix `requirements.txt`, commit the change, then open the Streamlit Cloud dashboard "
        "→ your app → **⋮ menu → Reboot app**."
    )
    st.code(
        "# Correct requirements.txt (key pins)\nmoviepy==1.0.3\nimageio==2.25.1\ndecorator==4.4.2\nimageio-ffmpeg==0.4.9",
        language="text",
    )
    st.stop()

# ── Upload ────────────────────────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-title">📁 Upload Video</div>', unsafe_allow_html=True)
uploaded = st.file_uploader(
    "Drop your reel here (MP4 / MOV / AVI · max 1 minute)",
    type=["mp4", "mov", "avi", "mkv"],
    label_visibility="collapsed",
)
st.markdown('</div>', unsafe_allow_html=True)

video_duration = None
tmp_input_path = None

if uploaded:
    # Save to temp file
    suffix = Path(uploaded.name).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded.read())
    tmp.flush()
    tmp_input_path = tmp.name

    video_duration = get_video_duration(tmp_input_path)

    col_prev, col_info = st.columns([1, 1])
    with col_prev:
        st.video(tmp_input_path)
    with col_info:
        if video_duration:
            if video_duration > 60:
                st.markdown(f'<div class="warn-box">⚠️ Video is {video_duration:.1f}s — over the 60s limit. It will be trimmed.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="info-box">✅ Video loaded — {video_duration:.1f}s · ready to edit</div>', unsafe_allow_html=True)
            st.markdown(f"""
<div class="metric-row">
  <div class="metric-chip">Duration<span>{format_time(video_duration)}</span></div>
  <div class="metric-chip">File<span>{uploaded.name}</span></div>
  <div class="metric-chip">Size<span>{uploaded.size / 1e6:.1f} MB</span></div>
</div>""", unsafe_allow_html=True)
        else:
            st.info("Upload a supported video file to begin.")

# ── Trim ──────────────────────────────────────────────────────────────────────
trim_start = 0.0
trim_end = 60.0

if video_duration:
    max_dur = min(video_duration, 60.0)
    st.markdown('<div class="card"><div class="card-title">✂️ Trim Clip</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        trim_start = st.slider("Start (seconds)", 0.0, float(max_dur - 0.5), 0.0, 0.1, format="%.1fs")
    with c2:
        trim_end = st.slider("End (seconds)", float(trim_start + 0.5), float(max_dur), float(max_dur), 0.1, format="%.1fs")
    st.markdown(f'<div class="info-box">📐 Selected clip: <b>{format_time(trim_start)}</b> → <b>{format_time(trim_end)}</b> &nbsp;·&nbsp; Duration: <b>{trim_end-trim_start:.1f}s</b></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Effects builder ───────────────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-title">✨ Effects Timeline</div>', unsafe_allow_html=True)

if not uploaded:
    st.markdown('<p style="color:#6e6a8a;font-size:0.9rem;">Upload a video first to add effects.</p>', unsafe_allow_html=True)
else:
    clip_duration = trim_end - trim_start if video_duration else 60.0

    # Show existing effects
    if st.session_state.effects:
        st.markdown("**Added effects:**")
        for i, eff in enumerate(st.session_state.effects):
            cols = st.columns([3, 2, 2, 1])
            with cols[0]:
                st.markdown(f'<div class="effect-badge"><span class="effect-dot"></span>{eff["name"]}</div>', unsafe_allow_html=True)
            with cols[1]:
                st.caption(f"⏱ {format_time(eff['start'])} → {format_time(eff['end'])}")
            with cols[2]:
                if eff["name"] == "Subtitle Burn-in":
                    st.caption(f'💬 "{eff.get("subtitle_text","")}"')
            with cols[3]:
                if st.button("✕", key=f"del_eff_{i}", help="Remove this effect"):
                    st.session_state.effects.pop(i)
                    st.rerun()
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Add new effect form
    st.markdown("**Add effect:**")
    ae1, ae2, ae3 = st.columns([2, 1.5, 1.5])
    with ae1:
        cat = st.selectbox("Category", list(EFFECTS_LIBRARY.keys()), key="new_cat", label_visibility="collapsed")
        eff_name = st.selectbox("Effect", EFFECT_NAMES_BY_CAT[cat], key="new_eff", label_visibility="collapsed")
        if eff_name in FLAT_EFFECTS:
            st.caption(f"ℹ️ {FLAT_EFFECTS[eff_name]['description']}")
    with ae2:
        new_start = st.number_input("Start (s)", 0.0, float(clip_duration), 0.0, 0.1, key="new_start")
    with ae3:
        new_end = st.number_input("End (s)", float(new_start), float(clip_duration), float(clip_duration), 0.1, key="new_end")

    subtitle_text_val = ""
    if eff_name == "Subtitle Burn-in":
        subtitle_text_val = st.text_input("Subtitle text", "Type your subtitle here…", key="sub_text")

    if st.button("＋ Add Effect to Timeline", use_container_width=True):
        entry = {"name": eff_name, "start": new_start, "end": new_end}
        if eff_name == "Subtitle Burn-in":
            entry["subtitle_text"] = subtitle_text_val
        st.session_state.effects.append(entry)
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ── Watermark ─────────────────────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-title">🔏 Watermark</div>', unsafe_allow_html=True)

wm_col1, wm_col2, wm_col3 = st.columns([3, 1.5, 1.5])
with wm_col1:
    watermark_text = st.text_input("Watermark text", placeholder="@yourhandle  or  YourBrand™", key="wm_text", label_visibility="collapsed")
with wm_col2:
    wm_opacity = st.slider("Opacity", 5, 50, 20, 1, key="wm_op", format="%d%%")
with wm_col3:
    wm_font_size = st.slider("Font size", 16, 72, 32, 2, key="wm_fs", format="%dpx")

# Live preview strip
if watermark_text.strip():
    st.markdown(f"""
<div class="wm-preview">
  <span class="wm-text" style="opacity:{wm_opacity/100}; font-size:{wm_font_size}px">{watermark_text}</span>
</div>
<p style="font-size:0.78rem;color:#6e6a8a;margin-top:0.4rem;">↑ Preview: watermark appears at top-center, transparent over your video</p>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Export ────────────────────────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-title">🚀 Export</div>', unsafe_allow_html=True)

exp_col1, exp_col2 = st.columns([2, 1])
with exp_col1:
    output_filename = st.text_input("Output filename", value="reel_edited.mp4", key="out_name")
with exp_col2:
    st.markdown("<br>", unsafe_allow_html=True)
    export_ready = uploaded is not None

if export_ready:
    st.markdown(f"""
<div class="metric-row">
  <div class="metric-chip">Effects<span>{len(st.session_state.effects)}</span></div>
  <div class="metric-chip">Watermark<span>{"✓" if watermark_text.strip() else "—"}</span></div>
  <div class="metric-chip">Trim<span>{format_time(trim_start)} → {format_time(trim_end)}</span></div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
    if st.button("🎬 Render & Export Reel", use_container_width=True, disabled=st.session_state.processing):
        st.session_state.processing = True
        st.session_state.output_path = None

        with st.spinner("Rendering your reel… this may take a moment 🎞"):
            progress = st.progress(0, text="Initialising pipeline…")
            import time

            progress.progress(15, text="Loading video clip…")
            time.sleep(0.3)

            out_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            out_tmp.close()

            progress.progress(35, text="Applying effects…")
            success, msg = apply_effects_and_export(
                input_path=tmp_input_path,
                output_path=out_tmp.name,
                effects_list=st.session_state.effects,
                watermark_text=watermark_text,
                wm_opacity=wm_opacity,
                wm_font_size=wm_font_size,
                trim_start=trim_start,
                trim_end=trim_end,
            )
            progress.progress(90, text="Encoding final file…")
            time.sleep(0.3)
            progress.progress(100, text="Done!")

        st.session_state.processing = False

        if success:
            with open(out_tmp.name, "rb") as f:
                video_bytes = f.read()
            st.session_state.output_path = out_tmp.name
            st.success("✅ Reel exported successfully!")
            st.video(out_tmp.name)
            st.download_button(
                label="⬇️ Download Reel",
                data=video_bytes,
                file_name=output_filename,
                mime="video/mp4",
                use_container_width=True,
            )
        else:
            st.error(f"❌ Export failed: {msg}")
            st.info("Tip: Make sure all dependencies in requirements.txt are installed.")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown('<p style="color:#6e6a8a">Upload a video to enable export.</p>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<hr style="border-color:#2a2a3d;margin-top:2rem"/>
<p style="text-align:center;color:#3a3a55;font-size:0.78rem;padding-bottom:1rem">
  Reels Studio · Built with Streamlit & MoviePy · Max clip duration 60 s
</p>
""", unsafe_allow_html=True)
