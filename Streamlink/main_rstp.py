import av
import matplotlib.pyplot as plt
import datetime
import os
import json

# Stream URL
LIVE_STREAM_URL_RTMP = 'rtmp://192.168.2.87:1935/DMA/brick'  # Change to your live stream URL
LIVE_STREAM_URL_RTSP = 'rtsp://192.168.2.87:1935/DMA/brick'
LIVE_STREAM_URL_MPEG = 'http://192.168.2.87:1935/DMA/brick/manifest.mpd'
LIVE_STREAM_URL_HLS = 'http://192.168.2.87:1935/DMA/brick/playlist.m3u8'

# Open the stream and record the start time
start_time = datetime.datetime.now()

# Replace with the path to your recorded .ts file
ts_file_path = 'output-file.ts'


input_container = av.open(LIVE_STREAM_URL_RTMP)
startup_time = None

# Initialize variables
timestamps = []
bitrates = []
frame_rates = []
packet_sizes = []
frame_window = []
WINDOW_SIZE = 30
previous_pts = None
jitters = []
packet_intervals = []
buffer_times = []
latencies = []

# Metrics for Bandwidth and Frame Loss Rate
frame_count = 0
lost_frames = 0

# Buffering related metrics
BUFFER_THRESHOLD = 5  # Threshold in seconds below which rebuffering might occur
buffer_health = 0  # Current buffer fill rate in seconds
prev_packet_time = None
last_buffer_health_check = start_time
rebuffering_count = 0
rebuffering_duration = datetime.timedelta()

# Limit the monitoring duration to 2 minutes
end_time = datetime.datetime.now() + datetime.timedelta(minutes=2)

for packet in input_container.demux():
    # Stop
    if datetime.datetime.now() > end_time:
        break

    # Measure startup time as the time until the first video packet is received
    if startup_time is None and packet.stream.type == 'video':
        startup_time = datetime.datetime.now() - start_time

    # Only process video packets
    if packet.stream.type != 'video':
        continue

    timestamp = packet.pts * packet.stream.time_base if packet.pts is not None else None



    # Frame count and lost frames for FLR
    frame_count += 1
    if previous_pts is not None and packet.pts is not None:
        pts_delta = packet.pts - previous_pts

        if pts_delta > 1:
            lost_frames += pts_delta - 1

    # Packet Size
    packet_sizes.append(packet.size)

    # Buffer Health Update
    elapsed_since_last_check = datetime.datetime.now() - last_buffer_health_check
    buffer_health -= elapsed_since_last_check.total_seconds()
    last_buffer_health_check = datetime.datetime.now()

    if packet.pts:
        buffer_health += packet.duration * packet.stream.time_base

    # Check for rebuffering events
    if buffer_health < BUFFER_THRESHOLD:
        rebuffering_count += 1
        rebuffer_duration = BUFFER_THRESHOLD - buffer_health
        rebuffering_duration += datetime.timedelta(seconds=rebuffer_duration)
        buffer_health = BUFFER_THRESHOLD

    if packet.pts is not None and previous_pts is not None:
        delta_pts = packet.pts - previous_pts
    else:
        delta_pts = None

    if delta_pts is not None and delta_pts != 0 and packet.stream.time_base != 0:
        frame_rate = 1 / (delta_pts * packet.stream.time_base)
        frame_rates.append(frame_rate)

        # Calculate jitter
        if prev_packet_time is not None and timestamp is not None:
            interval = timestamp - prev_packet_time
            jitters.append(interval)
        prev_packet_time = timestamp


    if all(p.pts is not None for p in frame_window) and len(frame_window) == WINDOW_SIZE:
        total_bits = sum(p.size * 8 for p in frame_window)
        duration = (frame_window[-1].pts - frame_window[0].pts) * packet.stream.time_base
        bitrate = total_bits / duration
        bitrates.append(bitrate)
        buffer_time = duration
        buffer_times.append(buffer_time)  # Hinzufügen zur Liste

    if timestamp is not None:
        timestamps.append(timestamp)

        # Calculate buffer time
    frame_window.append(packet)
    if len(frame_window) > WINDOW_SIZE:
        frame_window.pop(0)

    # Update the previous PTS
    previous_pts = packet.pts

    # Ensure lost_frames does not exceed frame_count
    lost_frames = min(lost_frames, frame_count)

    if packet.pts:
        expected_display_time = start_time + startup_time + datetime.timedelta(
            seconds=float(packet.pts * packet.stream.time_base))
        latency = datetime.datetime.now() - expected_display_time
        if latency.total_seconds() < 0:
            latency = latency * -1
        latencies.append(latency.total_seconds())

