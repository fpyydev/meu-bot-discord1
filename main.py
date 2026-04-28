import discord
from discord.ext import commands
import json
import random
from datetime import datetime, timedelta

# ═══════════════════════════════════════════════════════
#  CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════

TOKEN = "MTQ5ODM4MjU3Mjg5NDQyMTAyMg.GaplqV.guR1UPar_eG0wrXH7rZNCYyl0tiQLDmy6SublQ"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

DUELOS_PENDENTES = {}

# ═══════════════════════════════════════════════════════
#  BANCO DE DADOS (JSON)
# ═══════════════════════════════════════════════════════

DB_FILE = "banco.json"

def carregar():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def salvar(dados):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def pegar_user(dados, user_id: int) -> dict:
    uid = str(user_id)
    if uid not in dados:
        dados[uid] = {}
    u = dados[uid]
    defaults = {
        "pontos": 0,
        "espadas": [],
        "equipada": None,
        "ultimo_daily": None,
        "vitorias": 0,
        "derrotas": 0,
        "level": 1,
        "xp": 0,
        "ultimo_lutar": None,
        "armaduras": [],
        "armadura_cabeca": None,
        "armadura_corpo": None,
        "armadura_pes": None,
        "kills": 0,
        "mortes": 0,
        "buffs": [],
        "itens_secretos": [],
        "guilda": None,
        "ultimo_atacar_boss": None,
    }
    for k, v in defaults.items():
        u.setdefault(k, v)
    return u

def pegar_globals(dados) -> dict:
    if "_globals" not in dados:
        dados["_globals"] = {
            "chinelo_revelado": False,
            "chinelo_dono_id": None,
            "chinelo_dono_nome": None,
        }
    return dados["_globals"]

def pegar_guildas(dados) -> dict:
    if "_guildas" not in dados:
        dados["_guildas"] = {}
    return dados["_guildas"]

def pegar_boss(dados) -> dict:
    if "_boss" not in dados:
        dados["_boss"] = {
            "ativo": False,
            "hp_atual": 100_000_000,
            "hp_max":   100_000_000,
            "participantes": {},   # uid -> {"dano_total": int, "guilda": str, "nome": str}
            "morto": False,
            "vencedor_id":   None,
            "vencedor_nome": None,
            "spawned_em":    None,
        }
    return dados["_boss"]

# ═══════════════════════════════════════════════════════
#  CONSTANTES — ARMAS DA LOJA (EXPANDIDA)
# ═══════════════════════════════════════════════════════

LOJA = {
    # ── TIER 1: Comuns ──────────────────────────────────
    "Faca Enferrujada":       {"preco": 50,         "dano": 6,       "emoji": "🔪", "raridade": "Comum"},
    "Clava de Madeira":       {"preco": 80,         "dano": 9,       "emoji": "🪵", "raridade": "Comum"},
    "Faca de Combate":        {"preco": 150,        "dano": 12,      "emoji": "🔪", "raridade": "Comum"},
    "Espada Curta":           {"preco": 300,        "dano": 18,      "emoji": "🗡️", "raridade": "Comum"},
    "Arco Simples":           {"preco": 400,        "dano": 22,      "emoji": "🏹", "raridade": "Comum"},
    # ── TIER 2: Incomuns ────────────────────────────────
    "Lâmina Amaldiçoada":    {"preco": 500,        "dano": 35,      "emoji": "🗡️", "raridade": "Incomum"},
    "Machado de Guerra":      {"preco": 800,        "dano": 48,      "emoji": "🪓", "raridade": "Incomum"},
    "Martelo de Ferro":       {"preco": 950,        "dano": 55,      "emoji": "🔨", "raridade": "Incomum"},
    "Lança de Osso":          {"preco": 1000,       "dano": 60,      "emoji": "🦴", "raridade": "Incomum"},
    "Espada de Prata":        {"preco": 1100,       "dano": 65,      "emoji": "⚔️", "raridade": "Incomum"},
    # ── TIER 3: Raras ───────────────────────────────────
    "Espada do Caos":         {"preco": 1200,       "dano": 70,      "emoji": "⚔️", "raridade": "Rara"},
    "Arco Sombrio":           {"preco": 2000,       "dano": 90,      "emoji": "🏹", "raridade": "Rara"},
    "Alabarda Amaldiçoada":   {"preco": 2500,       "dano": 105,     "emoji": "🔱", "raridade": "Rara"},
    "Espada de Cristal":      {"preco": 2800,       "dano": 115,     "emoji": "💎", "raridade": "Rara"},
    # ── TIER 4: Épicas ──────────────────────────────────
    "Katana de Almas":        {"preco": 3000,       "dano": 120,     "emoji": "🏮", "raridade": "Épica"},
    "Foice do Reaper":        {"preco": 4500,       "dano": 160,     "emoji": "☠️", "raridade": "Épica"},
    "Machado de Gelo":        {"preco": 5500,       "dano": 200,     "emoji": "🧊", "raridade": "Épica"},
    "Espada do Abismo":       {"preco": 6000,       "dano": 225,     "emoji": "🌑", "raridade": "Épica"},
    # ── TIER 5: Lendárias ───────────────────────────────
    "Lança Sagrada":          {"preco": 7000,       "dano": 260,     "emoji": "🔱", "raridade": "Lendária"},
    "Excalibur":              {"preco": 10000,      "dano": 350,     "emoji": "✨", "raridade": "Lendária"},
    "Lâmina do Dragão":       {"preco": 12000,      "dano": 420,     "emoji": "🐉", "raridade": "Lendária"},
    "Tridente do Mar":        {"preco": 13500,      "dano": 470,     "emoji": "🔱", "raridade": "Lendária"},
    # ── TIER 6: Míticas ─────────────────────────────────
    "Machado das Trevas":     {"preco": 15000,      "dano": 550,     "emoji": "🪓", "raridade": "Mítica"},
    "Espada do Fogo Eterno":  {"preco": 20000,      "dano": 700,     "emoji": "🔥", "raridade": "Mítica"},
    "Lança da Tempestade":    {"preco": 28000,      "dano": 900,     "emoji": "⛈️", "raridade": "Mítica"},
    "Martelo do Trovão":      {"preco": 32000,      "dano": 1050,    "emoji": "⚡", "raridade": "Mítica"},
    # ── TIER 7: Divinas ─────────────────────────────────
    "Foice da Morte":         {"preco": 35000,      "dano": 1200,    "emoji": "☠️", "raridade": "Divina"},
    "Espada Dimensional":     {"preco": 60000,      "dano": 2000,    "emoji": "🌌", "raridade": "Divina"},
    "Lâmina do Juízo Final":  {"preco": 100000,     "dano": 3500,    "emoji": "⚖️", "raridade": "Divina"},
    "Cetro do Apocalipse":    {"preco": 250000,     "dano": 7000,    "emoji": "🌋", "raridade": "Divina"},
    "Lâmina Cósmica":         {"preco": 500000,     "dano": 15000,   "emoji": "🌠", "raridade": "Divina"},
    "Bastão do Caos Primordial": {"preco": 1000000, "dano": 30000,   "emoji": "🫀", "raridade": "Divina"},
}

# ═══════════════════════════════════════════════════════
#  CONSTANTES — ARMAS SECRETAS
# ═══════════════════════════════════════════════════════

ARMAS_BAU_ORIGINAL = {
    "Espada do Vazio":       {"dano": 800,   "emoji": "🌑", "raridade": "⬛ Secreta", "bau": "original"},
    "Lâmina do Caos Eterno": {"dano": 650,   "emoji": "🌀", "raridade": "⬛ Secreta", "bau": "original"},
    "Glaive das Trevas":     {"dano": 750,   "emoji": "☄️",  "raridade": "⬛ Secreta", "bau": "original"},
    "Adaga Sombria":         {"dano": 500,   "emoji": "🩸", "raridade": "⬛ Secreta", "bau": "original"},
    "Machado Abissal":       {"dano": 700,   "emoji": "🔥", "raridade": "⬛ Secreta", "bau": "original"},
    "Lança do Destino":      {"dano": 850,   "emoji": "🌟", "raridade": "⬛ Secreta", "bau": "original"},
}

ARMAS_BAU_SOMBRIO = {
    "Lâmina da Extinção":        {"dano": 3000,  "emoji": "🖤", "raridade": "🖤 Sombria",  "bau": "sombrio"},
    "Foice Abissal":              {"dano": 3500,  "emoji": "💀", "raridade": "🖤 Sombria",  "bau": "sombrio"},
    "Espada do Fim dos Tempos":   {"dano": 4200,  "emoji": "🌑", "raridade": "🖤 Sombria",  "bau": "sombrio"},
    "Glaive da Morte Eterna":     {"dano": 5000,  "emoji": "☠️",  "raridade": "🖤 Sombria",  "bau": "sombrio"},
    "Martelo das Trevas Absolutas":{"dano": 6000, "emoji": "🪓", "raridade": "🖤 Sombria",  "bau": "sombrio"},
    "Katana do Vazio Eterno":     {"dano": 7500,  "emoji": "⚫", "raridade": "🖤 Sombria",  "bau": "sombrio"},
}

ARMAS_BAU_CELESTIAL = {
    "Espada da Luz Divina":   {"dano": 8000,  "emoji": "☀️",  "raridade": "🌟 Celestial", "bau": "celestial"},
    "Lança dos Arcanjos":     {"dano": 10000, "emoji": "👼", "raridade": "🌟 Celestial", "bau": "celestial"},
    "Arco da Aurora Sagrada": {"dano": 12000, "emoji": "🌅", "raridade": "🌟 Celestial", "bau": "celestial"},
    "Cetro do Serafim":       {"dano": 15000, "emoji": "🕊️",  "raridade": "🌟 Celestial", "bau": "celestial"},
    "Excalibur Sagrada":      {"dano": 20000, "emoji": "✨", "raridade": "🌟 Celestial", "bau": "celestial"},
    "Lâmina da Criação":      {"dano": 28000, "emoji": "🌈", "raridade": "🌟 Celestial", "bau": "celestial"},
}

ARMAS_BAU_CAOS = {
    "Faca do Caos Puro":      {"dano": 35000,  "emoji": "🌀", "raridade": "💥 Caos",     "bau": "caos"},
    "Machado da Discórdia":   {"dano": 45000,  "emoji": "🔴", "raridade": "💥 Caos",     "bau": "caos"},
    "Lâmina da Realidade":    {"dano": 55000,  "emoji": "🎭", "raridade": "💥 Caos",     "bau": "caos"},
    "Espada Omega":           {"dano": 65000,  "emoji": "Ω",  "raridade": "💥 Caos",     "bau": "caos"},
    "Glaive Supremo":         {"dano": 80000,  "emoji": "💢", "raridade": "💥 Caos",     "bau": "caos"},
    "Tridente do Caos Absoluto": {"dano": 95000,"emoji": "🔱", "raridade": "💥 Caos",    "bau": "caos"},
}

ARMA_CHINELO = {
    "Chinelo do Fpyy": {
        "dano": 100000,
        "emoji": "🩴",
        "raridade": "🌈 ABSURDA",
        "especial": True,
        "bau": "chinelo",
        "descricao": "Acumula TODOS os buffs ativos automaticamente.",
    }
}

ARMAS_SECRETAS = {**ARMAS_BAU_ORIGINAL, **ARMAS_BAU_SOMBRIO, **ARMAS_BAU_CELESTIAL, **ARMAS_BAU_CAOS, **ARMA_CHINELO}
TODAS_ARMAS    = {**LOJA, **ARMAS_SECRETAS}

# ═══════════════════════════════════════════════════════
#  CONSTANTES — ARMADURAS
# ═══════════════════════════════════════════════════════

ARMADURAS = {
    "Capuz de Couro":     {"preco": 200,   "defesa": 5,   "emoji": "🪖", "raridade": "Comum",    "slot": "cabeca"},
    "Elmo de Ferro":      {"preco": 800,   "defesa": 15,  "emoji": "⛑️",  "raridade": "Incomum",  "slot": "cabeca"},
    "Elmo Encantado":     {"preco": 3500,  "defesa": 40,  "emoji": "👑", "raridade": "Rara",     "slot": "cabeca"},
    "Coroa das Trevas":   {"preco": 12000, "defesa": 90,  "emoji": "💀", "raridade": "Mítica",   "slot": "cabeca"},
    "Elmo do Caos":       {"preco": 50000, "defesa": 250, "emoji": "🌀", "raridade": "Divina",   "slot": "cabeca"},
    "Peitoral de Couro":  {"preco": 300,   "defesa": 8,   "emoji": "👕", "raridade": "Comum",    "slot": "corpo"},
    "Cota de Malha":      {"preco": 1200,  "defesa": 25,  "emoji": "🥋", "raridade": "Incomum",  "slot": "corpo"},
    "Armadura de Aço":    {"preco": 5000,  "defesa": 65,  "emoji": "🛡️", "raridade": "Rara",     "slot": "corpo"},
    "Armadura do Dragão": {"preco": 20000, "defesa": 150, "emoji": "🐉", "raridade": "Lendária", "slot": "corpo"},
    "Armadura do Abismo": {"preco": 80000, "defesa": 400, "emoji": "🌑", "raridade": "Divina",   "slot": "corpo"},
    "Botas de Couro":     {"preco": 150,   "defesa": 3,   "emoji": "👢", "raridade": "Comum",    "slot": "pes"},
    "Botas de Ferro":     {"preco": 600,   "defesa": 12,  "emoji": "🥾", "raridade": "Incomum",  "slot": "pes"},
    "Botas Místicas":     {"preco": 4000,  "defesa": 45,  "emoji": "✨", "raridade": "Épica",    "slot": "pes"},
    "Botas Abissais":     {"preco": 10000, "defesa": 80,  "emoji": "🌑", "raridade": "Mítica",   "slot": "pes"},
    "Botas do Vazio":     {"preco": 40000, "defesa": 200, "emoji": "⚫", "raridade": "Divina",   "slot": "pes"},
}

# ═══════════════════════════════════════════════════════
#  CONSTANTES — BUFFS
# ═══════════════════════════════════════════════════════

