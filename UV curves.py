# Author- Carl Bass
# Description- make isoparametric curves on a sketch
# create a 3D sketch and U and V lines will be created according to the user input

import adsk.core, adsk.fusion, adsk.cam, traceback
import os

# Global list to keep all event handlers in scope.
handlers = []

# global variables available in all functions
app = adsk.core.Application.get()
ui  = app.userInterface

# global variables because I can't find a better way to pass this info around -- would be nice if fusion api had some cleaner way to do this
debug = False
u_num_curves = 5
v_num_curves = 5

def run(context):
    try:
        
        # Find where the python file lives and look for the icons in the ./.resources folder
        python_file_folder = os.path.dirname(os.path.realpath(__file__))
        resource_folder = os.path.join (python_file_folder, '.resources')

        # Get the CommandDefinitions collection
        command_definitions = ui.commandDefinitions
        
        tooltip = 'Create isoparmatric curves on a surface'

        # Create a button command definition.
        uv_curves_button = command_definitions.addButtonDefinition('UV_curves', 'UV curves', tooltip, resource_folder)
        
        # Connect to the command created event.
        uv_curves_command_created = command_created()
        uv_curves_button.commandCreated.add (uv_curves_command_created)
        handlers.append(uv_curves_command_created)

        # add the Moose Tools and the xy to uv button to the Tools tab
        utilities_tab = ui.allToolbarTabs.itemById('ToolsTab')
        if utilities_tab:
            moose_tools_panel = ui.allToolbarPanels.itemById('MoosePanel')
            if not moose_tools_panel:
                moose_tools_panel = utilities_tab.toolbarPanels.add('MoosePanel', 'Moose Tools')
                debug_print ('Creating Moose Tools panel')
            else:
                debug_print ('Moose Tools already installed')

        if moose_tools_panel:
            # Add the command to the panel.
            control = moose_tools_panel.controls.addCommand(uv_curves_button)
            control.isPromoted = False
            control.isPromotedByDefault = False
            debug_print ('UV curves button added to Moose Tools')

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Event handler for the commandCreated event.
class command_created (adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):

        event_args = adsk.core.CommandCreatedEventArgs.cast(args)
        command = event_args.command
        inputs = command.commandInputs
 
        # Connect to the execute event.
        onExecute = command_executed()
        command.execute.add(onExecute)
        handlers.append(onExecute)

        # create the face selection input
        face_selection_input = inputs.addSelectionInput('face_select', 'Face', 'Select the face')
        face_selection_input.addSelectionFilter('Faces')
        face_selection_input.setSelectionLimits(1,1)

        # create spinner for number of u curves
        inputs.addIntegerSpinnerCommandInput('u_num_curves', 'Number of U curves', 0, 50, 1, u_num_curves)

        # create spinner for number of v curves
        inputs.addIntegerSpinnerCommandInput('v_num_curves', 'Number of V curves', 0, 50, 1, v_num_curves)

        # create debug checkbox
        inputs.addBoolValueInput('debug', 'Debug', True, '', False)

