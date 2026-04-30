extends ColorRect

@onready var top_area = $TopBar
@onready var tool_bar = $"../../Toolbar/ColorRect"

var pressing = false
var offset = Vector2.ZERO

func _ready() -> void:
	top_area.text = "   " + str(name)
	mouse_filter = Control.MOUSE_FILTER_STOP

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
	#z_index = globals.max_window_index + 1
	#globals.max_window_index = z_index
	move_to_front()
	offset = get_global_mouse_position() - global_position


func _on_top_bar_button_up() -> void:
	pressing = false


func _on_close_pressed() -> void:
	visible = false


func _on_convo_started() -> void: #conected via write message signal
	$"Panel/BG".texture = load("res://art/NPC backgrounds/" + globals.characters[globals.current_char] + "_BG.jpg")
	$"Panel/Character".texture = load("res://art/NPCs/" + globals.characters[globals.current_char] + ".png")


func _on_convo_ended() -> void:
	$"Panel/BG".texture = null
	$"Panel/Character".texture = null
	
