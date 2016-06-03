from EarleyParser import EarleyParser
import nltk

"""
USAGE EXAMPLE
rules = {'S':[['NP', 'VP']],
         'NP': [['art', 'adj', 'n'], ['art', 'n'], ['adj', 'n']],
         'VP':[['aux', 'VP'], ['v', 'NP']]}
x = ['art', 'adj', 'n', 'aux', 'v', 'art', 'n', 'eos']
parser = EarleyParser(rules)
c = parser.parse(x)
"""

p = EarleyParser()
p.load_rule_from_path("/Users/Tony/Documents/intellIJWorkSpace/HRL-RavenClawJava/log/grammar.txt")

x = ['inform-my_name', 'inform-welcome', 'request-weather', 'implicit_confirm-datetime_date',
     'request-geography_city', 'implicit_confirm-geography_city',
     'inform-weather']
xx = [u'inform-my_name',
 u'inform-welcome',
 u'request-cambridge',
 u'cambridge_newcall',
 u'cambridge_next']
c = p.parse(xx)
p.print_chart()
p_trees = p.get_parses(False)
if p_trees is not None:
    p_trees[1].draw()
