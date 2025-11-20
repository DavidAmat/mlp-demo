FROM python:3.10-slim-bullseye

WORKDIR /app

# Copy app code
COPY main.py /app/main.py
COPY bin/entrypoint /usr/local/bin/entrypoint

# Ensure entrypoint is executable
RUN chmod +x /usr/local/bin/entrypoint

# (Optional but nice) Don't buffer Python output
ENV PYTHONUNBUFFERED=1

# Default entrypoint: our tiny dispatcher
ENTRYPOINT ["entrypoint"]
