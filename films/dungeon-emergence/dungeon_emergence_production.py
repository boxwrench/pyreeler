"""
PyReeler: Dungeon Emergence (Production Version)
45-60 second code-generated film with:
- Proper dungeon maze visualization
- Character growth P → PYREELER with voice
- Enemy encounters
- Satisfying title reveal

Run: python dungeon_emergence_production.py
"""

from __future__ import annotations

import math
import os
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Add skill templates to path
sys.path.insert(0, str(Path(__file__).parent.parent / "pyreeler-codex" / "templates" / "video"))
sys.path.insert(0, str(Path(__file__).parent.parent / "pyreeler-codex" / "templates" / "audio"))

from render_runtime import detect_render_runtime
from audio_engine import mix_stems, write_mono_wav
from voice import render_edge_tts


# =============================================================================
# CONFIGURATION
# =============================================================================

WIDTH, HEIGHT = 1280, 720
FPS = 24
DURATION = 50.0  # seconds
TOTAL_FRAMES = int(DURATION * FPS)

# Color palette
COLORS = {
    "void": (10, 10, 15),
    "wall": (40, 45, 60),
    "wall_highlight": (60, 65, 85),
    "floor": (25, 30, 40),
    "floor_lit": (35, 42, 55),
    "player_glow": (100, 200, 255),
    "enemy": (255, 80, 80),
    "enemy_glow": (255, 120, 120),
    "text": (240, 245, 255),
    "accent": (255, 200, 100),
}

# Growth phases: (start_frame, end_frame, text, has_voice)
GROWTH_PHASES = [
    (0, 48, "P", False),      # 0-2s: Just P
    (48, 96, "PY", False),    # 2-4s: PY
    (96, 168, "PYR", False),  # 4-7s: PYR
    (168, 264, "PYRE", False), # 7-11s: PYRE
    (264, 360, "PYREE", False), # 11-15s: PYREE
    (360, 480, "PYREELER", True), # 15-20s: PYREELER + voice
    (480, 600, "PYREELER", False), # 20-25s: Hold full name
]

# Title reveal: (start_frame, end_frame)
TITLE_REVEAL = (720, 960)  # 30-40s
TITLE_HOLD = (960, 1200)   # 40-50s


# =============================================================================
# DUNGEON GENERATION
# =============================================================================

class Dungeon:
    """Simple maze with rooms and corridors."""
    
    def __init__(self, width: int = 21, height: int = 15):
        self.width = width
        self.height = height
        self.grid = [[1 for _ in range(width)] for _ in range(height)]  # 1 = wall
        self.rooms = []
        self.enemies = []
        self._generate()
    
    def _generate(self):
        """Generate dungeon with rooms and connecting corridors."""
        # Create central starting room
        cx, cy = self.width // 2, self.height // 2
        self._carve_room(cx - 2, cy - 2, 5, 5)
        self.start_pos = (cx, cy)
        
        # Add rooms radiating outward
        room_centers = [
            (cx - 6, cy - 4), (cx + 6, cy - 4),
            (cx - 6, cy + 4), (cx + 6, cy + 4),
            (cx, cy - 7), (cx, cy + 7),
        ]
        
        for rx, ry in room_centers:
            if 2 <= rx < self.width - 3 and 2 <= ry < self.height - 3:
                self._carve_room(rx - 1, ry - 1, 3, 3)
                self._carve_corridor(cx, cy, rx, ry)
                # Add enemy to this room
                self.enemies.append({
                    'pos': (rx, ry),
                    'alive': True,
                    'type': random.choice(['hunter', 'patrol']),
                    'hp': 2
                })
        
        # Center is clear
        self.grid[cy][cx] = 0
        
        # Final room at bottom
        self.end_pos = (cx, self.height - 3)
        self._carve_room(cx - 2, self.height - 5, 5, 4)
        self._carve_corridor(cx, cy + 3, cx, self.height - 5)
    
    def _carve_room(self, x, y, w, h):
        """Carve out a rectangular room."""
        for dy in range(h):
            for dx in range(w):
                if 0 <= y + dy < self.height and 0 <= x + dx < self.width:
                    self.grid[y + dy][x + dx] = 0
                    self.rooms.append((x + dx, y + dy))
    
    def _carve_corridor(self, x1, y1, x2, y2):
        """L-shaped corridor between two points."""
        # Horizontal then vertical
        x, y = x1, y1
        while x != x2:
            x += 1 if x2 > x else -1
            if 0 <= y < self.height and 0 <= x < self.width:
                self.grid[y][x] = 0
        while y != y2:
            y += 1 if y2 > y else -1
            if 0 <= y < self.height and 0 <= x < self.width:
                self.grid[y][x] = 0
    
    def is_wall(self, x, y):
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.grid[y][x] == 1
        return True
    
    def get_visible_cells(self, px, py, radius=4):
        """Get cells visible from position."""
        visible = []
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                x, y = px + dx, py + dy
                if 0 <= y < self.height and 0 <= x < self.width:
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist <= radius:
                        visible.append((x, y, dist))
        return visible


