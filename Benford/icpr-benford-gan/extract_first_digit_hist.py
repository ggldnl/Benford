import argparse
import glob
import io
import os
import uuid
import warnings
from multiprocessing import Pool, cpu_count

import cv2
import jpeg
import numpy as np
from PIL import Image
from tqdm import tqdm

from params import base_list, dataset_root, dataset_ext, fd_hist_root, tmp_path

np.random.seed(21)

warnings.simplefilter('ignore')  # we actually want nan as first digit when we meet a 0

zig_zag_idx = np.asarray([0, 1, 5, 6, 14, 15, 27, 28, 2, 4, 7, 13, 16, 26, 29, 42,
                          3, 8, 12, 17, 25, 30, 41, 43, 9, 11, 18, 24, 31, 40, 44, 53,
                          10, 19, 23, 32, 39, 45, 52, 54, 20, 22, 33, 38, 46, 51, 55, 60,
                          21, 34, 37, 47, 50, 56, 59, 61, 35, 36, 48, 49, 57, 58, 62, 63])


def extract_features_from_dct(img_path):

    # returns an array of size (xmax * ymax, b, b)
    # basically xmax * ymax elements 
    # each element is a 8x8 matrix
    # each 8x8 matrix is a block
    # the array contains all the blocks of the given image

    # Params
    b = 8
    # Block-wise 2D-DCT (Luma only)
    img = jpeg.Jpeg(img_path)
    xmax, ymax = img.getcomponentdimensions(0)
    blocks_dct = np.zeros((xmax * ymax, b, b))
    cnt = 0
    for y in range(ymax):
        for x in range(xmax):
            block = img.getblock(x, y, 0)
            blocks_dct[cnt, :, :] = np.frombuffer(block, dtype=np.int16).reshape((8, 8))
            cnt += 1
    return blocks_dct 


def compute_histograms(img: np.ndarray, base: int, n_freq: int = 9):
    h_img = []
    for k in range(n_freq):
        try:
            h, _ = np.histogram(img[:, k], range=(np.nanmin(img[:, k]), np.nanmax(img[:, k])),
                                bins=np.arange(0.5, base + 0.5, 1), density=True) # stupid
        except ValueError:
            h = np.zeros(base - 1, dtype=np.float64)
        h_img += [h]

    return np.asarray(h_img)


def first_digit_gen(d: float, base):
    return np.floor(np.abs(d) / base ** np.floor(np.log(np.abs(d)) / np.log(base)))


