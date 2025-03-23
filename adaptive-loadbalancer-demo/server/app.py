from flask import Flask, jsonify
import random
import os

app = Flask(__name__)
# Get a unique identifier for this server instance from an environment variable.
server_id = os.environ.get('SERVER_ID', 'unknown')

@app.route('/')
def index():
    # Simulate CPU and Memory idle percentages (random values for demonstration).
    cpu_idle = random.randint(10, 90)
    mem_idle = random.randint(10, 90)
    return jsonify(server=server_id, cpu_idle=cpu_idle, mem_idle=mem_idle)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
