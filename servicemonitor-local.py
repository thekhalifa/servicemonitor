#!/usr/bin/env python3
import os
import sys
RUN_LIB_DIR = os.path.join(os.getcwd(), 'src')
os.chdir(RUN_LIB_DIR)
sys.path.append(RUN_LIB_DIR)
from src.application import ServiceMonitor
sm = ServiceMonitor(os.getcwd())
sm.run()
