"""Run offline tests in a disposable source copy, never beside private data."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pattern', default='test_*.py')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    scratch = Path(tempfile.mkdtemp(prefix='more-outbound-tests-'))
    files = subprocess.check_output(
        ['git', '-c', f'safe.directory={root.as_posix()}', 'ls-files', '--cached', '--others', '--exclude-standard'],
        cwd=root, text=True).splitlines()
    for name in set(files):
        source = root / name
        if source.is_file():
            target = scratch / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    env = {k: v for k, v in os.environ.items() if not k.startswith(
        ('GOOGLE_', 'OPENAI_', 'TWILIO_', 'CANDIDATE_', 'PIPELINE_', 'QUICKLINKS_', 'STORIES_', 'DEMO_MODE', 'PRIVATE_OFFLINE'))}
    env.update(PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
    code = '''
import dotenv, socket, sys, unittest
dotenv.load_dotenv = lambda *a, **k: False
original_connect = socket.socket.connect
def local_only(self, address):
    if address[0] not in ('127.0.0.1', '::1', 'localhost'):
        raise AssertionError('External network forbidden in offline tests')
    return original_connect(self, address)
socket.socket.connect = local_only
suite = unittest.defaultTestLoader.discover('job_pipeline/domain/tests', pattern=sys.argv[1])
result = unittest.TextTestRunner(verbosity=1).run(suite)
raise SystemExit(not result.wasSuccessful())
'''
    log_path = scratch / 'test-results.log'
    with log_path.open('w', encoding='utf-8') as log:
        result = subprocess.run([sys.executable, '-c', code, args.pattern], cwd=scratch,
                                env=env, stdout=log, stderr=subprocess.STDOUT)
    print(f'Isolated test log: {log_path}')
    for line in log_path.read_text(encoding='utf-8').splitlines():
        if line.startswith(('ERROR:', 'FAIL:', 'Ran ', 'FAILED ', 'OK')):
            print(line)
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
