# config.py
import os

def _str_to_bool(val: str) -> bool:
    """
    Helper to interpret string like "true", "yes", "1" as True.
    """
    return val.lower() in ("true", "yes", "1")

# 1) Fallback defaults for local development
DEFAULT_USE_CACHE = False
DEFAULT_CACHE_FQDN = "localhost:11211"

# 2) Read from environment variables if present
ENV_USE_CACHE = os.environ.get("USE_CACHE", str(DEFAULT_USE_CACHE))
ENV_CACHE_FQDN = os.environ.get("CACHE_FQDN", DEFAULT_CACHE_FQDN)

# 3) Actual config values used by the app
USE_CACHE = _str_to_bool(ENV_USE_CACHE)  # convert from string to bool
CACHE_FQDN = ENV_CACHE_FQDN

#environment:
#  - USE_CACHE=true
#  - CACHE_FQDN=meghacache.prod.ae-cache-prod.ms-df-cache.prod-gcp-uscentral1-1.gcp.us.walmart.net

#apiVersion: apps/v1
#kind: Deployment
#metadata:
#  name: your-app
#spec:
#  template:
#    spec:
#      containers:
#      - name: your-app-container
#        image: your-app-image
#        env:
#        - name: USE_CACHE
#          value: "true"
#        - name: CACHE_FQDN
#          value: "meghacache.prod.ae-cache-prod..."
