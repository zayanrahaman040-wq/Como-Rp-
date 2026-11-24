# ================= MAIN.PY - CASTREZZATO RP BOT =================
import os
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
import asyncio

# ---------- CONFIG ----------
TOKEN = os.getenv("DISCORD_TOKEN")  # Metti il token nelle variabili d'ambiente
OPENAI_KEY = os.getenv("OPENAI_KEY")  # Per /ai se lo usi
CHECK_PASSWORD = os.getenv("CHECK_PASSWORD", "INSERISCI_QUI_LA_TUA_PASSWORD")
TICKET_PASSWORD = os.getenv("TICKET_PASSWORD", "INSERISCI_QUI_LA_TUA_PASSWORD")
AI_PASSWORD = os.getenv("AI_PASSWORD", "INSERISCI_QUI_LA_TUA_PASSWORD")

# ID TUOI - CAMBIALI
ZAYAN_ID = 0  # Metti il tuo ID Discord qui
GUILD_ID = 0  # Metti ID server Castrezzato RP (opzionale)
TICKET_CATEGORY_ID = 0  # ID categoria dove aprire i ticket
STAFF_ROLE_ID = 0  # ID ruolo Staff

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= ON READY =================
@bot.event
async def on_ready():
    print(f"✅ Bot online come {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Sincronizzati {len(synced)} comandi slash")
    except Exception as e:
        print(f"❌ Errore sync: {e}")

