"""
defines GuiAttributes, which defines Gui getter/setter methods
and is inherited from many GUI classes
"""
from __future__ import print_function
import os
import traceback
from collections import OrderedDict

import numpy as np

from pyNastran.gui.gui_objects.settings import Settings
from pyNastran.gui.tool_actions import ToolActions
from pyNastran.gui.views import ViewActions
from pyNastran.gui.utils.load_results import create_res_obj
from pyNastran.gui.utils.vtk.vtk_utils import (
    numpy_to_vtk_points, create_vtk_cells_of_constant_element_type)
from pyNastran.bdf.cards.base_card import deprecated

#class GuiAttributes(QMainWindow):
class GuiAttributes(object):
    """All methods in this class must not require VTK"""
    def __init__(self, **kwds):
        """
        These variables are common between the GUI and
        the batch mode testing that fakes the GUI
        """
        inputs = kwds['inputs']
        res_widget = kwds['res_widget']
        self.dev = False
        self.settings = Settings(self)
        self.tool_actions = ToolActions(self)
        self.view_actions = ViewActions(self)

        # the result type being currently shown
        # for a Nastran NodeID/displacement, this is 'node'
        # for a Nastran ElementID/PropertyID, this is 'element'
        self.result_location = None

        self.case_keys = {}
        self.res_widget = res_widget
        self._show_flag = True
        self._camera_mode = None
        self.observers = {}

        if 'test' in inputs:
            self.is_testing_flag = inputs['test']
        else:
            self.is_testing_flag = False
        self.is_groups = False
        self._logo = None
        self._script_path = None
        self._icon_path = ''

        self.title = None
        self.min_value = None
        self.max_value = None
        self.blue_to_red = False
        self._is_axes_shown = True
        self.nvalues = 9
        #-------------

        # window variables
        self._legend_window_shown = False
        self._preferences_window_shown = False
        self._clipping_window_shown = False
        self._edit_geometry_properties_window_shown = False
        self._modify_groups_window_shown = False
        #self._label_window = None
        #-------------
        # inputs dict
        self.is_edges = False
        self.is_edges_black = self.is_edges

        #self.format = ''
        debug = inputs['debug']
        self.debug = debug
        assert debug in [True, False], 'debug=%s' % debug

        #-------------
        # file
        self.menu_bar_format = None
        self.format = None
        self.infile_name = None
        self.out_filename = None
        self.dirname = ''
        self.last_dir = '' # last visited directory while opening file
        self._default_python_file = None

        #-------------
        # internal params
        self.ncases = 0
        self.icase = 0
        self.icase_disp = None
        self.icase_vector = None
        self.icase_fringe = None

        self.nnodes = 0
        self.nelements = 0

        self.supported_formats = []
        self.model_type = None

        self.tools = []
        self.checkables = []
        self.actions = {}
        self.modules = OrderedDict()

        # actor_slots
        self.text_actors = {}
        self.geometry_actors = OrderedDict()
        self.alt_grids = {} #additional grids

        # coords
        self.transform = {}
        self.axes = {}

        #geom = Geom(color, line_thickness, etc.)
        #self.geometry_properties = {
        #    'name' : Geom(),
        #}
        self.geometry_properties = OrderedDict()
        self.follower_nodes = {}
        self.follower_functions = {}

        self.pick_state = 'node/centroid'
        self.label_actors = {-1 : []}
        self.label_ids = {}
        self.cameras = {}
        self.label_scale = 1.0 # in percent

        self.is_horizontal_scalar_bar = False
        self.is_low_to_high = True

        self.result_cases = {}
        self.num_user_points = 0

        self._is_displaced = False
        self._is_forces = False
        self._is_fringe = False

        self._xyz_nominal = None

        self.nvalues = 9
        self.nid_maps = {}
        self.eid_maps = {}
        self.name = 'main'

        self.groups = {}
        self.group_active = 'main'

        #if not isinstance(res_widget, MockResWidget):
            #if qt_version == 4:
                #QMainWindow.__init__(self)
            #elif qt_version == 5:
                #super(QMainWindow, self).__init__()

        self.main_grids = {}
        self.main_grid_mappers = {}
        self.main_geometry_actors = {}

        self.main_edge_mappers = {}
        self.main_edge_actors = {}

    #-------------------------------------------------------------------
    # deprecated attributes
    def deprecated(self, old_name, new_name, deprecated_version):
        # type: (str, str, str, Optional[List[int]]) -> None
        """
        Throws a deprecation message and crashes if past a specific version.

        Parameters
        ----------
        old_name : str
            the old function name
        new_name : str
            the new function name
        deprecated_version : float
            the version the method was first deprecated in
        """
        deprecated(old_name, new_name, deprecated_version, levels=[0])

    @property
    def nNodes(self):
        """gets the number of nodes"""
        self.deprecated('self.nNodes', 'self.nnodes', '1.1')
        return self.nnodes

    @nNodes.setter
    def nNodes(self, nnodes):
        """sets the number of nodes"""
        self.deprecated('self.nNodes', 'self.nnodes', '1.1')
        self.nnodes = nnodes

    @property
    def nElements(self):
        """gets the number of elements"""
        self.deprecated('self.nElements', 'self.nelements', '1.1')
        return self.nelements

    @nElements.setter
    def nElements(self, nelements):
        """sets the number of elements"""
        self.deprecated('self.nElements', 'self.nelements', '1.1')
        self.nelements = nelements

    #-------------------------------------------------------------------
    # geom
    @property
    def grid(self):
        """gets the active grid"""
        #print('get grid; %r' % self.name)
        return self.main_grids[self.name]

    @grid.setter
    def grid(self, grid):
        """sets the active grid"""
        #print('set grid; %r' % self.name)
        self.main_grids[self.name] = grid

    @property
    def grid_mapper(self):
        """gets the active grid_mapper"""
        return self.main_grid_mappers[self.name]

    @grid_mapper.setter
    def grid_mapper(self, grid_mapper):
        """sets the active grid_mapper"""
        self.main_grid_mappers[self.name] = grid_mapper

    @property
    def geom_actor(self):
        """gets the active geom_actor"""
        return self.main_geometry_actors[self.name]

    @geom_actor.setter
    def geom_actor(self, geom_actor):
        """sets the active geom_actor"""
        self.main_geometry_actors[self.name] = geom_actor

    #-------------------------------------------------------------------
    # edges
    @property
    def edge_mapper(self):
        return self.main_edge_mappers[self.name]

    @edge_mapper.setter
    def edge_mapper(self, edge_mapper):
        self.main_edge_mappers[self.name] = edge_mapper

    @property
    def edge_actor(self):
        """gets the active edge_actor"""
        return self.main_edge_actors[self.name]

    @edge_actor.setter
    def edge_actor(self, edge_actor):
        """sets the active edge_actor"""
        self.main_edge_actors[self.name] = edge_actor

    def set_glyph_scale_factor(self, scale):
        """sets the glyph scale factor"""
        self.glyph_scale_factor = scale
        self.glyphs.SetScaleFactor(scale)

    @property
    def nid_map(self):
        """gets the node_id map"""
        return self.nid_maps[self.name]

    @nid_map.setter
    def nid_map(self, nid_map):
        """sets the node_id map"""
        self.nid_maps[self.name] = nid_map

    @property
    def eid_map(self):
        """gets the element_id map"""
        try:
            return self.eid_maps[self.name]
        except:
            msg = 'KeyError: key=%r; keys=%s' % (self.name, list(self.eid_maps.keys()))
            raise KeyError(msg)

    @eid_map.setter
    def eid_map(self, eid_map):
        """sets the element_id map"""
        self.eid_maps[self.name] = eid_map

    #---------------------------------------------------------------------------
    def _load_patran_nod(self, nod_filename):
        """reads a Patran formatted *.nod file"""
        from pyNastran.bdf.patran_utils.read_patran import load_patran_nod
        A, fmt_dict, headers = load_patran_nod(nod_filename, self.node_ids)

        out_filename_short = os.path.relpath(nod_filename)
        result_type = 'node'
        self._add_cases_to_form(A, fmt_dict, headers, result_type,
                                out_filename_short, update=True,
                                is_scalar=True)

    def _add_cases_to_form(self, A, fmt_dict, headers, result_type,
                           out_filename_short, update=True, is_scalar=True,
                           is_deflection=False, is_force=False):
        """
        common method between:
          - _load_csv
          - _load_deflection_csv

        Parameters
        ----------
        A : dict[key] = (n, m) array
            the numpy arrays
            key : str
                the name
            n : int
                number of nodes/elements
            m : int
                secondary dimension
                N/A : 1D array
                3 : deflection
        fmt_dict : dict[header] = fmt
            the format of the arrays
            header : str
                the name
            fmt : str
                '%i', '%f'
        headers : List[str]???
            the titles???
        result_type : str
            'node', 'centroid'
        out_filename_short : str
            the display name
        update : bool; default=True
            ???

        # A = np.loadtxt('loadtxt_spike.txt', dtype=('float,int'))
        # dtype=[('f0', '<f8'), ('f1', '<i4')])
        # A['f0']
        # A['f1']
        """
        #print('A =', A)
        formi = []
        form = self.get_form()
        icase = len(self.case_keys)
        islot = 0
        for case_key in self.case_keys:
            if isinstance(case_key, tuple):
                islot = case_key[0]
                break

        #assert len(headers) > 0, 'headers=%s' % (headers)
        #assert len(headers) < 50, 'headers=%s' % (headers)
        for header in headers:
            if is_scalar:
                out = create_res_obj(islot, headers, header, A, fmt_dict, result_type)
            else:
                out = create_res_obj(islot, headers, header, A, fmt_dict, result_type,
                                     self.settings.dim_max, self.xyz_cid0)
            res_obj, title = out

            #cases[icase] = (stress_res, (subcase_id, 'Stress - isElementOn'))
            #form_dict[(key, itime)].append(('Stress - IsElementOn', icase, []))
            #key = (res_obj, (0, title))
            self.case_keys.append(icase)
            self.result_cases[icase] = (res_obj, (islot, title))
            formi.append((header, icase, []))

            # TODO: double check this should be a string instead of an int
            self.label_actors[icase] = []
            self.label_ids[icase] = set([])
            icase += 1
        form.append((out_filename_short, None, formi))

        self.ncases += len(headers)
        #cases[(ID, 2, 'Region', 1, 'centroid', '%i')] = regions
        self.res_widget.update_results(form, 'main')


    #-------------------------------------------------------------------
    def set_quad_grid(self, name, nodes, elements, color, line_width=5, opacity=1.):
        """
        Makes a CQUAD4 grid
        """
        self.create_alternate_vtk_grid(name, color=color, line_width=line_width,
                                       opacity=opacity, representation='wire')

        nnodes = nodes.shape[0]
        nquads = elements.shape[0]
        #print(nodes)
        if nnodes == 0:
            return
        if nquads == 0:
            return

        #print('adding quad_grid %s; nnodes=%s nquads=%s' % (name, nnodes, nquads))
        assert isinstance(nodes, np.ndarray), type(nodes)

        points = numpy_to_vtk_points(nodes)
        grid = self.alt_grids[name]
        grid.SetPoints(points)

        etype = 9  # vtk.vtkQuad().GetCellType()
        create_vtk_cells_of_constant_element_type(grid, elements, etype)

        self._add_alt_actors({name : self.alt_grids[name]})

        #if name in self.geometry_actors:
        self.geometry_actors[name].Modified()

    @property
    def displacement_scale_factor(self):
        """
        # dim_max = max_val * scale
        # scale = dim_max / max_val
        # 0.25 added just cause

        scale = self.displacement_scale_factor / tnorm_abs_max
        """
        #scale = dim_max / tnorm_abs_max * 0.25
        scale = self.settings.dim_max * 0.25
        return scale

    def set_script_path(self, script_path):
        """Sets the path to the custom script directory"""
        self._script_path = script_path

    def set_icon_path(self, icon_path):
        """
        Sets the path to the icon directory where custom icons are found
        """
        self._icon_path = icon_path

    def form(self):
        formi = self.res_widget.get_form()
        return formi

    def get_form(self):
        return self._form

    def set_form(self, formi):
        self._form = formi
        data = []
        for key in self.case_keys:
            assert isinstance(key, int), key
            unused_obj, (i, unused_name) = self.result_cases[key]
            t = (i, [])
            data.append(t)

        self.res_widget.update_results(formi, self.name)

        key = list(self.case_keys)[0]
        location = self.get_case_location(key)
        method = 'centroid' if location else 'nodal'

        data2 = [(method, None, [])]
        self.res_widget.update_methods(data2)

    def _remove_old_geometry(self, geom_filename):
        skip_reading = False
        if self.dev:
            return skip_reading

        self.eid_map = {}
        self.nid_map = {}
        params_to_delete = (
            'case_keys', 'icase', 'isubcase_name_map',
            'result_cases', 'eid_map', 'nid_map',
        )
        if geom_filename is None or geom_filename is '':
            skip_reading = True
            return skip_reading
        else:
            self.turn_text_off()
            self.grid.Reset()

            self.result_cases = {}
            self.ncases = 0
            for param in params_to_delete:
                if hasattr(self, param):  # TODO: is this correct???
                    try:
                        delattr(self, param)
                    except AttributeError:
                        msg = 'cannot delete %r; hasattr=%r' % (param, hasattr(self, param))
                        self.log.warning(msg)

            skip_reading = False
        #self.scalarBar.VisibilityOff()
        self.scalarBar.Modified()
        return skip_reading

    #---------------------------------------------------------------------------
    def on_run_script(self, python_file=False):
        """pulldown for running a python script"""
        is_failed = True
        if python_file in [None, False]:
            title = 'Choose a Python Script to Run'
            wildcard = "Python (*.py)"
            infile_name = self._create_load_file_dialog(
                wildcard, title, self._default_python_file)[1]
            if not infile_name:
                return is_failed # user clicked cancel

            #python_file = os.path.join(script_path, infile_name)
            python_file = os.path.join(infile_name)

        if not os.path.exists(python_file):
            msg = 'python_file = %r does not exist' % python_file
            self.log_error(msg)
            return is_failed

        lines = open(python_file, 'r').read()
        try:
            exec(lines)
        except Exception as error:
            #self.log_error(traceback.print_stack(f))
            self.log_error('\n' + ''.join(traceback.format_stack()))
            #traceback.print_exc(file=self.log_error)
            self.log_error(str(error))
            return is_failed
        is_failed = False
        self._default_python_file = python_file
        self.log_command('self.on_run_script(%r)' % python_file)
        print('self.on_run_script(%r)' % python_file)
        return is_failed

    #---------------------------------------------------------------------------
    def create_coordinate_system(self, coord_id, dim_max, label='',
                                 origin=None, matrix_3x3=None,
                                 coord_type='xyz'):
        """
        Creates a coordinate system

        Parameters
        ----------
        coord_id : float
            the coordinate system id
        dim_max : float
            the max model dimension; 10% of the max will be used for the coord length
        label : str
            the coord id or other unique label (default is empty to indicate the global frame)
        origin : (3, ) ndarray/list/tuple
            the origin
        matrix_3x3 : (3, 3) ndarray
            a standard Nastran-style coordinate system
        coord_type : str
            a string of 'xyz', 'Rtz', 'Rtp' (xyz, cylindrical, spherical)
            that changes the axis names

        .. todo::  coord_type is not supported ('xyz' ONLY)
        .. todo::  Can only set one coordinate system
        """
        self.tool_actions.create_coordinate_system(
            coord_id, dim_max, label=label,
            origin=origin, matrix_3x3=matrix_3x3,
            coord_type=coord_type)

    def create_global_axes(self, dim_max):
        """creates the global axis"""
        cid = 0
        self.tool_actions.create_coordinate_system(
            cid, dim_max, label='', origin=None, matrix_3x3=None, coord_type='xyz')

    def create_corner_axis(self):
        """creates the axes that sits in the corner"""
        self.tool_actions.create_corner_axis()

    def update_axes_length(self, dim_max):
        """
        sets the driving dimension for:
          - picking?
          - coordinate systems
          - label size
        """
        self.settings.dim_max = dim_max
        dim = self.dim * 0.10
        self.on_set_axes_length(dim)

    def on_set_axes_length(self, dim=None):
        """
        scale coordinate system based on model length
        """
        if dim is None:
            dim = self.settings.dim_max * 0.10
        for axes in itervalues(self.axes):
            axes.SetTotalLength(dim, dim, dim)

    def update_text_actors(self, subcase_id, subtitle, min_value, max_value, label):
        """
        Updates the text actors in the lower left

        Max:  1242.3
        Min:  0.
        Subcase: 1 Subtitle:
        Label: SUBCASE 1; Static
        """
        self.tool_actions.update_text_actors(subcase_id, subtitle, min_value, max_value, label)

    def update_camera(self, code):
        self.tool_actions.update_camera(code)

    def _update_camera(self, camera=None):
        self.tool_actions._update_camera(camera)

    def create_text(self, position, label, text_size=18):
        """creates the lower left text actors"""
        self.tool_actions.create_text(position, label, text_size=text_size)

    def turn_text_off(self):
        """turns all the text actors off"""
        self.tool_actions.turn_text_off()

    def turn_text_on(self):
        """turns all the text actors on"""
        self.tool_actions.turn_text_on()

    def export_case_data(self, icases=None):
        """exports CSVs of the requested cases"""
        self.tool_actions.export_case_data(icases=icases)

    #---------------------------------------------------------------------------
    def on_pan_left(self, event):
        self.view_actions.on_pan_left(event)

    def on_pan_right(self, event):
        self.view_actions.on_pan_right(event)

    def on_pan_up(self, event):
        self.view_actions.on_pan_up(event)

    def on_pan_down(self, event):
        self.view_actions.on_pan_down(event)

    #------------------------------
    def rotate(self, rotate_deg, render=True):
        """rotates the camera by a specified amount"""
        self.view_actions.rotate(rotate_deg, render=render)

    def on_rotate_clockwise(self):
        """rotate clockwise"""
        self.view_actions.rotate(15.0)

    def on_rotate_cclockwise(self):
        """rotate counter clockwise"""
        self.view_actions.rotate(-15.0)

    #------------------------------
    def zoom(self, value):
        return self.view_actions.zoom(value)

    def on_increase_magnification(self):
        """zoom in"""
        self.view_actions.on_increase_magnification()

    def on_decrease_magnification(self):
        """zoom out"""
        self.view_actions.on_decrease_magnification()

    def set_focal_point(self, focal_point):
        """
        Parameters
        ----------
        focal_point : (3, ) float ndarray
            The focal point
            [ 188.25109863 -7. -32.07858658]
        """
        self.view_actions.set_focal_point(focal_point)

    def on_surface(self):
        """sets the main/toggle actors to surface"""
        self.view_actions.on_surface()

    def on_wireframe(self):
        """sets the main/toggle actors to wirefreme"""
        self.view_actions.on_wireframe()

