class_name Pet
extends Node2D
## Mochi the cat. Origin is the point between its feet; the body squashes from there.

signal chewed(bite: int)
signal finished_eating
signal hopped

const BODY_TEX := preload("res://art/pet.png")
const FACE_POS := Vector2(-36, -352)   ## between the eyes, in body texture pixels from bottom centre
const BODY_SCALE := 0.88

var squash := Vector2.ONE   ## tweened by actions, multiplied with breathing
var hop := 0.0               ## tweened vertical jump offset
var focus: Node2D = null     ## food the pet is watching
var eating := false
var hunger := 50.0           ## set by main, used for the mood

var body: Sprite2D
var face: Face
var _t := 0.0
var _seq: Tween
var _glance := Vector2.ZERO
var _glance_in := 1.0


func _ready() -> void:
	body = Sprite2D.new()
	body.texture = BODY_TEX
	body.offset = Vector2(0, -BODY_TEX.get_height() / 2.0)
	add_child(body)
	face = Face.new()
	face.position = FACE_POS
	body.add_child(face)


func _process(delta: float) -> void:
	_t += delta
	var b := sin(_t * 2.4) * 0.018
	body.scale = BODY_SCALE * squash * Vector2(1.0 - b, 1.0 + b)
	body.position.y = hop
	queue_redraw()  # shadow follows the hop

	# eyes: follow the food, otherwise glance around now and then
	_glance_in -= delta
	if _glance_in <= 0.0:
		_glance_in = randf_range(1.2, 3.5)
		_glance = Vector2(randf_range(-1, 1), randf_range(-0.6, 0.6)) if randf() < 0.6 else Vector2.ZERO
	var target := _glance
	if is_instance_valid(focus):
		var d := focus.global_position - face.global_position
		target = d.normalized() * clampf(d.length() / 250.0, 0.0, 1.0)
		if not eating:
			# open wide as the food gets close
			var want := clampf(1.0 - (d.length() - 120.0) / 380.0, 0.0, 1.0)
			face.mouth_open = lerpf(face.mouth_open, want, 1.0 - exp(-delta * 14.0))
	elif not eating:
		face.mouth_open = lerpf(face.mouth_open, 0.0, 1.0 - exp(-delta * 10.0))
	face.look = face.look.lerp(target, 1.0 - exp(-delta * 10.0))
	face.sad = lerpf(face.sad, 1.0 if hunger < 30.0 else 0.0, delta * 3.0)


func _draw() -> void:
	var k := 1.0 + hop / 300.0  # shadow shrinks while in the air
	var w := 170.0 * squash.x * k
	var pts := PackedVector2Array()
	for i in 32:
		pts.append(Vector2.from_angle(TAU * i / 32.0) * Vector2(w, 26.0 * k) + Vector2(0, -6))
	draw_colored_polygon(pts, Color(0.45, 0.25, 0.3, 0.18 * k))


func mouth_global() -> Vector2:
	return face.to_global(Vector2(0, face.mouth_y + 10))


func head_global() -> Vector2:
	return body.to_global(Vector2(-20, -520))


func hit(p: Vector2) -> bool:
	var l := body.to_local(p) - Vector2(-20, -250)
	return (l / Vector2(240, 260)).length() < 1.0


func poke() -> void:
	if eating:
		return
	_restart()
	face.eyes = Face.Eyes.HAPPY
	_seq.tween_property(self, "squash", Vector2(1.25, 0.78), 0.07).set_trans(Tween.TRANS_QUAD)
	_seq.tween_property(self, "squash", Vector2.ONE, 0.7).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	_seq.parallel().tween_callback(func(): face.eyes = Face.Eyes.OPEN).set_delay(0.5)


func eat() -> void:
	_restart()
	eating = true
	face.eyes = Face.Eyes.OPEN
	_seq.tween_property(face, "mouth_open", 0.0, 0.05)
	_seq.parallel().tween_property(self, "squash", Vector2(1.2, 0.84), 0.07)
	for bite in 3:
		_seq.tween_callback(func(): chewed.emit(bite))
		_seq.tween_property(face, "mouth_open", 0.4, 0.11).set_trans(Tween.TRANS_SINE)
		_seq.parallel().tween_property(self, "squash", Vector2(0.94, 1.07), 0.11).set_trans(Tween.TRANS_SINE)
		_seq.tween_property(face, "mouth_open", 0.0, 0.1).set_trans(Tween.TRANS_SINE)
		_seq.parallel().tween_property(self, "squash", Vector2(1.08, 0.93), 0.1).set_trans(Tween.TRANS_SINE)
	_seq.tween_callback(func():
		eating = false
		face.eyes = Face.Eyes.HAPPY
		finished_eating.emit())
	_add_hop()
	_seq.tween_interval(0.5)
	_seq.tween_callback(func(): face.eyes = Face.Eyes.OPEN)


func refuse() -> void:
	_restart()
	face.eyes = Face.Eyes.SQUINT
	face.mouth_open = 0.0
	for i in 4:
		_seq.tween_property(self, "rotation", 0.09 * (1 if i % 2 == 0 else -1), 0.07)
	_seq.tween_property(self, "rotation", 0.0, 0.08)
	_seq.tween_interval(0.35)
	_seq.tween_callback(func(): face.eyes = Face.Eyes.OPEN)


func celebrate() -> void:
	if eating:
		return
	_restart()
	face.eyes = Face.Eyes.HAPPY
	_add_hop()
	_add_hop()
	_seq.tween_callback(func(): face.eyes = Face.Eyes.OPEN)


func _add_hop() -> void:
	_seq.tween_property(self, "squash", Vector2(1.22, 0.8), 0.09).set_trans(Tween.TRANS_QUAD)
	_seq.tween_callback(func(): hopped.emit())
	_seq.tween_property(self, "hop", -90.0, 0.2).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	_seq.parallel().tween_property(self, "squash", Vector2(0.88, 1.15), 0.12)
	_seq.tween_property(self, "hop", 0.0, 0.17).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	_seq.parallel().tween_property(self, "squash", Vector2.ONE, 0.17)
	_seq.tween_property(self, "squash", Vector2(1.2, 0.82), 0.06)
	_seq.tween_property(self, "squash", Vector2.ONE, 0.5).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)


func _restart() -> void:
	if _seq:
		_seq.kill()
	eating = false
	rotation = 0.0
	hop = 0.0
	_seq = create_tween()
