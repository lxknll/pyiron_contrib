import ipywidgets as widgets
import os

from pyiron_base import Project
#from pyiron_base import InputList
from pyiron_contrib.RDM.internal_widgets import MultiComboBox, MultiTextBox


class GUI_RDM:
    """
    Access to the Research Data Management (RDM) system
    """

    # TODO: Add metadata into hdf of project and reload afterwards
    def __init__(self, project=None, Vbox=None):
        if Vbox is None:
            self.box = widgets.VBox()
        else:
            self.box = Vbox
        # rmd_project is a relative path like string representation
        self.default_proj = "SFB1394"
        if project is not None:
            self.default_proj = project.base_name
        self.pr = project
        self.list_groups()
        self.rdm_project = ""

    def list_nodes(self):
        return []

    def list_groups(self):
        if self.pr is None:
            pr = Project(self.default_proj)
            return pr.parent_group.list_groups()
        else:
            return self.pr.list_groups()

    def gui(self):
        self.headerbox = widgets.HBox()
        Hseperator = widgets.HBox(layout=widgets.Layout(border="solid 1px"))
        self.bodybox = widgets.VBox()
        self.footerbox = widgets.HBox()
        self._update_header(self.headerbox)
        self._update_body(self.bodybox)
        self.box.children = tuple([self.headerbox, Hseperator, self.bodybox, self.footerbox])
        return self.box

    def update(self, headerbox=None, bodybox=None, footerbox=None):
        if headerbox is not None:
            self.headerbox = headerbox
        if bodybox is not None:
            self.bodybox = bodybox
        if footerbox is not None:
            self.footerbox = footerbox
        self._update_header(self.headerbox)
        self._update_body(self.bodybox)

    def _update_body(self, box):
        btnLayout = widgets.Layout(color="green", height="120px", width="120px")
        res_buttons = []
        for res in self.list_nodes():
            button = widgets.Button(description=res, icon="fa-briefcase", layout=btnLayout)
            button.on_click(self.open_res)
            res_buttons.append(button)
        button = widgets.Button(description="Add Resource", icon="fa-plus-circle", layout=btnLayout)
        button.on_click(self.add_resource)
        res_buttons.append(button)
        proj_buttons = []
        for proj in self.list_groups():
            button = widgets.Button(description=proj, icon="fa-folder", layout=btnLayout)
            button.path = self.rdm_project + proj + '/'
            button.on_click(self.change_proj)
            proj_buttons.append(button)
        button = widgets.Button(description="Add Project", icon="fa-plus-circle", layout=btnLayout)
        button.on_click(self.add_project)
        proj_buttons.append(button)
        childs = []
        if len(self.rdm_project.split("/")) > 1:
            childs.append(widgets.HTML("<h2>Resources:</h2>"))
            resBox = widgets.HBox(res_buttons)
            resBox.layout.flex_flow = "row wrap"
            childs.append(resBox)
            childs.append(widgets.HTML("<h2>Sub-Projects:</h2>"))
        else:
            childs.append(widgets.HTML("<h2>Projects:</h2>"))
        projBox = widgets.HBox(proj_buttons)
        projBox.layout.flex_flow = "row wrap"
        childs.append(projBox)
        box.children = tuple(childs)

    def _update_header(self, box):
        buttons = []
        tmppath_old = self.rdm_project + ' '
        tmppath = os.path.split(self.rdm_project)[0]
        while tmppath != tmppath_old:
            tmppath_old = tmppath
            [tmppath, proj] = os.path.split(tmppath)
            button = widgets.Button(description=proj, layout=widgets.Layout(width='auto'))
            button.style.button_color = '#DDDDAA'
            button.path = tmppath_old + '/'
            button.on_click(self.change_proj)
            buttons.append(button)
        button = widgets.Button(icon="fa-home", layout=widgets.Layout(width='auto'))
        button.path = ""
        button.style.button_color = '#999999'
        button.on_click(self.change_proj)
        buttons[-1] = button
        buttons.reverse()
        box.children = tuple(buttons)

    def change_proj(self, b):
        self.rdm_project = b.path
        if b.path == "":
            self.pr = None
        else:
            self.pr = Project(self.rdm_project)
        self.rdm_projects = self.list_groups()
        #if not hasattr(self.pr, "metadata"):
        #    self.pr.metadata = None
        self._update_body(self.bodybox)
        self._update_header(self.headerbox)

    def open_res(self, b):
        pass

    def add_resource(self, b):
        pass

    def add_project(self, b):
        add = GUI_AddProject(project=self.pr, VBox=self.bodybox, origin=self)
        add.gui()


