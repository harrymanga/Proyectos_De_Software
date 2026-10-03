# GDRE i18n (local integration).
# Setup: gdre_main.gd creates the node in _ready (see _setup_i18n).
extends Node
class_name GDREI18n

const LOCALE_DIR := "res://locale/overlay/"
const CFG_PATH := "user://gdre_i18n.cfg"

var current_locale := "en"
var texts := {}


func _ready() -> void:
	_load_preferences()
	apply_language(current_locale)


func _load_preferences() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(CFG_PATH) == OK:
		# New English key with fallback to legacy Spanish key.
		if cfg.has_section_key("ui", "language"):
			current_locale = str(cfg.get_value("ui", "language", "en"))
		else:
			current_locale = str(cfg.get_value("ui", "idioma", "en"))


func _save_preferences() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("ui", "language", current_locale)
	cfg.save(CFG_PATH)


func _parse_csv(path: String) -> Dictionary:
	var out := {}
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return out
	var first := true
	while not file.eof_reached():
		var line := file.get_csv_line()
		if first:
			first = false
			continue
		if line.size() >= 3 and line[0].strip_edges() != "":
			out[line[1]] = line[2]
	return out


func apply_language(code: String) -> void:
	if code == "en":
		texts = {}
		current_locale = code
		_save_preferences()
		return
	var path := LOCALE_DIR + code + ".csv"
	if not FileAccess.file_exists(path):
		push_warning("GDREI18n: missing CSV for '" + code + "'")
		return
	texts = _parse_csv(path)
	# Note: Godot imports the CSV to .translation when opening the project;
	# here the already imported translation is loaded when available.
	var translation_path := LOCALE_DIR + code + ".translation"
	if FileAccess.file_exists(translation_path):
		var translation := load(translation_path) as Translation
		if translation:
			TranslationServer.add_translation(translation)
	current_locale = code
	_save_preferences()


func translate(source: String) -> String:
	var target: String = texts.get(source, "")
	return target if target.strip_edges() != "" else source


# Walk a subtree translating static texts (buttons, labels, window
# titles, foldable titles, option items, tooltips). Keep originals in
# `memory` to switch en/es. Skip user input and dynamic content
# (LineEdit, TextEdit, Tree, ItemList, file containers).
func translate_interface(root: Node, memory: Dictionary) -> void:
	_walk(root, memory)


func _walk(node: Node, memory: Dictionary) -> void:
	# MenuButtons are handled by _translate_menus (with their popups, which
	# are not nodes): touching them here would freeze translated texts.
	if node is MenuButton:
		return
	var key := str(node.get_path())
	if node is LineEdit or node is TextEdit:
		# User content stays untouched, but chrome placeholders translate.
		var placeholder: Variant = node.get("placeholder_text")
		if placeholder is String and placeholder.strip_edges() != "":
			_save_and_restore(memory, key + "#placeholder", node, "placeholder_text")
		return
	# Dialog button properties (AcceptDialog/ConfirmationDialog and custom
	# derivatives): translated before the container early-out below.
	var ok_text: Variant = node.get("ok_button_text")
	if ok_text is String and ok_text.strip_edges() != "":
		_save_and_restore(memory, key + "#ok", node, "ok_button_text")
	var cancel_text: Variant = node.get("cancel_button_text")
	if cancel_text is String and cancel_text.strip_edges() != "":
		_save_and_restore(memory, key + "#cancel", node, "cancel_button_text")
	if node is Tree or node is ItemList or node is FileDialog:
		return
	if node is Window:
		_save_and_restore(memory, key + "#title", node, "title")
	elif node is OptionButton:
		_translate_option_items(node, memory)
	elif node is BaseButton or node is Label:
		_save_and_restore(memory, key + "#text", node, "text")
	elif node is RichTextLabel and node.bbcode_enabled:
		# BBCode labels are static templates (placeholders like
		# <LOG_FILE_URI> survive in every locale). Plain RichTextLabels
		# hold live logs and must keep their runtime content.
		_save_and_restore(memory, key + "#text", node, "text")
	else:
		# Duck-typed title (e.g. FoldableContainer): no parse-time
		# dependency on custom engine classes.
		var title_value: Variant = node.get("title")
		if title_value is String and title_value.strip_edges() != "":
			_save_and_restore(memory, key + "#title", node, "title")
	if node is Control:
		var tip: Variant = node.get("tooltip_text")
		if tip is String and tip.strip_edges() != "":
			_save_and_restore(memory, key + "#tip", node, "tooltip_text")
	for child in node.get_children():
		_walk(child, memory)


func _translate_option_items(option: OptionButton, memory: Dictionary) -> void:
	var key := str(option.get_path())
	for i in range(option.item_count):
		var item_key := key + "#item_" + str(i)
		if not memory.has(item_key):
			memory[item_key] = option.get_item_text(i)
		var original: String = memory[item_key]
		option.set_item_text(i, translate(original))
	# Keep the button text in sync with the current selection so a
	# selection change under a non-English locale never fossilizes text.
	var selected := option.selected
	if selected >= 0 and selected < option.item_count:
		var selected_key := key + "#item_" + str(selected)
		var selected_original: String = memory.get(selected_key, option.get_item_text(selected))
		option.text = translate(selected_original)


func _save_and_restore(memory: Dictionary, key: String, node: Object, prop: String) -> void:
	if not memory.has(key):
		memory[key] = node.get(prop)
	var original: String = memory[key]
	node.set(prop, translate(original))
