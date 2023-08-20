import json
import subprocess
import time
import os
import re
# # define stream url
# LIVE_STREAM_URLS = [
#     'rtmp://192.168.2.87:1935/DMA/brick',
#     'rtsp://192.168.2.87:1935/DMA/brick',
#     'http://192.168.2.87:1935/DMA/brick/manifest.mpd',
#     'http://192.168.2.87:1935/DMA/brick/playlist.m3u8'
# ]
#
# # path to vlc
# VLC_PATH = "/Applications/VLC.app/Contents/MacOS/VLC"
#
# # path for logs
# TARGET_DIR = "/Users/sven/PycharmProjects/LiveStreamClient"
#
# # stream every url one by one
# for idx, url in enumerate(LIVE_STREAM_URLS):
#     log_file_path = os.path.join(TARGET_DIR, f"vlc_log_{idx}.txt")
#     cmd = [VLC_PATH, "-vvv", url, "--file-logging", f"--logfile={log_file_path}", "--run-time=120"]
#     process = subprocess.Popen(cmd)
#
#     # for viedeo duration
#     time.sleep(120)
#
#     #stop vlc
#     process.terminate()



# Define a function to extract QoS metrics from the VLC logs
def extract_qos_metrics(log_content):
    metrics = {
        'Buffer Time (ms)': 0,
        'Buffer Deadlocks': 0,
        'Late Frames': 0,
        'Total Delay of Late Frames (ms)': 0,
        'Video Decoding Timeouts': 0
    }

    # Extract buffer time
    buffer_time_matches = re.findall(r'Buffering (\d+) ms', log_content)
    if buffer_time_matches:
        metrics['Buffer Time (ms)'] = sum([int(time) for time in buffer_time_matches])

    # Extract buffer deadlocks
    metrics['Buffer Deadlocks'] = log_content.count('buffer deadlock prevented')

    # Extract late frames and their delays
    late_frame_matches = re.findall(r'picture is too late to be displayed \(missing (\d+) ms\)', log_content)
    if late_frame_matches:
        metrics['Late Frames'] = len(late_frame_matches)
        metrics['Total Delay of Late Frames (ms)'] = sum([int(delay) for delay in late_frame_matches])

    # Extract video decoding timeouts
    metrics['Video Decoding Timeouts'] = log_content.count('pic_holder_wait timed out')

    return metrics

# Extract QoS metrics for each log
log_files = ["vlc_log_0.txt", "vlc_log_1.txt", "vlc_log_2.txt", "vlc_log_3.txt"]
qos_metrics_data = []

for log_file in log_files:
    with open(log_file, 'r', encoding='utf-8') as file:
        log_content = file.read()
        qos_metrics = extract_qos_metrics(log_content)
        qos_metrics_data.append(qos_metrics)

# Output as JSON
print(json.dumps(qos_metrics_data, indent=4))
