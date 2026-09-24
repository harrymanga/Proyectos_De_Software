import json

# Nombre del archivo JSON de entrada
json_file = 'enlaces_zip.json'

# Nombre del archivo de salida
output_file = 'comandos_curl.sh'

# Cargar los datos del archivo JSON
def load_json_data(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Generar las líneas de comandos curl
def generate_curl_commands(data):
    commands = []
    for file_name, url in data.items():
        commands.append(f'curl -OL {url}')
    return commands

# Guardar los comandos en un archivo de texto
def save_commands_to_file(commands, file_path):
    with open(file_path, 'w') as file:
        file.write('\n'.join(commands))

# Proceso principal
try:
    # Cargar los datos del JSON
    data = load_json_data(json_file)

    # Generar comandos curl
    curl_commands = generate_curl_commands(data)

    # Guardar los comandos en un archivo
    save_commands_to_file(curl_commands, output_file)

    print(f"Se han generado {len(curl_commands)} comandos curl en el archivo {output_file}.")
except Exception as e:
    print(f"Error: {e}")
