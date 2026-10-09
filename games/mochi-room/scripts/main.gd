extends Control
## Mochi Room: feed the cat, pet the cat. Run with `-- --demo` to play a scripted showcase.

const FOODS := [
	{"name": "Fish", "tex": preload("res://art/food_fish.png"), "fill": 30.0, "color": Color("#bde0fe"), "crumb": Color("#ffb86b")},
	{"name": "Cake", "tex": preload("res://art/food_cake.png"), "fill": 22.0, "color": Color("#ffc8dd"), "crumb": Color("#fff3e0")},
	{"name": "Milk", "tex": preload("res://art/food_milk.png"), "fill": 15.0, "color": Color("#cdeac0"), "crumb": Color("#ffffff")},
	{"name": "Cookie", "tex": preload("res://art/food_cookie.png"), "fill": 10.0, "color": Color("#ffe5b4"), "crumb": Color("#e0a96d")},
]
const SFX := {
	"pop": preload("res://sfx/pop.wav"),
	"chomp": preload("res://sfx/chomp.wav"),
	"meow": preload("res://sfx/meow.wav"),
	"whoosh": preload("res://sfx/whoosh.wav"),
	"sparkle": preload("res://sfx/sparkle.wav"),
	"boing": preload("res://sfx/boing.wav"),
	"purr": preload("res://sfx/purr.wav"),
}
const PINKS := [Color("#ff8fab"), Color("#ffb3c6"), Color("#ff7aa2"), Color("#ffc2d1")]
const HUNGER_DECAY := 0.45   ## per second (fast, for testing)
const HAPPY_DECAY := 0.25

var hunger := 40.0
var happy := 55.0

var pet: Pet
var fx: Node2D
var hunger_bar: StatBar
var happy_bar: StatBar
var buttons: Array[FoodButton] = []
var music: AudioStreamPlayer
var bubble: Node2D

var _drag: Sprite2D = null
var _drag_food := 0
var _fake_mouse = null        ## Vector2 while the demo drives the pointer
var _pokes := []
var _meow_cooldown := 0.0
var _clock := 0.0


func _ready() -> void:
	randomize()
	var bg := TextureRect.new()
	bg.texture = preload("res://art/room.jpg")
	bg.set_anchors_preset(PRESET_FULL_RECT)
	bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bg.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	bg.mouse_filter = MOUSE_FILTER_IGNORE
	add_child(bg)

	pet = Pet.new()
	pet.position = Vector2(370, 905)
	add_child(pet)
	pet.chewed.connect(_on_chewed)
	pet.finished_eating.connect(_on_finished_eating)
	pet.hopped.connect(func(): _play("boing", 1.5, 1.8, -14.0))
	_build_bubble()

	_build_top_panel()
	_build_tray()

	fx = Node2D.new()
	add_child(fx)

	music = AudioStreamPlayer.new()
	var song: AudioStreamOggVorbis = preload("res://sfx/music.ogg")
	song.loop = true
	music.stream = song
	music.volume_db = -40.0
	add_child(music)
	music.play()
	create_tween().tween_property(music, "volume_db", -13.0, 2.5)

	if "--demo" in OS.get_cmdline_user_args():
		_demo()


func _process(delta: float) -> void:
	_clock += delta
	_meow_cooldown -= delta
	hunger = maxf(hunger - HUNGER_DECAY * delta, 0.0)
	happy = maxf(happy - HAPPY_DECAY * delta * (2.0 if hunger < 30.0 else 1.0), 0.0)
	hunger_bar.set_value(hunger)
	happy_bar.set_value(happy)
	pet.hunger = hunger

	if _drag:
		var p := _pointer() + Vector2(0, -50)
		var before := _drag.position
		_drag.position = _drag.position.lerp(p, 1.0 - exp(-delta * 22.0))
		_drag.rotation = lerpf(_drag.rotation, clampf((_drag.position.x - before.x) * 0.02, -0.5, 0.5), 0.2)

	# hungry thought bubble
	var want := 1.0 if hunger < 35.0 and not pet.eating else 0.0
	bubble.scale = bubble.scale.lerp(Vector2.ONE * want, 1.0 - exp(-delta * 10.0))
	bubble.position = Vector2(150, -470 + sin(_clock * 2.5) * 8.0)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if pet.hit(get_global_mouse_position()):
			_poke_pet()


# ---------------------------------------------------------------- feeding

