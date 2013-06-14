tikz-circular-arc-model
=======================

This repo is a set of utilities that aid in creation of circular-arc models with acceptable layout to be used in academic papers. These are generated using a simple json input representation which outputs tikz which can be included into your latex documents with ease. The layout of arcs will ignore the alsolute positions around the circle and instead draw a clear and spaced out diagram.

Example usage
-------------

Create a json file with all the arcs your model requires, each arc needs a label a start and end position.

```json
	{
		"arcs": [
			{"label": "a", "start":  50, "end": 100},
			{"label": "b", "start":  50, "end":  50},
			{"label": "c", "start": 100, "end": 200},
			{"label": "d", "start": 200, "end": 300},
			{"label": "e", "start": 300, "end": 400},
			{"label": "f", "start": 400, "end": 100}
		],
		"options": {}
	}
```

Then call the generate script to make LaTeX code for the circular-arc diagram.

```bash
	./generate.py example1.json
```

If you want to make pdf images to include into your document then just pipe it through `pdflatex`

```bash
	python ./generate.py example1.json | pdflatex --jobname outfile --
```

For the json given above you can expect the following circular-arc diagram to be generated:

![Circular-arc model](https://raw.github.com/Ignition/tikz-circular-arc-model/master/example1.png)

You may also add into options `"show-intersection": ["a","b"]` which would give a graph like this:

![Circular-arc model](https://raw.github.com/Ignition/tikz-circular-arc-model/master/example2.png)

