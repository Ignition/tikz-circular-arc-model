#!/usr/bin/env python

import json
import sys
import os.path
import math
from django.template import Template, Context
from django.conf import settings
settings.configure()
from pprint import pprint
import itertools

dist_scale = 0.7
max_dist = 3

twopi = 2.0*math.pi

clique_index = []

latex_template = Template('\
\documentclass[tikz]{standalone}\n\
\usepackage{amsmath, amsthm, amssymb}\n\
\usepackage{tkz-euclide}\n\
\usetkzobj{all}\n\
\usetikzlibrary{calc}\n\
\\begin{document}\n\
\\begin{tikzpicture}[scale={{ scale }}]\n\
\coordinate (centre) at (0,0);\n\
\n{{ coords }}\n\
\n{{ extra }}\n\
\draw[dashed] (centre) circle ({{ circle }});\n\
\n{{ arcs }}\n\
\end{tikzpicture}\n\
\end{document}')

def coord_template(num, total):
	v_sin = round(2.0*math.sin(twopi*num/total),5)
	v_cos = round(2.0*math.cos(twopi*num/total),5)
	latex_template = Template('\coordinate (p{{ num }}) at ( {{ sin }} , {{ cos }} );\n')
	c = Context({"num": num, "cos": v_cos, "sin": v_sin})
	return latex_template.render(c)

def arc_template(name, start, end, total, dist):
	overhang_deg = (360.0/total)/5
	overhang_rad = twopi*overhang_deg/360
	position = twopi*start/total
	scale = dist_scale*(dist+0.3)
	v_sin = round(scale*math.sin(position - 0.9*overhang_rad),5)
	v_cos = round(scale*math.cos(position - 0.9*overhang_rad),5)
	latex_template = Template('\
\\tkzDrawArc[R with nodes, delta={{ overhang }}](centre,{{ dist }})(p{{ end }},p{{ start }});\n\
\\node (LABEL-{{ start }}-{{ end }}) at ({{ sin }}, {{ cos }}) {${{ name }}$};\n')
	c = Context({"name": name, "cos": v_cos, "sin": v_sin, "dist": dist_scale*dist, "start":start,"end":end,"overhang":overhang_deg})
	return latex_template.render(c)

def region_template(start, end, total):
	scale1 = dist_scale*(max_dist + 0.1)
	scale2 = dist_scale*(2.0 - 0.1)
	overhang_deg = (360.0/total)/5
	overhang_rad = twopi*overhang_deg/360
	position1 = twopi*start/total
	position2 = twopi*end/total
	v_sin_s1 = round(scale2*math.sin(position1-overhang_rad),5) #10deg ~=0.175rad
	v_cos_s1 = round(scale2*math.cos(position1-overhang_rad),5) #10deg ~=0.175rad
	v_sin_e1 = round(scale2*math.sin(position2+overhang_rad),5) #10deg ~=0.175rad
	v_cos_e1 = round(scale2*math.cos(position2+overhang_rad),5) #10deg ~=0.175rad
	v_sin_s2 = round(scale1*math.sin(position1-overhang_rad),5) #10deg ~=0.175rad
	v_cos_s2 = round(scale1*math.cos(position1-overhang_rad),5) #10deg ~=0.175rad
	latex_template = Template('\\fill[red!50]\
( {{ sins1 }} , {{ coss1 }}) -- ( {{ sins2 }} , {{ coss2 }})\
arc[end angle={-{{ end }}*360/ {{ total }}+90-{{ overhang }}}, start angle={-{{ start }}*360/ {{ total }}+90+ {{ overhang }}},radius={{ dist }}] -- \
({{ sine1 }}, {{ cose1 }})\
arc[end angle={-{{ start }}*360/ {{ total }}+90+ {{ overhang }}}, start angle={-{{ end }}*360/ {{ total }}+90- {{ overhang }}},radius={{ dist2 }}] ;')
	c = Context({"sins1": v_sin_s1, "coss1": v_cos_s1, "sins2": v_sin_s2, "coss2": v_cos_s2, "end":end,"total":total,"start":start,"dist":scale1,"sine1":v_sin_e1,"cose1":v_cos_e1,"dist2":scale2,"overhang":overhang_deg})
	return latex_template.render(c)

