import re
import nltk


class Utils(object):
    @staticmethod
    def resolve_unbalanced_parse(parse):
        forward_cnt = parse.count('(')
        backward_cnt = parse.count(')')
        if forward_cnt > backward_cnt:
            return parse + ")"*(forward_cnt - backward_cnt)
        else:
            return "("*(backward_cnt-forward_cnt) + parse

    @staticmethod
    def node_label(tree):
        if type(tree) is not nltk.Tree:
            return tree
        else:
            return tree.label()

    @staticmethod
    def find_nth(source, target, n):
        return source.replace(target, "$"*len(target), n-1).find(target)

    @staticmethod
    def rev_replace(s, old, new, occurrence):
        li = s.rsplit(old, occurrence)
        return new.join(li)

    @staticmethod
    def clean_parse(parse):
        norm_parse = re.sub(' +', ' ', parse)
        norm_parse = re.sub('\( +', '(', norm_parse)
        norm_parse = re.sub(' +\)', ')', norm_parse)
        return norm_parse

#print Utils.resolve_unbalanced_parse('()))')
#print Utils.resolve_unbalanced_parse('((()')