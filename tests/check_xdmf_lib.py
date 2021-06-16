"""Testing the library implementation of xdmf."""

# type annotations
from __future__ import annotations
from typing import NamedTuple

# standard libraries
import os
import re
from pathlib import Path
from xml.etree import ElementTree

# exernal libraries
import pytest

# internal libraries
from .support import change_directory

# precompiled regular expression constants
RE_STEPS = re.compile(r'^Step_[0-9]{4,4}$')
RE_JOINS = re.compile(r'^join\((\$[0-9], ){1,2}\$[0-9]\)$')
RE_FLOAT = re.compile(r'^[0-9]*\.[0-9]*$')
RE_INT_1 = re.compile(r'^[0-9]*$')
RE_INT_2 = re.compile(r'^[0-9]* [0-9]*$')
RE_INT_3 = re.compile(r'^([0-9]* ){2,2}[0-9]*$')
RE_INT_4 = re.compile(r'^([0-9]* ){3,3}[0-9]*$')
RE_INT_6 = re.compile(r'^([0-9]* ){5,5}[0-9]*$')
RE_INT_12 = re.compile(r'^([0-9]* ){11,11}[0-9]*$')

class Case(NamedTuple):
    """Useful tuple of test cases definition."""
    folder: str
    options: str
    output: str

@pytest.fixture(params=[
    Case('test/lidcavity/pm', '--auto', 'INS_LidDr_Cavity.xmf'),
    Case('test/lidcavity/ug', '--auto', 'INS_LidDr_Cavity.xmf'),
    ], ids=['lidcavity/pm', 'lidcavity/ug'])
def data(request, example, loaded):
    """Parameterized setup for xdmf feature tests."""
    case = request.param
    working = example.joinpath(case.folder)
    with change_directory(working):
        os.system('flashkit create xdmf --ignore ' + case.options)
    return case

@pytest.mark.lib
def check_xdmf(example, data):
    """Verify that the output matches the intent."""
    working = example.joinpath(data.folder)
    with change_directory(working):
        tree = ElementTree.parse(data.output)
        root = tree.getroot()[0]
        time_series = root[0]

        for step in time_series:
            assert step.tag == 'Grid'
            assert RE_STEPS.match(step.attrib['Name'])
            assert step.attrib['GridType'] == 'Collection' 
            assert step.attrib['CollectionType'] == 'Spatial'

            time, *blocks = step

            assert time.tag == 'Time'
            assert RE_FLOAT.match(time.attrib['Value'])
            
            for block in blocks:
                assert block.tag == 'Grid'
                assert RE_INT_1.match(block.attrib['Name'])
                assert block.attrib['GridType'] == 'Uniform'

                topology, geometry, *fields = block

                assert topology.tag == 'Topology'
                assert topology.attrib['Type'] == '3DRectMesh'
                assert RE_INT_3.match(topology.attrib['NumberOfElements'])
                
                assert geometry.tag == 'Geometry'
                assert geometry.attrib['Type'] == 'VXVYVZ'
                for axis in geometry:
                    assert axis.tag == 'DataItem'
                    assert axis.attrib['ItemType'] == 'HyperSlab'
                    assert RE_INT_1.match(axis.attrib['Dimensions'])
                    assert axis.attrib['Type'] == 'HyperSlab'

                    info, link = axis

                    assert info.tag == 'DataItem'
                    assert info.attrib['Dimensions'] == '3 2'
                    assert info.attrib['NumberType'] == 'Int'
                    assert info.attrib['Format'] == 'XML'
                    assert RE_INT_6.match(info.text)
                
                    assert link.tag == 'DataItem'
                    assert link.attrib['Format'] == 'HDF'
                    RE_INT_2.match(link.attrib['Dimensions'])
                    assert link.attrib['Name'] in 'xyz'
                    assert link.attrib['NumberType'] == 'Float'
                    assert link.attrib['Precision'] == '4'
                    assert link.text
                
                for field in fields:
                    assert field.tag == 'Attribute'
                    assert field.attrib['AttributeType'] in {'Scalar', 'Vector'}
                    assert field.attrib['Center'] == 'Cell'

                    for item in field:
                        assert item.tag == 'DataItem'
                        if item.attrib['ItemType'] == 'Function':
                            RE_JOINS.match(item.attrib['Function'])
                            RE_INT_4.match(item.attrib['Dimensions'])
                            item, *_ = item
                        
                        assert item.attrib['ItemType'] == 'HyperSlab'
                        RE_INT_3.match(item.attrib['Dimensions'])
                        assert item.attrib['Type'] == 'HyperSlab'
                        
                        info, link = item

                        assert info.tag == 'DataItem'
                        assert info.attrib['Dimensions'] == '3 4'
                        assert info.attrib['NumberType'] == 'Int'
                        assert info.attrib['Format'] == 'XML'
                        assert RE_INT_12.match(info.text)
                
                        assert link.tag == 'DataItem'
                        assert link.attrib['Format'] == 'HDF'
                        RE_INT_4.match(item.attrib['Dimensions'])
                        assert link.attrib['NumberType'] == 'Float'
                        assert link.attrib['Precision'] == '4'
                        assert link.text
