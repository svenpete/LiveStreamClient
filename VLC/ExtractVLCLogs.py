import re
import json


# Define a function to extract QoS metrics from the VLC logs
def extract_qos_metrics(log_content):
    metrics = {
        'Buffer Time Count': 0,
        'Buffer Deadlocks': 0,
        'Late Frames': 0,
        'Total Delay of Late Frames (ms)': 0,
        'Video Decoding Timeouts': 0,
        'Buffer Duration (ms)': 0,
        'Buffer Fill Time (ms)': 0,
        'Min Buffer Time (s)': 0,
        'Late Buffer Warnings': 0,
        'Video Start-up Time (ms)': 0  # We will fill this up later
    }

    # Count occurrences of buffering
    metrics['Buffer Time Count'] = len(re.findall(r'Stream buffering done', log_content))

    # Extract buffer deadlocks
    metrics['Prevented Buffer Deadlocks'] = log_content.count('buffer deadlock prevented')

    # Extract late frames and their delays
    late_frame_matches = re.findall(r'picture is too late to be displayed \(missing (\d+) ms\)', log_content)
    if late_frame_matches:
        metrics['Late Frames'] = len(late_frame_matches)
        metrics['Total Delay of Late Frames (ms)'] = sum([int(delay) for delay in late_frame_matches])

    # Extract video decoding timeouts
    metrics['Video Decoding Timeouts'] = log_content.count('pic_holder_wait timed out')

    # Extract buffer duration and fill times
    buffer_matches = re.findall(r'Stream buffering done \((\d+) ms in (\d+) ms\)', log_content)
    if buffer_matches:
        metrics['Buffer Duration (ms)'], metrics['Buffer Fill Time (ms)'] = map(int, buffer_matches[0])

    # Extract minimum buffer time for adaptive bitrate
    min_buffer_time_match = re.search(r'minBufferTime=(\d+)', log_content)
    if min_buffer_time_match:
        metrics['Min Buffer Time (s)'] = int(min_buffer_time_match.group(1))

    # Count late buffer warnings
    metrics['Late Buffer Warnings'] = log_content.count('buffer too late')

    return metrics


# Extract QoS metrics for each log
log_files = ["VLC_Log/vlc_log_0.txt", "VLC_Log/vlc_log_1.txt", "VLC_Log/vlc_log_2.txt", "VLC_Log/vlc_log_3.txt"]
qos_metrics_data = []

for log_file in log_files:
    with open(log_file, 'r', encoding='utf-8') as file:
        log_content = file.read()
        qos_metrics = extract_qos_metrics(log_content)
        qos_metrics_data.append(qos_metrics)

# Output as JSON
print(json.dumps(qos_metrics_data, indent=4))
