extends TextEdit
#@onready var messageBox = get_node("TextEdit")
#@onready var replyBox = get_node("Panel/RichTextLabel")

@onready var GameManager = $"../../.."

@onready var green_bubble = preload("res://scripts/scenes/green_bubble.tscn")
@onready var blue_bubble = preload("res://scripts/scenes/blue_bubble.tscn")
@onready var vcontainer = get_parent().get_node("ScrollContainer/VBoxContainer")

@onready var clicks_sfx = [preload("res://scripts/click_sfx1.mp3"), preload("res://scripts/click_sfx2.mp3"), preload("res://scripts/click_sfx3.mp3")]

@onready var SFX = $AudioStreamPlayer
var thread: Thread
var pipes: Dictionary

signal convo_started
signal convo_ended

func _ready():
	thread = Thread.new()
	thread.start(_run_server)

func SendServerMessage() -> void:
	#make green bubble
	var green_bub = green_bubble.instantiate()
	green_bub.prose = text
	vcontainer.add_child(green_bub)
	
	SFX.stop()
	SFX.volume_db = 10.0
	SFX.stream = load("res://art/SFXs/plop_sfx.mp3") 
	SFX.play()
	
	#green bubble for now!
	#$Timer.start()
	
	editable = false
	
	$"../Button".disabled = true
	
	var body = JSON.stringify({"path": "request_reply", "message": text})
	pipes.stdio.store_line(body)
	
	clear()
	
func _request_completed(body):
	var json = JSON.new()
	json.parse(body)
	var dict_package = json.get_data()
	print(dict_package)
	if dict_package == null:
		return
	
	if  dict_package["Points"] != null:
		GameManager._increment_points(dict_package["Points"])
	
	if dict_package["Fridge"] != null:
		GameManager._update_fridge(dict_package["Fridge"])
	
	var blue_bub = blue_bubble.instantiate()
	blue_bub.prose = str(dict_package["Response"])
	vcontainer.add_child(blue_bub)
	
	SFX.stop()
	SFX.volume_db = -10.0
	SFX.stream = load("res://art/SFXs/ding_sfx.mp3") 
	SFX.play()
	clear() #clear message!

	editable = true
	
	$"../Button".disabled = false
	
	if "Ended" in dict_package and dict_package["Ended"]:
		_end_convo()
	

func _on_text_changed() -> void:
	SFX.volume_db = 0.0
	SFX.stop()
	SFX.stream = clicks_sfx.pick_random()
	SFX.play()


func _on_timer_timeout() -> void:
	var green_bub = green_bubble.instantiate()
	green_bub.prose = "Wow that's amazing!"
	vcontainer.add_child(green_bub)
	clear()
	
	SFX.stop()
	SFX.volume_db = -10.0
	SFX.stream = load("res://art/SFXs/ding_sfx.mp3") 
	SFX.play()


func _on_end_convo_button_pressed() -> void:
	var body = JSON.stringify({"path": "end_convo"})
	pipes.stdio.store_line(body)
	_end_convo()

func _end_convo():
	editable = false
	emit_signal("convo_ended")
	
	$"../Button".disabled = true
	
	$"../../../Client/Panel/EndConvoButton".disabled = true
	
	$"../../Panel/StartConvo".disabled = false
	
	var end_label = Label.new()
	end_label.text = "--- Conversation ended ---"
	end_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	end_label.add_theme_color_override("font_color", Color.GRAY)
	
	if globals.current_char < 4:
		globals.current_char += 1
	
	vcontainer.add_child(end_label)
	


func _on_start_convo_pressed() -> void:
	var body = JSON.stringify({"path": "start_convo","char_idx": globals.current_char})
	pipes.stdio.store_line(body)
	
	emit_signal("convo_started")
		
	$"../../../Client/Panel/EndConvoButton".disabled = false
	
	$"../../Panel/StartConvo".disabled = true
	
	var start_label = Label.new()
	start_label.text = "--- Conversation started ---"
	start_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	#start_label.pos.y += 50
	start_label.add_theme_color_override("font_color", Color.GRAY)
	
	vcontainer.add_child(start_label)
	

func _run_server():
	pipes = OS.execute_with_pipe("../python/python", ["../webserver/main.py"], false )
	if pipes.is_empty():
		print("Error?")
	else:
		while (OS.is_process_running(pipes.pid)):
			if pipes.stdio.get_position() < pipes.stdio.get_length():
				print("Python out:")
				var body = pipes.stdio.get_as_text()
				_request_completed(body)
				print("-------------------------")
			if pipes.stderr.get_position() < pipes.stderr.get_length():
				print("Python Error:")
				print(pipes.stderr.get_as_text())
				print("-------------------------")
				assert(OS.is_process_running(pipes.pid), "Error!: Server crashed due to an error.")
			await get_tree().create_timer(1).timeout


func _exit_tree() -> void:
	if thread != null and !pipes.is_empty():
		pipes.stdio.store_line(r"\x03")
		thread.wait_to_finish()
