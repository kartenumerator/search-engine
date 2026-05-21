import urllib.request
import sys

try:
    # Set a small timeout so the check doesn't hang indefinitely
    response = urllib.request.urlopen('http://localhost:3333/health', timeout=3)
    if response.getcode() == 200:
        sys.exit(0)  # Healthy
    else:
        sys.exit(1)  # Unhealthy
except Exception:
    sys.exit(1)      # Unhealthy (connection refused, timeout, etc.)