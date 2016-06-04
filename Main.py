from DialogParser import DialogParser
from SessionReader import SessionReader
from nltk.draw.tree import TreeView

import nltk

x = ['inform-my_name', 'inform-welcome', 'request-weather', 'implicit_confirm-datetime_date',
     'request-geography_city', 'implicit_confirm-geography_city',
     'inform-weather']

p = DialogParser()
p.load_rule_from_path("/Users/Tony/Documents/intellIJWorkSpace/HRL-RavenClawJava/log/grammar.txt")

reader = SessionReader()
reader.parse_session_log("/Users/Tony/Documents/intellIJWorkSpace/HRL-RavenClawJava/log/sessions/11001D2016-06-03T22-05-21.log")
sys_str_tree = reader.cur_log.get('parseTree')
sys_tree = nltk.Tree.fromstring(sys_str_tree)

TreeView(sys_tree)._cframe.print_to_file('original.ps')

terminals = sys_tree.leaves()
print reader.print_turns()

c = p.parse(terminals)

p_trees = p.get_parses(False)
print "Found " + str(len(p_trees)) + " trees."
if p_trees is not None:
    for idx, tree in enumerate(p_trees):
        TreeView(tree)._cframe.print_to_file(str(idx)+'.ps')