def next_free(arc):
	if arc["start"] <= arc["end"]:
		not_free = itertools.chain(*clique_index[arc["start"]:arc["end"]+1])
	else:
		not_free = itertools.chain(*clique_index[0:arc["end"]+1])
		not_free = itertools.chain(not_free, itertools.chain(*clique_index[arc["start"]:]))
	not_free = filter(lambda x: "dist" in x, not_free)
	not_free = set(x["dist"] for x in not_free)
	dist = 3
	while dist in not_free:
		dist += 1
	return dist

def helper(d, dists_done, arcs, clique_num):
	global max_dist
	if "dist" not in d:
		dist = next_free(d)
		max_dist = max(max_dist, dist)
		arcs += arc_template(d["label"], d["start"], d["end"], clique_num, dist)
		d["dist"] = dist
		dists_done.add(dist)
	else:
		dists_done.add(d["dist"])
	return arcs

def main():
	global clique_index

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

		options = None
		if "options" in data:
			options = data["options"]
		data = data["arcs"]

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
		in_clique = []
		while len(s_sort) != 0 and len(e_sort) != 0:
			if s_sort[0]["start"] <= e_sort[0]["end"]:
				d = s_sort[0]
				s_sort.pop(0)
				if start_seq != True:
					clique_num += 1
					start_seq = True
				d["start"] = clique_num
				in_clique.append(d)
			else:
				d = e_sort[0]
				e_sort.pop(0)
				if start_seq == True:
					clique_index.append(list(in_clique))
					start_seq = False
				d["end"] = clique_num
				if d in in_clique:
					in_clique.remove(d)
		for d in s_sort:
			d["start"] = 0
			for cn in xrange(d["end"]+1):
				clique_index[cn].append(d)
		for d in e_sort:
			if start_seq == True:
				clique_index.append(list(in_clique))
				start_seq = False
			d["end"] = clique_num
			if d in in_clique:
				in_clique.remove(d)
		for d in in_clique:
			for cn in xrange(d["end"]+1):
				clique_index[cn].append(d)

		# correct to get clique count
		clique_num += 1

		coords = ''
		arcs = ''
		#create evenly spaced clique points
		for i in xrange(clique_num):
			coords += coord_template(i, clique_num)
			# get arcs that need placing here
			to_place = clique_index[i]
			dists_done = set()
			#filter out those allocated
			to_place = filter(lambda x: "dist" not in x, to_place)
			#sort by arc length
			to_place.sort(reverse=True, key=lambda x: (x["end"] - x["start"] + 1) if (x["start"] <= x["end"]) else (clique_num - x["start"] + x["end"] + 1))
			for d in to_place:
				arcs = helper(d, dists_done, arcs, clique_num)


		#show-intersection
		extra = ''
		if options != None and "show-intersection" in options:
			a, b = options["show-intersection"]
			arca = filter(lambda x: x["label"] == a, data)[0]
			arcb = filter(lambda x: x["label"] == b, data)[0]
			if arca["start"] > arcb["start"]:
				arca, arcb = arcb, arca
			if arca["start"] <= arca["end"]:
				if arcb["start"] <= arcb["end"]:
					if arcb["start"] <= arca["end"]:
						extra += region_template(arcb["start"], min(arca["end"],arcb["end"]), clique_num)
				else:
					if arcb["start"] <= arca["end"]:
						extra += region_template(arcb["start"], arca["end"], clique_num)
					if arca["start"] <= arcb["end"]:
						extra += region_template(arca["start"], arcb["end"], clique_num)
			else:
				if arcb["start"] <= arcb["end"]:
					extra += region_template(arcb["start"], min(arca["end"],arcb["end"]), clique_num)
				else:
					if arca["start"] <= arcb["end"]:
						extra += region_template(arca["start"], arcb["end"], clique_num)
						extra += region_template(arcb["start"], arca["end"], clique_num)
					else:
						extra += region_template(arcb["start"], min(arca["end"],arcb["end"]), clique_num)

		c = Context({"coords":coords,"arcs":arcs,"extra":extra,"circle": 1.0/dist_scale,"scale":0.8 })
		print latex_template.render(c)

if __name__ == '__main__':
	main()
