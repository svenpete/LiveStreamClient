from moviepy.editor import VideoFileClip, concatenate_videoclips

def merge_videos(video_paths, output_path):
    clips = [VideoFileClip(video) for video in video_paths]
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(output_path, codec="libx264")

if __name__ == "__main__":
    videos_to_merge = [r"../142579 (Original).mp4", r"../ink_-_67358 (1080p).mp4"]
    output_video = "merged_output.mp4"
    merge_videos(videos_to_merge, output_video)
