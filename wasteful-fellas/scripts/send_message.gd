extends TextEdit
#@onready var messageBox = get_node("TextEdit")
#@onready var replyBox = get_node("Panel/RichTextLabel")

@onready var GameManager = $"../../.."

@onready var green_bubble = preload("res://scripts/scenes/green_bubble.tscn")
@onready var blue_bubble = preload("res://scripts/scenes/blue_bubble.tscn")
@onready var vcontainer = get_parent().get_node("ScrollContainer/VBoxContainer")

@onready var clicks_sfx = [preload("res://scripts/click_sfx1.mp3"), preload("res://scripts/click_sfx2.mp3"), preload("res://scripts/click_sfx3.mp3")]

@onready var SFX = $AudioStreamPlayer
@onready var init_chat_button = get_parent().get_node("StartConvo")

@onready var ball_scene = preload("res://scripts/scenes/balls.tscn")

var base_url = "https://wastefulfellas-dkdsd4bkhrepf8ec.swedencentral-01.azurewebsites.net"

var cur_chat #chat button that appears

var model_idx = 0
var steps
var log = []
var last_sent_message = ""

var history = {}
var selected_chat #chat for history

signal convo_started
signal convo_ended

func _ready():
	set("theme_override_colors/font_placeholder_color", Color(0.348, 0.345, 0.33, 0.522))
	cur_chat = init_chat_button
	$HTTPRequest.request_completed.connect(self._request_completed)
	
	for i in range(5):
		history[str(i)] = []
	
	print(history)

func SendServerMessage() -> void:
	placeholder_text = "Client is typing..."
	set("theme_override_colors/font_placeholder_color", Color(0.348, 0.345, 0.33, 0.522))
	#make green bubble
	if selected_chat == globals.current_char:
		var green_bub = green_bubble.instantiate()
		green_bub.prose = text
		vcontainer.add_child(green_bub)
	#else add vfx at button?
	
	if text != null:
		history[str(globals.current_char)].append(text)
	
	SFX.stop()
	SFX.volume_db = 10.0
	SFX.stream = load("res://art/SFXs/plop_sfx.mp3") 
	SFX.play()
	
	editable = false
	
	$"../Button".disabled = true
	
	last_sent_message = text
	
	var body = JSON.stringify({"message": text, "model_idx": int(model_idx), "char_idx": int(globals.current_char), "steps": steps, "log": log, "fridge": GameManager.fridge})
	var error = $HTTPRequest.request(base_url + "/request_reply", ["Content-type: application/json"], HTTPClient.METHOD_POST, body)
	if error != OK:
		push_error("An error occurred in the HTTP request.")
		
	clear()
	
	var balls = ball_scene.instantiate()
	balls.get_child(-1).play("ball_bounce")
	balls.name = "BALLS"
	vcontainer.add_child(balls)
	
	
