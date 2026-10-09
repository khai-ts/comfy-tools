class_name FoodButton
extends Control
## A round, squishy food button. Tap it to toss the food, or drag the food onto the pet.

signal pressed_down(button: FoodButton)
signal tapped(button: FoodButton)
signal drag_started(button: FoodButton)
signal drag_ended(button: FoodButton)

var index := 0
var texture: Texture2D
var color := Color("#ffc8dd")
var label := ""

var _held := false
var _dragging := false
var _press_pos := Vector2.ZERO
var _t := 0.0
var _hover := 0.0
var _tween: Tween


func _ready() -> void:
	custom_minimum_size = Vector2(140, 170)
	mouse_filter = MOUSE_FILTER_STOP
	mouse_entered.connect(func(): _hover = 1.0)
	mouse_exited.connect(func(): _hover = 0.0)
	_t = index * 0.7


func _process(delta: float) -> void:
	_t += delta
	pivot_offset = Vector2(size.x / 2, 70)
	rotation = sin(_t * 2.0) * 0.03 + _hover * sin(_t * 9.0) * 0.04
	queue_redraw()


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_held = true
			_press_pos = event.position
			squish()
			pressed_down.emit(self)
		elif _held:
			_held = false
			_release()
			if _dragging:
				_dragging = false
				drag_ended.emit(self)
			else:
				tapped.emit(self)
	elif event is InputEventMouseMotion and _held and not _dragging:
		if event.position.distance_to(_press_pos) > 24.0:
			_dragging = true
			drag_started.emit(self)


func squish() -> void:
	_bounce(Vector2(1.15, 0.82), 0.06)


func _release() -> void:
	_bounce(Vector2(0.92, 1.1), 0.07)


func _bounce(to: Vector2, t: float) -> void:
	if _tween:
		_tween.kill()
	_tween = create_tween()
	_tween.tween_property(self, "scale", to, t).set_trans(Tween.TRANS_QUAD)
	_tween.tween_property(self, "scale", Vector2.ONE, 0.6).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)


func center_global() -> Vector2:
	return global_position + Vector2(size.x / 2, 70) * scale


func _draw() -> void:
	var c := Vector2(size.x / 2, 70)
	var r := 62.0
	draw_circle(c + Vector2(0, 8), r, color.darkened(0.25))
	draw_circle(c, r, Color.WHITE)
	draw_circle(c, r - 6, color)
	draw_arc(c, r - 16, PI * 1.1, PI * 1.5, 12, Color(1, 1, 1, 0.55), 8.0, true)
	if texture:
		var s := texture.get_size()
		var k := 92.0 / maxf(s.x, s.y)
		var bob := sin(_t * 3.0) * 3.0
		draw_texture_rect(texture, Rect2(c - s * k / 2.0 + Vector2(0, bob), s * k), false)
	var font := get_theme_default_font()
	draw_string_outline(font, Vector2(0, 160), label, HORIZONTAL_ALIGNMENT_CENTER, size.x, 26, 8, Color.WHITE)
	draw_string(font, Vector2(0, 160), label, HORIZONTAL_ALIGNMENT_CENTER, size.x, 26, Color("#7a4b55"))
