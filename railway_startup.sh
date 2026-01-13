#!/bin/bash
# Start script for Railway deployment
# Runs both FastAPI server and Celery worker

set -e

echo "=========================================="
echo "Starting QuantAgentic API services..."
echo "=========================================="

ENV_NAME_LOWER="${RAILWAY_ENVIRONMENT_NAME,,}"

# SANITIZE HOSTNAME: Replace underscores (_) with hyphens (-) for DNS compatibility
# Tailscale will fail if the hostname contains underscores.
SAFE_HOSTNAME="${ENV_NAME_LOWER//_/-}"

# Check if "pr-" is IN the name (start, middle, or end)
if [[ "$ENV_NAME_LOWER" == *"pr-"* ]]; then
	echo "NOTICE: PR Environment detected ($RAILWAY_ENVIRONMENT_NAME)"
	export IS_PR_ENV="true"
	HOSTNAME="$SAFE_HOSTNAME"
else
	echo "NOTICE: Production/Standard Environment detected ($RAILWAY_ENVIRONMENT_NAME)"
	export IS_PR_ENV="false"
	HOSTNAME="$SAFE_HOSTNAME"
fi

# --- TAILSCALE "NO-DOCKERFILE" SETUP START ---
if [ -n "$TAILSCALE_AUTH_KEY" ]; then
	echo "Tailscale: Installing standalone binaries..."
	
	TS_VERSION="1.92.5"
	curl -fsSL "https://pkgs.tailscale.com/stable/tailscale_${TS_VERSION}_amd64.tgz" -o tailscale.tgz
	tar xzf tailscale.tgz
	
	mv "tailscale_${TS_VERSION}_amd64"/tailscale .
	mv "tailscale_${TS_VERSION}_amd64"/tailscaled .
	chmod +x tailscale tailscaled
	export PATH=$PATH:$(pwd)

	mkdir -p /var/run/tailscale
	mkdir -p /var/lib/tailscale

	echo "Tailscale: Starting daemon..."
	./tailscaled --tun=userspace-networking --socket=/var/run/tailscale/tailscaled.sock --state=/var/lib/tailscale/tailscaled.state &
	
	sleep 3
	
	echo "Tailscale: Authenticating..."
	# Connect using the sanitized SAFE_HOSTNAME
	./tailscale up --authkey="${TAILSCALE_AUTH_KEY}" --hostname="${HOSTNAME}"
	
	echo "Tailscale is online."
else
	echo "WARNING: TAILSCALE_AUTH_KEY not set. Skipping Tailscale setup."
fi
# --- TAILSCALE SETUP END ---

# Seed counties if SEED_COUNTIES is not set to "false"
if [ "${SEED_COUNTIES:-true}" != "false" ]; then
	echo "Seeding counties data..."
	if python3 app/seeds/seed_counties.py; then
		echo "County seeding completed successfully"
	else
		echo "WARNING: County seeding failed, but continuing startup..."
		echo "Services will start, but drought sync may not work without county data"
	fi
else
	echo "Skipping county seeding (SEED_COUNTIES=false)"
fi

echo "=========================================="

echo "Starting Celery worker with beat scheduler..."
celery -A app.celery_app worker --beat --loglevel=info --logfile=/dev/stdout &
CELERY_PID=$!

cleanup() {
	echo "Shutting down services..."
	kill $CELERY_PID 2>/dev/null || true
	pkill tailscaled || true
	exit
}

trap cleanup SIGTERM SIGINT EXIT

sleep 3

if ! kill -0 $CELERY_PID 2>/dev/null; then
	echo "ERROR: Celery worker failed to start!"
	exit 1
fi

echo "Celery worker started (PID: $CELERY_PID)"
echo "Starting FastAPI server..."
echo "=========================================="

exec hypercorn main:app --bind "[::]:${PORT:-8000}"