# Event handler for the execute event.
class command_executed (adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        global debug
        global u_num_curves, v_num_curves

        try:
            doc = app.activeDocument
            design = app.activeProduct

            # get current command
            command = args.firingEvent.sender

            #text_palette = ui.palettes.itemById('TextCommands')
            for input in command.commandInputs:
                if (input.id == 'face_select'):
                    face = input.selection(0).entity
                elif (input.id == 'u_num_curves'):
                    u_num_curves = input.value 
                elif (input.id == 'v_num_curves'):
                    v_num_curves = input.value                           
                elif (input.id == 'debug'):
                    debug = input.value           
                else:
                    debug_print (f'OOOPS --- too much input')
        
            debug_print (f'face: {face.objectType}')
            debug_print (f'number of u curves: {u_num_curves}')
            debug_print (f'number of v curves: {v_num_curves}')
            
            # Get the root component of the active design.
            root_component = design.rootComponent

            # Create a new sketch on the xy plane.
            sketch = root_component.sketches.add(root_component.xYConstructionPlane)
            sketch.name = f'UV curves {u_num_curves} x {v_num_curves}'
            debug_print (f'created sketch {sketch.name}')

            sketch_curves = adsk.fusion.SketchCurves.cast(sketch.sketchCurves)      

            # find the isoparametric curves in u
            if u_num_curves > 0:
                curves = get_isoparametric_curves (face, u_num_curves, True)

                # add the u curves to the 3D sketch
                for curve in curves:
                    sketch_curves.sketchFittedSplines.addByNurbsCurve(curve)

            # find the isoparametric curves in v
            if v_num_curves > 0:
                curves = get_isoparametric_curves (face, v_num_curves, False)

                # add the v curves to the 3D sketch
                for curve in curves:
                    sketch_curves.sketchFittedSplines.addByNurbsCurve(curve)
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))	

def get_isoparametric_curves (face, num_curves, u_direction):
    try:

		# Get the evaluator from the input face.
        surface_evaluator = adsk.core.SurfaceEvaluator.cast(face.evaluator)

        if u_direction:
            debug_print ('------------------- U direction -----------------------')
        else:
            debug_print ('------------------- V direction -----------------------')
        
        debug_print (f'number of curves = {num_curves}')

        range_bounding_box = surface_evaluator.parametricRange()
        range_min = range_bounding_box.minPoint
        range_max = range_bounding_box.maxPoint
        
        debug_print (f'u ranges from {range_min.x:.3f} to {range_max.x:.3f} ')
        debug_print (f'v ranges from {range_min.y:.3f} to {range_max.y:.3f} ')


        # Determine the length of the perpendicular curve in parametric space.           
            
        if u_direction:
            parametric_min = range_min.y
            parametric_max = range_max.y

            parametric_length = parametric_max - parametric_min

            parametric_midpoint = (parametric_min + parametric_max) * 0.5  

        else: 

            parametric_min = range_min.x
            parametric_max = range_max.x

            parametric_length = parametric_max - parametric_min

            parametric_midpoint = (parametric_min + parametric_max) * 0.5  


        debug_print (f'parametric length =  {parametric_length:.3f}')

        parameters = []       
        if num_curves == 1:
            parameters.append(parametric_midpoint)
        else:
            parametric_spacing = parametric_length / (num_curves - 1)

            debug_print (f'parametric spacing = {parametric_spacing:.3f}')

            parameters.append(parametric_min)
            for i in range(1, num_curves-1):
                parameters.append (parametric_min + (parametric_spacing * i))
            parameters.append(parametric_max)

        curves = []
        for p in parameters:
            curve_collection = surface_evaluator.getIsoCurve(p, u_direction)
            if curve_collection.count == 0:
                debug_print (f'No curves created')
            else:
                for curve in curve_collection:
                    if curve.objectType != adsk.core.NurbsCurve3D.classType():
                        curve = curve.asNurbsCurve
                        debug_print (f'converted and added {curve_collection.count} curve(s) at p = {p:.3f}')
                    else:
                        debug_print (f'curve {curve.objectType} at p = {p:.3f} added')

                    curves.append(curve)

        return (curves)
    
    except:
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))   
        
def debug_print (msg):
    if debug:
        text_palette = ui.palettes.itemById('TextCommands')
        text_palette.writeText (msg)
        
def stop(context):
    try:

        # Clean up the UI.
        command_definitions = ui.commandDefinitions.itemById('UV_curves')
        if command_definitions:
            command_definitions.deleteMe()
        
        # get rid of this button
        moose_tools_panel = ui.allToolbarPanels.itemById('MoosePanel')
        control = moose_tools_panel.controls.itemById('UV_curves')
        if control:
            control.deleteMe()

        # and if it's the last button, get rid of the moose panel
        if moose_tools_panel.controls.count == 0:
                    moose_tools_panel.deleteMe()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))	