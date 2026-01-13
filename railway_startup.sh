#!/bin/bash
# Start script for Railway deployment
# Runs both FastAPI server and Celery worker

set -e

echo "=========================================="
echo "Starting QuantAgentic API services..."
echo "=========================================="

# --- TAILSCALE "NO-DOCKERFILE" SETUP START ---
if [ -n "$TAILSCALE_AUTH_KEY" ]; then
	echo "Tailscale: Installing standalone binaries..."
	
	# 1. Download and extract the static binaries (prevents package manager errors)
	# We use a static version to ensure stability. You can update the version number if needed.
	TS_VERSION="1.70.0"
	curl -fsSL "https://pkgs.tailscale.com/stable/tailscale_${TS_VERSION}_amd64.tgz" -o tailscale.tgz
	tar xzf tailscale.tgz
	
	# 2. Move binaries to a location in your path (or use them directly)
	# We move them to the current directory for simplicity and add to path
	mv "tailscale_${TS_VERSION}_amd64"/tailscale .
	mv "tailscale_${TS_VERSION}_amd64"/tailscaled .
	chmod +x tailscale tailscaled
	export PATH=$PATH:$(pwd)

	# 3. Create the state directory (crucial for "tun" mode)
	mkdir -p /var/run/tailscale
	mkdir -p /var/lib/tailscale

	echo "Tailscale: Starting daemon..."
	# 4. Start the daemon in userspace mode
	./tailscaled --tun=userspace-networking --socket=/var/run/tailscale/tailscaled.sock --state=/var/lib/tailscale/tailscaled.state &
	
	# 5. Wait for daemon to initialize
	sleep 3
	
	echo "Tailscale: Authenticating..."
	# 6. Connect to your tailnet
	./tailscale up --authkey="${TAILSCALE_AUTH_KEY}" --hostname="railway-app"
	
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

# Start Celery worker with beat in the background
echo "Starting Celery worker with beat scheduler..."
celery -A app.celery_app worker --beat --loglevel=info --logfile=/dev/stdout &
CELERY_PID=$!

# Function to cleanup on exit
cleanup() {
	echo "Shutting down services..."
	kill $CELERY_PID 2>/dev/null || true
	# Kill tailscaled if we started it
	pkill tailscaled || true
	exit
}

# Set trap to cleanup on script exit
trap cleanup SIGTERM SIGINT EXIT

# Wait a moment for Celery to start
sleep 3

if ! kill -0 $CELERY_PID 2>/dev/null; then
	echo "ERROR: Celery worker failed to start!"
	exit 1
fi

echo "Celery worker started (PID: $CELERY_PID)"
echo "Starting FastAPI server..."
echo "=========================================="

exec hypercorn main:app --bind "[::]:${PORT:-8000}"