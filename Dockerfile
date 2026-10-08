FROM python:3.12-slim

# Lambda Web Adapter: lets this same image run on AWS Lambda. It is a Lambda
# extension, so it's inert on any other host (Docker, ECS, Lightsail...).
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:1.1.0 /lambda-adapter /opt/extensions/lambda-adapter

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    BOYD_OUTPUT_DIR=/tmp/output \
    # Trust X-Forwarded-* from the front door (Lambda Function URL / load balancer) so
    # request URLs are https. Narrow this if the container is directly exposed.
    FORWARDED_ALLOW_IPS=* \
    AWS_LWA_PORT=8000 \
    AWS_LWA_READINESS_CHECK_PATH=/health

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY templates/ templates/
COPY assets/ assets/

RUN useradd --create-home --uid 1000 app && mkdir -p /tmp/output && chown app /tmp/output
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/health', timeout=4)"

CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --proxy-headers"]
