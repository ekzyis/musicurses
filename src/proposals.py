import os
from filetypes import Filetype
import re

class Proposal:
    def __init__(self, fname, ftype, path):
        self.__name = fname # filename
        self.__type = ftype # file type
        self.__path = path # full path to file

    def name(self):
        return self.__name

    def type(self):
        return self.__type

    def path(self):
        return self.__path

def loadProposals(path, pattern):
    name_list = [f for f in os.listdir(path) \
        if re.match(r'{}'.format(pattern), f, re.IGNORECASE)]
    type_list = [filetype(path + '/' + f) for f in name_list]
    return [Proposal(fname,ftype,path+'/'+fname) \
        for (fname, ftype) in zip(name_list,type_list) if ftype != Filetype.OTHER]

def filetype(fpath):
    if(os.path.isdir(fpath)): return Filetype.DIRECTORY
    ext = os.path.splitext(fpath)[1]
    #pathLogger.debug(ext)
    if(ext in [".flac", ".mp3"]): return Filetype.AUDIO
    if(ext in [".pls"]): return Filetype.PLAYLIST
    else: return Filetype.OTHER
