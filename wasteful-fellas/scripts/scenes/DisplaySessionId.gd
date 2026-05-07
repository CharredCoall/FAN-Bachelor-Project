extends RichTextLabel

func _ready() -> void:
	text = "%09d" % globals.session_id
