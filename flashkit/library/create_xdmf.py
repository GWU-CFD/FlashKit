"""Create an xdmf file associated with flash simulation HDF5 output."""

# type annotations
from __future__ import annotations
from typing import Tuple, List, Set, Dict, Iterable, Callable, NamedTuple

# standard libraries
import sys
import os
from xml.etree import ElementTree
from xml.dom import minidom
from contextlib import nullcontext

# internal libraries
from ..resources import DEFAULTS 

# external libraries
import h5py

# define public interface
__all__ = ['file', ]

# define default constants
LOW: int = DEFAULTS['create']['xdmf']['low']
HIGH: int = DEFAULTS['create']['xdmf']['high']
SKIP: int = DEFAULTS['create']['xdmf']['skip']
PATH: str = DEFAULTS['general']['paths']['working']
OUT: str = DEFAULTS['general']['files']['output']
PLOT: str = DEFAULTS['general']['files']['plot']
GRID: str = DEFAULTS['general']['files']['grid']
CONTEXT: Callable[[int], Callable[[], None]] = lambda *_: nullcontext(lambda *_: None) 

# internal library (public) function 
def file(*, files: Iterable[int], basename: str, path: str, filename: str, plotname: str, gridname: str,
         context: Callable[[int], Callable[[], None]] = CONTEXT) -> None:
    """ Method for creating an xmdf specification for reading simulation hdf5 output """
    filenames = {name: os.getcwd() + '/' + path + basename + footer 
                 for name, footer in zip(('plot', 'grid', 'xmf'), 
                                         (plotname, gridname, filename))}
    _write_xmf(_create_xmf(filenames, files, context), filenames['xmf'], context)

class _SimulationInfo(NamedTuple):
    "Necessary information to extract from a plot or checkpoint file"
    time: float
    grid: str
    dims: int
    blocks: int
    types: List[int]
    sizes: Dict[str, int]
    fields: Set[str]
    velflds: List[str]

def _first_true(iterable, predictor):
    return next(filter(predictor, iterable))

def _create_xmf(filenames: Dict[str, str], filesteps: List[int], context: Callable[[int], Callable[[], None]]) -> ElementTree.Element:
    root = ElementTree.Element(*_get_root_element())
    domain = ElementTree.SubElement(root, *_get_domain_element())

    collection = ElementTree.SubElement(domain, *_get_temporal_collection())
    with context(len(filesteps)) as progress:
        for step, number in enumerate(filesteps):
            plotname = filenames['plot'] + f'{number:04}'
            info = _get_simulation_info(plotname)
            gridname = filenames['grid'] + (f'{number:04}' if info.grid == 'pm' else '0000')
            simulation = ElementTree.SubElement(collection, *_get_spatial_collection(step))
            temporal = ElementTree.SubElement(simulation, *_get_time_element(info.time))

            leaves = [block for block, ntype in enumerate(info.types) if ntype == 1] 
            for block in leaves:
                grid = ElementTree.SubElement(simulation, *_get_grid_element(block))
                topology = ElementTree.SubElement(grid, *_get_topology_element(info.sizes))

                geometry = ElementTree.SubElement(grid, *_get_geometry_element())
                for axis in ('x', 'y', 'z'):
                    hyperslab = ElementTree.SubElement(geometry, *_get_geometry_hyperslab_header(info.sizes, axis))
                    tag, attribute, text = _get_geometry_hyperslab_slab(info.sizes, axis, block)
                    ElementTree.SubElement(hyperslab, tag, attribute).text = text
                    tag, attribute, text = _get_geometry_hyperslab_data(info.sizes, info.blocks, axis, gridname)
                    ElementTree.SubElement(hyperslab, tag, attribute).text = text

                for field in info.fields:
                    attribute = ElementTree.SubElement(grid, *_get_attribute_element(field))
                    hyperslab = ElementTree.SubElement(attribute, *_get_attribute_hyperslab_header(info.sizes))
                    tag, attr, text = _get_attribute_hyperslab_slab(info.sizes, block)
                    ElementTree.SubElement(hyperslab, tag, attr).text = text
                    tag, attr, text = _get_attribute_hyperslab_data(info.sizes, info.blocks, field, plotname)
                    ElementTree.SubElement(hyperslab, tag, attr).text = text

                if len(info.velflds):
                    attribute = ElementTree.SubElement(grid, *_get_attribute_element('velc', 'Vector'))
                    func_join = ElementTree.SubElement(attribute, *_get_attribute_join_header(info.sizes, info.dims))
                for field in info.velflds:
                    hyperslab = ElementTree.SubElement(func_join, *_get_attribute_hyperslab_header(info.sizes))
                    tag, attr, text = _get_attribute_hyperslab_slab(info.sizes, block)
                    ElementTree.SubElement(hyperslab, tag, attr).text = text
                    tag, attr, text = _get_attribute_hyperslab_data(info.sizes, info.blocks, field, plotname)
                    ElementTree.SubElement(hyperslab, tag, attr).text = text
            progress()
    return root

