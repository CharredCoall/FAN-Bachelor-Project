extends Node

@onready var session_id = RandomNumberGenerator.new().randi_range(0, 999999999)

#var max_window_index = 0

var current_char = 0

var characters = ["Jim", "Brody", "Cecilia", "Jasmine", "Voll"]

var max_points = 0.0

var sound_on = true
