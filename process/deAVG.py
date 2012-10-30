#!/usr/bin/env python
import copy

from pyAVG.DNAHistoryGraph.graph import DNAHistoryGraph
from pyAVG.inputs.simulator import RandomHistory

def deAVG(avg):
	# Copy graph
	graph = copy.copy(avg)

	# Remove all non-root or leaf segments
	for segment in list(graph.segments):
		if segment.parent is not None and len(segment.children) > 0:
			segment.left.deleteBond()
			segment.right.deleteBond()
			for child in segment.children:
				child.parent = segment.parent
				segment.parent.children.add(child)
			segment.parent.children.remove(segment)
			graph.segments.remove(segment)

	# Recompute the event graph from scratch
	graph.eventGraph, graph.segmentThreads = graph.threads()
	graph.timeEventGraph()
	return graph

def test_main():
	history = RandomHistory(10, 10)
	avg = history.avg()
	assert avg.validate()
	graph = deAVG(avg)
	assert graph.validate()

if __name__ == "__main__":
	test_main()