# Post-processing and metrics calculation
total_time = timestamps[-1] - timestamps[0] if timestamps else 1
bandwidth = float(sum(bitrates) / len(bitrates)) if bitrates else 0
flr = lost_frames / frame_count if frame_count >= 0 else 0

# Print metrics
print(f"Start-up Time: {startup_time.total_seconds():.2f} seconds")
print(f"Latency: {latency.total_seconds():.2f} seconds")
print(f"Buffer Health at end: {buffer_health:.2f} seconds")
print(f"Number of Rebuffering Events: {rebuffering_count}")
print(f"Total Rebuffering Duration: {rebuffering_duration.total_seconds():.2f} seconds")
print("Number of timestamps:", len(timestamps))
print("Number of bitrates:", len(bitrates))
print(f"Bandwidth: {bandwidth:.2f} bps")
print(f"Frame Loss Rate: {flr:.2%}")
print("Latencies:", latencies)
print("Bitrates:", bitrates)
print("Buffer Health Values:", buffer_times)
print("Jitter Values:", jitters)


# Saving all figures
current_time_str = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
directory_name = f"Results_{current_time_str}"
os.makedirs(directory_name, exist_ok=True)


# Create a dictionary with all metrics
metrics = {
    "Start-up Time": startup_time.total_seconds(),
    "Latency": latency.total_seconds(),
    "Buffer Health at end": buffer_health,
    "Number of Rebuffering Events": rebuffering_count,
    "Total Rebuffering Duration": rebuffering_duration.total_seconds(),
    "Number of timestamps": len(timestamps),
    "Number of bitrates": len(bitrates),
    "Bandwidth": bandwidth,
    "Frame Loss Rate": flr,
    "Latencies": latencies,
    "Timestamps": [float(value) for value in timestamps],
    "Bitrate Values": [float(value) for value in bitrates],
    "Buffer Health Values": [float(value) for value in buffer_times],
    "Jitter Values": [float(value) for value in jitters]
}

# Save metrics to JSON
with open(os.path.join(directory_name, 'metrics.json'), 'w') as json_file:
    json.dump(metrics, json_file, indent=4)


import os

def plot_and_save_data(x_values, y_values, x_label, y_label, title, filename, directory):
    plt.figure()
    plt.plot(x_values, y_values)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    plt.savefig(os.path.join(directory, filename))

# Example usage for plotting Bitrate
min_len = min(len(timestamps), len(bitrates))
plot_and_save_data(timestamps[:min_len], bitrates[:min_len], 'Time (s)', 'Bitrate (bps)', 'Bitrate Over Time', 'bitrate.png', directory_name)

# Example usage for plotting Jitter
min_len = min(len(timestamps), len(jitters))
plot_and_save_data(timestamps[:min_len], jitters[:min_len], 'Time (s)', 'Jitter (s)', 'Jitter Over Time', 'jitter.png', directory_name)

# Example usage for plotting Latency
min_len = min(len(timestamps), len(latencies))
plot_and_save_data(timestamps[:min_len], latencies[:min_len], 'Time (s)', 'Latency (s)', 'Latency Over Time', 'latency.png', directory_name)

# Example usage for plotting Buffer Health
min_len = min(len(timestamps), len(buffer_times))
plot_and_save_data(timestamps[:min_len], buffer_times[:min_len], 'Time (s)', 'Buffer Health (s)', 'Buffer Health Over Time', 'buffer_health.png', directory_name)

