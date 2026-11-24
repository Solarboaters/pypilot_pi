"""Real pypilot server/client with synthetic read-only telemetry, no autopilot."""
import gettext
import json
import os
import pathlib
import sys
import time

gettext.install('pypilot')
os.environ['PYPILOT_MULTIPROCESSING'] = '1'
os.environ['PYPILOT_CONFIG_DIR'] = str(pathlib.Path('evidence/server-config').resolve())
sys.path.insert(0, sys.argv[1])
from pypilot.server import pypilotServer
from pypilot.client import pypilotClient
from pypilot.values import Value, BooleanValue, StringValue, SensorValue

server = pypilotServer()
owner = pypilotClient(server)
values = [BooleanValue('ap.enabled', False), StringValue('ap.mode', 'compass'),
          Value('ap.modes', ['compass', 'gps', 'wind']),
          SensorValue('ap.heading', 123.4), SensorValue('ap.heading_command', 125.0),
          SensorValue('imu.heading', 123.4), SensorValue('imu.uptime', 0),
          StringValue('ap.tack.state', 'none'), StringValue('servo.flags', ''),
          StringValue('ap.tack.direction', 'port'), StringValue('imu.error', ''),
          StringValue('imu.warning', ''), StringValue('servo.state', 'idle'),
          StringValue('servo.controller', 'none'), SensorValue('rudder.angle', 0)]
for value in values:
    owner.register(value)
server.init()  # Run in this process while keeping the production socket-pair transport.
started = time.monotonic()
last = None
while time.monotonic() - started < 150:
    values[6].set(time.monotonic() - started)
    server.poll(0)
    owner.poll()
    state = {'connections': len(server.sockets),
             'watched': sorted(name for name, value in server.values.values.items()
                               if value.awatches or value.pwatches),
             'enabled': values[0].value}
    if state != last:
        print('FIXTURE_STATE ' + json.dumps(state), flush=True)
        last = state
    assert values[0].value is False
    time.sleep(.02)
