
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    PORT=5000 \
    BIND_HOST=0.0.0.0

WORKDIR /app

# System deps (kept minimal). Add libs here if build of any dependency requires them.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . /app

# Create non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 5000

# Use Gunicorn with eventlet worker for production-grade serving of Socket.IO
# Note: `wsgi:application` exposes the Socket.IO-wrapped WSGI app.
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "wsgi:application", "-b", "0.0.0.0:5000", "--log-level", "info"]
