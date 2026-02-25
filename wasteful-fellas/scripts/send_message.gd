extends Panel
@onready var messageBox = get_node("TextEdit")
@onready var replyBox = get_node("Panel/RichTextLabel")

func _ready():
	
	$HTTPRequest.request_completed.connect(self._http_request_completed)

func SendServerMessage() -> void:
	var body = JSON.new().stringify({"message": messageBox.text})
	var error = $HTTPRequest.request("http://127.0.0.1:5000/request_reply", ["Content-type: application/json"], HTTPClient.METHOD_POST, body)
	if error != OK:
		push_error("An error occurred in the HTTP request.")
	
func _http_request_completed(result, response_code, headers, body):
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var response = json.get_data()
	
	replyBox.add_text("\nYou: \n \t\t" + messageBox.text)
	replyBox.add_text("\nServer: \n" + response)
	replyBox.scroll_to_line(replyBox.get_line_count())
	messageBox.clear()
	
