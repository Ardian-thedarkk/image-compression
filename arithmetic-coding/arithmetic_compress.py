import os
import sys
import cv2
import pickle
import time

import numpy as np
from arithmetic_coding import encoder, freqTable, bitOutStream

class arithmetic_compress:
    def __init__(self, image_path, output_path):
        # image path
        self.image_path  = image_path
        # compressed path
        self.output_path = output_path
        # string output path (string before changed to bytearray)
        self.string_path = "encoded_string"

        # image
        self.image = None
        # 1d array create from image
        self.array = None

        # number of bits on image
        self.numbits_input  = 0
        # number of bits on compression
        self.numbits_output = 0

        # compress ratio: equal bitsinput / bitsoutput
        self.ratio = 1.0
        
        # dictionary frequencies make from array
        self.freq = {}
        
        # time using for compressing
        self.time = 0

        self.read()
        self.toarray()

    # read image from image_path and compute bits input
    def read(self):
        try:
            self.image = cv2.imread(self.image_path)
            w, h, c = self.image.shape
            self.numbits_input = w * h * c * 8
        except:
            raise Exception("Image Invalid")
    
    # convert image into 1d-array
    def toarray(self):
        YCrCb = cv2.cvtColor(self.image, cv2.COLOR_BGR2YCrCb)
        
        Y, Cr, Cb = YCrCb[:, :, 0], YCrCb[:, :, 1], YCrCb[:, :, 2]
        
        w, h, _c = self.image.shape
        Y  = Y.reshape((1, w*h))[0]
        Cr = Cr.reshape((1, w*h))[0]
        Cb = Cb.reshape((1, w*h))[0]

        self.array = list(np.concatenate((Y, Cr, Cb), axis = 0))

    def compress(self, numbits):
        # time
        t = time.time()
        # push eof into array
        self.array.append(256)

        # set up frequencies table
        freq = freqTable()
        freq.set_array(self.array)
        self.freq = freq.freq_dict

        # set up bit string output
        bitout = bitOutStream(self.string_path)

        model  = encoder(numbits = numbits, bitout = bitout)
        
        # Encode each elements in array image
        # and save it into string_path
        leng_array = len(self.array)
        for i,elem in enumerate(self.array):
            sys.stdout.write("Processing:\t%d\t/\t%d\r"%(i+1, leng_array))
            sys.stdout.flush()
            model.encode(freq, elem)
        model.finish()
        print('')
        
        self.time = time.time() - t
        self.get_total_bitout()
        
    def get_total_bitout(self):
        # bit use for dictionary
        self.numbits_output = 256 * 8 * 2

        # bit use for encoded file
        with open(self.string_path, 'r') as f:
            encoded = f.read()
            self.numbits_output += len(encoded)
        
        self.ratio = self.numbits_input * 1.0 / self.numbits_output
    
    # write to bytes output
    def write(self):
        # Save the w, h (shape of image) into bitstring
        # It has structure: length_shape (8bits) + value (length_shape bits)
        shape_str = ""
        w, h, _ = self.image.shape
        wstring = '{:b}'.format(w)
        hstring = '{:b}'.format(h)
        wlength = '{:05b}'.format(len(wstring))
        hlength = '{:05b}'.format(len(hstring))
        shape_str = wlength + wstring + hlength + hstring

        # pop the eof out of dictionary
        if 256 in self.freq:
            self.freq.pop(256)

        dict_str = ""
        # The first is length of dictionary
        dict_str += '{:09b}'.format(len(self.freq))

        # Dictionary is save as "key" + "length_frequency" + "frequency"
        # "key" : 8 bits
        # "length_frequency" : 5 bits
        # "frequency" : length_frequency bits
        for key, frequency in self.freq.items():    
            str_frequency = '{:b}'.format(frequency)
            length_frequency = '{:05b}'.format(len(str_frequency))
            dict_str += '{:08b}'.format(key) + length_frequency + str_frequency
        
        # read encoded array
        with open(self.string_path, 'r') as f:
            encoded_array = f.read()
        
        # combine shapestr, dictstr and encoded array
        encoded_text = shape_str + dict_str + encoded_array
        
        # add some zero into encoded_text to make sure they can save as byte array
        leng = len(encoded_text)
        num_zero = 8  - leng % 8

        encoded_text += '{:08b}'.format(num_zero)
        encoded_text  = '0' * num_zero + encoded_text
        # extract every 8 bits and save them as an item into bytearray
        b = bytearray()
        for i in range(0, leng + num_zero + 8, 8):
            b.append(int(encoded_text[i: i + 8], 2))

        # save byte array to output
        with open(self.output_path, 'wb') as f:
            pickle.dump(b, f)
            print("Input: \'%s\'\tOutput: \'%s\'\tTime: %.2f(s)\tRatio: %.2f" %(self.image_path, self.output_path, self.time, self.ratio))
            

def main(argv):

    images, output = argv
    
    compressor = arithmetic_compress(images, output)
    compressor.compress(numbits = 32)
    compressor.write()

if __name__ == "__main__":
    main(sys.argv[1:])
