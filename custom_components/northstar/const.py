"""Constants for the NorthStar Polestar integration."""

DOMAIN = "northstar"

# Configuration
CONF_API_URL = "api_url"
DEFAULT_API_URL = "http://NorthS-North-gSKdeBKDKYCa-509940918.eu-west-1.elb.amazonaws.com"

# Update intervals
DEFAULT_UPDATE_INTERVAL = 900  # 15 minutes
MIN_UPDATE_INTERVAL = 300  # 5 minutes
MAX_UPDATE_INTERVAL = 3600  # 1 hour
STREAMING_UPDATE_INTERVAL = 60  # 1 minute (stream data is cached server-side)

# Streaming
CONF_ENABLE_STREAMING = "enable_streaming"
DEFAULT_ENABLE_STREAMING = False

# API
REQUEST_TIMEOUT = 20

# Attributes
ATTR_VIN = "vin"
ATTR_MODEL = "model"
ATTR_REGISTRATION = "registration"