BUFFS_LOJA = {
    "Poção de Força":    {"preco": 500,  "emoji": "🧪", "efeito": "dano",   "mult": 1.50, "dur": 300,  "desc": "+50% dano por 5min"},
    "Elixir de Defesa":  {"preco": 800,  "emoji": "🛡️", "efeito": "defesa", "mult": 1.50, "dur": 300,  "desc": "+50% defesa por 5min"},
    "Bênção do Oráculo": {"preco": 2000, "emoji": "🔮", "efeito": "xp",     "mult": 2.00, "dur": 600,  "desc": "+100% XP por 10min"},
    "Talismã da Sorte":  {"preco": 3000, "emoji": "🍀", "efeito": "pontos", "mult": 1.75, "dur": 600,  "desc": "+75% pontos/msg por 10min"},
    "Fúria Sanguinária": {"preco": 5000, "emoji": "🩸", "efeito": "critico","mult": 2.00, "dur": 600,  "desc": "+100% dano crítico por 10min"},
}

# ═══════════════════════════════════════════════════════
#  CONSTANTES — INIMIGOS (EXPANDIDOS)
# ═══════════════════════════════════════════════════════

INIMIGOS = [
    {"nome": "Goblin Selvagem",      "hp": 60,      "dano_min": 3,     "dano_max": 8,     "rec": 80,      "emoji": "👺", "xp": 20},
    {"nome": "Lobo das Sombras",     "hp": 120,     "dano_min": 10,    "dano_max": 20,    "rec": 160,     "emoji": "🐺", "xp": 45},
    {"nome": "Esqueleto Guerreiro",  "hp": 250,     "dano_min": 20,    "dano_max": 35,    "rec": 300,     "emoji": "💀", "xp": 80},
    {"nome": "Ogro Enfurecido",      "hp": 500,     "dano_min": 35,    "dano_max": 55,    "rec": 550,     "emoji": "👹", "xp": 140},
    {"nome": "Hidra Venenosa",       "hp": 800,     "dano_min": 55,    "dano_max": 85,    "rec": 900,     "emoji": "🐍", "xp": 220},
    {"nome": "Dragão de Gelo",       "hp": 1500,    "dano_min": 80,    "dano_max": 130,   "rec": 1800,    "emoji": "🐉", "xp": 380},
    {"nome": "Demônio Ancestral",    "hp": 3000,    "dano_min": 150,   "dano_max": 230,   "rec": 4000,    "emoji": "😈", "xp": 700},
    {"nome": "Titã Dimensional",     "hp": 6000,    "dano_min": 280,   "dano_max": 420,   "rec": 9000,    "emoji": "🌌", "xp": 1500},
    {"nome": "Lich Supremo",         "hp": 15000,   "dano_min": 500,   "dano_max": 800,   "rec": 22000,   "emoji": "🧙", "xp": 3500},
    {"nome": "Leviatã Ancião",       "hp": 30000,   "dano_min": 1000,  "dano_max": 1600,  "rec": 55000,   "emoji": "🌊", "xp": 7000},
    {"nome": "Fênix das Cinzas",     "hp": 60000,   "dano_min": 2000,  "dano_max": 3200,  "rec": 120000,  "emoji": "🦅", "xp": 15000},
    {"nome": "Deus das Trevas",      "hp": 150000,  "dano_min": 5000,  "dano_max": 8000,  "rec": 300000,  "emoji": "🌑", "xp": 40000},
    {"nome": "Omega Supremo",        "hp": 500000,  "dano_min": 15000, "dano_max": 25000, "rec": 1000000, "emoji": "Ω",  "xp": 150000},
    {"nome": "O Absoluto",           "hp": 2000000, "dano_min": 50000, "dano_max": 80000, "rec": 5000000, "emoji": "♾️", "xp": 500000},
]

# ═══════════════════════════════════════════════════════
#  CONSTANTES — WORLD BOSS
# ═══════════════════════════════════════════════════════

BOSS_NOME   = "Kael'Thor, o Deus Primordial"
BOSS_EMOJI  = "👁️"
BOSS_HP_MAX = 100_000_000
# Ataques especiais do boss (só narrativos por turno)
BOSS_ATAQUES = [
    "lança um raio dimensional que atravessa dimensões",
    "invoca um buraco negro que consome tudo ao redor",
    "libera uma onda de energia cósmica destruidora",
    "abre portais para o vazio e lança projéteis do além",
    "grita com uma voz que faz o servidor tremer",
    "usa A MALDIÇÃO DO FIM DOS TEMPOS",
    "absorve a energia vital de todos ao redor",
    "convoca 1000 demônios auxiliares que atacam em uníssono",
    "usa EXTINÇÃO TOTAL — dano massivo em área",
    "abre o olho do apocalipse e envolve todos em trevas",
]
# Cada ataque do boss causa dano narrativo (não desativa jogadores de verdade)
BOSS_DANO_MIN = 500_000
BOSS_DANO_MAX = 2_000_000

# Recompensas para participantes que NÃO ganharam o chinelo
BOSS_RECOMPENSA_DANO_BONUS = 50_000   # pontos extras para todos que participaram
BOSS_RECOMPENSA_XP          = 200_000  # XP para todos participantes

# ═══════════════════════════════════════════════════════
#  CONSTANTES — MARCOS, MEDALHAS, PREÇOS
# ═══════════════════════════════════════════════════════

MARCOS = [100, 250, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000,
          250000, 500000, 1000000, 5000000, 10000000]
MARCO_EMOJIS = {
    100:"🌱", 250:"⭐", 500:"💫", 1000:"🔥", 2500:"💎",
    5000:"👑", 10000:"🌟", 25000:"⚡", 50000:"🏆", 100000:"🌈",
    250000:"🔮", 500000:"🌌", 1000000:"♾️", 5000000:"🌋", 10000000:"💠",
}
MEDALHAS = ["🥇","🥈","🥉"] + ["🏅"]*17

CORES_RARIDADE = {
    "Comum":0x95a5a6, "Incomum":0x2ecc71, "Rara":0x3498db,
    "Épica":0x9b59b6, "Lendária":0xf39c12, "Mítica":0xe74c3c,
    "Divina":0xffd700, "⬛ Secreta":0x2c3e50, "🖤 Sombria":0x1a1a2e,
    "🌟 Celestial":0xfff176, "💥 Caos":0xff4444, "🌈 ABSURDA":0xff69b4,
}

PRECO_BAU           = 100_000
PRECO_BAU_SOMBRIO   = 500_000
PRECO_BAU_CELESTIAL = 1_000_000
PRECO_BAU_CAOS      = 5_000_000
PRECO_CAIXA_CHINELO = 5_000
CHANCE_CHINELO      = 0.000001

PRECO_CRIAR_GUILDA  = 1_000   # custo de criar uma guilda

# ═══════════════════════════════════════════════════════
#  UTILIDADES
# ═══════════════════════════════════════════════════════

def xp_para_level(level: int) -> int:
    return int(100 * (level ** 1.6))

def get_buffs_ativos(user: dict) -> list:
    agora = datetime.now()
    ativos = [
        b for b in user.get("buffs", [])
        if datetime.strptime(b["expira"], "%Y-%m-%d %H:%M:%S") > agora
    ]
    user["buffs"] = ativos
    return ativos

def dano_arma(user: dict) -> int:
    eq = user.get("equipada")
    if eq and eq in TODAS_ARMAS:
        base = TODAS_ARMAS[eq]["dano"]
    else:
        base = 5

    buffs = get_buffs_ativos(user)

    if eq == "Chinelo do Fpyy":
        for b in buffs:
            base = int(base * b["mult"])
        return base

    for b in buffs:
        if b["efeito"] == "dano":
            base = int(base * b["mult"])
    return base

def defesa_total(user: dict) -> int:
    total = 0
    for slot in ["armadura_cabeca", "armadura_corpo", "armadura_pes"]:
        nome = user.get(slot)
        if nome and nome in ARMADURAS:
            total += ARMADURAS[nome]["defesa"]
    for b in get_buffs_ativos(user):
        if b["efeito"] == "defesa":
            total = int(total * b["mult"])
    return total

def barra_progresso(valor, maximo, tam=18) -> str:
    pct = min(valor / maximo, 1.0) if maximo > 0 else 0
    f = int(tam * pct)
    return "█" * f + "░" * (tam - f)

def posicao_ranking(dados: dict, uid: str) -> int:
    valid = {k: v for k, v in dados.items() if not k.startswith("_")}
    ranking = sorted(valid.items(), key=lambda x: x[1].get("pontos", 0), reverse=True)
    return next((i + 1 for i, (k, _) in enumerate(ranking) if k == uid), 0)

async def verificar_levelup(channel, membro, user: dict) -> bool:
    needed = xp_para_level(user["level"])
    if user["xp"] >= needed:
        user["xp"] -= needed
        user["level"] += 1
        bonus = user["level"] * 60
        user["pontos"] += bonus
        embed = discord.Embed(
            title="⬆️ LEVEL UP!",
            description=(
                f"🎉 {membro.mention} subiu para o **Nível {user['level']}**!\n"
                f"💰 Bônus de **+{bonus:,} pontos** desbloqueado!"
            ),
            color=0xf39c12,
        )
        embed.set_thumbnail(url=membro.display_avatar.url)
        await channel.send(embed=embed)
        return True
    return False

def boss_barra_hp(boss: dict) -> str:
    hp_at  = max(boss["hp_atual"], 0)
    hp_max = boss["hp_max"]
    pct    = hp_at / hp_max
    tam    = 20
    f      = int(tam * pct)
    cor    = "🟥" if pct < 0.25 else ("🟨" if pct < 0.60 else "🟩")
    return cor * f + "⬛" * (tam - f)

# ═══════════════════════════════════════════════════════
#  EVENTOS
# ═══════════════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"✅ {bot.user} online e pronto!")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="+ajuda | RPG de Pontos"
        )
    )

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    dados = carregar()
    user  = pegar_user(dados, message.author.id)
    pontos_antes = user["pontos"]

    pts_mult = 1.0
    xp_mult  = 1.0
    for b in get_buffs_ativos(user):
        if b["efeito"] == "pontos": pts_mult *= b["mult"]
        if b["efeito"] == "xp":    xp_mult  *= b["mult"]

    pts_ganhos = int(random.randint(1, 4) * pts_mult)
    xp_ganho   = int(random.randint(2, 6) * xp_mult)
    user["pontos"] += pts_ganhos
    user["xp"]     += xp_ganho
    pontos_agora = user["pontos"]
    salvar(dados)

    await verificar_levelup(message.channel, message.author, user)
    salvar(dados)

    for marco in MARCOS:
        if pontos_antes < marco <= pontos_agora:
            emoji = MARCO_EMOJIS.get(marco, "🎯")
            embed = discord.Embed(
                title=f"{emoji} MARCO ALCANÇADO!",
                description=(
                    f"**{message.author.mention}** atingiu **{marco:,} pontos**!\n"
                    f"Parabéns! {emoji}"
                ),
                color=0x2ecc71,
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            await message.channel.send(embed=embed)
            break

    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=discord.Embed(description="❌ Argumento faltando! Use `+ajuda`.", color=0xe74c3c))
    elif isinstance(error, commands.BadArgument):
        await ctx.send(embed=discord.Embed(description="❌ Argumento inválido! Verifique a menção.", color=0xe74c3c))
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=discord.Embed(description="❌ Sem permissão para isso!", color=0xe74c3c))
    elif isinstance(error, commands.CommandNotFound):
        pass

# ═══════════════════════════════════════════════════════
#  COMANDO: +pontos
# ═══════════════════════════════════════════════════════

@bot.command(name="pontos")
async def cmd_pontos(ctx, membro: discord.Member = None):
    membro = membro or ctx.author
    dados  = carregar()
    user   = pegar_user(dados, membro.id)

    proximo    = next((m for m in MARCOS if m > user["pontos"]), None)
    pos        = posicao_ranking(dados, str(membro.id))
    xp_need    = xp_para_level(user["level"])
    barra      = barra_progresso(user["xp"], xp_need)
    eq         = user.get("equipada") or "Punhos 👊"
    dano       = dano_arma(user)
    defesa     = defesa_total(user)
    total_mem  = len([k for k in dados if not k.startswith("_")])
    guilda_tag = f"\n🏰 Guilda: **{user['guilda']}**" if user.get("guilda") else ""

    embed = discord.Embed(title=f"💰 Carteira — {membro.display_name}", color=0xf1c40f)
    embed.set_thumbnail(url=membro.display_avatar.url)

    embed.add_field(
        name="〔 📊 Status 〕",
        value=(
            f"```\n"
            f"Pontos   ➜  {user['pontos']:>15,}\n"
            f"Ranking  ➜  #{pos} de {total_mem}\n"
            f"Nível    ➜  {user['level']:>15}\n"
            f"Vitórias ➜  {user.get('vitorias', 0):>15}\n"
            f"Kills PvP➜  {user.get('kills', 0):>15}\n"
            f"```"
            f"{guilda_tag}"
        ),
        inline=False,
    )
    embed.add_field(
        name=f"〔 ⭐ XP — Nível {user['level']} 〕",
        value=f"`{barra}` **{int(user['xp'] / xp_need * 100)}%**\n`{user['xp']:,} / {xp_need:,} XP`",
        inline=False,
    )

    item_info = TODAS_ARMAS.get(eq, {})
    rar = item_info.get("raridade", "—")
    chinelo_tag = "\n🩴 *Acumula TODOS os buffs!*" if eq == "Chinelo do Fpyy" else ""
    embed.add_field(
        name="〔 ⚔️ Arma Equipada 〕",
        value=f"`{eq}`\n⚡ Dano: **{dano:,}** | ✨ {rar}{chinelo_tag}",
        inline=True,
    )
    embed.add_field(
        name="〔 🛡️ Defesa Total 〕",
        value=f"**{defesa:,}** pts de defesa",
        inline=True,
    )

    if proximo:
        faltam = proximo - user["pontos"]
        emoji  = MARCO_EMOJIS.get(proximo, "🎯")
        embed.add_field(name="〔 🎯 Próximo Marco 〕", value=f"{emoji} **{proximo:,}** pts\nFaltam `{faltam:,}`", inline=True)
    else:
        embed.add_field(name="〔 🎯 Marco 〕", value="💠 **Máximo atingido!**", inline=True)

    embed.set_footer(text="Mande mensagens para ganhar pontos! • Use +loja para gastar")
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  COMANDO: +perfil
# ═══════════════════════════════════════════════════════

