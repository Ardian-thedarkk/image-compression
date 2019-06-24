import heapq
import os
# - Node for huffman Tree
class node:
    def __init__(self, data = None, weight = 0, code = ""):

        # Data of a node, this don't hold any value
        # except node is the leaf one
        self.data = data

        # Weigth of data, sum of two children's weights
        self.weight = weight

        # Code generated after traversing the tree
        # it's string type
        self.code = code

        # two children of node
        self.left  = None
        self.right = None
    
    def __lt__(self, other):
        return self.weight <= other.weight

class huffmanTree:
    def __init__(self, freqs):
        # Initialize a root
        self.root = node()
        
        # - freqTable class
        self.freqs = freqs
        
        # Heap of nodes
        self.heap_nodes = []
        
        # Codewords created by huff man tree
        self.codewords = {}
        
    # Make heap nodes from frequencies table
    def make_heap_nodes(self):
        self.freqs.make_heap_nodes()
        self.heap_nodes = self.freqs.get_heap_nodes()
    
    # - Update a root by huffman algorithm
    #   pop out two nodes on heap,
    #   create a parent node of theses,
    # Set it as root and push into heap
    def update_root(self):
        left_child  = heapq.heappop(self.heap_nodes)
        right_child = heapq.heappop(self.heap_nodes)
        
        # Create a new root
        new_root = node(weight = left_child.weight + right_child.weight)
        new_root.left  = left_child
        new_root.right = right_child
        
        # Set as root
        self.root = new_root
        # Push to heap
        heapq.heappush(self.heap_nodes, self.root)
    
    # Generate codewords on the current branch node
    def make_codewords(self, cur):
        # If cur node is not a leaf
        if cur.left and cur.right:
            cur.left.code  = cur.code + "0"
            cur.right.code = cur.code + "1"
            self.make_codewords(cur.left)
            self.make_codewords(cur.right)
        # Otherwise, change cur node data into string and
        # save into codewords
        else:
            cur_string = ""
            for elem in cur.data:
                cur_string += '{:08b}'.format(elem)
            self.codewords[cur_string] = cur.code

    # Create a huffman tree
    def make_tree(self):
        # Create Heap
        self.make_heap_nodes()

        # Repeat update root until heap has only 1 node
        leng_heap = len(self.heap_nodes)
        for _ in range(leng_heap - 1):
            self.update_root()
        
        # Generate codewords
        self.make_codewords(self.root)

    def get_codewords(self):
        return self.codewords

class freqTable:
    def __init__(self, arr = [], extended_size = 1):
        
        self.array = arr

        # frequencies talbe
        self.freqs = {}

        # Use for extended huffman coding
        # with extended_size = 2,
        # {'a' : ?, 'b', ?} becomes
        # {'aa': ?, 'ab' : ?, 'ba' : ?, 'bb': ?}
        self.extended_size = extended_size
        
        # Heap nodes of freqs table
        self.heap_nodes = []
        heapq.heapify(self.heap_nodes)

    def make_freqs(self):
        for key in self.array:
            if key not in self.freqs:
                self.freqs[key]  = 1
            else:
                self.freqs[key] += 1
    
    # - Backtracking to create nodes with data is
    #   a set of elements in self.array,
    #   then push them into heap_nodes
    def push_to_heap(self, set_elements, i, weight):
        if i < self.extended_size:
            for key, value in self.freqs.items():
                self.push_to_heap(set_elements + [key], i + 1, weight + value)
        else:
            newnode = node(data = set_elements, weight = weight)
            heapq.heappush(self.heap_nodes, newnode)

    def make_heap_nodes(self):
        # make frequencies dict
        if len(self.freqs) == 0:
            self.make_freqs()

        # create heap_nodes
        self.push_to_heap(set_elements = [], i = 0, weight = 0)
    
    def set_freqs(self, freqs):
        self.freqs = freqs
    def get_freqs(self):
        return self.freqs
    
    def get_heap_nodes(self):
        return self.heap_nodes


class encoder:
    def __init__(self, codewords, bitout):
        
        # Codewords create from huffman Tree
        self.codewords = codewords
        
        # Bitout stream to write to a file,
        # for efficent memorry usage
        self.output = bitout

    def encode(self, set_of_symbols):
        # change set of symbols into string
        string = ""
        for symbol in set_of_symbols:
            string += "{:08b}".format(symbol)

        if string in self.codewords:
            code = self.codewords[string]
            self.output.write(code)

    def finish(self):
        self.output.close()


class decoder:
    def __init__(self, codewords, bitin):

        # codewords
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
            string_keys = self.rev_codewords[self.value]
            for i in range(0, len(string_keys), 8):
                self.array.append(int(string_keys[i: i+8], 2))
            self.value = ""    
        return 1

    def finish(self):
        self.input.close()

    def get_array(self):
        return self.array

# table of frequencies create from an array
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

