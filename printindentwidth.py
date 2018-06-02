"""SRT 25th May 2018. Given a string or list, print contents in accordance with
the indentation and width per line specified.
"""


def PrintIndentWidth(S_in, indent=0, width=0):
    """EGOF function for pretty print with indent and width. Arg1 can be a
       list, tuple, set, dict or string
    """
    def StartNewLine(item, chars_used, S_indent):
        """Keep track of how many chars used this line. If 'item' is going
         to go past indent+width then write CR and start a new line
        """
        if width:
            chars_item = len(str(item))
            if chars_used + chars_item + len(S_indent) > width:
                print "\n", S_indent,              #start a new indented line
                chars_used = chars_item            #reset
            else:
                chars_used += chars_item           #accum
        return chars_used
    #-----------------------------
    
    #sets, lists, tuples, dicts, strings all need a little different treatment
    if isinstance(S_in, set):     #EGOF isinstance. types module is deprecated
        S_in = list(S_in)         #convert to a list

    chars_used = 0             #chars used on line so far
    S_indent = indent*' '
    print S_indent,
    if isinstance(S_in, list) or isinstance(S_in, tuple):
        #treat each list item as an item
        for i in range(len(S_in)):
            chars_used = StartNewLine(S_in[i], chars_used, S_indent)
            print S_in[i],                     #no <CR>
            if i < len(S_in)-1: print ",",    #no comma for last i
        print "\n"
    elif isinstance(S_in, dict):
        #treat each dict item as a string, S2
        S_in = S_in.items()    #convert to a key, value list
        print "{",
        for i in range(len(S_in)):
            k,v = S_in[i]
            S2 = "%s: %s" % (repr(k), repr(v))
            chars_used = StartNewLine(S2, chars_used, S_indent)
            print S2,                     #no <CR>
            if i < len(S_in)-1: print ",",    #no comma for last i
        print "}\n"
    elif isinstance(S_in, str):
        #write as much as possible per line, then pre-truncate
        #and repeat
        S = S_in
        if width:
            while len(S):
                S2 = S[:width-indent]     #output for cur line
                chars_used = StartNewLine(S2, chars_used, S_indent)
                print S2,                     #no <CR>
                S = S[width-indent:]      #remaining chars
            print "\n"
        else:
            print S_indent, S

#-------------------------------------------------------------------------

#--------------------------main---------------------------------
if __name__ == "__main__":             #for testing
    L = ['qqqqqqqqqqq','wwwwwwwwwww','eeeeeeeeeeeee','rrrrrrrrrrrrrr','tttttttttttttttttt','yyyyyyyyyyyyy']
    print "A list\n", L
    PrintIndentWidth(L)
    S = set(L)
    print "A set\n", repr(S)
    PrintIndentWidth(S, 5, width = 50)
    T = tuple(L)
    print "A tuple\n", repr(T)
    PrintIndentWidth(T, 10, 30)

    print "strings"
    PrintIndentWidth('qqqqqqqqqqqwwwwwwwwwweeeeeeeeeeeerrrrrrrrrrrrrtttttttttttttttttyyyyyyyyyyyyy', 0, 30)
    PrintIndentWidth('0123456789012345678901234567890123456789012345678901234567890123456789', 5, 30)

    D = {1:"qqqqqqqqqqq", 2:"zzzzzzzzzzzzzzzzz", 3:"cccccccccccccccc", 4:[0,9,8,7,6], "fred":(1,3,5,7,9)}
    print "A dictionary\n", D
    PrintIndentWidth(D, 3, 50)