func _request_completed(_result, _response_code, _headers, body):
	placeholder_text = "Write something..."
	set("theme_override_colors/font_placeholder_color", Color(0.0, 0.425, 0.593, 0.522))
	if vcontainer.get_node("BALLS") != null:
		vcontainer.get_node("BALLS").queue_free()
	
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var dict_package = json.get_data()
	if dict_package == null:
		return
		
	if "error" in dict_package:
		push_error(dict_package["error"])
		return
	
	if "points" in dict_package:
		GameManager._increment_points(dict_package["points"])
		print("Points:", dict_package["points"])
	
	if "fridge" in dict_package:
		GameManager._update_fridge(dict_package["fridge"])
		print("Fridge:", dict_package["fridge"])
	
	if "model_idx" in dict_package:
		model_idx = dict_package["model_idx"]
		print("Model:", model_idx)
	
	if "char_idx" in dict_package:
		print("Character:", dict_package["char_idx"])
	
	if "steps" in dict_package:
		steps = dict_package["steps"]
	
	if selected_chat == globals.current_char:
		var blue_bub = blue_bubble.instantiate()
		blue_bub.prose = str(dict_package["response"])
		print("Response:", dict_package["response"], "\n")
		vcontainer.add_child(blue_bub)
	
	SFX.stop()
	SFX.volume_db = -10.0
	SFX.stream = load("res://art/SFXs/ding_sfx.mp3") 
	SFX.play()
	clear() #clear message!

	if selected_chat == globals.current_char:
		editable = true
	
		$"../Button".disabled = false
	
	if len(log) == 0 or log == []:
		last_sent_message = "[System Information: The fridge currently contains: " + str(GameManager.fridge) + "]
        [System Event: The conversation has just started, and you are speaking first. 
        Generate your opening message to the player strictly based on your character's persona, current mood, and constraints. Do not break character.]"
	
	log.append(['"' + last_sent_message.replace('"', "'") + '"', '"' + dict_package["response"].replace('"', "'") + '"'])
	
	history[str(globals.current_char)].append(dict_package["response"])
	print(history)
	
	if "ended" in dict_package and dict_package["ended"]:
		_end_convo()
	
	
	

func _on_text_changed() -> void:
	SFX.volume_db = 0.0
	SFX.stop()
	SFX.stream = clicks_sfx.pick_random()
	SFX.play()


func _on_timer_timeout() -> void:
	cur_chat.visible = true
	
	SFX.stop()
	SFX.volume_db = -10.0
	SFX.stream = load("res://art/SFXs/ding_sfx.mp3") 
	SFX.play()


func _on_end_convo_button_pressed() -> void:
	if len(log) > 0 and log != []:
		var body = JSON.stringify({"model_idx": int(model_idx), "char_idx": int(globals.current_char), "log": log})
		var error = $HTTPRequest.request(base_url + "/end_convo", ["Content-type: application/json"], HTTPClient.METHOD_GET, body)
		if error != OK:
			push_error("An error occurred in the HTTP request.")
	
	_end_convo()

func _end_convo():
	editable = false
	emit_signal("convo_ended")
	
	$"../Button".disabled = true
	
	var prev_char = globals.current_char
	
	if globals.current_char < 4:
		globals.current_char += 1
		
	#print("disabled: ", cur_chat)
	#cur_chat.disabled = true
	
	cur_chat.text = "Conversation ended"
	
	#next chat button
	cur_chat = init_chat_button.get_child(globals.current_char - 1)
	if prev_char != 4:
		$Timer.start()
	else:
		$"../../../End of the Day Report".visible = true
		globals.max_window_index += 1
		$"../../../End of the Day Report".z_index = globals.max_window_index
		$"../../../Toolbar/EndButton".visible = true
		#make end tool bare icon visible
		
	
	#$"../../Panel/StartConvo".disabled = false
	
	#var end_label = Label.new()
	#end_label.text = "--- Conversation ended ---"
	#end_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	#end_label.add_theme_color_override("font_color", Color.GRAY)
	
	log = []
  
	#vcontainer.add_child(end_label)
	


func _on_start_convo_pressed(chat_idx) -> void:
	selected_chat = chat_idx
	if history[str(chat_idx)] != []:
		load_history(chat_idx)
		
		if selected_chat != globals.current_char: #only be able to respond if in correct chat
			editable = false
		else:
			editable = true
		
	else:
		load_history(chat_idx)
		log = []
		
		placeholder_text = "Client is typing..."
	
		print("Attempting to request message from character:", globals.current_char)
		var body = JSON.stringify({"char_idx": int(globals.current_char)})
		var error = $HTTPRequest.request(base_url + "/start_convo", ["Content-type: application/json"], HTTPClient.METHOD_GET, body)
		if error != OK:
			push_error("An error occurred in the HTTP request.")
	
		emit_signal("convo_started")
		
		$"../../../Client/Panel/EndConvoButton".disabled = false
	
		cur_chat.disabled = false
		
		var balls = ball_scene.instantiate()
		balls.get_child(-1).play("ball_bounce")
		balls.name = "BALLS"
		vcontainer.add_child(balls)
	
		#var start_label = Label.new()
		#start_label.text = "\n--- Conversation started ---"
		#start_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		#start_label.pos.y += 50
		#start_label.add_theme_color_override("font_color", Color.GRAY)
	
		#vcontainer.add_child(start_label)
		
	

func load_history(idx):
	for child in vcontainer.get_children():
		child.queue_free()
		
	var convo = history[str(idx)]
	if convo != []:
		for i in range(convo.size()):
			var bubble
			if i%2 == 0:
				bubble = blue_bubble.instantiate()
			else:
				bubble = green_bubble.instantiate()
			bubble.prose = convo[i]
			vcontainer.add_child(bubble)
