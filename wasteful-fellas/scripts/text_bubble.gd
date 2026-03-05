extends Control

@export var prose : String

func _ready() -> void:
	var text_edit = get_child(-1)
	text_edit.scroll_fit_content_height = true
	text_edit.text = prose
	
	await get_tree().process_frame
	custom_minimum_size.y = text_edit.size.y + 125
	
