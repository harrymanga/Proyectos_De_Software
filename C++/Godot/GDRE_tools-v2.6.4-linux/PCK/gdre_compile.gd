class_name GDRECompile
extends GDRECompDecomp


func _tr(source: String) -> String:
	var i18n_node: Node = get_tree().get_first_node_in_group("gdre_i18n")
	if i18n_node != null and i18n_node.has_method("translate"):
		return i18n_node.translate(source)
	return source



func confirm():
	var selector:OptionButton = %BytecodeSelector
	var bytecode_str = selector.get_item_text( selector.get_selected_id())
	var bytecode_version = bytecode_str.split(" ", false, 1)[0].strip_edges()
	var decomp = GDScriptDecomp.create_decomp_for_version(bytecode_version)
	if decomp == null:
		popup_error_box(_tr("Failed to create decompiler for version: ") + bytecode_version, _tr("Decompiler Error"))
		return
	var files = get_file_list()
	if files.size() == 0:
		popup_error_box(_tr("No files selected"), "Error")
		return
	var dest_folder = %DestinationFolder.text
	if dest_folder == "":
		popup_error_box(_tr("No destination folder selected"), "Error")
		return
	for file in files:
		var code_string = FileAccess.get_file_as_string(file)
		if code_string.is_empty():
			popup_error_box(_tr("Failed to read file: ") + file, _tr("File Error"))
			return
		var compiled = decomp.compile_code_string(code_string)
		if compiled.is_empty():
			popup_error_box(_tr("Failed to compile file: ") + file, _tr("Compile Error"))
			return
		var dest_file = dest_folder.path_join(file.get_file().get_basename() + ".gdc")
		var f = FileAccess.open(dest_file, FileAccess.WRITE)
		if f == null:
			popup_error_box(_tr("Failed to open file for writing: ") + dest_file, _tr("File Error"))
			return
		f.store_buffer(compiled)
		f.close()
	popup_confirm_box(_tr("The following files were successfully compiled: ") + "\n".join(files), _tr("Compile Complete"), self.close, self.close)
