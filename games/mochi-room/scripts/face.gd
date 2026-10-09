class_name Face
extends Node2D
## The pet's face, drawn in code so it can blink, look around, chew and smile.
## Origin is the point between the eyes.

enum Eyes { OPEN, HAPPY, SQUINT }

const INK := Color("#4a3434")
const MOUTH_IN := Color("#c25b6a")
const TONGUE := Color("#ff9aa8")

var eyes := Eyes.OPEN
var openness := 1.0        ## 1 = eyes open, 0 = closed (blink)
var mouth_open := 0.0      ## 0 = little cat mouth, 1 = wide open
var sad := 0.0             ## 0..1, turns the mouth into a frown
var look := Vector2.ZERO   ## -1..1 pupil offset
var eye_gap := 62.0
var eye_size := Vector2(19, 25)
var mouth_y := 54.0

var _blink_in := 2.0


func _process(delta: float) -> void:
	_blink_in -= delta
	if _blink_in <= 0.0:
		_blink_in = randf_range(1.8, 4.5)
		var tw := create_tween()
		tw.tween_property(self, "openness", 0.05, 0.06)
		tw.tween_property(self, "openness", 1.0, 0.1)
		if randf() < 0.2:  # sometimes a double blink
			tw.tween_property(self, "openness", 0.05, 0.06)
			tw.tween_property(self, "openness", 1.0, 0.1)
	queue_redraw()


func _draw() -> void:
	for side in [-1.0, 1.0]:
		var c := Vector2(side * eye_gap, 0)
		match eyes:
			Eyes.HAPPY:
				_arc(c + Vector2(0, 6), eye_size.x, PI * 1.15, PI * 1.85, 7.0)
			Eyes.SQUINT:
				var w := eye_size.x
				draw_polyline(PackedVector2Array([c + Vector2(-w * side, -12), c + Vector2(w * 0.6 * side, 0),
					c + Vector2(-w * side, 12)]), INK, 7.0, true)
			_:
				var h := eye_size.y * maxf(openness, 0.08)
				_ellipse(c, Vector2(eye_size.x, h), INK)
				if openness > 0.4:
					var hl := c + look * Vector2(6, 5)
					draw_circle(hl + Vector2(-6, -9) * openness, 7.0, Color.WHITE)
					draw_circle(hl + Vector2(6, 7) * openness, 3.5, Color(1, 1, 1, 0.85))

	var m := Vector2(0, mouth_y)
	if mouth_open > 0.05:
		var s := Vector2(16 + 20 * mouth_open, 6 + 30 * mouth_open)
		_ellipse(m + Vector2(0, s.y * 0.4), s, INK)
		_ellipse(m + Vector2(0, s.y * 0.4), s - Vector2(4, 4), MOUTH_IN)
		_ellipse(m + Vector2(0, s.y * 0.85), Vector2(s.x * 0.6, s.y * 0.4), TONGUE)
	elif sad > 0.3:
		_arc(m + Vector2(0, 18), 14.0, PI * 1.2, PI * 1.8, 5.0)
	else:
		# the little "w" cat mouth
		_arc(m + Vector2(-10, -2), 10.0, PI * 0.05, PI * 0.95, 5.0)
		_arc(m + Vector2(10, -2), 10.0, PI * 0.05, PI * 0.95, 5.0)


func _ellipse(c: Vector2, r: Vector2, col: Color) -> void:
	var pts := PackedVector2Array()
	for i in 28:
		pts.append(c + Vector2.from_angle(TAU * i / 28.0) * r)
	draw_colored_polygon(pts, col)


func _arc(c: Vector2, r: float, a0: float, a1: float, w: float) -> void:
	draw_arc(c, r, a0, a1, 16, INK, w, true)
