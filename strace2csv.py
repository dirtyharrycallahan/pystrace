#!/usr/bin/python

#
# pystrace -- Python tools for parsing and analysing strace output files
#
#
# Copyright 2012
#      The President and Fellows of Harvard College.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the University nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE UNIVERSITY AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE UNIVERSITY OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
#
#
# Contributor(s):
#   Peter Macko (http://eecs.harvard.edu/~pmacko)
#

import getopt
import os.path
import sys

from strace import *
from strace_utils import *


#
# Convert to a .csv
#
def convert2csv(input_file, output_file=None, separator=',', quote='"'):
	'''
	Convert to a .csv
	
	Arguments:
	  input_file  - the input file, or None for standard input
	  output_file - the output file, or None for standard output
	  separator   - the separator
	'''

	# Open the files
	
	if input_file is not None:
		f_in = open(input_file, "r")
	else:
		f_in = sys.stdin
	
	if output_file is not None:
		f_out = open(output_file, "w")
	else:
		f_out = sys.stdout
	
	
	# Process the file
	
	strace_stream = StraceInputStream(f_in)
	first = True
	
	for entry in strace_stream:
		
		if first:
			first = False
			headers = ["TIMESTAMP", "SYSCALL", "CATEGORY", "SPLIT", \
					   "ARGC", "ARG1", "ARG2", "ARG3", "ARG4", "ARG5", "ARG6",
					   "RESULT", "ELAPSED"]
			if strace_stream.have_pids: headers.insert(0, "PID")
			csv_write_row_array(f_out, headers, separator, "")
		
		
		# Print
		
		if entry.was_unfinished:
			i_was_unfinished = 1
		else:
			i_was_unfinished = 0
		
		data = [entry.timestamp, entry.syscall_name, entry.category,
			   i_was_unfinished,
			   len(entry.syscall_arguments),
			   array_safe_get(entry.syscall_arguments, 0),
			   array_safe_get(entry.syscall_arguments, 1),
			   array_safe_get(entry.syscall_arguments, 2),
			   array_safe_get(entry.syscall_arguments, 3),
			   array_safe_get(entry.syscall_arguments, 4),
			   array_safe_get(entry.syscall_arguments, 5),
			   entry.return_value,
			   entry.elapsed_time]
		if strace_stream.have_pids: data.insert(0, entry.pid)
		csv_write_row_array(f_out, data, separator, quote)


	# Close the files

	if f_out is not sys.stdout:
		f_out.close()
	strace_stream.close()


#
# Print the usage information
#
def usage():
	sys.stderr.write('Usage: %s [OPTIONS] [FILE]\n\n'
		% os.path.basename(sys.argv[0]))
	sys.stderr.write('Options:\n')
	sys.stderr.write('  -h, --help         Print this help message and exit\n')
	sys.stderr.write('  -o, --output FILE  Print to file instead of the standard output\n')


#
# The main function
#
# Arguments:
#   argv - the list of command-line arguments, excluding the executable name
#
def main(argv):

	input_file = None
	output_file = None
	

	# Parse the command-line options

	try:
		options, remainder = getopt.gnu_getopt(argv, 'ho:',
			['help', 'output='])
		
		for opt, arg in options:
			if opt in ('-h', '--help'):
				usage()
				return
			elif opt in ('-o', '--output'):
				output_file = arg
		
		if len(remainder) > 1:
			raise Exception("Too many options")
		elif len(remainder) == 1:
			input_file = remainder[0]
	except Exception as e:
		sys.stderr.write("%s: %s\n" % (os.path.basename(sys.argv[0]), e))
		sys.exit(1)
	
	
	# Convert to .csv

	try:
		convert2csv(input_file, output_file)
	except IOError as e:
		sys.stderr.write("%s: %s\n" % (os.path.basename(sys.argv[0]), e))
		sys.exit(1)


#
# Entry point to the application
#
if __name__ == "__main__":
	main(sys.argv[1:])
