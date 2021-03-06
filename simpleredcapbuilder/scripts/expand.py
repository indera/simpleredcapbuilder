#!/Users/pagapow/anaconda/bin/python
"""
Convert a compact REDCap data dictionary to the full and proper form.
"""

### IMPORTS

### CONSTANTS & DEFINES

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import open
from future import standard_library
standard_library.install_aliases()

import csv
import os

from simpleredcapbuilder import __version__ as version
from simpleredcapbuilder import ExpDataDictReader
from simpleredcapbuilder import ExpandDbSchema, render_template
from simpleredcapbuilder import consts
from simpleredcapbuilder import PostValidator
from simpleredcapbuilder import ext_from_path, ext_to_format, parse_ext_vars


### CODE ###

### UTILS

import pprint
pp = pprint.PrettyPrinter (indent=2)

def pprint (x):
	pp.pprint (x)


### MAIN

def parse_clargs ():
	import argparse
	aparser = argparse.ArgumentParser()

	aparser.add_argument ('infile', help='compact REDCap file to be processed')

	aparser.add_argument ('-o', "--outfile",
		help='output expanded redcap data dictionary',
		default=None,
	)

	aparser.add_argument('-i', '--include-tags', action='append',
		help='only include untagged sections or those with this tag',
	)

	aparser.add_argument('-n', '--name', action='store_true',
		help='name the output file for the tags passed in',
		default=False,
	)

	aparser.add_argument ('-v', "--include-vars",
		help='include external file of variables',
		default=None,
	)

	args = aparser.parse_args()

	filename, file_ext = os.path.splitext (args.infile)
	args.fileroot = args.infile.replace (file_ext, '')

	if args.outfile == None:
		if args.name and args.include_tags:
			ext = '.inc-%s.expanded.csv' % '-'.join (args.include_tags)
		else:
			ext = '.expanded.csv'
		args.outfile = args.fileroot + ext

	assert (args.infile != args.outfile)

	return args


def parse_included_vars (inc_var_pth):
	ext = ext_from_path (inc_var_pth)
	fmt = ext_to_format (ext)
	data = open (inc_var_pth, 'rU').read()
	return parse_ext_vars (data, fmt)



def main ():
	args = parse_clargs()

	# read in compact dd and parse out structure
	print ("Parsing & validating input file ...")
	rdr = ExpDataDictReader()
	exp_dd_struct = rdr.parse (args.infile)

	# read in compact dd and parse out structure
	if args.include_vars:
		print ("Parsing file of included variables ...")
		inc_vars = parse_included_vars (args.include_vars)
	else:
		inc_vars = {}

	# dump structure as json
	print ("Dumping structure as JSON ...")
	import json
	json_pth = args.fileroot + '.json'
	with open (json_pth, 'w') as out_hndl:
	    json.dump (exp_dd_struct, out_hndl, indent=3)

	# expand structure to templ
	print ("Expanding structure to template ...")
	tmpl_pth = args.fileroot + '.jinja'
	xpndr = ExpandDbSchema()
	xpndr.expand (exp_dd_struct, using_tags=args.include_tags, out_pth=tmpl_pth)

	# now render the template
	print ("Rendering template ...")
	with open (tmpl_pth, 'rU') as in_hndl:
		tmpl_data = in_hndl.read()
	# XXX: need a better way to handle this
	inc_vars['tags'] = args.include_tags
	exp_tmpl = render_template (tmpl_data, inc_vars)
	print ("Saving template as data dictionary ...")
	with open (args.outfile, 'w') as out_hndl:
		out_hndl.write (exp_tmpl)

	# do the postvalidation
	print ("Post-validating output data dictionary ...")
	with open (args.outfile, 'rU') as in_hndl:
		rdr = csv.DictReader (in_hndl)
		recs = [r for r in rdr]
		pvalidator = PostValidator()
		pvalidator.check (recs)

	print ("Done.")



if __name__ == '__main__':
	import sys
	main()
	sys.exit (0)


### END ###
