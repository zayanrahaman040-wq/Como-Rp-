import discord
from discord.ext import commands
from discord import app_commands
import os
import random
from openai import OpenAI

TOKEN = os.getenv("TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client_ai = OpenAI(api_key=OPENAI_KEY)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- 20 CATEGORIE TICKET ---
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

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = []
        for nome, desc, emoji in TICKET_CATEGORIE:
            options.append(discord.SelectOption(label=nome, description=desc[:100], emoji=emoji, value=nome))
        super().__init__(placeholder="Clicca e scegli la categoria ticket...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        global ticket_counter
        ticket_counter += 1
        scelta = self.values[0]
        guild = interaction.guild
        user = interaction.user

        # Cerca o crea categoria TICKET
        categoria = discord.utils.get(guild.categories, name="🎫 ─ TICKET")
        if not categoria:
            categoria = await guild.create_category("🎫 ─ TICKET")

        nome_canale = f"ticket-{user.name}-{ticket_counter}".lower().replace(" ", "-")
        # Permessi: solo tu + staff vedono
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        canale = await guild.create_text_channel(nome_canale, category=categoria, overwrites=overwrites)
        await canale.send(f"👋 Ciao {user.mention}! Hai aperto un ticket per **{scelta}**\n\n**Scrivi qui:**\n- Nome Roblox:\n- Spiega il problema:\n- Foto / video se hai\n\nUno staffer ti risponderà presto!")
        await interaction.response.send_message(f"✅ Ticket creato! Vai in {canale.mention}", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

@bot.event
async def on_ready():
    print(f"Bot online {bot.user}")
    await bot.tree.sync()
    print("Comandi /ticket e /ai pronti")

@bot.tree.command(name="ticket", description="Apri il pannello ticket")
async def ticket(interaction: discord.Interaction):
    embed = discord.Embed(title="🎫 Apri un Ticket - 118 RP", description="Clicca in basso e scegli la categoria!\n\nHai 20 categorie: Assistenza, CEO, Medico, Partnership, Segnalazioni e altro.", color=0x3498DB)
    await interaction.response.send_message(embed=embed, view=TicketView())

# --- AI COME CHATGPT ---
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
