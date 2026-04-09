extends ColorRect

@onready var top_area = $TopBar
@onready var tool_bar = get_parent().get_node("Toolbar/ColorRect")

var pressing = false
var offset = Vector2.ZERO

func _ready() -> void:
	top_area.text = "   " + str(name)

func _process(_delta: float) -> void:
	if pressing:
		var new_pos = get_global_mouse_position() - offset
		var max_y = tool_bar.position.y - size.y
		var max_x = get_viewport_rect().size.x - size.x
		
		new_pos.x = clamp(new_pos.x, 0, max_x)
		new_pos.y = clamp(new_pos.y, 0, max_y)
		
		global_position = new_pos


func _on_top_bar_button_down() -> void:
	pressing = true
	z_index = globals.max_window_index + 1
	globals.max_window_index = z_index
	offset = get_global_mouse_position() - global_position


func _on_top_bar_button_up() -> void:
	pressing = false
