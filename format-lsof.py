#!/usr/bin/env python3
import re
import sys
import subprocess
from typing import List


COMMAND = 'c'
PID = 'p'
HOST = 'n'
PORT = ':'
FID = 'f'

def mergeRuns(numbers: List[int]) -> List[str]:
  if len(numbers) == 0:
    return []

  runStart = numbers.pop(0)
  current = runStart

  while len(numbers) > 0 and numbers[0] == current + 1:
    current = numbers.pop(0)

  result = str(runStart) if runStart == current else f"{runStart}-{current}"

  return [result] + mergeRuns(numbers)

results = {}
hostWidth = -1

lines = subprocess.check_output([
  'lsof',
  '+c0',          # Print all characters of command name
  '-iTCP',        # Only list TCP streams
  '-sTCP:LISTEN', # Only list streams in state LISTEN
  '-P',           # Do not convert port numbers to service names
  '-Fpcn'         # Output machine-readable format with process IDs, command names, and Internet addresses
]).decode('utf-8').splitlines()

command = ''
pid = ''
host = ''
port = ''
fid = ''

for line in lines:
  prefix = line[0]
  rest = line[1:]
  if prefix == PID:
    pid = rest
  elif prefix == COMMAND:
    command = rest
    command = re.sub(r'\\x20', ' ', command)
    command = f"{command}:{pid}"
    if not command in results:
      results[command] = {}
  elif prefix == FID:
    fid = rest # not used
  elif prefix == HOST:
    host, port = rest.split(':')
    port = int(port)
    hostWidth = max(hostWidth, len(host))
    if not host in results[command]:
      results[command][host] = {}
    results[command][host][port] = True

for command, hostDict in sorted(
    results.items(),
    key = lambda command: command[0].lower()
  ):
  print(command)
  for host, portDict in sorted(hostDict.items()):
    print(f"\t%-{hostWidth}s " % host, end='')
    ports = sorted(portDict.keys())
    print(*mergeRuns(ports))
