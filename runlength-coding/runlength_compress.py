import numpy as np
import cv2
import time
import sys
import pickle

import runlength_coding

class runlength_compress:
    def __init__(self, image_path, output_path):
        
        self.image_path  = image_path
        self.output_path = output_path
        
        # Image for compressing
        self.image = None

        # 1d array create from image
        self.array = []
        
        # array of symbols and run-length for each one
        self.symbols = []
        self.run_length = []

        # number of bits using to store image
        self.numbits_input  = 0
        # number of bits using to store output
        self.numbits_output = 0

        # ratio of compressing ( it equal bits input / bits output)
        self.ratio = None
        
        # time processing
        self.time = 0

        self.read()
        self.toarray()

    # Read image to input
    def read(self):
        try:
            self.image = cv2.imread(self.image_path)
            w, h, c = self.image.shape
            self.numbits_input = w * h * c * 8
        except:
            raise Exception("Image Invalid")
    

    # convert image into zigzag array
    def toarray(self):
        w, h, _ = self.image.shape
        YCrCb = cv2.cvtColor(self.image, cv2.COLOR_BGR2YCrCb)
        
        Y, Cr, Cb = YCrCb[:, :, 0], YCrCb[:, :, 1], YCrCb[:, :, 2]

        # create 1D array
        Y_array  = Y.reshape((1,w*h))[0]
        Cr_array = Cr.reshape((1,w*h))[0]
        Cb_array = Cb.reshape((1,w*h))[0]

        self.array = list(np.concatenate((Y_array, Cr_array, Cb_array), axis = 0))

    
    # Modify symbols and run_length array for better compress,
    # the first one is 3A2B1C, we change it to 3AA2BBC,
    # simple delete any run-length = 1 in run_length array,
    # and double any symbol has run-length >= 2
    def modify_compress(self):
        # new_symbols and new_runlength
        new_symbols   = []
        new_runlength = []
        for symbol, runlength in zip(self.symbols, self.run_length):
            if runlength >= 2:
                new_symbols.extend([symbol, symbol])
                new_runlength.append(runlength)
            else:
                new_symbols.append(symbol)
        
        self.symbols   = new_symbols
        self.run_length = new_runlength


    def compress(self):
        t = time.time()

        model = runlength_coding.encoder()
        #leng_array = len(self.array)
        for i, symbol in enumerate(self.array):
            #sys.stdout.write("Processing:\t%d\t/\t%d\r"%(i+1, leng_array))
            #sys.stdout.flush()
            model.encode(symbol)

        self.symbols    = model.get_symbols()
        self.run_length = model.get_run_length()

        self.modify_compress()

        self.numbits_output = len(self.symbols) * 8 + len(self.run_length) * 8
        self.ratio = self.numbits_input * 1.0 / self.numbits_output

        self.time = time.time() - t
    
    # write symbols and run_length array into a byte file
    def write(self):
        encoded_text = ""

        # Convert image shape into str, it has structure
        # length_of_w_bitstring (5bits) + w_bitstring (? bits) +
        # + length_of_h_bitstring (5bits) + h_bitstring (? bits)
        w, h , _  = self.image.shape
        w_string  = '{:b}'.format(w)
        h_string  = '{:b}'.format(h)
        length_w  = '{:05b}'.format(len(w_string))
        length_h  = '{:05b}'.format(len(h_string))
        # save them as string
        shape_text = length_w + w_string + length_h + h_string

        # Convert symbols array into string
        # structure: length_of_length_symbol(5bits) + length_symbols (? bits) + 
        # + symbol[0] + symbol[1] + ...
        length_symbols   = '{:b}'.format(len(self.symbols))
        length_of_length = '{:05b}'.format(len(length_symbols))
        symbols_text = length_of_length + length_symbols
        # Save symbol into symbols text
        for symbol in self.symbols:
            symbols_text += '{:08b}'.format(symbol)

        # Convert run_length into string
        # stuturce: length_of_length_run (5bits) + length_run (? bits) + ....
        runlength_text = ""
        for runlength in self.run_length:
            length_run       = '{:b}'.format(runlength)
            length_of_length = '{:05b}'.format(len(length_run))
            runlength_text += length_of_length + length_run

        # Combine to a text
        encoded_text = shape_text + symbols_text + runlength_text

        # Add some "0" into encoded_text so it can devide by 8,
        # so we can save that text to a bytearray
        leng_text = len(encoded_text)
        num_zero  = 8 - leng_text % 8
        # add num_zero to 8 bits to easily get back when decompressing
        encoded_text += '{:08b}'.format(num_zero)
        encoded_text  = "0" * num_zero + encoded_text

        # Create byte array and add every 8bits in
        # encoded_text into this byte array
        b = bytearray()
        for i in range(0, leng_text + num_zero + 8, 8):
            b.append(int(encoded_text[i: i + 8], 2))

        # Write byte array to output
        with open(self.output_path, 'wb') as f:
            pickle.dump(b, f)
            print("Input: \'%s\'\tOutput: \'%s\'\tTime: %.2f(s)\tRatio: %.2f" %(self.image_path, self.output_path, self.time, self.ratio))


def main(argv):
    
    image, output = argv

    compressor = runlength_compress(image, output)
    compressor.compress()
    compressor.write()

if __name__ == "__main__":
    main(sys.argv[1:])
