#!/usr/bin/env python

import json
import sys
import os.path
import math
from django.template import Template, Context
from django.conf import settings
settings.configure()
from pprint import pprint

dist_scale = 0.7
max_dist = 3

twopi = 2.0*math.pi

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
	offset = 0.9*(twopi/total)/5
	overhang = (360.0/total)/5
	v_sin = round(dist_scale*(dist+0.3)*math.sin(twopi*start/total - offset),5)
	v_cos = round(dist_scale*(dist+0.3)*math.cos(twopi*start/total - offset),5)
	latex_template = Template('\
\\tkzDrawArc[R with nodes, delta={{ overhang }}](centre,{{ dist }})(p{{ end }},p{{ start }});\n\
\\node (LABEL-{{ start }}-{{ end }}) at ({{ sin }}, {{ cos }}) {${{ name }}$};\n')
	c = Context({"name": name, "cos": v_cos, "sin": v_sin, "dist": dist_scale*dist, "start":start,"end":end,"overhang":overhang})
	return latex_template.render(c)

def region_template(start, end, total):
	dist = dist_scale*(max_dist + 0.1)
	dist2 = dist_scale*(2.0 - 0.1)
	overhang_deg = (360.0/total)/5
	overhang_rad = twopi*overhang_deg/360
	v_sin_s1 = round(dist2*math.sin(twopi*start/total-overhang_rad),5) #10deg ~=0.175rad
	v_cos_s1 = round(dist2*math.cos(twopi*start/total-overhang_rad),5) #10deg ~=0.175rad
	v_sin_e1 = round(dist2*math.sin(twopi*end/total+overhang_rad),5) #10deg ~=0.175rad
	v_cos_e1 = round(dist2*math.cos(twopi*end/total+overhang_rad),5) #10deg ~=0.175rad
	v_sin_s2 = round(dist*math.sin(twopi*start/total-overhang_rad),5) #10deg ~=0.175rad
	v_cos_s2 = round(dist*math.cos(twopi*start/total-overhang_rad),5) #10deg ~=0.175rad
	latex_template = Template('\\fill[red!50]\
( {{ sins1 }} , {{ coss1 }}) -- ( {{ sins2 }} , {{ coss2 }})\
arc[end angle={-{{ end }}*360/ {{ total }}+90-{{ overhang }}}, start angle={-{{ start }}*360/ {{ total }}+90+ {{ overhang }}},radius={{ dist }}] -- \
({{ sine1 }}, {{ cose1 }})\
arc[end angle={-{{ start }}*360/ {{ total }}+90+ {{ overhang }}}, start angle={-{{ end }}*360/ {{ total }}+90- {{ overhang }}},radius={{ dist2 }}] ;')
	c = Context({"sins1": v_sin_s1, "coss1": v_cos_s1, "sins2": v_sin_s2, "coss2": v_cos_s2, "end":end,"total":total,"start":start,"dist":dist,"sine1":v_sin_e1,"cose1":v_cos_e1,"dist2":dist2,"overhang":overhang_deg})
	return latex_template.render(c)


def helper(d, dists_done, arcs, clique_num):
	global max_dist
	if "dist" not in d:
		dist = 3
		while (dist in dists_done):
			dist += 1
		max_dist = max(max_dist, dist)
		arcs += arc_template(d["label"], d["start"], d["end"], clique_num, dist)
		d["dist"] = dist
		dists_done.add(dist)
	else:
		dists_done.add(d["dist"])
	return arcs

def main():
	global dist_scale
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

		#dist_scale /= 3
		#dist_scale *= clique_num

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
			to_place.sort(reverse=True, key=lambda x: "dist" in x)
			while len(to_place) != 0 and "dist" in to_place[0]:
				dists_done.add(to_place[0]["dist"])
				to_place = to_place[1:]
			to_place.sort(reverse=True, key=lambda x: (x["end"] - x["start"] + 1) if (x["start"] <= x["end"]) else (clique_num - x["start"] + x["end"] + 1))
			for d in to_place:
				arcs = helper(d, dists_done, arcs, clique_num)
		extra = ''
		if "show-intersection" in options:
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
