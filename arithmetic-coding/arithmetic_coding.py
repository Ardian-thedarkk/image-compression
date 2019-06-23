import os

class arithmetic:
    
    def __init__(self, numbits = 32):
        
        
        if numbits < 1:
            raise ValueError("Number of bits using for encoding must higher than 1")

        # Bitlength use for arithmetic-coding, 32 is recommended
        self.numbits = numbits
        
        self.max_range = 1 << (numbits - 1)         # 1000.000

        # Mask to make sure our value have exactly "numbits" bitlength
        self.mask = (self.max_range << 1) - 1

        #   - Initialize low and high
        #   - Low with infinite 0: 000...000
        #   - High with infinite 1: 111...111
        self.low  = 0
        self.high = self.mask


class encoder(arithmetic):
    def __init__(self, numbits, bitout):
        arithmetic.__init__(self, numbits)
        
        # bitstream output
        self.output = bitout
        
        # pending bits to check if low and high are convergencing
        self.pending_bits = 0

    # encode each symbol and write out to bitstream
    def encode(self, freq, symbol):
        
        total   = freq.get_total()
        symlow  = freq.get_low(symbol)
        symhigh = freq.get_high(symbol)
        _range   = self.high - self.low + 1
        
        self.high = self.low + symhigh * _range // total - 1
        self.low  = self.low + symlow  * _range // total
        
        # Checking if high and low have same MSB,
        # write their MSB to bitout
        while (self.low ^ self.high) & self.max_range == 0:
            # write to output
            bit = self.low >> (self.numbits - 1)
            self.write(bit)

            # shift 1 left
            self.low  = (self.low  << 1) & self.mask
            self.high = (self.high << 1) & self.mask | 1

        # Checking if high's MSB: "10" and low's MSB: "01",
        # then they are convergencing
        while (self.low >> (self.numbits - 2)) == 1 and (self.high >> (self.numbits - 2)) == 2:
            self.pending_bits += 1

            # delete 2-MSB bit and shift in
            self.low  = ((self.low  << 2) & self.mask) >> 1
            self.high = (((self.high << 2) & self.mask) >> 1) | self.max_range | 1
    
    # write bit into a file for speeding
    def write(self, bit):
        self.output.write(bit)
        for _ in range(self.pending_bits):
            self.output.write(1 ^ bit)
        self.pending_bits = 0
    
    # finish encoding
    def finish(self):
        self.output.write(1)
        self.output.close()


class decoder(arithmetic):

    def __init__(self, numbits, bitin):
        arithmetic.__init__(self, numbits)
        
        # encoded input
        self.input = bitin
        
        # a code to get symbol
        self.code = 0
        for _ in range(self.numbits):
            self.code = (self.code << 1) | self.read()
        
        # array output
        # It could be faster if we write to file
        self.array = []


    def decode(self, freq):
        
        total  = freq.get_total()
        _range = self.high - self.low + 1

        value  = ((self.code - self.low + 1) * total - 1) // _range
        symbol = freq.get_symbol(value)
        
        if symbol == 256:
            return symbol
        
        self.array.append(symbol)
        
        symlow  = freq.get_low(symbol)
        symhigh = freq.get_high(symbol)

        self.high = self.low + symhigh * _range // total - 1
        self.low  = self.low + symlow  * _range // total

        # Checking if high and low have same MSB,
        # write their MSB to bitout
        while (self.low ^ self.high) & self.max_range == 0:
            # shift 1 left
            self.code = (self.code << 1) & self.mask | self.read()
            self.low  = (self.low  << 1) & self.mask
            self.high = (self.high << 1) & self.mask | 1

        # Checking if high's MSB: "10" and low's MSB: "01",
        # then they are convergencing
        while (self.low >> (self.numbits - 2)) == 1 and (self.high >> (self.numbits - 2)) == 2:

            # delete 2-MSB bit and shift in
            self.code = (self.code & self.max_range) | ((self.code << 1) & (self.mask >> 1)) | self.read()
            self.low  = ((self.low  << 2) & self.mask) >> 1
            self.high = (((self.high << 2) & self.mask) >> 1) | self.max_range | 1
        
        return symbol

    def read(self):
        bit = self.input.read()
        return bit

    def finish(self):
        self.input.close()



#   - Table holding frequency of each element in an "Array"
#   - It directly creates Range for each symbol if it has "Array"
#     or frequencies of elements.
class freqTable:
    def __init__(self, arr = [], freq_dict = {}):
        
        # Array and length of Array
        self.arr   = list(arr)
        self.total = 0

        #   - Dictionary of frequencies and Range of symbols
        #   - Range symbol is a dictionary in format {"symbol" : (low, high)},
        self.freq_dict    = freq_dict
        self.symbol_range = {}
        self.symnum       = len(freq_dict)

    
    # make range of symbols 
    def _make_symbol_range(self):
        if len(self.freq_dict) > 0:
            _sum = 0
            for symbol in self.freq_dict.keys():
                low  = _sum
                high = _sum + self.freq_dict[symbol]
                _sum = high
                self.symbol_range[symbol] = (low, high)

    def set_freq_dict(self, freq_dict):
        self.freq_dict = freq_dict
        self.symnum    = len(freq_dict)
        self.total     = sum(freq_dict.values())
        self._make_symbol_range()

    def set_array(self, arr):
        self.arr   = list(arr)
        self.total = len(arr)
        # make dictionary of frequencies
        self.freq_dict = {}
        for key in arr:
            if key in self.freq_dict:
                self.freq_dict[key] += 1
            else:
                self.freq_dict[key] = 1

        self.symnum = len(self.freq_dict)
        self._make_symbol_range()
    
    def get_total(self):
        return self.total

    def get_low(self, symbol):
        if symbol in self.freq_dict:
            return self.symbol_range[symbol][0]

    def get_high(self, symbol):
        if symbol in self.freq_dict:
            return self.symbol_range[symbol][1]
    
    # get symbol depend on value (binary seach)
    def get_symbol(self, value):
        left  = 0
        right = self.symnum - 1
        
        while left <= right:
            middle = (left + right) // 2
            symbol = list(self.freq_dict.keys())[middle]
            
            low, high = self.symbol_range[symbol]
            if value < low:
                right = middle - 1
            elif value >= high:
                left = middle + 1
            else:
                return symbol


# writing output to a temp file
class bitOutStream:

    def __init__(self, stringpath):
        
        if os.path.exists(stringpath):
            os.remove(stringpath)

        self.stringpath = stringpath
        
        self.stringout = open(stringpath, 'a+')

    # append bit into string file
    def write(self, bit):
        self.stringout.write(str(bit))
    
    # terminate writing
    def close(self):
        self.stringout.close()

# reading input bitstream
class bitInStream:

    def __init__(self, stringpath):
        
        assert os.path.exists(stringpath)

        self.stringpath = stringpath
        self.stringin = open(stringpath, 'r')
    
    def read(self):
        bit = self.stringin.read(1)
        if bit == '':
            bit = 0
        return int(bit)
    
    def close(self):
        self.stringin.close()


