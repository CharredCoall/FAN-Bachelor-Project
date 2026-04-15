extends Node2D
@onready var points_label = $"Client Satisfaction/Panel/RichTextLabel"
@onready var fridge_label = $"Client's Fridge/Panel/RichTextLabel"

var points = 0
var fridge = {}

func _increment_points(value) -> void:
	points += value
	points_label.text = str(points)

func _update_fridge(new_fridge) -> void:
	fridge = new_fridge
	var fridge_string = "Items in fridge:"
	
	for item in fridge:
		fridge_string += "\n -  " + str(fridge[item]) + " " + item
	
	fridge_label.text = fridge_string


func _on_app_pressed(butt_name) -> void:
	var window
	var dot = get_node("Toolbar/" + butt_name).get_child(0)
	
	match butt_name:
		"RecycleButton":
			window = $"Waste Planner"
		"CameraButton":
			window = $"Client"
		"PointsButton":
			window = $"Client Satisfaction"
		"FridgeButton":
			window = $"Client's Fridge"
		"HelpButton":
			window = $"Work Guide"
	
	window.visible = !window.visible
	globals.max_window_index += 1
	window.z_index = globals.max_window_index
	
	if !window.visible:
		dot.visible = false
	else:
		dot.visible = true
