import os


class lzw_coding:
    def __init__(self, numbits):
        
        # - Numbits used for coding, it the bitstring's length
        #   of dictionary's value
        self.numbits = numbits
        self.format_type = "{:0"+ str(numbits) +"b}"
        # - Initialize dictionary with 256 symbols
        #   {string : value}
        #   {"0000 0001" : "0000 0001", "0000 0010" : "0000 0010", ...}
        self.dict_size = 256
        self.dict = {}
        for i in range(256):
            self.dict["{:08b}".format(i)] = self.format_type.format(i)


class encoder(lzw_coding):

    def __init__(self, numbits, bitout):
        lzw_coding.__init__(self, numbits)
        
        # - BitStream writing to output
        self.output = bitout
        
        # - String code, to check whether symbol sequence
        #   is in dictionary or not
        self.code = ""

    def encode(self, symbol):
        
        # If the eof is met
        if symbol == None:
            self.output.write(self.dict[self.code])
        else:
            string_symbol = "{:08b}".format(symbol)
            self.code += string_symbol
            # - If code is not in dicionary, add
            #   and encode the previous one (8 bits behind)
            if self.code not in self.dict:

                # Add new
                value = self.format_type.format(self.dict_size)
                self.dict_size += 1
                self.dict[self.code] = value

                # decode the old one
                self.output.write(self.dict[self.code[:-8]])
                self.code = string_symbol
                
    def finish(self):
        self.output.close()
        

class decoder:
    def __init__(self, numbits, bitin):
        lzw_coding.__init__(self, numbits)
        
        # Bitstream input
        self.input = bitin

        # Array encoded
        self.array = []
        
        # Reverse dictionary
        self.revdict = dict(zip(self.dict.values(), self.dict.keys()))
    

    # - Decode each bitstring with length equal "numbits" on the encodedstring
    #   every time decoding, update the dictionary last value, by adding the 
    #   first "character" decoded
    #   Eg: decoding "XYZ" (result is "TOP")
    #       - step 1: Decode X, got T, add T into array and "T?" into dictionary
    #       - step 2: Decode Y, got O, add O into array, change "T?" into "TO",
    #                   and add "O?" into dictionary
    #           ....
    def decode(self):
        # Read numbits string
        bitstring = self.input.read(self.numbits)
        
        if bitstring == None:
            return None

        code = int(bitstring, 2)
        
        # Look at the dictionary and decode
        key  = self.revdict[bitstring]

        # Update the last value of dictionary
        if self.dict_size > 256:
            last_code = self.format_type.format(self.dict_size - 1)
            self.revdict[last_code] += key[:8]
        
        # Modify the key again
        key = self.revdict[bitstring]
        
        # Add new item decoded into dictionary
        new_code = self.format_type.format(self.dict_size)
        self.revdict[new_code] = key
        self.dict_size += 1

        # Append key into array
        for i in range(0, len(key), 8):
            self.array.append(int(key[i:i+8], 2))
    
        return True

    def finish(self):
        self.input.close()

    def get_array(self):
        return self.array
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

    def read(self, numbits):
        bit = self.stringin.read(numbits)
        if bit == '':
            return None
        return bit

    def close(self):
        self.stringin.close()




