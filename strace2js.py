#!/usr/bin/python2

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

document_template = \
'''
<html>
<head>
    <script src="./vis.min.js"></script>
    <link href="./vis.min.css" rel="stylesheet" type="text/css" />

    <style type="text/css">
        #mynetwork {{
            width:  100%;
            height: 100%;
            border: 1px solid lightgray;
		}}
    </style>
</head>
<body>
<div id="mynetwork"></div>

<script type="text/javascript">
    // create an array with nodes
    var nodes = new vis.DataSet([ {nodes} ]);

    // create an array with edges
    var edges = new vis.DataSet([ {edges} ]);

    // create a network
    var container = document.getElementById('mynetwork');

    // provide the data in the vis format
    var data = {{
        nodes: nodes,
        edges: edges
	}};
    var options = {{
        physics: {{
            enabled: false
        }}
    }};

    // initialize your network!
    var network = new vis.Network(container, data, options);
</script>
</body>
</html>
'''

execve_node_template = \
        "{{id: {ts}, label: 'execve', title: '{arguments}', x: {xx}, y: {yy}, size: 25, color: 'orange', shape: 'diamond' }},"
default_node_template = \
        "{{ id: {ts}, label: '{syscall}', x: {xx}, y: {yy}, size: 10, color: 'grey' }},"
fork_node_template = \
        "{{ id: {ts}, label: '{syscall}', title: '{arguments}', x: {xx}, y: {yy}, size: 25 }},"
exited_ok_node_template = \
		"{{ id: {ts}, label: 'EXITED', title: '{arguments}', x: {xx}, y: {yy}, size: 25, color: 'green', shape: 'box' }},"
exited_ko_node_template = \
		"{{ id: {ts}, label: 'EXITED', title: '{arguments}', x: {xx}, y: {yy}, size: 25, color: 'red', shape: 'box' }},"
killed_node_template = \
        "{{ id: {ts}, label: '{arguments}', x: {xx}, y: {yy}, size: 25, color: 'red', shape: 'box' }},"

edge_template = "{{from: {f}, to: {t} }},"

label_node_template = \
        "{{id: {pid}, label: '{label}', x: {xx}, y: {yy}, size: 25, shape: 'text' }},"


#
# Convert to a .js
#
def convert2js(input_file, output_file=None, skip_nonproc=False):
	'''
	Convert to a .html with vis.js
	
	Arguments:
	  input_file  - the input file, or None for standard input
	  output_file - the output file, or None for standard output
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
	nodes = ""
	edges = ""

	pid_to_y    = {}
	pid_to_node = {}

	x     = 0
	max_y = 0

	pid_to_first_x = {}
	
	for entry in strace_stream:
		
		# Get yy from PID
		pid = entry.pid
		if pid in pid_to_y:
			y = pid_to_y[pid]
		else:
			y = max_y
			pid_to_y[pid] = y
			max_y += 100

		# Which template to use?
		if entry.syscall_name in ('fork', 'clone'):
			entry_template = fork_node_template

			# Register the fork/clone syscall as predecessor of the first
			# syscall of the new process
			if entry.return_value in pid_to_node:
				# Sometimes the first syscall of a new process appears in the strace
				# before the fork/clone that creates that process
				edge = edge_template.format(
						f=entry.timestamp,
						t=pid_to_node[entry.return_value]
						)
				edges = edges + edge
			else:
				pid_to_node[entry.return_value] = entry.timestamp
		elif entry.syscall_name == 'execve':
			entry_template = execve_node_template
		elif entry.syscall_name == 'EXIT':
			if entry.return_value == '0':
				entry_template = exited_ok_node_template
			else:
				entry_template = exited_ko_node_template
		elif entry.syscall_name == 'KILL':
			entry_template = killed_node_template
		else:
			entry_template = default_node_template

		# Get/update the predecessor timestamp
		if pid in pid_to_node:
			pred = pid_to_node[pid]
		else:
			pred = None

		if pid not in pid_to_first_x:
			pid_to_first_x[pid] = x
		elif entry_template == default_node_template and skip_nonproc:
			continue

		pid_to_node[pid] = entry.timestamp

		# Generate node
		if not len(entry.syscall_arguments) == 0:
			args = str(entry.syscall_arguments)
			args = args.replace('\'', '"')
			args = args + ' / ' + str(entry.return_value)
		else:
			args = entry.return_value

		node = entry_template.format(
				ts=entry.timestamp,
				syscall=entry.syscall_name,
				arguments=args,
				xx=x,
				yy=y,
				)

		nodes = nodes + node

		x = x + 25

		# Generate edge
		if not pred is None:
			edge = edge_template.format(
					f=pred,
					t=entry.timestamp,
					)
			
			edges = edges + edge

	for pid,x in pid_to_first_x.iteritems():
		label = label_node_template.format(
				pid=pid,
				label=pid,
				xx=(x - 50),
				yy=pid_to_y[pid],
				)

		nodes = nodes + label

	f_out.write(document_template.format(
			nodes=nodes,
			edges=edges,
			))

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
	sys.stderr.write('  -c, --compress     Skip non process related syscalls\n')


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
		options, remainder = getopt.gnu_getopt(argv, 'hco:',
			['help', 'compress', 'output='])

		skip  = False
		
		for opt, arg in options:
			if opt in ('-h', '--help'):
				usage()
				return
			elif opt in ('-o', '--output'):
				output_file = arg
			elif opt in ('-c', '--compress'):
				skip = True
		
		if len(remainder) > 1:
			raise Exception("Too many options")
		elif len(remainder) == 1:
			input_file = remainder[0]
	except Exception as e:
		sys.stderr.write("%s: %s\n" % (os.path.basename(sys.argv[0]), e))
		sys.exit(1)
	
	
	# Convert to .html

	try:
		convert2js(input_file, output_file, skip)
	except IOError as e:
		sys.stderr.write("%s: %s\n" % (os.path.basename(sys.argv[0]), e))
		sys.exit(1)


#
# Entry point to the application
#
if __name__ == "__main__":
	main(sys.argv[1:])