# =============================================================================
# RENDERING
# =============================================================================

def get_tile_char(x, y, dungeon, player_pos, enemies, frame):
    """Get the display character/color for a dungeon tile."""
    px, py = player_pos
    
    # Check for enemies
    for enemy in enemies:
        if enemy['alive'] and enemy['pos'] == (x, y):
            # Animated enemy
            pulse = math.sin(frame * 0.2) * 0.3 + 0.7
            return ('E', COLORS["enemy"], pulse)
    
    # Check for player
    if (x, y) == (int(px), int(py)):
        glow = math.sin(frame * 0.15) * 0.2 + 0.8
        return ('@', COLORS["player_glow"], glow)
    
    # Wall or floor
    if dungeon.is_wall(x, y):
        # Wall with depth shading
        return ('#', COLORS["wall"], 1.0)
    else:
        # Floor with subtle variation
        noise = (math.sin(x * 0.5) + math.cos(y * 0.5)) * 0.1 + 0.9
        base = COLORS["floor"]
        color = tuple(int(c * noise) for c in base)
        return ('·', color, 1.0)


def render_dungeon(draw, dungeon, player_pos, enemies, frame, camera_offset=(0, 0)):
    """Render the dungeon with isometric-style depth."""
    tile_size = 32
    offset_x = (WIDTH - dungeon.width * tile_size) // 2 + camera_offset[0]
    offset_y = (HEIGHT - dungeon.height * tile_size) // 2 + camera_offset[1]
    
    # Draw floor grid first
    for y in range(dungeon.height):
        for x in range(dungeon.width):
            if not dungeon.is_wall(x, y):
                screen_x = offset_x + x * tile_size
                screen_y = offset_y + y * tile_size
                
                # Distance from player for fog
                dist = math.sqrt((x - player_pos[0])**2 + (y - player_pos[1])**2)
                fog = max(0, min(1, 1 - dist / 6))
                
                if fog > 0.1:
                    base_color = COLORS["floor"]
                    lit = tuple(int(c * fog) for c in base_color)
                    draw.rectangle(
                        [screen_x, screen_y, screen_x + tile_size - 2, screen_y + tile_size - 2],
                        fill=lit
                    )
    
    # Draw walls and entities
    for y in range(dungeon.height):
        for x in range(dungeon.width):
            char, color, brightness = get_tile_char(x, y, dungeon, player_pos, enemies, frame)
            screen_x = offset_x + x * tile_size
            screen_y = offset_y + y * tile_size
            
            dist = math.sqrt((x - player_pos[0])**2 + (y - player_pos[1])**2)
            fog = max(0, min(1, 1 - dist / 5))
            
            if fog < 0.05:
                continue
            
            final_color = tuple(min(255, int(c * brightness * fog)) for c in color)
            
            if char == '#':
                # Wall with 3D effect
                draw.rectangle(
                    [screen_x, screen_y, screen_x + tile_size - 2, screen_y + tile_size - 2],
                    fill=final_color,
                    outline=COLORS["wall_highlight"]
                )
                # Top highlight for depth
                draw.line(
                    [(screen_x, screen_y), (screen_x + tile_size - 2, screen_y)],
                    fill=tuple(min(255, c + 20) for c in final_color),
                    width=2
                )
            elif char == 'E':
                # Enemy - pulsing square
                size = int(tile_size * 0.6 * brightness)
                margin = (tile_size - size) // 2
                draw.rectangle(
                    [screen_x + margin, screen_y + margin, 
                     screen_x + margin + size, screen_y + margin + size],
                    fill=final_color,
                    outline=COLORS["enemy_glow"]
                )
            elif char == '@':
                # Player - glowing circle
                size = int(tile_size * 0.5 * brightness)
                cx = screen_x + tile_size // 2
                cy = screen_y + tile_size // 2
                draw.ellipse(
                    [cx - size, cy - size, cx + size, cy + size],
                    fill=final_color,
                    outline=(255, 255, 255)
                )


