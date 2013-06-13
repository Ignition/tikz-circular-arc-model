tikz-circular-arc-model
=======================

Utilities to aid in creating circular-arc models with acceptable layout. These are generated using tikz and can be included into your latex document with ease. Layout will ignore arcs alsolute possitions around the circle.

Example usage
-------------

Create a json file with all the arcs your model requires, each arc needs a label a start and end position.

	[
		{"label": "a", "start":  50, "end": 100},
		{"label": "b", "start":  50, "end":  50},
		{"label": "c", "start": 100, "end": 200},
		{"label": "d", "start": 200, "end": 300},
		{"label": "e", "start": 300, "end": 400},
		{"label": "f", "start": 400, "end": 100}
	]

Then call the python generate script to make LaTeX code for the circular-arc diagram.

	./generate.py example1.json

If you want to make pdf images to include into your document then just pipe it through `pdflatex`

	python ./generate.py example1.json | pdflatex --jobname outfile --

That should give you pdf files which you can include into LaTeX documents which look like this:
![Circular-arc model](https://raw.github.com/Ignition/tikz-circular-arc-model/master/example1.png)
