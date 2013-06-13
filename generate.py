#!/usr/bin/env python

import json
import sys
import os.path
import math
from django.template import Template, Context
from django.conf import settings
settings.configure()
from pprint import pprint

dist_scale = 0.5

latex_template = Template('\
\documentclass[tikz]{standalone}\n\
\usepackage{amsmath, amsthm, amssymb}\n\
\usepackage{tkz-euclide}\n\
\usetkzobj{all}\n\
\usetikzlibrary{calc}\n\
\\begin{document}\n\
\\begin{tikzpicture}[scale=.7]\n\
\coordinate (centre) at (0,0);\n\
\n{{ coords }}\n\
\draw[dashed] (centre) circle (1);\n\
\n{{ arcs }}\n\
\end{tikzpicture}\n\
\end{document}')

def coord_template(num, total):
	v_sin = round(2.0*math.sin(2.0*num*math.pi/total),5)
	v_cos = round(2.0*math.cos(2.0*num*math.pi/total),5)
	latex_template = Template('\coordinate (p{{ num }}) at ( {{ sin }} , {{ cos }} );\n')
	c = Context({"num": num, "cos": v_cos, "sin": v_sin})
	return latex_template.render(c)

def arc_template(name, start, end, total, dist):
	v_sin = round(float(dist)*math.sin(2.0*start*math.pi/total - 0.35),5) # 0.35rad ~= 20deg
	v_cos = round(float(dist)*math.cos(2.0*start*math.pi/total - 0.35),5)
	latex_template = Template('\
\\tkzDrawArc[R with nodes, delta=10](centre,{{ dist }})(p{{ end }},p{{ start }});\n\
\\node (LABEL-{{ start }}-{{ end }}) at ({{ sin }}, {{ cos }}) {${{ name }}$};\n')
	c = Context({"name": name, "cos": v_cos, "sin": v_sin, "dist": dist, "start":start,"end":end})
	return latex_template.render(c)

def helper(d, dists_done, arcs, clique_num):
	if "dist" not in d:
		dist = 3
		while (dist in dists_done):
			dist += 1
		arcs += arc_template(d["label"], d["start"], d["end"], clique_num, dist_scale*dist)
		d["dist"] = dist
		dists_done.add(dist)
	else:
		dists_done.add(d["dist"])
	return arcs

def main():
	if len(sys.argv) != 2:
		sys.stderr.write('Usage: {0} {{file}}\n'.format(sys.argv[0]))
		sys.exit(1)
	elif not os.path.isfile(sys.argv[1]):
		sys.stderr.write('Error: File {0} not found\n'.format(sys.argv[1]))
		sys.exit(1)
	else:
		file_name = sys.argv[1]
		with open(file_name) as data_file:
			data = json.load(data_file)

		#offset all the posiitons, such that at least one start is equal to 0
		min_start = min(data, key=lambda d: d["start"])["start"]
		max_pos   = max(data, key=lambda d: max(d["start"],d["end"]))
		max_pos   = max(max_pos["start"], max_pos["end"])
		for d in data:
			d["start"] -= min_start
			d["end"]   -= min_start
			if d["end"] < 0:
				d["end"] += max_pos

		#sort by start/end position
		s_sort = sorted(data, key=lambda d: d["start"])
		e_sort = sorted(data, key=lambda d: d["end"])

		#reposition depending on clique grouping
		clique_num = 0
		start_seq = True
		while len(s_sort) != 0 and len(e_sort) != 0:
			if s_sort[0]["start"] <= e_sort[0]["end"]:
				d = s_sort[0]
				s_sort.pop(0)
				if start_seq != True:
					clique_num += 1
					start_seq = True
				d["start"] = clique_num
			else:
				d = e_sort[0]
				e_sort.pop(0)
				if start_seq == True:
					start_seq = False
				d["end"] = clique_num
		while len(s_sort) != 0:
			d = s_sort[0]
			s_sort.pop(0)
			d["start"] = 0
		while len(e_sort) != 0:
			d = e_sort[0]
			e_sort.pop(0)
			d["end"] = clique_num

		# correct to get clique count
		clique_num += 1

		coords = ''
		arcs = ''
		#create evenly spaced clique points
		for i in xrange(clique_num):
			coords += coord_template(i, clique_num)
			# get arcs that need placing here
			to_place = []
			for d in data:
				if d["start"] <= d["end"]:
					if d["start"] <= i and d["end"] >= i:
						to_place.append(d)
				else:
					if d["start"] <= i or d["end"] >= i:
						to_place.append(d)
			dists_done = set()
			#sort by arc length
			to_place.sort(reverse=True, key=lambda x: (x["end"] - x["start"] + 1) if (x["start"] <= x["end"]) else (clique_num - x["start"] + x["end"] + 1))
			for d in to_place:
				arcs = helper(d, dists_done, arcs, clique_num)
		c = Context({"coords":coords,"arcs":arcs})
		print latex_template.render(c)



if __name__ == '__main__':
	main()
