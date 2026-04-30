extends Node2D
@onready var points_label = $"Windows/Client Satisfaction/Panel/RichTextLabel"
@onready var fridge_label = $"Windows/Client's Fridge/Panel/RichTextLabel"

var points = 0
var fridge = {}

var first_open = true

func _increment_points(value) -> void:
	points += int(value)
	points_label.text = str(points)

func _update_fridge(new_fridge) -> void:
	fridge = new_fridge
	var fridge_string = "Items in fridge:"
	
	for item in fridge:
		fridge_string += "\n -  " + str(int(fridge[item])) + " " + item
	
	fridge_label.text = fridge_string


func _on_app_pressed(butt_name) -> void:
	var window
	var dot = get_node("Toolbar/" + butt_name).get_child(0)
	
	match butt_name:
		"RecycleButton":
			window = $"Windows/Waste Planner"
			if first_open: #when first opening window
				$"Windows/Waste Planner/Panel/WriteMessage/Timer".start()
				first_open = false
		"CameraButton":
			window = $"Windows/Client"
		"PointsButton":
			window = $"Windows/Client Satisfaction"
		"FridgeButton":
			window = $"Windows/Client's Fridge"
		"HelpButton":
			window = $"Windows/Work Guide"
		"EndButton":
			window = $"Windows/End of the Day Report"
	
	window.visible = !window.visible
	#globals.max_window_index += 1
	#window.z_index = globals.max_window_index
	window.move_to_front()
	
	if !window.visible:
		dot.visible = false
	else:
		dot.visible = true