class GUI_AddProject():
    def __init__(self, project=None, VBox=None, origin=None):
        if VBox is None:
            self.bodybox = widgets.VBox()
        else:
            self.bodybox = VBox
        self.pr = project
        if hasattr(self.pr, 'metadata'):
            self.old_metadata = self.pr.metadata
        else:
            self.old_metadata = None
        if origin is not None:
            self.origin = origin

    def gui(self):
        self._update(self.bodybox)
        return self.bodybox

    def _update(self, box, _metadata=None):
        def on_click(b):
            if b.description == "Submit":
                dic = {}
                for child in childs:
                    if hasattr(child, 'value') and (child.description != ""):
                        dic[child.description] = child.value
                self.add_proj(dic)
            if b.description == 'Copy Metadata':
                self._update(box, _metadata=self.old_metadata)

        childs = []
        childs.append(widgets.HTML("<h2>Create Project:</h2>"))
        for field in ["Project Name", "Display Name"]:
            childs.append(widgets.Text(
                value='',
                placeholder=field,
                description=field + ":*",
                disabled=False,
                layout=widgets.Layout(width="80%"),
                style={'description_width': '25%'}
            ))
        childs.append(widgets.Textarea(
            value="",
            placeholder="Project Description",
            description="Project Description:*",
            disable=False,
            layout=widgets.Layout(width="80%"),
            style={'description_width': '25%'}
        ))
        childs.append(widgets.HBox(layout=widgets.Layout(border="solid 0.5px lightgray")))
        childs.append(widgets.HTML("<h3>Project Metadata</h3>"))

        if self.old_metadata is not None:
            Label = widgets.Label(
                value="Copy metadata from '" + self.pr.base_name + "'",
                layout=widgets.Layout(
                    width="30%",
                    display="flex",
                    justify_content="flex-end"
                ))
            Button = widgets.Button(description="Copy Metadata")
            Button.on_click(on_click)
            childs.append(widgets.HBox([Label, Button], layout=widgets.Layout(width="85%")))

        if _metadata is None:
            metadata = {
                'Principal Investigators (PIs):*': [[], 'stringlist'],
                'Project Start:*': [None, 'date'],
                'Project End:*': [None, 'date'],
                'Discipline:*': [[], 'stringlist'],
                'Participating Organizations:*': [[], 'stringlist'],
                'Project Keywords:': [[], 'stringlist'],
                'Visibility:*': ["Project Members", 'radiobox'],
                'Grand ID:': [None, 'string']
            }
        else:
            metadata = _metadata

        childs.append(MultiTextBox(
            description="Principal Investigators (PIs):*",
            placeholder="Principal Investigators (PIs)",
            value=metadata["Principal Investigators (PIs):*"][0],
            disable=False,
            layout=widgets.Layout(width="85%"),
            style={'description_width': '30%'}
        ).widget())
        childs.append(widgets.DatePicker(
            description="Project Start:*",
            value=metadata["Project Start:*"][0],
            layout=widgets.Layout(width="50%", display="flex"),
            style={'description_width': '50%'}
        ))
        childs.append(widgets.DatePicker(
            description="Project End:*",
            value=metadata["Project End:*"][0],
            layout=widgets.Layout(width="50%"),
            style={'description_width': '50%'}
        ))
        childs.append(MultiComboBox(
            description="Discipline:*",
            value=metadata["Discipline:*"][0],
            placeholder="Discipline",
            options=["Theoretical Chemistry", "Arts"],
            layout=widgets.Layout(width="85%"),
            style={'description_width': '30%'}
        ).widget())
        childs.append(MultiComboBox(
            description='Participating Organizations:*',
            value=metadata['Participating Organizations:*'][0],
            placeholder="Participating Organizations:",
            options=["MPIE", "RWTH"],
            layout=widgets.Layout(width="85%"),
            style={'description_width': '30%'}
        ).widget())
        childs.append(MultiTextBox(
            description='Project Keywords:',
            value=metadata['Project Keywords:'][0],
            placeholder="Keywords",
            layout=widgets.Layout(width="85%"),
            style={'description_width': '30%'}
        ).widget())
        childs.append(widgets.RadioButtons(
            description='Visibility:*',
            value=metadata['Visibility:*'][0],
            options=["Project Members", "Public"],
            layout=widgets.Layout(width="50%"),
            style={'description_width': '50%'}
        ))
        childs.append(widgets.Text(
            description='Grand ID:',
            placeholder='Grand ID',
            value=metadata['Grand ID:'][0],
            layout=widgets.Layout(width="85%"),
            style={'description_width': '30%'}
        ))

        SubmitButton = widgets.Button(
            description="Submit"
        )
        SubmitButton.on_click(on_click)
        childs.append(SubmitButton)
        box.children = tuple(childs)

    def add_proj(self, dic):
        if self.pr is not None:
            #try:
                pr = self.pr.open(dic["Project Name:*"])
                pr.metadata = dic
            #except None:
            #    print ("Failed to open new project.")
        else:
            #try:
                pr = Project(dic["Project Name:*"])
                pr.metadata = dic
            #except None:
            #    print("Failed to open new project.")
        if self.origin is not None:
            self.origin.update(bodybox=self.bodybox)
        else:
            self.bodybox.children = tuple(widgets.HTML("Project added"))


