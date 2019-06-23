import os
import sys
import cv2
import pickle
import time

import numpy as np
from arithmetic_coding import decoder, freqTable, bitInStream

class arithmetic_decompress:
    def __init__(self, encoded_path, image_output_path):
        
        # encoded file
        self.encoded_path = encoded_path
        
        # output path
        self.output_path = image_output_path

        # encoded array path (keep as file for faster memory)
        self.string_path  = "encoded_string"
        
        # dictionary of frequencies
        self.freq_dict = {}

        # 1d array image
        self.array = None

        # image and shape
        self.image = None
        self.shape = None

        # time processing
        self.time = time.time()

        self.read()



    # Read from an encoded byte file,
    # Extract them into dict and encoded array
    def read(self):
        encoded_text = ""
        with open(self.encoded_path, 'rb') as f:
            byte_array = pickle.load(f)
        for byte in byte_array:
            encoded_text += '{:08b}'.format(byte)
        
        # extract some "0" at the first
        num_zero = int(encoded_text[-8:],2)
        encoded_text = encoded_text[num_zero: -8]
        
        # get the image's shape
        wlength = int(encoded_text[:5], 2)
        hlength = int(encoded_text[5 + wlength: 10 + wlength], 2)
        w = int(encoded_text[5: 5 + wlength], 2)
        h = int(encoded_text[10 + wlength: 10 + wlength + hlength], 2)
        self.shape = (w,h)
        encoded_text = encoded_text[10 + wlength + hlength : ]

        # get length dictionary
        length_dict = int(encoded_text[:9], 2)
        encoded_text = encoded_text[9:]
        
        # Reconstruct dictionary frequencies
        # key(8bits) + length frequency (5bits) + frequency
        i = 0
        for _ in range(length_dict):
            key         = int(encoded_text[i: i + 8], 2)
            length_freq = int(encoded_text[i + 8: i + 13], 2)
            freq        = int(encoded_text[i + 13: i + 13 + length_freq], 2)
            
            self.freq_dict[key] = freq

            i = i + 13 + length_freq
        
        # extract and save encoded array into string path
        encoded_array = encoded_text[i:]
        with open(self.string_path, 'w') as f:
            f.write(encoded_array)

    # conver 1d-array to image
    def toimage(self):
        w, h = self.shape
        # image area
        s = w * h

        # extract into 3 sub arrays
        Y_array  = np.array(self.array[ : s])
        Cr_array = np.array(self.array[s: 2*s])
        Cb_array = np.array(self.array[2*s : 3*s])

        # reshape into image channels
        Y  = Y_array.reshape(self.shape) 
        Cr = Cr_array.reshape(self.shape)
        Cb = Cb_array.reshape(self.shape)

        # create a image
        image = np.zeros((w,h,3), dtype = np.uint8)
        image[:, :, 0], image[:, :, 1], image[:, :, 2] = Y, Cr, Cb

        # convert to RGB color space
        self.image = cv2.cvtColor(image, cv2.COLOR_YCrCb2BGR)


    def decompress(self, numbits):

        # push eof into dict
        if 256 not in self.freq_dict:
            self.freq_dict[256] = 1

        freq = freqTable()
        freq.set_freq_dict(self.freq_dict)
        total = freq.get_total()

        # set up bitin
        bitin = bitInStream(self.string_path)
        
        # set up decoder
        model = decoder(numbits = 32, bitin = bitin)
        
        i = 0
        percent = 0
        while True:
            if i * 100.0 / total > percent:
                percent += 1
                sys.stdout.write("Processing:\t{} %\r".format(percent))
                sys.stdout.flush()

            i += 1
            symbol = model.decode(freq)
            if symbol == 256:
                break
        print('')
        model.finish()
        self.array = model.array
        self.toimage()

    def write(self):
        cv2.imwrite(self.output_path, self.image)
        self.time = time.time() - self.time
        print("Input: \'%s\' \tOutput: \'%s\' \tTime: %2.f(s)"%(self.encoded_path, self.output_path, self.time))


def main(argv):
    compressed, image = argv
    decompressor = arithmetic_decompress(compressed, image)
    decompressor.decompress(32)
    decompressor.write()

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except:
        raise Exception("Wrong compressed file")

