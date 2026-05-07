extends Node2D

func _start_game():
	globals.session_id = RandomNumberGenerator.new().randi_range(0, 999999999)
	globals.current_char = 0
	globals.max_points = 0
	get_tree().change_scene_to_file("res://scripts/scenes/desktop.tscn")
