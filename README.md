# Decompile Bot — versión actualizada

Bot de Discord en Python. Incluye:
- `/help`
- `/game universe_id`: metadatos públicos de Roblox.
- `/analyze archivo`: informe estático básico de `.lua` / `.luau`, enviado por DM.
- `/decompile link`: recibe un enlace público de Roblox y envía por DM la información pública del juego.

## Importante
El comando `/decompile` solo acepta un enlace público de un juego de Roblox y consulta datos públicos como el nombre, descripción, creador, visitas y jugadores activos. No descarga archivos, no extrae scripts ni revela el código privado del juego. No utiliza cookies `.ROBLOSECURITY`.

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
- `/decompile link:https://www.roblox.com/games/123456789/Nombre` → consulta información pública y la envía por DM.
- `/analyze archivo:script.luau` → devuelve por DM un informe.
- `/game universe_id:123456789` → consulta metadatos públicos.

El comando `/analyze` sigue aceptando scripts `.lua`/`.luau` como adjuntos para realizar un análisis estático básico.