func _on_button_down(b: FoodButton) -> void:
	_play("pop", 0.95, 1.15)


func _on_button_tapped(b: FoodButton) -> void:
	var s := _food_sprite(b.index, b.center_global())
	_toss(s, b.index)


func _on_drag_started(b: FoodButton) -> void:
	_drag = _food_sprite(b.index, b.center_global())
	_drag_food = b.index
	_drag.scale = Vector2.ONE * 0.5
	create_tween().tween_property(_drag, "scale", Vector2.ONE * 0.95, 0.35) \
		.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	pet.focus = _drag
	_play("pop", 1.3, 1.4, -6.0)


func _on_drag_ended(_b: FoodButton) -> void:
	var s := _drag
	_drag = null
	if s == null:
		return
	if pet.hit(s.position) or s.position.distance_to(pet.mouth_global()) < 180.0:
		var tw := create_tween()
		tw.tween_property(s, "position", pet.mouth_global(), 0.1)
		tw.parallel().tween_property(s, "scale", Vector2.ONE * 0.6, 0.1)
		tw.tween_callback(_arrive.bind(s, _drag_food))
	else:
		# dropped on the floor: shrink away
		pet.focus = null
		var tw := create_tween()
		tw.tween_property(s, "scale", Vector2.ZERO, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
		tw.tween_callback(s.queue_free)
		_play("pop", 0.7, 0.8, -6.0)


func _food_sprite(i: int, at: Vector2) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = FOODS[i].tex
	s.position = at
	s.scale = Vector2.ONE * 0.6
	fx.add_child(s)
	return s


func _toss(s: Sprite2D, i: int) -> void:
	_play("whoosh", 1.0, 1.3, -4.0)
	pet.focus = s
	var from := s.position
	var to := pet.mouth_global()
	var ctrl := (from + to) / 2.0 + Vector2(0, -420)
	var tw := create_tween()
	tw.tween_method(_fly.bind(s, from, ctrl, to), 0.0, 1.0, 0.6).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_callback(_arrive.bind(s, i))


func _fly(t: float, s: Sprite2D, from: Vector2, ctrl: Vector2, to: Vector2) -> void:
	s.position = from.lerp(ctrl, t).lerp(ctrl.lerp(to, t), t)
	s.rotation = t * TAU
	s.scale = Vector2.ONE * (0.6 + 0.45 * sin(t * PI) - 0.1 * t)


func _arrive(s: Sprite2D, i: int) -> void:
	if pet.focus == s:
		pet.focus = null
	if hunger >= 97.0:
		_refuse(s)
		return
	s.queue_free()
	var food: Dictionary = FOODS[i]
	_play("chomp", 0.95, 1.1)
	pet.eat()
	var m := pet.mouth_global()
	_burst(m, FxBit.Kind.DOT, 10, food.crumb, Vector2(6, 11), 420.0, 1500.0)
	hunger = minf(hunger + food.fill, 100.0)
	happy = minf(happy + food.fill * 0.3, 100.0)
	_float_text("+%d" % int(food.fill), m + Vector2(110, -40), Color("#ff6f91"))


func _refuse(s: Sprite2D) -> void:
	pet.refuse()
	_play("boing", 0.6, 0.7, -2.0)
	_float_text("I'm full!", pet.head_global() + Vector2(0, -20), Color("#8a6cff"))
	var side := -1.0 if randf() < 0.5 else 1.0
	var tw := create_tween().set_parallel()
	tw.tween_property(s, "position", s.position + Vector2(side * 260, 330), 0.55).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tw.tween_property(s, "rotation", side * 7.0, 0.55)
	tw.tween_property(s, "modulate:a", 0.0, 0.25).set_delay(0.3)
	tw.chain().tween_callback(s.queue_free)


func _on_chewed(bite: int) -> void:
	if bite > 0:
		_play("chomp", 1.15 + bite * 0.08, 1.3 + bite * 0.08, -9.0)
		_burst(pet.mouth_global(), FxBit.Kind.DOT, 4, Color("#fff3e0"), Vector2(4, 8), 300.0, 1500.0)


func _on_finished_eating() -> void:
	_play("sparkle", 1.0, 1.1, -6.0)
	_burst(pet.head_global(), FxBit.Kind.HEART, 6, Color.TRANSPARENT, Vector2(14, 24), 320.0, -120.0)
	_burst(pet.head_global(), FxBit.Kind.STAR, 8, Color("#fff4a3"), Vector2(8, 14), 520.0, 0.0)
	if _meow_cooldown <= 0.0:
		_meow_cooldown = 2.5
		get_tree().create_timer(0.25).timeout.connect(func(): _play("meow", 1.05, 1.2, -3.0))


# ---------------------------------------------------------------- petting

func _poke_pet() -> void:
	if pet.eating:
		return
	pet.poke()
	_play("boing", 1.0, 1.3, -4.0)
	happy = minf(happy + 4.0, 100.0)
	_burst(pet.head_global(), FxBit.Kind.HEART, 3, Color.TRANSPARENT, Vector2(12, 20), 260.0, -100.0)
	_pokes.append(_clock)
	_pokes = _pokes.filter(func(t): return _clock - t < 2.5)
	if _pokes.size() >= 5:
		_pokes.clear()
		pet.celebrate()
		_play("purr", 1.0, 1.0, -4.0)
		_play("sparkle", 1.2, 1.3, -8.0)
		_burst(pet.head_global(), FxBit.Kind.HEART, 12, Color.TRANSPARENT, Vector2(14, 26), 480.0, -150.0)
		_float_text("Love!", pet.head_global() + Vector2(0, -40), Color("#ff6f91"))
	elif _meow_cooldown <= 0.0 and randf() < 0.4:
		_meow_cooldown = 2.0
		_play("meow", 1.15, 1.35, -5.0)


# ---------------------------------------------------------------- building

func _build_top_panel() -> void:
	var panel := Panel.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(1, 1, 1, 0.55)
	sb.set_corner_radius_all(36)
	sb.shadow_color = Color(0.55, 0.3, 0.4, 0.15)
	sb.shadow_size = 12
	sb.shadow_offset = Vector2(0, 6)
	panel.add_theme_stylebox_override("panel", sb)
	panel.position = Vector2(24, 28)
	panel.size = Vector2(672, 190)
	panel.mouse_filter = MOUSE_FILTER_IGNORE
	add_child(panel)

	var title := Label.new()
	title.text = "Mochi"
	var ls := LabelSettings.new()
	ls.font_size = 46
	ls.font_color = Color("#ff6f91")
	ls.outline_size = 14
	ls.outline_color = Color.WHITE
	ls.shadow_color = Color(0.6, 0.3, 0.4, 0.25)
	ls.shadow_offset = Vector2(0, 4)
	title.label_settings = ls
	title.position = Vector2(36, 10)
	panel.add_child(title)

	hunger_bar = StatBar.new()
	hunger_bar.icon = FOODS[0].tex
	hunger_bar.fill_color = Color("#ffc46b")
	hunger_bar.value = hunger
	hunger_bar.position = Vector2(30, 76)
	hunger_bar.size = Vector2(300, 84)
	panel.add_child(hunger_bar)

	happy_bar = StatBar.new()
	happy_bar.fill_color = Color("#ff9ebb")
	happy_bar.value = happy
	happy_bar.position = Vector2(350, 76)
	happy_bar.size = Vector2(300, 84)
	panel.add_child(happy_bar)

	var mute := Button.new()
	mute.text = "Music: on"
	mute.flat = true
	mute.add_theme_font_size_override("font_size", 24)
	mute.add_theme_color_override("font_color", Color("#7a4b55"))
	mute.position = Vector2(500, 18)
	mute.focus_mode = FOCUS_NONE
	mute.pressed.connect(func():
		music.stream_paused = not music.stream_paused
		mute.text = "Music: off" if music.stream_paused else "Music: on"
		_play("pop", 1.2, 1.3))
	panel.add_child(mute)


func _build_tray() -> void:
	var tray := Panel.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(1, 1, 1, 0.6)
	sb.set_corner_radius_all(48)
	sb.shadow_color = Color(0.55, 0.3, 0.4, 0.18)
	sb.shadow_size = 14
	sb.shadow_offset = Vector2(0, -2)
	tray.add_theme_stylebox_override("panel", sb)
	tray.position = Vector2(20, 1050)
	tray.size = Vector2(680, 210)
	tray.mouse_filter = MOUSE_FILTER_IGNORE
	add_child(tray)
	for i in FOODS.size():
		var b := FoodButton.new()
		b.index = i
		b.texture = FOODS[i].tex
		b.color = FOODS[i].color
		b.label = FOODS[i].name
		b.position = Vector2(20 + i * 162, 22)
		b.size = Vector2(150, 170)
		b.pressed_down.connect(_on_button_down)
		b.tapped.connect(_on_button_tapped)
		b.drag_started.connect(_on_drag_started)
		b.drag_ended.connect(_on_drag_ended)
		tray.add_child(b)
		buttons.append(b)


func _build_bubble() -> void:
	bubble = Node2D.new()
	bubble.scale = Vector2.ZERO
	pet.add_child(bubble)
	bubble.draw.connect(func():
		bubble.draw_circle(Vector2(-70, 80), 12, Color(1, 1, 1, 0.9))
		bubble.draw_circle(Vector2(-45, 50), 18, Color(1, 1, 1, 0.9))
		bubble.draw_circle(Vector2(0, 0), 62, Color(0.6, 0.35, 0.45, 0.15))
		bubble.draw_circle(Vector2(0, -4), 60, Color.WHITE))
	var icon := Sprite2D.new()
	icon.texture = FOODS[0].tex
	icon.scale = Vector2.ONE * 0.36
	icon.position = Vector2(0, -6)
	bubble.add_child(icon)


# ---------------------------------------------------------------- juice

func _play(sound: String, pitch_lo := 1.0, pitch_hi := 1.0, db := 0.0) -> void:
	var p := AudioStreamPlayer.new()
	p.stream = SFX[sound]
	p.pitch_scale = randf_range(pitch_lo, pitch_hi)
	p.volume_db = db
	add_child(p)
	p.finished.connect(p.queue_free)
	p.play()


func _burst(at: Vector2, kind: FxBit.Kind, n: int, color: Color, size: Vector2, speed: float, gravity: float) -> void:
	for k in n:
		var b := FxBit.new()
		b.kind = kind
		b.color = PINKS.pick_random() if color.a == 0.0 else color
		b.size = randf_range(size.x, size.y)
		b.position = at + Vector2(randf_range(-30, 30), randf_range(-20, 20))
		var ang := randf_range(-PI * 0.85, -PI * 0.15)
		b.velocity = Vector2.from_angle(ang) * speed * randf_range(0.5, 1.0)
		b.gravity = gravity
		b.drag = 2.5 if kind != FxBit.Kind.DOT else 0.5
		b.spin = randf_range(-4, 4) if kind == FxBit.Kind.STAR else 0.0
		b.life = randf_range(0.8, 1.3)
		b.scale = Vector2.ZERO
		fx.add_child(b)


func _float_text(text: String, at: Vector2, color: Color) -> void:
	var l := Label.new()
	l.text = text
	var ls := LabelSettings.new()
	ls.font_size = 52
	ls.font_color = color
	ls.outline_size = 14
	ls.outline_color = Color.WHITE
	l.label_settings = ls
	add_child(l)
	l.reset_size()
	l.pivot_offset = l.size / 2.0
	l.position = at - l.size / 2.0
	l.scale = Vector2.ZERO
	var tw := create_tween()
	tw.tween_property(l, "scale", Vector2.ONE, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.parallel().tween_property(l, "position:y", l.position.y - 110, 1.1).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tw.parallel().tween_property(l, "modulate:a", 0.0, 0.35).set_delay(0.75)
	tw.tween_callback(l.queue_free)


func _pointer() -> Vector2:
	return _fake_mouse if _fake_mouse != null else get_global_mouse_position()


# ---------------------------------------------------------------- demo

func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func _demo_tap(i: int) -> void:
	buttons[i].squish()
	_on_button_down(buttons[i])
	await _wait(0.12)
	_on_button_tapped(buttons[i])


func _demo() -> void:
	await _wait(1.6)
	await _demo_tap(0)
	await _wait(2.4)
	for k in 6:
		_poke_pet()
		await _wait(0.32)
	await _wait(1.8)
	# drag the cake into the mouth
	var b := buttons[1]
	buttons[1].squish()
	_on_button_down(b)
	_fake_mouse = b.center_global()
	_on_drag_started(b)
	var tw := create_tween()
	tw.tween_property(self, "_fake_mouse", pet.mouth_global() + Vector2(40, 60), 1.0).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	await tw.finished
	await _wait(0.3)
	_drag.position = pet.mouth_global()
	_on_drag_ended(b)
	_fake_mouse = null
	await _wait(2.4)
	await _demo_tap(2)
	await _wait(2.2)
	await _demo_tap(3)
	await _wait(2.2)
	await _demo_tap(0)
	await _wait(2.5)
