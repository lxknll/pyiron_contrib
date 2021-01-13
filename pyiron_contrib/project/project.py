from pyiron_base import InputList, ImportAlarm
from pyiron import Project as ProjectCore
import posixpath
try:
    from pyiron_contrib.project.project_browser import ProjectBrowser
    import_alarm = ImportAlarm()
except ImportError:
    import_alarm = ImportAlarm(
        "The dependencies of the project's browser are not met (ipywidgets, IPython)."
    )
from pyiron_contrib.generic.display_item import DisplayItem


class Project(ProjectCore):

    """ Basically a wrapper of Project from pyiron_atomistic to extend functionality. """
    @import_alarm
    def __init__(self, path="", user=None, sql_query=None, default_working_directory=False):
        super().__init__(path=path,
                         user=user,
                         sql_query=sql_query,
                         default_working_directory=default_working_directory
                         )
        self._project_browser = None
    __init__.__doc__ = ProjectCore.__init__.__doc__

    def open_browser(self, Vbox=None, show_files=False):
        """
        Provides a file browser to inspect the local data system.

        Args:
             Vbox (:class:`ipywidgets.Vbox` / None): Vbox in which the file browser is displayed.
                                            If None, a new Vbox is provided.
        """
        if self._project_browser is None:
            self._project_browser = ProjectBrowser(project=self,
                                                   show_files=show_files,
                                                   Vbox=Vbox)
        else:
            self._project_browser.update(Vbox=Vbox, show_files=show_files)
        return self._project_browser.gui()

    def list_nodes(self, recursive=False):
        """
        List nodes/ jobs/ pyiron objects inside the project

        Args:
            recursive (bool): search subprojects [True/False] - default=False

        Returns:
            list: list of nodes/ jobs/ pyiron objects inside the project
        """
        if "nodes" not in self._filter:
            return []
        nodes = self.get_jobs(recursive=recursive, columns=["job"])["job"]
        return nodes

    def copy(self):
        """
        Copy the project object - copying just the Python object but maintaining the same pyiron path

        Returns:
            Project: copy of the project object
        """
        new = Project(path=self.path, user=self.user, sql_query=self.sql_query)
        return new

    def display_item(self, item, outwidget=None):
        if item in self.list_files() and item not in self.list_files(extension="h5"):
            return DisplayItem(self.path+item, outwidget).display()
        else:
            return DisplayItem(self.__getitem__(item), outwidget).display()

    def _get_item_helper(self, item, convert_to_object=True):
        """
        Internal helper function to get item from project

        Args:
            item (str, int): key
            convert_to_object (bool): convert the object to an pyiron object or only access the HDF5 file - default=True
                                      accessing only the HDF5 file is about an order of magnitude faster, but only
                                      provides limited functionality. Compare the GenericJob object to JobCore object.

        Returns:
            Project, GenericJob, JobCore, dict, list, float: basically any kind of item inside the project.
        """
        if item == "..":
            return self.parent_group
        if item in self.list_nodes():
            if self._inspect_mode or not convert_to_object:
                return self.inspect(item)
            return self.load(item)
        if item in self.list_files(extension="h5"):
            file_name = posixpath.join(self.path, "{}.h5".format(item))
            return ProjectHDFio(project=self, file_name=file_name)
        if item in self.list_files():
            file_name = posixpath.join(self.path, "{}".format(item))
            return DisplayItem(file_name).display()
        if item in self.list_dirs():
            with self.open(item) as new_item:
                return new_item.copy()
        raise ValueError("Unknown item: {}".format(item))

    def __repr__(self):
        """
        Human readable string representation of the project object

        Returns:
            str: string representation
        """
        return str(self.list_all())
