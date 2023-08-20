import time
import cv2
from flask import Flask, Response, request
from prometheus_flask_exporter import PrometheusMetrics
import logging
import matplotlib.pyplot as plt
import json
import psutil


app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Static information as metric
metrics.info('app_info', 'Application info', version='1.0.3')

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

frame_processing_times = []  # Liste zur Speicherung der Bufferzeiten
bitrates = []
cpu_usages = []
memory_usages = []



@app.before_request
def log_request_info():
    logger.info('Headers: %s', request.headers)
    logger.info('Body: %s', request.get_data())

@app.route('/')
def index():
    """Homepage - mainly for checking application health."""
    return "Flask Video Streamer with Metrics!", 200

def generate_frames(video_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Fehler: Video konnte nicht geöffnet werden.")
        return

    while True:
        start_time = time.time()

        ret, frame = cap.read()
        if not ret:
            break
        ret, jpeg = cv2.imencode('.jpg', frame)
        frame = jpeg.tobytes()

        end_time = time.time()
        processing_time = end_time - start_time
        frame_processing_times.append(processing_time)

        # Bitrate in bits pro Sekunde berechnen (8 Bits pro Byte)
        bitrate = (len(frame) * 8) / processing_time
        bitrates.append(bitrate)

        # CPU- und Speicher-Auslastung erfassen
        cpu_usage = psutil.cpu_percent(interval=0.1)  # % der CPU-Auslastung
        memory_info = psutil.virtual_memory()  # Speicherinformationen
        memory_usage = memory_info.percent  # % der Speicherauslastung

        cpu_usages.append(cpu_usage)
        memory_usages.append(memory_usage)


        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    # Wenn das Video zu Ende ist, rufen Sie die Funktion auf, um das Diagramm zu zeichnen
    plot_processing_times()
    plot_bitrates()
    plot_cpu_usage()
    plot_memory_usage()
    save_to_json()
def plot_processing_times():
    plt.figure(figsize=(10, 5))
    plt.plot(frame_processing_times, marker='', linestyle='-', linewidth=1)  # marker='' und linewidth=1
    plt.title("Bufferzeiten für Videoframes")
    plt.xlabel("Frame-Index")
    plt.ylabel("Bufferzeit (in Sekunden)")
    plt.grid(True)
    plt.savefig("buffer_times_plot.png")
    plt.close()

def plot_bitrates():
    plt.figure(figsize=(10, 5))
    plt.plot(bitrates, marker='', linestyle='-', linewidth=1)  # marker='' und linewidth=1
    plt.title("Bitrate für Videoframes")
    plt.xlabel("Frame-Index")
    plt.ylabel("Bitrate (Bits pro Sekunde)")
    plt.grid(True)
    plt.savefig("bitrate_plot.png")
    plt.close()

def plot_cpu_usage():
    plt.figure(figsize=(10, 5))
    plt.plot(cpu_usages, marker='', linestyle='-', linewidth=1)
    plt.title("CPU-Auslastung während des Streamens")
    plt.xlabel("Frame-Index")
    plt.ylabel("CPU-Auslastung (%)")
    plt.grid(True)
    plt.savefig("cpu_usage_plot.png")
    plt.close()

def plot_memory_usage():
    plt.figure(figsize=(10, 5))
    plt.plot(memory_usages, marker='', linestyle='-', linewidth=1)
    plt.title("Speicherauslastung während des Streamens")
    plt.xlabel("Frame-Index")
    plt.ylabel("Speicherauslastung (%)")
    plt.grid(True)
    plt.savefig("memory_usage_plot.png")
    plt.close()


def save_to_json():
    data = {
        'frame_processing_times': frame_processing_times,
        'bitrates': bitrates,
        'cpu_usages': cpu_usages,
        'memory_usages': memory_usages
    }

    with open("video_metrics.json", "w") as f:
        json.dump(data, f)


@app.route('/video_feed')
def video_feed():
    video_path = '../merged_output.mp4'  # Ersetzen Sie durch den Pfad zu Ihrer Videodatei.
    return Response(generate_frames(video_path),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='localhost', port=8900)
