"""Small Flask web app for the Docker homework (week 3)."""

import os
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify

app = Flask(__name__)
STARTED_AT = datetime.now(timezone.utc)


@app.get("/")
def index():
    return jsonify(
        message="Hello from DevOps week 3",
        hostname=socket.gethostname(),
        user=os.getenv("USER", "unknown"),
    )


@app.get("/healthz")
def healthz():
    uptime = (datetime.now(timezone.utc) - STARTED_AT).total_seconds()
    return jsonify(status="ok", uptime_seconds=round(uptime, 1))


if __name__ == "__main__":
    # Local development only; the container runs gunicorn instead.
    app.run(host="0.0.0.0", port=8000)
