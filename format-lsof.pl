#!/usr/bin/perl
use warnings;
use strict;
use List::Util 'max';
# Field indices in lsof output, split on [\s:]+
use constant COMMAND => 0;
use constant HOST => 8;
use constant PORT => 9;

# Sample input that this command parses
# COMMAND         PID     USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
# Code\x20Helper 1985 ccherlin   43u  IPv4 0x355daa078b4355ff      0t0  TCP localhost:31760 (LISTEN)
# Code\x20Helper 1988 ccherlin   43u  IPv4 0x355daa078ab76f7f      0t0  TCP localhost:8687 (LISTEN)

# Note that Code Helper gets mangled to Code\x20Helper

my @lines = `lsof +c0 -iTCP -sTCP:LISTEN -P`;
shift @lines; # Remove header row
chomp @lines;

if (@lines == 0) {
  STDERR->print("No output received from lsof\n");
  exit($? >> 8);
}

my %results;
my $hostWidth = -1;
foreach my $line (@lines) {
  my @fields = split(/[\s:]+/, $line); # split on whitespace OR colon
  my ($command, $host, $port) = @fields[COMMAND, HOST, PORT];
  $command =~ s/\\x20/ /;      # unmangle spaces
  $hostWidth = max($hostWidth, length($host));
  $results{$command}{$host}{$port}++;
};

for my $command (sort { lc $a cmp lc $b or $a cmp $b } keys %results) {
  print($command, $/);
  for my $host (sort keys %{$results{$command}}) {
    printf(qq(\t\%-${hostWidth}s ), $host);
    my @ports = sort {$a <=> $b } keys %{$results{$command}{$host}};
    print(join(' ', mergeRuns(@ports)), $/);
  }
}

# Input to mergeRuns must be sorted in ascending order.
sub mergeRuns {
  if (@_ == 0) {
    return ();
  }

  my $runStart = shift;
  my $current = $runStart;

  while (@_ > 0 and $_[0] == ($current + 1)) {
    $current = shift;
  }

  my $result = $runStart == $current ? $runStart : "$runStart-$current";

  return ($result, mergeRuns(@_));
}
