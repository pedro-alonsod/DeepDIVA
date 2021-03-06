"""
Load a dataset of images by specifying the folder where its located.
"""

# Utils
import logging
import os
import sys
import pandas as pd
import numpy as np

# Torch related stuff
import torch
import torchvision
import torch.utils.data as data
from torchvision.datasets.folder import pil_loader

from util.misc import get_all_files_in_folders_and_subfolders, has_extension


def load_dataset(dataset_folder, in_memory=False, workers=1):
    """
    Loads the dataset from file system and provides the dataset splits for train validation and test

    The dataset is expected to be in the following structure, where 'dataset_folder' has to point to
    the root of the three folder train/val/test.

    Example:

        dataset_folder = "~/../../data/cifar"

    which contains the splits sub-folders as follow:

        'dataset_folder'/train
        'dataset_folder'/val
        'dataset_folder'/test

    In each of the three splits (train, val, test) should have different classes in a separate folder
    with the class name. The file name can be arbitrary i.e. it does not have to be 0-* for classes 0
    of MNIST.

    Example:

        train/dog/whatever.png
        train/dog/you.png
        train/dog/like.png

        train/cat/123.png
        train/cat/nsdf3.png
        train/cat/asd932_.png

        train/"class_name"/*.png

    Parameters
    ----------
    dataset_folder : string
        Path to the dataset on the file System

    in_memory : boolean
        Load the whole dataset in memory. If False, only file names are stored and images are loaded
        on demand. This is slower than storing everything in memory.

    workers: int
        Number of workers to use for the dataloaders

    Returns
    -------
    train_ds : data.Dataset

    val_ds : data.Dataset

    test_ds : data.Dataset
        Train, validation and test splits
    """
    # Get the splits folders
    train_dir = os.path.join(dataset_folder, 'train')
    val_dir = os.path.join(dataset_folder, 'val')
    test_dir = os.path.join(dataset_folder, 'test')

    # Sanity check on the splits folders
    if not os.path.isdir(train_dir):
        logging.error("Train folder not found in the dataset_folder=" + dataset_folder)
        sys.exit(-1)
    if not os.path.isdir(val_dir):
        logging.error("Val folder not found in the dataset_folder=" + dataset_folder)
        sys.exit(-1)
    if not os.path.isdir(test_dir):
        logging.error("Test folder not found in the dataset_folder=" + dataset_folder)
        sys.exit(-1)

    train_ds = MultiLabelImageFolder(train_dir, workers)
    val_ds = MultiLabelImageFolder(val_dir, workers)
    test_ds = MultiLabelImageFolder(test_dir, workers)
    return train_ds, val_ds, test_ds


class MultiLabelImageFolder(data.Dataset):
    """
    This class loads the multi-label image data provided.

    """

    def __init__(self, path, transform=None, target_transform=None, workers=1):
        """
        Load the data in memory and prepares it as a dataset.

        Parameters
        ----------
        path : string
            Path to the dataset on the file System
        transform : torchvision.transforms
            Transformation to apply on the data
        target_transform : torchvision.transforms
            Transformation to apply on the labels
        workers: int
            Number of workers to use for the dataloaders
        """
        self.dataset_folder = os.path.expanduser(path)
        self.transform = transform
        self.target_transform = target_transform

        df = pd.read_csv(os.path.join(self.dataset_folder, 'labels.csv'))

        self.filenames = df.as_matrix()[:, 0]
        self.filenames = [os.path.join(self.dataset_folder, item) for item in self.filenames]

        self.labels = df.as_matrix()[:, 1:]

        self.class_names = df.columns[1:]
        self.classes = np.arange(len(self.class_names))

    def __getitem__(self, index):
        """
        Retrieve a sample by index

        Parameters
        ----------
        index : int

        Returns
        -------
        img : FloatTensor
        target : int
            label of the image
        """

        img, target = self.filenames[index], self.labels[index]

        img = pil_loader(img)
        target = torch.from_numpy(target.astype(np.float32))
        target[target == -1] = 0

        if self.transform is not None:
            img = self.transform(img)
        if self.target_transform is not None:
            target = self.target_transform(target)

        return img, target

    def __len__(self):
        return len(self.filenames)
