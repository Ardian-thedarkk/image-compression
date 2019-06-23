
class encoder:
    def __init__(self):
        # array to store symbols and run-length for each one
        self.symbols = []
        self.run_length = []
    
    def encode(self, symbol):
        
        # Checking if symbol is on the length,
        # If it on, we add the length of run,
        # otherwise we create the new run
        if len(self.symbols) == 0 or symbol != self.symbols[-1]:
            self.symbols.append(symbol)
            self.run_length.append(1)
        else:
            self.run_length[-1] += 1

    def get_symbols(self):
        return self.symbols

    def get_run_length(self):
        return self.run_length

class decoder:
    def __init__(self):
        # array result
        self.array = []
    
    def decode(self, symbol, length):
        
        # add the runlength of symbol into array
        self.array.extend([symbol] * length)

    def get_array(self):
        return self.array