def render_growth_text(draw, text, frame, center=(WIDTH//2, HEIGHT//2)):
    """Render the growing name above player."""
    try:
        # Try to load a font, fall back to default
        font_large = ImageFont.truetype("arial.ttf", 48)
        font_glow = ImageFont.truetype("arial.ttf", 52)
    except:
        font_large = ImageFont.load_default()
        font_glow = font_large
    
    # Glow effect
    glow_color = (*COLORS["player_glow"][:3], 100)
    for offset in range(3, 0, -1):
        alpha = int(50 / offset)
        glow = tuple(list(COLORS["player_glow"][:3]) + [alpha])
        draw.text(
            (center[0] - offset, center[1] - 80 - offset),
            text,
            font=font_glow,
            fill=glow
        )
    
    # Main text
    draw.text(
        (center[0], center[1] - 80),
        text,
        font=font_large,
        fill=COLORS["text"],
        anchor="mm"
    )


def render_title_reveal(draw, frame, progress_start, progress_end):
    """Render the final title reveal with particle effects."""
    progress = (frame - progress_start) / (progress_end - progress_start)
    progress = max(0, min(1, progress))
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 96)
        font_subtitle = ImageFont.truetype("arial.ttf", 24)
    except:
        font_title = ImageFont.load_default()
        font_subtitle = font_title
    
    # Particle explosion from center
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    if progress < 0.3:
        # Phase 1: Particles converging
        part_progress = progress / 0.3
        for i in range(20):
            angle = (i / 20) * 2 * math.pi
            radius = 300 * (1 - part_progress)
            px = center_x + math.cos(angle + frame * 0.05) * radius
            py = center_y + math.sin(angle + frame * 0.05) * radius
            size = int(4 * part_progress)
            if size > 0:
                draw.ellipse([px-size, py-size, px+size, py+size], 
                           fill=COLORS["accent"])
    
    # Title with glow buildup
    glow_intensity = min(1, progress * 2)
    for glow_layer in range(5, 0, -1):
        alpha = int(30 * glow_intensity / glow_layer)
        offset = glow_layer * 2
        glow_color = (*COLORS["player_glow"][:3], alpha)
        draw.text(
            (center_x, center_y + offset),
            "PYREELER",
            font=font_title,
            fill=glow_color,
            anchor="mm"
        )
    
    # Main title
    title_color = tuple(int(c * (0.5 + 0.5 * progress)) for c in COLORS["text"])
    draw.text(
        (center_x, center_y),
        "PYREELER",
        font=font_title,
        fill=title_color,
        anchor="mm"
    )
    
    # Subtitle fade in
    if progress > 0.5:
        sub_alpha = min(255, int((progress - 0.5) * 2 * 255))
        sub_color = (*COLORS["text"][:3], sub_alpha)
        draw.text(
            (center_x, center_y + 70),
            "code-generated films",
            font=font_subtitle,
            fill=sub_color[:3],
            anchor="mm"
        )


def render_frame(frame):
    """Render a single frame."""
    img = Image.new('RGB', (WIDTH, HEIGHT), COLORS["void"])
    draw = ImageDraw.Draw(img)
    
    # Initialize dungeon (deterministic)
    random.seed(42)
    dungeon = Dungeon()
    
    # Calculate player position based on frame (smooth movement through dungeon)
    t = frame / TOTAL_FRAMES
    
    # Movement path: start -> rooms -> end
    key_positions = [
        dungeon.start_pos,
        (dungeon.start_pos[0] - 4, dungeon.start_pos[1] - 3),
        (dungeon.start_pos[0] + 4, dungeon.start_pos[1] - 3),
        (dungeon.start_pos[0] - 4, dungeon.start_pos[1] + 3),
        (dungeon.start_pos[0] + 4, dungeon.start_pos[1] + 3),
        dungeon.end_pos
    ]
    
    # Interpolate between key positions
    pos_index = min(int(t * (len(key_positions) - 1)), len(key_positions) - 2)
    local_t = (t * (len(key_positions) - 1)) - pos_index
    
    p1 = key_positions[pos_index]
    p2 = key_positions[pos_index + 1]
    player_pos = (
        p1[0] + (p2[0] - p1[0]) * local_t,
        p1[1] + (p2[1] - p1[1]) * local_t
    )
    
    # Camera follows player
    camera_x = -int((player_pos[0] - dungeon.width / 2) * 32)
    camera_y = -int((player_pos[1] - dungeon.height / 2) * 32)
    
    # Determine growth phase
    growth_text = ""
    for start, end, text, _ in GROWTH_PHASES:
        if start <= frame < end:
            growth_text = text
            break
    
    # Render based on phase
    if frame < TITLE_REVEAL[0]:
        # Dungeon exploration phase
        render_dungeon(draw, dungeon, player_pos, dungeon.enemies, frame, (camera_x, camera_y))
        
        if growth_text:
            # Calculate text position in screen space
            text_x = WIDTH // 2 + camera_x + int(player_pos[0] * 32)
            text_y = HEIGHT // 2 + camera_y + int(player_pos[1] * 32)
            render_growth_text(draw, growth_text, frame, (text_x, text_y - 40))
    else:
        # Title reveal phase
        render_title_reveal(draw, frame, TITLE_REVEAL[0], TITLE_REVEAL[1])
    
    return img


# =============================================================================
# AUDIO GENERATION
# =============================================================================

def generate_audio(output_path: Path):
    """Generate complete audio track with voice."""
    sample_rate = 44100
    total_samples = int(DURATION * sample_rate)
    
    # Voice: "Py-Reeler" at PYREELER reveal
    voice_path = Path("temp_voice_pyreeler.mp3")
    render_edge_tts("Py-Reeler", voice_path, rate="-10%", pitch="-5Hz")
    
    # Load voice and position it at the right time
    import wave
    with wave.open(str(voice_path), 'rb') as wf:
        voice_samples = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        voice_samples = voice_samples.astype(np.float32) / 32767.0
    
    voice_start_sample = int((GROWTH_PHASES[5][0] / FPS) * sample_rate)  # Start of PYREELER phase
    
    # Generate stems
    stems = {}
    
    # Ambience: low drone
    t = np.linspace(0, DURATION, total_samples)
    ambience = np.sin(2 * np.pi * 60 * t) * 0.1
    ambience += np.sin(2 * np.pi * 63 * t) * 0.05  # Detuned for width
    stems['ambience'] = ambience.astype(np.float32)
    
    # Pulse: rhythmic heartbeat
    pulse = np.zeros(total_samples)
    beat_interval = int(sample_rate * 0.8)  # 75 BPM
    for i in range(0, total_samples, beat_interval):
        end = min(i + int(sample_rate * 0.1), total_samples)
        if end > i:
            beat_t = np.linspace(0, 0.1, end - i)
            pulse[i:end] = np.sin(2 * np.pi * 80 * beat_t) * np.exp(-10 * beat_t) * 0.3
    stems['pulse'] = pulse.astype(np.float32)
    
    # Impacts: level up sounds for each growth phase
    impacts = np.zeros(total_samples)
    for start, _, text, _ in GROWTH_PHASES:
        if text != "P":  # Skip first
            time_sec = start / FPS
            sample_idx = int(time_sec * sample_rate)
            # Short swell
            swell_len = int(0.3 * sample_rate)
            if sample_idx + swell_len < total_samples:
                swell_t = np.linspace(0, 0.3, swell_len)
                freq = 200 + len(text) * 50  # Higher pitch for longer words
                swell = np.sin(2 * np.pi * freq * swell_t) * np.exp(-3 * swell_t) * 0.2
                impacts[sample_idx:sample_idx+swell_len] += swell
    stems['impacts'] = impacts.astype(np.float32)
    
    # Voice stem
    voice_stem = np.zeros(total_samples)
    voice_end = min(voice_start_sample + len(voice_samples), total_samples)
    if voice_end > voice_start_sample:
        voice_stem[voice_start_sample:voice_end] = voice_samples[:voice_end-voice_start_sample] * 0.8
    stems['voice'] = voice_stem.astype(np.float32)
    
    # Mix
    final_mix = mix_stems(stems, gains={
        'ambience': 0.8,
        'pulse': 0.6,
        'impacts': 0.7,
        'voice': 1.0
    }, duck_voice=True)
    
    write_mono_wav(output_path, final_mix, sample_rate)
    
    # Cleanup temp
    voice_path.unlink(missing_ok=True)
    
    return output_path


# =============================================================================
# MAIN RENDER
# =============================================================================

def main():
    """Main entry point."""
    output_dir = Path("dungeon_emergence_output")
    output_dir.mkdir(exist_ok=True)
    
    # Get render runtime
    runtime = detect_render_runtime()
    print(f"Render runtime: {runtime}")
    
    # Generate audio first
    print("Generating audio...")
    audio_path = output_dir / "audio.wav"
    try:
        generate_audio(audio_path)
        print(f"Audio: {audio_path}")
    except Exception as e:
        print(f"Audio generation failed (edge-tts may not be installed): {e}")
        audio_path = None
    
    # Render frames
    print(f"Rendering {TOTAL_FRAMES} frames...")
    
    # Use FFmpeg for rendering
    ffmpeg_cmd = [
        runtime.ffmpeg_path,
        "-y",
        "-hide_banner",
        "-loglevel", "error",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
    ]
    
    if audio_path and audio_path.exists():
        ffmpeg_cmd.extend(["-i", str(audio_path)])
    
    ffmpeg_cmd.extend(list(runtime.video_args))
    ffmpeg_cmd.extend([
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_dir / "dungeon_emergence.mp4")
    ])
    
    process = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        for frame_idx in range(TOTAL_FRAMES):
            if frame_idx % 30 == 0:
                print(f"  Frame {frame_idx}/{TOTAL_FRAMES}")
            
            img = render_frame(frame_idx)
            process.stdin.write(img.tobytes())
        
        process.stdin.close()
        process.wait()
        
        if process.returncode == 0:
            print(f"\nDone! Output: {output_dir / 'dungeon_emergence.mp4'}")
        else:
            err = process.stderr.read().decode()
            print(f"FFmpeg error: {err}")
    
    except KeyboardInterrupt:
        process.terminate()
        raise


if __name__ == "__main__":
    main()
