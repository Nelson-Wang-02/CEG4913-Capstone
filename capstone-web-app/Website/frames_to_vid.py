import imageio
import os
from concurrent.futures import ThreadPoolExecutor


def clean_folder():
    """
    Cleans the folder after concatenating images

    """
    path = os.getcwd() + '\\Website\\animation\\MotionCapture_Data\\Animation Frames'
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        # If it's a .png file, delete it
        os.remove(item_path)

def read_image(filename):
    return imageio.imread(filename)

def png_to_mp4_multithreaded(input_folder, output_file, fps, num_threads=8):
    print("Buiding mp4 at " + str(fps) + " fps")
    """Converts PNG images to MP4 using imageio with multithreading and optimized encoding."""
    images = sorted(
        [os.path.join(input_folder, img) for img in os.listdir(input_folder) if img.endswith(".png")]
    )
    if not images:
        raise ValueError("No PNG images found in the specified folder.")

    # Use ThreadPoolExecutor to read images in parallel
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        frames = list(executor.map(read_image, images))

    writer = imageio.get_writer(
        output_file,
        fps=fps,
        codec='libx264',
        ffmpeg_params=[
            '-pix_fmt', 'yuv420p',
            '-preset', 'ultrafast',  # Add this line for faster encoding
        ]
    )

    for frame in frames:
        writer.append_data(frame)

    writer.close()
    clean_folder()
    print(f"Video saved to {output_file}")