@bot.command(name="perfil")
async def cmd_perfil(ctx, membro: discord.Member = None):
    membro = membro or ctx.author
    dados  = carregar()
    user   = pegar_user(dados, membro.id)

    xp_need = xp_para_level(user["level"])
    barra   = barra_progresso(user["xp"], xp_need)
    eq      = user.get("equipada") or "Punhos 👊"
    dano    = dano_arma(user)
    defesa  = defesa_total(user)
    pos     = posicao_ranking(dados, str(membro.id))

    vitorias = user.get("vitorias", 0)
    derrotas = user.get("derrotas", 0)
    kills    = user.get("kills", 0)
    mortes   = user.get("mortes", 0)
    total_b  = vitorias + derrotas
    taxa     = f"{int(vitorias / total_b * 100)}%" if total_b > 0 else "—"
    kd       = f"{kills}/{mortes}" if mortes > 0 else str(kills)

    cab = user.get("armadura_cabeca") or "—"
    cor = user.get("armadura_corpo") or "—"
    pes = user.get("armadura_pes")   or "—"

    embed = discord.Embed(title=f"👤 Perfil de {membro.display_name}", color=0x3498db)
    embed.set_thumbnail(url=membro.display_avatar.url)

    guilda_val = f"🏰 **{user['guilda']}**" if user.get("guilda") else "❌ Sem guilda"
    embed.add_field(name="💰 Pontos",    value=f"`{user['pontos']:,}`",  inline=True)
    embed.add_field(name="🏅 Ranking",   value=f"`#{pos}`",              inline=True)
    embed.add_field(name="⭐ Nível",     value=f"`{user['level']}`",     inline=True)

    embed.add_field(name="🏆 Vitórias",  value=f"`{vitorias}`",  inline=True)
    embed.add_field(name="💀 Derrotas",  value=f"`{derrotas}`",  inline=True)
    embed.add_field(name="📈 Taxa Win",  value=f"`{taxa}`",       inline=True)

    embed.add_field(name="⚔️ Kills PvP", value=f"`{kills}`",    inline=True)
    embed.add_field(name="🪦 Mortes PvP",value=f"`{mortes}`",   inline=True)
    embed.add_field(name="📊 K/D",       value=f"`{kd}`",        inline=True)

    embed.add_field(name="🏰 Guilda",    value=guilda_val, inline=False)

    chinelo_tag = " 🩴 *[TODOS OS BUFFS]*" if eq == "Chinelo do Fpyy" else ""
    embed.add_field(
        name="⚔️ Arma | 🛡️ Defesa",
        value=f"`{eq}`{chinelo_tag} ⚡{dano:,} dano | 🛡️ {defesa:,} defesa",
        inline=False,
    )
    embed.add_field(
        name="🛡️ Armaduras Equipadas",
        value=(
            f"🪖 Cabeça: `{cab}`\n"
            f"👕 Corpo:  `{cor}`\n"
            f"👢 Pés:    `{pes}`"
        ),
        inline=True,
    )
    embed.add_field(
        name=f"📊 XP — Nível {user['level']}",
        value=f"`{barra}` {int(user['xp'] / xp_need * 100)}%\n`{user['xp']:,} / {xp_need:,}`",
        inline=True,
    )

    itens_s = user.get("itens_secretos", [])
    if itens_s:
        embed.add_field(
            name=f"🌑 Itens Secretos ({len(itens_s)})",
            value=" • ".join(
                f"{ARMAS_SECRETAS[i]['emoji']} {i}" if i in ARMAS_SECRETAS else f"🌑 {i}"
                for i in itens_s
            ),
            inline=False,
        )

    embed.set_footer(text="Use +lutar para ganhar XP • +duelar @user para PvP!")
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  COMANDO: +daily
# ═══════════════════════════════════════════════════════

