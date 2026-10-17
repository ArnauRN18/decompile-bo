# Decompile Bot — versión actualizada

Bot de Discord en Python. Incluye:
- `/help`
- `/game universe_id`: metadatos públicos de Roblox.
- `/analyze archivo`: informe estático básico de `.lua` / `.luau`, enviado por DM.
- `/decompile archivo`: recibe un `.rbxlx` autorizado, conserva únicamente los servicios principales `Workspace` y `ReplicatedStorage`, y envía el archivo filtrado por DM.

## Importante sobre los formatos
Esta versión genera `workspace_replicatedstorage.rbxlx`, no un `.rbxl` binario. RBXLX es el formato XML de Roblox Studio. No renombres el archivo a `.rbxl`, porque eso no lo convierte a formato binario.

No se puede recuperar el archivo completo de un juego privado usando solo el enlace público. El comando `/decompile` necesita que adjuntes un `.rbxlx` que tengas permiso para procesar. No utiliza cookies `.ROBLOSECURITY` ni extrae código privado de experiencias ajenas.

## Discord Developer Portal
1. Ve a https://discord.com/developers/applications y crea una aplicación.
2. En la sección **Bot**, crea el bot y copia el token.
3. En **Installation** / OAuth2, habilita `bot` y `applications.commands`.
4. Invítalo al servidor con permisos mínimos para enviar mensajes y adjuntar archivos.
5. Nunca compartas el token ni lo subas al repositorio.

## Hosting
Configura un worker Python persistente:
- Build command: `pip install -r requirements.txt`
- Start command: `python bot.py`
- Variable secreta requerida: `DISCORD_TOKEN`
- Variable opcional: `GUILD_ID` (ID del servidor de prueba para sincronizar comandos más rápido)

Un plan gratuito puede suspender procesos o no permitir workers persistentes. Verifica las condiciones actuales del proveedor para disponibilidad real 24/7.

## Ejecutar en Windows
1. Instala Python 3.11 o 3.12.
2. En PowerShell, abre esta carpeta.
3. `py -m venv .venv`
4. `.\.venv\Scripts\Activate.ps1`
5. `pip install -r requirements.txt`
6. `$env:DISCORD_TOKEN="TU_TOKEN"`
7. Opcional: `$env:GUILD_ID="ID_DE_TU_SERVIDOR"`
8. `python bot.py`

## Uso
- `/decompile archivo:mi_juego.rbxlx` → devuelve por DM un `.rbxlx` con `Workspace` y `ReplicatedStorage`.
- `/analyze archivo:script.luau` → devuelve por DM un informe.
- `/game universe_id:123456789` → consulta metadatos públicos.

El bot procesa los adjuntos en memoria y no los guarda deliberadamente en disco. El usuario debe tener permiso para subir y procesar el archivo.
