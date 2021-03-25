# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

"""
Job class for calculating the MTP descriptors for a set of structures.
"""

__author__ = "Marvin Poul"
__copyright__ = "Copyright 2021, Max-Planck-Institut für Eisenforschung GmbH - " \
                "Computational Materials Design (CM) Department"
__version__ = "1.0"
__maintainer__ = "Marvin Poul"
__email__ = "poul@mpie.de"
__status__ = "development"
__date__ = "Mar 25, 2021"

from pyiron_base import Settings, DataContainer, GenericJob, Executable
from .cfgs import Cfg, savecfgs

import os.path

# This class expects the job executable to read the potential and configurations and write the descriptors to a few
# hard-coded paths
_POTENTIAL_PATH="potential.mtp"
_INPUT_PATH="input.cfg"
_OUTPUT_PATH="out.xyz"

class MlipDescriptors(GenericJob):
    """
    Calculates the descriptors for a set of structures from a given MTP potential.

    As input a :class:`.Mlip` job with the MTP potential and a
    :class:`pyiron_atomistics.atomistics.job.structurecontainer.StructureContainer` with the structures of interest
    must be set to the respective attributes of the job :attribute:`.potential` and :attribute:`.structures`.  There are
    no other input parameters.
    """
    def __init__(self, project, job_name):
        super().__init__(project, job_name)
        self.input = DataContainer({'potential_job_id': None, 'structure_container_id': None})
        self._executable_activate()

    @property
    def potential(self):
        """
        :class:`.Mlip`: job that contains a fitted MTP potential or `None` if not set
        """
        return self.project.load(self.input.potential_job_id)

    @potential.setter
    def potential(self, job):
        self.input.potential_job_id = job.id

    @property
    def structures(self):
        """
        :class:`pyiron_atomistics.atomistics.job.structurecontainer.StructureContainer`:
                structure container that keeps the structures to be evaluated
        """
        return self.project.load(self.input.structure_container_id)

    @potential.setter
    def structures(self, job):
        self.input.structure_container_id = job.id

    def write_input(self):
        self._create_working_directory()

        cfgs = []
        container = self.project.load(self.input.structure_container_id)
        for structure in container.structure_lst:
            c = Cfg()
            c.pos = structure.position
            c.lat = structure.cell
            c.types = structure.indices
            cfgs.append(c)

        savecfgs(file_name=os.path.join(self.working_directory, _INPUT_PATH), cfgs=cfgs)

    def collect_output(self):

        def parse(f):
            s = f.readline()
            while s != '':
                N = int(s)
                M = int(f.readline().split()[-1])
                x = np.empty((N,M))
                for i, l in zip(range(N), f):
                    d = np.fromiter(map(float, l.split()), dtype=float)
                    x[i, :] = d[4:4 + M]
                yield x
                s = f.readline()

        file_name = os.path.join(self.working_directory, _OUTPUT_PATH)
        with open(file_name) as f:
            descriptors = np.array(list(parse(f)), dtype=object)

        with self.project_hdf5.open("output") as hdf:
            hdf["descriptors"] = descriptors