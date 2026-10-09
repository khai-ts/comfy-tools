class_name FxBit
extends Node2D
## One small particle (heart, sparkle star or crumb) that moves, pops in and fades out on its own.

enum Kind { HEART, STAR, DOT }

var kind := Kind.DOT
var color := Color.WHITE
var size := 10.0
var velocity := Vector2.ZERO
var gravity := 0.0
var drag := 0.0
var spin := 0.0
var life := 1.0
var age := 0.0


func _process(delta: float) -> void:
	age += delta
	velocity.y += gravity * delta
	velocity *= exp(-drag * delta)
	position += velocity * delta
	rotation += spin * delta
	scale = Vector2.ONE * _ease_out_back(minf(age / 0.18, 1.0))
	modulate.a = clampf((life - age) / 0.35, 0.0, 1.0)
	if age >= life:
		queue_free()


func _draw() -> void:
	match kind:
		Kind.HEART:
			var pts := PackedVector2Array()
			for i in 32:
				var t := TAU * i / 32.0
				pts.append(Vector2(16.0 * pow(sin(t), 3),
					-(13.0 * cos(t) - 5.0 * cos(2 * t) - 2.0 * cos(3 * t) - cos(4 * t))) * size / 16.0)
			draw_colored_polygon(pts, color)
			draw_polyline(pts + PackedVector2Array([pts[0]]), color.darkened(0.15), 2.0, true)
			draw_circle(Vector2(-size * 0.45, -size * 0.35), size * 0.22, Color(1, 1, 1, 0.7))
		Kind.STAR:
			var pts := PackedVector2Array()
			for i in 8:
				var r := size if i % 2 == 0 else size * 0.32
				pts.append(Vector2.from_angle(TAU * i / 8.0 - PI / 2) * r)
			draw_colored_polygon(pts, color)
		Kind.DOT:
			draw_circle(Vector2.ZERO, size, color)
			draw_circle(Vector2(-size * 0.3, -size * 0.3), size * 0.35, Color(1, 1, 1, 0.5))


static func _ease_out_back(x: float) -> float:
	const C1 := 1.70158
	const C3 := C1 + 1.0
	return 1.0 + C3 * pow(x - 1.0, 3) + C1 * pow(x - 1.0, 2)
