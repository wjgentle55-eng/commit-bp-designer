# BP Workflow Studio, hosted: the page plus the read-only Pull from Workday server.
# Set STUDIO_PUBLIC_URL and STUDIO_ACCESS_CODE (12+ characters) in the host's environment settings.
FROM python:3.12-slim
WORKDIR /app
COPY tools/wd_pull/requirements.txt tools/wd_pull/requirements.txt
RUN pip install --no-cache-dir -r tools/wd_pull/requirements.txt
COPY index.html ./
COPY assets ./assets
COPY designs ./designs
COPY tools/wd_pull/pull_bp_definitions.py tools/wd_pull/studio_server.py tools/wd_pull/
ENV PYTHONUNBUFFERED=1
EXPOSE 8765
CMD ["sh", "-c", "python tools/wd_pull/studio_server.py --host 0.0.0.0 --port ${PORT:-8765}"]
