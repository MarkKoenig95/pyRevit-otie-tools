from pyrevit import HOST_APP, DB
from System import Guid
import os

one_inch = 0.083333333334

imperial_sizes = [(one_inch * 0.25, "o_0.25in Scale Text"),
				 (one_inch * 0.375, "o_0.375in Scale Text"),
				 (one_inch * 0.5, "o_0.5in Scale Text"),
				 (one_inch * 0.75, "o_0.75in Scale Text"),
				 (one_inch * 1, "o_1.0in Scale Text"),
				 (one_inch * 1.5, "o_1.5in Scale Text"),
				 (one_inch * 2, "o_2.0in Scale Text"),
				 (one_inch * 2.25, "o_2.25in Scale Text")]

def get_parameter_names():
	parameter_names = []
	for size in imperial_sizes:
		parameter_name = size[1]
		parameter_names.append(parameter_name)
	return parameter_names

def add_shared_parameters(app, doc):
	absolute_path = os.path.dirname(os.path.abspath(__file__))
	relative_path = "supporting_files\graphic_scale_shared_parameters.txt"
	graphic_scale_SPFN = os.path.join(absolute_path, relative_path)

	shared_parameters_group_name = "Graphic Scale"

	cat = doc.Settings.Categories.get_Item(DB.BuiltInCategory.OST_Views)
	
	previous_SPFN = app.SharedParametersFilename

	app.SharedParametersFilename = graphic_scale_SPFN

	shared_params_file = app.OpenSharedParameterFile()

	app.SharedParametersFilename = previous_SPFN

	shared_params_group = shared_params_file.Groups.get_Item(shared_parameters_group_name)

	parameter_names = get_parameter_names()

	t = DB.Transaction(doc, 'Add Graphic Scale Shared Parameters')
 
	t.Start()

	for param in parameter_names:
		definition = shared_params_group.Definitions.get_Item(param)

		cat_set = app.Create.NewCategorySet()

		cat_set.Insert(cat)
 
		binding = app.Create.NewInstanceBinding(cat_set)

		doc.ParameterBindings.Insert(definition, binding)
 
	t.Commit()
	t.Dispose()


def get_segment_length_text_from_scale_value(scale_value, sheet_segment_length):
	segment_length_text = ''
	
	drawing_segment_length = (scale_value * sheet_segment_length)
	drawing_segment_length_feet = drawing_segment_length - (drawing_segment_length % 1)
	drawing_segment_length_rough_inches = (drawing_segment_length % 1) * 12
	drawing_segment_length_inches = round(drawing_segment_length_rough_inches)

	if drawing_segment_length_feet > 0:
		segment_length_text += str(int(drawing_segment_length_feet)) + "'"

	if drawing_segment_length_inches > 0:
		if segment_length_text:
			segment_length_text += "-"
		if drawing_segment_length_rough_inches >= 1:
			segment_length_text += str(int(drawing_segment_length_inches)) + '"'

	return segment_length_text

def update_one_scale_value(view):
	scale_value = view.LookupParameter("View Scale").AsInteger()

	for size_index in range(0,len(imperial_sizes)):
		segment_length = imperial_sizes[size_index][0]
		parameter_name = imperial_sizes[size_index][1]

		segment_length_text = get_segment_length_text_from_scale_value(scale_value, segment_length)
			
		o_scale_value_param = view.LookupParameter(parameter_name)
			
		o_scale_value_param.Set(segment_length_text)
		
	# Add another for loop for metric values here

def check_if_has_shared_parameters(view_collector):
	has_shared_parameters = True
	parameter_names = get_parameter_names()
	for param in parameter_names:
		first_view = view_collector.FirstElement()
		for param in parameter_names:
			shared_parameter_on_first_view = first_view.LookupParameter(param)
			if not shared_parameter_on_first_view:
				has_shared_parameters = False

	return has_shared_parameters

def update_all_scale_values(app, doc, view_collector_param):
	view_collector = view_collector_param or DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Views).WhereElementIsNotElementType()

	has_shared_parameter_on_first_view = check_if_has_shared_parameters(view_collector)

	if not has_shared_parameter_on_first_view:
		add_shared_parameters(app, doc)

	t = DB.Transaction(doc, 'Update Graphic Scale Values')
 
	t.Start()

	for view in view_collector:
		update_one_scale_value(view)
	t.Commit()
	t.Dispose()


class GraphicScaleUpdater(DB.IUpdater):
	def __init__(self, application_id):
		self.app_id = application_id
		self.updater_id = DB.UpdaterId(application_id, Guid("9f80a6d6-2a6d-4414-9f31-3b1bf01d542c"))

	def Execute(self, data):
		doc = data.GetDocument()
		
		view_ids = data.GetModifiedElementIds()

		for view_id in view_ids:
			
			view = doc.GetElement(view_id)

			update_one_scale_value(view)
			
			
	def GetAdditionalInformation(self):
		return "View Title Graphic Scale Updater: updates graphic scale values to match view scale"

	def GetChangePriority(self):
		return DB.ChangePriority.Views

	def GetUpdaterId(self):
		return self.updater_id

	def GetUpdaterName(self):
		return "View Title Graphic Scale Updater"

def register_graphic_scale_updater():
	view_filter = DB.ElementCategoryFilter(DB.BuiltInCategory.OST_Views)
	view_scale_updater = GraphicScaleUpdater(HOST_APP.app.ActiveAddInId)
	parameter_id = DB.ElementId(DB.BuiltInParameter.VIEW_SCALE)
	# Make sure we're not trying to reregister the same updater
	if DB.UpdaterRegistry.IsUpdaterRegistered(view_scale_updater.GetUpdaterId()):
		DB.UpdaterRegistry.UnregisterUpdater(view_scale_updater.GetUpdaterId())
	DB.UpdaterRegistry.RegisterUpdater(view_scale_updater)
	DB.UpdaterRegistry.AddTrigger(view_scale_updater.GetUpdaterId(), view_filter, DB.Element.GetChangeTypeParameter(parameter_id))