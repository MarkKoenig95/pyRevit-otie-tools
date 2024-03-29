from pyrevit import HOST_APP, framework, DB
import os

# In order to import the utilities we need to manually add it's path to sys.path.
# Pretty annoyingly complicated if you ask me...
import sys

absolute_path = os.path.dirname(os.path.abspath(__file__))
graphic_scale_utilities_path = absolute_path + '\pyRevit.tab\Drawing Set.panel\Graphic Scale.pushbutton'
sys.path.insert(1, graphic_scale_utilities_path)

from graphic_scale_utilities import update_all_scale_values, check_if_has_shared_parameters, register_graphic_scale_updater

def docopen_eventhandler(sender, args):
	doc = args.Document
	view_collector = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Views).WhereElementIsNotElementType()
	if check_if_has_shared_parameters(view_collector):
		update_all_scale_values(HOST_APP.app, doc, view_collector)
		register_graphic_scale_updater()

HOST_APP.app.DocumentOpened += \
    framework.EventHandler[DB.Events.DocumentOpenedEventArgs](
        docopen_eventhandler
	)