def _write_xmf(root: ElementTree.Element, filename: str, context: Callable[[int], Callable[[], None]]) -> None:
    with open(filename + '.xmf', 'wb') as file, context() as progress:
        file.write('<?xml version="1.0" ?>\n<!DOCTYPE Xdmf SYSTEM "Xdmf.dtd" []>\n'.encode('utf-8'))
        file.write(minidom.parseString(ElementTree.tostring(root, short_empty_elements=False)
                                      ).toprettyxml(indent="    ").replace('<?xml version="1.0" ?>\n', '').encode('utf-8'))

def _get_simulation_info(filename: str) -> _SimulationInfo:
    with h5py.File(filename, 'r') as file:
        int_scalars = list(file['integer scalars'])
        real_scalars = list(file['real scalars'])
        node_type = list(file['node type'])
        unknown_names = list(file['unknown names'][:, 0])
        velocity_names = [name for name in ('cc_u', 'cc_v', 'cc_w') if name in file.keys()]
        setup_call = str(file['sim info'][0][1])

    sim_time = float(_first_true(real_scalars, lambda l: 'time' in str(l[0]))[1])
    blk_num = _first_true(int_scalars, lambda l: 'globalnumblocks' in str(l[0]))[1]
    blk_sizes = {i: _first_true(int_scalars, lambda l: 'n' + i + 'b' in str(l[0]))[1] for i in ('x', 'y', 'z')}
    dimension = _first_true(int_scalars, lambda l: 'dimensionality' in str(l[0]))[1]
    fields = {k.decode('utf-8') for k in unknown_names}
    grid = [grid[1:] for grid in {'+pm', '+ug', '+rg'} if grid in setup_call][0]
    return _SimulationInfo(sim_time, grid, dimension, blk_num, node_type, blk_sizes, fields, velocity_names)

def _get_comment_element() -> str:
    return 'DOCTYPE Xdmf SYSTEM "Xdmf.dtd" []'

def _get_root_element() -> Tuple[str, Dict[str, str]]:
    return ('Xdmf', {'xmlns:xi': 'http://www.w3.org/2003/XInclude', 'version': '2.2'})

def _get_domain_element() -> Tuple[str, Dict[str, str]]:
    return ('Domain', {})

def _get_temporal_collection() -> Tuple[str, Dict[str, str]]:
    return ('Grid', {'Name': 'Time_Series', 'GridType': 'Collection', 'CollectionType': 'Temporal'})

def _get_spatial_collection(step: int) -> Tuple[str, Dict[str, str]]:
    return ('Grid', {'Name': f'Step_{step:04}', 'GridType': 'Collection', 'CollectionType': 'Spatial'})

def _get_grid_element(block: int) -> Tuple[str, Dict[str, str]]:
    return ('Grid', {'Name': str(block), 'GridType': 'Uniform'})

