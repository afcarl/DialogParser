import re

class Utils(object):
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