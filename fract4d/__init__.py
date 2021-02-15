#!/usr/bin/env python3

# package file for fract4d

import sys
import os

if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
    sys.setdlopenflags(os.RTLD_GLOBAL | os.RTLD_NOW)
