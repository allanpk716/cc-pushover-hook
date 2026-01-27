#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple test to verify Python can run
"""
import sys
import os

print("Python is working!")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"CLAUDE_PROJECT_DIR: {os.getenv('CLAUDE_PROJECT_DIR', 'NOT SET')}")

sys.exit(0)
