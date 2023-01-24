import os

root_dir = '/content/gdrive/MyDrive/VisionPE/icpr-benford-gan/'

tmp_path = '/content/gdrive/MyDrive/VisionPE/icpr-benford-gan/.temp'

# images1024x1024 dataset (original)
images1024x1024_root = '/content/gdrive/MyDrive/VisionPE/data/images1024x1024_jpg'

# all the dataset generated will be named 'images1024x1024_orig_x_jpg'
dataset_images1024x1024_dict =  dict((f'images1024x1024_orig_{i}_jpg', os.path.join(images1024x1024_root, f'{i * 1000:0>5d}_jpg')) for i in range(70))
dataset_images1024x1024_ext =   dict((f'images1024x1024_orig_{i}_jpg', 'jpg') for i in range(70))
dataset_images1024x1024_label = dict((f'images1024x1024_orig_{i}_jpg', i) for i in range(70))

# celebHQ dataset (original)
celebAHQ_root = '/content/gdrive/MyDrive/VisionPE/data/celebAHQ/images1024x1024'
dataset_celebAHQ_dict  = {'celebAHQ_orig': celebAHQ_root}
dataset_celebAHQ_ext   = {'celebAHQ_orig': 'jpg'}
dataset_celebAHQ_label = {'celebAHQ_orig': 71} # last images1024x1024 label + 1

# FaceForensics (gan)
FaceForensics_root = '/content/gdrive/MyDrive/VisionPE/data/FaceForensics_Images_jpg/images_jpg'
dataset_FaceForensics_dict  = {'FaceForensics_gan_jpg': FaceForensics_root}
dataset_FaceForensics_ext   = {'FaceForensics_gan_jpg': 'jpg'}
dataset_FaceForensics_label = {'FaceForensics_gan_jpg': 72} # last celebHQ label + 1

# StyleGAN2 (gan)
StyleGAN2_root = '/content/gdrive/MyDrive/VisionPE/data/StyleGAN2_jpg'
dataset_StyleGAN2_dict  = dict((f'StyleGAN2_gan_{i}_jpg', os.path.join(StyleGAN2_root, f'{i * 1000:0>6d}_jpg')) for i in range(100))
dataset_StyleGAN2_ext   = dict((f'StyleGAN2_gan_{i}_jpg', 'jpg') for i in range(100)) # 100 folders
dataset_StyleGAN2_label = dict((f'StyleGAN2_gan_{i - 73}_jpg', i) for i in range(73, 174))


# putting all dictionaries together
# for python 3.5 or greater
#dataset_root = {**dataset_images1024x1024_dict, **dataset_celebAHQ_dict}
#dataset_ext = {**dataset_images1024x1024_ext, **dataset_celebAHQ_ext}
#dataset_label = {**dataset_images1024x1024_label, **dataset_celebAHQ_label}

# putting all dictionaries together
# for python 3.9 or greater
#dataset_root = dataset_images1024x1024_dict | dataset_celebAHQ_dict | dataset_StyleGAN2_dict | dataset_FaceForensics_dict
#dataset_ext = dataset_images1024x1024_ext | dataset_celebAHQ_ext | dataset_StyleGAN2_ext | dataset_FaceForensics_ext
#dataset_label = dataset_images1024x1024_label | dataset_celebAHQ_label | dataset_StyleGAN2_label | dataset_FaceForensics_label

# good ol way

roots  = [dataset_images1024x1024_dict, dataset_celebAHQ_dict, dataset_StyleGAN2_dict, dataset_FaceForensics_dict]
exts   = [dataset_images1024x1024_ext, dataset_celebAHQ_ext, dataset_StyleGAN2_ext, dataset_FaceForensics_ext]
labels = [dataset_images1024x1024_label, dataset_celebAHQ_label, dataset_StyleGAN2_label, dataset_FaceForensics_label]

dataset_root = {k: v for d in roots for k,v in d.items()}
dataset_ext = {k: v for d in exts for k,v in d.items()}
dataset_label = {k: v for d in labels for k,v in d.items()}


# other parameters

popt_dict = {'scale': 0, 'alpha': 1, 'beta': 2}

features_root = os.path.join(root_dir, 'features')
fd_hist_root = os.path.join(features_root, 'fd_hist')
features_div_root = os.path.join(features_root, 'features_div')
cooccurrences_root = os.path.join(root_dir, 'cooccurrences')
data_root = os.path.join(root_dir, 'data')
runs_root = os.path.join(root_dir, 'runs')
results_root = os.path.join(root_dir, 'results')

# numeric system bases
#base_list = [10, 20, 40, 60]
base_list = [10, 20, 40, 60]

# bins
coeff_list = list(range(9))

# compression quality 
#compression_list = ['jpeg_80', 'jpeg_85', 'jpeg_90', 'jpeg_95', 'jpeg_100']
compression_list = ['jpeg_100']

#jpeg_list = [80, 85, 90, 95, 100]
jpeg_list = [100]

# Just a reminder of which params we use as best combinations
default_param_idx = [674, 662, 581, 554]

# Handy for dealing with datasets
dataset_label_vis = {v: k.rsplit('_', 1)[0] for k, v in dataset_label.items()}

