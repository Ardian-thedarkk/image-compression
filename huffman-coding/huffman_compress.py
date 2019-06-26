import os
import cv2
import time
import pickle
import numpy as np
import sys

import huffman_coding

class huffman_compress:
    def __init__(self, image_path, output_path, extended_size):

        self.image_path  = image_path
        self.output_path = output_path
        
        # - Extended_size for extended huffman coding
        #   if this is 1, we have normal huffman coding
        self.extended_size = int(extended_size)

        # String path (temp file to write out some bits)
        # use for efficient memorry
        self.string_path = 'temp'

        # Image
        self.image = None
        # 1D array create from image
        self.array = None
        
        # - To make sure array can be divided into set
        #   of subarrays with length = extended_size,
        #   some "last element" need to be added into our array
        #   this is number of last elements added
        self.num_last_elems = 0

        # frequencies of array symbols
        self.freqs = None
        
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
        self.array = list(np.concatenate((Y_array, Cr_array, Cb_array), axis = 0))
        
        # Add some "last element"
        l = len(self.array)
        if l % self.extended_size:
            self.num_last_elems = 0
        else:
            self.num_last_elems = self.extended_size - l % self.extended_size
            self.array.extend([self.array[-1]] * self.num_last_elems)

    def compress(self):

        # Set up frequencies of value from array
        freq_table = huffman_coding.freqTable(self.array, self.extended_size)
        freq_table.make_freqs()
        self.freqs = freq_table.get_freqs()
        
        # Set up a huffman tree based on freq_table
        h_tree = huffman_coding.huffmanTree(freq_table)
        h_tree.make_tree()
        codewords = h_tree.get_codewords()

        # Set up bitout stream
        bitout = huffman_coding.bitOutStream(self.string_path)

        encoder = huffman_coding.encoder(codewords, bitout)
        
        # encode
        leng = len(self.array)
        percent = 0
        for i in range(0, leng, self.extended_size):
            encoder.encode(self.array[i: i + self.extended_size])
            #if i * 100.0 / leng > percent:
                #percent += 1
                #sys.stdout.write("Processing:\t{} % \r".format(percent))
                #sys.stdout.flush()
        #print('')
        encoder.finish()
        
        with open(self.string_path, "r") as f:
            output = f.read()
            self.numbits_output = len(output) + 8 * 2 * len(self.freqs)
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

        # - Write the dictionary freqs {"key": "frequencies"}
        #   the first one is length of freqs, then:
        #   key(8bits) + length_freq(5bits) + freq(?bits) + ...
        freqs_str = '{:09b}'.format(len(self.freqs))
        for key, freq in self.freqs.items():
            freq_bits  = '{:b}'.format(freq)
            freqs_str += '{:08b}{:05b}{}'.format(key, len(freq_bits), freq_bits)
        
        # - Write extended_size
        numlast_str = '{:08b}'.format(self.extended_size)

        # - Write the encoded array made from compress
        with open(self.string_path, "r") as f:
            encoded_str = f.read()

        # - Combine all the string
        encoded_text = shape_str + freqs_str + numlast_str + encoded_str
        
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
    image_path, output_path = argv[:2]
    if len(argv) == 2:
        extended_size = 1
    else:
        extended_size = argv[2:]

    compressor = huffman_compress(image_path, output_path, extended_size)
    compressor.compress()
    compressor.write()

if __name__ == "__main__":
    main(sys.argv[1:])
