import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat
import os
import subprocess
import shutil
import sys
import wave

# --- 3D Projection Engine ---

def get_rotation_matrix(rx, ry, rz):
    rot_x = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
    rot_y = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
    rot_z = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    return rot_z @ rot_y @ rot_x

def project_points(points, width, height, field_of_view=800, viewer_distance=6):
    z_eff = points[:, 2] + viewer_distance
    z_eff[z_eff < 0.1] = 0.1
    factor = field_of_view / z_eff
    x_2d = points[:, 0] * factor + width / 2
    y_2d = points[:, 1] * factor + height / 2
    return np.stack([x_2d, y_2d], axis=1), z_eff

# --- Utils: Perspective Transform (Homography) ---

def find_coeffs(pa, pb):
    """Calculates coefficients for PIL.PERSPECTIVE transform mapping pa to pb."""
    # pa: 4 source points [(x0,y0), (x1,y1), (x2,y2), (x3,y3)]
    # pb: 4 target points
    matrix = []
    for p1, p2 in zip(pa, pb):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])
    A = np.matrix(matrix, dtype=float)
    B = np.array(pb).reshape(8)
    res = np.linalg.solve(A, B)
    return np.array(res).reshape(8)

# --- Assets & Textures ---

def create_black_hole_texture(size=256):
    y, x = np.ogrid[-1:1:size*1j, -1:1:size*1j]
    dist = np.sqrt(x*x + y*y)
    alpha = np.zeros((size, size))
    # Event Horizon Glow
    alpha = np.clip(1.0 - dist, 0, 1) * 150 
    # Singular boundary
    horizon_mask = (dist > 0.3) & (dist < 0.5)
    alpha[horizon_mask] = 255 * (1.0 - np.abs(dist[horizon_mask] - 0.4) / 0.1)
    # Inner void
    alpha[dist < 0.35] = 0
    # Colors
    r = np.clip(alpha * 0.1, 0, 255)
    g = np.clip(alpha * 0.9, 0, 255)
    b = np.clip(alpha * 1.0, 0, 255)
    img_data = np.stack([r, g, b, alpha], axis=-1).astype(np.uint8)
    return Image.fromarray(img_data, mode="RGBA")