def first_digit_call(args: dict):
    path = args['path']
    base = args['base']
    jpeg_qf = args['jpeg_qf']
    jpeg_recompression = args['jpeg_recompression']
    recompression_qf = args['recompression_qf']

    """
    from PIL import Image
    img = Image.open(path).convert('L')
    
    If you have a P mode image, that means it is palettised. 
    That means there is a palette with up to 256 different colours in it, 
    and instead of storing 3 bytes for R, G and B for each pixel, 
    you store 1 byte which is the index into the palette. This confers 
    both advantages and disadvantages. The advantage is that your image 
    requires 1/3 of the space in memory and on disk. The disadvantage 
    is that it can only represent 256 unique colours - so you may get 
    banding or artefacts.

    If you have an L mode image, that means it is a single channel image 
    - normally interpreted as greyscale. The L means that is just stores 
    the Luminance. It is very compact, but only stores a greyscale, not colour.
    """

    # the conversion should be done only if the extension is not jpg
    """

    # load image
    if path.split('.')[-1] == 'webp':
        img = Image.fromarray(cv2.imread(path))
    else:
        img = Image.open(path).convert('L')

    # JPEG recompression
    if jpeg_recompression:
        buffer = io.BytesIO()
        np.random.seed(int.from_bytes(os.urandom(4), byteorder='little'))  # needed for real multiprocessing randomness
        qf = np.random.randint(low=85, high=101) if recompression_qf is None else recompression_qf
        img.save(buffer, 'JPEG', quality=qf)
        img = Image.open(buffer).convert('L')


    # DCT extraction
    tmp_name = uuid.uuid4().hex + '.jpg'
    # taken from http://discourse.techart.online/t/pil-wait-for-image-save/3994/9
    with open(os.path.join(tmp_path, tmp_name), 'wb') as tmp_file:
        img.save(tmp_file, 'JPEG', quality=jpeg_qf)
        tmp_file.flush()
        os.fsync(tmp_file)

    """

    ext = path.split('.')[-1]

    if ext == 'webp':
        img = Image.fromarray(cv2.imread(path))
    else:
        img = Image.open(path).convert('L')

    # JPEG recompression
    if jpeg_recompression:
        buffer = io.BytesIO()
        np.random.seed(int.from_bytes(os.urandom(4), byteorder='little'))  # needed for real multiprocessing randomness
        qf = np.random.randint(low=85, high=101) if recompression_qf is None else recompression_qf
        img.save(buffer, 'JPEG', quality=qf)
        img = Image.open(buffer).convert('L')

    # this will tell us later if the image was converted and the new copy needs to be remove
    converted_flag = False

    if ext != 'jpg':

        converted_flag = True

        new_name = uuid.uuid4().hex + '.jpg'
        new_path = os.path.join(tmp_path, new_name) 
        
        # taken from http://discourse.techart.online/t/pil-wait-for-image-save/3994/9
        with open(new_path, 'wb') as image_jpg:
            img.save(image_jpg, 'JPEG', quality=jpeg_qf)
            image_jpg.flush()
            os.fsync(image_jpg)

        path = new_path

    # extract dct from the image
    img_dct = extract_features_from_dct(path)

    # remove newly created tmp image
    if converted_flag:
        os.remove(path)

    # img_dct -> array containing all the 8x8 blocks in which we split the image 

    # vectorize and remove DC
    img_dct = img_dct.reshape(-1, 64) # reshape the blocks to have size (1x64)

    # img_dct should have one element for each block, as before, and each element 
    # should be a 64-element array instread of a 8x8 2d matrix

    # remove the first element, only god knows why
    img_dct = img_dct[:, 1:] 
    
    # img_dct should have n blocks each with 63 dct coefficients in a row

    # actually compute first digit vector
    fd = first_digit_gen(img_dct, base)

    # we should have n rows, each with 10 columns
    # each column should contain the frequency of the index + 1 as first digit
    
    # reordering in zig zag order
    fd = fd[:, zig_zag_idx[1:] - 1]

    # computing histograms
    ff = compute_histograms(fd, base)

    return ff


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', help='dataset name', type=str)
    parser.add_argument('--jpeg', help='jpeg compression QF', required=True, type=int)
    parser.add_argument('--jpeg_recompression', action='store_true', default=False)
    parser.add_argument('--recompression_qf', type=int)
    parser.add_argument('--workers', help='Number of parallel workers', type=int, default=cpu_count() // 2)
    args = parser.parse_args()

    dataset_name = args.dataset
    jpeg_qf = args.jpeg
    jpeg_recompression = args.jpeg_recompression
    recompression_qf = args.recompression_qf
    workers = args.workers

    recompression_qf_suf = '_{}'.format(recompression_qf)

    # create temporary folder to store the intermediate jpeg files
    os.makedirs(tmp_path, mode=0o755, exist_ok=True)

    if dataset_name is None:
        dataset_list = [x for x in dataset_ext.keys()]
    else:
        dataset_list = [dataset_name]

    for dataset_name in tqdm(dataset_list):

        if dataset_name not in dataset_root:
            print('Dataset must be registered in dataset_root variable (params.py). {} not found'.format(dataset_name))
            return 1

        # Retrieve all the dataset filenames
        path_list = glob.glob(os.path.join(dataset_root[dataset_name], '*.{}'.format(dataset_ext[dataset_name])))

        for base in base_list:

            # check if already computed
            compression = 'jpeg_{}'.format(jpeg_qf)
            fd_hist_dir = fd_hist_root + '_recompression{}'.format(
                recompression_qf_suf) if jpeg_recompression else fd_hist_root
            dir_name = os.path.join(fd_hist_dir, compression, 'b{}'.format(base))
            out_name = os.path.join(dir_name, '{}.npy'.format(dataset_name))

            if os.path.exists(out_name):
                print('Already computed, {}, base {},'
                      'compression {}, recompression {}. Skipping...'.format(dataset_name,
                                                                             base,
                                                                             jpeg_qf,
                                                                             jpeg_recompression))
                continue
            else:
                # prepare arguments
                args_list = list()
                for path in path_list:
                    arg = dict()
                    arg['path'] = os.path.join(dataset_root[dataset_name], path)
                    arg['base'] = base
                    arg['jpeg_qf'] = jpeg_qf
                    arg['jpeg_recompression'] = jpeg_recompression
                    arg['recompression_qf'] = recompression_qf
                    args_list += [arg]

                # compute first digits
                p = Pool(workers, maxtasksperchild=2)

                print('Computing first digits for {}, base {}, compression {}, {} images'.format(dataset_name, base,
                                                                                                 jpeg_qf,
                                                                                                 len(args_list)))

                """

                first_digit_call:
                    JPEG recompression if jpeg_recompression flag is True
                    
                    DCT extraction 
                        extract_features_from_dct -> returns the dct for each 8x8 block

                    vectorize and remove DC
                    
                    actually compute first digit vector
                        first_digit_gen

                    reordering in zig zag order (?)

                    computing histograms
                        compute_histograms

                """
                ff = p.map(first_digit_call, args_list)
                ff = np.asarray(ff)

                # saving features
                os.makedirs(dir_name, mode=0o755, exist_ok=True)
                np.save(out_name, ff)

                # cleaning unused variables
                del ff
                tmp_file_list = glob.glob(os.path.join(tmp_path, '*.jpg'))
                [os.remove(x) for x in tmp_file_list]

    return 0


if __name__ == '__main__':
    main()
