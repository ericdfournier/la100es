#%% Package Imports

import graphviz

#%% Single-Family Decision Tree

dot = graphviz.Digraph(comment="A graph", format="svg")
dot.node('A', 'Pre-1978')
dot.node('B', 'Post-1978')

dot.node('C', '<1,000 sqft.')
dot.node('D', '1,000-2,000 sqft.')
dot.node('E', '2,000-3,000 sqft.')
dot.node('F', '3,000-4,000 sqft.')
dot.node('G', '4,000-5,000 sqft.')
dot.node('H', '5,000-8,000 sqft.')
dot.node('I', '8,000-10,000 sqft.')
dot.node('J', '10,000-20,000 sqft.')
dot.node('K', '10,000-20,000 sqft.')
dot.node('L', '>20,000 sqft.')

dot.edge('A', 'C')
dot.edge('A', 'D')
dot.edge('A', 'E')
dot.edge('A', 'F')
dot.edge('A', 'G')
dot.edge('A', 'H')
dot.edge('A', 'I')
dot.edge('A', 'J')
dot.edge('A', 'K')
dot.edge('A', 'L')

dot.render('digraph.gv', view=True)
