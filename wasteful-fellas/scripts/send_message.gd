extends TextEdit
#@onready var messageBox = get_node("TextEdit")
#@onready var replyBox = get_node("Panel/RichTextLabel")

@onready var GameManager = $"../../.."

@onready var green_bubble = preload("res://scripts/scenes/green_bubble.tscn")
@onready var blue_bubble = preload("res://scripts/scenes/blue_bubble.tscn")
@onready var vcontainer = get_parent().get_node("ScrollContainer/VBoxContainer")

@onready var clicks_sfx = [preload("res://scripts/click_sfx1.mp3"), preload("res://scripts/click_sfx2.mp3"), preload("res://scripts/click_sfx3.mp3")]

@onready var SFX = $AudioStreamPlayer

var model_idx = 0
var steps = {}
var log = []
var last_sent_message = ""

signal convo_started
signal convo_ended

func _ready():
	$HTTPRequest.request_completed.connect(self._request_completed)

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
	
	last_sent_message = text
	
	var body = JSON.stringify({"message": text, "model_idx": int(model_idx), "char_idx": int(globals.current_char), "steps": steps, "log": log, "fridge": GameManager.fridge})
	var error = $HTTPRequest.request("http://127.0.0.1:5000/request_reply", ["Content-type: application/json"], HTTPClient.METHOD_POST, body)
	if error != OK:
		push_error("An error occurred in the HTTP request.")
		
	clear()
	
func _request_completed(_result, _response_code, _headers, body):
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var dict_package = json.get_data()
	print(dict_package)
	if dict_package == null:
		return
		
	if "error" in dict_package:
		push_error(dict_package["error"])
		return
	
	if "points" in dict_package:
		GameManager._increment_points(dict_package["points"])
	
	if "fridge" in dict_package:
		GameManager._update_fridge(dict_package["fridge"])
	
	if "model_idx" in dict_package:
		model_idx = dict_package["model_idx"]
	
	if "char_idx" in dict_package:
		globals.current_char = dict_package["char_idx"]
	
	if "steps" in dict_package:
		steps = dict_package["steps"]
	
	var blue_bub = blue_bubble.instantiate()
	blue_bub.prose = str(dict_package["response"])
	vcontainer.add_child(blue_bub)
	
	SFX.stop()
	SFX.volume_db = -10.0
	SFX.stream = load("res://art/SFXs/ding_sfx.mp3") 
	SFX.play()
	clear() #clear message!

	editable = true
	
	$"../Button".disabled = false
	
	log.append([last_sent_message, dict_package["response"]])
	
	if "ended" in dict_package and dict_package["ended"]:
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
	var body = JSON.stringify({"model_idx": int(model_idx), "char_idx": int(globals.current_char), "log": log})
	var error = $HTTPRequest.request("http://127.0.0.1:5000/end_convo", ["Content-type: application/json"], HTTPClient.METHOD_GET, body)
	if error != OK:
		push_error("An error occurred in the HTTP request.")
	
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
	var body = JSON.stringify({"char_idx": int(globals.current_char)})
	var error = $HTTPRequest.request("http://127.0.0.1:5000/start_convo", ["Content-type: application/json"], HTTPClient.METHOD_GET, body)
	if error != OK:
		push_error("An error occurred in the HTTP request.")
	
	emit_signal("convo_started")
		
	$"../../../Client/Panel/EndConvoButton".disabled = false
	
	$"../../Panel/StartConvo".disabled = true
	
	var start_label = Label.new()
	start_label.text = "--- Conversation started ---"
	start_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	#start_label.pos.y += 50
	start_label.add_theme_color_override("font_color", Color.GRAY)
	
	vcontainer.add_child(start_label)
	
