
"""
Paths to various files and resources
"""

import os
import sys

PROGRAM_NAME = "gsni-authenticator"
UI_DIR_NAME = "ui"
LAUNCH_DIR = os.path.abspath(sys.path[0])
DATA_DIRS = [LAUNCH_DIR]

try:
    import xdg
    DATA_BASE_DIRS = xdg.BaseDirectory.xdg_data_dirs
except:
    DATA_BASE_DIRS = [
      os.path.join(os.path.expanduser("~"), ".local", "share"),
      "/usr/local/share", "/usr/share"]
  
DATA_DIRS += [os.path.join(d, PROGRAM_NAME) for d in DATA_BASE_DIRS]

def get_ui_asset(asset_name):
    for base in DATA_DIRS:
        asset_path = os.path.join(base, UI_DIR_NAME, asset_name)
        if os.path.exists(asset_path):
            return asset_path

