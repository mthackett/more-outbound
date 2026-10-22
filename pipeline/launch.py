"""Explicit-mode launcher for both instances of the same Streamlit source."""
import argparse
import os
from pathlib import Path
import subprocess
import sys


def launch_command(mode, port, address):
    env = os.environ.copy()
    env['PIPELINE_MODE'] = mode
    env['DEMO_MODE'] = 'true' if mode == 'demo' else 'false'
    env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    app = Path(__file__).resolve().parent / 'adapters/primary/app.py'
    command = [sys.executable, '-m', 'streamlit', 'run', str(app),
               '--server.port', str(port), '--server.address', address,
               '--server.headless', 'true', '--browser.gatherUsageStats', 'false']
    if mode == 'demo':
        # Public visitors never see Deploy / developer menu items.
        command += ['--client.toolbarMode', 'minimal']
    return command, env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['demo', 'private'], required=True)
    parser.add_argument('--port', type=int, default=8501)
    parser.add_argument('--address', default='127.0.0.1')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('Port must be between 1 and 65535')
    command, env = launch_command(args.mode, args.port, args.address)
    raise SystemExit(subprocess.call(command, env=env))


if __name__ == '__main__':
    main()
