import os

# - Node of Tree to create shannon-fano tree
class node:
    def __init__(self, data = None, weight = 0, code = ""):

        # Data of a node, this don't hold any value
        # except node is the leaf one
        self.data = data

        # Weigth of data, sum of two children's weights,
        # also sum of data
        self.weight = weight

        # Code generated after traversing the tree
        # it's string type
        self.code = code

        # two children of node
        self.left  = None
        self.right = None
    

# - Shannon-fano Tree (not adaptive one),
#   this is a binary-weight-balanced tree, with weight left < right 
#   every node have 2 children or 0 child
class sfTree:
    def __init__(self, freqs):
        
        # Initialize a root of tree
        self.root = node()
        

        # Sorted dictionary,
        # frequency of each symbol on the tree: {"symbol": "frequency"}..
        # this is used for making weight node
        self.freqs   = freqs
        # symbol of frequency table
        self.symbols = list(freqs.keys())

        # Dictionary of sfTree use for coding
        self.codewords = {}
        
        # Generate codewords
        self.update()


    # - Create children of a current node
    #   with symbol is in symbols[start: end]
    def add_children(self, cur, start, end):
        # Get m so that symbols[start: m] near to symbols[m: end]
        m = start
        sum_left = 0
        sum_right = cur.weight
        while m < end:
            if sum_left > sum_right:
                break
            else:
                sum_left  += self.freqs[self.symbols[m]]
                sum_right -= self.freqs[self.symbols[m]]
                m += 1

        # fix infinite recursion
        if end - start == 2:
            m = start + 1
            sum_left = self.freqs[self.symbols[start]]
            sum_right = self.freqs[self.symbols[start + 1]]

        # Create the children node
        cur.left  = node(weight = sum_left , code = cur.code + "0")
        cur.right = node(weight = sum_right, code = cur.code + "1")
        
        # - If cur.left have only 1 element (m - start = 1)
        #   we update the codewords, otherwise we add child into left
        if m - start == 1:
            self.codewords[self.symbols[start]] = cur.left.code
        else:
            self.add_children(cur.left, start, m)

        # Doing the same on right node
        if end - m == 1:
            self.codewords[self.symbols[m]] = cur.right.code
        else:
            self.add_children(cur.right, m, end)
        

    # Generate codewords
    def update(self):
        self.root.weight = sum(list(self.freqs.values()))
        self.add_children(self.root, 0, len(self.symbols))
    
    def get_codewords(self):
        return self.codewords


class encoder:
    def __init__(self, codewords, bitout):
        
        # Codewords create by sfTree
        self.codewords = codewords
        
        # Bitout stream to write to a file,
        # for better memory saving only
        self.output = bitout

    def encode(self, symbol):
        if symbol in self.codewords:
            self.output.write(self.codewords[symbol])
    
    def finish(self):
        self.output.close()

class decoder:
    def __init__(self, codewords, bitin):

        # codewords create by sfTree
        self.codewords = codewords
        
        # reverse codewords:
        self.rev_codewords = dict(zip(codewords.values(), codewords.keys()))

        # Bitstream file encoded by codewords
        self.input = bitin
        
        # current value
        self.value = ""
        
        # array decoded
        self.array = []


    def decode(self):
        bit = self.input.read()
        if bit == None:
            return None
        self.value += bit
        if self.value in self.rev_codewords:
            self.array.append(self.rev_codewords[self.value])
            self.value = ""    
        return 1

    def finish(self):
        self.input.close()

    def get_array(self):
        return self.array

# table of frequencies create from an array
class freqTable:
    def __init__(self, arr = []):
        
        self.array = arr
        self.freqs = {}
        
        self.make_freqs()

    # Make frequencies table
    def make_freqs(self):
        if len(self.freqs) == 0:
            for key in self.array:
                if key not in self.freqs:
                    self.freqs[key]  = 1
                else:
                    self.freqs[key] += 1
        
        _sorted = sorted(self.freqs.items(), key = lambda x: x[1], reverse = True)

        keys    = [x[0] for x in _sorted]
        values  = [x[1] for x in _sorted]

        self.freqs = dict(zip(keys, values))
    
    def get_freqs(self):
        return self.freqs


# Writting to temp file (for better saving memory)
class bitOutStream:
    def __init__(self, stringpath):
        
        if os.path.exists(stringpath):
            os.remove(stringpath)

        self.stringpath = stringpath
        self.stringout = open(stringpath, 'a+')

    # append bitstring into string file
    def write(self, bitstring):
        self.stringout.write(str(bitstring))

    # terminate writing
    def close(self):
        self.stringout.close()


# Reading input bitstream
class bitInStream:
    def __init__(self, stringpath):
        assert os.path.exists(stringpath)
        self.stringpath = stringpath
        self.stringin = open(stringpath, 'r')

    def read(self):
        bit = self.stringin.read(1)
        if bit == '':
            return None
        return bit

    def close(self):
        self.stringin.close()

