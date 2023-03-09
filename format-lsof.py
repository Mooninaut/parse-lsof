#!/usr/bin/env python3
import re
import subprocess
import math
from typing import List
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--trunc', type=int, help='Truncate output to N columns', default=-1)
args = parser.parse_args()

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

def getCommandLine(pid):
  f = open(f"/proc/{pid}/cmdline", "r")
  cmdline = f.read()
  f.close()
  cmdline = cmdline.rstrip('\0')
  if ('\0' in cmdline):
    return cmdline.split('\0')
  return cmdline.split()

def getJavaClass(cmdline):
  for cmd in reversed(cmdline):
    if re.match(r'^[0-9A-Za-z.]+\.[A-Z][0-9A-Za-z]+$', cmd):
      return cmd
  return cmdline[-1]

results = {}
hostWidth = -1

lines = subprocess.run([
  'lsof',
  '+c0',          # Print all characters of command name
  '-iTCP',        # Only list TCP streams
  '-sTCP:LISTEN', # Only list streams in state LISTEN
  '-P',           # Do not convert port numbers to service names
  '-n',           # Do not convert IP addresses to host names
  '-Fpcn'         # Output machine-readable [F]ormat with [p]rocess IDs, [c]ommand names, and [n]etwork addresses
], capture_output=True, timeout=10).stdout.decode('utf-8').splitlines()

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
    command = ''
    host = ''
    port = 0
    hostWidth = max(hostWidth, len(pid))
  elif prefix == COMMAND:
    command = rest
    command = re.sub(r'\\x20', ' ', command)

    if not command in results:
      results[command] = {}
    if not pid in results[command]:
      results[command][pid] = {}

  elif prefix == FID:
    fid = rest # not used
  elif prefix == HOST:
    # use rsplit and limit to 1 split (2 results) to handle IPv6 [xxxx:y::z]:port type addresses
    host, port = rest.rsplit(PORT, 1)
    port = int(port)
    hostWidth = max(hostWidth, len(host))
    if not host in results[command][pid]:
      results[command][pid][host] = {}
    results[command][pid][host][port] = True

# sort case-insensitive, but use case to break ties
def keyify(k_v):
  command = k_v[0] # tuple of string:dictionary
  return (command.lower(), command) # tuple of string:string

lines = [f"{'PID':>{hostWidth}} COMMAND\n{'HOST':>{hostWidth}} PORT(s)"]

for command, cmdDict in sorted(
    results.items(),
    key = keyify):

  for pid, pidDict in sorted(cmdDict.items()):

    commandLine = getCommandLine(pid)

    cmdPath = commandLine[0]
    line = f"{int(pid):{hostWidth}d} "
    if args.trunc > 0 and (len(line) + len(cmdPath)) > args.trunc:
      shrinkBy = (len(line) + len(cmdPath)) - args.trunc
      shrinkTo = len(cmdPath) - shrinkBy
      cmdPath = cmdPath[:math.floor(shrinkTo/2)] + "…" + cmdPath[-math.ceil(shrinkTo/2):]

    line = line + cmdPath
    lines.append(line)

    if command == "java":
      line = f"{'Class':>{hostWidth}} "
      javaClass = getJavaClass(commandLine)
      if args.trunc > 0 and (len(line) + len(javaClass)) > args.trunc:
        shrinkBy = (len(line) + len(javaClass)) - args.trunc
        shrinkTo = len(javaClass) - shrinkBy
        javaClass = javaClass[:math.floor(shrinkTo/2)] + "…" + javaClass[-math.ceil(shrinkTo/2):]
      line = line + javaClass
      lines.append(line)

    for host, portDict in sorted(pidDict.items()):
      ports = sorted(portDict.keys())
      lines.append((f"{host:>{hostWidth}} ") + " ".join(mergeRuns(ports)))
    lines.append("")
if len(lines) > 0:
  print("\n".join(lines))
