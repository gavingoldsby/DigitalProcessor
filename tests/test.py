#!/usr/bin/env python

import os
import os.path
import tempfile
import subprocess
import time
import signal
import re
import sys
import shutil
import decode_out as dec
import csv
import abc

#file_locations = os.path.expanduser(os.getcwd())
file_locations = '.'
#logisim_location = os.path.join(os.getcwd(),"logisim.jar")
logisim_location = "logisim.jar"


class TestCase():
  """
      Runs specified circuit file and compares output against the provided reference trace file.
  """

  def __init__(self, circfile, expected):
    self.circfile  = circfile
    self.expected = expected

  def __call__(self, typ):
    oformat = dec.get_test_format(typ)
    if not oformat:
        print "CANNOT format test type called [{}]".format(typ)
        return (False, "Error in the test")

    try:
        if not isinstance(self.expected, list):
            # it is a file so parse it
            self.expected = [x for x in ReferenceFileParser(oformat, self.expected).outputs()]
        else:
            [oformat.validate(x) for x in self.expected]
    except dec.OutputFormatException as e:
        print "Error in formatting of expected output (check test.py if this is a test you wrote):"
        print "\t", e
        return (False, "Error in the test")

    output = tempfile.TemporaryFile(mode='r+')
    command = ["java","-jar",logisim_location,"-tty","table", self.circfile]
    proc = subprocess.Popen(command,
                            stdin=open(os.devnull),
                            stdout=subprocess.PIPE)
    try:
      debug_buffer = [] 
      passed = compare_unbounded(proc.stdout,self.expected, oformat, debug_buffer)
    except dec.OutputFormatException as e:
        print "Error in formatting of Logisim output (check {}):".format(self.circfile)
        print "\t", e
        return (False, "Error in the test")
    finally:
      if os.name != 'nt':
        os.kill(proc.pid,signal.SIGTERM)
    if passed:
      return (True, "Matched expected output")
    else:
      print "Format is student then expected"
      wtr = csv.writer(sys.stdout, delimiter='\t')
      oformat.header(wtr)
      for row in debug_buffer:
        wtr.writerow(['{0:x}'.format(b) for b in row[0]])
        wtr.writerow(['{0:x}'.format(b) for b in row[1]])

      return (False, "Did not match expected output (check {}, also check test.py if this is a test you wrote)".format(self.circfile))

def compare_unbounded(student_out, expected, oformat, debug):
  parser = OutputProvider(oformat)
  for i in range(0, len(expected)):
    line1 = student_out.readline()
    values_student_parsed = parser.parse_line(line1.rstrip())

    debug.append((values_student_parsed, expected[i]))

    if values_student_parsed != expected[i]:
      return False

  return True

def run_tests(tests):
  # actual submission testing code
  print "Testing files..."
  tests_passed = 0
  tests_failed = 0

  for description,test,typ in tests:
    test_passed, reason = test(typ)
    if test_passed:
      print "\tPASSED test: %s" % description
      tests_passed += 1
    else:
      print "\tFAILED test: %s (%s)" % (description, reason)
      tests_failed += 1
  
  print "Passed %d/%d tests" % (tests_passed, (tests_passed + tests_failed))

class OutputProvider(object):
    def __init__(self, format):
        self.format = format

    @abc.abstractmethod
    def outputs(self):
        pass
    
    def parse_line(self, line):
        value_strs = line.split('\t')   
        values_bin = [''.join(v.split(' ')) for v in value_strs] 
        try:
            values = [int(v, 2) for v in values_bin]
        except ValueError as e:
            if values_bin == ['']:
                raise dec.OutputFormatException("you have a non-integer in this list: {}. If this is logisim output, are you sure you have a circ file for this test?".format(values_bin))
            else :
                raise dec.OutputFormatException("you have a non-integer in this list: {}".format(values_bin))
        self.format.validate(values)
        return values

class ReferenceFileParser(OutputProvider):
    def __init__(self, format, filename=None):
        self.f = filename
        super(ReferenceFileParser, self).__init__(format)

    def outputs(self):
        assert self.f is not None, "cannot use outputs if no filename given"
        with open(self.f, 'r') as inp:
            for line in inp.readlines():
                values = self.parse_line(line)
                yield values 

