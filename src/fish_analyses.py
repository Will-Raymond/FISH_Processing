# !/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Python codes to analyze FISH images using (FISH-quant v2) BIG-FISH.
Created on Fri Oct 22 10:41:00 2021
Authors: Luis U. Aguilera, Joshua Cook, Brian Munsky.
'''

# Conventions.
# module_name, package_name, ClassName, method_name,
# ExceptionName, function_name, GLOBAL_CONSTANT_NAME,
# global_var_name, instance_var_name, function_parameter_name, local_var_name.


import_libraries = 1
if import_libraries == 1:
    # importing Big-FISH
    import bigfish.stack as stack
    import bigfish.plot as plot
    import bigfish.detection as detection
    import bigfish.multistack as multistack
    import pandas as pd
    # importing libraries
    import pathlib
    import numpy as np
    import matplotlib.pyplot as plt
    import re  
    #import time
    from skimage.io import imread
    from scipy import ndimage
    import glob
    import tifffile
    import pyfiglet
    import sys
    import datetime
    import getpass
    import pkg_resources
    import platform
    from cellpose import models
    import os; from os import listdir; from os.path import isfile, join
    import warnings
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    warnings.filterwarnings('ignore', category=FutureWarning)
    # Skimage
    from skimage.measure import find_contours
    from skimage.io import imread
    from scipy import ndimage
    # Plotting
    import matplotlib.pyplot as plt
    import matplotlib.path as mpltPath
    #from matplotlib import gridspec
    plt.style.use('ggplot')  # ggplot  #default

    from joblib import Parallel, delayed
    import multiprocessing
    # SMB connection
    from smb.SMBConnection import SMBConnection
    import socket
    import pathlib
    import yaml
    import shutil
    # To create PDF report
    from fpdf import FPDF
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    if np.random.randint(0,2,1)[0] ==0:
        try:
            os.environ["CUDA_VISIBLE_DEVICES"] = "1" 
        except:
            os.environ["CUDA_VISIBLE_DEVICES"] = "0" 
    else:
        os.environ["CUDA_VISIBLE_DEVICES"] = "0" 

class Banner():
    def __init__(self,show=True):
        self.show = show
    def print_banner(self):
        if self.show == True:
            print(" \n"
                "FISH processing repository by : \n"
                "Luis U. Aguilera, Joshua Cook, Tim Stasevich, and Brian Munsky. \n" 
                "_____________________________________________________________  \n"      
                "|                      ,#^^^^^^^%&&&                         | \n"
                "|  .&.                 &.           ,&&&___                  | \n"
                "|  &  &         ___&&&/                    (&&&&____         | \n"
                "|  &    &,____#&                   .       #.       %&**,    | \n"
                "|  /(                  &         ,%       &       %     ,&   | \n"
                "|    &          &.                       %.      %&%     &*  | \n"
                "|     &&         *         .%            &             &(    | \n"
                "|   &                &(           ,#     .%             ,.&  | \n"
                "|  &    _&&__#&.     &&           &.      ,&         ,%&     | \n"
                "|  &  (%        #&,___                      (-***%&%^        | \n"
                "|  & &                %&&&(,.      .*#&&&&&%.                | \n"
                "|                          &    ,%%%%                        | \n"
                "|___________________________/%%^_____________________________| \n" )


class NASConnection():
    
    '''
    This class is intended to establish a connection between a Network-Attached storage and a local computer. The class allow the user to establish a connection to NAS, download specific files, and write back files to NAS.
    This class doesn't allow the user to delete, modify or overwrite files in NAS.
    To use this class you need to:
    1) Use the university's network or use the two factor authentication to connect to the university's VPN.
    2) You need to create a configuration yaml file, with the following format:
    user:
        username: name_of_the_user_in_the_nas_server
        password: user_password_in_the_nas_server 
        remote_address : ip or name for the nas server
        domain: domain for the nas server
    
    Parameters
    --  --  --  --  -- 
    ,: bool, optional
        parameter description. The default is True. 
    path_to_config_file : str, Pathlib obj
        The path in the local computer that containts the config file.
    share_name : str
        Name of the share partition to access in NAS. The default is 'share'.
    '''
    def __init__(self,path_to_config_file,share_name = 'share'):
        # Loading credentials
        conf = yaml.safe_load(open(str(path_to_config_file)))
        usr = conf['user']['username']
        pwd = conf['user']['password']
        remote_address = conf['user']['remote_address']
        domain = conf['user']['domain']
        # LOCAL NAME
        local_name = socket.gethostbyname(socket.gethostname())
        # SERVER NAME
        self.share_name = share_name
        self.server_name, alias, addresslist = socket.gethostbyaddr(remote_address)
        # Deffining the connection to NAS
        self.conn = SMBConnection(username=usr, password=pwd, domain=domain, my_name=local_name, remote_name=self.server_name, is_direct_tcp=True)
    def connect_to_server(self,timeout=60):
        is_connected = self.conn.connect(self.server_name,timeout=timeout)
        if is_connected == True:
            print('Connection established')
        else:
            print('Connection failed')
        return self.conn

    def read_files(self, remote_folder_path, timeout=60):
        '''
        This method reads all files from a NAS directory
        Parameters
        --  --  --  --  -- 
        remote_folder_path : str, Pathlib obj
            The path in the remote folder to download
        timeout : int, optional
            seconds to establish connection. The default is 60.
        '''
        # Connecting to NAS
        is_connected = self.conn.connect(self.server_name,timeout=timeout)
        if is_connected == True:
            print('Connection established')
        else:
            print('Connection failed')
        # Converting the paths to a Pathlib object
        if type(remote_folder_path)==str:
            remote_folder_path = pathlib.Path(remote_folder_path)
        # Iterate in the folder to download all tif files
        list_files =[]
        list_dir = self.conn.listPath(self.share_name, str(remote_folder_path))
        for file in list_dir:
            list_files.append(file.filename)
        return list_files

    def download_file(self, remote_file_path, local_folder_path, timeout=60):
        '''
        This method download an specific file
        Parameters
        --  --  --  --  -- 
        remote_file_path : str, Pathlib obj
            The path in the remote file to download
        local_folder_path : str, Pathlib obj
            The path in the local computer where the files will be copied
        timeout : int, optional
            seconds to establish connection. The default is 60.
        '''
        # Connecting to NAS
        is_connected = self.conn.connect(self.server_name,timeout=timeout)
        if is_connected == True:
            print('Connection established')
        else:
            print('Connection failed')
        # Converting the paths to a Pathlib object
        if type(local_folder_path) == str:
            local_folder_path = pathlib.Path(local_folder_path)
        if type(remote_file_path)==str:
            remote_file_path = pathlib.Path(remote_file_path)
        # Making the local directory
        if not (os.path.exists(local_folder_path)) :
            os.makedirs(str(local_folder_path))
        filename = remote_file_path.name
        fileobj = open(remote_file_path.name,'wb')
        self.conn.retrieveFile(self.share_name, str(remote_file_path), fileobj)
        fileobj.close()
        # moving files in the local computer
        shutil.move(pathlib.Path().absolute().joinpath(filename), local_folder_path.joinpath(filename))
        print('Files downloaded to: ' + str(local_folder_path.joinpath(filename)))


    def copy_files(self, remote_folder_path, local_folder_path, timeout=60, file_extension ='.tif'):
        '''
        This method downloads the tif files from NAS to a temp folder in the local computer
        Parameters
        --  --  --  --  -- 
        remote_folder_path : str, Pathlib obj
            The path in the remote folder to download
        local_folder_path : str, Pathlib obj
            The path in the local computer where the files will be copied
        timeout : int, optional
            seconds to establish connection. The default is 60.
        '''
        # Connecting to NAS
        is_connected = self.conn.connect(self.server_name,timeout=timeout)
        if is_connected == True:
            print('Connection established')
        else:
            print('Connection failed')
        # Converting the paths to a Pathlib object
        if type(local_folder_path) == str:
            local_folder_path = pathlib.Path(local_folder_path)
        if type(remote_folder_path)==str:
            remote_folder_path = pathlib.Path(remote_folder_path)
        # Creating a temporal folder in path
        #if  not str(local_folder_path)[0:5] ==  'temp_':
        #    local_folder_path = pathlib.Path(local_folder_path).joinpath('temp_' + local_folder_path.name )
        # Making the local directory
        if (os.path.exists(local_folder_path))  and  (str(local_folder_path.name)[0:5] ==  'temp_'):
            shutil.rmtree(local_folder_path)
        os.makedirs(str(local_folder_path))
        
        # Iterate in the folder to download all tif files
        list_dir = self.conn.listPath(self.share_name, str(remote_folder_path))
        for file in list_dir:
            if (file.filename not in ['.', '..']) and (file_extension in file.filename)  :
                print ('File Downloaded :', file.filename)
                fileobj = open(file.filename,'wb')
                self.conn.retrieveFile(self.share_name, str( pathlib.Path(remote_folder_path).joinpath(file.filename) ),fileobj)
                fileobj.close()
                # moving files in the local computer
                shutil.move(pathlib.Path().absolute().joinpath(file.filename), local_folder_path.joinpath(file.filename))
        print('Files downloaded to: ' + str(local_folder_path))
    
    def write_files_to_NAS(self, local_file_to_send_to_NAS, remote_folder_path,  timeout=60):
        '''
        This method writes files from a local computer to NAS 
        Parameters
        --  --  --  --  -- 
        remote_folder_path : str, Pathlib obj
            The path in the remote folder to download
        local_folder_path : str, Pathlib obj
            The path in the local computer where the files will be copied
        timeout : int, optional
            seconds to establish connection. The default is 60.
        '''
        # Connecting to NAS
        is_connected = self.conn.connect(self.server_name,timeout=timeout)
        if is_connected == True:
            print('Connection established')
        else:
            print('Connection failed')
        # Converting the paths to a Pathlib object
        if type(local_file_to_send_to_NAS) == str:
            local_file_to_send_to_NAS = pathlib.Path(local_file_to_send_to_NAS)

        if type(remote_folder_path)==str:
            remote_folder_path = pathlib.Path(remote_folder_path)

        # checks that the file doesn't exist on NAS. If it exist it will create a new name as follows original_name__1
        # Iterate in the folder to download all tif files
        list_dir = self.conn.listPath(self.share_name, str(remote_folder_path))
        list_all_files_in_NAS = [file.filename for file in list_dir]
        if str(local_file_to_send_to_NAS.name) not in list_all_files_in_NAS:
            with open(str(local_file_to_send_to_NAS), 'rb') as file_obj:
                self.conn.storeFile(self.share_name, str( pathlib.Path(remote_folder_path).joinpath(local_file_to_send_to_NAS.name) ) ,  file_obj )
                print ('The file was uploaded to NAS in location:', str( pathlib.Path(remote_folder_path).joinpath(local_file_to_send_to_NAS.name))  )
      

class ReadImages():
    '''
    This class reads all .tif images in a given folder and returns the names of these files, path, and number of files.
    
    Parameters
    --  --  --  --  -- 
    directory: str or PosixPath
        Directory containing the images to merge.
    '''    
    def __init__(self, directory:str ):
        if type(directory)== pathlib.PosixPath:
            self.directory = directory
        else:
            self.directory = pathlib.Path(directory)
    def read(self):
        '''
        Method takes all the videos in the folder and merge those with similar names.
        Returns
        --  --  -- -
        list_images : List of NumPy arrays. 
            List of NumPy arrays with format np.uint16 and dimensions [Z, Y, X, C] or [T, Y, X, C] . 
        list_file_names : List of strings 
            List with strings of names.
        number_files : int. 
            Number of images in the folder.
        '''
        list_files_names = sorted([f for f in listdir(self.directory) if isfile(join(self.directory, f)) and ('.tif') in f], key=str.lower)  # reading all tif files in the folder
        list_files_names.sort(key=lambda f: int(re.sub('\D', '', f)))  # sorting the index in numerical order
        path_files = [ str(self.directory.joinpath(f).resolve()) for f in list_files_names ] # creating the complete path for each file
        number_files = len(path_files)
        list_images = [imread(f) for f in path_files]
        list_images_rm = [RemoveExtrema(im,min_percentile=0.01, max_percentile=99.9).remove_outliers()  for im in list_images]
        list_images_unit16 = [img[1:15].astype(np.uint16) for img in list_images_rm  ]
        return list_images_unit16, path_files, list_files_names, number_files


class MergeChannels():
    '''
    This class takes images as arrays with format [Z,Y,X] and merge then in a numpy array with format [Z, Y, X, C].
    It recursively merges the channels in a new dimenssion in the array. Minimal number of Channels 2 maximum is 4
    
    Parameters
    --  --  --  --  -- 
    directory: str or PosixPath
        Directory containing the images to merge.
    substring_to_detect_in_file_name: str
        String with the prefix to detect in the files names. 
    save_figure: bool, optional
        Flag to save the merged images as .tif. The default is False. 
    '''
    def __init__(self, directory:str ,substring_to_detect_in_file_name:str = '.*_C0.tif', save_figure:bool = False ):
        if type(directory)== pathlib.PosixPath:
            self.directory = directory
        else:
            self.directory = pathlib.Path(directory)
        self.substring_to_detect_in_file_name = substring_to_detect_in_file_name
        self.save_figure=save_figure

    def checking_images(self):
        '''
        Method takes all the videos in the folder and merge those with similar names.
        Returns
        --  --  -- -
        list_file_names : List of strings 
            List with strings of names.
        list_merged_images : List of NumPy arrays. 
            List of NumPy arrays with format np.uint16 and dimensions [Z, Y, X, C].
        number_files : int. 
            Number of merged images in the folder.
        '''
        # This function 
        ending_string = re.compile(self.substring_to_detect_in_file_name)  # detecting files ending in _C0.tif
        for _, _, files in os.walk(self.directory):
            for file in files:
                if ending_string.match(file) and file[0]!= '.' : # detecting a match in the end, not consider hidden files starting with '.'
                    prefix = file.rpartition('_')[0]            # stores a string with the first part of the file name before the last underscore character in the file name string.
                    list_files_per_image = sorted ( glob.glob( str(self.directory.joinpath(prefix)) + '*.tif')) # List of files that match the pattern 'file_prefix_C*.tif'
                    if len(list_files_per_image)>1:             # creating merged files if more than one images with the same ending substring are detected.
                        return True
                    else:
                        return False
    
    def merge(self):
        '''
        Method takes all the videos in the folder and merge those with similar names.
        Returns
        --  --  -- -
        list_file_names : List of strings 
            List with strings of names.
        list_merged_images : List of NumPy arrays. 
            List of NumPy arrays with format np.uint16 and dimensions [Z, Y, X, C].
        number_files : int. 
            Number of merged images in the folder.
        '''
        # This function 
        list_file_names =[]
        list_merged_images =[]  # list that stores all files belonging to the same image in a sublist
        ending_string = re.compile(self.substring_to_detect_in_file_name)  # detecting files ending in _C0.tif
        save_to_path = self.directory.joinpath('merged')
        for _, _, files in os.walk(self.directory):
            for file in files:
                if ending_string.match(file) and file[0]!= '.': # detecting a match in the end, not consider hidden files starting with '.'
                    prefix = file.rpartition('_')[0]            # stores a string with the first part of the file name before the last underscore character in the file name string.
                    list_files_per_image = sorted ( glob.glob( str(self.directory.joinpath(prefix)) + '*.tif') ) # List of files that match the pattern 'file_prefix_C*.tif'
                    if len(list_files_per_image)>1:             # creating merged files if more than one images with the same ending substring are detected.
                        try:
                            list_file_names.append(prefix)
                            merged_img = np.concatenate([ imread(list_files_per_image[i])[..., np.newaxis] for i,_ in enumerate(list_files_per_image)],axis=-1).astype('uint16')
                            list_merged_images.append(merged_img) 
                        except:
                            print('A corrupted file was detected during the merge of the following files: \n', list_files_per_image,'\n')
                    if self.save_figure ==1 and len(list_files_per_image)>1:
                        if not os.path.exists(str(save_to_path)):
                            os.makedirs(str(save_to_path))
                        tifffile.imsave(str(save_to_path.joinpath(prefix+'_merged'+'.tif')), merged_img, metadata={'axes': 'ZYXC'})
                    #del merged_img, list_files_per_image
        number_files = len(list_file_names)
        return list_file_names, list_merged_images, number_files,save_to_path


class RemoveExtrema():
    '''
    This class is intended to remove extreme values from a video. The format of the video must be [Y, X] , [Y, X, C] , [Z, Y, X, C] or [T, Y, X, C].
    Parameters
    --  --  --  --  -- 
    video : NumPy array
        Array of images with dimensions [Y, X] , [Y, X, C] , [Z, Y, X, C] or [T, Y, X, C].
    min_percentile : float, optional
        Lower bound to normalize intensity. The default is 1.
    max_percentile : float, optional
        Higher bound to normalize intensity. The default is 99.
    selected_channels : List or None, optional
        Use this option to select a list channels to remove extrema. The default is None and applies the removal of extrema to all the channels.
    '''
    def __init__(self, video:np.ndarray, min_percentile:float = 1, max_percentile:float = 99, selected_channels = None):
        self.video = video
        self.min_percentile = min_percentile
        self.max_percentile = max_percentile
        #self.ignore_channel = ignore_channel
        if not (type(selected_channels) is list):
                self.selected_channels = [selected_channels]
        else:
            self.selected_channels =selected_channels

    def remove_outliers(self):
        '''
        This method normalizes the values of a video by removing extreme values.
        Returns
        --  --  -- -
        normalized_video : np.uint16
            Normalized video. Array with dimensions [T, Y, X, C] or image with format [Y, X].
        '''
        normalized_video = np.copy(self.video)
        normalized_video = np.array(normalized_video, 'float32')
        # Normalization code for image with format [Y, X]
        if len(self.video.shape) == 2:
            number_timepoints = 1
            number_channels = 1
            normalized_video_temp = normalized_video
            if not np.amax(normalized_video_temp) == 0: # this section detect that the channel is not empty to perform the normalization.
                max_val = np.percentile(normalized_video_temp, self.max_percentile)
                min_val = np.percentile(normalized_video_temp, self.min_percentile)
                normalized_video_temp [normalized_video_temp > max_val] = max_val
                normalized_video_temp [normalized_video_temp < min_val] = min_val
                normalized_video_temp [normalized_video_temp < 0] = 0
        
        # Normalization for video with format [Y, X, C].
        if len(self.video.shape) == 3:
            number_channels   = self.video.shape[2]
            for index_channels in range (number_channels):
                if (index_channels in self.selected_channels) or (self.selected_channels is None) :
                    normalized_video_temp = normalized_video[ :, :, index_channels]
                    if not np.amax(normalized_video_temp) == 0: # this section detect that the channel is not empty to perform the normalization.
                        max_val = np.percentile(normalized_video_temp, self.max_percentile)
                        min_val = np.percentile(normalized_video_temp, self.min_percentile)
                        normalized_video_temp [normalized_video_temp > max_val] = max_val
                        normalized_video_temp [normalized_video_temp < min_val] =  min_val
                        normalized_video_temp [normalized_video_temp < 0] = 0
        
        # Normalization for video with format [T, Y, X, C] or [Z, Y, X, C].
        if len(self.video.shape) == 4:
            number_timepoints, number_channels   = self.video.shape[0], self.video.shape[3]
            for index_channels in range (number_channels):
                if (index_channels in self.selected_channels) or (self.selected_channels is None) :
                #if not self.ignore_channel == index_channels:
                    for index_time in range (number_timepoints):
                        normalized_video_temp = normalized_video[index_time, :, :, index_channels]
                        if not np.amax(normalized_video_temp) == 0: # this section detect that the channel is not empty to perform the normalization.
                            max_val = np.percentile(normalized_video_temp, self.max_percentile)
                            min_val = np.percentile(normalized_video_temp, self.min_percentile)
                            normalized_video_temp [normalized_video_temp > max_val] = max_val
                            normalized_video_temp [normalized_video_temp < min_val] = min_val
                            normalized_video_temp [normalized_video_temp < 0] = 0
        return np.asarray(normalized_video, 'uint16')


class Cellpose():
    '''
    This class is intended to detect cells by image masking using **Cellpose** . The class uses optimization to maximize the number of cells or maximize the size of the detected cells.
    Parameters
    --  --  --  --  -- 
    video : NumPy array
        Array of images with dimensions [T, Y, X, C].
    num_iterations : int, optional
        Number of iterations for the optimization process. The default is 5.
    channels : List, optional
        List with the channels in the image. For gray images use [0, 0], for RGB images with intensity for cytosol and nuclei use [0, 1] . The default is [0, 0].
    diameter : float, optional
        Average cell size. The default is 120.
    model_type : str, optional
        To detect between the two options: 'cyto' or 'nuclei'. The default is 'cyto'.
    selection_method : str, optional
        Option to use the optimization algorithm to maximize the number of cells or maximize the size options are 'max_area' or 'max_cells' or 'max_cells_and_area'. The default is 'max_cells_and_area'.
    '''
    def __init__(self, video:np.ndarray, num_iterations:int = 5, channels:list = [0, 0], diameter:float = 120, model_type:str = 'cyto', selection_method:str = 'max_cells_and_area', NUMBER_OF_CORES:int=1):
        self.video = video
        self.num_iterations = num_iterations
        self.minimumm_probability = 0
        self.maximum_probability = 2
        self.channels = channels
        self.diameter = diameter
        self.model_type = model_type # options are 'cyto' or 'nuclei'
        self.selection_method = selection_method # options are 'max_area' or 'max_cells'
        self.NUMBER_OF_CORES = NUMBER_OF_CORES
        self.CELLPOSE_PROBABILITY = 0.6
        self.optimization_parameter = np.round(np.linspace(self.minimumm_probability, self.maximum_probability, self.num_iterations), 2)
        #self.optimization_parameter = np.round(np.linspace( self.diameter ,self.diameter+50, self.num_iterations),0)
        #self.optimization_parameter = np.linspace(50,350,self.num_iterations)
    def calculate_masks(self):
        '''
        This method performs the process of image masking using **Cellpose**.
        Returns
        --  --  -- -
        selected_masks : List of NumPy arrays
            List of NumPy arrays with values between 0 and the number of detected cells in the image, where a number larger than zero represents the masked area for each cell, and 0 represents the area where no cells are detected.
        '''
        # Next two lines suppressing output from cellpose
        #old_stdout = sys.stdout
        #sys.stdout = open(os.devnull, "w")
        model = models.Cellpose(gpu = 1, model_type = self.model_type, omni = False) # model_type = 'cyto' or model_type = 'nuclei'
        # Loop that test multiple probabilities in cell pose and returns the masks with the longest area.
        def cellpose_max_area( optimization_parameter):
            try:
                #masks, _, _, _ = model.eval(self.video, normalize = True, mask_threshold =  self.CELLPOSE_PROBABILITY , diameter = optimization_parameter, min_size = -1, channels = self.channels, progress = None)
                masks, _, _, _ = model.eval(self.video, normalize = True, mask_threshold = optimization_parameter, diameter = self.diameter, min_size = -1, channels = self.channels, progress = None)
            except:
                masks =0
            n_masks = np.amax(masks)
            if n_masks > 1: # detecting if more than 1 mask are detected per cell
                size_mask = []
                for nm in range (1, n_masks+1): # iterating for each mask in a given cell. The mask has values from 0 for background, to int n, where n is the number of detected masks.
                    size_mask.append(np.sum(masks == nm)) # creating a list with the size of each mask
                largest_mask = np.argmax(size_mask)+1 # detecting the mask with the largest value
                temp_mask = np.zeros_like(masks) # making a copy of the image
                selected_mask = temp_mask + (masks == largest_mask) # Selecting a single mask and making this mask equal to one and the background equal to zero.
                return np.sum(selected_mask)
            else: # do nothing if only a single mask is detected per image.
                return np.sum(masks)
        def cellpose_max_cells(optimization_parameter):
            try:
                masks, _, _, _ = model.eval(self.video, normalize = True, mask_threshold = optimization_parameter, diameter =self.diameter, min_size = -1, channels = self.channels, progress = None)
            except:
                masks =0
            return np.amax(masks)

        def cellpose_max_cells_and_area( optimization_parameter):
            try:
                masks, _, _, _ = model.eval(self.video, normalize = True, mask_threshold = optimization_parameter, diameter = self.diameter, min_size = -1, channels = self.channels, progress = None)
            except:
                masks =0
            n_masks = np.amax(masks)
            if n_masks > 1: # detecting if more than 1 mask are detected per cell
                size_mask = []
                for nm in range (1, n_masks+1): # iterating for each mask in a given cell. The mask has values from 0 for background, to int n, where n is the number of detected masks.
                    size_mask.append(np.sum(masks == nm)) # creating a list with the size of each mask
                number_masks= np.amax(masks)
                #metric = np.sum(np.asarray(size_mask)) * number_masks
                metric = np.sum(np.asarray(size_mask)) * number_masks

                return metric
            if n_masks == 1: # do nothing if only a single mask is detected per image.
                return np.sum(masks == 1)
            else:  # return zero if no mask are detected
                return 0     
        if self.selection_method == 'max_area':
            list_metrics_masks = Parallel(n_jobs = self.NUMBER_OF_CORES)(delayed(cellpose_max_area)(tested_parameter) for _, tested_parameter in enumerate(self.optimization_parameter))
            evaluated_metric_for_masks = np.asarray(list_metrics_masks)
        if self.selection_method == 'max_cells':
            list_metrics_masks = Parallel(n_jobs = self.NUMBER_OF_CORES)(delayed(cellpose_max_cells)(tested_parameter) for _,tested_parameter in enumerate(self.optimization_parameter))
            evaluated_metric_for_masks = np.asarray(list_metrics_masks)
        if self.selection_method == 'max_cells_and_area':
            list_metrics_masks = Parallel(n_jobs = self.NUMBER_OF_CORES)(delayed(cellpose_max_cells_and_area)(tested_parameter) for _,tested_parameter in enumerate(self.optimization_parameter))
            evaluated_metric_for_masks = np.asarray(list_metrics_masks)
        if np.amax(evaluated_metric_for_masks) >0:
            selected_conditions = self.optimization_parameter[np.argmax(evaluated_metric_for_masks)]
            selected_masks, _, _, _ = model.eval(self.video, normalize = True, mask_threshold = selected_conditions , diameter = self.diameter, min_size = -1, channels = self.channels, progress = None)
        else:
            selected_masks = None
            print('No cells detected on the image')
        #sys.stdout.close()
        #sys.stdout = old_stdout
        return selected_masks


class CellSegmentation():
    '''
    This class is intended to detect cells in FISH images using **Cellpose**. The class uses optimization to generate the meta-parameters used by cellpose. This class segments the nucleus and cytosol for every cell detected in the image.
    Parameters
    --  --  --  --  -- 
    video : NumPy array
        Array of images with dimensions [Z, Y, X, C] or maximum projection with dimensions [Y,X,C].
    channels_with_cytosol : List of int or None, optional
        DESCRIPTION. The default is None.
    channels_with_nucleus : list of int or None, optional
        DESCRIPTION. The default is None.
    selected_z_slice : int, optional
        DESCRIPTION. The default is 5.
    diameter_cytosol : float, optional
        Average cytosol size in pixels. The default is 150.
    diamter_nucleus : float, optional
        Average nucleus size in pixels. The default is 100.
    remove_fragmented_cells: bool, optional
        If true, it removes masks  in the border of the image. The default is False.
    show_plot : bool, optional
        If true, it shows a plot with the detected masks. The default is True.
    '''
    def __init__(self, video:np.ndarray, channels_with_cytosol = None, channels_with_nucleus= None, selected_z_slice:int = 5, diameter_cytosol:float = 150, diamter_nucleus:float = 100, optimization_segmentation_method='z_slice_segmentation', remove_fragmented_cells:bool=False, show_plot: bool = True, image_name = None):
        self.video = video
        self.selected_z_slice = selected_z_slice
        self.channels_with_cytosol = channels_with_cytosol
        self.channels_with_nucleus = channels_with_nucleus
        self.diameter_cytosol = diameter_cytosol
        self.diamter_nucleus = diamter_nucleus
        self.show_plot = show_plot
        self.NUMBER_OPTIMIZATION_VALUES= 5
        self.remove_fragmented_cells = remove_fragmented_cells
        model_test = models.Cellpose(gpu=True, model_type='cyto')
        self.optimization_segmentation_method = optimization_segmentation_method  # optimization_segmentation_method = 'intensity_segmentation' 'z_slice_segmentation', 'gaussian_filter_segmentation' , None
        if model_test.gpu ==0:
            self.NUMBER_OF_CORES = multiprocessing.cpu_count()
        else:
            self.NUMBER_OF_CORES = 1
        self.image_name = image_name

    def calculate_masks(self):
        '''
        This method performs the process of cell detection for FISH images using **Cellpose**.
        Returns
        --  --  -- -
        list_masks_complete_cells : List of NumPy arrays or a single NumPy array
            Masks for every cell detected in the image. The list contains the mask arrays consisting of one or multiple Numpy arrays with format [Y, X].
        list_masks_nuclei : List of NumPy arrays or a single NumPy array
            Masks for the nuclei for every cell detected in the image. The list contains the mask arrays consisting of one or multiple Numpy arrays with format [Y, X].
        list_masks_cytosol_no_nuclei : List of NumPy arrays or a single NumPy array
            Masks for every nucleus and cytosol for every cell detected in the image. The list contains the mask arrays consisting of one or multiple Numpy arrays with format [Y, X].
        index_paired_masks: List of pairs of int
            List of pairs of integers that associates the detected nuclei and cytosol.
        '''
        # This function is intended to separate masks in list of submasks
        def separate_masks (masks):
            list_masks = []
            n_masks = np.amax(masks)
            if not ( n_masks is None):
                if n_masks > 1: # detecting if more than 1 mask are detected per cell
                    #number_particles = []
                    for nm in range (1, n_masks+1): # iterating for each mask in a given cell. The mask has values from 0 for background, to int n, where n is the number of detected masks.
                        mask_copy = masks.copy()
                        tested_mask = np.where(mask_copy == nm, 1, 0) # making zeros all elements outside each mask, and once all elements inside of each mask.
                        list_masks.append(tested_mask)
                else:  # do nothing if only a single mask is detected per image.
                    list_masks.append(masks)
            else:
                list_masks.append(masks)
            return list_masks

        # This function is intended to merge masks in a single image
        def merge_masks (list_masks):
            n_masks = len(list_masks)
            if not ( n_masks is None):
                if n_masks > 1: # detecting if more than 1 mask are detected per cell
                    base_image = np.zeros_like(list_masks[0])
                    for nm in range (1, n_masks): # iterating for each mask in a given cell. The mask has values from 0 for background, to int n, where n is the number of detected masks.
                        tested_mask = np.where(list_masks[nm] == 1, nm, 0)
                        base_image = base_image + tested_mask
                # making zeros all elements outside each mask, and once all elements inside of each mask.
                else:  # do nothing if only a single mask is detected per image.
                    base_image = list_masks[0]
            else:
                base_image =[]
            masks = base_image.astype(np.uint8)
            return masks

        # function that determines if a cell is in the border of the image
        def remove_fragmented(img_masks):
            img_masks_copy = np.copy(img_masks)
            num_masks_detected = np.amax(img_masks)
            if num_masks_detected > 1:
                for nm in range(1,num_masks_detected+1):
                    tested = np.where(img_masks_copy == nm, 1, 0)   # making zeros all elements outside each mask, and once all elements inside of each mask.
                    # testing if tested is touching the border of the image
                    is_border = np.any( np.concatenate( ( tested[:,0],tested[:,-1],tested[0,:],tested[-1,:] ) ) )
                    #num_border = np.count_nonzero(np.concatenate( ( tested[:,0],tested[:,-1],tested[0,:],tested[-1,:] ) ) )
                    if is_border == True:
                        img_masks = np.where(img_masks == nm, 0, img_masks)
            return img_masks
        
        # this function is intended to convert and np.int16 image to np.int8
        def convert_to_int8(image):
            image = stack.rescale(image, channel_to_stretch=0,stretching_percentile=95)
            imin, imax = np.min(image), np.max(image) 
            image -= imin
            imf = np.array(image, 'float32')
            imf *= 255./(imax-imin)
            image = np.asarray(np.round(imf), 'uint8')
            # padding with zeros the channel dimenssion.
            while image.shape[2]<3:
                zeros_plane = np.zeros_like(image[:,:,0])
                image = np.concatenate((image,zeros_plane[:,:,np.newaxis]),axis=2)
            return image
        
        # function that determines if the nucleus is in the cytosol
        def is_nucleus_in_cytosol(mask_nucleus, mask_cyto):
            nucleusInCell = []
            nucleusInCell.append(0) # Appending an empty value, to avoid errors
            contuour_n = find_contours(mask_nucleus, 0.5)
            contuour_c = find_contours(mask_cyto, 0.5)
            path = mpltPath.Path(contuour_c[0])
            # calculating the center of the mask applying a 10% reduction
            x_coord = [[i][0][1] for i in contuour_n[0]]
            y_coord = [[i][0][0] for i in contuour_n[0]]
            # Center of mask
            center_value = 0.5
            x_center = center_value* min(x_coord) + center_value * max(x_coord)
            y_center = center_value* min(y_coord) + center_value* max(y_coord)
            test_point = [y_center, x_center]
            if path.contains_point(test_point) == 1:
                return 1
            else:
                return 0
        
        # This function takes two list of images for masks and returns a list of lists with pairs indicating the nucleus masks that are contained in a cytosol
        def paired_masks(list_masks_nuclei:list, list_masks_cyto:list):
            n_masks_nuclei = len (list_masks_nuclei)
            n_masks_cyto = len(list_masks_cyto)
            array_paired_masks = np.zeros((n_masks_cyto, n_masks_nuclei)) # This array has dimensions n_masks_cyto, n_masks_nuclei and each entry indicate if the masks are paired
            for i in range(0, n_masks_cyto):
                for j in range (0, n_masks_nuclei):
                    try:
                        array_paired_masks[i, j] = is_nucleus_in_cytosol(list_masks_nuclei[j], list_masks_cyto[i])
                    except:
                        array_paired_masks[i, j] = 0
            # vertical array with paired masks
            itemindex = np.where(array_paired_masks == 1)
            index_paired_masks = np.vstack((itemindex[0], itemindex[1])).T
            return index_paired_masks # This array has dimensions [n_masks_cyto, n_masks_nuclei]
        # This function creates a mask for each cell.
        def generate_masks_complete_cell(index_paired_masks:np.ndarray, list_separated_masks_cyto:list):
            list_masks_complete_cells = []
            #list_idx = []
            for i in range(0, index_paired_masks.shape[0]):
                sel_mask_c = index_paired_masks[i][0]
                list_masks_complete_cells.append(list_separated_masks_cyto[sel_mask_c])
            return list_masks_complete_cells
        # This function creates a mask for each nuclei
        def generate_masks_nuclei(index_paired_masks:np.ndarray, list_separated_masks_nuclei:list):
            list_masks_nuclei = []
            for i in range(0, index_paired_masks.shape[0]):
                sel_mask_n = index_paired_masks[i][1]
                list_masks_nuclei.append(list_separated_masks_nuclei[sel_mask_n])
            return list_masks_nuclei
        
        # This function creates a mask for each cytosol without nucleus
        def generate_masks_cytosol_no_nuclei(index_paired_masks:np.ndarray, list_masks_complete_cells:list, list_masks_nuclei:list):
            list_masks_cytosol_no_nuclei = []
            for i in range(0, index_paired_masks.shape[0]):
                substraction = list_masks_complete_cells[i] - list_masks_nuclei[i]
                substraction[substraction < 0] = 0
                list_masks_cytosol_no_nuclei.append(substraction)
            return list_masks_cytosol_no_nuclei
        
        def join_nulcei_masks(index_paired_masks:np.ndarray, list_masks_nuclei:list):
            # this code detects duplicated mask for the nucleus in the same cell and replaces with a joined mask. Also deletes from the list the duplicated elements.
            index_masks_cytosol = index_paired_masks[:, 0]
            idxs_to_delete = []
            for i in range(0, len (index_masks_cytosol)):
                duplicated_masks_idx = np.where(index_masks_cytosol == i)[0]
                if len(duplicated_masks_idx) > 1:
                    joined_mask = np.zeros_like(list_masks_nuclei[0])
                    for j in range(0, len(duplicated_masks_idx)):
                        joined_mask = joined_mask + list_masks_nuclei[duplicated_masks_idx[j]]
                        joined_mask[joined_mask > 0] = 1
                    list_masks_nuclei[duplicated_masks_idx[0]] = joined_mask # replacing the first duplication occurrence with the joined mask
                    idxs_to_delete.append(duplicated_masks_idx[1::][0])
            # creating a new list with the joined masks
            list_mask_joined = []
            for i in range(0, len (list_masks_nuclei)):
                if i not in idxs_to_delete:
                    list_mask_joined.append(list_masks_nuclei[i])
            # removing from index
            new_index_paired_masks = np.delete(index_paired_masks, idxs_to_delete, axis = 0)
            return list_mask_joined, new_index_paired_masks
        
        ##### IMPLEMENTATION #####
        if len(self.video.shape) > 3:  # [ZYXC]
            video_normalized = np.amax(self.video[3:-3,:,:,:],axis=0)    # taking the mean value
        else:
            video_normalized = self.video # [YXC]       
        
        def function_to_find_masks (video):                
            if not (self.channels_with_cytosol is None):
                masks_cyto = Cellpose(video[:, :, self.channels_with_cytosol],diameter = self.diameter_cytosol, model_type = 'cyto', selection_method = 'max_cells_and_area' ,NUMBER_OF_CORES=self.NUMBER_OF_CORES).calculate_masks()
                if self.remove_fragmented_cells ==1:
                    masks_cyto= remove_fragmented(masks_cyto)
            if not (self.channels_with_nucleus is None):
                masks_nuclei = Cellpose(video[:, :, self.channels_with_nucleus],  diameter = self.diamter_nucleus, model_type = 'nuclei', selection_method = 'max_cells_and_area',NUMBER_OF_CORES=self.NUMBER_OF_CORES).calculate_masks()
                if self.remove_fragmented_cells ==1:
                    masks_nuclei= remove_fragmented(masks_nuclei)
            if not (self.channels_with_cytosol is None) and not(self.channels_with_nucleus is None):
                # Implementation
                list_separated_masks_nuclei = separate_masks(masks_nuclei)
                list_separated_masks_cyto = separate_masks(masks_cyto)
                # Array with paired masks
                index_paired_masks  =  paired_masks(list_separated_masks_nuclei, list_separated_masks_cyto)
                # Optional section that joins multiple nucleus masks
                id_c = index_paired_masks[:, 0].tolist()
                duplicated_nuclei_in_masks = any(id_c.count(x) > 1 for x in id_c)
                if duplicated_nuclei_in_masks == True:
                    list_masks_nuclei, index_paired_masks = join_nulcei_masks(index_paired_masks, list_separated_masks_nuclei)
                # List of mask
                list_masks_complete_cells = generate_masks_complete_cell(index_paired_masks, list_separated_masks_cyto)
                list_masks_nuclei = generate_masks_nuclei(index_paired_masks, list_separated_masks_nuclei)
                list_masks_cytosol_no_nuclei = generate_masks_cytosol_no_nuclei(index_paired_masks, list_masks_complete_cells, list_masks_nuclei)
            else:
                if not (self.channels_with_cytosol is None):
                    list_masks_complete_cells = separate_masks(masks_cyto) # []
                    list_masks_nuclei = []
                    list_masks_cytosol_no_nuclei = []
                    index_paired_masks =[]
                    masks_cyto = None
                    masks_nuclei= None
                if not (self.channels_with_nucleus is None):
                    list_masks_complete_cells = []
                    list_masks_nuclei = separate_masks(masks_nuclei)
                    list_masks_cytosol_no_nuclei = []
                    index_paired_masks =[]
                    masks_cyto = None
            return list_masks_complete_cells, list_masks_nuclei, list_masks_cytosol_no_nuclei, index_paired_masks, masks_cyto, masks_nuclei
        
        # OPTIMIZATION METHODS FOR SEGMENTATION
        if (self.optimization_segmentation_method == 'intensity_segmentation') and (len(self.video.shape) > 3):
            # Intensity Based Optimization to find the maximum number of index_paired_masks. 
            if not (self.channels_with_cytosol is None) and not(self.channels_with_nucleus is None):
                tested_thresholds = np.round(np.linspace(0, 3, self.NUMBER_OPTIMIZATION_VALUES), 0)
                list_sotring_number_paired_masks = []
                for idx, threshold in enumerate(tested_thresholds):
                    video_copy = video_normalized.copy()
                    video_temp = RemoveExtrema(video_copy,min_percentile=threshold, max_percentile=100-threshold,selected_channels=self.channels_with_cytosol).remove_outliers() 
                    list_masks_complete_cells, list_masks_nuclei, list_masks_cytosol_no_nuclei, index_paired_masks, masks_cyto,masks_nuclei = function_to_find_masks (video_temp)
                    list_sotring_number_paired_masks.append(len(list_masks_cytosol_no_nuclei))
                array_number_paired_masks = np.asarray(list_sotring_number_paired_masks)
                selected_threshold = tested_thresholds[np.argmax(array_number_paired_masks)]
            else:
                selected_threshold = 0
            # Running the mask selection once a threshold is obtained
            video_copy = video_normalized.copy()
            video_temp = RemoveExtrema(video_copy,min_percentile=selected_threshold,max_percentile=100-selected_threshold,selected_channels=self.channels_with_cytosol).remove_outliers() 
            list_masks_complete_cells, list_masks_nuclei, list_masks_cytosol_no_nuclei, index_paired_masks, masks_cyto,masks_nuclei  = function_to_find_masks (video_temp)
        
        elif (self.optimization_segmentation_method == 'z_slice_segmentation') and (len(self.video.shape) > 3):
            # Optimization based on selecting a z-slice to find the maximum number of index_paired_masks. 
            number_z_slices = self.video.shape[0]
            list_idx = np.round(np.linspace(4, number_z_slices-4, self.NUMBER_OPTIMIZATION_VALUES), 0).astype(int)  
            # Optimization based on slice
            if not (self.channels_with_cytosol is None) and not(self.channels_with_nucleus is None):
                list_sotring_number_paired_masks = []
                for idx, idx_value in enumerate(list_idx):
                    #test_video_optimization = stack.gaussian_filter(self.video[idx_value,:,:,:],sigma=1)  
                    test_video_optimization = np.amax(self.video[idx_value-3:idx_value+3,:,:,:],axis=0)  
                    list_masks_complete_cells, list_masks_nuclei, list_masks_cytosol_no_nuclei, index_paired_masks, masks_cyto,masks_nuclei = function_to_find_masks (test_video_optimization)
                    metric = (len(list_masks_cytosol_no_nuclei) *  np.count_nonzero(np.asarray(list_masks_cytosol_no_nuclei) )  )
                    list_sotring_number_paired_masks.append(metric)
                array_number_paired_masks = np.asarray(list_sotring_number_paired_masks)
                selected_threshold = list_idx[np.argmax(array_number_paired_masks)]
            else:
                selected_threshold = list_idx[0]
            # Running the mask selection once a threshold is obtained
            test_video_optimization = np.amax(self.video[selected_threshold-3:selected_threshold+3,:,:,:],axis=0) 
            list_masks_complete_cells, list_masks_nuclei, list_masks_cytosol_no_nuclei, index_paired_masks, masks_cyto,masks_nuclei  = function_to_find_masks (test_video_optimization)
        
        elif (self.optimization_segmentation_method == 'gaussian_filter_segmentation') and (len(self.video.shape) > 3):
            # Optimization based on testing different sigmas in a gaussian filter to find the maximum number of index_paired_masks. 
            half_z_slices = self.video.shape[0]//2
            list_sigmas = np.round(np.linspace(0.5, 20, self.NUMBER_OPTIMIZATION_VALUES), 1) 
            # Optimization based on slice
            if not (self.channels_with_cytosol is None) and not(self.channels_with_nucleus is None):
                list_sotring_number_paired_masks = []
                for idx, sigma_value in enumerate(list_sigmas):
                    test_video_optimization = stack.gaussian_filter(self.video[half_z_slices,:,:,:],sigma=sigma_value)  
                    list_masks_complete_cells, list_masks_nuclei, list_masks_cytosol_no_nuclei, index_paired_masks, masks_cyto,masks_nuclei = function_to_find_masks (test_video_optimization)
                    list_sotring_number_paired_masks.append(len(list_masks_cytosol_no_nuclei))
                array_number_paired_masks = np.asarray(list_sotring_number_paired_masks)
                selected_threshold = list_sigmas[np.argmax(array_number_paired_masks)]
            else:
                selected_threshold = list_sigmas[0]
            # Running the mask selection once a threshold is obtained
            test_video_optimization = stack.gaussian_filter(self.video[half_z_slices,:,:,:],sigma=selected_threshold) 
            list_masks_complete_cells, list_masks_nuclei, list_masks_cytosol_no_nuclei, index_paired_masks, masks_cyto,masks_nuclei  = function_to_find_masks (test_video_optimization)
        else:
            # no optimization is applied if a 2D image is passed
            list_masks_complete_cells, list_masks_nuclei, list_masks_cytosol_no_nuclei, index_paired_masks, masks_cyto,masks_nuclei  = function_to_find_masks (video_normalized)

        # This functions makes zeros the border of the mask, it is used only for plotting.
        def remove_border(img,px_to_remove = 5):
            img[0:10, :] = 0;img[:, 0:px_to_remove] = 0;img[img.shape[0]-px_to_remove:img.shape[0]-1, :] = 0; img[:, img.shape[1]-px_to_remove: img.shape[1]-1 ] = 0#This line of code ensures that the corners are zeros.
            return img
        
        if len(index_paired_masks) != 0 and not(self.channels_with_cytosol is None) and not(self.channels_with_nucleus is None):
            if self.show_plot == 1:
                n_channels = np.amin([3, video_normalized.shape[2]])
                _, axes = plt.subplots(nrows = 1, ncols = 4, figsize = (15, 10))
                im = convert_to_int8(video_normalized[ :, :, 0:n_channels])  
                masks_plot_cyto= merge_masks (list_masks_complete_cells) 
                masks_plot_nuc = merge_masks (list_masks_nuclei)              
                axes[0].imshow(im)
                axes[0].set(title = 'All channels')
                axes[1].imshow(masks_plot_cyto)
                axes[1].set(title = 'Cytosol mask')
                axes[2].imshow(masks_plot_nuc)
                axes[2].set(title = 'Nuclei mask')
                axes[3].imshow(im)
                for i in range(0, len(index_paired_masks)):
                    # Removing the borders just for plotting
                    temp_nucleus_mask= remove_border(list_masks_nuclei[i])
                    temp_complete_mask = remove_border(list_masks_complete_cells[i])
                    contuour_n = find_contours(temp_nucleus_mask, 0.5)
                    contuour_c = find_contours(temp_complete_mask, 0.5)
                    axes[3].fill(contuour_n[0][:, 1], contuour_n[0][:, 0], facecolor = 'none', edgecolor = 'red', linewidth=2) # mask nucleus
                    axes[3].fill(contuour_c[0][:, 1], contuour_c[0][:, 0], facecolor = 'none', edgecolor = 'red', linewidth=2) # mask cytosol
                    axes[3].set(title = 'Paired masks')
                print(index_paired_masks.shape[0])
                if not(self.image_name is None):
                    plt.savefig(self.image_name,bbox_inches='tight')
                plt.show()
        else:
            if not(self.channels_with_cytosol is None) and (self.channels_with_nucleus is None):
                if self.show_plot == 1:
                    n_channels = np.amin([3, video_normalized.shape[2]])
                    _, axes = plt.subplots(nrows = 1, ncols = 2, figsize = (20, 10))
                    im = convert_to_int8(video_normalized[ :, :, 0:n_channels])
                    axes[0].imshow(im)
                    axes[0].set(title = 'All channels')
                    axes[1].imshow(masks_plot_cyto)
                    axes[1].set(title = 'Cytosol mask')
                    if not(self.image_name is None):
                        plt.savefig(self.image_name,bbox_inches='tight')
                    plt.show()
            if (self.channels_with_cytosol is None) and not(self.channels_with_nucleus is None):
                if self.show_plot == 1:
                    n_channels = np.amin([3, video_normalized.shape[2]])
                    _, axes = plt.subplots(nrows = 1, ncols = 2, figsize = (20, 10))
                    im = convert_to_int8(video_normalized[ :, :, 0:n_channels])
                    axes[0].imshow(im)
                    axes[0].set(title = 'All channels')
                    axes[1].imshow(masks_plot_nuc)
                    axes[1].set(title = 'Nuclei mask')
                    if not(self.image_name is None):
                        plt.savefig(self.image_name,bbox_inches='tight')
                    plt.show()
            print('No paired masks were detected for this image')

        if (self.channels_with_cytosol is None):
            index_paired_masks = np.linspace(0, len(list_masks_nuclei)-1, len(list_masks_nuclei), dtype='int32')

        if (self.channels_with_nucleus is None):
            index_paired_masks = np.linspace(0, len(list_masks_complete_cells)-1, len(list_masks_complete_cells), dtype='int32')
        
        # generating a single image with all the masks for cyto and nuclei 
        masks_cyto_single = merge_masks(list_masks_complete_cells)
        masks_nuclei_single = merge_masks(list_masks_nuclei)
        masks_cytosol_no_nuclei_single = merge_masks(list_masks_cytosol_no_nuclei)

        # return values
        return list_masks_complete_cells, list_masks_nuclei, list_masks_cytosol_no_nuclei, index_paired_masks, masks_cyto_single, masks_nuclei_single,masks_cytosol_no_nuclei_single


class BigFISH():
    '''
    This class is intended to detect spots in FISH images using Big-FISH Copyright © 2020, Arthur Imbert. The format of the image must be  [Z, Y, X, C].
    Parameters
    --  --  --  --  -- 
    The description of the parameters is taken from Big-FISH BSD 3-Clause License. Copyright © 2020, Arthur Imbert. 
    image : NumPy array
        Array of images with dimensions [Z, Y, X, C] .
    FISH_channel : int
        Specific channel with FISH spots that are used for the quantification
    voxel_size_z : int, optional
        Height of a voxel, along the z axis, in nanometers. The default is 300.
    voxel_size_yx : int, optional
        Size of a voxel on the yx plan in nanometers. The default is 150.
    psf_z : int, optional
        Theoretical size of the PSF emitted by a spot in the z plan, in nanometers. The default is 350.
    psf_yx : int, optional
        Theoretical size of the PSF emitted by a spot in the yx plan in nanometers.
    cluster_radius : int, optional
        Maximum distance between two samples for one to be considered as in the neighborhood of the other. Radius expressed in nanometer.
    minimum_spots_cluster : int, optional
        Number of spots in a neighborhood for a point to be considered as a core point (from which a cluster is expanded). This includes the point itself.
    show_plot : bool, optional
        If True shows a 2D maximum projection of the image and the detected spots. The default is False
    
    '''
    def __init__(self,image, FISH_channel , voxel_size_z = 300,voxel_size_yx = 103,psf_z = 350, psf_yx = 150, cluster_radius = 350,minimum_spots_cluster = 4,  show_plot =False,image_name=None):
        self.image = image
        self.FISH_channel = FISH_channel
        self.voxel_size_z = voxel_size_z
        self.voxel_size_yx = voxel_size_yx
        self.psf_z = psf_z
        self.psf_yx = psf_yx
        self.cluster_radius = cluster_radius
        self.minimum_spots_cluster = minimum_spots_cluster
        self.show_plot = show_plot
        self.image_name=image_name
    def detect(self):
        '''
        This method is intended to detect RNA spots in the cell and Transcription Sites (Clusters) using Big-FISH Copyright © 2020, Arthur Imbert.
        Returns
        --  --  -- -
        clusterDectionCSV : np.int64 Array with shape (nb_clusters, 5) or (nb_clusters, 4). 
            One coordinate per dimension for the clusters centroid (zyx or yx coordinates), the number of spots detected in the clusters and its index.
        spotDectionCSV :  np.int64 with shape (nb_spots, 4) or (nb_spots, 3).
            Coordinates of the detected spots . One coordinate per dimension (zyx or yx coordinates) plus the index of the cluster assigned to the spot. If no cluster was assigned, value is -1.
        '''
        rna=self.image[:,:,:,self.FISH_channel]
        # Calculating Sigma with  the parameters for the PSF.
        spot_radius_px = detection.get_object_radius_pixel(
            voxel_size_nm=(self.voxel_size_z, self.voxel_size_yx, self.voxel_size_yx), 
            object_radius_nm=(self.psf_z, self.psf_yx, self.psf_yx), ndim=3)
        sigma = spot_radius_px

        ## SPOT DETECTION
        try:
            #rna_filtered = stack.remove_background_gaussian(rna, sigma)
            rna_filtered = stack.log_filter(rna, sigma) # LoG filter
        except ValueError:
            print('Error during the log filter calculation, try using larger parameters values for the psf')
            #rna_filtered = stack.gaussian_filter(rna, sigma) # Gaussian filter
            rna_filtered = stack.remove_background_gaussian(rna, sigma)
        mask = detection.local_maximum_detection(rna_filtered, min_distance=sigma) # local maximum detection
        threshold = detection.automated_threshold_setting(rna_filtered, mask) # thresholding
        spots, _ = detection.spots_thresholding(rna_filtered, mask, threshold, remove_duplicate=True)
        
        # Decomposing dense regions
        spots_post_decomposition, _, _ = detection.decompose_dense(
            image=rna, spots=spots, 
            voxel_size = (self.voxel_size_z, self.voxel_size_yx, self.voxel_size_yx), 
            spot_radius = (self.psf_z, self.psf_yx, self.psf_yx),
            alpha=0.9,   # alpha impacts the number of spots per candidate region
            beta=1,      # beta impacts the number of candidate regions to decompose
            gamma=5)     # gamma the filtering step to denoise the image
        ### CLUSTER DETECTION
        
        spots_post_clustering, clusters = detection.detect_clusters(spots_post_decomposition, 
                                            voxel_size=(self.voxel_size_z, self.voxel_size_yx, self.voxel_size_yx),
                                             radius= self.cluster_radius, nb_min_spots = self.minimum_spots_cluster)
        # Saving results with new variable names
        spotDectionCSV = spots_post_clustering
        clusterDectionCSV = clusters
        #print(spots_post_decomposition.shape, clusters.shape)
        ## PLOTTING
        if self.show_plot == True:
            try:
                plot.plot_elbow(rna, voxel_size_z=self.voxel_size_z, voxel_size_yx = self.voxel_size_yx, psf_z = self.psf_z, psf_yx = self.psf_yx)
                plt.show()
            except:
                print('not showing elbow plot')
            #selected_slice = 5
            #values, counts = np.unique(spots_post_decomposition[:,0], return_counts=True)
            #ind = np.argmax(counts)
            #selected_slice = np.argmax(values[ind])
            #counts = np.bincount(spots_post_decomposition[:,0][spots_post_decomposition[:,0]>0])
            #counts = np.bincount(clusters[:,0][clusters[:,0]>0])
            #selected_slice = np.argmax(counts)
            #image_2D = stack.focus_projection(rna, proportion = 0.2, neighborhood_size = 7, method = 'max') # maximum projection 
            #image_2D = stack.maximum_projection(rna)
            #image_2D = stack.rescale(image_2D, channel_to_stretch = 0, stretching_percentile = 99)
            central_slice = rna.shape[0]//2
            #for i in range(central_slice-1, central_slice+2): # rna.shape[0]):
            #for i in range(0,    rna.shape[0]//2):
            for i in range(central_slice,central_slice+1):
                print('Z-Slice: ', str(i))
                image_2D = rna_filtered[i,:,:]
                if i > 1 and i<rna.shape[0]-1:
                    #clusters_to_plot = clusters[(clusters[:,0]>=i-1) & (clusters[:,0]<=i+2) ] 
                    clusters_to_plot = clusters[clusters[:,0]==i]
                    #spots_to_plot =  spots_post_decomposition [(spots_post_decomposition[:,0]>=i-1) & (spots_post_decomposition[:,0]<=i+1) ] 
                    spots_to_plot =  spots_post_decomposition [spots_post_decomposition[:,0]==i ]
                else:
                    clusters_to_plot = clusters[clusters[:,0]==i]
                    spots_to_plot =  spots_post_decomposition [spots_post_decomposition[:,0]==i ]
                #clusters_to_plot = clusters 
                if not(self.image_name is None) and (i==central_slice): # saving only the central slice
                    path_output= str(self.image_name) + '_ch_' + str(self.FISH_channel)
                else:
                    path_output = None 
                plot.plot_detection(image_2D, 
                                spots=[spots_to_plot, clusters_to_plot[:, :3]], 
                                shape=["circle", "polygon"], 
                                radius=[3, 6], 
                                color=["orangered", "blue"],
                                linewidth=[1, 1], 
                                fill=[False, False], 
                                framesize=(15, 10), 
                                contrast=True,
                                rescale=True,
                                path_output = path_output)
                plt.show()
                del spots_to_plot, clusters_to_plot
        return [spotDectionCSV, clusterDectionCSV]


class Intensity():
    '''
    This class is intended to calculate the average intensity in an spot and substract the intensity in background.
    
    Parameters
    --  --  --  --  -- 
    image : NumPy array
        Array of images with dimensions [Z, Y, X, C] . 
    dataframe : Pandas dataframe
            Pandas dataframe with the following columns. image_id, cell_id, spot_id, nucleus_y, nucleus_x, nuc_area_px, cyto_area_px, cell_area_px, z, y, x, is_nuc, is_cluster, cluster_size, spot_type, is_cell_fragmented.
    '''
    def __init__(self,image,dataframe,spot_size):
        self.dataframe = dataframe
        self.image = image
        self.spot_size = spot_size

    def get_intensity(self):
        '''
        This method extracts data from the class SpotDetection and return the data as a dataframe.
        Returns
        --  --  -- -
        dataframe : Pandas dataframe
            Pandas dataframe with the following columns. image_id, cell_id, spot_id, nucleus_y, nucleus_x, nuc_area_px, cyto_area_px, cell_area_px, z, y, x, is_nuc, is_cluster, cluster_size, spot_type, is_cell_fragmented.
        '''
        pass


class DataProcessing():
    '''
    This class is intended to extract data from the class SpotDetection and return the data as a dataframe. 
    
    Parameters
    --  --  --  --  -- 
    spotDectionCSV: np.int64 Array with shape (nb_clusters, 5) or (nb_clusters, 4). 
            One coordinate per dimension for the clusters centroid (zyx or yx coordinates), the number of spots detected in the clusters and its index.
    clusterDectionCSV : np.int64 with shape (nb_spots, 4) or (nb_spots, 3).
            Coordinates of the detected spots . One coordinate per dimension (zyx or yx coordinates) plus the index of the cluster assigned to the spot. If no cluster was assigned, value is -1.
    masks_complete_cells : List of NumPy arrays or a single NumPy array
            Masks for every cell detected in the image. The list contains the mask arrays consisting of one or multiple Numpy arrays with format [Y, X].
    masks_nuclei: List of NumPy arrays or a single NumPy array
            Masks for every cell detected in the image. The list contains the mask arrays consisting of one or multiple Numpy arrays with format [Y, X].
    masks_cytosol_no_nuclei : List of NumPy arrays or a single NumPy array
            Masks for every cell detected in the image. The list contains the mask arrays consisting of one or multiple Numpy arrays with format [Y, X].
    spot_type : int, optional
        integer indicates the type of spot if more than one channel are used for quantification. The default is zero.
    dataframe : Pandas dataframe or None.
        Pandas dataframe with the following columns. image_id, cell_id, spot_id, nucleus_y, nucleus_x, nuc_area_px, cyto_area_px, cell_area_px, z, y, x, is_nuc, is_cluster, cluster_size, spot_type, is_cell_fragmented. The default is None.
    reset_cell_counter : int or None
        Number of cells in channel. This number is used only to reset the counter of number of cells.
    image_counter : int, optional
        counter for the number of images in the folder. The default is zero.
    '''
    def __init__(self,spotDectionCSV, clusterDectionCSV,masks_complete_cells, masks_nuclei, masks_cytosol_no_nuclei,spot_type=0,dataframe =None,reset_cell_counter=False,image_counter=0):
        self.spotDectionCSV=spotDectionCSV 
        self.clusterDectionCSV=clusterDectionCSV
        self.masks_complete_cells=masks_complete_cells
        self.masks_nuclei=masks_nuclei
        self.masks_cytosol_no_nuclei=masks_cytosol_no_nuclei
        self.dataframe=dataframe
        self.spot_type = spot_type
        self.reset_cell_counter = reset_cell_counter
        self.image_counter = image_counter
    def get_dataframe(self):
        '''
        This method extracts data from the class SpotDetection and return the data as a dataframe.
        Returns
        --  --  -- -
        dataframe : Pandas dataframe
            Pandas dataframe with the following columns. image_id, cell_id, spot_id, nucleus_y, nucleus_x, nuc_area_px, cyto_area_px, cell_area_px, z, y, x, is_nuc, is_cluster, cluster_size, spot_type, is_cell_fragmented.
        '''
        def mask_selector(mask,calculate_centroid= True):
            #temp_mask = np.zeros_like(masks) # making a copy of the image
            #selected_mask = temp_mask + (masks==id) # Selecting a single mask and making this mask equal to one and the background equal to zero.
            mask_area = np.count_nonzero(mask)
            if calculate_centroid == True:
                centroid_y,centroid_x = ndimage.measurements.center_of_mass(mask)
            else:
                centroid_y,centroid_x = 0,0
            return  mask_area, centroid_y, centroid_x
        def data_to_df( df, spotDectionCSV, clusterDectionCSV, mask_nuc = None, mask_cytosol_only=None, nuc_area = 0, cyto_area =0, cell_area=0, centroid_y=0, centroid_x=0, image_counter=0, is_cell_in_border = 0, spot_type=0, cell_counter =0 ):
            # spotDectionCSV      nrna x  [Z,Y,X,idx_foci]
            # clusterDectionCSV   nc   x  [Z,Y,X,size,idx_foci]
            
            # Removing TS from the image and calculating RNA in nucleus
            spots_no_ts, _, ts = multistack.remove_transcription_site(spotDectionCSV, clusterDectionCSV, mask_nuc, ndim=3)
            #rna_out_ts      [Z,Y,X,idx_foci]         Coordinates of the detected RNAs with shape. One coordinate per dimension (zyx or yx coordinates) plus the index of the foci assigned to the RNA. If no foci was assigned, value is -1. RNAs from transcription sites are removed.
            #foci            [Z,Y,X,size, idx_foci]   One coordinate per dimension for the foci centroid (zyx or yx coordinates), the number of RNAs detected in the foci and its index.
            #ts              [Z,Y,X,size,idx_ts]      One coordinate per dimension for the transcription site centroid (zyx or yx coordinates), the number of RNAs detected in the transcription site and its index.
            spots_nuc, _ = multistack.identify_objects_in_region(mask_nuc, spots_no_ts, ndim=3)
            # Detecting spots in the nucleus
            spots_cytosol_only, _ = multistack.identify_objects_in_region(mask_cytosol_only, spotDectionCSV[:,:3], ndim=3)
            # coord_innp  Coordinates of the objects detected inside the region.
            # coord_outnp Coordinates of the objects detected outside the region.
            # ts                     n x [Z,Y,X,size,idx_ts]
            # spots_nuc              n x [Z,Y,X]
            # spots_cytosol_only     n x [Z,Y,X]
            number_columns = len(df. columns)
            num_ts = ts.shape[0]
            num_nuc = spots_nuc.shape[0]
            num_cyt = spots_cytosol_only.shape[0] 
            array_ts =                  np.zeros( ( num_ts,number_columns)  )
            array_spots_nuc =           np.zeros( ( num_nuc,number_columns) )
            array_spots_cytosol_only =  np.zeros( ( num_cyt  ,number_columns) )
            # Spot index 
            spot_idx_ts =  np.arange(0,                  num_ts                                                 ,1 )
            spot_idx_nuc = np.arange(num_ts,             num_ts + num_nuc                                       ,1 )
            spot_idx_cyt = np.arange(num_ts + num_nuc,   num_ts + num_nuc + num_cyt  ,1 )
            spot_idx = np.concatenate((spot_idx_ts,  spot_idx_nuc, spot_idx_cyt ))
            # Populating arrays
            array_ts[:,8:11] = ts[:,:3]         # populating coord 
            array_ts[:,11] = 1                  # is_nuc
            array_ts[:,12] = 1                  # is_cluster
            array_ts[:,13] =  ts[:,3]           # cluster_size
            array_ts[:,14] = spot_type          # spot_type
            array_ts[:,15] = is_cell_in_border  # is_cell_fragmented
            array_spots_nuc[:,8:11] = spots_nuc[:,:3]   # populating coord 
            array_spots_nuc[:,11] = 1                   # is_nuc
            array_spots_nuc[:,12] = 0                   # is_cluster
            array_spots_nuc[:,13] = 0                   # cluster_size
            array_spots_nuc[:,14] =  spot_type          # spot_type
            array_spots_nuc[:,15] =  is_cell_in_border  # is_cell_fragmented
            array_spots_cytosol_only[:,8:11] = spots_cytosol_only[:,:3]    # populating coord 
            array_spots_cytosol_only[:,11] = 0                             # is_nuc
            array_spots_cytosol_only[:,12] = 0                             # is_cluster
            array_spots_cytosol_only[:,13] =  0                            # cluster_size
            array_spots_cytosol_only[:,14] =  spot_type                    # spot_type
            array_spots_cytosol_only[:,15] =  is_cell_in_border            # is_cell_fragmented
            # concatenate array
            array_complete = np.vstack((array_ts, array_spots_nuc, array_spots_cytosol_only))
            # Saves a dataframe with zeros when no spots  are detected on the cell.
            if array_complete.size ==0:
                array_complete = np.zeros( ( 1,number_columns)  )
                # if NO spots are detected populate  with -1
                array_complete[:,2] = -1     # spot_id
                array_complete[:,8:11] = -1
            else:
                # if spots are detected populate  the reported  array
                array_complete[:,2] = spot_idx.T     # spot_id
            # populating  array with cell  information
            array_complete[:,0] = image_counter  # image_id
            array_complete[:,1] = cell_counter   # cell_id
            array_complete[:,3] = centroid_y     #'nuc_y_centoid'
            array_complete[:,4] = centroid_x     #'nuc_x_centoid'
            array_complete[:,5] = nuc_area       #'nuc_area_px'
            array_complete[:,6] = cyto_area      # cyto_area_px
            array_complete[:,7] = cell_area      #'cell_area_px'
            # df = pd.DataFrame( columns=['image_id', 'cell_id', 'spot_id','nucleus_y', 'nucleus_x','nuc_area_px','cyto_area_px', 'cell_area_px','z', 'y', 'x','is_nuc','is_cluster','cluster_size','spot_type','is_cell_fragmented'])
            df = df.append(pd.DataFrame(array_complete, columns=df.columns), ignore_index=True)
            new_dtypes = {'image_id':int, 'cell_id':int, 'spot_id':int,'is_nuc':int,'is_cluster':int,'nucleus_y':int, 'nucleus_x':int,'nuc_area_px':int,'cyto_area_px':int, 'cell_area_px':int,'x':int,'y':int,'z':int,'cluster_size':int,'spot_type':int,'is_cell_fragmented':int}
            df = df.astype(new_dtypes)
            return df
        # Initializing Dataframe
        if (not ( self.dataframe is None))   and  ( self.reset_cell_counter == False): # IF the dataframe exist and not reset for multi-channel fish is passed
            new_dataframe = self.dataframe
            counter_total_cells = np.amax( self.dataframe['cell_id'].values) +1
            #counter_image =  np.amax( self.dataframe['image_id'].values) +1
        elif (not ( self.dataframe is None)) and (self.reset_cell_counter == True):    # IF dataframe exist and reset is passed
            new_dataframe = self.dataframe
            counter_total_cells = np.amax( self.dataframe['cell_id'].values) - len(self.masks_nuclei) +1   # restarting the counter for the number of cells
        else: # IF the dataframe does not exist.
            new_dataframe = pd.DataFrame( columns=['image_id', 'cell_id', 'spot_id','nucleus_y', 'nucleus_x','nuc_area_px','cyto_area_px', 'cell_area_px','z', 'y', 'x','is_nuc','is_cluster','cluster_size','spot_type','is_cell_fragmented'])
            #counter_image = 0 
            counter_total_cells = 0
        # loop for each cell in image
        n_masks = len(self.masks_nuclei)
        for id_cell in range (0,n_masks): # iterating for each mask in a given cell. The mask has values from 0 for background, to int n, where n is the number of detected masks.
            nuc_area, nuc_centroid_y, nuc_centroid_x = mask_selector(self.masks_nuclei[id_cell], calculate_centroid=True)
            cyto_area, _ ,_                          = mask_selector(self.masks_cytosol_no_nuclei[id_cell],calculate_centroid=False)
            cell_area, _, _                          = mask_selector(self.masks_complete_cells[id_cell],calculate_centroid=False)
            tested_mask =  self.masks_nuclei[id_cell]
            is_cell_in_border =  np.any( np.concatenate( ( tested_mask[:,0],tested_mask[:,-1],tested_mask[0,:],tested_mask[-1,:] ) ) )   
            # Data extraction
            new_dataframe = data_to_df(new_dataframe, 
                                self.spotDectionCSV, 
                                self.clusterDectionCSV, 
                                mask_nuc = self.masks_nuclei[id_cell], 
                                mask_cytosol_only=self.masks_cytosol_no_nuclei[id_cell], 
                                nuc_area=nuc_area,
                                cyto_area=cyto_area, 
                                cell_area=cell_area, 
                                centroid_y = nuc_centroid_y, 
                                centroid_x = nuc_centroid_x,
                                image_counter=self.image_counter,
                                is_cell_in_border = is_cell_in_border,
                                spot_type = self.spot_type ,
                                cell_counter =counter_total_cells)
            counter_total_cells +=1
        return new_dataframe


class SpotDetection():
    '''
    This class is intended to detect spots in FISH images using Big-FISH Copyright © 2020, Arthur Imbert. The format of the image must be  [Z, Y, X, C].
    This class is intended to extract data from the class SpotDetection and return the data as a dataframe. 
    
    Parameters
    --  --  --  --  -- 
    The description of the parameters is taken from Big-FISH BSD 3-Clause License. Copyright © 2020, Arthur Imbert. 
    image : NumPy array
        Array of images with dimensions [Z, Y, X, C] .
    FISH_channels : int, or List
        List of channels with FISH spots that are used for the quantification
    voxel_size_z : int, optional
        Height of a voxel, along the z axis, in nanometers. The default is 300.
    voxel_size_yx : int, optional
        Size of a voxel on the yx plan in nanometers. The default is 150.
    psf_z : int, optional
        Theoretical size of the PSF emitted by a spot in the z plan, in nanometers. The default is 350.
    psf_yx : int, optional
        Theoretical size of the PSF emitted by a spot in the yx plan in nanometers.
    cluster_radius : int, optional
        Maximum distance between two samples for one to be considered as in the neighborhood of the other. Radius expressed in nanometer.
    minimum_spots_cluster : int, optional
        Number of spots in a neighborhood for a point to be considered as a core point (from which a cluster is expanded). This includes the point itself.
    masks_complete_cells : List of NumPy arrays or a single NumPy array
            Masks for every cell detected in the image. The list contains the mask arrays consisting of one or multiple Numpy arrays with format [Y, X].
    masks_nuclei: List of NumPy arrays or a single NumPy array
            Masks for every cell detected in the image. The list contains the mask arrays consisting of one or multiple Numpy arrays with format [Y, X].
    masks_cytosol_no_nuclei : List of NumPy arrays or a single NumPy array
            Masks for every cell detected in the image. The list contains the mask arrays consisting of one or multiple Numpy arrays with format [Y, X].
    dataframe : Pandas Dataframe 
        Pandas dataframe with the following columns. image_id, cell_id, spot_id, nucleus_y, nucleus_x, nuc_area_px, cyto_area_px, cell_area_px, z, y, x, is_nuc, is_cluster, cluster_size, spot_type, is_cell_fragmented. The default is None.
    image_counter : int, optional
        counter for the number of images in the folder. The default is zero.
    list_voxels : List of tupples or None
        list with a tuple with two elements (voxel_size_z,voxel_size_yx ) for each FISH channel.
    list_psfs : List of tuples or None
        list with a tuple with two elements (psf_z, psf_yx ) for each FISH channel.
    
    show_plot : bool, optional
        If True shows a 2D maximum projection of the image and the detected spots. The default is False
    '''
    def __init__(self,image,  FISH_channels , cluster_radius=350,minimum_spots_cluster=4, masks_complete_cells = None, masks_nuclei  = None, masks_cytosol_no_nuclei = None, dataframe=None,image_counter=0, list_voxels=[[500,200]], list_psfs=[[300,100]], show_plot=True,image_name=None):
        self.image = image
        self.masks_complete_cells=masks_complete_cells
        self.masks_nuclei=masks_nuclei
        self.masks_cytosol_no_nuclei=masks_cytosol_no_nuclei        
        self.FISH_channels = FISH_channels
        self.cluster_radius = cluster_radius
        self.minimum_spots_cluster = minimum_spots_cluster
        self.dataframe = dataframe
        self.image_counter = image_counter
        self.show_plot = show_plot
        if type(list_voxels[0]) != list:
            self.list_voxels = [list_voxels]
        else:
            self.list_voxels = list_voxels
        if type(list_psfs[0]) != list:
            self.list_psfs = [list_psfs]
        else:
            self.list_psfs = list_psfs
        # converting FISH channels to a list
        if not (type(FISH_channels) is list):
            self.list_FISH_channels = [FISH_channels]
        else:
            self.list_FISH_channels = FISH_channels
        self.image_name = image_name
    def get_dataframe(self):
        for i in range(0,len(self.list_FISH_channels)):
            print('Spot Detection for Channel :', str(self.list_FISH_channels[i]) )
            if (i ==0):
                dataframe_FISH = self.dataframe 
                reset_cell_counter = False
            voxel_size_z = self.list_voxels[i][0]
            voxel_size_yx = self.list_voxels[i][1]
            psf_z = self.list_psfs[i][0] 
            psf_yx = self.list_psfs[i][1]
            [spotDectionCSV, clusterDectionCSV] = BigFISH(self.image, self.list_FISH_channels[i], voxel_size_z = voxel_size_z,voxel_size_yx = voxel_size_yx, psf_z = psf_z, psf_yx = psf_yx, cluster_radius=self.cluster_radius,minimum_spots_cluster=self.minimum_spots_cluster, show_plot=self.show_plot,image_name=self.image_name).detect()
            dataframe_FISH = DataProcessing(spotDectionCSV, clusterDectionCSV, self.masks_complete_cells, self.masks_nuclei, self.masks_cytosol_no_nuclei, dataframe =dataframe_FISH,reset_cell_counter=reset_cell_counter,image_counter = self.image_counter ,spot_type=i).get_dataframe()
            # reset counter for image and cell number
            reset_cell_counter = True
        return dataframe_FISH
    
    

class Utilities ():
    '''
    Description for the class.
    
    Parameters
    --  --  --  --  -- 
    parameter: bool, optional
        parameter description. The default is True. 
    '''
    def __init__(self,argument):
        pass
    
    
class Metadata():
    '''
    This class is intended to generate a metadata file with information about used dependencies, user information, and parameters used.
    
    Parameters
    --  --  --  --  -- 
    parameter: bool, optional
        parameter description. The default is True. 
    '''
    def __init__(self,data_dir, channels_with_cytosol, channels_with_nucleus, channels_with_FISH,diamter_nucleus, diameter_cytosol, minimum_spots_cluster,list_voxels=None, list_psfs=None,file_name_str=None):
        self.list_images, self.path_files, self.list_files_names, self.number_images = ReadImages(data_dir).read()
        self.channels_with_cytosol = channels_with_cytosol
        self.channels_with_nucleus = channels_with_nucleus
        self.channels_with_FISH = channels_with_FISH
        self.diamter_nucleus = diamter_nucleus
        self.diameter_cytosol = diameter_cytosol
        self.list_voxels = list_voxels
        self.list_psfs = list_psfs
        self.file_name_str=file_name_str
        self.minimum_spots_cluster = minimum_spots_cluster
        if  (not str(data_dir.name)[0:5] ==  'temp_') and (self.file_name_str is None):
            self.filename = './metadata_'+ str(data_dir.name) +'.txt'
        elif not(self.file_name_str is None):
            self.filename = './metadata_'+ str(file_name_str) +'.txt'
        else:
            self.filename = './metadata_'+ str(data_dir.name[5:]) +'.txt'
        self.data_dir = data_dir
        
    def write_metadata(self):
      installed_modules = [str(module).replace(" ","==") for module in pkg_resources.working_set]
      important_modules = [ 'tqdm', 'torch','tifffile', 'setuptools', 'scipy', 'scikit-learn', 'scikit-image', 'PyYAML', 'pysmb', 'pyfiglet', 'pip', 'Pillow', 'pandas', 'opencv-python-headless', 'numpy', 'numba', 'natsort', 'mrc', 'matplotlib', 'llvmlite', 'jupyter-core', 'jupyter-client', 'joblib', 'ipython', 'ipython-genutils', 'ipykernel', 'cellpose', 'big-fish']
      
      def create_data_file(filename):
        if sys.platform == 'linux' or sys.platform == 'darwin':
          os.system('touch' + filename)
        elif sys.platform == 'win32':
          os.system('echo , > ' + filename)
          
      number_spaces_pound_sign = 75
      def write_data_in_file(filename):
          with open(filename, 'w') as fd:
              fd.write('#' * (number_spaces_pound_sign)) 
              fd.write('\nAUTHOR INFORMATION  ')
              fd.write('\n    Author: ' + getpass.getuser())
              fd.write('\n    Created at: ' + datetime.datetime.today().strftime('%d %b %Y'))
              fd.write('\n    Time: ' + str(datetime.datetime.now().hour) + ':' + str(datetime.datetime.now().minute) )
              fd.write('\n    Operative System: ' + sys.platform )
              fd.write('\n    Hostname: ' + socket.gethostname() + '\n')
              fd.write('#' * (number_spaces_pound_sign) ) 
              fd.write('\nPARAMETERS USED  ')
              fd.write('\n    channels_with_cytosol: ' + str(self.channels_with_cytosol) )
              fd.write('\n    channels_with_nucleus: ' + str(self.channels_with_nucleus) )
              fd.write('\n    channels_with_FISH: ' + str(self.channels_with_FISH) )
              fd.write('\n    diamter_nucleus: ' + str(self.diamter_nucleus) )
              fd.write('\n    diameter_cytosol: ' + str(self.diameter_cytosol) )
              fd.write('\n    FISH parameters')
              for k in range (0,len(self.channels_with_FISH)):
                fd.write('\n      For Channel ' + str(self.channels_with_FISH[k]) )
                fd.write('\n        voxel_size_z: ' + str(self.list_voxels[k][0]) )
                fd.write('\n        voxel_size_yx: ' + str(self.list_voxels[k][1]) )
                fd.write('\n        psf_z: ' + str(self.list_psfs[k][0]) )
                fd.write('\n        psf_yx: ' + str(self.list_psfs[k][1]) )
              fd.write('\n    minimum_spots_cluster: ' + str(self.minimum_spots_cluster) )
              fd.write('\n') 
              fd.write('#' * (number_spaces_pound_sign) ) 
              fd.write('\nFILES AND DIRECTORIES USED ')
              fd.write('\n    Directory path: ' + str(self.data_dir) )
              fd.write('\n    Folder name: ' + str(self.data_dir.name)  )
              # for loop for all the images.
              fd.write('\n    Images in directory :'  )
              for img_name in self.list_files_names:
                fd.write('\n        '+ img_name)
              fd.write('\n')  
              fd.write('#' * (number_spaces_pound_sign)) 
              fd.write('\nREPRODUCIBILITY ')
              fd.write('\n    Platform: \n')
              fd.write('        Python: ' + str(platform.python_version()) )
              fd.write('\n    Dependancies: ')
              # iterating for all modules
              for module_name in installed_modules:
                if any(module_name[0:4] in s for s in important_modules):
                  fd.write('\n        '+ module_name)
              fd.write('\n') 
              fd.write('#' * (number_spaces_pound_sign) ) 
      create_data_file(self.filename)
      write_data_in_file(self.filename)
    

class PlotImages():
    '''
    This class intended to plot all the channels from an image with format  [Z, Y, X, C].
    
    Parameters
    --  --  --  --  -- 
    image: NumPy array
        Array of images with dimensions [Z, Y, X, C].
    figsize : tuple with figure size, optional.
        Tuple with format (x_size, y_size). the default is (8.5, 5).
    '''
    def __init__(self,image,figsize=(8.5, 5),image_name='temp'):
        self.image = image
        self.figsize = figsize
        self.image_name = image_name
        
    def plot(self):
        '''
        This function plots all the channels for the original image.
        '''
        print(self.image.shape)
        number_channels = self.image.shape[3]
        fig, axes = plt.subplots(nrows=1, ncols=number_channels, figsize=self.figsize)
        rescaled_video = stack.rescale(self.image[:,:,:,:], channel_to_stretch=None, stretching_percentile=99)
        for i in range (0,number_channels ):
            #temp_img = RemoveExtrema(self.image[:,:,:,i],min_percentile=1, max_percentile=95).remove_outliers() 
            img_2D = stack.focus_projection(rescaled_video[3:-3,:,:,i], proportion=0.5, neighborhood_size=5, method='median') # maximum projection 
            #img_2D=difference_of_gaussians(img_2D,low_sigma=1, high_sigma=10)
            #img_2D = stack.remove_background_mean(img_2D, kernel_shape='disk', kernel_size=50)
            #img_2D = np.amax(temp_img,axis=0)
            img_2D = stack.gaussian_filter(img_2D,sigma=2)
            axes[i].imshow( img_2D ,cmap='viridis') 
            axes[i].set_title('Channel_'+str(i))
        plt.savefig(self.image_name,bbox_inches='tight')
        plt.show()
        return 

class ReportPDF():
    '''
    This class intended to create a PDF report including the images generated during the pipeline.
    
    Parameters
    --  --  --  --  -- 
    directory_results: str or PosixPath
        Directory containing the images to include in the report.
    substring_to_detect_in_file_name: str
        String with the prefix to detect in the files names. 
    file_name: str
        Name of the report. 
    folder_output: str or PosixPath
        Directory to place the report.

    '''    
    def __init__(self,directory, channels_with_FISH):
        self.directory = directory
        self.channels_with_FISH = channels_with_FISH
    
    def create_report(self):
        pdf = FPDF()
        WIDTH = 210
        HEIGHT = 297
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        # code that reads the main file names
        list_files_names =[]
        substring_to_detect_in_file_name = 'ori_'               # prefix 'ori_' means original image 
        ending_string = re.compile(substring_to_detect_in_file_name)  # for faster search in the file
        for _, _, files in os.walk(self.directory):
            for file in files:
                if ending_string.match(file) and file[0]!= '.': # detecting a match in the end, not consider hidden files starting with '.'
                    file_name = file.rpartition('.')[0]         # getting the file name and removing extention
                    list_files_names.append(file_name[4:])      # removing the prefix from the file name.
        list_files_names.sort()
        # Main loop that reads each image and makes the pdf
        for i,temp_file_name in enumerate(list_files_names):
            pdf.cell(w=0, h=10, txt='Original image: ' + temp_file_name,ln =2,align = 'L')
            # code that returns the path of the original image
            temp_original_img_name = pathlib.Path().absolute().joinpath( self.directory, 'ori_' + temp_file_name +'.png' )
            pdf.image(str(temp_original_img_name), x=0, y=20, w=WIDTH-25)
            # creating some space
            for text_idx in range(0, 12):
                pdf.cell(w=0, h=10, txt='',ln =1,align = 'L')
            pdf.cell(w=0, h=10, txt='Cell segmentation: ' + temp_file_name,ln =1,align = 'L')
            # code that returns the path of the segmented image
            temp_segmented_img_name = pathlib.Path().absolute().joinpath( self.directory, 'seg_' + temp_file_name +'.png' )
            pdf.image(str(temp_segmented_img_name), x=0, y=HEIGHT/2, w=WIDTH-25)
            pdf.add_page()
            for id_channel, channel in enumerate(self.channels_with_FISH):
                temp_seg_name = pathlib.Path().absolute().joinpath( self.directory, 'det_' + temp_file_name + '_ch_'+str(channel)+'.png' )
                if id_channel ==0: 
                    pdf.cell(w=0, h=10, txt='FISH Ch_ ' + str(channel) + ': '+ temp_file_name,ln =2,align = 'L') 
                    pdf.image(str(temp_seg_name), x=0, y=20, w=WIDTH-30)
                else: 
                    for j in range(0, 12):
                        pdf.cell(w=0, h=10, txt='',ln =1,align = 'L')
                    pdf.cell(w=0, h=10, txt='FISH Ch_ ' + str(channel) + ': '+ temp_file_name,ln =2,align = 'L')
                    pdf.image(str(temp_seg_name), x=0, y=HEIGHT/2, w=WIDTH-25)
                    pdf.add_page()
                if len(self.channels_with_FISH)==1:
                    pdf.add_page()
        pdf_name =  'pdf_report_' + self.directory.name[13:] + '.pdf'
        pdf.output(pdf_name, 'F')


class PipelineFISH():
    '''
    This class is intended to perform complete FISH analyses including cell segmentation and spot detection.
    
    Parameters
    --  --  --  --  -- 
    parameter: bool, optional
        parameter description. The default is True. 
        
    list_voxels : List of lists or None
        list with a tuple with two elements (voxel_size_z,voxel_size_yx ) for each FISH channel.
    list_psfs : List of lists or None
        list with a tuple with two elements (psf_z, psf_yx ) for each FISH channel.
    '''
    def __init__(self,data_dir, channels_with_cytosol=None, channels_with_nucleus=None, channels_with_FISH=None,diamter_nucleus=100, diameter_cytosol=200, minimum_spots_cluster=None,show_plot=True,list_voxels=[[500,200]], list_psfs=[[300,100]],file_name_str =None,optimization_segmentation_method='z_slice_segmentation'):
        self.list_images, self.path_files, self.list_files_names, self.number_images = ReadImages(data_dir).read()
        self.channels_with_cytosol = channels_with_cytosol
        self.channels_with_nucleus = channels_with_nucleus
        self.channels_with_FISH = channels_with_FISH
        self.diamter_nucleus = diamter_nucleus
        self.diameter_cytosol = diameter_cytosol
        self.optimization_segmentation_method = optimization_segmentation_method # optimization_segmentation_method = 'intensity_segmentation' 'z_slice_segmentation', 'gaussian_filter_segmentation' , None
        if type(list_voxels[0]) != list:
            self.list_voxels = [list_voxels]
        else:
            self.list_voxels = list_voxels
        if type(list_psfs[0]) != list:
            self.list_psfs = [list_psfs]
        else:
            self.list_psfs = list_psfs
        self.minimum_spots_cluster = minimum_spots_cluster
        self.show_plot = show_plot
        self.CLUSTER_RADIUS = 500
        self.data_dir = data_dir
        if not(file_name_str is None):
            self.name_for_files = file_name_str
        else:
            self.name_for_files = self.data_dir.name
        
    def run(self):
        # Printing banner
        #Banner(show=True).print_banner()
        # Prealocating arrays
        list_masks_complete_cells=[]
        list_masks_nuclei=[]
        list_masks_cytosol_no_nuclei=[]
        # temp_results_images
        temp_folder_name = str('temp_results_'+ self.name_for_files)
        if not os.path.exists(temp_folder_name):
            os.makedirs(temp_folder_name)
        
        # Running the pipeline.
        for i in range (0, self.number_images ):
            print( pyfiglet.figlet_format('IMAGE : '+ str(i) ) )
            if i ==0:
                dataframe = None
            print('ORIGINAL IMAGE')
            print(self.list_files_names[i])
            temp_file_name = self.list_files_names[i][:self.list_files_names[i].rfind('.')] # slcing the name of the file. Removing after finding '.' in the string.
            temp_original_img_name = pathlib.Path().absolute().joinpath( temp_folder_name, 'ori_' + temp_file_name +'.png' )
            PlotImages(self.list_images[i],figsize=(15, 10) ,image_name=  temp_original_img_name ).plot()
            print('CELL SEGMENTATION')
            temp_segmentation_img_name = pathlib.Path().absolute().joinpath( temp_folder_name, 'seg_' + temp_file_name +'.png' )
            masks_complete_cells, masks_nuclei, masks_cytosol_no_nuclei, index_paired_masks, masks_cyto_single, masks_nuclei_single,masks_cytosol_no_nuclei_single = CellSegmentation(self.list_images[i],self.channels_with_cytosol, self.channels_with_nucleus, diameter_cytosol = self.diameter_cytosol, diamter_nucleus=self.diamter_nucleus, show_plot=self.show_plot,optimization_segmentation_method = self.optimization_segmentation_method,image_name = temp_segmentation_img_name).calculate_masks() 
            print('SPOT DETECTION')
            temp_detection_img_name = pathlib.Path().absolute().joinpath( temp_folder_name, 'det_' + temp_file_name )
            dataframe_FISH = SpotDetection(self.list_images[i],self.channels_with_FISH,cluster_radius=self.CLUSTER_RADIUS,minimum_spots_cluster=self.minimum_spots_cluster,masks_complete_cells=masks_complete_cells, masks_nuclei=masks_nuclei, masks_cytosol_no_nuclei=masks_cytosol_no_nuclei, dataframe=dataframe,image_counter=i, list_voxels=self.list_voxels,list_psfs=self.list_psfs, show_plot=self.show_plot,image_name = temp_detection_img_name).get_dataframe()
            dataframe = dataframe_FISH
            list_masks_complete_cells.append(masks_cyto_single)
            list_masks_nuclei.append(masks_nuclei_single)
            list_masks_cytosol_no_nuclei.append(masks_cytosol_no_nuclei_single)
            del masks_complete_cells, masks_nuclei, masks_cytosol_no_nuclei, index_paired_masks, masks_cyto_single, masks_nuclei_single,masks_cytosol_no_nuclei_single
        
        # Creating the dataframe        
        if  not str(self.name_for_files)[0:5] ==  'temp_':
            dataframe.to_csv('dataframe_' + self.name_for_files +'.csv')
        else:
            dataframe.to_csv('dataframe_' + self.name_for_files[5:] +'.csv')
        
        # Creating the metadata
        Metadata(self.data_dir, self.channels_with_cytosol, self.channels_with_nucleus, self.channels_with_FISH,self.diamter_nucleus, self.diameter_cytosol, self.minimum_spots_cluster,list_voxels=self.list_voxels, list_psfs=self.list_psfs,file_name_str=self.name_for_files).write_metadata()
        
        # Creating a PDF report
        ReportPDF(directory=pathlib.Path().absolute().joinpath(temp_folder_name) , channels_with_FISH=self.channels_with_FISH).create_report()

        return dataframe, list_masks_complete_cells, list_masks_nuclei, list_masks_cytosol_no_nuclei



