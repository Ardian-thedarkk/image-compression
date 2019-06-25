import os
import cv2
import sys
import time
import pickle
import numpy as np
import huffman_coding

class huffman_decompress:
    def __init__(self, encoded_path, image_output_path):

        self.input_path  = encoded_path
        self.output_path = image_output_path
        
        # string tem file to read bit in
        self.string_path = "temp"

        # Image output and shape (w, h)
        self.image = None
        self.w = None
        self.h = None
        
        # 1D array
        self.array = None
        # extended size (if 1: normal huffman)
        self.extended_size = None

        # Array's frequencies
        self.freqs = {}
    
        # length of  encoded array string
        self.length_encoded = None

        # Time processing
        self.time = time.time()

        self.read()

    # Read from compressed file 
    def read(self):
        
        # Read byte compressed to encoded_text
        encoded_text = ""
        with open(self.input_path, 'rb') as f:
            byte_array = pickle.load(f)
        for byte in byte_array:
            encoded_text += '{:08b}'.format(byte)
        
        # Delete some "0" bit at first
        num_zero = int(encoded_text[-8:], 2)
        encoded_text = encoded_text[num_zero : -8]
        # Read image's shape
        w_length = int(encoded_text[:5], 2)
        self.w   = int(encoded_text[5: 5 + w_length], 2)
        h_length = int(encoded_text[5 + w_length: 10 + w_length], 2)
        self.h   = int(encoded_text[10 + w_length: 10 + w_length + h_length], 2)
        encoded_text = encoded_text[10 + w_length + h_length: ]
        
        # Read frequencies dictionary
        leng_freqs = int(encoded_text[:9], 2)
        encoded_text = encoded_text[9:]
        i = 0
        while i < leng_freqs:
            key = int(encoded_text[:8], 2)
            length_freq = int(encoded_text[8: 13], 2)
            freq_value  = int(encoded_text[13: 13 + length_freq], 2)
            self.freqs[key] = freq_value
            encoded_text = encoded_text[13 + length_freq: ]
            i += 1
        
        # Get extended_size
        self.extended_size = int(encoded_text[:8],2)
        encoded_text = encoded_text[8:]
        
        
        # length encoded_text
        self.length_encoded = len(encoded_text)
        # Save the rest into temp
        with open(self.string_path, "w") as f:
            f.write(encoded_text)

    # Covert 1D array into image
    def toimage(self):
        w, h = self.w, self.h
        
        # Subtract 1D array into 3 sub arrays
        Y_array  = self.array[: w*h]
        Cr_array = self.array[w*h : 2*w*h]
        Cb_array = self.array[2*w*h : 3*w*h]
        
        # convert array into 3 channels image
        Y  = np.array(Y_array).reshape((w,h))
        Cr = np.array(Cr_array).reshape((w,h))
        Cb = np.array(Cb_array).reshape((w,h))
        
        # Create a copy zero image
        image = np.zeros((w,h,3), dtype = np.uint8)
        image[:, :, 0], image[:, :, 1], image[:, :, 2] = Y, Cr, Cb
        
        # Convert to RGB
        self.image = cv2.cvtColor(image, cv2.COLOR_YCrCb2BGR)


    def decompress(self):
        # Create freq table
        freq_table = huffman_coding.freqTable(extended_size = self.extended_size)
        freq_table.set_freqs(self.freqs)
        
        # Create codewords
        h_tree = huffman_coding.huffmanTree(freq_table)
        h_tree.make_tree()
        codewords = h_tree.get_codewords()
        
        # set up bit stream input
        bitin = huffman_coding.bitInStream(self.string_path)

        decoder = huffman_coding.decoder(codewords, bitin)
        
        percent = 0
        i = 0
        while decoder.decode():
            if i * 100.0 / self.length_encoded > percent:
                percent += 1
                sys.stdout.write("Processing:\t{} % \r".format(percent))
                sys.stdout.flush()
            i += 1
        print('')
        decoder.finish()
        self.array = decoder.get_array()
        self.toimage()

    def write(self):
        cv2.imwrite(self.output_path, self.image)
        self.time = time.time() - self.time
        print("Input: \'%s\' \tOutput: \'%s\' \tTime: %.2f(s)"%(self.input_path, self.output_path, self.time))


def main(argv):
    input_path, image_path = argv
    
    decompressor = huffman_decompress(input_path, image_path)
    decompressor.decompress()
    decompressor.write()

if __name__ == "__main__":
    main(sys.argv[1:])
