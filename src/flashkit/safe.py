"""Safe versions (no exception) of flashkit api"""

# standard libraries
from .core.error import error
from . import api as flash

flash.create.block = error('Unable to create block file!')(flash.create.block)
flash.create.grid = error('Unable to create grid file!')(flash.create.grid)
flash.create.interp = error('Unable to block par file!')(flash.create.interp)
flash.create.par = error('Unable to create par file!')(flash.create.par)
flash.create.xdmf = error('Unable to create xdmf file!')(flash.create.xdmf)
