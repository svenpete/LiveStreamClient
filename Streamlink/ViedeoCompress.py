import subprocess
import json
import os

# Pfad zu VLC und Zielverzeichnis
VLC_PATH = "/Applications/VLC.app/Contents/MacOS/VLC"
TARGET_DIR = "/Users/sven/PycharmProjects/LiveStreamClient/Streamlink/CompressedVideos"

# Wenn das Verzeichnis nicht existiert, erstelle es
if not os.path.exists(TARGET_DIR):
    os.makedirs(TARGET_DIR)

# Aufnahmezeit in Sekunden
RECORDING_TIME = 120  # 2 Minuten


def record_stream(url, protocol, output_file):
    """
    Verwendet VLC, um einen Stream für eine bestimmte Dauer aufzunehmen.

    Parameters:
    - url: Die URL des Streams
    - protocol: Der Streaming-Protokollname (RTMP, RTSP, MPEG-DASH, HLS)
    - output_file: Pfad zur Ausgabedatei
    """
    protocol_dir = os.path.join(TARGET_DIR, protocol)
    if not os.path.exists(protocol_dir):
        os.makedirs(protocol_dir)

    cmd = [
        VLC_PATH,
        url,
        '--sout=file/ts:' + os.path.join(protocol_dir, output_file),
        '--run-time=' + str(RECORDING_TIME),
        'vlc://quit'
    ]
    subprocess.run(cmd)


def analyze_video_quality(original, protocol, compressed):
    """
    Analysiert die Videoqualität zwischen dem Original und der komprimierten Datei mithilfe von ffmpeg.

    Parameters:
    - original: Pfad zur Originalvideodatei
    - protocol: Der Streaming-Protokollname (RTMP, RTSP, MPEG-DASH, HLS)
    - compressed: Pfad zur komprimierten Videodatei

    Returns:
    - VMAF score
    """
    protocol_dir = os.path.join(TARGET_DIR, protocol)
    log_file = os.path.join(protocol_dir, "vmaf_log.json")
    cmd = [
        'ffmpeg',
        '-i', original,
        '-i', compressed,
        '-filter_complex',
        'libvmaf=model_path=/Users/sven/PycharmProjects/LiveStreamClient/vmaf/model/vmaf_v0.6.1.json:psnr=true:log_path=' + log_file,
        '-f', 'null', '-'
    ]
    subprocess.run(cmd)

    with open(log_file, 'r') as file:
        data = json.load(file)
        return data['VMAF score']


# URLs und entsprechende Ausgabedateien definieren
streams = {
    'rtmp://192.168.2.87:1935/DMA/brick': ('RTMP', 'brick_rtmp_compressed.mp4'),
    'rtsp://192.168.2.87:1935/DMA/brick': ('RTSP', 'brick_rtsp_compressed.mp4'),
    'http://192.168.2.87:1935/DMA/brick/manifest.mpd': ('MPEG-DASH', 'brick_mpd_compressed.mp4'),
    'http://192.168.2.87:1935/DMA/brick/playlist.m3u8': ('HLS', 'brick_m3u8_compressed.mp4')
}

results = {}

# Für jede URL den Stream aufnehmen und Videoqualität analysieren
for url, (protocol, output) in streams.items():
    record_stream(url, protocol, output)
    vmaf_score = analyze_video_quality('/Users/sven/PycharmProjects/LiveStreamClient/Streamlink/merged_output.mp4', protocol,
                                       os.path.join(TARGET_DIR, protocol, output))
    results[url] = vmaf_score

    # Ergebnisse in JSON-Datei speichern
    with open(os.path.join(TARGET_DIR, protocol, 'vmaf_results.json'), 'w') as json_file:
        json.dump({url: vmaf_score}, json_file, indent=4)