def _get_time_element(time: int) -> Tuple[str, Dict[str, str]]:
    return ('Time', {'Value': f'{time}'})

def _get_topology_element(sizes: Dict[str, int]) -> Tuple[str, Dict[str, str]]:
    sizes = [sizes[axis] for axis in ('z', 'y', 'x')]
    dimensions = ' '.join([str(size + 1) for size in sizes])
    return ('Topology', {'Type': '3DRectMesh', 'NumberOfElements': dimensions})

def _get_geometry_element() -> Tuple[str, Dict[str, str]]:
    return ('Geometry', {'Type': 'VXVYVZ'})

def _get_geometry_hyperslab_header(sizes: Dict[str, int], axis: str) -> Tuple[str, Dict[str, str]]:
    dimensions = str(sizes[axis] + 1)
    return ('DataItem', {'ItemType': 'HyperSlab', 'Dimensions': dimensions, 'Type': 'HyperSlab'})

def _get_geometry_hyperslab_slab(sizes: Dict[str, int], axis: str, block: int) -> Tuple[str, Dict[str, str], str]:
    size = sizes[axis] + 1
    dimensions = ' '.join(map(str, [block, 0, 1, 1, 1, size]))
    return ('DataItem', {'Dimensions': '3 2', 'NumberType': 'Int', 'Format': 'XML'}, dimensions)

def _get_geometry_hyperslab_data(sizes: Dict[str, int], blocks: int, axis: str, filename: str) -> Tuple[str, Dict[str, str], str]:
    size = sizes[axis] + 1
    dimensions = ' '.join(map(str, [blocks, size]))
    filename = filename + ':/' + {'x': 'xxxf', 'y': 'yyyf', 'z': 'zzzf'}[axis]
    return ('DataItem', {'Format': 'HDF', 'Dimensions': dimensions, 'Name': axis,
                         'NumberType': 'Float', 'Precision': '4'}, filename)

def _get_attribute_element(field: str, rank: str='Scalar', center: str='Cell') -> Tuple[str, Dict[str, str]]:
    return ('Attribute', {'Name': field, 'AttributeType': rank, 'Center': center})

def _get_attribute_join_header(sizes: Dict[str, int], length: int) -> Tuple[str, Dict[str, str]]:
    sizes = [sizes[axis] for axis in ('z', 'y', 'x')] + [length, ]
    function = ''.join(('join(', ', '.join((f'${i}' for i in range(length))), ')')) 
    dimensions = ' '.join([str(size) for size in sizes])
    return ('DataItem', {'ItemType': 'Function', 'Function': function, 'Dimensions': dimensions})

def _get_attribute_hyperslab_header(sizes: Dict[str, int]) -> Tuple[str, Dict[str, str]]:
    sizes = [sizes[axis] for axis in ('z', 'y', 'x')]
    dimensions = ' '.join([str(size) for size in sizes])
    return ('DataItem', {'ItemType': 'HyperSlab', 'Dimensions': dimensions, 'Type': 'HyperSlab'})

def _get_attribute_hyperslab_slab(sizes: Dict[str, int], block: int) -> Tuple[str, Dict[str, str], str]:
    sizes = [sizes[axis] for axis in ('z', 'y', 'x')]
    dimensions = ' '.join(map(str, [block, 0, 0, 0, 1, 1, 1, 1, 1] + sizes))
    return ('DataItem', {'Dimensions': '3 4', 'NumberType': 'Int', 'Format': 'XML'}, dimensions)

def _get_attribute_hyperslab_data(sizes: Dict[str, int], blocks: int, field: str, filename: str) -> Tuple[str, Dict[str, str], str]:
    sizes = [sizes[axis] for axis in ('z', 'y', 'x')]
    dimensions = ' '.join(map(str, [blocks, ] + sizes))
    filename = filename + ':/' + field
    return ('DataItem', {'Format': 'HDF', 'Dimensions': dimensions, 'Name': field,
                         'NumberType': 'Float', 'Precision': '4'}, filename)