@bot.command(name="daily")
async def cmd_daily(ctx):
    dados = carregar()
    user  = pegar_user(dados, ctx.author.id)
    agora = datetime.now()

    ultimo_str = user.get("ultimo_daily")
    if ultimo_str:
        ultimo  = datetime.strptime(ultimo_str, "%Y-%m-%d %H:%M:%S")
        proximo = ultimo + timedelta(days=1)
        if agora < proximo:
            espera  = proximo - agora
            horas   = int(espera.total_seconds() // 3600)
            minutos = int((espera.total_seconds() % 3600) // 60)
            return await ctx.send(embed=discord.Embed(
                title="⏳ Daily em Cooldown",
                description=f"Volte em **{horas}h {minutos}m** para coletar!",
                color=0xe67e22,
            ))

    recompensa = random.randint(200, 600)
    user["pontos"] += recompensa
    user["ultimo_daily"] = agora.strftime("%Y-%m-%d %H:%M:%S")
    salvar(dados)

    embed = discord.Embed(title="🎁 Daily Coletado!", description=f"{ctx.author.mention} recebeu **+{recompensa:,} pontos**!", color=0x2ecc71)
    embed.add_field(name="💰 Saldo Atual", value=f"`{user['pontos']:,} pts`", inline=True)
    embed.set_footer(text="Volte amanhã para mais pontos!")
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  COMANDO: +apostar
# ═══════════════════════════════════════════════════════

@bot.command(name="apostar")
async def cmd_apostar(ctx, valor: int):
    dados = carregar()
    user  = pegar_user(dados, ctx.author.id)

    if valor <= 0:
        return await ctx.send(embed=discord.Embed(description="❌ Valor precisa ser maior que 0!", color=0xe74c3c))
    if user["pontos"] < valor:
        return await ctx.send(embed=discord.Embed(description=f"❌ Você só tem **{user['pontos']:,} pts**!", color=0xe74c3c))
    if valor > 10_000_000:
        return await ctx.send(embed=discord.Embed(description="❌ Limite: **10.000.000 pts** por aposta!", color=0xe74c3c))

    ganhou = random.random() > 0.5
    if ganhou:
        user["pontos"] += valor
        embed = discord.Embed(title="🎰 GANHOU!", description=f"{ctx.author.mention} dobrou **{valor:,} pontos**! 🤑", color=0x2ecc71)
        embed.add_field(name="💸 Ganho",      value=f"`+{valor:,} pts`",        inline=True)
        embed.add_field(name="💰 Novo Saldo", value=f"`{user['pontos']:,} pts`", inline=True)
    else:
        user["pontos"] -= valor
        embed = discord.Embed(title="😢 PERDEU!", description=f"{ctx.author.mention} perdeu **{valor:,} pontos**.", color=0xe74c3c)
        embed.add_field(name="💸 Perda",    value=f"`-{valor:,} pts`",        inline=True)
        embed.add_field(name="💰 Restante", value=f"`{user['pontos']:,} pts`", inline=True)

    salvar(dados)
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  COMANDO: +doar
# ═══════════════════════════════════════════════════════

@bot.command(name="doar")
async def cmd_doar(ctx, membro: discord.Member, valor: int):
    if membro.bot:
        return await ctx.send(embed=discord.Embed(description="❌ Não dá pra doar para um bot!", color=0xe74c3c))
    if membro == ctx.author:
        return await ctx.send(embed=discord.Embed(description="❌ Não pode se doar pontos!", color=0xe74c3c))
    if valor <= 0:
        return await ctx.send(embed=discord.Embed(description="❌ Valor precisa ser positivo!", color=0xe74c3c))

    dados    = carregar()
    doador   = pegar_user(dados, ctx.author.id)
    receptor = pegar_user(dados, membro.id)

    if doador["pontos"] < valor:
        return await ctx.send(embed=discord.Embed(description=f"❌ Você só tem **{doador['pontos']:,} pts**!", color=0xe74c3c))

    doador["pontos"]   -= valor
    receptor["pontos"] += valor
    salvar(dados)

    embed = discord.Embed(title="💝 Doação Realizada!", color=0xe91e63)
    embed.add_field(name="📤 De",    value=f"{ctx.author.mention}\n`-{valor:,} pts`", inline=True)
    embed.add_field(name="➡️",       value="━━━━━━",                                   inline=True)
    embed.add_field(name="📥 Para",  value=f"{membro.mention}\n`+{valor:,} pts`",      inline=True)
    embed.set_footer(text=f"{ctx.author.display_name} agora tem {doador['pontos']:,} pts")
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  COMANDO: +loja
# ═══════════════════════════════════════════════════════

@bot.command(name="loja")
async def cmd_loja(ctx, pagina: int = 1):
    dados = carregar()
    user  = pegar_user(dados, ctx.author.id)

    tiers = {
        1: ("🌿 Tier 1 — Comuns",     [k for k, v in LOJA.items() if v["raridade"] == "Comum"]),
        2: ("🟢 Tier 2 — Incomuns",   [k for k, v in LOJA.items() if v["raridade"] == "Incomum"]),
        3: ("🔵 Tier 3 — Raras",      [k for k, v in LOJA.items() if v["raridade"] == "Rara"]),
        4: ("🟣 Tier 4 — Épicas",     [k for k, v in LOJA.items() if v["raridade"] == "Épica"]),
        5: ("🟡 Tier 5 — Lendárias",  [k for k, v in LOJA.items() if v["raridade"] == "Lendária"]),
        6: ("🔴 Tier 6 — Míticas",    [k for k, v in LOJA.items() if v["raridade"] == "Mítica"]),
        7: ("🌟 Tier 7 — Divinas",    [k for k, v in LOJA.items() if v["raridade"] == "Divina"]),
    }

    if pagina not in tiers:
        return await ctx.send(embed=discord.Embed(
            description="❌ Página inválida! Use `+loja 1` até `+loja 7`.",
            color=0xe74c3c,
        ))

    titulo_tier, armas_tier = tiers[pagina]
    embed = discord.Embed(
        title=f"🏪 Loja de Armas — {titulo_tier}",
        description=f"💰 Seus pontos: **{user['pontos']:,}**\nUse `+comprar <nome>` para comprar!\n{'━'*30}",
        color=0x9b59b6,
    )
    for nome in armas_tier:
        item = LOJA[nome]
        pode = "✅" if user["pontos"] >= item["preco"] else "❌"
        tem  = " *(possuída)*" if nome in user.get("espadas", []) else ""
        embed.add_field(
            name=f"{item['emoji']} {nome}{tem}",
            value=f"💰 **{item['preco']:,} pts** {pode}\n⚡ Dano: `{item['dano']:,}`\n✨ `{item['raridade']}`",
            inline=True,
        )
    embed.set_footer(text=f"Página {pagina}/7 • Use +loja 1 até +loja 7 • +armaduras para defesa")
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  COMANDO: +comprar
# ═══════════════════════════════════════════════════════

@bot.command(name="comprar")
async def cmd_comprar(ctx, *, nome_arma: str):
    item_key = next((k for k in LOJA if k.lower() == nome_arma.lower()), None)
    if not item_key:
        return await ctx.send(embed=discord.Embed(description=f"❌ **`{nome_arma}`** não encontrado! Use `+loja`.", color=0xe74c3c))

    dados = carregar()
    user  = pegar_user(dados, ctx.author.id)
    item  = LOJA[item_key]

    if item_key in user.get("espadas", []):
        return await ctx.send(embed=discord.Embed(description=f"❌ Você já possui **{item_key}**!", color=0xe74c3c))
    if user["pontos"] < item["preco"]:
        return await ctx.send(embed=discord.Embed(description=f"❌ Faltam **{item['preco']-user['pontos']:,} pts**.", color=0xe74c3c))

    user["pontos"] -= item["preco"]
    user.setdefault("espadas", []).append(item_key)
    salvar(dados)

    cor = CORES_RARIDADE.get(item["raridade"], 0x2ecc71)
    embed = discord.Embed(title="✅ Compra Efetuada!", description=f"{item['emoji']} **{item_key}** no inventário!", color=cor)
    embed.add_field(name="💸 Gasto",    value=f"`{item['preco']:,} pts`",  inline=True)
    embed.add_field(name="💳 Saldo",    value=f"`{user['pontos']:,} pts`", inline=True)
    embed.add_field(name="✨ Raridade", value=f"`{item['raridade']}`",      inline=True)
    embed.set_footer(text=f"Use +equipar {item_key} para usar em combate!")
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  COMANDO: +inventario
# ═══════════════════════════════════════════════════════

@bot.command(name="inventario")
async def cmd_inventario(ctx, membro: discord.Member = None):
    membro   = membro or ctx.author
    dados    = carregar()
    user     = pegar_user(dados, membro.id)
    espadas  = user.get("espadas", [])
    equipada = user.get("equipada")

    embed = discord.Embed(title=f"🎒 Arsenal de {membro.display_name}", color=0x1abc9c)
    embed.set_thumbnail(url=membro.display_avatar.url)

    if not espadas:
        embed.description = "❌ Nenhuma arma no inventário!\nUse `+loja` para comprar."
    else:
        for arma in espadas:
            it    = TODAS_ARMAS.get(arma, {})
            emoji = it.get("emoji", "⚔️")
            dano  = it.get("dano", "?")
            rar   = it.get("raridade", "?")
            tag   = " 🟢 *equipada*" if arma == equipada else ""
            chinelo_tag = "\n🩴 *Acumula TODOS os buffs!*" if arma == "Chinelo do Fpyy" else ""
            embed.add_field(
                name=f"{emoji} {arma}{tag}",
                value=f"⚡ Dano: `{dano:,}` | ✨ {rar}{chinelo_tag}",
                inline=False,
            )
    embed.set_footer(text="Use +equipar <arma> para trocar!")
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  COMANDO: +equipar
# ═══════════════════════════════════════════════════════

@bot.command(name="equipar")
async def cmd_equipar(ctx, *, nome_arma: str):
    dados = carregar()
    user  = pegar_user(dados, ctx.author.id)

    arma = next((e for e in user.get("espadas", []) if e.lower() == nome_arma.lower()), None)
    if not arma:
        return await ctx.send(embed=discord.Embed(description="❌ Você não possui essa arma! Use `+inventario`.", color=0xe74c3c))

    user["equipada"] = arma
    salvar(dados)

    it  = TODAS_ARMAS.get(arma, {})
    cor = CORES_RARIDADE.get(it.get("raridade", ""), 0x3498db)
    embed = discord.Embed(title="⚔️ Arma Equipada!", description=f"{it.get('emoji','⚔️')} **{arma}** pronta para o combate!", color=cor)
    embed.add_field(name="⚡ Dano",    value=f"`{it.get('dano', '?'):,}`",   inline=True)
    embed.add_field(name="✨ Raridade", value=f"`{it.get('raridade','?')}`",  inline=True)
    if arma == "Chinelo do Fpyy":
        embed.add_field(name="🩴 Efeito Especial", value="*Acumula TODOS os buffs ativos automaticamente!*", inline=False)
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  COMANDO: +armaduras
# ═══════════════════════════════════════════════════════

@bot.command(name="armaduras")
async def cmd_armaduras(ctx):
    dados = carregar()
    user  = pegar_user(dados, ctx.author.id)

    embed = discord.Embed(
        title="🛡️ Loja de Armaduras",
        description=f"💰 Seus pontos: **{user['pontos']:,}**\nUse `+comprar_armadura <nome>`\n{'━'*30}",
        color=0x3498db,
    )
    slots = [("cabeca", "🪖 Cabeça"), ("corpo", "👕 Corpo"), ("pes", "👢 Pés")]
    for slot_key, slot_nome in slots:
        itens = {n: i for n, i in ARMADURAS.items() if i["slot"] == slot_key}
        linhas = []
        for nome, item in itens.items():
            pode = "✅" if user["pontos"] >= item["preco"] else "❌"
            tem  = " *(possuída)*" if nome in user.get("armaduras", []) else ""
            eq   = " 🟢" if user.get(f"armadura_{slot_key}") == nome else ""
            linhas.append(
                f"{item['emoji']} **{nome}**{tem}{eq}\n"
                f"💰 `{item['preco']:,}` {pode} | 🛡️ `{item['defesa']:,}` defesa | ✨ {item['raridade']}"
            )
        embed.add_field(name=slot_nome, value="\n".join(linhas) or "—", inline=False)

    embed.set_footer(text="Mais defesa = mais HP efetivo em combate!")
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  COMANDO: +comprar_armadura
# ═══════════════════════════════════════════════════════

@bot.command(name="comprar_armadura")
async def cmd_comprar_armadura(ctx, *, nome: str):
    key = next((k for k in ARMADURAS if k.lower() == nome.lower()), None)
    if not key:
        return await ctx.send(embed=discord.Embed(description=f"❌ **`{nome}`** não encontrada! Use `+armaduras`.", color=0xe74c3c))

    dados = carregar()
    user  = pegar_user(dados, ctx.author.id)
    item  = ARMADURAS[key]

    if key in user.get("armaduras", []):
        return await ctx.send(embed=discord.Embed(description=f"❌ Você já possui **{key}**!", color=0xe74c3c))
    if user["pontos"] < item["preco"]:
        return await ctx.send(embed=discord.Embed(description=f"❌ Faltam **{item['preco']-user['pontos']:,} pts**!", color=0xe74c3c))

    user["pontos"] -= item["preco"]
    user.setdefault("armaduras", []).append(key)
    salvar(dados)

    embed = discord.Embed(title="✅ Armadura Comprada!", description=f"{item['emoji']} **{key}** no inventário!", color=0x2ecc71)
    embed.add_field(name="🛡️ Defesa",  value=f"`+{item['defesa']:,}`",     inline=True)
    embed.add_field(name="💸 Gasto",   value=f"`{item['preco']:,} pts`",   inline=True)
    embed.add_field(name="💳 Saldo",   value=f"`{user['pontos']:,} pts`",  inline=True)
    embed.set_footer(text=f"Use +vestir {key} para equipar!")
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  COMANDO: +vestir
# ═══════════════════════════════════════════════════════

@bot.command(name="vestir")
async def cmd_vestir(ctx, *, nome: str):
    dados = carregar()
    user  = pegar_user(dados, ctx.author.id)

    arma = next((a for a in user.get("armaduras", []) if a.lower() == nome.lower()), None)
    if not arma:
        return await ctx.send(embed=discord.Embed(description="❌ Você não possui essa armadura! Use `+inventario_armadura`.", color=0xe74c3c))

    slot = ARMADURAS[arma]["slot"]
    user[f"armadura_{slot}"] = arma
    salvar(dados)

    it = ARMADURAS[arma]
    embed = discord.Embed(title="🛡️ Armadura Equipada!", description=f"{it['emoji']} **{arma}** equipada no slot **{slot}**!", color=0x3498db)
    embed.add_field(name="🛡️ Defesa", value=f"`+{it['defesa']:,}`", inline=True)
    embed.add_field(name="✨ Raridade", value=f"`{it['raridade']}`", inline=True)
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  COMANDO: +inventario_armadura
# ═══════════════════════════════════════════════════════

@bot.command(name="inventario_armadura")
async def cmd_inventario_armadura(ctx, membro: discord.Member = None):
    membro   = membro or ctx.author
    dados    = carregar()
    user     = pegar_user(dados, membro.id)
    armaduras = user.get("armaduras", [])

    embed = discord.Embed(title=f"🛡️ Armaduras de {membro.display_name}", color=0x3498db)
    embed.set_thumbnail(url=membro.display_avatar.url)

    if not armaduras:
        embed.description = "❌ Nenhuma armadura! Use `+armaduras` para comprar."
    else:
        slots = {"cabeca": "🪖 Cabeça", "corpo": "👕 Corpo", "pes": "👢 Pés"}
        for slot_key, slot_nome in slots.items():
            itens_slot = [a for a in armaduras if ARMADURAS[a]["slot"] == slot_key]
            eq = user.get(f"armadura_{slot_key}")
            if itens_slot:
                for arma in itens_slot:
                    it  = ARMADURAS[arma]
                    tag = " 🟢 *equipada*" if arma == eq else ""
                    embed.add_field(
                        name=f"{it['emoji']} {arma}{tag}",
                        value=f"🛡️ Defesa: `{it['defesa']:,}` | ✨ {it['raridade']} | Slot: {slot_nome}",
                        inline=False,
                    )
    embed.set_footer(text="Use +vestir <nome> para equipar!")
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  COMANDOS: +buffs_loja / +comprar_buff / +meus_buffs
# ═══════════════════════════════════════════════════════

@bot.command(name="buffs_loja")
async def cmd_buffs_loja(ctx):
    dados = carregar()
    user  = pegar_user(dados, ctx.author.id)

    embed = discord.Embed(
        title="⚗️ Loja de Buffs",
        description=(
            f"💰 Seus pontos: **{user['pontos']:,}**\n"
            f"Use `+comprar_buff <nome>`\n"
            f"🩴 *Dica: O Chinelo do Fpyy acumula TODOS os buffs!*\n{'━'*30}"
        ),
        color=0x9b59b6,
    )
    for nome, b in BUFFS_LOJA.items():
        pode = "✅" if user["pontos"] >= b["preco"] else "❌"
        embed.add_field(
            name=f"{b['emoji']} {nome}",
            value=f"💰 `{b['preco']:,}` {pode}\n📝 {b['desc']}",
            inline=True,
        )
    embed.set_footer(text="Buffs são temporários! O Chinelo acumula todos simultaneamente.")
    await ctx.send(embed=embed)

@bot.command(name="comprar_buff")
async def cmd_comprar_buff(ctx, *, nome: str):
    key = next((k for k in BUFFS_LOJA if k.lower() == nome.lower()), None)
    if not key:
        return await ctx.send(embed=discord.Embed(description=f"❌ Buff **`{nome}`** não encontrado! Use `+buffs_loja`.", color=0xe74c3c))

    dados = carregar()
    user  = pegar_user(dados, ctx.author.id)
    b     = BUFFS_LOJA[key]

    if user["pontos"] < b["preco"]:
        return await ctx.send(embed=discord.Embed(description=f"❌ Faltam **{b['preco']-user['pontos']:,} pts**!", color=0xe74c3c))

    user["pontos"] -= b["preco"]
    expira = datetime.now() + timedelta(seconds=b["dur"])
    user.setdefault("buffs", []).append({
        "nome":   key,
        "efeito": b["efeito"],
        "mult":   b["mult"],
        "expira": expira.strftime("%Y-%m-%d %H:%M:%S"),
    })
    salvar(dados)

    eq = user.get("equipada", "")
    chinelo_nota = "\n🩴 *Chinelo do Fpyy vai usar este buff automaticamente!*" if eq == "Chinelo do Fpyy" else ""
    embed = discord.Embed(title=f"{b['emoji']} Buff Ativado!", description=f"**{key}** está ativo!\n📝 {b['desc']}{chinelo_nota}", color=0x9b59b6)
    embed.add_field(name="⏰ Expira às",  value=f"`{expira.strftime('%H:%M:%S')}`", inline=True)
    embed.add_field(name="💸 Gasto",      value=f"`{b['preco']:,} pts`",            inline=True)
    await ctx.send(embed=embed)

@bot.command(name="meus_buffs")
async def cmd_meus_buffs(ctx):
    dados  = carregar()
    user   = pegar_user(dados, ctx.author.id)
    ativos = get_buffs_ativos(user)
    salvar(dados)

    embed = discord.Embed(title=f"⚗️ Buffs Ativos — {ctx.author.display_name}", color=0x9b59b6)
    if not ativos:
        embed.description = "❌ Nenhum buff ativo!\nUse `+buffs_loja` para comprar."
    else:
        for b in ativos:
            expira = datetime.strptime(b["expira"], "%Y-%m-%d %H:%M:%S")
            resta  = expira - datetime.now()
            mins   = int(resta.total_seconds() // 60)
            segs   = int(resta.total_seconds() % 60)
            embed.add_field(
                name=b["nome"],
                value=f"⏰ Restam: `{mins}m {segs}s`\n✖️ ×{b['mult']} — {b['efeito']}",
                inline=True,
            )
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  COMANDO: +lutar
# ═══════════════════════════════════════════════════════

@bot.command(name="lutar")
async def cmd_lutar(ctx):
    dados = carregar()
    user  = pegar_user(dados, ctx.author.id)
    agora = datetime.now()

    ultimo_str = user.get("ultimo_lutar")
    if ultimo_str:
        ultimo  = datetime.strptime(ultimo_str, "%Y-%m-%d %H:%M:%S")
        proximo = ultimo + timedelta(seconds=30)
        if agora < proximo:
            espera = int((proximo - agora).total_seconds())
            return await ctx.send(embed=discord.Embed(
                description=f"⏳ Recuperando! Aguarde **{espera}s**.",
                color=0xe67e22,
            ))

    nivel_idx = min(user["level"] - 1, len(INIMIGOS) - 1)
    faixa     = INIMIGOS[:nivel_idx + 1]
    pesos     = [i + 1 for i in range(len(faixa))]
    inimigo   = random.choices(faixa, weights=pesos, k=1)[0]

    dano_player  = dano_arma(user)
    def_player   = defesa_total(user)
    hp_inimigo   = inimigo["hp"]
    hp_player    = 100 + user["level"] * 15

    crit_mult = 1.8
    for b in get_buffs_ativos(user):
        if b["efeito"] == "critico":
            crit_mult *= b["mult"]

    log_turnos = []
    turno = 1
    while hp_inimigo > 0 and hp_player > 0 and turno <= 25:
        dano_p  = random.randint(int(dano_player * 0.75), int(dano_player * 1.25))
        critico = random.random() < 0.15
        if critico:
            dano_p = int(dano_p * crit_mult)

        dano_e = max(1, random.randint(inimigo["dano_min"], inimigo["dano_max"]) - def_player // 2)
        hp_inimigo -= dano_p
        if hp_inimigo > 0:
            hp_player -= dano_e

        crit_txt = " ✦CRÍTICO" if critico else ""
        log_turnos.append(f"#{turno:02}  Você ➜ -{dano_p:,}{crit_txt} | {inimigo['nome'][:10]} ➜ -{dano_e:,}")
        turno += 1
        if hp_inimigo <= 0 or hp_player <= 0:
            break

    vitoria = hp_inimigo <= 0
    user["ultimo_lutar"] = agora.strftime("%Y-%m-%d %H:%M:%S")

    if vitoria:
        bonus_rand = random.randint(0, int(inimigo["rec"] * 0.4))
        recompensa = inimigo["rec"] + bonus_rand
        xp_ganho   = inimigo["xp"]
        user["pontos"]  += recompensa
        user["xp"]      += xp_ganho
        user["vitorias"] = user.get("vitorias", 0) + 1

        embed = discord.Embed(
            title=f"⚔️ VITÓRIA! {inimigo['emoji']} {inimigo['nome']} derrotado!",
            color=0x2ecc71,
        )
        embed.add_field(name="📜 Últimos Turnos", value=f"```{chr(10).join(log_turnos[-6:])}```", inline=False)
        embed.add_field(name="💰 Recompensa", value=f"`+{recompensa:,} pts`", inline=True)
        embed.add_field(name="✨ XP",         value=f"`+{xp_ganho:,} XP`",   inline=True)
        embed.add_field(name="🏆 Vitórias",   value=f"`{user['vitorias']}`",  inline=True)
        embed.set_footer(text="Use +lutar novamente em 30s!")
        salvar(dados)
        await ctx.send(embed=embed)
        await verificar_levelup(ctx.channel, ctx.author, user)
        salvar(dados)
    else:
        user["derrotas"] = user.get("derrotas", 0) + 1
        embed = discord.Embed(
            title=f"💀 DERROTA! {inimigo['emoji']} {inimigo['nome']} te venceu!",
            color=0xe74c3c,
        )
        embed.add_field(name="📜 Últimos Turnos", value=f"```{chr(10).join(log_turnos[-6:])}```", inline=False)
        embed.add_field(name="💡 Dica", value="Compre armaduras na `+armaduras` para mais defesa!", inline=False)
        embed.set_footer(text=f"Derrotas: {user['derrotas']} • Tente novamente em 30s")
        salvar(dados)
        await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  COMANDO: +duelar / +aceitar / +recusar
# ═══════════════════════════════════════════════════════

@bot.command(name="duelar")
async def cmd_duelar(ctx, alvo: discord.Member, valor: int = 100):
    if alvo.bot or alvo == ctx.author:
        return await ctx.send(embed=discord.Embed(description="❌ Alvo inválido!", color=0xe74c3c))
    if valor <= 0:
        return await ctx.send(embed=discord.Embed(description="❌ Valor deve ser maior que 0!", color=0xe74c3c))

    dados = carregar()
    desa  = pegar_user(dados, ctx.author.id)
    dest  = pegar_user(dados, alvo.id)

    if desa["pontos"] < valor:
        return await ctx.send(embed=discord.Embed(description=f"❌ Você não tem **{valor:,} pts**!", color=0xe74c3c))
    if dest["pontos"] < valor:
        return await ctx.send(embed=discord.Embed(description=f"❌ **{alvo.display_name}** não tem **{valor:,} pts**!", color=0xe74c3c))
    if alvo.id in DUELOS_PENDENTES:
        return await ctx.send(embed=discord.Embed(description="❌ Esse jogador já tem um duelo pendente!", color=0xe74c3c))

    DUELOS_PENDENTES[alvo.id] = {
        "desafiante_id": ctx.author.id,
        "valor":         valor,
        "channel_id":    ctx.channel.id,
        "timestamp":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    embed = discord.Embed(
        title="⚔️ DESAFIO DE DUELO!",
        description=(
            f"**{ctx.author.mention}** desafiou **{alvo.mention}**!\n"
            f"💰 Em jogo: **{valor:,} pontos**\n\n"
            f"{alvo.mention} — use `+aceitar` ou `+recusar`!\n"
            f"*(Expira em 60 segundos)*"
        ),
        color=0xe74c3c,
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="aceitar")
async def cmd_aceitar(ctx):
    if ctx.author.id not in DUELOS_PENDENTES:
        return await ctx.send(embed=discord.Embed(description="❌ Você não tem desafios pendentes!", color=0xe74c3c))

    info = DUELOS_PENDENTES.pop(ctx.author.id)
    ts   = datetime.strptime(info["timestamp"], "%Y-%m-%d %H:%M:%S")
    if datetime.now() > ts + timedelta(seconds=60):
        return await ctx.send(embed=discord.Embed(description="❌ O desafio expirou!", color=0xe74c3c))

    dados      = carregar()
    uid_desa   = info["desafiante_id"]
    uid_dest   = ctx.author.id
    valor      = info["valor"]

    try:
        membro_desa = await bot.fetch_user(uid_desa)
    except Exception:
        return await ctx.send(embed=discord.Embed(description="❌ Desafiante não encontrado!", color=0xe74c3c))

    u_desa = pegar_user(dados, uid_desa)
    u_dest = pegar_user(dados, uid_dest)

    if u_desa["pontos"] < valor or u_dest["pontos"] < valor:
        return await ctx.send(embed=discord.Embed(description="❌ Um dos jogadores não tem pontos suficientes!", color=0xe74c3c))

    d_desa   = dano_arma(u_desa)
    d_dest   = dano_arma(u_dest)
    def_desa = defesa_total(u_desa)
    def_dest = defesa_total(u_dest)
    hp_desa  = 100 + u_desa["level"] * 15
    hp_dest  = 100 + u_dest["level"] * 15

    crit_desa = 1.8
    crit_dest = 1.8
    for b in get_buffs_ativos(u_desa):
        if b["efeito"] == "critico": crit_desa *= b["mult"]
    for b in get_buffs_ativos(u_dest):
        if b["efeito"] == "critico": crit_dest *= b["mult"]

    log = []
    turno = 1
    while hp_desa > 0 and hp_dest > 0 and turno <= 30:
        atk1 = max(1, random.randint(int(d_desa*0.75), int(d_desa*1.25)) - def_dest // 2)
        atk2 = max(1, random.randint(int(d_dest*0.75), int(d_dest*1.25)) - def_desa // 2)
        c1   = random.random() < 0.15
        c2   = random.random() < 0.15
        if c1: atk1 = int(atk1 * crit_desa)
        if c2: atk2 = int(atk2 * crit_dest)
        hp_dest -= atk1
        hp_desa -= atk2
        log.append(
            f"#{turno:02} {membro_desa.name[:8]}{'✦' if c1 else ''} -{atk1:,} | "
            f"{ctx.author.name[:8]}{'✦' if c2 else ''} -{atk2:,}"
        )
        turno += 1
        if hp_desa <= 0 or hp_dest <= 0:
            break

    desa_ganhou = hp_dest <= 0 or (hp_desa > hp_dest)
    if desa_ganhou:
        venc_u, perd_u = u_desa, u_dest
        venc_m, perd_m = membro_desa, ctx.author
    else:
        venc_u, perd_u = u_dest, u_desa
        venc_m, perd_m = ctx.author, membro_desa

    venc_u["pontos"]  += valor
    perd_u["pontos"]  -= valor
    venc_u["kills"]    = venc_u.get("kills", 0) + 1
    perd_u["mortes"]   = perd_u.get("mortes", 0) + 1
    xp_duelo           = 50 + valor // 20
    venc_u["xp"]      += xp_duelo
    salvar(dados)

    embed = discord.Embed(
        title="⚔️ DUELO FINALIZADO!",
        description=f"🏆 **{venc_m.display_name}** venceu!",
        color=0xf1c40f,
    )
    embed.add_field(name="📜 Últimos Turnos", value=f"```{chr(10).join(log[-8:])}```", inline=False)
    embed.add_field(name="💰 Prêmio",   value=f"`+{valor:,} pts` → {venc_m.mention}", inline=True)
    embed.add_field(name="💀 Derrota",  value=f"`-{valor:,} pts` → {perd_m.mention}", inline=True)
    embed.add_field(name="✨ XP Bônus", value=f"`+{xp_duelo:,}` → {venc_m.mention}", inline=True)
    embed.set_footer(text=f"Kills de {venc_m.display_name}: {venc_u.get('kills',0)} • Use +top kills!")
    await ctx.send(embed=embed)

    await verificar_levelup(ctx.channel, venc_m, venc_u)
    salvar(dados)

@bot.command(name="recusar")
async def cmd_recusar(ctx):
    if ctx.author.id not in DUELOS_PENDENTES:
        return await ctx.send(embed=discord.Embed(description="❌ Nenhum desafio pendente!", color=0xe74c3c))
    DUELOS_PENDENTES.pop(ctx.author.id)
    await ctx.send(embed=discord.Embed(description=f"❌ {ctx.author.mention} recusou o duelo.", color=0xe67e22))

# ═══════════════════════════════════════════════════════
#  SISTEMA DE GUILDAS
# ═══════════════════════════════════════════════════════

@bot.command(name="criar_guilda")
async def cmd_criar_guilda(ctx, *, nome: str):
    if len(nome) > 25:
        return await ctx.send(embed=discord.Embed(description="❌ Nome máximo: **25 caracteres**!", color=0xe74c3c))
    if len(nome) < 3:
        return await ctx.send(embed=discord.Embed(description="❌ Nome mínimo: **3 caracteres**!", color=0xe74c3c))

    dados   = carregar()
    user    = pegar_user(dados, ctx.author.id)
    guildas = pegar_guildas(dados)

    if user.get("guilda"):
        return await ctx.send(embed=discord.Embed(
            description=f"❌ Você já faz parte da guilda **{user['guilda']}**!\nSaia com `+sair_guilda` primeiro.",
            color=0xe74c3c,
        ))

    # Verifica se o nome já existe (case-insensitive)
    if any(g.lower() == nome.lower() for g in guildas):
        return await ctx.send(embed=discord.Embed(description=f"❌ Já existe uma guilda chamada **{nome}**!", color=0xe74c3c))

    if user["pontos"] < PRECO_CRIAR_GUILDA:
        return await ctx.send(embed=discord.Embed(
            description=f"❌ Criar guilda custa **{PRECO_CRIAR_GUILDA:,} pts**! Você tem `{user['pontos']:,}`.",
            color=0xe74c3c,
        ))

    user["pontos"] -= PRECO_CRIAR_GUILDA
    user["guilda"]  = nome
    guildas[nome] = {
        "lider_id":  str(ctx.author.id),
        "membros":   [str(ctx.author.id)],
        "criada_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "descricao": "",
    }
    salvar(dados)

    embed = discord.Embed(
        title="🏰 Guilda Criada!",
        description=(
            f"A guilda **{nome}** foi fundada por {ctx.author.mention}!\n\n"
            f"Convide membros com `+entrar_guilda {nome}`\n"
            f"💰 Custo debitado: `{PRECO_CRIAR_GUILDA:,} pts`"
        ),
        color=0xf39c12,
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.set_footer(text="Forme sua equipe e derote o World Boss juntos!")
    await ctx.send(embed=embed)

@bot.command(name="entrar_guilda")
async def cmd_entrar_guilda(ctx, *, nome: str):
    dados   = carregar()
    user    = pegar_user(dados, ctx.author.id)
    guildas = pegar_guildas(dados)

    if user.get("guilda"):
        return await ctx.send(embed=discord.Embed(
            description=f"❌ Você já está na guilda **{user['guilda']}**! Saia com `+sair_guilda`.",
            color=0xe74c3c,
        ))

    guilda_key = next((g for g in guildas if g.lower() == nome.lower()), None)
    if not guilda_key:
        return await ctx.send(embed=discord.Embed(description=f"❌ Guilda **{nome}** não encontrada! Use `+guildas`.", color=0xe74c3c))

    guilda = guildas[guilda_key]
    if str(ctx.author.id) in guilda["membros"]:
        return await ctx.send(embed=discord.Embed(description="❌ Você já está nessa guilda!", color=0xe74c3c))

    guilda["membros"].append(str(ctx.author.id))
    user["guilda"] = guilda_key
    salvar(dados)

    embed = discord.Embed(
        title="🏰 Entrou na Guilda!",
        description=(
            f"{ctx.author.mention} entrou em **{guilda_key}**!\n"
            f"👥 Membros agora: **{len(guilda['membros'])}**"
        ),
        color=0x2ecc71,
    )
    embed.set_footer(text="Agora você pode atacar o World Boss com sua equipe!")
    await ctx.send(embed=embed)

@bot.command(name="sair_guilda")
async def cmd_sair_guilda(ctx):
    dados   = carregar()
    user    = pegar_user(dados, ctx.author.id)
    guildas = pegar_guildas(dados)

    guilda_nome = user.get("guilda")
    if not guilda_nome or guilda_nome not in guildas:
        return await ctx.send(embed=discord.Embed(description="❌ Você não está em nenhuma guilda!", color=0xe74c3c))

    guilda = guildas[guilda_nome]
    uid    = str(ctx.author.id)

    # Líder não pode sair sem transferir ou dissolver
    if guilda["lider_id"] == uid and len(guilda["membros"]) > 1:
        return await ctx.send(embed=discord.Embed(
            description=(
                "❌ Você é o **líder**! Não pode sair com membros na guilda.\n"
                "Use `+promover @user` para passar a liderança ou `+disbanda_guilda` para dissolver."
            ),
            color=0xe74c3c,
        ))

    guilda["membros"] = [m for m in guilda["membros"] if m != uid]
    user["guilda"] = None

    # Se guilda ficou vazia, remove
    if not guilda["membros"]:
        del guildas[guilda_nome]

    salvar(dados)
    await ctx.send(embed=discord.Embed(
        description=f"👋 {ctx.author.mention} saiu da guilda **{guilda_nome}**.",
        color=0xe67e22,
    ))

@bot.command(name="disbanda_guilda")
async def cmd_disbanda_guilda(ctx):
    dados   = carregar()
    user    = pegar_user(dados, ctx.author.id)
    guildas = pegar_guildas(dados)

    guilda_nome = user.get("guilda")
    if not guilda_nome or guilda_nome not in guildas:
        return await ctx.send(embed=discord.Embed(description="❌ Você não está em nenhuma guilda!", color=0xe74c3c))

    guilda = guildas[guilda_nome]
    uid    = str(ctx.author.id)

    is_admin = ctx.author.guild_permissions.administrator if ctx.guild else False
    if guilda["lider_id"] != uid and not is_admin:
        return await ctx.send(embed=discord.Embed(description="❌ Apenas o **líder** pode dissolver a guilda!", color=0xe74c3c))

    # Remove guilda de todos os membros
    for mid in guilda["membros"]:
        m_data = dados.get(mid)
        if m_data:
            m_data["guilda"] = None

    del guildas[guilda_nome]
    salvar(dados)

    await ctx.send(embed=discord.Embed(
        title="💥 Guilda Dissolvida",
        description=f"A guilda **{guilda_nome}** foi dissolvida por {ctx.author.mention}.",
        color=0xe74c3c,
    ))

@bot.command(name="promover")
async def cmd_promover(ctx, novo_lider: discord.Member):
    dados   = carregar()
    user    = pegar_user(dados, ctx.author.id)
    guildas = pegar_guildas(dados)

    guilda_nome = user.get("guilda")
    if not guilda_nome or guilda_nome not in guildas:
        return await ctx.send(embed=discord.Embed(description="❌ Você não está em nenhuma guilda!", color=0xe74c3c))

    guilda = guildas[guilda_nome]
    if guilda["lider_id"] != str(ctx.author.id):
        return await ctx.send(embed=discord.Embed(description="❌ Apenas o **líder** pode promover outro membro!", color=0xe74c3c))

    if str(novo_lider.id) not in guilda["membros"]:
        return await ctx.send(embed=discord.Embed(description=f"❌ **{novo_lider.display_name}** não está na guilda!", color=0xe74c3c))

    guilda["lider_id"] = str(novo_lider.id)
    salvar(dados)

    await ctx.send(embed=discord.Embed(
        title="👑 Nova Liderança!",
        description=f"{novo_lider.mention} agora é o **líder** de **{guilda_nome}**!",
        color=0xf39c12,
    ))

@bot.command(name="expulsar")
async def cmd_expulsar(ctx, membro: discord.Member):
    dados   = carregar()
    user    = pegar_user(dados, ctx.author.id)
    guildas = pegar_guildas(dados)

    guilda_nome = user.get("guilda")
    if not guilda_nome or guilda_nome not in guildas:
        return await ctx.send(embed=discord.Embed(description="❌ Você não está em nenhuma guilda!", color=0xe74c3c))

    guilda = guildas[guilda_nome]
    if guilda["lider_id"] != str(ctx.author.id):
        return await ctx.send(embed=discord.Embed(description="❌ Apenas o **líder** pode expulsar membros!", color=0xe74c3c))

    if str(membro.id) not in guilda["membros"]:
        return await ctx.send(embed=discord.Embed(description=f"❌ **{membro.display_name}** não está na guilda!", color=0xe74c3c))

    if membro.id == ctx.author.id:
        return await ctx.send(embed=discord.Embed(description="❌ Você não pode se expulsar!", color=0xe74c3c))

    guilda["membros"] = [m for m in guilda["membros"] if m != str(membro.id)]
    m_data = pegar_user(dados, membro.id)
    m_data["guilda"] = None
    salvar(dados)

    await ctx.send(embed=discord.Embed(
        description=f"👢 **{membro.display_name}** foi expulso de **{guilda_nome}**.",
        color=0xe74c3c,
    ))

@bot.command(name="guilda")
async def cmd_guilda(ctx, *, nome: str = None):
    dados   = carregar()
    guildas = pegar_guildas(dados)

    if nome is None:
        user = pegar_user(dados, ctx.author.id)
        nome = user.get("guilda")
        if not nome:
            return await ctx.send(embed=discord.Embed(
                description="❌ Você não está em nenhuma guilda!\nUse `+guildas` para ver todas ou `+criar_guilda <nome>` para criar.",
                color=0xe74c3c,
            ))

    guilda_key = next((g for g in guildas if g.lower() == nome.lower()), None)
    if not guilda_key:
        return await ctx.send(embed=discord.Embed(description=f"❌ Guilda **{nome}** não encontrada!", color=0xe74c3c))

    guilda = guildas[guilda_key]

    # Calcula dano total da guilda no boss
    boss        = pegar_boss(dados)
    dano_guilda = sum(
        v["dano_total"] for v in boss["participantes"].values()
        if v.get("guilda") == guilda_key
    )

    try:
        lider_user = await bot.fetch_user(int(guilda["lider_id"]))
        lider_nome = lider_user.display_name
    except Exception:
        lider_nome = "Desconhecido"

    membros_str = []
    for mid in guilda["membros"]:
        try:
            m    = await bot.fetch_user(int(mid))
            tag  = " 👑" if mid == guilda["lider_id"] else ""
            u    = pegar_user(dados, int(mid))
            membros_str.append(f"• {m.display_name}{tag} (Nv.{u['level']} | {u['pontos']:,} pts)")
        except Exception:
            membros_str.append(f"• ID:{mid}")

    embed = discord.Embed(
        title=f"🏰 Guilda — {guilda_key}",
        color=0xf39c12,
    )
    embed.add_field(name="👑 Líder",        value=lider_nome,                          inline=True)
    embed.add_field(name="👥 Membros",      value=str(len(guilda["membros"])),           inline=True)
    embed.add_field(name="🗓️ Criada em",   value=guilda.get("criada_em", "?")[:10],    inline=True)
    embed.add_field(
        name="🧑‍🤝‍🧑 Membros da Guilda",
        value="\n".join(membros_str) or "—",
        inline=False,
    )
    if dano_guilda > 0:
        embed.add_field(name="👁️ Dano ao Boss", value=f"`{dano_guilda:,}` de dano total", inline=False)
    embed.set_footer(text="+guilda para ver sua guilda • +atacar_boss para lutar!")
    await ctx.send(embed=embed)

@bot.command(name="guildas")
async def cmd_guildas(ctx):
    dados   = carregar()
    guildas = pegar_guildas(dados)

    if not guildas:
        return await ctx.send(embed=discord.Embed(
            description="❌ Nenhuma guilda criada ainda!\nUse `+criar_guilda <nome>` para criar a primeira!",
            color=0xe74c3c,
        ))

    embed = discord.Embed(
        title="🏰 Todas as Guildas do Servidor",
        description=f"Total: **{len(guildas)}** guilda(s)\n{'━'*30}",
        color=0xf39c12,
    )

    boss = pegar_boss(dados)
    for nome, g in list(guildas.items())[:10]:
        dano_total = sum(
            v["dano_total"] for v in boss["participantes"].values()
            if v.get("guilda") == nome
        )
        try:
            lider = await bot.fetch_user(int(g["lider_id"]))
            lider_nome = lider.display_name
        except Exception:
            lider_nome = "?"
        boss_tag = f"\n👁️ Boss: `{dano_total:,}` dano" if dano_total > 0 else ""
        embed.add_field(
            name=f"🏰 {nome}",
            value=f"👑 Líder: {lider_nome}\n👥 {len(g['membros'])} membro(s){boss_tag}",
            inline=True,
        )

    embed.set_footer(text="+guilda <nome> para mais detalhes • +criar_guilda <nome> para criar")
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  WORLD BOSS — +boss / +atacar_boss
# ═══════════════════════════════════════════════════════

@bot.command(name="boss")
async def cmd_boss(ctx):
    dados = carregar()
    boss  = pegar_boss(dados)

    if boss.get("morto"):
        venc = boss.get("vencedor_nome", "Alguém")
        embed = discord.Embed(
            title=f"💀 {BOSS_EMOJI} {BOSS_NOME} — DERROTADO",
            description=(
                f"O boss foi derrotado! O **Chinelo do Fpyy** foi entregue a **{venc}**!\n\n"
                f"Aguarde o admin invocar o próximo boss com `+invocar_boss`."
            ),
            color=0x95a5a6,
        )
        return await ctx.send(embed=embed)

    if not boss.get("ativo"):
        embed = discord.Embed(
            title=f"😴 {BOSS_EMOJI} Nenhum Boss Ativo",
            description=(
                "Nenhum World Boss está ativo no momento.\n"
                "Aguarde um administrador invocar o boss com `+invocar_boss`!\n\n"
                "⚠️ **Você precisa estar em uma guilda para atacar!**"
            ),
            color=0x95a5a6,
        )
        return await ctx.send(embed=embed)

    hp_at   = max(boss["hp_atual"], 0)
    hp_max  = boss["hp_max"]
    pct     = hp_at / hp_max * 100
    barra   = boss_barra_hp(boss)
    n_part  = len(boss["participantes"])

    # Top atacantes
    top = sorted(boss["participantes"].items(), key=lambda x: x[1]["dano_total"], reverse=True)[:5]
    top_str = []
    for i, (uid, info) in enumerate(top):
        medals = ["🥇","🥈","🥉","🏅","🏅"]
        top_str.append(f"{medals[i]} **{info['nome']}** [{info.get('guilda','?')}] — `{info['dano_total']:,}`")

    embed = discord.Embed(
        title=f"{BOSS_EMOJI} WORLD BOSS — {BOSS_NOME}",
        description=(
            f"**O terror do servidor está ativo! Derrote-o em equipe!**\n"
            f"🩴 *Recompensa: O **Chinelo do Fpyy** (100k dano + todos os buffs)*\n\n"
            f"{barra}\n"
            f"❤️ **HP: {hp_at:,} / {hp_max:,}** ({pct:.2f}%)\n\n"
            f"⚔️ Atacantes: **{n_part}**"
        ),
        color=0xff0000 if pct < 25 else (0xff8800 if pct < 60 else 0x8b0000),
    )
    if top_str:
        embed.add_field(
            name="🏆 Top Atacantes",
            value="\n".join(top_str),
            inline=False,
        )
    embed.add_field(
        name="💡 Como participar",
        value=(
            "1️⃣ Entre em uma guilda: `+entrar_guilda <nome>`\n"
            "2️⃣ Ataque o boss: `+atacar_boss` (60s cooldown)\n"
            "3️⃣ Quando morrer: **1 atacante aleatório** ganha o 🩴 **Chinelo do Fpyy**!"
        ),
        inline=False,
    )
    embed.set_footer(text=f"Invocado em: {boss.get('spawned_em', '?')}")
    await ctx.send(embed=embed)


@bot.command(name="atacar_boss")
async def cmd_atacar_boss(ctx):
    dados = carregar()
    user  = pegar_user(dados, ctx.author.id)
    boss  = pegar_boss(dados)
    agora = datetime.now()

    # ── Validações ───────────────────────────────────────
    if not boss.get("ativo") or boss.get("morto"):
        return await ctx.send(embed=discord.Embed(
            description="❌ Não há World Boss ativo! Aguarde `+invocar_boss`.",
            color=0xe74c3c,
        ))

    guilda_nome = user.get("guilda")
    if not guilda_nome:
        return await ctx.send(embed=discord.Embed(
            description=(
                "❌ Você precisa estar em uma **guilda** para atacar o World Boss!\n"
                "Use `+criar_guilda <nome>` ou `+entrar_guilda <nome>`."
            ),
            color=0xe74c3c,
        ))

    ultimo_str = user.get("ultimo_atacar_boss")
    if ultimo_str:
        ultimo  = datetime.strptime(ultimo_str, "%Y-%m-%d %H:%M:%S")
        proximo = ultimo + timedelta(seconds=60)
        if agora < proximo:
            espera = int((proximo - agora).total_seconds())
            return await ctx.send(embed=discord.Embed(
                description=f"⏳ Recuperando do ataque! Aguarde **{espera}s**.",
                color=0xe67e22,
            ))

    # ── Cálculo de dano ──────────────────────────────────
    dano_base = dano_arma(user)
    # Variação ±30%, mínimo 1
    dano_real  = max(1, random.randint(int(dano_base * 0.70), int(dano_base * 1.30)))
    critico    = random.random() < 0.15
    crit_mult  = 1.8
    for b in get_buffs_ativos(user):
        if b["efeito"] == "critico":
            crit_mult *= b["mult"]
    if critico:
        dano_real = int(dano_real * crit_mult)

    # Bônus de guilda: +10% se tiver ≥3 membros atacando
    guildas       = pegar_guildas(dados)
    guilda_data   = guildas.get(guilda_nome, {})
    membros_boss  = [v for v in boss["participantes"].values() if v.get("guilda") == guilda_nome]
    if len(membros_boss) >= 2:
        dano_real = int(dano_real * 1.10)  # +10% bônus de grupo

    boss["hp_atual"] = max(0, boss["hp_atual"] - dano_real)

    # Atualiza participante
    uid_str = str(ctx.author.id)
    if uid_str not in boss["participantes"]:
        boss["participantes"][uid_str] = {
            "dano_total": 0,
            "guilda":     guilda_nome,
            "nome":       ctx.author.display_name,
        }
    boss["participantes"][uid_str]["dano_total"] += dano_real
    boss["participantes"][uid_str]["nome"]        = ctx.author.display_name

    user["ultimo_atacar_boss"] = agora.strftime("%Y-%m-%d %H:%M:%S")

    # ── Contra-ataque do boss ─────────────────────────────
    boss_atk_dano = random.randint(BOSS_DANO_MIN, BOSS_DANO_MAX)
    boss_atk_nome = random.choice(BOSS_ATAQUES)

    hp_at  = max(boss["hp_atual"], 0)
    hp_max = boss["hp_max"]
    pct    = hp_at / hp_max * 100
    barra  = boss_barra_hp(boss)
    crit_txt = " ✦ **CRÍTICO!**" if critico else ""

    # ── Verifica se boss morreu ───────────────────────────
    boss_morreu = boss["hp_atual"] <= 0

    if boss_morreu:
        # Escolhe vencedor: 1 participante aleatório (de qualquer guilda)
        participantes_lista = list(boss["participantes"].keys())
        vencedor_uid = random.choice(participantes_lista)
        vencedor_info = boss["participantes"][vencedor_uid]
        vencedor_nome = vencedor_info["nome"]

        boss["morto"]         = True
        boss["ativo"]         = False
        boss["vencedor_id"]   = vencedor_uid
        boss["vencedor_nome"] = vencedor_nome

        # Dá o Chinelo ao vencedor
        venc_user = pegar_user(dados, int(vencedor_uid))
        glob      = pegar_globals(dados)

        ja_tem_chinelo = "Chinelo do Fpyy" in venc_user.get("espadas", [])

        if not ja_tem_chinelo:
            venc_user.setdefault("espadas", []).append("Chinelo do Fpyy")
            venc_user.setdefault("itens_secretos", []).append("Chinelo do Fpyy")
            glob["chinelo_revelado"]  = True
            glob["chinelo_dono_id"]   = vencedor_uid
            glob["chinelo_dono_nome"] = vencedor_nome
            recompensa_txt = f"🩴 **CHINELO DO FPYY** (100.000 de dano + todos os buffs!)"
        else:
            # Vencedor já tem o chinelo, dá pontos massivos
            bonus_pts = 5_000_000
            venc_user["pontos"] += bonus_pts
            recompensa_txt = f"💰 **{bonus_pts:,} pontos** (já possuía o Chinelo!)"

        # Recompensa para TODOS os participantes
        for pid, pinfo in boss["participantes"].items():
            p_user = pegar_user(dados, int(pid))
            p_user["pontos"] += BOSS_RECOMPENSA_DANO_BONUS
            p_user["xp"]     += BOSS_RECOMPENSA_XP
            p_user["vitorias"] = p_user.get("vitorias", 0) + 1

        salvar(dados)

        # Embed de vitória épica
        n_part = len(boss["participantes"])
        anuncio = discord.Embed(
            title=f"💀 {BOSS_EMOJI} {BOSS_NOME} FOI DERROTADO! 💀",
            description=(
                f"# 🎉 VITÓRIA DO SERVIDOR! 🎉\n\n"
                f"**{n_part} guerreiro(s)** uniram forças e derrotaram o boss!\n\n"
                f"🎲 O destino escolheu...\n"
                f"# 🏆 **{vencedor_nome}** 🏆\n\n"
                f"🎁 **Recompensa:** {recompensa_txt}\n\n"
                f"✨ **Todos os participantes** receberam:\n"
                f"💰 `+{BOSS_RECOMPENSA_DANO_BONUS:,} pts` e `+{BOSS_RECOMPENSA_XP:,} XP`!\n\n"
                f"*O próximo boss pode ser invocado por um admin!*"
            ),
            color=0xff69b4,
        )
        anuncio.set_footer(text=f"Boss derrotado por {n_part} jogador(es)!")
        await ctx.send(embed=anuncio)
        return

    # ── Embed de ataque normal ────────────────────────────
    dano_total_player = boss["participantes"][uid_str]["dano_total"]
    salvar(dados)

    embed = discord.Embed(
        title=f"⚔️ {BOSS_EMOJI} Ataque ao World Boss!",
        color=0x8b0000,
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.add_field(
        name=f"💥 {ctx.author.display_name} atacou!{crit_txt}",
        value=(
            f"⚔️ Seu dano: **{dano_real:,}**\n"
            f"🏰 Guilda: **{guilda_nome}**\n"
            f"📊 Seu total: **{dano_total_player:,}**"
        ),
        inline=True,
    )
    embed.add_field(
        name=f"😡 {BOSS_NOME} contra-ataca!",
        value=(
            f"O boss **{boss_atk_nome}**!\n"
            f"💥 Dano narrativo: **{boss_atk_dano:,}**\n"
            f"*(Dano ao boss, não ao jogador)*"
        ),
        inline=True,
    )
    embed.add_field(
        name=f"❤️ HP do Boss — {pct:.1f}%",
        value=f"{barra}\n`{hp_at:,} / {hp_max:,}`",
        inline=False,
    )
    embed.set_footer(text=f"Cooldown: 60s • Participantes: {len(boss['participantes'])} • +boss para status completo")
    await ctx.send(embed=embed)

    await verificar_levelup(ctx.channel, ctx.author, user)
    salvar(dados)


# ═══════════════════════════════════════════════════════
#  ADMIN: +invocar_boss
# ═══════════════════════════════════════════════════════

@bot.command(name="invocar_boss")
@commands.has_permissions(administrator=True)
async def cmd_invocar_boss(ctx):
    dados = carregar()
    boss  = pegar_boss(dados)

    if boss.get("ativo"):
        hp_at = max(boss["hp_atual"], 0)
        return await ctx.send(embed=discord.Embed(
            description=f"❌ Já existe um boss ativo com **{hp_at:,} HP**! Derrotem-no primeiro!",
            color=0xe74c3c,
        ))

    # Reseta o boss
    dados["_boss"] = {
        "ativo":         True,
        "hp_atual":      BOSS_HP_MAX,
        "hp_max":        BOSS_HP_MAX,
        "participantes": {},
        "morto":         False,
        "vencedor_id":   None,
        "vencedor_nome": None,
        "spawned_em":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    salvar(dados)

    embed = discord.Embed(
        title=f"☄️ WORLD BOSS INVOCADO! {BOSS_EMOJI}",
        description=(
            f"# {BOSS_EMOJI} {BOSS_NOME} {BOSS_EMOJI}\n\n"
            f"**O terror primordial chegou ao servidor!**\n\n"
            f"❤️ HP: **{BOSS_HP_MAX:,}**\n"
            f"⚔️ Ataques: Devastadores\n"
            f"🩴 **Recompensa:** Chinelo do Fpyy (100k dano + TODOS os buffs)\n\n"
            f"**Como participar:**\n"
            f"1️⃣ Tenha uma guilda (`+criar_guilda` ou `+entrar_guilda`)\n"
            f"2️⃣ Use `+atacar_boss` para atacar (cooldown 60s)\n"
            f"3️⃣ Quando morrer, **1 atacante aleatório** ganha o 🩴!\n\n"
            f"*Todos os participantes ganham pontos e XP ao derrotar!*"
        ),
        color=0xff0000,
    )
    embed.set_footer(text="Unam-se! Formem guildas! Derrote o boss!")
    await ctx.send(embed=embed)


# ═══════════════════════════════════════════════════════
#  COMANDO: +top
# ═══════════════════════════════════════════════════════

@bot.command(name="top")
async def cmd_top(ctx, categoria: str = "pontos"):
    dados = carregar()
    valid = {k: v for k, v in dados.items() if not k.startswith("_")}

    mapa = {
        "pontos":   ("pontos",   "💰 TOP 10 — Pontos",       lambda x: x[1].get("pontos", 0)),
        "kills":    ("kills",    "⚔️ TOP 10 — Kills PvP",    lambda x: x[1].get("kills", 0)),
        "nivel":    ("level",    "⭐ TOP 10 — Nível",         lambda x: x[1].get("level", 1)),
        "vitorias": ("vitorias", "🏆 TOP 10 — Vitórias PvE", lambda x: x[1].get("vitorias", 0)),
        "derrotas": ("derrotas", "💀 TOP 10 — Derrotas",     lambda x: x[1].get("derrotas", 0)),
        "mortes":   ("mortes",   "🪦 TOP 10 — Mortes PvP",   lambda x: x[1].get("mortes", 0)),
    }

    if categoria.lower() not in mapa:
        return await ctx.send(embed=discord.Embed(
            description="❌ Categoria inválida!\nUse: `pontos` · `kills` · `nivel` · `vitorias` · `derrotas` · `mortes`",
            color=0xe74c3c,
        ))

    campo, titulo, key_fn = mapa[categoria.lower()]
    ranking = sorted(valid.items(), key=key_fn, reverse=True)[:10]

    embed = discord.Embed(title=titulo, color=0xf1c40f)
    linhas = []
    for i, (uid, info) in enumerate(ranking):
        try:
            m    = await bot.fetch_user(int(uid))
            nome = m.display_name
        except Exception:
            nome = "Desconhecido"
        valor = info.get(campo, 0)
        linhas.append(f"{MEDALHAS[i]} **{nome}** — `{valor:,}`")

    embed.description = "\n".join(linhas) if linhas else "Ninguém ainda!"
    embed.set_footer(text="+top pontos | kills | nivel | vitorias | derrotas | mortes")
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  FUNÇÃO AUXILIAR: abrir_bau_generico
# ═══════════════════════════════════════════════════════

async def abrir_bau_generico(ctx, preco: int, pool: dict, titulo: str, emoji: str, cor: int, descricao_preview: str):
    dados = carregar()
    user  = pegar_user(dados, ctx.author.id)

    armas_pool = list(pool.keys())

    if user["pontos"] < preco:
        faltam = preco - user["pontos"]
        nomes_mist = "  •  ".join(["???" for _ in armas_pool])
        embed = discord.Embed(
            title=f"{emoji} {titulo}",
            description=(
                f"**Custo:** `{preco:,} pontos`\n"
                f"**Você tem:** `{user['pontos']:,}` ❌  |  Faltam: `{faltam:,}`\n\n"
                f"{descricao_preview}\n\n"
                f"**Itens:** `{nomes_mist}`"
            ),
            color=cor,
        )
        embed.set_footer(text="Continue acumulando pontos para abrir!")
        return await ctx.send(embed=embed)

    possuidas   = set(user.get("espadas", [])) | set(user.get("itens_secretos", []))
    disponiveis = [k for k in armas_pool if k not in possuidas]

    if not disponiveis:
        return await ctx.send(embed=discord.Embed(
            description=f"🎉 Você já possui **todos** os itens deste baú!\nAguarde novos itens...",
            color=0xf39c12,
        ))

    user["pontos"] -= preco
    item_ganho = random.choice(disponiveis)
    user.setdefault("espadas", []).append(item_ganho)
    user.setdefault("itens_secretos", []).append(item_ganho)
    salvar(dados)

    it    = pool[item_ganho]
    cor_r = CORES_RARIDADE.get(it["raridade"], cor)
    embed = discord.Embed(
        title=f"{emoji} BAÚ ABERTO!",
        description=(
            f"✨ {ctx.author.mention} revelou o item secreto...\n\n"
            f"# {it['emoji']} **{item_ganho}** {it['emoji']}\n\n"
            f"⚡ Dano: **{it['dano']:,}** | ✨ {it['raridade']}\n\n"
            f"*Este item não está disponível em nenhuma loja!*"
        ),
        color=cor_r,
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.add_field(name="💳 Saldo Restante", value=f"`{user['pontos']:,} pts`", inline=True)
    embed.set_footer(text=f"Use +equipar {item_ganho} para usar em combate!")
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  BAÚS
# ═══════════════════════════════════════════════════════

@bot.command(name="bau")
async def cmd_bau(ctx):
    await abrir_bau_generico(ctx, preco=PRECO_BAU, pool=ARMAS_BAU_ORIGINAL,
        titulo="Baú Secreto", emoji="🗝️", cor=0x2c3e50,
        descricao_preview="*Este baú contém armas secretas que não existem em nenhuma loja.*\n*Ao abrir você recebe **garantidamente** uma arma secreta!*")

@bot.command(name="bau_sombrio")
async def cmd_bau_sombrio(ctx):
    await abrir_bau_generico(ctx, preco=PRECO_BAU_SOMBRIO, pool=ARMAS_BAU_SOMBRIO,
        titulo="Baú das Sombras", emoji="🖤", cor=0x1a1a2e,
        descricao_preview="*Forjadas nas trevas absolutas. Armas que nunca viram a luz.*\n*Dano letal — só para os ricos do servidor.*")

@bot.command(name="bau_celestial")
async def cmd_bau_celestial(ctx):
    await abrir_bau_generico(ctx, preco=PRECO_BAU_CELESTIAL, pool=ARMAS_BAU_CELESTIAL,
        titulo="Baú Celestial", emoji="🌟", cor=0xfff176,
        descricao_preview="*Bênçãos dos deuses encarnadas em aço e luz.*\n*Apenas os mais poderosos podem empunhá-las.*")

@bot.command(name="bau_caos")
async def cmd_bau_caos(ctx):
    await abrir_bau_generico(ctx, preco=PRECO_BAU_CAOS, pool=ARMAS_BAU_CAOS,
        titulo="Baú do Caos Supremo", emoji="💥", cor=0xff4444,
        descricao_preview="*O caos primordial cristalizado em armas impossíveis.*\n*Quase tão fortes quanto o lendário Chinelo do Fpyy.*")

# ═══════════════════════════════════════════════════════
#  COMANDO: +caixa_chinelo
# ═══════════════════════════════════════════════════════

@bot.command(name="caixa_chinelo")
async def cmd_caixa_chinelo(ctx):
    dados = carregar()
    user  = pegar_user(dados, ctx.author.id)
    glob  = pegar_globals(dados)

    ja_revelado = glob.get("chinelo_revelado", False)
    nome_mist   = "Chinelo do Fpyy" if ja_revelado else "???"
    dono_nome   = glob.get("chinelo_dono_nome", "")
    chance_txt  = f"{CHANCE_CHINELO * 100:.4f}%"

    if "Chinelo do Fpyy" in user.get("espadas", []):
        return await ctx.send(embed=discord.Embed(
            description=f"🩴 Você já possui o **Chinelo do Fpyy**! Só pode ter um.\n⚡ Dano: **100.000** + TODOS os buffs!",
            color=0xff69b4,
        ))

    if user["pontos"] < PRECO_CAIXA_CHINELO:
        embed = discord.Embed(
            title="🎁 Caixa Misteriosa do ???",
            description=(
                f"**Custo por abertura:** `{PRECO_CAIXA_CHINELO:,} pontos`\n"
                f"**Você tem:** `{user['pontos']:,}` ❌\n\n"
                f"Esta caixa contém **1 único item**: **{nome_mist}**\n"
                f"⚡ Poder: **100.000 de dano + TODOS os buffs acumulados!**\n"
                f"🎲 Chance de obter: **`{chance_txt}`** *(1 em 1.000.000!)*\n"
                f"❌ Se não ganhar — **não recebe nada**.\n\n"
                f"💡 *Também é possível obter o Chinelo matando o* **👁️ World Boss!**\n\n"
            ) + (
                f"✅ Item já revelado: **Chinelo do Fpyy** — obtido por **{dono_nome}**!"
                if ja_revelado else
                "🔒 O item ??? ainda não foi revelado por ninguém no servidor..."
            ),
            color=0xff69b4,
        )
        return await ctx.send(embed=embed)

    user["pontos"] -= PRECO_CAIXA_CHINELO
    ganhou = random.random() < CHANCE_CHINELO

    if ganhou:
        user.setdefault("espadas", []).append("Chinelo do Fpyy")
        user.setdefault("itens_secretos", []).append("Chinelo do Fpyy")
        glob["chinelo_revelado"]  = True
        glob["chinelo_dono_id"]   = str(ctx.author.id)
        glob["chinelo_dono_nome"] = ctx.author.display_name
        salvar(dados)

        anuncio = discord.Embed(
            title="🌈🩴 O MISTÉRIO FOI REVELADO! 🩴🌈",
            description=(
                f"# 🩴 CHINELO DO FPYY 🩴\n\n"
                f"**{ctx.author.mention}** conseguiu o item mais raro do servidor!\n\n"
                f"O item **???** foi finalmente revelado como:\n"
                f"# **✨ CHINELO DO FPYY ✨**\n\n"
                f"⚡ Dano: **100.000** — A arma mais forte do jogo!\n"
                f"🌀 **Acumula TODOS os buffs do jogo automaticamente!**\n"
                f"✨ Raridade: **🌈 ABSURDA**\n"
                f"🎲 Chance: **{chance_txt}** (1 em 1.000.000)\n"
                f"📦 Obtido via: **Caixa Misteriosa**\n\n"
                f"*Histórico! Parabéns, lenda do servidor!* 🏆"
            ),
            color=0xff69b4,
        )
        anuncio.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=anuncio)
    else:
        salvar(dados)
        embed = discord.Embed(
            title="📦 Caixa Aberta... Nada.",
            description=(
                f"Você abriu a caixa e encontrou... **nada**. 😔\n\n"
                f"O item **{nome_mist}** não estava desta vez.\n"
                f"*(100.000 de dano + todos os buffs — vale cada tentativa!)*\n\n"
                f"🎲 Chance: **`{chance_txt}`** *(1 em 1.000.000)*\n"
                f"💰 Saldo restante: `{user['pontos']:,} pts`\n\n"
                f"💡 *Dica: Derrote o **👁️ World Boss** para outra chance de obter!*\n\n"
            ) + (
                f"🔓 Item revelado: **Chinelo do Fpyy** — já obtido por **{dono_nome}**."
                if ja_revelado else
                "🔒 O item ??? ainda não foi revelado... tente de novo!"
            ),
            color=0x7f8c8d,
        )
        embed.set_footer(text=f"Chances: {chance_txt} • Continue tentando!")
        await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  OUTROS COMANDOS
# ═══════════════════════════════════════════════════════

@bot.command(name="top_secretos")
async def cmd_top_secretos(ctx):
    dados = carregar()
    valid = {k: v for k, v in dados.items() if not k.startswith("_")}
    ranking = sorted(valid.items(), key=lambda x: len(x[1].get("itens_secretos", [])), reverse=True)[:10]

    embed = discord.Embed(title="🌑 TOP 10 — Colecionadores de Itens Secretos", color=0x2c3e50)
    linhas = []
    for i, (uid, info) in enumerate(ranking):
        try:
            m    = await bot.fetch_user(int(uid))
            nome = m.display_name
        except Exception:
            nome = "Desconhecido"
        qtd     = len(info.get("itens_secretos", []))
        chinelo = " 🩴" if "Chinelo do Fpyy" in info.get("espadas", []) else ""
        linhas.append(f"{MEDALHAS[i]} **{nome}**{chinelo} — `{qtd} itens secretos`")

    embed.description = "\n".join(linhas) if linhas else "Ninguém ainda!"
    embed.set_footer(text="Use +bau / +bau_sombrio / +bau_celestial / +bau_caos / mate o Boss!")
    await ctx.send(embed=embed)

@bot.command(name="status_chinelo")
async def cmd_status_chinelo(ctx):
    dados = carregar()
    glob  = pegar_globals(dados)
    boss  = pegar_boss(dados)

    boss_ativo = boss.get("ativo", False)
    boss_hp    = max(boss.get("hp_atual", 0), 0)

    if glob.get("chinelo_revelado"):
        dono = glob.get("chinelo_dono_nome", "Alguém")
        embed = discord.Embed(
            title="🩴 Status do Chinelo do Fpyy",
            description=(
                f"✅ **O Chinelo do Fpyy foi obtido!**\n\n"
                f"🏆 Dono: **{dono}**\n"
                f"⚡ Dano: **100.000** — A arma mais forte!\n"
                f"🌀 **Acumula TODOS os buffs do jogo!**\n"
                f"✨ Raridade: **🌈 ABSURDA**\n\n"
                f"**Formas de obter:**\n"
                f"📦 Caixa: `{CHANCE_CHINELO * 100:.4f}%` de chance\n"
                f"👁️ World Boss: **100%** (1 atacante aleatório vence)"
            ),
            color=0xff69b4,
        )
    else:
        boss_str = (
            f"👁️ Boss ativo! HP: **{boss_hp:,}** — use `+atacar_boss`!"
            if boss_ativo else
            f"👁️ Nenhum boss ativo. Admin pode usar `+invocar_boss`."
        )
        embed = discord.Embed(
            title="🩴 Status do Chinelo do Fpyy",
            description=(
                f"🔒 **O ??? ainda não foi revelado!**\n\n"
                f"**Formas de obter:**\n\n"
                f"📦 **Caixa Misteriosa** (`+caixa_chinelo`)\n"
                f"🎲 Chance: **0,0001%** (1 em 1.000.000)\n"
                f"💰 Custo por tentativa: **{PRECO_CAIXA_CHINELO:,} pts**\n\n"
                f"👁️ **World Boss** (`+atacar_boss`)\n"
                f"🎲 Chance: **100%** — quem matar o boss, 1 atacante aleatório GANHA!\n"
                f"⚠️ Requer guilda!\n\n"
                f"{boss_str}"
            ),
            color=0x2c3e50,
        )
    await ctx.send(embed=embed)

@bot.command(name="baus_info")
async def cmd_baus_info(ctx):
    embed = discord.Embed(
        title="🗃️ Todos os Baús Secretos",
        description="Cada baú garante itens exclusivos que não existem na loja!\n" + "━"*35,
        color=0x9b59b6,
    )
    embed.add_field(name="🗝️ Baú Secreto — `+bau`",
        value=f"💰 `{PRECO_BAU:,} pts`\n⚡ Dano: 500–850\n✨ ⬛ Secreta\n📦 {len(ARMAS_BAU_ORIGINAL)} itens", inline=True)
    embed.add_field(name="🖤 Baú das Sombras — `+bau_sombrio`",
        value=f"💰 `{PRECO_BAU_SOMBRIO:,} pts`\n⚡ Dano: 3k–7.5k\n✨ 🖤 Sombria\n📦 {len(ARMAS_BAU_SOMBRIO)} itens", inline=True)
    embed.add_field(name="🌟 Baú Celestial — `+bau_celestial`",
        value=f"💰 `{PRECO_BAU_CELESTIAL:,} pts`\n⚡ Dano: 8k–28k\n✨ 🌟 Celestial\n📦 {len(ARMAS_BAU_CELESTIAL)} itens", inline=True)
    embed.add_field(name="💥 Baú do Caos — `+bau_caos`",
        value=f"💰 `{PRECO_BAU_CAOS:,} pts`\n⚡ Dano: 35k–95k\n✨ 💥 Caos\n📦 {len(ARMAS_BAU_CAOS)} itens", inline=True)
    embed.add_field(name="🩴 Caixa Chinelo — `+caixa_chinelo`",
        value=f"💰 `{PRECO_CAIXA_CHINELO:,} pts`\n⚡ Dano: **100k** + TODOS buffs!\n🎲 **0,0001%** chance", inline=True)
    embed.add_field(name="👁️ World Boss — `+atacar_boss`",
        value=f"💰 Grátis (requer guilda!)\n⚡ Dano: **100k** + TODOS buffs!\n🎲 **100%** — 1 atacante aleatório!", inline=True)
    embed.set_footer(text="Use +top_secretos para ver os maiores colecionadores!")
    await ctx.send(embed=embed)

@bot.command(name="monstros")
async def cmd_monstros(ctx):
    embed = discord.Embed(
        title="👹 Bestiário — Todos os Inimigos",
        description="Inimigos mais fortes surgem em níveis mais altos!\n" + "━"*35,
        color=0xe74c3c,
    )
    for ini in INIMIGOS:
        embed.add_field(
            name=f"{ini['emoji']} {ini['nome']}",
            value=(
                f"❤️ HP: `{ini['hp']:,}`\n"
                f"⚔️ Dano: `{ini['dano_min']:,}–{ini['dano_max']:,}`\n"
                f"💰 Rec: `{ini['rec']:,}` pts\n"
                f"✨ XP: `{ini['xp']:,}`"
            ),
            inline=True,
        )
    embed.set_footer(text="Use +lutar para batalhar! Nível mais alto = inimigos mais fortes.")
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  COMANDO: +ajuda
# ═══════════════════════════════════════════════════════

@bot.command(name="ajuda")
async def cmd_ajuda(ctx):
    embed = discord.Embed(
        title="📖 Comandos do Bot",
        description="Prefixo: `+`",
        color=0x9b59b6,
    )
    embed.add_field(
        name="💰 Economia",
        value=(
            "`+pontos [@user]` — Pontos e status\n"
            "`+daily` — Bônus diário\n"
            "`+apostar <valor>` — 50% de dobrar (limite 10M)\n"
            "`+doar <@user> <valor>` — Doe pontos\n"
        ),
        inline=False,
    )
    embed.add_field(
        name="⚔️ Combate & Perfil",
        value=(
            "`+lutar` — Lute vs inimigos (30s cooldown)\n"
            "`+monstros` — Ver todos os 14 inimigos\n"
            "`+duelar <@user> <valor>` — Duelo PvP\n"
            "`+aceitar` / `+recusar` — Responder duelo\n"
            "`+perfil [@user]` — Perfil completo\n"
        ),
        inline=False,
    )
    embed.add_field(
        name="🏰 Sistema de Guildas",
        value=(
            f"`+criar_guilda <nome>` — Criar guilda ({PRECO_CRIAR_GUILDA:,} pts)\n"
            "`+entrar_guilda <nome>` — Entrar em uma guilda\n"
            "`+sair_guilda` — Sair da guilda\n"
            "`+disbanda_guilda` — Dissolver (líder)\n"
            "`+promover @user` — Passar liderança\n"
            "`+expulsar @user` — Expulsar membro (líder)\n"
            "`+guilda [nome]` — Ver info da guilda\n"
            "`+guildas` — Listar todas as guildas\n"
        ),
        inline=False,
    )
    embed.add_field(
        name="👁️ World Boss",
        value=(
            "`+boss` — Status do World Boss\n"
            "`+atacar_boss` — Atacar boss (60s cooldown, requer guilda!)\n"
            "🏆 **Recompensa:** Chinelo do Fpyy (100k dano!) para 1 atacante aleatório!\n"
            "✨ **Todos** os participantes ganham pontos e XP!\n"
        ),
        inline=False,
    )
    embed.add_field(
        name="🏪 Loja & Inventário (30+ armas!)",
        value=(
            "`+loja [1-7]` — Armas por tier (7 tiers!)\n"
            "`+comprar <nome>` — Comprar arma\n"
            "`+equipar <nome>` — Equipar arma\n"
            "`+inventario [@user]` — Ver armas\n"
            "`+armaduras` — Loja de armaduras\n"
            "`+comprar_armadura <nome>` — Comprar armadura\n"
            "`+vestir <nome>` — Equipar armadura\n"
            "`+inventario_armadura [@user]` — Ver armaduras\n"
        ),
        inline=False,
    )
    embed.add_field(
        name="⚗️ Buffs",
        value=(
            "`+buffs_loja` — Loja de buffs temporários\n"
            "`+comprar_buff <nome>` — Ativar buff\n"
            "`+meus_buffs` — Ver buffs ativos\n"
            "*🩴 O Chinelo do Fpyy acumula TODOS os buffs!*\n"
        ),
        inline=False,
    )
    embed.add_field(
        name="🗃️ Baús Secretos",
        value=(
            f"`+baus_info` — Ver todos os baús\n"
            f"`+bau` — Baú Secreto ({PRECO_BAU:,} pts)\n"
            f"`+bau_sombrio` — Baú das Sombras ({PRECO_BAU_SOMBRIO:,} pts)\n"
            f"`+bau_celestial` — Baú Celestial ({PRECO_BAU_CELESTIAL:,} pts)\n"
            f"`+bau_caos` — Baú do Caos ({PRECO_BAU_CAOS:,} pts)\n"
            f"`+caixa_chinelo` — 0,0001% p/ **100k dano + TODOS buffs**!\n"
            "`+status_chinelo` — Status do item ???\n"
        ),
        inline=False,
    )
    embed.add_field(
        name="🏆 Rankings",
        value=(
            "`+top [pontos|kills|nivel|vitorias|derrotas|mortes]`\n"
            "`+top_secretos` — Ranking de itens secretos\n"
        ),
        inline=False,
    )
    embed.add_field(
        name="💡 Como ganhar pontos?",
        value="Mande mensagens! Cada mensagem dá **1–4 pts** e **XP** automaticamente.",
        inline=False,
    )
    embed.set_footer(text="Bot de RPG • Desenvolvido com discord.py")
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════
#  COMANDOS DE ADMIN
# ═══════════════════════════════════════════════════════

@bot.command(name="setar_pontos")
@commands.has_permissions(administrator=True)
async def cmd_setar_pontos(ctx, membro: discord.Member, valor: int):
    dados = carregar()
    user  = pegar_user(dados, membro.id)
    user["pontos"] = valor
    salvar(dados)
    await ctx.send(embed=discord.Embed(
        description=f"⚙️ **{membro.display_name}** agora tem **{valor:,} pontos**.", color=0x3498db))

@bot.command(name="dar_pontos")
@commands.has_permissions(administrator=True)
async def cmd_dar_pontos(ctx, membro: discord.Member, valor: int):
    dados = carregar()
    user  = pegar_user(dados, membro.id)
    user["pontos"] += valor
    salvar(dados)
    await ctx.send(embed=discord.Embed(
        description=f"⚙️ **+{valor:,}** adicionados a **{membro.display_name}**. Total: **{user['pontos']:,}**", color=0x3498db))

@bot.command(name="resetar")
@commands.has_permissions(administrator=True)
async def cmd_resetar(ctx, membro: discord.Member):
    dados = carregar()
    uid   = str(membro.id)
    # Remove da guilda antes de resetar
    if uid in dados and dados[uid].get("guilda"):
        guilda_nome = dados[uid]["guilda"]
        guildas = pegar_guildas(dados)
        if guilda_nome in guildas:
            guildas[guilda_nome]["membros"] = [m for m in guildas[guilda_nome]["membros"] if m != uid]
    if uid in dados:
        dados.pop(uid)
        salvar(dados)
    await ctx.send(embed=discord.Embed(
        description=f"⚙️ Perfil de **{membro.display_name}** resetado.", color=0xe74c3c))

@bot.command(name="dar_arma_secreta")
@commands.has_permissions(administrator=True)
async def cmd_dar_arma_secreta(ctx, membro: discord.Member, *, nome: str):
    key = next((k for k in ARMAS_SECRETAS if k.lower() == nome.lower()), None)
    if not key:
        return await ctx.send(embed=discord.Embed(
            description=f"❌ Arma secreta `{nome}` não existe!", color=0xe74c3c))
    dados = carregar()
    user  = pegar_user(dados, membro.id)
    if key not in user.get("espadas", []):
        user.setdefault("espadas", []).append(key)
    if key not in user.get("itens_secretos", []):
        user.setdefault("itens_secretos", []).append(key)
    if key == "Chinelo do Fpyy":
        glob = pegar_globals(dados)
        glob["chinelo_revelado"]  = True
        glob["chinelo_dono_id"]   = str(membro.id)
        glob["chinelo_dono_nome"] = membro.display_name
    salvar(dados)
    it = ARMAS_SECRETAS[key]
    await ctx.send(embed=discord.Embed(
        description=f"⚙️ **{key}** ({it['emoji']} ⚡{it['dano']:,} dano) concedido a **{membro.display_name}**.", color=0x2c3e50))

@bot.command(name="resetar_boss")
@commands.has_permissions(administrator=True)
async def cmd_resetar_boss(ctx):
    """Admin: reseta o boss sem invocar"""
    dados = carregar()
    dados["_boss"] = {
        "ativo": False, "hp_atual": BOSS_HP_MAX, "hp_max": BOSS_HP_MAX,
        "participantes": {}, "morto": False,
        "vencedor_id": None, "vencedor_nome": None, "spawned_em": None,
    }
    salvar(dados)
    await ctx.send(embed=discord.Embed(description="⚙️ Boss resetado. Use `+invocar_boss` para invocar.", color=0x3498db))

# ═══════════════════════════════════════════════════════
#  START
# ═══════════════════════════════════════════════════════

bot.run(TOKEN)