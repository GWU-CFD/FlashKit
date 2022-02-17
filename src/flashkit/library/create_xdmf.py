"""Create an xdmf file associated with flash simulation HDF5 output."""

# type annotations
from __future__ import annotations
from typing import NamedTuple
from collections.abc import Sequence

# standard libraries
import sys
import os
from xml.etree import ElementTree
from xml.dom import minidom

# internal libraries
from ..core.parallel import squash
from ..core.progress import Bar
from ..core.tools import first_true
from ..support.types import TagAttr, TagAttrEx

# external libraries
import h5py # type: ignore

# define library (public) interface
__all__ = ['create_xdmf', ]

@squash
def create_xdmf(*, files: Sequence[int], basename: str, dest: str, source: str, 
                filename: str, plotname: str, gridname: str, context: Bar) -> None:
    """Create an xdmf file associated with flash simulation HDF5 output."""
    filenames = {'plot-source': source + '/' + basename + plotname,
                 'plot-dest': os.path.relpath(source, dest) + '/' + basename + plotname,
                 'grid-source': source + '/' + basename + gridname,
                 'grid-dest': os.path.relpath(source, dest) + '/' + basename + gridname,
                 'filename': dest + '/' + basename + filename}
    write_xdmf(author_xdmf(filenames, files, context), filenames['filename'], context)

class SimulationInfo(NamedTuple):
    time: float
    grid: str
    dims: int
    blocks: int
    types: list[int]
    sizes: dict[str, int]
    fields: list[str]
    velflds: list[str]

def author_xdmf(filenames: dict[str, str], filesteps: Sequence[int], context: Bar) -> ElementTree.Element:
    root = ElementTree.Element(*get_root_element())
    domain = ElementTree.SubElement(root, *get_domain_element())

    collection = ElementTree.SubElement(domain, *get_temporal_collection())
    with context(len(filesteps)) as progress:
        for step, number in enumerate(filesteps):
            plotsource = filenames['plot-source'] + f'{number:04}'
            plotdest = filenames['plot-dest'] + f'{number:04}'
            info = get_simulation_info(plotsource)
            gridsource = filenames['grid-source'] + (f'{number:04}' if info.grid == 'pm' else '0000')
            griddest = filenames['grid-dest'] + (f'{number:04}' if info.grid == 'pm' else '0000')
            simulation = ElementTree.SubElement(collection, *get_spatial_collection(step))
            temporal = ElementTree.SubElement(simulation, *get_time_element(info.time))

            leaves = [block for block, ntype in enumerate(info.types) if ntype == 1] 
            for block in leaves:
                grid = ElementTree.SubElement(simulation, *get_grid_element(block))
                topology = ElementTree.SubElement(grid, *get_topology_element(info.sizes))

                geometry = ElementTree.SubElement(grid, *get_geometry_element())
                for axis in ('x', 'y', 'z'):
                    hyperslab = ElementTree.SubElement(geometry, *get_geometry_hyperslab_header(info.sizes, axis))
                    tag, attribute, text = get_geometry_hyperslab_slab(info.sizes, axis, block)
                    ElementTree.SubElement(hyperslab, tag, attribute).text = text
                    tag, attribute, text = get_geometry_hyperslab_data(info.sizes, info.blocks, axis, griddest)
                    ElementTree.SubElement(hyperslab, tag, attribute).text = text

                for field in info.fields:
                    attr_base = ElementTree.SubElement(grid, *get_attribute_element(field))
                    hyperslab = ElementTree.SubElement(attr_base, *get_attribute_hyperslab_header(info.sizes))
                    tag, attribute, text = get_attribute_hyperslab_slab(info.sizes, block)
                    ElementTree.SubElement(hyperslab, tag, attribute).text = text
                    tag, attribute, text = get_attribute_hyperslab_data(info.sizes, info.blocks, field, plotdest)
                    ElementTree.SubElement(hyperslab, tag, attribute).text = text

                if len(info.velflds):
                    attr_base = ElementTree.SubElement(grid, *get_attribute_element('velc', 'Vector'))
                    func_join = ElementTree.SubElement(attr_base, *get_attribute_join_header(info.sizes, info.dims))
                for field in info.velflds:
                    hyperslab = ElementTree.SubElement(func_join, *get_attribute_hyperslab_header(info.sizes))
                    tag, attribute, text = get_attribute_hyperslab_slab(info.sizes, block)
                    ElementTree.SubElement(hyperslab, tag, attribute).text = text
                    tag, attribute, text = get_attribute_hyperslab_data(info.sizes, info.blocks, field, plotdest)
                    ElementTree.SubElement(hyperslab, tag, attribute).text = text
            progress()
    return root

def get_simulation_info(filename: str) -> SimulationInfo:
    with h5py.File(filename, 'r') as file:
        int_scalars = list(file['integer scalars'])
        real_scalars = list(file['real scalars'])
        node_type = list(file['node type'])
        unknown_names = list(file['unknown names'][:, 0])
        velocity_names = [name for name in ('cc_u', 'cc_v', 'cc_w') if name in file.keys()]
        setup_call = str(file['sim info'][0][1])

    sim_time = float(first_true(real_scalars, lambda l: 'time' in str(l[0]))[1])
    blk_num = first_true(int_scalars, lambda l: 'globalnumblocks' in str(l[0]))[1]
    blk_sizes = {i: first_true(int_scalars, lambda l: 'n' + i + 'b' in str(l[0]))[1] for i in ('x', 'y', 'z')}
    dimension = first_true(int_scalars, lambda l: 'dimensionality' in str(l[0]))[1]
    fields = [k.decode('utf-8') for k in unknown_names]
    grid = [grid[1:] for grid in {'+am', '+pm', '+ug', '+rg'} if grid in setup_call][0]
    return SimulationInfo(sim_time, grid, dimension, blk_num, node_type, blk_sizes, fields, velocity_names)

