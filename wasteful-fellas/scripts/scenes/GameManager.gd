extends Node2D
@onready var points_label = $"Client Satisfaction/Panel/RichTextLabel"
@onready var fridge_label = $"Client's Fridge/Panel/RichTextLabel"
var thread: Thread
var pipes: Dictionary

var points = 0
var fridge = {}

func _ready():
	thread = Thread.new()
	thread.start(_run_server)

func _increment_points(value) -> void:
	points += value
	points_label.text = str(points)

func _update_fridge(new_fridge) -> void:
	fridge = new_fridge
	var fridge_string = "Items in fridge:"
	
	for item in fridge:
		fridge_string += "\n -  " + str(fridge[item]) + " " + item
	
	fridge_label.text = fridge_string

	thread = Thread.new()
	thread.start(_run_server)
		
func _run_server():
	pipes = OS.execute_with_pipe("../python/python", ["../webserver/main.py"], false )
	if pipes.is_empty():
		print("Error?")
	else:
		while (OS.is_process_running(pipes.pid)):
			if pipes.stdio.get_position() < pipes.stdio.get_length():
				print("Python out:")
				print(pipes.stdio.get_as_text())
				print("-------------------------")
			if pipes.stderr.get_position() < pipes.stderr.get_length():
				print("Python out:")
				print(pipes.stderr.get_as_text())
				print("-------------------------")
			await get_tree().create_timer(2).timeout


func _exit_tree() -> void:
	if thread != null and !pipes.is_empty():
		pipes.stdio.store_line(r"\x03")
		thread.wait_to_finish()
