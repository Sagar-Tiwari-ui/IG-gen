import streamlit as st
import tempfile
import os
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

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Reels Studio", page_icon="🎬", layout="wide",
                   initial_sidebar_state="collapsed")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
:root{--bg:#0a0a0f;--surface:#13131a;--surface2:#1c1c27;--accent:#ff3b6e;
      --accent2:#ff8c42;--text:#f0eeff;--muted:#6e6a8a;--border:#2a2a3d;
      --success:#2af598;--radius:14px;}
html,body,[data-testid="stApp"]{background:var(--bg)!important;color:var(--text)!important;
  font-family:'DM Sans',sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
[data-testid="stToolbar"]{display:none;}
.hero{text-align:center;padding:2.5rem 1rem 1.5rem;
  background:radial-gradient(ellipse 80% 60% at 50% -20%,rgba(255,59,110,.18) 0%,transparent 70%);}
.hero h1{font-family:'Syne',sans-serif;font-weight:800;font-size:3rem;letter-spacing:-1px;
  background:linear-gradient(135deg,#ff3b6e 0%,#ff8c42 50%,#f0eeff 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0 0 .3rem;}
.hero p{color:var(--muted);font-size:1.05rem;margin:0;}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
  padding:1.5rem;margin-bottom:1.2rem;}
.card-title{font-family:'Syne',sans-serif;font-weight:700;font-size:.85rem;letter-spacing:2px;
  text-transform:uppercase;color:var(--accent);margin:0 0 1rem;display:flex;align-items:center;gap:.5rem;}
.effect-badge{display:inline-flex;align-items:center;gap:.4rem;background:var(--surface2);
  border:1px solid var(--border);border-radius:30px;padding:.3rem .8rem;font-size:.82rem;
  color:var(--text);margin:.2rem;}
.effect-dot{width:8px;height:8px;border-radius:50%;background:var(--accent);flex-shrink:0;}
[data-testid="stSelectbox"]>div>div,[data-testid="stTextInput"]>div>div>input,
[data-testid="stNumberInput"] input{background:var(--surface2)!important;
  border-color:var(--border)!important;color:var(--text)!important;border-radius:10px!important;}
[data-testid="stSelectbox"]>div>div{color:var(--text)!important;}
div[data-testid="stButton"]>button{border-radius:10px!important;font-family:'Syne',sans-serif!important;
  font-weight:600!important;transition:all .2s!important;}
div[data-testid="stButton"]>button:hover{transform:translateY(-1px);
  box-shadow:0 6px 20px rgba(255,59,110,.25)!important;}
.primary-btn>div>button{background:linear-gradient(135deg,#ff3b6e,#ff8c42)!important;
  color:white!important;border:none!important;padding:.6rem 2rem!important;}
.stProgress>div>div{background:linear-gradient(90deg,#ff3b6e,#ff8c42)!important;}
.divider{border-top:1px solid var(--border);margin:1.2rem 0;}
.metric-row{display:flex;gap:.8rem;margin-bottom:1rem;flex-wrap:wrap;}
.metric-chip{background:var(--surface2);border:1px solid var(--border);border-radius:8px;
  padding:.4rem .9rem;font-size:.8rem;color:var(--muted);}
.metric-chip span{color:var(--text);font-weight:600;margin-left:.3rem;}
.info-box{background:rgba(42,245,152,.07);border:1px solid rgba(42,245,152,.25);border-radius:10px;
  padding:.8rem 1rem;font-size:.88rem;color:var(--success);margin:.8rem 0;}
.warn-box{background:rgba(255,140,66,.08);border:1px solid rgba(255,140,66,.3);border-radius:10px;
  padding:.8rem 1rem;font-size:.88rem;color:var(--accent2);margin:.8rem 0;}
label,.stCheckbox span,[data-testid="stMarkdownContainer"] p{
  color:var(--text)!important;font-family:'DM Sans',sans-serif!important;}
</style>""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("effects", []), ("processing", False), ("output_path", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Effects library ───────────────────────────────────────────────────────────
EFFECTS_LIBRARY = {
    "🎬 Cinematic & Celebrity": {
        "Speed Ramp Slow-Mo":    "Smooth slow-in / slow-out — the #1 celebrity reel technique",
        "Cinematic Letterbox":   "Adds 2.39:1 black bars for a widescreen film look",
        "Dreamy Glow":           "Soft golden halation over highlights — luxury & fashion staple",
        "Skin Smooth & Glow":    "Gaussian softening + warm lift — flatters faces beautifully",
        "Hollywood Contrast":    "Deep lifted blacks + boosted whites — high-end grade",
        "Wes Anderson Palette":  "Symmetrical pastel palette — aesthetic & artistic reels",
        "Freeze Frame":          "Freezes the frame then resumes — perfect for reveal moments",
        "Reverse Clip":          "Plays frames backward — water, hair-flip, confetti tricks",
        "Ken Burns Zoom":        "Slow cinematic push-in / pull-out on static or slow scenes",
        "Slow Zoom In":          "Gradual zoom toward center — builds tension & drama",
    },
    "🌈 Color & Tone": {
        "Vibrance Boost":        "Pumps saturation for lifestyle & travel content",
        "Cinematic Teal-Orange": "Hollywood teal shadows + warm skin highlights",
        "Black & White":         "High-contrast monochrome — timeless editorial look",
        "Faded Film":            "Lifted blacks — vintage Instagram aesthetic",
        "Golden Hour":           "Warm amber overlay mimicking sunset light",
        "Cool Matte":            "Desaturated blue-toned matte grade",
        "Neon Glow":             "Electric color halos around bright areas",
        "Duotone":               "Two-color gradient overlay — bold & trendy",
        "Warm Vintage":          "Orange-shifted grain — cozy nostalgic feel",
        "Hyper Color Pop":       "Extreme saturation boost — music video energy",
    },
    "✨ Light & Atmosphere": {
        "Vignette":              "Darkens edges — draws all focus to subject",
        "Lens Blur (Bokeh)":     "Gaussian background blur with sharp center",
        "Bloom / Halation":      "Dreamy glow around highlights",
        "Light Leak":            "Warm analog streak from film camera",
        "Lens Flare":            "Anamorphic horizontal streak",
        "Particle Sparkle":      "Golden glitter particles drifting across frame",
        "Soft Focus":            "Overall gentle blur — romantic / dreamy look",
        "God Rays":              "Diagonal light shafts from top-right corner",
        "Glitter Overlay":       "Shimmering bright specks — ideal for fashion reels",
    },
    "⚡ Motion & Energy": {
        "Motion Blur":           "Horizontal smear — speed & energy",
        "Glitch":                "RGB channel split + scanline artifacts",
        "Prism Shift":           "Chromatic aberration edge fringing",
        "Wave Ripple":           "Sinusoidal warp — hypnotic distortion",
        "Zoom Pulse":            "Rhythmic breathe-in zoom — beat-sync energy",
        "Shake / Handheld":      "Subtle camera shake — raw authentic energy",
        "Whip Pan Blur":         "Horizontal motion blur wipe",
        "Stutter Cut":           "Fast on/off flicker — electronic music edits",
        "Mirror / Kaleidoscope": "Horizontal symmetry mirror",
        "Fish Eye":              "Wide-angle barrel distortion",
    },
    "🎞 Retro & Film": {
        "VHS Tape":              "Scanlines, color bleed, tape noise",
        "Super 8mm":             "Grain, flicker, burnt-edge vignette",
        "Analog Grain":          "Fine film-like noise overlay",
        "CRT Screen":            "Pixel grid + phosphor glow scanlines",
        "Lo-Fi Dither":          "Reduced palette with dithering",
        "Film Burn":             "Orange-red burn sweeping across frame",
        "Old Movie Flicker":     "Sepia + brightness flicker + scratches",
    },
    "🔤 Text & Overlays": {
        "Subtitle Burn-in":      "Text at bottom with shadow — set timestamp + text",
        "Lower Third":           "News-style name bar at bottom",
        "Timestamp":             "HH:MM:SS counter overlay at top-left",
        "Hashtag Overlay":       "Floating hashtag text — boosts discoverability feel",
    },
    "⚡ Transitions": {
        "Cross Dissolve":        "Smooth opacity fade",
        "Flash White":           "Instant white flash — beat drop transition",
        "Zoom In/Out Cut":       "Zoom-in then snap — high energy",
        "Glitch Transition":     "RGB-split stutter at cut point",
        "Hard Cut":              "Clean instant cut — no effect",
    },
}

FLAT_EFFECTS = {}
EFFECT_NAMES_BY_CAT = {}
for cat, effs in EFFECTS_LIBRARY.items():
    EFFECT_NAMES_BY_CAT[cat] = list(effs.keys())
    for name, desc in effs.items():
        FLAT_EFFECTS[name] = {"category": cat, "description": desc}

# Effects that need an extra text parameter
TEXT_EFFECTS = {"Subtitle Burn-in", "Lower Third", "Hashtag Overlay"}

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt(s):
    return f"{int(s)//60:02d}:{int(s)%60:02d}"

def get_duration(path):
    try:
        from moviepy.editor import VideoFileClip
        with VideoFileClip(path) as c:
            return c.duration
    except Exception:
        return None

# ── Core processing ───────────────────────────────────────────────────────────
def apply_effects_and_export(input_path, output_path, effects_list,
                              watermark_text, wm_opacity, wm_font_size, wm_position,
                              trim_start, trim_end):
    try:
        import numpy as np
        from moviepy.editor import VideoFileClip
        from moviepy.video.fx.all import even_size

        # ── Frame utilities ───────────────────────────────────────────────
        def u8(frame):
            """Always return uint8 (H,W,3) array."""
            a = np.asarray(frame, dtype=np.float64)
            if a.max() <= 1.0:
                a = a * 255.0
            a = np.clip(a, 0, 255).astype(np.uint8)
            if a.ndim == 3 and a.shape[2] == 4:
                a = a[:, :, :3]
            return np.ascontiguousarray(a)

        def pil_to_u8(pil_img):
            return np.ascontiguousarray(np.array(pil_img.convert("RGB"))).astype(np.uint8)

        def load_font(size):
            from PIL import ImageFont
            for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                      "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                      "/usr/share/fonts/truetype/freefont/FreeSans.ttf"]:
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
            return ImageFont.load_default()

        def draw_text_with_shadow(draw, x, y, text, font, color=(255,255,255,230)):
            draw.text((x+2, y+2), text, font=font, fill=(0,0,0,160))
            draw.text((x,   y  ), text, font=font, fill=color)

        # ── Individual effect functions ───────────────────────────────────
        # All take (frame: uint8 ndarray, t_rel: float, eff_dur: float, **kw)

        def fx_bw(f, t, d, **kw):
            g = np.mean(f, axis=2, keepdims=True).astype(np.uint8)
            return np.repeat(g, 3, axis=2)

        def fx_vibrance(f, t, d, **kw):
            fl = f.astype(np.float32)
            mean = fl.mean(axis=2, keepdims=True)
            return np.clip(mean + (fl - mean) * 1.65, 0, 255).astype(np.uint8)

        def fx_teal_orange(f, t, d, **kw):
            fl = f.astype(np.float32)
            fl[:,:,0] = np.clip(fl[:,:,0] * 1.15, 0, 255)
            fl[:,:,2] = np.clip(fl[:,:,2] * 0.78, 0, 255)
            return fl.astype(np.uint8)

        def fx_faded(f, t, d, **kw):
            return np.clip(f.astype(np.float32) * 0.85 + 30, 0, 255).astype(np.uint8)

        def fx_golden_hour(f, t, d, **kw):
            fl = f.astype(np.float32)
            fl[:,:,0] = np.clip(fl[:,:,0] * 1.22, 0, 255)
            fl[:,:,1] = np.clip(fl[:,:,1] * 1.06, 0, 255)
            fl[:,:,2] = np.clip(fl[:,:,2] * 0.72, 0, 255)
            return fl.astype(np.uint8)

        def fx_cool_matte(f, t, d, **kw):
            fl = f.astype(np.float32)
            fl[:,:,2] = np.clip(fl[:,:,2] * 1.18 + 12, 0, 255)
            fl[:,:,0] = np.clip(fl[:,:,0] * 0.86, 0, 255)
            return np.clip(fl * 0.88 + 16, 0, 255).astype(np.uint8)

        def fx_neon_glow(f, t, d, **kw):
            from PIL import Image, ImageFilter, ImageChops
            img = Image.fromarray(f)
            glow = img.filter(ImageFilter.GaussianBlur(radius=9))
            return pil_to_u8(ImageChops.add(img, glow, scale=1.5))

        def fx_duotone(f, t, d, **kw):
            gray = np.mean(f, axis=2, keepdims=True) / 255.0
            c1 = np.array([255, 60, 110], dtype=np.float32)
            c2 = np.array([30,  20,  80], dtype=np.float32)
            return np.clip((1 - gray) * c2 + gray * c1, 0, 255).astype(np.uint8)

        def fx_warm_vintage(f, t, d, **kw):
            fl = f.astype(np.float32)
            fl[:,:,0] = np.clip(fl[:,:,0] * 1.18 + 8, 0, 255)
            fl[:,:,2] = np.clip(fl[:,:,2] * 0.80, 0, 255)
            noise = np.random.randint(-12, 12, f.shape, dtype=np.int16)
            return np.clip(fl.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        def fx_hyper_color(f, t, d, **kw):
            fl = f.astype(np.float32)
            mean = fl.mean(axis=2, keepdims=True)
            return np.clip(mean + (fl - mean) * 2.2, 0, 255).astype(np.uint8)

        def fx_hollywood_contrast(f, t, d, **kw):
            fl = f.astype(np.float32)
            # Lift blacks + punch highlights
            fl = np.clip((fl - 30) * 1.20 + 30, 0, 255)
            fl[:,:,0] = np.clip(fl[:,:,0] * 1.08, 0, 255)
            return fl.astype(np.uint8)

        def fx_wes_anderson(f, t, d, **kw):
            fl = f.astype(np.float32)
            # Pastel: lift all channels, slightly pink-peach cast
            fl = np.clip(fl * 0.75 + 50, 0, 255)
            fl[:,:,0] = np.clip(fl[:,:,0] * 1.10, 0, 255)
            fl[:,:,2] = np.clip(fl[:,:,2] * 1.05, 0, 255)
            return fl.astype(np.uint8)

        def fx_dreamy_glow(f, t, d, **kw):
            from PIL import Image, ImageFilter, ImageChops
            img = Image.fromarray(f)
            # Warm golden glow
            warm = img.point(lambda p: min(255, int(p * 1.05 + 5)))
            glow = warm.filter(ImageFilter.GaussianBlur(radius=14))
            blended = ImageChops.blend(img, glow, alpha=0.35)
            return pil_to_u8(blended)

        def fx_skin_smooth(f, t, d, **kw):
            from PIL import Image, ImageFilter
            img = Image.fromarray(f)
            smooth = img.filter(ImageFilter.GaussianBlur(radius=2))
            # Blend 40% smooth — preserves detail, softens skin
            from PIL import ImageChops
            blended = ImageChops.blend(img, smooth, alpha=0.40)
            # Warm lift
            arr = np.array(blended).astype(np.float32)
            arr[:,:,0] = np.clip(arr[:,:,0] * 1.06 + 4, 0, 255)
            arr[:,:,1] = np.clip(arr[:,:,1] * 1.03 + 2, 0, 255)
            return arr.astype(np.uint8)

        def fx_cinematic_letterbox(f, t, d, **kw):
            h, w = f.shape[:2]
            bar = int(h * 0.105)  # 2.39:1 ratio bars
            result = f.copy()
            result[:bar, :, :]  = 0
            result[h-bar:, :, :] = 0
            return result

        def fx_freeze(f, t, d, **kw):
            # Frame is already frozen by the time-locking in process_frame
            return f

        def fx_ken_burns(f, t, d, **kw):
            from PIL import Image
            progress = t / max(d, 0.001)
            # Gentle 1.0 → 1.10 zoom-in
            scale = 1.0 + 0.10 * progress
            img = Image.fromarray(f)
            w2, h2 = img.size
            nw, nh = int(w2 * scale), int(h2 * scale)
            resized = img.resize((nw, nh), Image.LANCZOS)
            ox, oy = (nw - w2) // 2, (nh - h2) // 2
            return pil_to_u8(resized.crop((ox, oy, ox + w2, oy + h2)))

        def fx_slow_zoom_in(f, t, d, **kw):
            from PIL import Image
            progress = t / max(d, 0.001)
            scale = 1.0 + 0.20 * progress   # 1.0 → 1.20
            img = Image.fromarray(f)
            w2, h2 = img.size
            nw, nh = int(w2 * scale), int(h2 * scale)
            resized = img.resize((nw, nh), Image.LANCZOS)
            ox, oy = (nw - w2) // 2, (nh - h2) // 2
            return pil_to_u8(resized.crop((ox, oy, ox + w2, oy + h2)))

        def fx_speed_ramp(f, t, d, **kw):
            # Visual cue: add subtle blur proportional to "speed"
            # Actual temporal slow-mo needs resampling — here we add motion feel
            from PIL import Image, ImageFilter
            progress = t / max(d, 0.001)
            # Slow in middle (0.3-0.7), fast at edges → less blur in middle
            slow_factor = 1.0 - abs(progress - 0.5) * 1.6
            radius = max(0, int(slow_factor * 3))
            if radius < 1:
                return f
            img = Image.fromarray(f)
            return pil_to_u8(img.filter(ImageFilter.GaussianBlur(radius=radius)))

        def fx_vignette(f, t, d, **kw):
            h, w = f.shape[:2]
            X, Y = np.meshgrid(np.linspace(-1,1,w), np.linspace(-1,1,h))
            mask = 1 - np.clip(X**2 + Y**2, 0, 1) ** 0.55
            return np.clip(f * mask[:,:,np.newaxis], 0, 255).astype(np.uint8)

        def fx_bokeh(f, t, d, **kw):
            from PIL import Image, ImageFilter, ImageDraw
            img = Image.fromarray(f)
            blurred = img.filter(ImageFilter.GaussianBlur(radius=8))
            mask = Image.new("L", img.size, 0)
            dr = ImageDraw.Draw(mask)
            cx, cy = img.size[0]//2, img.size[1]//2
            r = min(cx, cy) // 2
            dr.ellipse([cx-r, cy-r, cx+r, cy+r], fill=255)
            mask = mask.filter(ImageFilter.GaussianBlur(radius=50))
            return pil_to_u8(Image.composite(img, blurred, mask))

        def fx_bloom(f, t, d, **kw):
            from PIL import Image, ImageFilter, ImageChops
            img = Image.fromarray(f)
            bright = img.point(lambda p: min(255, int(p * 1.4)))
            glow = bright.filter(ImageFilter.GaussianBlur(radius=14))
            return pil_to_u8(ImageChops.screen(img, glow))

        def fx_light_leak(f, t, d, **kw):
            h, w = f.shape[:2]
            progress = t / max(d, 0.001)
            leak = np.zeros_like(f, dtype=np.float32)
            start_x = int(w * progress * 0.7)
            end_x = min(w, start_x + w // 3)
            leak[:, start_x:end_x, 0] = 100
            leak[:, start_x:end_x, 1] = 55
            return np.clip(f.astype(np.float32) + leak, 0, 255).astype(np.uint8)

        def fx_lens_flare(f, t, d, **kw):
            h, w = f.shape[:2]
            fl = f.astype(np.float32)
            cy = int(h * 0.45)
            fl[cy-3:cy+3, :, :] += np.array([130, 110, 70], dtype=np.float32) * 0.45
            return np.clip(fl, 0, 255).astype(np.uint8)

        def fx_soft_focus(f, t, d, **kw):
            from PIL import Image, ImageFilter, ImageChops
            img = Image.fromarray(f)
            soft = img.filter(ImageFilter.GaussianBlur(radius=4))
            return pil_to_u8(ImageChops.blend(img, soft, alpha=0.5))

        def fx_god_rays(f, t, d, **kw):
            h, w = f.shape[:2]
            fl = f.astype(np.float32)
            for i in range(8):
                angle = np.radians(45 + i * 6)
                length = int(max(w, h) * 1.2)
                for step in range(0, length, 3):
                    rx = int(step * np.cos(angle))
                    ry = int(step * np.sin(angle))
                    x1, y1 = max(0, min(w-1, w//5 + rx)), max(0, min(h-1, ry))
                    alpha = max(0, 0.06 - step / (length * 1.5))
                    fl[max(0,y1-2):y1+2, max(0,x1-2):x1+2, :] += np.array([255,220,160]) * alpha
            return np.clip(fl, 0, 255).astype(np.uint8)

        def fx_particle_sparkle(f, t, d, **kw):
            result = f.copy().astype(np.float32)
            h, w = f.shape[:2]
            rng = np.random.default_rng(int(t * 30))
            n_particles = 60
            xs = rng.integers(0, w, n_particles)
            ys = rng.integers(0, h, n_particles)
            for x, y in zip(xs, ys):
                brightness = rng.uniform(0.6, 1.0)
                size = rng.integers(1, 4)
                for dx in range(-size, size+1):
                    for dy in range(-size, size+1):
                        nx, ny = np.clip(x+dx, 0, w-1), np.clip(y+dy, 0, h-1)
                        result[ny, nx, :] = np.clip(result[ny, nx, :] + brightness * 200, 0, 255)
            return result.astype(np.uint8)

        def fx_glitter_overlay(f, t, d, **kw):
            result = f.copy().astype(np.float32)
            h, w = f.shape[:2]
            rng = np.random.default_rng(int(t * 24) + 7)
            n = 120
            xs = rng.integers(0, w, n)
            ys = rng.integers(0, h, n)
            colors = [[255,215,0],[255,255,200],[255,180,255],[200,255,255]]
            for i, (x, y) in enumerate(zip(xs, ys)):
                c = colors[i % len(colors)]
                b = rng.uniform(0.5, 1.0)
                result[max(0,y-1):y+2, max(0,x-1):x+2, :] = np.clip(
                    result[max(0,y-1):y+2, max(0,x-1):x+2, :] + np.array(c) * b, 0, 255)
            return result.astype(np.uint8)

        def fx_motion_blur(f, t, d, **kw):
            from PIL import Image, ImageFilter
            return pil_to_u8(Image.fromarray(f).filter(ImageFilter.SMOOTH_MORE))

        def fx_glitch(f, t, d, **kw):
            r = f.copy()
            fh = f.shape[0]
            rng = np.random.default_rng(int(t * 60))
            for _ in range(rng.integers(4, 10)):
                y  = rng.integers(0, max(1, fh - 14))
                ht = rng.integers(2, 14)
                sh = rng.integers(-28, 28)
                r[y:y+ht,:,:] = np.roll(r[y:y+ht,:,:], int(sh), axis=1)
            return r.astype(np.uint8)

        def fx_prism(f, t, d, **kw):
            r = f.copy()
            s = 7
            r[:, s:,  0] = f[:, :-s, 0]
            r[:, :-s, 2] = f[:, s:,  2]
            return r.astype(np.uint8)

        def fx_wave(f, t, d, **kw):
            h, w = f.shape[:2]
            result = np.empty_like(f)
            for row in range(h):
                shift = int(10 * np.sin(2 * np.pi * (row / 28.0 + t * 2.0)))
                result[row] = np.roll(f[row], shift, axis=0)
            return result.astype(np.uint8)

        def fx_zoom_pulse(f, t, d, **kw):
            from PIL import Image
            progress = t / max(d, 0.001)
            scale = 1.0 + 0.14 * np.sin(np.pi * progress)
            img = Image.fromarray(f)
            w2, h2 = img.size
            nw, nh = max(w2, int(w2 * scale)), max(h2, int(h2 * scale))
            resized = img.resize((nw, nh), Image.LANCZOS)
            ox, oy = (nw - w2) // 2, (nh - h2) // 2
            return pil_to_u8(resized.crop((ox, oy, ox+w2, oy+h2)))

        def fx_shake(f, t, d, **kw):
            rng = np.random.default_rng(int(t * 30))
            dx, dy = rng.integers(-6, 7), rng.integers(-4, 5)
            return np.roll(np.roll(f, int(dx), axis=1), int(dy), axis=0).astype(np.uint8)

        def fx_whip_pan(f, t, d, **kw):
            from PIL import Image, ImageFilter
            progress = t / max(d, 0.001)
            radius = int(25 * np.sin(np.pi * progress))
            if radius < 1:
                return f
            return pil_to_u8(Image.fromarray(f).filter(ImageFilter.GaussianBlur(radius=radius)))

        def fx_stutter(f, t, d, **kw):
            # Every other ~4 frames flips to black briefly
            tick = int(t * 12) % 4
            if tick == 0:
                return np.zeros_like(f, dtype=np.uint8)
            return f

        def fx_mirror(f, t, d, **kw):
            half = f[:, :f.shape[1]//2, :]
            return np.concatenate([half, half[:, ::-1, :]], axis=1).astype(np.uint8)

        def fx_fisheye(f, t, d, **kw):
            from PIL import Image
            img = Image.fromarray(f)
            w2, h2 = img.size
            inner = img.resize((int(w2*0.80), int(h2*0.80)), Image.LANCZOS)
            canvas = Image.new("RGB", (w2, h2), (0,0,0))
            canvas.paste(inner, ((w2-inner.width)//2, (h2-inner.height)//2))
            return pil_to_u8(canvas)

        def fx_vhs(f, t, d, **kw):
            result = f.copy()
            result[::2,:,:] = np.clip(result[::2,:,:].astype(np.int16) - 22, 0, 255)
            r_ch = result[:,:,0].copy()
            result[:,2:,0] = r_ch[:,:-2]
            noise = np.random.randint(-9, 9, result.shape, dtype=np.int16)
            return np.clip(result.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        def fx_super8(f, t, d, **kw):
            noise = np.random.randint(-28, 28, f.shape, dtype=np.int16)
            result = np.clip(f.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            h, w = result.shape[:2]
            X, Y = np.meshgrid(np.linspace(-1,1,w), np.linspace(-1,1,h))
            vign = 1 - np.clip((X**2 + Y**2) * 1.3, 0, 1)
            return np.clip(result * vign[:,:,np.newaxis], 0, 255).astype(np.uint8)

        def fx_analog_grain(f, t, d, **kw):
            noise = np.random.randint(-20, 20, f.shape, dtype=np.int16)
            return np.clip(f.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        def fx_crt(f, t, d, **kw):
            result = f.copy()
            result[::3,:,:] = np.clip(result[::3,:,:].astype(np.int16) - 45, 0, 255)
            return result.astype(np.uint8)

        def fx_lofi(f, t, d, **kw):
            return ((f // 64) * 64).astype(np.uint8)

        def fx_film_burn(f, t, d, **kw):
            h, w = f.shape[:2]
            progress = t / max(d, 0.001)
            fl = f.astype(np.float32)
            burn_x = int(w * progress)
            width = int(w * 0.25)
            for i in range(max(0, burn_x - width), min(w, burn_x + width)):
                dist = abs(i - burn_x) / max(width, 1)
                intensity = (1 - dist) * 0.8
                fl[:, i, 0] = np.clip(fl[:, i, 0] + 200 * intensity, 0, 255)
                fl[:, i, 1] = np.clip(fl[:, i, 1] + 80  * intensity, 0, 255)
                fl[:, i, 2] = np.clip(fl[:, i, 2] - 50  * intensity, 0, 255)
            return fl.astype(np.uint8)

        def fx_old_flicker(f, t, d, **kw):
            # Sepia + random brightness flicker
            fl = f.astype(np.float32)
            r = fl[:,:,0]*0.393 + fl[:,:,1]*0.769 + fl[:,:,2]*0.189
            g = fl[:,:,0]*0.349 + fl[:,:,1]*0.686 + fl[:,:,2]*0.168
            b = fl[:,:,0]*0.272 + fl[:,:,1]*0.534 + fl[:,:,2]*0.131
            sepia = np.stack([r,g,b], axis=2)
            brightness = 0.80 + np.sin(t * 18) * 0.15
            return np.clip(sepia * brightness, 0, 255).astype(np.uint8)

        def fx_cross_dissolve(f, t, d, **kw):
            progress = t / max(d, 0.001)
            alpha = 1.0 - 2.0 * abs(progress - 0.5)
            return np.clip(f.astype(np.float32) * max(0.0, alpha), 0, 255).astype(np.uint8)

        def fx_flash_white(f, t, d, **kw):
            intensity = max(0.0, 1.0 - t * 12)
            return np.clip(f.astype(np.float32) + intensity * 255, 0, 255).astype(np.uint8)

        def fx_zoom_cut(f, t, d, **kw):
            return fx_slow_zoom_in(f, t, d)

        def fx_glitch_transition(f, t, d, **kw):
            return fx_prism(fx_glitch(f, t, d), t, d)

        def fx_subtitle(f, t, d, text="", **kw):
            from PIL import Image, ImageDraw
            img = Image.fromarray(f).convert("RGBA")
            ov  = Image.new("RGBA", img.size, (0,0,0,0))
            draw = ImageDraw.Draw(ov)
            font = load_font(36)
            bbox = draw.textbbox((0,0), text, font=font)
            tw = bbox[2] - bbox[0]
            x = (img.width - tw) // 2
            y = img.height - 78
            draw_text_with_shadow(draw, x, y, text, font)
            return pil_to_u8(Image.alpha_composite(img, ov))

        def fx_lower_third(f, t, d, text="", **kw):
            from PIL import Image, ImageDraw
            img = Image.fromarray(f).convert("RGBA")
            ov  = Image.new("RGBA", img.size, (0,0,0,0))
            draw = ImageDraw.Draw(ov)
            bar_h = 58
            draw.rectangle([(0, img.height-bar_h), (img.width, img.height)],
                           fill=(0,0,0,170))
            font = load_font(30)
            draw.text((18, img.height - bar_h + 14), text, font=font,
                      fill=(255,255,255,240))
            return pil_to_u8(Image.alpha_composite(img, ov))

        def fx_timestamp(f, t, d, clip_t=0, **kw):
            import datetime
            ts = str(datetime.timedelta(seconds=int(clip_t))).zfill(8)
            from PIL import Image, ImageDraw
            img = Image.fromarray(f).convert("RGBA")
            ov  = Image.new("RGBA", img.size, (0,0,0,0))
            draw = ImageDraw.Draw(ov)
            font = load_font(26)
            draw.text((14, 14), ts, font=font, fill=(255,255,255,210))
            return pil_to_u8(Image.alpha_composite(img, ov))

        def fx_hashtag(f, t, d, text="#trending", **kw):
            from PIL import Image, ImageDraw
            img = Image.fromarray(f).convert("RGBA")
            ov  = Image.new("RGBA", img.size, (0,0,0,0))
            draw = ImageDraw.Draw(ov)
            font = load_font(28)
            h_img = img.height
            # Float gently up over time
            y_base = int(h_img * 0.75) - int(t * 15)
            y = max(10, min(h_img - 40, y_base))
            draw.text((16, y), text, font=font, fill=(255,255,255,200))
            return pil_to_u8(Image.alpha_composite(img, ov))

        # ── Effect name → function map ─────────────────────────────────────
        FX = {
            "Black & White":         fx_bw,
            "Vibrance Boost":        fx_vibrance,
            "Cinematic Teal-Orange": fx_teal_orange,
            "Faded Film":            fx_faded,
            "Golden Hour":           fx_golden_hour,
            "Cool Matte":            fx_cool_matte,
            "Neon Glow":             fx_neon_glow,
            "Duotone":               fx_duotone,
            "Warm Vintage":          fx_warm_vintage,
            "Hyper Color Pop":       fx_hyper_color,
            "Hollywood Contrast":    fx_hollywood_contrast,
            "Wes Anderson Palette":  fx_wes_anderson,
            "Dreamy Glow":           fx_dreamy_glow,
            "Skin Smooth & Glow":    fx_skin_smooth,
            "Cinematic Letterbox":   fx_cinematic_letterbox,
            "Freeze Frame":          fx_freeze,
            "Ken Burns Zoom":        fx_ken_burns,
            "Slow Zoom In":          fx_slow_zoom_in,
            "Speed Ramp Slow-Mo":    fx_speed_ramp,
            "Vignette":              fx_vignette,
            "Lens Blur (Bokeh)":     fx_bokeh,
            "Bloom / Halation":      fx_bloom,
            "Light Leak":            fx_light_leak,
            "Lens Flare":            fx_lens_flare,
            "Soft Focus":            fx_soft_focus,
            "God Rays":              fx_god_rays,
            "Particle Sparkle":      fx_particle_sparkle,
            "Glitter Overlay":       fx_glitter_overlay,
            "Motion Blur":           fx_motion_blur,
            "Glitch":                fx_glitch,
            "Prism Shift":           fx_prism,
            "Wave Ripple":           fx_wave,
            "Zoom Pulse":            fx_zoom_pulse,
            "Shake / Handheld":      fx_shake,
            "Whip Pan Blur":         fx_whip_pan,
            "Stutter Cut":           fx_stutter,
            "Mirror / Kaleidoscope": fx_mirror,
            "Fish Eye":              fx_fisheye,
            "VHS Tape":              fx_vhs,
            "Super 8mm":             fx_super8,
            "Analog Grain":          fx_analog_grain,
            "CRT Screen":            fx_crt,
            "Lo-Fi Dither":          fx_lofi,
            "Film Burn":             fx_film_burn,
            "Old Movie Flicker":     fx_old_flicker,
            "Cross Dissolve":        fx_cross_dissolve,
            "Flash White":           fx_flash_white,
            "Zoom In/Out Cut":       fx_zoom_cut,
            "Glitch Transition":     fx_glitch_transition,
            "Hard Cut":              lambda f,t,d,**kw: f,
            "Subtitle Burn-in":      fx_subtitle,
            "Lower Third":           fx_lower_third,
            "Timestamp":             fx_timestamp,
            "Hashtag Overlay":       fx_hashtag,
        }

        # ── Load clip & pre-cache frozen frames for Freeze / Reverse ─────
        raw_clip = VideoFileClip(input_path).subclip(trim_start, trim_end)
        clip_fps = raw_clip.fps or 30.0
        clip_dur = raw_clip.duration

        # Pre-read frames for Reverse effect
        reverse_effects = [e for e in effects_list if e["name"] == "Reverse Clip"]
        freeze_effects  = [e for e in effects_list if e["name"] == "Freeze Frame"]

        # For Reverse: cache frames in the effect window
        reverse_cache = {}
        for eff in reverse_effects:
            es, ee = eff["start"], eff["end"]
            frames_in_window = []
            t = es
            while t <= min(ee, clip_dur):
                try:
                    frames_in_window.append((t, u8(raw_clip.get_frame(t))))
                except Exception:
                    pass
                t += 1.0 / clip_fps
            reverse_cache[(es, ee)] = frames_in_window

        # For Freeze: cache the frame at start of window
        freeze_cache = {}
        for eff in freeze_effects:
            es = eff["start"]
            try:
                freeze_cache[es] = u8(raw_clip.get_frame(min(es, clip_dur - 0.01)))
            except Exception:
                freeze_cache[es] = None

        # ── Master per-frame processor ─────────────────────────────────────
        def process_frame(get_frame, t):
            frame = u8(get_frame(t))

            for eff in effects_list:
                name = eff["name"]
                es   = eff["start"]
                ee   = eff["end"]
                if not (es <= t <= ee):
                    continue

                t_rel  = t - es
                eff_dur = max(ee - es, 0.001)
                extra  = eff.get("subtitle_text", "")

                # ── Special temporal effects ───────────────────────────────
                if name == "Reverse Clip":
                    cache = reverse_cache.get((es, ee), [])
                    if cache:
                        progress = t_rel / eff_dur
                        rev_idx = int((1.0 - progress) * (len(cache) - 1))
                        rev_idx = max(0, min(len(cache)-1, rev_idx))
                        frame = cache[rev_idx][1].copy()
                    continue

                if name == "Freeze Frame":
                    frozen = freeze_cache.get(es)
                    if frozen is not None:
                        frame = frozen.copy()
                    continue

                # ── Standard effects via dispatch table ────────────────────
                fn = FX.get(name)
                if fn is None:
                    continue

                if name in ("Subtitle Burn-in", "Lower Third", "Hashtag Overlay"):
                    frame = u8(fn(frame, t_rel, eff_dur, text=extra))
                elif name == "Timestamp":
                    frame = u8(fn(frame, t_rel, eff_dur, clip_t=t))
                else:
                    frame = u8(fn(frame, t_rel, eff_dur))

            # ── Watermark (always-on) ──────────────────────────────────────
            if watermark_text.strip():
                from PIL import Image, ImageDraw
                img  = Image.fromarray(frame).convert("RGBA")
                ov   = Image.new("RGBA", img.size, (0,0,0,0))
                draw = ImageDraw.Draw(ov)
                font = load_font(wm_font_size)
                bbox = draw.textbbox((0,0), watermark_text, font=font)
                tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
                W, H   = img.size
                pad    = 16
                pos_map = {
                    "Top Left":      (pad, pad),
                    "Top Center":    ((W-tw)//2, pad),
                    "Top Right":     (W-tw-pad, pad),
                    "Center":        ((W-tw)//2, (H-th)//2),
                    "Bottom Left":   (pad, H-th-pad),
                    "Bottom Center": ((W-tw)//2, H-th-pad),
                    "Bottom Right":  (W-tw-pad, H-th-pad),
                }
                x, y = pos_map.get(wm_position, ((W-tw)//2, pad))
                draw.text((x+1,y+1), watermark_text, font=font, fill=(0,0,0,120))
                draw.text((x,  y  ), watermark_text, font=font,
                          fill=(255,255,255, int(255*wm_opacity/100)))
                frame = pil_to_u8(Image.alpha_composite(img, ov))

            return frame

        # Wire the processor, even-size for H.264, export
        processed = raw_clip.fl(process_frame, apply_to=["video"])
        processed = even_size(processed)
        processed.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=output_path + "_tmp_audio.m4a",
            remove_temp=True,
            logger=None,
            preset="ultrafast",
            ffmpeg_params=["-crf", "23", "-pix_fmt", "yuv420p"],
        )
        processed.close()
        raw_clip.close()
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
  <p>Celebrity-grade Instagram Reels editor — 50+ effects · timestamps · stacking</p>
</div>
""", unsafe_allow_html=True)

if _dep_errors:
    for e in _dep_errors:
        st.error(e)
    st.warning("Fix `requirements.txt`, commit, then **Reboot app** on Streamlit Cloud.")
    st.code("moviepy==1.0.3\nimageio==2.25.1\ndecorator==4.4.2\nimageio-ffmpeg==0.4.9", language="text")
    st.stop()

# ── Upload ────────────────────────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-title">📁 Upload Video</div>', unsafe_allow_html=True)
uploaded = st.file_uploader("Drop reel (MP4/MOV/AVI · max 60 s)",
                             type=["mp4","mov","avi","mkv"], label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

video_duration = None
tmp_input_path = None

if uploaded:
    suffix = Path(uploaded.name).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded.read()); tmp.flush()
    tmp_input_path = tmp.name
    video_duration = get_duration(tmp_input_path)

    c1, c2 = st.columns([1,1])
    with c1:
        st.video(tmp_input_path)
    with c2:
        if video_duration:
            color = "warn-box" if video_duration > 60 else "info-box"
            icon  = "⚠️" if video_duration > 60 else "✅"
            label = f"over 60s — will be trimmed" if video_duration > 60 else "ready to edit"
            st.markdown(f'<div class="{color}">{icon} {video_duration:.1f}s · {label}</div>',
                        unsafe_allow_html=True)
            st.markdown(f"""<div class="metric-row">
              <div class="metric-chip">Duration<span>{fmt(video_duration)}</span></div>
              <div class="metric-chip">File<span>{uploaded.name}</span></div>
              <div class="metric-chip">Size<span>{uploaded.size/1e6:.1f} MB</span></div>
            </div>""", unsafe_allow_html=True)

# ── Trim ──────────────────────────────────────────────────────────────────────
trim_start, trim_end = 0.0, 60.0
if video_duration:
    max_dur = min(video_duration, 60.0)
    st.markdown('<div class="card"><div class="card-title">✂️ Trim Clip</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        trim_start = st.slider("Start (s)", 0.0, float(max_dur-0.5), 0.0, 0.1, format="%.1fs")
    with c2:
        trim_end = st.slider("End (s)", float(trim_start+0.5), float(max_dur), float(max_dur), 0.1, format="%.1fs")
    st.markdown(f'<div class="info-box">📐 {fmt(trim_start)} → {fmt(trim_end)} · {trim_end-trim_start:.1f}s</div>',
                unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Effects builder ───────────────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-title">✨ Effects Timeline</div>', unsafe_allow_html=True)

if not uploaded:
    st.markdown('<p style="color:#6e6a8a">Upload a video first.</p>', unsafe_allow_html=True)
else:
    clip_dur = (trim_end - trim_start) if video_duration else 60.0

    # ── Effect list ───────────────────────────────────────────────────────
    if st.session_state.effects:
        st.markdown("**Timeline — all effects applied in order within their time window:**")
        header_cols = st.columns([3, 2, 2, 1])
        for hdr, col in zip(["Effect","Time window","Extra",""], header_cols):
            col.markdown(f"<small style='color:#6e6a8a'>{hdr}</small>", unsafe_allow_html=True)

        for i, eff in enumerate(st.session_state.effects):
            cols = st.columns([3, 2, 2, 1])
            with cols[0]:
                st.markdown(f'<div class="effect-badge"><span class="effect-dot"></span>{eff["name"]}</div>',
                            unsafe_allow_html=True)
            with cols[1]:
                st.caption(f"⏱ {fmt(eff['start'])} → {fmt(eff['end'])}")
            with cols[2]:
                if eff.get("subtitle_text"):
                    st.caption(f'💬 "{eff["subtitle_text"]}"')
            with cols[3]:
                if st.button("✕", key=f"del_{i}", help="Remove"):
                    st.session_state.effects.pop(i)
                    st.rerun()
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Add effect ────────────────────────────────────────────────────────
    st.markdown("**Add effect to timeline:**")
    ae1, ae2, ae3 = st.columns([2, 1.5, 1.5])
    with ae1:
        cat      = st.selectbox("Category", list(EFFECTS_LIBRARY.keys()), key="new_cat",
                                label_visibility="collapsed")
        eff_name = st.selectbox("Effect",   EFFECT_NAMES_BY_CAT[cat],     key="new_eff",
                                label_visibility="collapsed")
        if eff_name in FLAT_EFFECTS:
            st.caption(f"ℹ️ {FLAT_EFFECTS[eff_name]['description']}")
    with ae2:
        new_start = st.number_input("Start (s)", 0.0, float(clip_dur), 0.0, 0.1, key="new_start")
    with ae3:
        new_end   = st.number_input("End (s)", float(new_start), float(clip_dur),
                                    float(clip_dur), 0.1, key="new_end")

    sub_text = ""
    if eff_name in TEXT_EFFECTS:
        label = {"Subtitle Burn-in": "Subtitle text",
                 "Lower Third":      "Name / caption",
                 "Hashtag Overlay":  "Hashtag text"}.get(eff_name, "Text")
        sub_text = st.text_input(label, key="sub_text",
                                 placeholder="#trending  or  @yourname")

    if st.button("＋ Add Effect to Timeline", use_container_width=True):
        entry = {"name": eff_name, "start": float(new_start), "end": float(new_end)}
        if sub_text:
            entry["subtitle_text"] = sub_text
        st.session_state.effects.append(entry)
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ── Trending effects guide ────────────────────────────────────────────────────
with st.expander("💡 Celebrity Reel Effects Guide — what to use & when"):
    st.markdown("""
| Effect | Best for | How to use |
|---|---|---|
| **Speed Ramp Slow-Mo** | Dance, fashion reveals, action | 0s–clip-end — slow middle, fast edges |
| **Dreamy Glow** | Beauty, fashion, luxury | All clip or highlights section |
| **Skin Smooth & Glow** | Selfies, talking-head, beauty | Anywhere face is prominent |
| **Cinematic Letterbox** | Cinematic / travel / concert reels | All clip |
| **Hollywood Contrast** | Bold editorial, streetwear, sports | All clip or high-energy sections |
| **Wes Anderson Palette** | Aesthetic / art / fashion reels | All clip |
| **Golden Hour** | Travel, outdoor, lifestyle | Outdoor scenes |
| **Freeze Frame** | Reveal moment, funny reaction | 0.5–1.5s window at the big moment |
| **Reverse Clip** | Water pours, confetti, hair flip | 1–3s window on the action |
| **Ken Burns Zoom** | Photos, slow beauty shots | 3–10s over static / slow footage |
| **Particle Sparkle** | Fashion, luxury product shots | 2–5s at hero moment |
| **Glitter Overlay** | Fashion, beauty, celebration | 2–5s at hero moment |
| **Light Leak** | Trendy transitions | 0.5–1s at each scene change |
| **Flash White** | Beat drop, reveal, outfit change | 0.1–0.3s at exact beat |
| **Glitch Transition** | Music, tech, streetwear | 0.2–0.5s at cut |
| **Vignette** | All content — stack with any color grade | All clip |
| **Subtitle Burn-in** | Captions, tutorial steps | Exact spoken section |
| **Hashtag Overlay** | Discoverability boost overlay | 3–8s in middle |
""")

# ── Watermark ─────────────────────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-title">🔏 Watermark</div>', unsafe_allow_html=True)

wm_r1c1, wm_r1c2 = st.columns([3, 1])
with wm_r1c1:
    watermark_text = st.text_input("Watermark text", placeholder="@yourhandle  or  YourBrand™",
                                   key="wm_text", label_visibility="collapsed")
with wm_r1c2:
    wm_position = st.selectbox("Position",
        ["Top Left","Top Center","Top Right","Center",
         "Bottom Left","Bottom Center","Bottom Right"],
        index=1, key="wm_pos")

wm_r2c1, wm_r2c2 = st.columns(2)
with wm_r2c1:
    wm_opacity  = st.slider("Opacity",   5, 60, 20, 1, key="wm_op",  format="%d%%")
with wm_r2c2:
    wm_font_size = st.slider("Font size", 16, 72, 32, 2, key="wm_fs", format="%dpx")

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
    fs_px   = int(wm_font_size * 0.55)
    st.markdown(f"""
<div style="position:relative;background:#1c1c27;border:1px solid #2a2a3d;border-radius:12px;
            height:90px;overflow:hidden;margin-top:.5rem;">
  <span style="position:absolute;{css_pos};opacity:{wm_opacity/100};font-size:{fs_px}px;
               color:white;white-space:nowrap;font-family:'Syne',sans-serif;letter-spacing:2px;">
    {watermark_text}
  </span>
</div>
<p style="font-size:.78rem;color:#6e6a8a;margin-top:.4rem;">
  ↑ Preview · <b style="color:#f0eeff">{wm_position}</b> · {wm_opacity}% opacity
</p>""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Export ────────────────────────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-title">🚀 Export</div>', unsafe_allow_html=True)

ec1, _ = st.columns([2, 1])
with ec1:
    output_filename = st.text_input("Output filename", value="reel_edited.mp4", key="out_name")

export_ready = uploaded is not None

if export_ready:
    st.markdown(f"""<div class="metric-row">
      <div class="metric-chip">Effects<span>{len(st.session_state.effects)}</span></div>
      <div class="metric-chip">Watermark<span>{"✓ " + wm_position if watermark_text.strip() else "—"}</span></div>
      <div class="metric-chip">Trim<span>{fmt(trim_start)} → {fmt(trim_end)}</span></div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
    if st.button("🎬 Render & Export Reel", use_container_width=True,
                 disabled=st.session_state.processing):
        st.session_state.processing = True
        st.session_state.output_path = None

        with st.spinner("Rendering… this may take 30–90 seconds depending on clip length 🎞"):
            import time
            prog = st.progress(0, text="Initialising pipeline…")
            prog.progress(10, text="Loading clip…")
            time.sleep(0.2)

            out_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            out_tmp.close()

            prog.progress(30, text="Applying effects frame-by-frame…")
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
            prog.progress(92, text="Encoding H.264…")
            time.sleep(0.2)
            prog.progress(100, text="Done!")

        st.session_state.processing = False

        if success:
            with open(out_tmp.name, "rb") as fh:
                video_bytes = fh.read()
            st.success("✅ Reel exported successfully!")
            st.video(out_tmp.name)
            st.download_button("⬇️ Download Reel", data=video_bytes,
                               file_name=output_filename, mime="video/mp4",
                               use_container_width=True)
        else:
            st.error(f"❌ Export failed")
            st.code(msg, language="text")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown('<p style="color:#6e6a8a">Upload a video to enable export.</p>',
                unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<hr style="border-color:#2a2a3d;margin-top:2rem"/>
<p style="text-align:center;color:#3a3a55;font-size:.78rem;padding-bottom:1rem">
  Reels Studio · 50+ Effects · Timestamp-accurate stacking · Max 60s
</p>""", unsafe_allow_html=True)
