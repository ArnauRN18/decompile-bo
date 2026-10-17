import os
import io
import re
from datetime import datetime, timezone

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
GUILD_ID = os.getenv("GUILD_ID", "").strip()
MAX_FILE_BYTES = 8 * 1024 * 1024  # 8 MiB; raise only if your host allows it
MAX_TEXT_CHARS = 150_000

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

SUSPICIOUS_PATTERNS = [
    (r"\bloadstring\s*\(", "loadstring(): ejecuta código dinámico; revisa cuidadosamente su origen."),
    (r"\bHttpService\b", "HttpService: puede realizar solicitudes HTTP si el contexto lo permite."),
    (r"\bgetfenv\s*\(", "getfenv(): acceso al entorno de ejecución; comprueba por qué se usa."),
    (r"\bsetfenv\s*\(", "setfenv(): modifica el entorno de ejecución; comprueba por qué se usa."),
    (r"\brequire\s*\(\s*\d+", "require(ID): carga un módulo por ID; verifica que sea confiable."),
]

def analyze_source(source: str) -> str:
    findings = []
    for pattern, description in SUSPICIOUS_PATTERNS:
        matches = list(re.finditer(pattern, source, flags=re.IGNORECASE))
        if matches:
            lines = sorted({source.count("\n", 0, m.start()) + 1 for m in matches})
            findings.append(f"- Línea(s) {', '.join(map(str, lines[:20]))}: {description}")
    summary = [
        "## Informe de análisis Luau",
        f"- Líneas: {source.count(chr(10)) + 1}",
        f"- Caracteres: {len(source)}",
        f"- Analizado (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "### Patrones para revisar",
    ]
    summary.extend(findings or ["No se detectaron los patrones sencillos configurados. Esto no garantiza que el código sea seguro."])
    summary += ["", "Análisis estático básico; no ejecuta el código y puede producir falsos positivos o no detectar problemas."]
    return "\n".join(summary)

async def read_attachment(attachment: discord.Attachment) -> bytes:
    if attachment.size > MAX_FILE_BYTES:
        raise ValueError(f"El archivo supera el límite de {MAX_FILE_BYTES // (1024 * 1024)} MiB.")
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(attachment.url) as response:
            if response.status != 200:
                raise ValueError("No se pudo descargar el archivo adjunto.")
            data = await response.read()
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(f"El archivo supera el límite de {MAX_FILE_BYTES // (1024 * 1024)} MiB.")
    return data

async def dm_file(interaction: discord.Interaction, filename: str, data: bytes, message: str):
    discord_file = discord.File(io.BytesIO(data), filename=filename)
    try:
        await interaction.user.send(content=message, file=discord_file)
    except discord.Forbidden:
        await interaction.followup.send(
            "No puedo enviarte un DM. Activa los mensajes directos de miembros del servidor e inténtalo otra vez.",
            ephemeral=True,
        )
        return
    await interaction.followup.send("¡Listo! Te he enviado el archivo por mensaje privado (DM).", ephemeral=True)

@bot.event
async def on_ready():
    try:
        if GUILD_ID.isdigit():
            guild = discord.Object(id=int(GUILD_ID))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"Conectado como {bot.user}; {len(synced)} comandos sincronizados en el servidor {GUILD_ID}.")
        else:
            synced = await bot.tree.sync()
            print(f"Conectado como {bot.user}; {len(synced)} comandos globales sincronizados.")
    except Exception as exc:
        print(f"Error sincronizando comandos: {exc}")

@bot.tree.command(name="help", description="Muestra la ayuda del Decompile Bot.")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Decompile Bot — Ayuda",
        description="Consulta información pública de experiencias de Roblox mediante un enlace.",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="/game universe_id", value="Consulta información pública de una experiencia.", inline=False)
    embed.add_field(name="/analyze archivo", value="Analiza un archivo .lua o .luau.", inline=False)
    embed.add_field(name="/decompile link", value="Consulta información pública de un juego usando su enlace de Roblox y te la envía por DM.", inline=False)
    embed.add_field(name="Importante", value="El enlace permite consultar datos públicos; no descarga ni revela scripts privados del juego.", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="game", description="Consulta información pública de una experiencia de Roblox.")
