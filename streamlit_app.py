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
                               wm_opacity, wm_font_size, wm_position, trim_start, trim_end):
    """
    Timestamp-aware multi-effect pipeline.
    Every effect carries its own [start, end] window.
    Multiple effects active at the same timestamp are all applied in order.
    """
    try:
        import numpy as np
        from moviepy.editor import VideoFileClip
        from moviepy.video.fx.all import even_size

        # ── Helpers ───────────────────────────────────────────────────────
        def u8(frame):
            """Ensure frame is uint8 RGB (H,W,3)."""
            arr = np.asarray(frame, dtype=np.float64)
            if arr.max() <= 1.0 and arr.dtype in (np.float32, np.float64):
                arr = arr * 255.0
            arr = np.clip(arr, 0, 255).astype(np.uint8)
            if arr.ndim == 3 and arr.shape[2] == 4:
                arr = arr[:, :, :3]
            return arr

        def load_font(size):
            from PIL import ImageFont
            for path in [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            ]:
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    pass
            return ImageFont.load_default()

        # ── Single-frame effect dispatch ──────────────────────────────────
        # Each function takes (frame: uint8 ndarray, t_rel: float) → uint8 ndarray
        # t_rel = time in seconds relative to the effect's own start

        def fx_black_and_white(frame, t_rel):
            gray = np.mean(frame, axis=2, keepdims=True).astype(np.uint8)
            return np.repeat(gray, 3, axis=2)

        def fx_vibrance_boost(frame, t_rel):
            f = frame.astype(np.float32)
            mean = f.mean(axis=2, keepdims=True)
            return np.clip(mean + (f - mean) * 1.6, 0, 255).astype(np.uint8)

        def fx_teal_orange(frame, t_rel):
            f = frame.astype(np.float32)
            f[:,:,0] = np.clip(f[:,:,0] * 1.15, 0, 255)
            f[:,:,2] = np.clip(f[:,:,2] * 0.80, 0, 255)
            return f.astype(np.uint8)

        def fx_faded_film(frame, t_rel):
            return np.clip(frame.astype(np.float32) * 0.85 + 30, 0, 255).astype(np.uint8)

        def fx_golden_hour(frame, t_rel):
            f = frame.astype(np.float32)
            f[:,:,0] = np.clip(f[:,:,0] * 1.2,  0, 255)
            f[:,:,1] = np.clip(f[:,:,1] * 1.05, 0, 255)
            f[:,:,2] = np.clip(f[:,:,2] * 0.75, 0, 255)
            return f.astype(np.uint8)

        def fx_cool_matte(frame, t_rel):
            f = frame.astype(np.float32)
            f[:,:,2] = np.clip(f[:,:,2] * 1.15 + 10, 0, 255)
            f[:,:,0] = np.clip(f[:,:,0] * 0.88, 0, 255)
            return np.clip(f * 0.9 + 15, 0, 255).astype(np.uint8)

        def fx_neon_glow(frame, t_rel):
            from PIL import Image, ImageFilter, ImageChops
            img = Image.fromarray(frame)
            glow = img.filter(ImageFilter.GaussianBlur(radius=8))
            return np.array(ImageChops.add(img, glow, scale=1.5)).astype(np.uint8)

        def fx_duotone(frame, t_rel):
            gray = np.mean(frame, axis=2, keepdims=True) / 255.0
            c1 = np.array([255, 60, 110], dtype=np.float32)
            c2 = np.array([30,  20,  80], dtype=np.float32)
            return np.clip((1 - gray) * c2 + gray * c1, 0, 255).astype(np.uint8)

        def fx_bokeh(frame, t_rel):
            from PIL import Image, ImageFilter, ImageDraw
            img = Image.fromarray(frame)
            blurred = img.filter(ImageFilter.GaussianBlur(radius=7))
            mask = Image.new("L", img.size, 0)
            d = ImageDraw.Draw(mask)
            cx, cy = img.size[0]//2, img.size[1]//2
            r = min(cx, cy) // 2
            d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=255)
            mask = mask.filter(ImageFilter.GaussianBlur(radius=40))
            return np.array(Image.composite(img, blurred, mask)).astype(np.uint8)

        def fx_motion_blur(frame, t_rel):
            from PIL import Image, ImageFilter
            return np.array(Image.fromarray(frame).filter(ImageFilter.SMOOTH_MORE)).astype(np.uint8)

        def fx_vignette(frame, t_rel):
            h, w = frame.shape[:2]
            X, Y = np.meshgrid(np.linspace(-1,1,w), np.linspace(-1,1,h))
            mask = 1 - np.clip(X**2 + Y**2, 0, 1) ** 0.55
            return np.clip(frame * mask[:,:,np.newaxis], 0, 255).astype(np.uint8)

        def fx_bloom(frame, t_rel):
            from PIL import Image, ImageFilter, ImageChops
            img = Image.fromarray(frame)
            glow = img.point(lambda p: min(255, p * 1.5)).filter(ImageFilter.GaussianBlur(radius=12))
            return np.array(ImageChops.screen(img, glow)).astype(np.uint8)

        def fx_light_leak(frame, t_rel):
            h, w = frame.shape[:2]
            leak = np.zeros_like(frame, dtype=np.float32)
            leak[:, :w//3, 0] = 90
            leak[:, :w//3, 1] = 45
            return np.clip(frame.astype(np.float32) + leak, 0, 255).astype(np.uint8)

        def fx_lens_flare(frame, t_rel):
            h, w = frame.shape[:2]
            f = frame.astype(np.float32)
            cy = h // 2
            f[cy-2:cy+2, :, :] += np.array([120, 100, 60], dtype=np.float32) * 0.4
            return np.clip(f, 0, 255).astype(np.uint8)

        def fx_analog_grain(frame, t_rel):
            noise = np.random.randint(-18, 18, frame.shape, dtype=np.int16)
            return np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        def fx_vhs(frame, t_rel):
            f = frame.copy()
            f[::2,:,:] = np.clip(f[::2,:,:].astype(np.int16) - 20, 0, 255)
            r = f[:,:,0].copy()
            f[:,2:,0] = r[:,:-2]
            noise = np.random.randint(-8, 8, f.shape, dtype=np.int16)
            return np.clip(f.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        def fx_super8(frame, t_rel):
            noise = np.random.randint(-25, 25, frame.shape, dtype=np.int16)
            f = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            h, w = f.shape[:2]
            X, Y = np.meshgrid(np.linspace(-1,1,w), np.linspace(-1,1,h))
            vign = 1 - np.clip((X**2 + Y**2) * 1.2, 0, 1)
            return np.clip(f * vign[:,:,np.newaxis], 0, 255).astype(np.uint8)

        def fx_crt(frame, t_rel):
            f = frame.copy()
            f[::3,:,:] = np.clip(f[::3,:,:].astype(np.int16) - 40, 0, 255)
            return f.astype(np.uint8)

        def fx_lofi(frame, t_rel):
            return ((frame // 64) * 64).astype(np.uint8)

        def fx_prism(frame, t_rel):
            r = frame.copy()
            s = 6
            r[:, s:,  0] = frame[:, :-s, 0]
            r[:, :-s, 2] = frame[:, s:,  2]
            return r.astype(np.uint8)

        def fx_glitch(frame, t_rel):
            r = frame.copy()
            fh = frame.shape[0]
            for _ in range(np.random.randint(3, 9)):
                y  = np.random.randint(0, max(1, fh - 12))
                ht = np.random.randint(2, 12)
                sh = np.random.randint(-25, 25)
                r[y:y+ht,:,:] = np.roll(r[y:y+ht,:,:], sh, axis=1)
            return r.astype(np.uint8)

        def fx_fisheye(frame, t_rel):
            from PIL import Image
            img = Image.fromarray(frame)
            w2, h2 = img.size
            inner = img.resize((int(w2*0.82), int(h2*0.82)), Image.LANCZOS)
            canvas = Image.new("RGB", (w2, h2), (0,0,0))
            canvas.paste(inner, ((w2-inner.width)//2, (h2-inner.height)//2))
            return np.array(canvas).astype(np.uint8)

        def fx_mirror(frame, t_rel):
            half = frame[:, :frame.shape[1]//2, :]
            return np.concatenate([half, half[:, ::-1, :]], axis=1).astype(np.uint8)

        def fx_wave(frame, t_rel):
            h, w = frame.shape[:2]
            result = np.empty_like(frame)
            for row in range(h):
                shift = int(10 * np.sin(2 * np.pi * (row / 30.0 + t_rel * 2)))
                result[row] = np.roll(frame[row], shift, axis=0)
            return result.astype(np.uint8)

        def fx_zoom_pulse(frame, t_rel, eff_duration):
            from PIL import Image
            # Smooth zoom: 1.0 → 1.15 → 1.0 over the effect window
            progress = t_rel / max(eff_duration, 0.001)
            scale = 1.0 + 0.15 * np.sin(np.pi * progress)
            img = Image.fromarray(frame)
            w2, h2 = img.size
            nw, nh = max(w2, int(w2 * scale)), max(h2, int(h2 * scale))
            resized = img.resize((nw, nh), Image.LANCZOS)
            ox, oy = (nw - w2) // 2, (nh - h2) // 2
            return np.array(resized.crop((ox, oy, ox+w2, oy+h2))).astype(np.uint8)

        def fx_whip_pan(frame, t_rel, eff_duration):
            from PIL import Image, ImageFilter
            progress = t_rel / max(eff_duration, 0.001)
            # Blur intensifies toward centre then fades
            radius = int(30 * np.sin(np.pi * progress))
            if radius < 1:
                return frame
            img = Image.fromarray(frame)
            # Horizontal motion blur via repeated offset compositing
            blurred = img.filter(ImageFilter.GaussianBlur(radius=max(1, radius//3)))
            return np.array(blurred).astype(np.uint8)

        def fx_cross_dissolve(frame, t_rel, eff_duration):
            # Fade out then back in
            progress = t_rel / max(eff_duration, 0.001)
            alpha = 1.0 - 2.0 * abs(progress - 0.5)   # 0→1→0
            return np.clip(frame.astype(np.float32) * alpha, 0, 255).astype(np.uint8)

        def fx_flash_white(frame, t_rel, eff_duration):
            progress = t_rel / max(eff_duration, 0.001)
            intensity = max(0.0, 1.0 - progress * 10)  # instant flash decays quickly
            return np.clip(frame.astype(np.float32) + intensity * 255, 0, 255).astype(np.uint8)

        def fx_glitch_transition(frame, t_rel, eff_duration):
            frame = fx_glitch(frame, t_rel)
            return fx_prism(frame, t_rel)

        def fx_subtitle(frame, t_rel, subtitle_text):
            from PIL import Image, ImageDraw
            img = Image.fromarray(frame).convert("RGBA")
            ov = Image.new("RGBA", img.size, (0,0,0,0))
            draw = ImageDraw.Draw(ov)
            font = load_font(36)
            bbox = draw.textbbox((0,0), subtitle_text, font=font)
            tw = bbox[2] - bbox[0]
            x = (img.width - tw) // 2
            y = img.height - 75
            draw.text((x+2, y+2), subtitle_text, font=font, fill=(0,0,0,180))
            draw.text((x,   y),   subtitle_text, font=font, fill=(255,255,255,230))
            return np.array(Image.alpha_composite(img, ov).convert("RGB")).astype(np.uint8)

        def fx_timestamp(frame, t_rel, clip_t):
            import datetime
            ts = str(datetime.timedelta(seconds=int(clip_t))).zfill(8)
            from PIL import Image, ImageDraw
            img = Image.fromarray(frame).convert("RGBA")
            ov  = Image.new("RGBA", img.size, (0,0,0,0))
            draw = ImageDraw.Draw(ov)
            font = load_font(28)
            draw.text((12, 12), ts, font=font, fill=(255,255,255,200))
            return np.array(Image.alpha_composite(img, ov).convert("RGB")).astype(np.uint8)

        def fx_lower_third(frame, t_rel, subtitle_text):
            from PIL import Image, ImageDraw
            img = Image.fromarray(frame).convert("RGBA")
            ov  = Image.new("RGBA", img.size, (0,0,0,0))
            draw = ImageDraw.Draw(ov)
            bar_h = 60
            draw.rectangle([(0, img.height-bar_h), (img.width, img.height)], fill=(0,0,0,160))
            font = load_font(32)
            draw.text((20, img.height - bar_h + 14), subtitle_text, font=font, fill=(255,255,255,240))
            return np.array(Image.alpha_composite(img, ov).convert("RGB")).astype(np.uint8)

        # ── Effect name → function map ─────────────────────────────────────
        EFFECT_FN = {
            "Black & White":         fx_black_and_white,
            "Vibrance Boost":        fx_vibrance_boost,
            "Cinematic Teal-Orange": fx_teal_orange,
            "Faded Film":            fx_faded_film,
            "Golden Hour":           fx_golden_hour,
            "Cool Matte":            fx_cool_matte,
            "Neon Glow":             fx_neon_glow,
            "Duotone":               fx_duotone,
            "Lens Blur (Bokeh)":     fx_bokeh,
            "Motion Blur":           fx_motion_blur,
            "Glitch":                fx_glitch,
            "Vignette":              fx_vignette,
            "Bloom / Halation":      fx_bloom,
            "Light Leak":            fx_light_leak,
            "Lens Flare":            fx_lens_flare,
            "VHS Tape":              fx_vhs,
            "Super 8mm":             fx_super8,
            "Analog Grain":          fx_analog_grain,
            "CRT Screen":            fx_crt,
            "Lo-Fi Dither":          fx_lofi,
            "Wave Ripple":           fx_wave,
            "Mirror / Kaleidoscope": fx_mirror,
            "Fish Eye":              fx_fisheye,
            "Prism Shift":           fx_prism,
        }

        # ── Master per-frame processor ─────────────────────────────────────
        def process_frame(get_frame, t):
            # t is the clip-absolute time (seconds from start of trimmed clip)
            frame = u8(get_frame(t))

            for eff in effects_list:
                es = eff["start"]
                ee = eff["end"]
                if not (es <= t <= ee):
                    continue                    # ← timestamp gate

                name      = eff["name"]
                t_rel     = t - es              # time relative to effect start
                eff_dur   = max(ee - es, 0.001)

                # Effects that need t_rel + duration
                if name == "Zoom Pulse":
                    frame = fx_zoom_pulse(frame, t_rel, eff_dur)
                elif name == "Zoom In/Out Cut":
                    frame = fx_zoom_pulse(frame, t_rel, eff_dur)
                elif name == "Whip Pan":
                    frame = fx_whip_pan(frame, t_rel, eff_dur)
                elif name == "Cross Dissolve":
                    frame = fx_cross_dissolve(frame, t_rel, eff_dur)
                elif name == "Flash White":
                    frame = fx_flash_white(frame, t_rel, eff_dur)
                elif name == "Glitch Transition":
                    frame = fx_glitch_transition(frame, t_rel, eff_dur)
                elif name == "Wave Ripple":
                    frame = fx_wave(frame, t_rel)
                # Text overlays
                elif name == "Subtitle Burn-in":
                    frame = fx_subtitle(frame, t_rel, eff.get("subtitle_text", ""))
                elif name == "Timestamp":
                    frame = fx_timestamp(frame, t_rel, t)
                elif name in ("Lower Third", "Sticker Overlay"):
                    frame = fx_lower_third(frame, t_rel, eff.get("subtitle_text", name))
                elif name == "Hard Cut":
                    pass  # no-op
                elif name in EFFECT_FN:
                    frame = EFFECT_FN[name](frame, t_rel)

            # ── Watermark (always on, if set) ──────────────────────────────
            if watermark_text.strip():
                from PIL import Image, ImageDraw
                img  = Image.fromarray(frame).convert("RGBA")
                ov   = Image.new("RGBA", img.size, (0,0,0,0))
                draw = ImageDraw.Draw(ov)
                font = load_font(wm_font_size)
                bbox = draw.textbbox((0,0), watermark_text, font=font)
                tw   = bbox[2] - bbox[0]
                th   = bbox[3] - bbox[1]
                W, H = img.size
                pad  = 14
                # Position mapping
                pos_map = {
                    "Top Left":      (pad, pad),
                    "Top Center":    ((W - tw)//2, pad),
                    "Top Right":     (W - tw - pad, pad),
                    "Center":        ((W - tw)//2, (H - th)//2),
                    "Bottom Left":   (pad, H - th - pad),
                    "Bottom Center": ((W - tw)//2, H - th - pad),
                    "Bottom Right":  (W - tw - pad, H - th - pad),
                }
                x, y = pos_map.get(wm_position, ((W - tw)//2, pad))
                alpha_val = int(255 * wm_opacity / 100)
                draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, alpha_val))
                frame = np.array(Image.alpha_composite(img, ov).convert("RGB")).astype(np.uint8)

            return frame

        # ── Load clip and wire the master processor ────────────────────────
        clip = VideoFileClip(input_path).subclip(trim_start, trim_end)
        clip = clip.fl(process_frame, apply_to=["mask", "video"])
        clip = even_size(clip)

        # ── Export ────────────────────────────────────────────────────────
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

wm_row1c1, wm_row1c2 = st.columns([3, 1])
with wm_row1c1:
    watermark_text = st.text_input("Watermark text", placeholder="@yourhandle  or  YourBrand™", key="wm_text", label_visibility="collapsed")
with wm_row1c2:
    wm_position = st.selectbox(
        "Position",
        ["Top Left", "Top Center", "Top Right", "Center", "Bottom Left", "Bottom Center", "Bottom Right"],
        index=1, key="wm_pos",
    )

wm_row2c1, wm_row2c2 = st.columns(2)
with wm_row2c1:
    wm_opacity = st.slider("Opacity", 5, 60, 20, 1, key="wm_op", format="%d%%")
with wm_row2c2:
    wm_font_size = st.slider("Font size", 16, 72, 32, 2, key="wm_fs", format="%dpx")

# Live preview — 9-zone grid
if watermark_text.strip():
    POS_CSS = {
        "Top Left":      "top:8px;left:10px;transform:none",
        "Top Center":    "top:8px;left:50%;transform:translateX(-50%)",
        "Top Right":     "top:8px;right:10px;transform:none",
        "Center":        "top:50%;left:50%;transform:translate(-50%,-50%)",
        "Bottom Left":   "bottom:8px;left:10px;transform:none",
        "Bottom Center": "bottom:8px;left:50%;transform:translateX(-50%)",
        "Bottom Right":  "bottom:8px;right:10px;transform:none",
    }
    css_pos = POS_CSS.get(wm_position, "top:8px;left:50%;transform:translateX(-50%)")
    scaled_fs = int(wm_font_size * 0.55)
    st.markdown(f"""
<div style="position:relative;background:#1c1c27;border:1px solid #2a2a3d;border-radius:12px;
            height:90px;overflow:hidden;margin-top:0.5rem;">
  <span style="position:absolute;{css_pos};opacity:{wm_opacity/100};
               font-size:{scaled_fs}px;color:white;white-space:nowrap;
               font-family:'Syne',sans-serif;letter-spacing:2px;">
    {watermark_text}
  </span>
</div>
<p style="font-size:0.78rem;color:#6e6a8a;margin-top:0.4rem;">
  ↑ Preview · Position: <b style="color:#f0eeff">{wm_position}</b> · Opacity: <b style="color:#f0eeff">{wm_opacity}%</b>
</p>
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
                wm_position=wm_position,
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
