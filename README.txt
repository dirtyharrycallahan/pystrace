
  pystrace -- Python tools for parsing and analysing strace output files
==========================================================================

Copyright 2012
    The President and Fellows of Harvard College.

Contributor(s):
    Peter Macko <pmacko at eecs.harvard.edu>


 Introduction
--------------

pystrace is a simple Python library and a small collection of tools for parsing
and analyzing the output of strace:
  
  strace.py -- the Python library
  strace2csv.py -- a tool to convert strace output to an easy-to-parse csv
  strace_systime_analyzer.py -- analyzes time spent in system calls

This project is an early stage, but unfortunately I do not currently have
resources to work on it. Nonetheless I hope that you would find it useful.
If you have any questions or if you would like to contribute, please just drop
me an email!


 Usage
-------

pystrace currently expects the analyzed file to contain timestamps in the "ttt"
format. For example, if you would like to analyze the strace of "ls", do the
following:

  strace -ttt -o ls.out ls

This generates ls.out, which you can read using class strace.StraceFile in your
Python programs or using one of the provided tools.

To take advantage of the full potential of pystrace, specify also the -T option
to measure the time spent in system calls and -f to follow the child processes:

  strace -f -ttt -T -o ls-full.out ls


 Using the Library: strace.py
------------------------------

You can use the library to either read a strace output file line by line using
strace.StraceInputStream or to load it in its entirety using strace.StraceFile.

StraceInputStream is an iterator that returns StraceEntry for each line in the
file. Please refer to strace2csv.py for an example.

StraceEntry contains the following fields:
  pid (if available)
  timestamp
  was_unfinished (True if the line ends with "<unfinished ...>")
  elapsed_time (if available)
  syscall_name
  syscall_arguments
  return_value
  category (currently "IO" for I/O system calls, "" for everything else)

StraceFile loads the given strace output file in its entirety. It contains the
following fields:
  input
  have_pids (True if each line in the input file is prefixed with a PID)
  content (an array of StraceEntry elements)
  processes (a dictionary mapping PIDs to StraceTracedProcess)
  start_time (the first timestamp)
  last_timestamp
  finish_time
  elapsed_time

StraceTracedProcess contains:
  pid
  name (the name of the process, if available)
  entries (an array of StraceEntry elements)

Please refer to strace_systime_analyzer.py for an example of how to use
StraceFile.


 Using strace2csv.py
---------------------

This tool converts a strace output file to a .csv file. For example:

  $ python strace2csv.py ls-full.out 
  PID,TIMESTAMP,SYSCALL,CATEGORY,SPLIT,ARGC,ARG1,ARG2,ARG3,ARG4,ARG5,ARG6,RESULT,ELAPSED
  2621,1388459393.107463,"execve",,0,3,"""/bin/ls""","[""ls""]","[/* 69 vars */]",,,,0,0.000138
  2621,1388459393.107761,"brk",,0,1,"0",,,,,,"0x2576000",0.000008
  2621,1388459393.107812,"access","IO",0,2,"""/etc/ld.so.nohwcap""","F_OK",,,,,"-1",0.000010
  2621,1388459393.107869,"mmap","IO",0,6,"NULL","8192","PROT_READ|PROT_WRITE","MAP_PRIVATE|MAP_ANONYMOUS","-1","0","0x7fbc0a2d2000",0.000009

You can use the -o argument to redirect the output to a file instead of the
standard output.


 Using strace_systime_analyzer.py
----------------------------------

This tool produces a .csv file that shows how much time the given process and
its children spent inside the system calls. The first column is a time in 0.1
second increments. The other columns correspond to the different PIDs contained
in the strace output. Each entry in these columns is the fraction of time spent
inside the system calls, where 0 means none and 1 means 100%.