@app_commands.describe(universe_id="Universe ID numérico (no Place ID).")
async def game_command(interaction: discord.Interaction, universe_id: str):
    if not universe_id.isdigit():
        await interaction.response.send_message("El Universe ID debe ser numérico.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get("https://games.roblox.com/v1/games", params={"universeIds": universe_id}) as response:
                if response.status != 200:
                    await interaction.followup.send(f"Roblox respondió con HTTP {response.status}.", ephemeral=True)
                    return
                payload = await response.json()
        games = payload.get("data", [])
        if not games:
            await interaction.followup.send("No se encontró información pública para ese Universe ID.", ephemeral=True)
            return
        game = games[0]
        embed = discord.Embed(
            title=str(game.get("name", "Experiencia de Roblox"))[:256],
            url=f"https://www.roblox.com/games/{game.get('rootPlaceId', '')}",
            description=(game.get("description") or "Sin descripción pública.")[:4000],
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Universe ID", value=str(game.get("id", universe_id)), inline=True)
        embed.add_field(name="Place ID principal", value=str(game.get("rootPlaceId", "No disponible")), inline=True)
        embed.add_field(name="Jugadores activos", value=str(game.get("playing", "No disponible")), inline=True)
        embed.add_field(name="Visitas", value=str(game.get("visits", "No disponible")), inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)
    except (aiohttp.ClientError, TimeoutError):
        await interaction.followup.send("No se pudo consultar Roblox en este momento.", ephemeral=True)

@bot.tree.command(name="analyze", description="Analiza un script Luau/Lua autorizado.")
@app_commands.describe(archivo="Archivo .lua o .luau")
async def analyze_command(interaction: discord.Interaction, archivo: discord.Attachment):
    if not archivo.filename.lower().endswith((".lua", ".luau")):
        await interaction.response.send_message("Adjunta un archivo .lua o .luau.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        raw = await read_attachment(archivo)
        source = raw.decode("utf-8", errors="replace")[:MAX_TEXT_CHARS]
        data = analyze_source(source).encode("utf-8")
        await dm_file(interaction, "informe_luau.txt", data, "Aquí tienes el informe del script que subiste.")
    except ValueError as exc:
        await interaction.followup.send(str(exc), ephemeral=True)
    except Exception as exc:
        await interaction.followup.send(f"No se pudo analizar el archivo ({exc.__class__.__name__}).", ephemeral=True)

@bot.tree.command(name="decompile", description="Consulta información pública de un juego de Roblox por su enlace.")
@app_commands.describe(link="Enlace público del juego, por ejemplo https://www.roblox.com/games/123456789/Nombre")
async def decompile_command(interaction: discord.Interaction, link: str):
    match = re.search(r"(?:https?://)?(?:www\.)?roblox\.com/games/(\d+)", link.strip(), flags=re.IGNORECASE)
    if not match:
        await interaction.response.send_message(
            "No reconozco ese enlace. Pega un enlace de juego como https://www.roblox.com/games/123456789/Nombre-del-juego",
            ephemeral=True,
        )
        return

    place_id = match.group(1)
    await interaction.response.defer(ephemeral=True, thinking=True)
    timeout = aiohttp.ClientTimeout(total=20)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Resolve the public place ID to its universe ID.
            async with session.get(f"https://apis.roblox.com/universes/v1/places/{place_id}/universe") as response:
                if response.status != 200:
                    await interaction.followup.send(
                        f"Roblox no pudo resolver ese juego (HTTP {response.status}). Comprueba el enlace e inténtalo de nuevo.",
                        ephemeral=True,
                    )
                    return
                universe_payload = await response.json()
            universe_id = universe_payload.get("universeId")
            if not universe_id:
                await interaction.followup.send("No encontré información pública para ese enlace.", ephemeral=True)
                return

            async with session.get(
                "https://games.roblox.com/v1/games", params={"universeIds": str(universe_id)}
            ) as response:
                if response.status != 200:
                    await interaction.followup.send(
                        f"Roblox no pudo devolver los datos del juego (HTTP {response.status}).",
                        ephemeral=True,
                    )
                    return
                payload = await response.json()

        games = payload.get("data", [])
        if not games:
            await interaction.followup.send("No se encontró información pública para ese juego.", ephemeral=True)
            return

        game = games[0]
        embed = discord.Embed(
            title=str(game.get("name", "Experiencia de Roblox"))[:256],
            url=f"https://www.roblox.com/games/{game.get('rootPlaceId', place_id)}",
            description=(game.get("description") or "Sin descripción pública.")[:4000],
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Creador", value=str((game.get("creator") or {}).get("name", "No disponible"))[:1024], inline=True)
        embed.add_field(name="Universe ID", value=str(game.get("id", universe_id)), inline=True)
        embed.add_field(name="Place ID", value=str(game.get("rootPlaceId", place_id)), inline=True)
        embed.add_field(name="Jugadores activos", value=str(game.get("playing", "No disponible")), inline=True)
        embed.add_field(name="Visitas", value=str(game.get("visits", "No disponible")), inline=True)
        embed.set_footer(text="Solo información pública; no se descargan archivos ni scripts del juego.")

        try:
            await interaction.user.send(embed=embed)
            await interaction.followup.send("¡Listo! Te he enviado la información pública del juego por mensaje privado (DM).", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send(
                "No puedo enviarte un DM. Activa los mensajes directos de miembros del servidor e inténtalo otra vez.",
                ephemeral=True,
            )
    except (aiohttp.ClientError, TimeoutError):
        await interaction.followup.send("No se pudo consultar Roblox en este momento. Inténtalo de nuevo más tarde.", ephemeral=True)

if not DISCORD_TOKEN:
    raise RuntimeError("Falta la variable de entorno DISCORD_TOKEN. Configúrala en el hosting.")
bot.run(DISCORD_TOKEN)
