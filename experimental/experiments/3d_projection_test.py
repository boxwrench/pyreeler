import numpy as np
from PIL import Image, ImageDraw

def get_rotation_matrix(rx, ry, rz):
    """Returns a 3D rotation matrix."""
    # Rotation X
    rot_x = np.array([
        [1, 0, 0],
        [0, np.cos(rx), -np.sin(rx)],
        [0, np.sin(rx), np.cos(rx)]
    ])
    # Rotation Y
    rot_y = np.array([
        [np.cos(ry), 0, np.sin(ry)],
        [0, 1, 0],
        [-np.sin(ry), 0, np.cos(ry)]
    ])
    # Rotation Z
    rot_z = np.array([
        [np.cos(rz), -np.sin(rz), 0],
        [np.sin(rz), np.cos(rz), 0],
        [0, 0, 1]
    ])
    return rot_z @ rot_y @ rot_x

def project_points(points, width, height, field_of_view=500, viewer_distance=4):
    """Projects 3D points to 2D screen coordinates."""
    # points is (N, 3)
    # Simple perspective: screen_x = x * fov / (z + distance)
    z_eff = points[:, 2] + viewer_distance
    
    # Avoid division by zero
    z_eff[z_eff < 0.1] = 0.1
    
    factor = field_of_view / z_eff
    
    x_2d = points[:, 0] * factor + width / 2
    y_2d = points[:, 1] * factor + height / 2
    
    return np.stack([x_2d, y_2d], axis=1)

def create_cube_points():
    """Returns the 8 vertices and 12 edges of a unit cube."""
    vertices = np.array([
        [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
        [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
    ], dtype=float)
    
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0), # Back face
        (4, 5), (5, 6), (6, 7), (7, 4), # Front face
        (0, 4), (1, 5), (2, 6), (3, 7)  # Connecting edges
    ]
    return vertices, edges

def render_frame(frame_num, width, height):
    """Renders a single frame of a rotating 3D cube."""
    t = frame_num * 0.05
    vertices, edges = create_cube_points()
    
    # Apply rotation
    rot = get_rotation_matrix(t, t * 0.7, t * 0.3)
    rotated_vertices = vertices @ rot.T
    
    # Project to 2D
    points_2d = project_points(rotated_vertices, width, height)
    
    # Draw using PIL
    img = Image.new("RGB", (width, height), (10, 10, 15)) # Dark blue-black background
    draw = ImageDraw.Draw(img)
    
    # Draw edges
    for edge in edges:
        p1 = tuple(points_2d[edge[0]])
        p2 = tuple(points_2d[edge[1]])
        
        # Color based on depth (simple fog effect)
        z_avg = (rotated_vertices[edge[0], 2] + rotated_vertices[edge[1], 2]) / 2
        brightness = int(max(50, 255 * (1 - (z_avg + 2) / 4)))
        color = (brightness, brightness, int(brightness * 1.2))
        
        draw.line([p1, p2], fill=color, width=2)
        
    # Draw vertices as small glowing dots
    for p in points_2d:
        r = 3
        draw.ellipse([p[0]-r, p[1]-r, p[0]+r, p[1]+r], fill=(200, 255, 255))
        
    return img

if __name__ == "__main__":
    import os
    import subprocess
    import shutil
    
    # Get the directory of the current script
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
    
    W, H = 1280, 720 # HD resolution
    FPS = 30
    SECONDS = 10
    TOTAL_FRAMES = FPS * SECONDS
    
    # Define paths relative to the repo root
    output_dir = os.path.join(REPO_ROOT, "experimental", "3d_test_frames")
    video_output = os.path.join(REPO_ROOT, "experimental", "3d_cube_10s.mp4")
    
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Rendering {TOTAL_FRAMES} frames ({SECONDS}s) at {W}x{H}...")
    for i in range(TOTAL_FRAMES):
        if i % 30 == 0:
            print(f"  Progress: {i}/{TOTAL_FRAMES} frames...")
        frame = render_frame(i, W, H)
        frame.save(os.path.join(output_dir, f"frame_{i:03d}.png"))
    
    print(f"Stitching video to {video_output}...")
    
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(output_dir, "frame_%03d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        video_output
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        print(f"Success! Video created: {video_output}")
        # Clean up frames to save space
        shutil.rmtree(output_dir)
        print("Cleaned up temporary frame files.")
    except subprocess.CalledProcessError as e:
        print(f"Error during FFmpeg stitching: {e.stderr.decode()}")
    except FileNotFoundError:
        print("Error: FFmpeg not found in PATH. Please install FFmpeg to create the video.")
