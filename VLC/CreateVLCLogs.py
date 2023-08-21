import json
import subprocess
import time
import os
import re
# define stream url
LIVE_STREAM_URLS = [
    'rtmp://192.168.2.87:1935/DMA/brick',
    'rtsp://192.168.2.87:1935/DMA/brick',
    'http://192.168.2.87:1935/DMA/brick/manifest.mpd',
    'http://192.168.2.87:1935/DMA/brick/playlist.m3u8'
]

# path to vlc
VLC_PATH = "/Applications/VLC.app/Contents/MacOS/VLC"

# # path for logs
TARGET_DIR = "/Users/sven/PycharmProjects/LiveStreamClient/VLC_Log"

# stream every url one by one
for idx, url in enumerate(LIVE_STREAM_URLS):
    log_file_path = os.path.join(TARGET_DIR, f"vlc_log_{idx}.txt")
    cmd = [VLC_PATH, "-vvv", url, "--file-logging", f"--logfile={log_file_path}", "--run-time=120"]
    process = subprocess.Popen(cmd)

    # for viedeo duration
    time.sleep(120)

    # stop vlc
    process.terminate()
