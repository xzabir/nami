import os
import yaml

CONFIG_PATH = os.environ.get("NAMI_CONFIG", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.yaml"))

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

CONFIG = load_config()
