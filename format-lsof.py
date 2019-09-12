#!/usr/bin/env python3
import re
import sys
import subprocess
from typing import List


COMMAND = 0
PID = 1
HOST = 8
PORT = 9

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
  '-P'            # Do not convert port numbers to service names
]).decode('utf-8').splitlines()

# remove header row
lines.pop(0)

for line in lines:
  words = re.split(r'[\s:]+', line) # split on whitespace OR colon

  command = f"{words[COMMAND]}:{words[PID]}"
  host    = words[HOST]
  port    = int(words[PORT])

  hostWidth = max(hostWidth, len(host))
  command = re.sub(r'\\x20', ' ', command) # unmangle spaces
  if not command in results:
    results[command] = {}
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
