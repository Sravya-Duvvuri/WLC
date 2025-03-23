# server.py
from flask import Flask, jsonify
import psutil

app = Flask(__name__)

@app.route('/metrics')
def metrics():
    # Get current CPU idle percentage (approximation)
    cpu_idle = 100 - psutil.cpu_percent(interval=0.5)
    # Get available memory percentage
    mem = psutil.virtual_memory()
    memory_idle = mem.available * 100 / mem.total
    return jsonify(cpu_idle=cpu_idle, memory_idle=memory_idle)

if __name__ == '__main__':
    # Listen on all interfaces on port 5000
    app.run(host='0.0.0.0', port=5000)
