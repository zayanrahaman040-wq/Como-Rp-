import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from openai import OpenAI

TOKEN = os.getenv("TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client_ai = OpenAI(api_key=OPENAI_KEY)

LOG_CHANNEL_ID = 1574465040336035940  # <-- il tuo canale log ticket

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TICKET_CATEGORIE = [
    ("Assistenza Generale", "Hai un problema in game? Apri qui!", "🎧"),
    ("Assistenza Game", "Problemi dentro il gioco, lag, bug RP", "🎮"),
    ("Richiesta CEO", "Vuoi parlare con il CEO? Apri qui!", "👑"),
    ("Richiesta Fondatore", "Vuoi parlare con il Fondatore?", "🏛️"),
    ("Richiesta Medico", "Vuoi parlare con il Medico / Capo Medico?", "🩺"),
    ("Partnership", "Vuoi fare Partnership con 118 RP?", "🤝"),
    ("Segnalazione Utente", "Segnala un utente per FailRP o troll", "🚨"),
    ("Segnalazione Bug", "Hai trovato un bug? Segnalalo qui", "🐛"),
    ("Richiesta Sban", "Sei stato bannato? Richiedi sban", "🔓"),
    ("Richiesta Staff", "Vuoi entrare nello Staff?", "🛡️"),
    ("Richiesta Ruolo", "Vuoi un ruolo o cambio ruolo?", "🎖️"),
    ("Problema Pagamento", "Problemi con pagamenti / donazioni", "💳"),
    ("Problema Account", "Problemi con account Roblox / Discord", "👤"),
    ("Problema Voice / Lag", "Non senti in voice? Lag?", "🔊"),
    ("Denuncia FailRP", "Denuncia FailRP con prove", "⚖️"),
    ("Richiesta Rimborso", "Hai perso oggetti per bug? Richiedi rimborso", "💰"),
    ("Idea / Suggerimento", "Hai un'idea per migliorare il server?", "💡"),
    ("Richiesta Evento", "Vuoi proporre un evento RP?", "🎉"),
    ("Richiesta Clan / Gang", "Vuoi creare una gang / clan?", "👥"),
    ("Altro / Altro Problema", "Altro problema non elencato", "❓"),
]

ticket_counter = 0
ticket_aperti = {}
# Per ricordare categoria e chi ha aperto: channel_id -> info
ticket_info = {}

async def manda_log(guild, embed):
    canale_log = guild.get_channel(LOG_CHANNEL_ID)
    if canale_log:
        await canale_log.send(embed=embed)

class TicketButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.green, emoji="✋")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Solo lo Staff può claimmare!", ephemeral=True)
            return
        button.disabled = True
        button.label = f"Claimato da {interaction.user.name}"
        await interaction.response.send_message(f"✅ Ticket claimato da {interaction.user.mention}!")
        await interaction.message.edit(view=self)
        # LOG CLAIM
        info = ticket_info.get(interaction.channel.id, {})
        embed = discord.Embed(title="✋ Ticket Claimato", description=f"**Canale:** {interaction.channel.name}\n**Claimato da:** {interaction.user.mention}\n**Aperto da:** <@{info.get('user_id')}>\n**Categoria:** {info.get('categoria')}", color=0x2ECC71)
        await manda_log(interaction.guild, embed)

    @discord.ui.button(label="Chiudi", style=discord.ButtonStyle.red, emoji="🔒")
    async def chiudi(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = None
        for uid, cid in list(ticket_aperti.items()):
            if cid == interaction.channel.id:
                user_id = uid
                break
        if interaction.user.id != user_id and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Solo tu o lo Staff potete chiudere!", ephemeral=True)
            return

        # LOG CHIUSURA - prima di cancellare
        info = ticket_info.get(interaction.channel.id, {})
        embed = discord.Embed(title="🔒 Ticket Chiuso", description=f"**Canale:** {interaction.channel.name}\n**Chiuso da:** {interaction.user.mention}\n**Aperto da:** <@{info.get('user_id')}>\n**Categoria:** {info.get('categoria')}", color=0xE74C3C)
        await manda_log(interaction.guild, embed)

        await interaction.response.send_message("🔒 Ticket chiuso! Cancello SOLO questo canale in 5 secondi...")
        await asyncio.sleep(5)
        if user_id in ticket_aperti:
            del ticket_aperti[user_id]
        if interaction.channel.id in ticket_info:
            del ticket_info[interaction.channel.id]
        try:
            await interaction.channel.delete()
        except:
            pass

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = []
        for nome, desc, emoji in TICKET_CATEGORIE:
            options.append(discord.SelectOption(label=nome, description=desc[:100], emoji=emoji, value=nome))
        super().__init__(placeholder="Clicca e scegli la categoria ticket...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        global ticket_counter
        user = interaction.user
        if user.id in ticket_aperti:
            canale_vecchio = interaction.guild.get_channel(ticket_aperti[user.id])
            if canale_vecchio:
                await interaction.response.send_message(f"❌ Hai già un ticket aperto! Vai in {canale_vecchio.mention} e chiudilo prima di aprirne un altro.", ephemeral=True)
                return
            else:
                del ticket_aperti[user.id]

        ticket_counter += 1
        scelta = self.values[0]
        guild = interaction.guild
        categoria = discord.utils.get(guild.categories, name="🎫 ─ TICKET")
        if not categoria:
            categoria = await guild.create_category("🎫 ─ TICKET")
        nome_canale = f"ticket-{user.name}-{ticket_counter}".lower().replace(" ", "-")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        canale = await guild.create_text_channel(nome_canale, category=categoria, overwrites=overwrites)
        ticket_aperti[user.id] = canale.id
        ticket_info[canale.id] = {"user_id": user.id, "categoria": scelta}

        embed = discord.Embed(title=f"🎫 Ticket - {scelta}", description=f"Ciao {user.mention}!\n\n**Categoria:** {scelta}\n\n**Scrivi qui:**\n- Nome Roblox:\n- Spiega il problema:\n- Foto / video se hai\n\nUno staffer ti risponderà presto!", color=0x3498DB)
        await canale.send(embed=embed, view=TicketButtons())
        await interaction.response.send_message(f"✅ Ticket creato! Vai in {canale.mention}", ephemeral=True)

        # LOG APERTURA
        embed_log = discord.Embed(title="🎫 Ticket Aperto", description=f"**Canale:** {canale.mention}\n**Aperto da:** {user.mention} ({user.id})\n**Categoria:** {scelta}", color=0x3498DB)
        await manda_log(guild, embed_log)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

@bot.event
async def on_ready():
    print(f"Bot online {bot.user}")
    await bot.tree.sync()
    print("Comandi /ticket e /ai pronti")

@bot.event
async def on_guild_channel_delete(channel):
    for uid, cid in list(ticket_aperti.items()):
        if cid == channel.id:
            del ticket_aperti[uid]
    if channel.id in ticket_info:
        del ticket_info[channel.id]

@bot.tree.command(name="ticket", description="Apri il pannello ticket")
async def ticket(interaction: discord.Interaction):
    embed = discord.Embed(title="🎫 Apri un Ticket - 118 RP", description="Clicca in basso e scegli la categoria!\n\nHai 20 categorie: Assistenza, CEO, Medico, Partnership, Segnalazioni e altro.", color=0x3498DB)
    await interaction.response.send_message(embed=embed, view=TicketView())

@bot.tree.command(name="ai", description="Chiedi qualsiasi cosa all'AI")
@app_commands.describe(domanda="Scrivi la tua domanda")
async def ai(interaction: discord.Interaction, domanda: str):
    await interaction.response.defer()
    try:
        resp = client_ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Sei l'AI di 118 RP, un server Roblox RP italiano. Rispondi in italiano, corto, simpatico e utile. Aiuti con RP, regole, ticket, staff."},
                {"role": "user", "content": domanda}
            ]
        )
        risposta = resp.choices[0].message.content
        await interaction.followup.send(f"🤖 **Tu:** {domanda}\n\n{risposta[:1900]}")
    except Exception as e:
        await interaction.followup.send(f"❌ Errore AI: {e}\nControlla OPENAI_API_KEY su Railway!")

bot.run(TOKEN)
