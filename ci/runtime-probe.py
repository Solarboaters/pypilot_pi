"""Exercise the installed plugin in the real Flatpak GUI, in a disposable runner."""
import json
import os
from pathlib import Path
import subprocess
import time
from PIL import ImageGrab

evidence = Path('evidence').resolve()
app_data = Path.home() / '.var/app/org.opencpn.OpenCPN'
config = app_data / 'config/opencpn/opencpn.conf'
config.parent.mkdir(parents=True, exist_ok=True)
config.write_text('''[Settings]
NavMessageShown=1
ConfigVersionString=Version 5.14.2 Build 2026-10-19
OpenGL=0
AutoHideToolbar=0
GlobalToolbarConfig=XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
[Settings/GlobalState]
FrameWinX=1280
FrameWinY=960
FrameWinPosX=0
FrameWinPosY=0
FrameMax=1
[PlugIns/libpypilot_pi.so]
bEnabled=1
[PlugIns/pypilot]
Host=127.0.0.1
ForwardNMEA=0
''')
processes = []
files = []
try:
    for name, command in [
        ('window-manager', ['openbox']),
        ('server', ['/usr/bin/python3', '-u', 'ci/server-fixture.py', 'pypilot-server']),
        ('gui', ['flatpak', 'run', 'org.opencpn.OpenCPN', '-G', '--loglevel=debug'])
    ]:
        out = (evidence / (name + '.log')).open('w')
        files.append(out)
        processes.append(subprocess.Popen(command, stdout=out, stderr=out))
        time.sleep(2)
    for elapsed in range(45):
        time.sleep(1)
        if elapsed in (5, 10, 15):
            welcome = subprocess.run(['xdotool', 'search', '--onlyvisible', '--name', '^Welcome to OpenCPN$'], capture_output=True, text=True)
            if welcome.returncode == 0:
                for window in welcome.stdout.split():
                    subprocess.run(['xdotool', 'windowactivate', '--sync', window, 'mousemove', '285', '438', 'click', '1'], check=True)
                print('Clicked Agree in isolated test profile.')
        if elapsed in (5, 20, 44):
            ImageGrab.grab().save(evidence / ('screen-' + str(elapsed) + '.png'))
    titles = subprocess.run(['xdotool', 'search', '--onlyvisible', '--name', '.*',
                             'getwindowname', '%@'], capture_output=True, text=True)
    (evidence / 'window-titles.txt').write_text(titles.stdout)
    states = [json.loads(line.split('FIXTURE_STATE ', 1)[1])
              for line in (evidence / 'server.log').read_text().splitlines()
              if line.startswith('FIXTURE_STATE ')]
    result = {'gui_alive': processes[-1].poll() is None,
              'connected': any(s['connections'] > 0 for s in states),
              'subscribed': any('ap.mode' in s['watched'] and 'ap.enabled' in s['watched'] for s in states),
              'steering_disabled': bool(states) and all(s['enabled'] is False for s in states)}
    (evidence / 'runtime-result.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))
    assert all(result.values()), result
finally:
    for proc in reversed(processes):
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    for f in files:
        f.close()
    for path in app_data.rglob('opencpn.log'):
        (evidence / 'opencpn-runtime.log').write_bytes(path.read_bytes())
