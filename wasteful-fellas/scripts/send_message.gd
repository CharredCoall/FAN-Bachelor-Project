extends TextEdit
#@onready var messageBox = get_node("TextEdit")
#@onready var replyBox = get_node("Panel/RichTextLabel")

@onready var green_bubble = preload("res://scripts/scenes/green_bubble.tscn")
@onready var blue_bubble = preload("res://scripts/scenes/blue_bubble.tscn")
@onready var vcontainer = get_parent().get_node("ScrollContainer/VBoxContainer")

@onready var clicks_sfx = [preload("res://scripts/click_sfx1.mp3"), preload("res://scripts/click_sfx2.mp3"), preload("res://scripts/click_sfx3.mp3")]

@onready var SFX = $AudioStreamPlayer

func _ready():
	$HTTPRequest.request_completed.connect(self._http_request_completed)

func SendServerMessage() -> void:
	var message = text
	
	#make blue bubble
	var blue_bub = blue_bubble.instantiate()
	blue_bub.prose = text
	vcontainer.add_child(blue_bub)
	
	SFX.stop()
	SFX.volume_db = 10.0
	SFX.stream = load("res://art/SFXs/plop_sfx.mp3") 
	SFX.play()
	
	#green bubble for now!
	#$Timer.start()
	
	var body = JSON.new().stringify({"message": text})
	var error = $HTTPRequest.request("http://127.0.0.1:5000/request_reply", ["Content-type: application/json"], HTTPClient.METHOD_POST, body)
	if error != OK:
		push_error("An error occurred in the HTTP request.")
	
	clear()
	
func _http_request_completed(result, response_code, headers, body):
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var dict_package = json.get_data()
	if dict_package["Response"] == null:
		return
	
	
	var green_bub = green_bubble.instantiate()
	green_bub.prose = str(dict_package["Response"])
	vcontainer.add_child(green_bub)
	clear()
	
	SFX.stop()
	SFX.volume_db = -10.0
	SFX.stream = load("res://art/SFXs/ding_sfx.mp3") 
	SFX.play()
	clear() #clear message!
	
func _increment_points(points) -> void:
	pass

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
	var error = $HTTPRequest.request("http://127.0.0.1:5000/end_convo", [], HTTPClient.METHOD_GET)
	if error != OK:
		push_error("An error occurred in the HTTP request.")
	
	editable = false
	
	$"../Button".disabled = true
	
	$"../../NPCWindow/EndConvoButton".disabled = true
	
	$"../StartConvo".disabled = false
	
	var end_label = Label.new()
	end_label.text = "--- Conversation ended ---"
	end_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	end_label.add_theme_color_override("font_color", Color.GRAY)
	
	vcontainer.add_child(end_label)


func _on_start_convo_pressed() -> void:
	var error = $HTTPRequest.request("http://127.0.0.1:5000/start_convo", [], HTTPClient.METHOD_GET)
	if error != OK:
		push_error("An error occurred in the HTTP request.")
	
	editable = true
	
	$"../Button".disabled = false
	
	$"../../NPCWindow/EndConvoButton".disabled = false
	
	$"../StartConvo".disabled = true
	
	var start_label = Label.new()
	start_label.text = "--- Conversation started ---"
	start_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	#start_label.pos.y += 50
	start_label.add_theme_color_override("font_color", Color.GRAY)
	
	vcontainer.add_child(start_label)
	
