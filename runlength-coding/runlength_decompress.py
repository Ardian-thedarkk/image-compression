import sys
import cv2
import time
import numpy as np
import pickle

import runlength_coding

class runlength_decompress:
    def __init__(self, compressed, image_output):
        
        self.input_path  = compressed
        self.output_path = image_output
        
        # 1D array (will be create from decompressing)
        self.array = None

        # image result
        self.image = None
        # image shape
        self.w = None
        self.h = None
        
        # symbols and runlength_array
        self.symbols = []
        self.run_length = []

        self.read()
        self.reconstruct()

    # Read a compress file and extract them into
    # image shape, symbols, run_length array
    def read(self):
        # load
        with open(self.input_path, 'rb') as f:
            bytearr = pickle.load(f)

        # write byte array into text
        encoded_text = ""
        for byte in bytearr:
            encoded_text += '{:08b}'.format(byte)

        # delete some "0" at the first
        num_zero = int(encoded_text[-8:], 2)
        encoded_text = encoded_text[num_zero: -8]

        # extract shape: (w, h)
        length_w = int(encoded_text[:5], 2)
        self.w   = int(encoded_text[5: 5 + length_w], 2)
        length_h = int(encoded_text[5 + length_w: 10 + length_w], 2)
        self.h   = int(encoded_text[10 + length_w: 10 + length_w + length_h], 2)
        encoded_text = encoded_text[10 + length_w + length_h: ]

        # extract symbols array
        length_of_length = int(encoded_text[: 5], 2)
        length_symbols   = int(encoded_text[5: 5 + length_of_length], 2)
        encoded_text = encoded_text[5 + length_of_length: ]
        for i in range(0, length_symbols * 8, 8):
            self.symbols.append(int(encoded_text[i: i + 8], 2))
        encoded_text = encoded_text[length_symbols * 8:]

        # extract run_length array
        leng_text = len(encoded_text)
        i = 0
        while i < leng_text:
            length_of_length = int(encoded_text[i: i + 5], 2)
            length_run       = int(encoded_text[i + 5: i + 5 + length_of_length], 2)
            self.run_length.append(length_run)
            i = i + 5 + length_of_length

    # Reconstruct symbols and run_length array into simple one
    # 3AA2BBC into 3A2B1C
    def reconstruct(self):
        new_symbols   = []
        new_runlength = []
        
        # Traverse on symbols array, if an element is doubled, add
        # it into new symbols and add runlength into new runlength array
        # otherwise add 1 into new runlength
        leng_symbols = len(self.symbols)
        i, j = 0, 0
        while i < leng_symbols - 1:
            if self.symbols[i] == self.symbols[i + 1]:
                new_symbols.append(self.symbols[i])
                new_runlength.append(self.run_length[j])
                i = i + 1
                j = j + 1
            else:
                new_symbols.append(self.symbols[i])
                new_runlength.append(1)
            i = i + 1
        
        # Add last symbol
        if i == leng_symbols - 1:
            new_symbols.append(self.symbols[i])
            new_runlength.append(1)

        self.symbols    = new_symbols
        self.run_length = new_runlength

        assert len(self.symbols) == len(self.run_length)

    # convert 1D array into RGB Image
    def toimage(self):
        w, h = self.w, self.h
        
        # 1D array
        Y_array  = self.array[: w*h]
        Cr_array = self.array[w*h: 2*w*h]
        Cb_array = self.array[2*w*h: 3*w*h]

        # reshape into (w,h) matrix
        Y  = np.array(Y_array).reshape((w,h))
        Cr = np.array(Cr_array).reshape((w,h))
        Cb = np.array(Cb_array).reshape((w,h))

        # create image
        image = np.zeros((w,h,3), dtype=np.uint8)
        image[:, :, 0], image[:, :, 1], image[:, :, 2] = Y, Cr, Cb
        self.image = cv2.cvtColor(image, cv2.COLOR_YCrCb2BGR)

    def decompress(self):
        t = time.time()

        model = runlength_coding.decoder()
        for symbol, length in zip(self.symbols, self.run_length):
            model.decode(symbol, length)

        self.array = model.get_array()
        self.time = time.time() - t
        self.toimage()

    def write(self):
        cv2.imwrite(self.output_path, self.image)
        print("Input: \'%s\' \tOutput: \'%s\' \tTime: %2.f(s)"%(self.input_path, self.output_path, self.time))

def main(argv):
    compressed, image_path = argv

    decompressor = runlength_decompress(compressed, image_path)
    decompressor.decompress()
    decompressor.write()

if __name__ == "__main__":
    main(sys.argv[1:])