# ================= TICKET =================
class TicketModal(Modal, title="Apri un Ticket"):
    motivo = TextInput(label="Motivo del ticket", placeholder="Scrivi il motivo...", max_length=200)
    dettagli = TextInput(label="Dettagli", placeholder="Spiega bene il problema...", style=discord.TextStyle.paragraph, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID) if TICKET_CATEGORY_ID != 0 else None
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        if STAFF_ROLE_ID != 0:
            role = guild.get_role(STAFF_ROLE_ID)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title=f"🎫 Ticket di {interaction.user.display_name}",
            description=f"**Motivo:** {self.motivo.value}\n\n**Dettagli:**\n{self.dettagli.value}",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Castrezzato RP | Ticket System")
        await channel.send(f"<@{interaction.user.id}>", embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket aperto: {channel.mention}", ephemeral=True)

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Chiudi Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔒 Ticket in chiusura tra 5 secondi...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Apri Ticket", style=discord.ButtonStyle.blurple, custom_id="open_ticket")
    async def open_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(TicketModal())

@bot.tree.command(name="ticket", description="Manda il pannello ticket")
@app_commands.describe(password="Password personalizzata di Zayan")
async def ticket_cmd(interaction: discord.Interaction, password: str):
    if password != TICKET_PASSWORD:
        await interaction.response.send_message("❌ Password errata!", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎫 TICKET - CASTREZZATO RP",
        description=(
            "Hai bisogno di aiuto?\n\n"
            "• Segnala un player\n"
            "• Fai una domanda allo Staff\n"
            "• Segnala un bug\n"
            "• Richiedi supporto\n\n"
            "Premi il bottone qui sotto per aprire un ticket.\n"
            "Lo Staff ti risponderà il prima possibile."
        ),
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed, view=TicketView())

# ================= AI =================
@bot.tree.command(name="ai", description="Chiedi qualcosa all'AI")
@app_commands.describe(password="Password personalizzata di Zayan", domanda="Cosa vuoi chiedere?")
async def ai_cmd(interaction: discord.Interaction, password: str, domanda: str):
    if password != AI_PASSWORD:
        await interaction.response.send_message("❌ Password errata!", ephemeral=True)
        return

    await interaction.response.defer()

    # Se hai OpenAI / altra AI collegala qui
    # Esempio semplice senza API - togli se usi OpenAI
    risposta = (
        f"🤖 **Hai chiesto:** {domanda}\n\n"
        f"Questa è la risposta dell'AI di Castrezzato RP.\n"
        f"Collega qui la tua API per risposte vere e intelligenti!"
    )

    # Se usi OpenAI, decommenta questo:
    # import openai
    # client = openai.OpenAI(api_key=OPENAI_KEY)
    # res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":domanda}])
    # risposta = res.choices[0].message.content

    embed = discord.Embed(title="🤖 AI - Castrezzato RP", description=risposta, color=discord.Color.purple())
    await interaction.followup.send(embed=embed)

# ================= CHECK ATTIVITÀ =================
check_attivi = {}  # {message_id: {"presenti": set(), "nomi": {}, "channel_id": int}}

class PresenteView(discord.ui.View):
    def __init__(self, message_id):
        super().__init__(timeout=None)
        self.message_id = message_id

    @discord.ui.button(label="✅ PRESENTE", style=discord.ButtonStyle.green, custom_id="btn_presente")
    async def presente_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = check_attivi.get(self.message_id)
        if not data:
            await interaction.response.send_message("❌ Check finito o non trovato.", ephemeral=True)
            return

        user_id = interaction.user.id
        if user_id in data["presenti"]:
            await interaction.response.send_message("⚠️ Sei già registrato come presente!", ephemeral=True)
            return

        data["presenti"].add(user_id)
        data["nomi"][user_id] = f"{interaction.user.display_name} (@{interaction.user.name})"
        await interaction.response.send_message("✅ Registrato come **PRESENTE**!", ephemeral=True)

@bot.tree.command(name="check", description="Avvia check attività Castrezzato RP Governo 3")
@app_commands.describe(password="Password personalizzata di Zayan")
async def check_cmd(interaction: discord.Interaction, password: str):
    if password != CHECK_PASSWORD:
        await interaction.response.send_message("❌ Password errata!", ephemeral=True)
        return

    embed = discord.Embed(
        title="📋 CHECK ATTIVITÀ - CASTREZZATO RP",
        description=(
            "**GOVERNO 3 - CONTROLLO PRESENZE**\n\n"
            "Ciao a tutti! 👋\n\n"
            "È iniziato il **Check Attività** per il **Governo 3 di Castrezzato RP**.\n"
            "Questo check serve per vedere chi è ancora attivo nel governo e chi invece è inattivo.\n\n"
            "**⚠️ IMPORTANTE - LEGGERE TUTTO:**\n"
            "• Premete il bottone **✅ PRESENTE** qui sotto per confermare la vostra presenza\n"
            "• Avete tempo fino a quando lo Staff dirà **STOP**\n"
            "• Chi non premerà il bottone verrà considerato **INATTIVO**\n"
            "• Chi è inattivo potrà essere rimosso dal Governo 3\n"
            "• Non fate finta di essere presenti se non siete attivi davvero\n"
            "• Un solo click a testa, non si può togliere\n\n"
            "**📌 Se siete in vacanza / assenti, avvisate in DM uno Staff.**\n\n"
            "Grazie a tutti per la collaborazione! 🙏\n"
            "**- Direzione Governo 3 - Castrezzato RP**"
        ),
        color=discord.Color.blue()
    )
    embed.set_footer(text="Castrezzato RP | Governo 3 | Check Attività")

    await interaction.response.send_message("✅ Check avviato!", ephemeral=True)
    msg = await interaction.channel.send(embed=embed, view=PresenteView(0))

    check_attivi[msg.id] = {
        "presenti": set(),
        "nomi": {},
        "channel_id": interaction.channel_id,
        "titolo": "Governo 3"
    }
    await msg.edit(view=PresenteView(msg.id))

@bot.tree.command(name="stopcheck", description="Ferma il check e manda la lista dei presenti")
@app_commands.describe(password="Password personalizzata di Zayan")
async def stopcheck_cmd(interaction: discord.Interaction, password: str):
    if password != CHECK_PASSWORD:
        await interaction.response.send_message("❌ Password errata!", ephemeral=True)
        return

    if not check_attivi:
        await interaction.response.send_message("❌ Nessun check attivo!", ephemeral=True)
        return

    last_id = list(check_attivi.keys())[-1]
    data = check_attivi.pop(last_id)

    nomi = list(data["nomi"].values())
    if not nomi:
        testo = "Nessuno ha premuto PRESENTE. 😢"
    else:
        testo = "\n".join([f"**{i+1}.** {nome}" for i, nome in enumerate(nomi)])

    embed = discord.Embed(
        title="🛑 CHECK FINITO - CASTREZZATO RP GOVERNO 3",
        description=f"**Totale presenti: {len(nomi)}**\n\n{testo}",
        color=discord.Color.green()
    )
    embed.set_footer(text="Castrezzato RP | Governo 3")

    await interaction.response.send_message("✅ Check fermato! Ecco la lista:", ephemeral=True)
    await interaction.channel.send(embed=embed)

# ================= SYNC MANUALE =================
@bot.tree.command(name="sync", description="Sincronizza i comandi (solo Zayan)")
@app_commands.describe(password="Password personalizzata di Zayan")
async def sync_cmd(interaction: discord.Interaction, password: str):
    if password != CHECK_PASSWORD:
        await interaction.response.send_message("❌ Password errata!", ephemeral=True)
        return
    synced = await bot.tree.sync()
    await interaction.response.send_message(f"✅ Sincronizzati {len(synced)} comandi!", ephemeral=True)

# ================= RUN =================
if __name__ == "__main__":
    if not TOKEN:
        print("❌ ERRORE: Metti DISCORD_TOKEN nelle variabili d'ambiente!")
    else:
        bot.run(TOKEN)
