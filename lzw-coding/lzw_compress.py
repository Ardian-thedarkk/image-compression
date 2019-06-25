import os
import cv2
import time
import pickle
import numpy as np
import sys

import lzw_coding

class lzw_compress:
    def __init__(self, image_path, output_path):

        self.image_path  = image_path
        self.output_path = output_path
        
        # String path
        self.string_path = 'temp'

        # Image
        self.image = None
        # 1D array create from image
        self.array = None
        
        # Number of bits using to represent the each output of key
        # in LZW dictionary
        self.numbits = None

        # Number of bits use for image
        self.numbits_input = 0
        # Number of bits output on compression
        self.numbits_output = 0
        # Ratio of image (bits in / bits out)
        self.ratio = 0
        
        # Time processing
        self.time = time.time()

        self.read()
        self.toarray()

    def read(self):
        try:
            self.image = cv2.imread(self.image_path)
            w, h, c = self.image.shape
            self.numbits_input = w * h * c * 8
            
            # The dicionary length doesnt exceed length array
            self.numbits = int(np.log2(w * h * c + 256))

        except:
            raise Exception("Image Invalid")
    
    # convert image into 1D array
    def toarray(self):
        w, h, c = self.image.shape
        YCrCb = cv2.cvtColor(self.image, cv2.COLOR_BGR2YCrCb)
        Y, Cr, Cb = YCrCb[:, :, 0], YCrCb[:, :, 1], YCrCb[:, :, 2]

        Y_array  = Y.reshape((1, w * h))[0]
        Cr_array = Cr.reshape((1, w * h))[0]
        Cb_array = Cb.reshape((1, w * h))[0]

        self.array = np.concatenate((Y_array, Cr_array, Cb_array), axis = 0)
        self.array = list(self.array)

    def compress(self):
        
        # Set up bitout stream
        bitout = lzw_coding.bitOutStream(self.string_path)

        encoder = lzw_coding.encoder(self.numbits, bitout)

        # Add None into array
        self.array.append(None)

        leng = len(self.array)
        percent = 0
        for i, symbol in enumerate(self.array):
            if i * 100.0 / leng > percent:
                percent += 1
                sys.stdout.write("Processing:\t{} % \r".format(percent))
                sys.stdout.flush()
            encoder.encode(symbol)
        print('')
        encoder.finish()
        
        with open(self.string_path, "r") as f:
            output = f.read()
            self.numbits_output = len(output)
        self.ratio = 1.0 * self.numbits_input / self.numbits_output
    
    # write to byte output
    def write(self):
        # - Write the shape (w and h)
        #   length_w_string(5bits) + w_string(?bits) +
        #   + length_h_string(5bits) + h_string(?bits)
        w, h, c  = self.image.shape
        w_string = '{:b}'.format(w)
        h_string = '{:b}'.format(h)
        w_length = '{:05b}'.format(len(w_string))
        h_length = '{:05b}'.format(len(h_string))
        shape_str = w_length + w_string + h_length + h_string

        # - Write the encoded array made from compress
        with open(self.string_path, "r") as f:
            encoded_str = f.read()

        # - Combine all the string
        encoded_text = shape_str +  encoded_str
        
        # - Add some "0" to encoded text
        leng = len(encoded_text)
        num_zero = 8 - leng % 8
        encoded_text = "0" * num_zero + encoded_text + '{:08b}'.format(num_zero)

        # - Write to byte output
        b = bytearray()
        for i in range(0, leng + num_zero + 8, 8):
            b.append(int(encoded_text[i : i + 8], 2))

        with open(self.output_path, 'wb') as f:
            pickle.dump(b, f)
            self.time = time.time() - self.time
            print("Input: \'%s\'\tOutput: \'%s\'\tBit Input: %d\tBit Output: %d\tRatio: %.2f\tTime: %.2f" %(self.image_path, self.output_path,self.numbits_input, self.numbits_output, self.ratio, self.time))



def main(argv):
    image_path, output_path = argv

    compressor = lzw_compress(image_path, output_path)
    compressor.compress()
    compressor.write()

if __name__ == "__main__":
    main(sys.argv[1:])