p1_tests = [
  ("ALU add (with overflow) test, with output in python",
        TestCase(os.path.join(file_locations,'alu-add.circ'),
                 [[0, 0, 0, 0x7659035D],
                  [1, 1, 0, 0x87A08D79],
                  [2, 1, 0, 0x80000000],
                  [3, 0, 1, 0x00000000],
                  [4, 0, 0, 0x00000000],
                  [5, 0, 0, 0x00000227],
                  [6, 1, 0, 0x70000203],
                  [7, 0, 0, 0xFFFFFEFF],
                  [8, 0, 1, 0x00000000],
                  [9, 0, 1, 0x00000000],
                  [10, 0, 1, 0x00000000],
                  [11, 0, 1, 0x00000000],
                  [12, 0, 1, 0x00000000],
                  [13, 0, 1, 0x00000000],
                  [14, 0, 1, 0x00000000],
                  [15, 0, 1, 0x00000000]]), "alu"),
  ("ALU arithmetic right shift test",
        TestCase(os.path.join(file_locations,'alu-sra.circ'),
                [[0, 0, 0, 0xF7AB6FBB],
                 [1, 0, 0, 0xFFFFFC00],
                 [2, 0, 0, 0x00000000],
                 [3, 0, 0, 0xFEEDF00D],
                 [4, 0, 1, 0x00000000],
                 [5, 0, 1, 0x00000000],
                 [6, 0, 1, 0x00000000],
                 [7, 0, 1, 0x00000000],
                  [8, 0, 1, 0x00000000],
                  [9, 0, 1, 0x00000000],
                  [10, 0, 1, 0x00000000],
                  [11, 0, 1, 0x00000000],
                  [12, 0, 1, 0x00000000],
                  [13, 0, 1, 0x00000000],
                  [14, 0, 1, 0x00000000],
                  [15, 0, 1, 0x00000000]]), "alu"),
  ("RegFile read/write test",
        TestCase(os.path.join(file_locations,'regfile-read_write.circ'),
                [[0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
                 [1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
                 [2, 0x0, 0x0, 0x0, 0x0, 0x0, 0xBAD00DAD, 0xBAD00DAD],
                 [3, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
                 [4, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
                 [5, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x10101010],
                 [6, 0x0, 0x0, 0x0, 0x0, 0x0, 0x10101010, 0x0],
                 [7, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]]), "regfile"),
  ("RegFile $zero test",
        TestCase(os.path.join(file_locations,'regfile-zero.circ'),
                [[0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
                 [1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
                 [2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
                 [3, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
                 [4, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
                 [5, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]]), "regfile"),
  ("RegFile debug outputs test",
        TestCase(os.path.join(file_locations,'regfile-debug_outputs.circ'),
                [[0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
                 [1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
                 [2, 0xBAD00DAD, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
                 [3, 0xBAD00DAD, 0xFEEDF00D, 0x0, 0x0, 0x0, 0x0, 0x0],
                 [4, 0xBAD00DAD, 0xFEEDF00D, 0x12345678, 0x0, 0x0, 0x0, 0x0],
                 [5, 0xBAD00DAD, 0xFEEDF00D, 0x12345678, 0x10101010, 0x0, 0x0, 0x0],
                 [6, 0xBAD00DAD, 0xFEEDF00D, 0x12345678, 0x10101010, 0xDADADADA, 0x0, 0x0],
                 [7, 0xBAD00DAD, 0xFEEDF00D, 0xBABABABA, 0x10101010, 0xDADADADA, 0x0, 0x0]]), "regfile")
]

# 2 stage pipeline tests
p2_tests = [
  ("CPU starter test",
        TestCase(os.path.join(file_locations,'CPU-starter_kit_test.circ'),
                 os.path.join(file_locations,'reference_output/CPU-starter_kit_test.out')), "cpu"),
]

# Single-cycle (sc) tests
p2sc_tests = [
  ("CPU starter test",
        TestCase(os.path.join(file_locations,'CPU-starter_kit_test.circ'),
                [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0x20100001],
                 [1, 0, 0, 0x0, 0x0, 1, 0x4, 0x20110002],
                 [1, 2, 0, 0x0, 0x0, 2, 0x8, 0x02119020],
                 [1, 2, 3, 0x0, 0x0, 3, 0xC, 0x00000000],
                 [1, 2, 3, 0x0, 0x0, 4, 0x10, 0x00000000]]), "cpu"),
  ("CPU shift test",
        TestCase(os.path.join(file_locations,'shift_test.circ'),
                [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0x2210000c],
                 [12, 0, 0, 0x0, 0x0, 1, 0x4, 0x00108040],
                 [24, 0, 0, 0x0, 0x0, 2, 0x8, 0x22310008],
                 [24, 8, 0, 0x0, 0x0, 3, 0xC, 0x00118842],
                 [24, 4, 0, 0x0, 0x0, 4, 0x10, 0x2252000c],
                 [24, 4, 12, 0x0, 0x0, 5, 0x14, 0x00129043],
                 [24, 4, 6, 0x0, 0x0, 6, 0x18, 0x00000000]]), "cpu"),
  ("CPU add test",
        TestCase(os.path.join(file_locations,'add_test.circ'),
                [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0x2210000c],
                 [12, 0, 0, 0x0, 0x0, 1, 0x4, 0x02108820],
                 [12, 24, 0, 0x0, 0x0, 2, 0x8, 0x26120004],
                 [12, 24, 16, 0x0, 0x0, 3, 0xC, 0x02519021],
                 [12, 24, 40, 0x0, 0x0, 4, 0x10, 0x00000000]]), "cpu"),
  ("CPU slt test",
        TestCase(os.path.join(file_locations,'slt_test.circ'),
                [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0x21080008],
                 [0, 0, 0, 0x0, 0x0, 1, 0x4, 0x21290004],
                 [0, 0, 0, 0x0, 0x0, 2, 0x8, 0x214a0006],
                 [0, 0, 0, 0x0, 0x0, 3, 0xC, 0x216b0004],
                 [0, 0, 0, 0x0, 0x0, 4, 0x10, 0x0128802a],
                 [1, 0, 0, 0x0, 0x0, 5, 0x14, 0x29310004],
                 [1, 0, 0, 0x0, 0x0, 6, 0x18, 0x2d720002],
                 [1, 0, 0, 0x0, 0x0, 7, 0x1C, 0x29100001],
                 [0, 0, 0, 0x0, 0x0, 8, 0x20, 0x00000000]]), "cpu"),
  ("CPU and/or test",
        TestCase(os.path.join(file_locations,'and-or_test.circ'),
                [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0x21080008],
                 [0, 0, 0, 0x0, 0x0, 1, 0x4, 0x21290005],
                 [0, 0, 0, 0x0, 0x0, 2, 0x8, 0x01098024],
                 [0, 0, 0, 0x0, 0x0, 3, 0xC, 0x01098825],
                 [0, 13, 0, 0x0, 0x0, 4, 0x10, 0x31320007],
                 [0, 13, 5, 0x0, 0x0, 5, 0x14, 0x36300009],
                 [13, 13, 5, 0x0, 0x0, 6, 0x18, 0x00000000]]), "cpu"),
  ("CPU lui test",
        TestCase(os.path.join(file_locations,'lui_test.circ'),
                [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0x3c10ffff],
                 [0xFFFF0000, 0, 0, 0x0, 0x0, 1, 0x4, 0x3c110001],
                 [0xFFFF0000, 0x00010000, 0, 0x0, 0x0, 2, 0x8, 0x2252ffff],
                 [0xFFFF0000, 0x00010000, 0xFFFFFFFF, 0x0, 0x0, 3, 0xC, 0x3c120064],
                 [0xFFFF0000, 0x00010000, 0x00640000, 0x0, 0x0, 4, 0x10, 0x00000000]]), "cpu"),
  ("CPU mult test",
        TestCase(os.path.join(file_locations,'mult_test.circ'),
                [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0x21080004],
                 [0, 0, 0, 0x0, 0x0, 1, 0x4, 0x21290003],
                 [0, 0, 0, 0x0, 0x0, 2, 0x8, 0x01090018],
                 [0, 0, 0, 0x0, 0x0, 3, 0xC, 0x00008012],
                 [12, 0, 0, 0x0, 0x0, 4, 0x10, 0x3c01acbd],
                 [12, 0, 0, 0x0, 0x0, 5, 0x14, 0x34210000],
                 [12, 0, 0, 0x0, 0x0, 6, 0x18, 0x01415020],
                 [12, 0, 0, 0x0, 0x0, 7, 0x1c, 0x01490018],
                 [12, 0, 0, 0x0, 0x0, 8, 0x20, 0x00008812],
                 [12, 0x06370000, 0, 0x0, 0x0, 9, 0x24, 0x00009010],
                 [12, 0x06370000, 0xFFFFFFFF, 0x0, 0x0, 10, 0x28, 0x00000000]]), "cpu"),
  ("CPU branch test",
        TestCase(os.path.join(file_locations,'branch_test.circ'),
                [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0x21080001],
                 [0, 0, 0, 0x0, 0x0, 1, 0x4, 0x21290002],
                 [0, 0, 0, 0x0, 0x0, 2, 0x8, 0x11280001],
                 [0, 0, 0, 0x0, 0x0, 3, 0xC, 0x15280001],
                 #[0, 0, 0, 0x0, 0x0, 4, 0x10, 0x22100001],
                 [0, 0, 0, 0x0, 0x0, 4, 0x14, 0x22100002],
                 [2, 0, 0, 0x0, 0x0, 5, 0x18, 0x214a0002],
                 [2, 0, 0, 0x0, 0x0, 6, 0x1c, 0x15490001],
                 [2, 0, 0, 0x0, 0x0, 7, 0x20, 0x11490001],
                 #[2, 0, 0, 0x0, 0x0, 9, 0x24, 0x22310001],
                 [2, 0, 0, 0x0, 0x0, 8, 0x28, 0x22310002],
                 [2, 2, 0, 0x0, 0x0, 9, 0x2c, 0x00000000]]), "cpu"),
  ("CPU load/store test",
        TestCase(os.path.join(file_locations,'load-store_test.circ'),
                [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0x22100001],
                 [1, 0, 0, 0x0, 0x0, 1, 0x4, 0x22310005],
                 [1, 5, 0, 0x0, 0x0, 2, 0x8, 0xac107f00],
                 [1, 5, 0, 0x0, 0x0, 3, 0xC, 0xac117f04],
                 [1, 5, 0, 0x0, 0x0, 4, 0x10, 0x8c127f00],
                 [1, 5, 1, 0x0, 0x0, 5, 0x14, 0x00000000]]), "cpu"),
  ("CPU I/O test",
        TestCase(os.path.join(file_locations,'iotest.circ'),
                [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0x21080001],
                 [0, 0, 0, 0x0, 0x0, 1, 0x4, 0xac087f00],
                 [0, 0, 0, 0x0, 0x0, 2, 0x8, 0x21290001],
                 [0, 0, 0, 0x0, 0x0, 3, 0xC, 0x214a0002],
                 [0, 0, 0, 0x0, 0x0, 4, 0x10, 0xac0a7f04],
                 [0, 0, 0, 0x0, 0x0, 5, 0x14, 0x00000000]]), "cpu"),
  ("func test",
        TestCase(os.path.join(file_locations,'func_test.circ'),
        [
                         [0,0,0,0],
                         [36,0,0,0],
                         [36,16,0,0]
                         ]), "cpu-end")
]

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print("Usage: " + sys.argv[0] + " (p1|p2|p2sc)")
    sys.exit(-1)
  if sys.argv[1] == 'p1':
    run_tests(p1_tests)
  elif sys.argv[1] == 'p2':
    run_tests(p2_tests)
  elif sys.argv[1] == 'p2sc':
    run_tests(p2sc_tests)
  else:
    print("Usage: " + sys.argv[0] + " (p1|p2)")
    sys.exit(-1)
