import os
import moviepy.video.io.ImageSequenceClip
from datetime import datetime


def clean_folder(path):
    """
    Cleans the folder after concatenating images

    """
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        # If it's a .png file, delete it
        if item_path.endswith('.png'):
            os.remove(item_path)

def build_video_from_frames(fps):
    image_folder='.\\Animation Frames'
    image_files = [os.path.join(image_folder,img)
                    for img in os.listdir(image_folder)
                    if img.endswith(".png")]
    clip = moviepy.video.io.ImageSequenceClip.ImageSequenceClip(image_files, fps=fps)
    time_now = datetime.now().strftime("%Y%m%d_%H%M%S") 
    clip.write_videofile(f'.\\Animation Results\\animation_{time_now}_.mp4')
    clean_folder(image_folder)

#if __name__ == "__main__":
#    build_video_from_frames(fps= 30)