def get_comment_element() -> str:
    return 'DOCTYPE Xdmf SYSTEM "Xdmf.dtd" []'

def get_root_element() -> TagAttr:
    return ('Xdmf', {'xmlns:xi': 'http://www.w3.org/2003/XInclude', 'version': '2.2'})

def get_domain_element() -> TagAttr:
    return ('Domain', {})

def get_temporal_collection() -> TagAttr:
    return ('Grid', {'Name': 'Time_Series', 'GridType': 'Collection', 'CollectionType': 'Temporal'})

def get_spatial_collection(step: int) -> TagAttr:
    return ('Grid', {'Name': f'Step_{step:04}', 'GridType': 'Collection', 'CollectionType': 'Spatial'})

def get_grid_element(block: int) -> TagAttr:
    return ('Grid', {'Name': str(block), 'GridType': 'Uniform'})

def get_time_element(time: float) -> TagAttr:
    return ('Time', {'Value': f'{time}'})

def get_topology_element(sizes: dict[str, int]) -> TagAttr:
    vector = [sizes[axis] for axis in ('z', 'y', 'x')]
    dimensions = ' '.join([str(size + 1) for size in vector])
    return ('Topology', {'Type': '3DRectMesh', 'NumberOfElements': dimensions})

def get_geometry_element() -> TagAttr:
    return ('Geometry', {'Type': 'VXVYVZ'})

def get_geometry_hyperslab_header(sizes: dict[str, int], axis: str) -> TagAttr:
    dimensions = str(sizes[axis] + 1)
    return ('DataItem', {'ItemType': 'HyperSlab', 'Dimensions': dimensions, 'Type': 'HyperSlab'})

def get_geometry_hyperslab_slab(sizes: dict[str, int], axis: str, block: int) -> TagAttrEx:
    size = sizes[axis] + 1
    dimensions = ' '.join(map(str, [block, 0, 1, 1, 1, size]))
    return ('DataItem', {'Dimensions': '3 2', 'NumberType': 'Int', 'Format': 'XML'}, dimensions)

def get_geometry_hyperslab_data(sizes: dict[str, int], blocks: int, axis: str, filename: str) -> TagAttrEx:
    size = sizes[axis] + 1
    dimensions = ' '.join(map(str, [blocks, size]))
    filename = filename + ':/' + {'x': 'xxxf', 'y': 'yyyf', 'z': 'zzzf'}[axis]
    return ('DataItem', {'Format': 'HDF', 'Dimensions': dimensions, 'Name': axis,
                         'NumberType': 'Float', 'Precision': '4'}, filename)

def get_attribute_element(field: str, rank: str='Scalar', center: str='Cell') -> TagAttr:
    return ('Attribute', {'Name': field, 'AttributeType': rank, 'Center': center})

def get_attribute_join_header(sizes: dict[str, int], length: int) -> TagAttr:
    vector = [sizes[axis] for axis in ('z', 'y', 'x')] + [length, ]
    function = ''.join(('join(', ', '.join((f'${i}' for i in range(length))), ')')) 
    dimensions = ' '.join([str(size) for size in vector])
    return ('DataItem', {'ItemType': 'Function', 'Function': function, 'Dimensions': dimensions})

def get_attribute_hyperslab_header(sizes: dict[str, int]) -> TagAttr:
    vector = [sizes[axis] for axis in ('z', 'y', 'x')]
    dimensions = ' '.join([str(size) for size in vector])
    return ('DataItem', {'ItemType': 'HyperSlab', 'Dimensions': dimensions, 'Type': 'HyperSlab'})

def get_attribute_hyperslab_slab(sizes: dict[str, int], block: int) -> TagAttrEx:
    vector = [sizes[axis] for axis in ('z', 'y', 'x')]
    dimensions = ' '.join(map(str, [block, 0, 0, 0, 1, 1, 1, 1, 1] + vector))
    return ('DataItem', {'Dimensions': '3 4', 'NumberType': 'Int', 'Format': 'XML'}, dimensions)

def get_attribute_hyperslab_data(sizes: dict[str, int], blocks: int, field: str, filename: str) -> TagAttrEx:
    vector = [sizes[axis] for axis in ('z', 'y', 'x')]
    dimensions = ' '.join(map(str, [blocks, ] + vector))
    filename = filename + ':/' + field
    return ('DataItem', {'Format': 'HDF', 'Dimensions': dimensions, 'Name': field,
                         'NumberType': 'Float', 'Precision': '4'}, filename)

def write_xdmf(root: ElementTree.Element, filename: str, context: Bar) -> None:
    with open(filename + '.xmf', 'wb') as file, context() as progress:
        file.write('<?xml version="1.0" ?>\n<!DOCTYPE Xdmf SYSTEM "Xdmf.dtd" []>\n'.encode('utf-8'))
        file.write(minidom.parseString(ElementTree.tostring(root, short_empty_elements=False)
                                      ).toprettyxml(indent="    ").replace('<?xml version="1.0" ?>\n', '').encode('utf-8'))