def create_cube():
    # Unit cube vertices
    vertices = np.array([
        [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
        [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
    ], dtype=float)
    # 6 faces (quads)
    faces = [
        (4, 5, 6, 7), # Front
        (1, 0, 3, 2), # Back
        (0, 4, 7, 3), # Left
        (5, 1, 2, 6), # Right
        (3, 7, 6, 2), # Top
        (0, 1, 5, 4)  # Bottom
    ]
    return vertices, faces

def clifford_attractor(count, a, b, c, d):
    x, y = 0.1, 0.1
    points = []
    for _ in range(count):
        xn = np.sin(a * y) + c * np.cos(a * x)
        yn = np.sin(b * x) + d * np.cos(b * y)
        z = np.sin(xn * yn) * 2.5
        points.append([xn * 6, yn * 6, z])
        x, y = xn, yn
    return np.array(points)

# --- Audio Synth ---

def fm_wave(duration, sr, carrier, modulator, index_env):
    t = np.linspace(0, duration, int(sr * duration), False)
    mod = index_env * np.sin(2 * np.pi * modulator * t)
    return np.sin(2 * np.pi * carrier * t + mod)

def generate_cosmic_audio(duration, sr=44100):
    t = np.linspace(0, duration, int(sr * duration), False)
    # Deep FM Drone
    index_env = 3.0 + 2.0 * np.sin(2 * np.pi * 0.15 * t)
    drone = fm_wave(duration, sr, 38, 38.2, index_env) * 0.4
    # Shimmer
    wind = np.random.normal(0, 1, len(t)) * ((np.sin(2 * np.pi * 0.05 * t) + 1) / 2) * 0.08
    # Bursts
    hits = np.zeros_like(t)
    for _ in range(10):
        start = np.random.randint(0, len(t)); duration_s = 0.6
        hit_len = int(sr * duration_s); end = min(start + hit_len, len(t)); actual_len = end - start
        hit_t = np.linspace(0, duration_s, hit_len, False)[:actual_len]
        hit_env = np.exp(-8 * hit_t) 
        hit = fm_wave(actual_len/sr, sr, 55, 55.5, 10.0)[:actual_len] * hit_env * 0.25
        hits[start:end] += hit
    mixed = np.clip(drone + wind + hits, -1.0, 1.0)
    return sr, np.int16(mixed * 32767)

# --- Rendering ---

def render_frame(frame_num, width, height, cloud, bh_texture, persistence_buffer, font, light_dir):
    t = frame_num * 0.045
    vertices, faces = create_cube()
    
    # Rotations
    rot_cube = get_rotation_matrix(t, t * 0.6, t * 0.2)
    rot_cloud = get_rotation_matrix(t * 0.12, t * 0.05, t * 0.18)
    
    rotated_vertices = vertices @ rot_cube.T
    rotated_cloud = cloud @ rot_cloud.T
    
    # Projections
    cube_2d, z_cube = project_points(rotated_vertices, width, height)
    cloud_2d, z_cloud = project_points(rotated_cloud, width, height)
    
    # Persistence
    if persistence_buffer is None:
        persistence_buffer = Image.new("RGBA", (width, height), (5, 5, 15, 255))
    
    particle_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(particle_layer)
    
    valid = (cloud_2d[:, 0] > 0) & (cloud_2d[:, 0] < width) & (cloud_2d[:, 1] > 0) & (cloud_2d[:, 1] < height)
    pts = cloud_2d[valid]
    depths = z_cloud[valid]
    for i in range(len(pts)):
        if i % 2 == 0:
            p = pts[i]; d = depths[i]
            alpha = int(max(5, 160 - d * 12))
            if alpha > 0: p_draw.point((p[0], p[1]), fill=(0, 200, 255, alpha))
            
    persistence_buffer = Image.blend(persistence_buffer, particle_layer, 0.45)
    frame = persistence_buffer.convert("RGBA")
    draw = ImageDraw.Draw(frame)
    
    # Depth Sort Faces
    face_depths = []
    for face in faces:
        z_avg = np.mean([rotated_vertices[v, 2] for v in face])
        face_depths.append((z_avg, face))
    face_depths.sort(key=lambda x: x[0], reverse=True)
    
    # Source Texture Corners
    src_pa = [(0, 0), (bh_texture.width, 0), (bh_texture.width, bh_texture.height), (0, bh_texture.height)]
    
    for z_avg, face in face_depths:
        v0, v1, v2 = rotated_vertices[face[0]], rotated_vertices[face[1]], rotated_vertices[face[2]]
        normal = np.cross(v1 - v0, v2 - v1)
        normal = normal / np.linalg.norm(normal)
        
        # Simple directional lighting (Light coming from front-top-right)
        intensity = np.dot(normal, light_dir)
        intensity = np.clip((intensity + 1.0) / 2.0, 0.1, 1.0) # Map [-1,1] to [0.1, 1.0]
        
        if normal[2] < 0: # Backface culling
            target_pb = [tuple(cube_2d[v]) for v in face]
            
            # Map texture using PERSPECTIVE transform
            coeffs = find_coeffs(src_pa, target_pb)
            warped = bh_texture.transform((width, height), Image.PERSPECTIVE, coeffs, Image.BILINEAR)
            
            # Apply shading: Multiply texture RGB by intensity
            if intensity < 1.0:
                r, g, b, a = warped.split()
                r = r.point(lambda i: i * intensity)
                g = g.point(lambda i: i * intensity)
                b = b.point(lambda i: i * intensity)
                warped = Image.merge("RGBA", (r, g, b, a))
            
            # Mask the warped texture to just the face polygon
            mask = Image.new("L", (width, height), 0)
            m_draw = ImageDraw.Draw(mask)
            m_draw.polygon(target_pb, fill=255)
            
            frame.paste(warped, (0, 0), mask)
            
            # Draw shaded outline
            draw.polygon(target_pb, outline=(0, int(255*intensity), int(200*intensity), 200))

    # Terminal
    draw = ImageDraw.Draw(frame)
    draw.text((40, 40), f">> SYSTEM_STATUS: SELF_HEALING_ACTIVE", font=font, fill=(0, 255, 150))
    draw.text((40, 70), f">> LIGHT_INTENSITY: {intensity:.2f}", font=font, fill=(0, 255, 150))
    
    return frame.convert("RGB"), persistence_buffer

# --- Self-Healing Engine ---

class SelfHealer:
    def __init__(self, width, height, font):
        self.width = width
        self.height = height
        self.font = font
        self.bh_texture = create_black_hole_texture(512)
        self.light_dir = np.array([0.5, 0.5, -0.5])
        self.light_dir = self.light_dir / np.linalg.norm(self.light_dir)
        
    def repair_and_render(self, target_path, seconds, fps):
        attempts = 0
        max_attempts = 5
        
        while attempts < max_attempts:
            attempts += 1
            print(f">> SELF-HEALING: Quality Audit Attempt {attempts}/{max_attempts}...")
            
            # Randomized Chaotic Parameters
            a = np.random.uniform(-2.5, -1.0)
            b = np.random.uniform(1.2, 2.5)
            c = np.random.uniform(0.5, 2.0)
            d = np.random.uniform(0.3, 1.5)
            
            cloud = clifford_attractor(15000, a, b, c, d)
            
            # Smoke test a few frames
            test_frame, _ = render_frame(1, self.width, self.height, cloud, self.bh_texture, None, self.font, self.light_dir)
            stats = ImageStat.Stat(test_frame)
            contrast = np.mean(stats.stddev)
            
            print(f"   [AUDIT] Contrast Index: {contrast:.2f}")
            
            if contrast > 10.0:
                print(">> REPAIR SUCCESSFUL: Parameters Stabilized.")
                self.perform_full_render(target_path, seconds, fps, cloud)
                return True
            else:
                print("   [WARNING] Low contrast/Boring frame. Re-randomizing phase...")
        
        print(">> CRITICAL FAILURE: Self-healing could not stabilize parameters.")
        return False

    def perform_full_render(self, video_output, seconds, fps, cloud):
        total_frames = seconds * fps
        output_dir = "experimental/cosmic_render_temp"
        if os.path.exists(output_dir): shutil.rmtree(output_dir)
        os.makedirs(output_dir)
        
        p_buffer = None
        print(f">> COMMENCING STABLE RENDER ({total_frames} frames)...")
        for i in range(total_frames):
            if i % 30 == 0: print(f"   [SYNC] {i}/{total_frames}")
            img, p_buffer = render_frame(i, self.width, self.height, cloud, self.bh_texture, p_buffer, self.font, self.light_dir)
            img.save(os.path.join(output_dir, f"frame_{i:03d}.png"))
            
        # Audio
        print(">> SYNTHESIZING FM AUDIO...")
        sr, audio = generate_cosmic_audio(seconds)
        audio_path = "experimental/temp_cosmic.wav"
        with wave.open(audio_path, 'wb') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
            wf.writeframes(audio.tobytes())
            
        print(">> FINAL ENCODING & MUXING...")
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", os.path.join(output_dir, "frame_%03d.png"),
            "-i", audio_path,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            video_output
        ]
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        shutil.rmtree(output_dir)
        os.remove(audio_path)
        print(f">> DONE: Cosmic Piece delivered to {video_output}")

if __name__ == "__main__":
    W, H = 1280, 720
    try:
        font = ImageFont.truetype(os.environ.get("PYREEL_FONT") or "DejaVuSansMono.ttf", 26)
    except:
        font = ImageFont.load_default()
        
    healer = SelfHealer(W, H, font)
    success = healer.repair_and_render("experimental/cosmic_self_healed.mp4", 10, 30)
    if not success:
        sys.exit(1)
