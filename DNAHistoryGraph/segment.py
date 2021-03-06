#!/usr/bin/env python

import side
import thread
from traversal import Traversal
from label import Label
from collections import Counter

class Segment(object):
	""" DNA history segment """

	##########################
	## Basics
	##########################
	def __init__(self, sequence=None, parent = None, children = []):
		if sequence is not None:
			self.label = Label(self, sequence)
		else:
			self.label = None
		self.children = set()
		for child in children:
			self.createBranch(child)
		self.parent = None
		if parent != None:
			parent.createBranch(self)
		self.right = None
		self.left = side.Side(self, True)
		self.right = side.Side(self, False)

	def __cmp__(self, other):
		return cmp(id(self), id(other))

	def __copy__(self):
		return Segment(self.label)

	def __str__(self):
		return str(self.label)

	def __hash__(self):
		return id(self)
	
	def getSide(self, left=True):
		if left:
			return side.left
		return side.right

	def sides(self):
		""" Returns list of segment sides """
		return [self.left, self.right]
	
	def createBranch(self, other):
		""" Creates branch between segments """
		assert other
		self.children.add(other)
		other.parent = self

	def deleteBranch(self, other):
		""" Removes branch between segments """
		self.children.remove(other)
		other.parent = None
		
	def setLabel(self, sequence):
		"""Safely set the label of a segment. #put in for future in which we move to storing lifted labels
		"""
		self.label = Label(self, sequence)
		
	def deleteLabel(self):
		"""Safely delete the label of a segment. #put in for future in which we move to storing lifted labels
		"""
		self.label = None

	def getSide(self, left):
		if left:
			return self.left
		else:
			return self.right

	def disconnect(self):
		"""Destroy pointers to this segment """
		self.left.deleteBond()
		self.right.deleteBond()
		for child in self.children:
			child.parent = self.parent
		if self.parent is not None:
			self.parent.children |= self.children
			self.parent.children.remove(self)
		self.children = set()
		self.parent = None
			
	##########################
	## Lifted labels
	##########################

	def _ancestor2(self):
		if self.label is not None or self.parent is None:
			return self
		else:
			return self.parent._ancestor2()

	def ancestor(self):
		if self.parent is None:
			return self
		else:
			return self.parent._ancestor2()

	def _liftedLabels2(self,):
		if self.label is None:
			return self.liftedLabels()
		else:
			return set([ self ])
	
	def liftedLabels(self):
		""" Returns set of labeled segments whose lifting ancestor is self"""
		if len(self.children) == 0:
			return set()
		return set(reduce(lambda x, y : x | y, [x._liftedLabels2() for x in self.children]))
	
	def nonTrivialLiftedLabels(self):
		return set([ i for i in self.liftedLabels() if i.label != self.label ])

	##########################
	## Ambiguity
	##########################

	def substitutionAmbiguity(self):
		if self.label == None and self.parent != None:
			return 0
		return max(0, len(self.nonTrivialLiftedLabels()) - 1)

	def rearrangementAmbiguity(self):
		return self.left.rearrangementAmbiguity() + self.right.rearrangementAmbiguity()
	
	def ambiguity(self):
		return self.substitutionAmbiguity() + self.rearrangementAmbiguity()
	
	def isJunction(self):
		if self.label == None:
			return False
		return len(self.liftedLabels()) > 1

	def isBridge(self):
		if self.label == None:
			return False
		return self.parent != None and self.ancestor().label != None and str(self.ancestor().label) == str(self.label) and len(self.nonTrivialLiftedLabels()) > 0 and len(self.ancestor().nonTrivialLiftedLabels()) > 0

	##########################
	## Cost
	##########################
	
	def lowerBoundSubstitutionCost(self):
		if self.label == None and self.parent != None:
			return 0
		return max(0, len(set([ str(x.label) for x in self.nonTrivialLiftedLabels() ])) - (self.label == None))
	
	def upperBoundSubstitutionCost(self):
		if self.label == None and self.parent != None:
			return 0
		nTLabels = self.nonTrivialLiftedLabels()
		i = 0
		if self.label == None and len(nTLabels) > 0:
			i = Counter([ str(x.label) for x in nTLabels ]).most_common()[0][1]
		return len(nTLabels) - i

	##########################
	## Threads
	##########################
	def thread(self):
		return thread.Thread([Traversal(self, True)])

	def threads(self, data):
		threads, segmentThreads = data
		if self in segmentThreads:
			return data
		else:
			thread = self.thread()
			for traversal in thread:
				segmentThreads[traversal.segment] = thread
			threads.add(thread)

			return threads, segmentThreads

	##########################
	## Output
	##########################
	def dot(self):
		if self.label != None:
			labelColour = { 'A':"greenyellow", 'C':'rosybrown', 'G':"powderblue", 'T':"plum" }[str(self.label)]
		else:
			labelColour = "white"
		colour = "black"
		if self.parent == None:
			colour = "grey"
		lines = ['%i [label="", style=filled, fillcolor=%s, width=0.25, height=0.25, color=%s, fixedsize=true]' % (id(self), labelColour, colour)]
		if self.parent is not None:
			if (self.label != None and self.ancestor().label == self.label) or (self.label == None and len(self.liftedLabels().intersection(self.ancestor().nonTrivialLiftedLabels())) == 0): 
				lines.append('%i -> %i [color=green, weight=1000]' % (id(self.parent), id(self)))
			else:
				if self.parent.parent == None:
					lines.append('%i -> %i [color=lightblue, weight=1000]' % (id(self.parent), id(self)))
				else:
					lines.append('%i -> %i [color=blue, weight=1000]' % (id(self.parent), id(self)))
		lines.append(self.left.dot())
		if self.left.bond is not self.right:
			lines.append(self.right.dot())
		return "\n".join(lines)	
		
	
	##########################
	## Validation
	##########################
	def validate(self):
		assert self.parent is None or self in self.parent.children
		assert all(self is child.parent for child in self.children)
		assert self.left.validate()
		assert self.right.validate()
		assert self.lowerBoundSubstitutionCost() <= self.upperBoundSubstitutionCost()
		return True
