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
