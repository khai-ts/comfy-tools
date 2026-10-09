class_name StatBar
extends Control
## A chunky rounded meter with an icon. The fill eases toward the value and the bar pops when it goes up.

var value := 50.0
var fill_color := Color("#ffb3c6")
var icon: Texture2D = null   ## drawn in the bubble on the left; a heart is drawn when null
var _shown := 50.0
var _pulse := 0.0
var _t := 0.0


func _ready() -> void:
	mouse_filter = MOUSE_FILTER_IGNORE
	_shown = value


func set_value(v: float) -> void:
	if v > value + 0.5:
		var tw := create_tween()
		tw.tween_property(self, "_pulse", 1.0, 0.08)
		tw.tween_property(self, "_pulse", 0.0, 0.5).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
	value = clampf(v, 0.0, 100.0)


func _process(delta: float) -> void:
	_t += delta
	_shown = lerpf(_shown, value, 1.0 - exp(-delta * 5.0))
	pivot_offset = size / 2.0
	scale = Vector2.ONE * (1.0 + 0.08 * _pulse)
	# low meters wobble to ask for attention
	rotation = sin(_t * 18.0) * 0.025 if value < 25.0 else 0.0
	queue_redraw()


func _draw() -> void:
	var h := size.y
	var r := h / 2.0
	var track := Rect2(Vector2(r, 6), Vector2(size.x - r, h - 12))
	_box(Rect2(track.position + Vector2(0, 4), track.size), Color(0.55, 0.35, 0.4, 0.18), track.size.y / 2)
	_box(track, Color(1, 1, 1, 0.92), track.size.y / 2)
	var inner := track.grow(-7)
	inner.position.x += r * 0.55
	inner.size.x -= r * 0.55
	var col := fill_color.lerp(Color("#ff8a80"), clampf((30.0 - _shown) / 30.0, 0.0, 1.0))
	var w := maxf(inner.size.x * _shown / 100.0, inner.size.y)
	_box(Rect2(inner.position, Vector2(w, inner.size.y)), col.lerp(Color.WHITE, 0.25 * _pulse), inner.size.y / 2)
	_box(Rect2(inner.position + Vector2(8, 4), Vector2(maxf(w - 16, 4), inner.size.y * 0.28)),
		Color(1, 1, 1, 0.45), inner.size.y * 0.14)
	# icon bubble
	draw_circle(Vector2(r, r + 4), r, Color(0.55, 0.35, 0.4, 0.18))
	draw_circle(Vector2(r, r), r, Color.WHITE)
	draw_circle(Vector2(r, r), r - 5, fill_color.lerp(Color.WHITE, 0.55))
	if icon:
		var s := icon.get_size()
		var k := (h * 0.72) / maxf(s.x, s.y)
		draw_texture_rect(icon, Rect2(Vector2(r, r) - s * k / 2.0, s * k), false)
	else:
		var pts := PackedVector2Array()
		for i in 32:
			var t := TAU * i / 32.0
			pts.append(Vector2(r, r + 2) + Vector2(16.0 * pow(sin(t), 3),
				-(13.0 * cos(t) - 5.0 * cos(2 * t) - 2.0 * cos(3 * t) - cos(4 * t))) * h * 0.022)
		draw_colored_polygon(pts, Color("#ff7aa2"))


func _box(rect: Rect2, col: Color, radius: float) -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = col
	sb.set_corner_radius_all(int(radius))
	sb.anti_aliasing = true
	draw_style_box(sb, rect)
