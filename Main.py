from DialogParser import DialogParser
from SessionReader import SessionReader
from nltk.draw.tree import TreeView

import nltk

x = ['inform-my_name', 'inform-welcome', 'request-weather',
     'request-geography_city', 'implicit_confirm-geography_city','inform-weather']

p = DialogParser()
p.load_grammar_from_path("/Users/Tony/Documents/intellIJWorkSpace/HRL-RavenClawJava/log/grammar.txt")
print p.print_grammar()

reader = SessionReader()
log_path = "/Users/Tony/Documents/intellIJWorkSpace/HRL-RavenClawJava/log/sessions/11001D2016-06-03T22-05-21.log"
#log_path = "/Users/Tony/Documents/intellIJWorkSpace/HRL-RavenClawJava/log/sessions/11001D2016-06-04T00-26-55.log"

reader.parse_session_log(log_path)
sys_str_tree = reader.cur_log.get('parseTree')
sys_tree = nltk.Tree.fromstring(sys_str_tree)

terminals = sys_tree.leaves()
reader.print_turns()
print terminals

c = p.parse(x)

p_trees = p.get_parses(False)

if p_trees is not None:
    TreeView(sys_tree)._cframe.print_to_file('imgs/original.ps')
    print "Found " + str(len(p_trees)) + " trees."
    for idx, tree in enumerate(p_trees):
        TreeView(tree)._cframe.print_to_file('imgs/'+str(idx)+'.ps')
        break
else:
    print "No parse found!"
    p.print_chart(with_parse=False)