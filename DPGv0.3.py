import sys
import random
import json
import os
import time 
from pygame import mixer as mix
import datetime

mix.init()
#music
music = mix.music
#sfx 
sound = mix.Sound

def sfx(file):
    name = sound(file)
    name.play()

damage_grunt = [f'Damage_grunt{i}.mp3' for i in range(1, 21)]
def damaged_sound():
    choice = random.choice(damage_grunt)
    a = sound(choice)
    a.play()
    
battle_grunt = [f'Battle_grunt{i}.mp3' for i in range(1,21)]

def battle_sound():
    choice = random.choice(battle_grunt)
    a = sound(choice)
    a.play()

# Global variables for character stats
username = None
class_input = None
health = None
stamina = None
mana = None
attack_power = 0
money = None
max_health = None
max_stamina = None
max_mana = None
armor = None  

last_daily_claim = None

# Global variables for level, experience, inventory, and equipped items
level = None
exp = None
max_exp = None
inventory = []
equipped = {
    "weapon": None,
    "amulet": None,
    "armor": None
}

# Assassin Evasion flag
evasion_active = False

# Skills per class
skills = {}

# Define weapon types and class restrictions
WEAPON_TYPES = {
    "staff": "mage",
    "sword": "knight",
    "dagger": "assassin"
}

current_path = None  # None means base class
unlocked_paths = []  # List of paths player has unlocked


#tips
tips = [
    "Tip: Your skill damage scales with both your base attack and weapon attack!",
    "Tip: Try fighting unarmed if you want to unlock the Brawler path!",
    "Tip: Dungeon keys can be found on expeditions or bought at the shop.",
    "Tip: Upgrading gear at the Blacksmith increases its power but may fail!",
    "Tip: Legendary items only drop from dungeons — save your keys for a strong run!",
    "Tip: Keep an eye on your mana — running out can cost you a fight!",
    "Tip: Switching paths can unlock new playstyles — use !path to check quests.",
    "Tip: Higher level means higher drop rate for materials in expeditions.",
    "Tip: Blackjack can be risky — bet only what you can afford to lose!",
    "Tip: Use potions before a dungeon boss fight to stay alive longer."
]



# Quest progress
quest_progress = {
    "brawler_kills": 0,
    "mage_dark_mission": False,
    "mage_holy_mission": False,
    "knight_crusader_mission": 0,
    "knight_berserker_mission": 0,
    "assassin_shadowblade_mission": 0
}

paths = {
    "mage": {
        "Shadow Caster": {
            "unlock_condition": "Find the Forbidden Tome during an expedition",
            "skills": {
                "Dark Bolt": {"mana_cost": 50, "damage": lambda : int(get_current_attack() * 10)},
                "Life Drain": {"mana_cost": 50, "damage": lambda : int(get_current_attack() * 3), "heal": 0.5}
            }
        },
        "Holy Mage": {
            "unlock_condition": "Complete the Shrine Purification event",
            "skills": {
                "Heal": {"mana_cost": 40, "heal": lambda max_hp: int(max_hp * 0.25)},
                "Smite": {"mana_cost": 35, "damage": lambda : int(get_current_attack() * 4.5)}
            }
        }
    },
    "knight": {
        "Crusader": {
            "unlock_condition": "Defeat 5 undead enemies (Skeletons) in one life",
            "skills": {
                "Holy Strike": {"mana_cost": 20, "damage": lambda : int(get_current_attack() * 3)},
                "Shield of Faith": {"mana_cost": 25, "effect": "damage_reduction"}
            }
        },
        "Berserker": {
            "unlock_condition": "Win 3 fights in a row at <30% HP",
            "skills": {
                "Rage Slash": {"mana_cost": 10, "damage": lambda : int(get_current_attack() * 2 + 10)},
                "Blood Frenzy": {"mana_cost": 30, "effect": "self_damage_boost"}
            }
        }
    },
    "assassin": {
        "Shadowblade": {
            "unlock_condition": "Land 5 backstabs in fights",
            "skills": {
                "Shadow Strike": {"mana_cost": 20, "damage": lambda : int(get_current_attack() * 2.5)},
                "Fade": {"mana_cost": 15, "effect": "evade_next"}
            }
        },
        "Brawler": {
            "unlock_condition": "Defeat 10 enemies with no weapon equipped",
            "skills": {
                "Haymaker": {"mana_cost": 10, "damage": lambda : int(get_current_attack() * 2) + 5},
                "Flurry Punches": {"mana_cost": 20, "damage": lambda : int(get_current_attack() * 1.2) * 3}
            }
        }
    }
}


enemies = [
    {"name": "Goblin", "health": 30, "attack": 5, "exp": 20, "money_min": 10, "money_max": 25, "material": "Goblin Fang"},
    {"name": "Wolf", "health": 40, "attack": 7, "exp": 30, "money_min": 15, "money_max": 35, "material": "Wolf Pelt"},
    {"name": "Bandit", "health": 50, "attack": 10, "exp": 40, "money_min": 20, "money_max": 50, "material": "Bandit Dagger"},
    {"name": "Skeleton", "health": 45, "attack": 8, "exp": 35, "money_min": 15, "money_max": 30, "material": "Bone Fragment"},
    {"name": "Orc", "health": 60, "attack": 12, "exp": 50, "money_min": 25, "money_max": 55, "material": "Orc Tooth"},
    {"name": "Giant Spider", "health": 55, "attack": 9, "exp": 45, "money_min": 20, "money_max": 40, "material": "Spider Silk"},
    {"name": "Dark Knight", "health": 80, "attack": 15, "exp": 70, "money_min": 40, "money_max": 80, "material": "Cursed Steel"},
    {"name": "Fire Elemental", "health": 70, "attack": 14, "exp": 65, "money_min": 30, "money_max": 70, "material": "Burning Ember"},
    {"name": "Troll", "health": 100, "attack": 18, "exp": 90, "money_min": 50, "money_max": 120, "material": "Troll Hide"},
]

# Equipment data and shop list
item_shop_list = [
    {"id": 101, "name": "Health Potion", "type": "consumable", "effect_stat": "health", "effect_value": 20, "price": 25, "rarity": "common"},
    {"id": 102, "name": "Mana Potion", "type": "consumable", "effect_stat": "mana", "effect_value": 20, "price": 30, "rarity": "common"},
    # Mage weapons
    {"id": 4, "name": "Mystic Staff", "slot": "weapon", "weapon_type": "staff", "attack_boost": 5, "price": 120, "rarity": "common"},
    {"id": 5, "name": "Enchanted Wand", "slot": "weapon", "weapon_type": "staff", "attack_boost": 7, "price": 180, "rarity": "uncommon"},
    {"id": 6, "name": "Arcane Staff", "slot": "weapon", "weapon_type": "staff", "attack_boost": 10, "price": 250, "rarity": "rare"},
    {"id": 7, "name": "Elder's Staff", "slot": "weapon", "weapon_type": "staff", "attack_boost": 15, "price": 400, "rarity": "epic"},
    # Knight weapons
    {"id": 1, "name": "Basic Sword", "slot": "weapon", "weapon_type": "sword", "attack_boost": 2, "price": 50, "rarity": "common"},
    {"id": 8, "name": "Iron Longsword", "slot": "weapon", "weapon_type": "sword", "attack_boost": 7, "price": 150, "rarity": "uncommon"},
    {"id": 9, "name": "Knight's Claymore", "slot": "weapon", "weapon_type": "sword", "attack_boost": 12, "price": 280, "rarity": "rare"},
    {"id": 10, "name": "King's Blade", "slot": "weapon", "weapon_type": "sword", "attack_boost": 20, "price": 500, "rarity": "epic"},
    # Assassin weapons
    {"id": 2, "name": "Rusty Dagger", "slot": "weapon", "weapon_type": "dagger", "attack_boost": 1, "price": 30, "rarity": "common"},
    {"id": 11, "name": "Shadow Dagger", "slot": "weapon", "weapon_type": "dagger", "attack_boost": 8, "price": 170, "rarity": "uncommon"},
    {"id": 12, "name": "Poisoned Blade", "slot": "weapon", "weapon_type": "dagger", "attack_boost": 13, "price": 310, "rarity": "rare"},
    {"id": 13, "name": "Executioner's Dagger", "slot": "weapon", "weapon_type": "dagger", "attack_boost": 22, "price": 550, "rarity": "epic"},
    # Ancient artifact
    {"id": 201, "name": "Ancient Amulet", "slot": "amulet", "health_boost": 10, "mana_boost": 10, "price": 200, "rarity": "rare"},
    {"id": 301, "name": "Leather Armor", "slot": "armor", "defense": 5, "price": 100, "rarity": "common"},
    {"id": 302, "name": "Chainmail Armor", "slot": "armor", "defense": 12, "price": 250, "rarity": "uncommon"},
    {"id": 303, "name": "Dragon Scale Armor", "slot": "armor", "defense": 25, "price": 500, "rarity": "epic"},
]

# Start by assigning unique IDs for loot items
next_loot_id = 1000

dungeon_loot_pool = {
    "common": [
        {"id": next_loot_id + 1, "name": "Iron Sword", "slot": "weapon", "weapon_type": "sword", "attack_boost": 5, "price": 50, "rarity": "common"},
        {"id": next_loot_id + 2, "name": "Iron Armor", "slot": "armor", "defense": 5, "price": 100, "rarity": "common"},
        {"id": next_loot_id + 3, "name": "Copper Amulet", "slot": "amulet", "mana_boost": 10, "price": 40, "rarity": "common"}
    ],
    "rare": [
        {"id": next_loot_id + 4, "name": "Steel Sword", "slot": "weapon", "weapon_type": "sword", "attack_boost": 10, "price": 280, "rarity": "rare"},
        {"id": next_loot_id + 5, "name": "Steel Armor", "slot": "armor", "defense": 10, "price": 250, "rarity": "rare"},
        {"id": next_loot_id + 6, "name": "Silver Amulet", "slot": "amulet", "mana_boost": 20, "price": 150, "rarity": "rare"}
    ],
    "epic": [
        {"id": next_loot_id + 7, "name": "Runed Blade", "slot": "weapon", "weapon_type": "sword", "attack_boost": 18, "price": 500, "rarity": "epic"},
        {"id": next_loot_id + 8, "name": "Runed Plate", "slot": "armor", "defense": 18, "price": 450, "rarity": "epic"},
        {"id": next_loot_id + 9, "name": "Runed Amulet", "slot": "amulet", "mana_boost": 40, "price": 400, "rarity": "epic"}
    ],
    "legendary": [
        {"id": next_loot_id + 10, "name": "Excalibur", "slot": "weapon", "weapon_type": "sword", "attack_boost": 25, "price": 1000, "rarity": "legendary",
        "description": "The legendary sword of kings."},
        {"id": next_loot_id + 11, "name": "Dragon Slayer", "slot": "weapon", "weapon_type": "sword", "attack_boost": 30, "price": 1200, "rarity": "legendary",
        "description": "Forged to slay dragons."},
        {"id": next_loot_id + 12, "name": "Celestial Armor", "slot": "armor", "defense": 20, "price": 1100, "rarity": "legendary",
        "description": "Armor blessed by the gods."},
        {"id": next_loot_id + 13, "name": "Shadow Amulet", "slot": "amulet", "mana_boost": 50, "price": 950, "rarity": "legendary",
        "description": "Empowers shadow abilities."},
        {"id": next_loot_id + 14, "name": "Archmage's Staff", "slot": "weapon", "weapon_type": "staff", "attack_boost": 20, "mana_boost": 60, "price": 1300, "rarity": "legendary",
        "description": "Legendary staff that boosts spell damage for Mages."},
        {"id": next_loot_id + 15, "name": "Void Tome", "slot": "weapon", "weapon_type": "staff", "attack_boost": 15, "mana_boost": 80, "price": 1400, "rarity": "legendary",
        "description": "A cursed book that increases dark magic damage (perfect for Shadow Caster)."},
        {"id": next_loot_id + 16, "name": "Paladin's Hammer", "slot": "weapon", "weapon_type": "sword", "attack_boost": 22, "defense": 5, "price": 1250, "rarity": "legendary",
        "description": "A holy hammer favored by Crusaders."},
        {"id": next_loot_id + 17, "name": "Bloodfang Axe", "slot": "weapon", "weapon_type": "sword", "attack_boost": 28, "price": 1500, "rarity": "legendary",
        "description": "A savage axe that empowers Berserkers with each kill."},
        {"id": next_loot_id + 18, "name": "Dagger of Eternal Night", "slot": "weapon", "weapon_type": "dagger", "attack_boost": 18, "crit_chance": 15, "price": 1350, "rarity": "legendary",
        "description": "Assassin’s dream dagger, increases critical chance."},
        {"id": next_loot_id + 19, "name": "Gauntlets of the Brawler", "slot": "weapon", "weapon_type": "dagger", "attack_boost": 12, "price": 1100, "rarity": "legendary",
        "description": "Worn by ancient warriors who fought barehanded. Boosts unarmed damage."}
    ]

}



dungeon_bosses = [
    {"name": "Ancient Dragon", "health": 500, "attack": 20, "exp": 500, "money_min": 200, "money_max": 400},
    {"name": "Demon Lord", "health": 600, "attack": 25, "exp": 600, "money_min": 250, "money_max": 500},
    {"name": "Lich King", "health": 450, "attack": 18, "exp": 550, "money_min": 220, "money_max": 450},
    {"name": "Titan Golem", "health": 700, "attack": 22, "exp": 700, "money_min": 300, "money_max": 550}
]


equipment_drop_list = [item for item in item_shop_list if item.get('slot') == 'weapon']

# Expedition events
expedition_events = [
    {"event": "approach_cave", "text": "You approach a dark cave. Do you enter?", 
     "choices": {"yes": "enter", "no": "continue"}, "fightable": True},
    
    {"event": "find_chest", "text": "You find a dusty old chest on the path. Do you open it?", 
     "choices": {"yes": "open", "no": "continue"}, "fightable": True},
    
    {"event": "encounter_wildlife", "text": "You hear a rustling in the bushes. Do you investigate?", 
     "choices": {"yes": "investigate", "no": "continue"}, "fightable": True},
    
    {"event": "mysterious_traveler", "text": "You encounter a mysterious traveler on the road. They seem burdened but intrigued by your presence. Do you offer to help them?", 
     "choices": {"yes": "offer help", "no": "ignore"}, "fightable": True},
    
    {"event": "ancient_ruin", "text": "You stumble upon the ruins of an ancient civilization. They radiate an otherworldly aura. Do you investigate the ruins further?", 
     "choices": {"yes": "investigate", "no": "avoid", "cautiously": "investigate cautiously"}, "fightable": True},
]

# Class descriptions
class_descriptions = {
    'mage': "The Mage is a master of arcane arts, wielding powerful spells. They possess high mana but are physically fragile.",
    'knight': "The Knight is a courageous warrior, armored and ready for battle. They have high health but less mana.",
    'assassin': "The Assassin is a stealthy and agile fighter, striking from the shadows. They have high attack power and balanced stats."
}


starting_equipment = {
    'mage': [4, 102],  # Mystic Staff, Mana Potion
    'knight': [1, 101],  # Basic Sword, Health Potion
    'assassin': [2, 101],  # Rusty Dagger, Health Potion
}

# Skills per class


RARITY_STARS = {
    "common": 1,
    "uncommon": 2,
    "rare": 3,
    "epic": 4,
    "legendary": 5
}

materials = {}
#music function
def title_theme():
    music.load("title.wav")
    music.play(-1)
def menu_theme():
    music.load('menu.wav')
    music.play(-1)
def boss_theme():
    music.load('boss.wav')
    music.play(-1)
def dungeon_theme():
    music.load('dungeon.wav')
    music.play(-1)
def battle_theme():
    music.load('battle.wav')
    music.play(-1)
def expedition_theme():
    music.load('expedition.wav')
    music.play(-1)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
    sys.stdout.flush()

def display_battle(player_class, player_health, player_max_health, enemy, attack_target=None, animate=False):
    """Displays the player and enemy side by side with movement and attack animation."""
    # ASCII for player classes
    player_art = {
        "mage": [
            "  /^\\  ",
            " (o_o) ",
            "  |=|  ",
            "  / \\  "
        ],
        "knight": [
            "  /|\\  ",
            " (o_o) ",
            "  |=|  ",
            "  / \\  "
        ],
        "assassin": [
            "  /_\\  ",
            " (•_•) ",
            "  |=|  ",
            "  / \\  "
        ]
    }

    # ASCII for monsters
    monster_art = {
        "Goblin": ["  , ,  ", " /(.-\"-.)\\", " \\  o o / ", "  \\_ v _/ "],
        "Wolf": ["  .--.  ", " /@  \\_ ", "|     __)", " \\__/   "],
        "Bandit": ["  .--.  ", " (o_o)  ", " <)   )╯", "  || || "],
        "Skeleton": ["  .--.  ", " (x_x)  ", " /|_|\\  ", "  / \\  "],
        "Orc": ["  .--.  ", " (ò_ó)  ", "  |=|  ", "  / \\  "],
        "Giant Spider": ["  \\_/  ", " (o.o) ", " /|_|\\ ", "  / \\  "],
        "Dark Knight": ["  /|\\  ", " (⚈_⚈) ", "  |=|  ", "  / \\  "],
        "Fire Elemental": ["  ~~~  ", " (🔥)  ", "  ~~~  ", "  ~~~  "],
        "Troll": ["  .--.  ", " (ಠ_ಠ) ", "  |=|  ", "  / \\  "]
    }


    def health_bar(current, maximum, length=12):
        current = max(0, current)
        filled = int(round((current / maximum) * length))
        empty = length - filled
        ratio = current / maximum
        if ratio > 0.6:
            color = '\033[92m'  # Green
        elif ratio > 0.3:
            color = '\033[93m'  # Yellow
        else:
            color = '\033[91m'  # Red
        reset = '\033[0m'
        return f"{color}[{'#'*filled}{' '*empty}]{reset} {current}/{maximum} HP"

    enemy_max = enemy.get('max_health', enemy['health'])
    player_lines = player_art.get(player_class, ["","","",""])
    enemy_lines = monster_art.get(enemy['name'], ["","","",""])

    if animate and attack_target:
        steps = 5  # Number of frames for movement
        for step in range(steps):
            os.system('cls' if os.name == 'nt' else 'clear')

            # Determine spacing
            if attack_target == 'enemy':
                spacing = " " * (step * 2)
                p_lines = [spacing + line for line in player_lines]
                e_lines = enemy_lines
            elif attack_target == 'player':
                spacing = " " * ((steps - step) * 2)
                p_lines = player_lines
                e_lines = [spacing + line for line in enemy_lines]

            # Highlight attack target on last frame
            if step == steps - 1:
                if attack_target == 'enemy':
                    e_lines = [f"\033[91m{line}\033[0m" for line in enemy_lines]
                else:
                    p_lines = [f"\033[91m{line}\033[0m" for line in player_lines]

            for p_line, m_line in zip(p_lines, e_lines):
                print(f"{p_line:<30}   {m_line}")

            # Colored health bars
            player_bar = health_bar(player_health, player_max_health)
            enemy_bar = health_bar(enemy['health'], enemy_max)
            print(f"{player_bar:<30}   {enemy_bar}\n")
            time.sleep(0.2)  
    else:
        
        for p_line, m_line in zip(player_lines, enemy_lines):
            print(f"{p_line:<30}   {m_line}")
        player_bar = health_bar(player_health, player_max_health)
        enemy_bar = health_bar(enemy['health'], enemy_max)
        print(f"{player_bar:<30}   {enemy_bar}\n")

def welcome_screen():
    clear_screen()
    title_theme()
    
    print(r"""
 __        __   _                            _          _____   ____     ____  
 \ \      / /__| | ___ ___  _ __ ___   ___  | |_ ___   |  _ \  |  o  \  / ___|
  \ \ /\ / / _ \ |/ __/ _ \| '_ ` _ \ / _ \ | __/ _ \  | | | | |____/  |  |  _ 
   \ V  V /  __/ | (_| (_) | | | | | |  __/ | || (_) | | |_| | | |     |  |_| |
    \_/\_/ \___|_|\___\___/|_| |_| |_|\___|  \__\___/  |____/  |_|      \_____|
""")
    input("\nPress Enter to continue...")
    clear_screen()

def create_bar(current, maximum, bar_length, fill_char='#', empty_char=' '):
    """Generates a text-based health, stamina, mana, or experience bar."""
    current = max(0, current)
    maximum = max(1, maximum) 

    filled_blocks = int(round((current / maximum) * bar_length))
    empty_blocks = bar_length - filled_blocks
    
    bar = f"[{fill_char * filled_blocks}{empty_char * empty_blocks}]"
    
    return f"{bar} {current}/{maximum}"

def character_creation():
    """Prompts the user to create a character and initializes stats."""
    global username, class_input, health, stamina, mana, attack_power, money
    global max_health, max_stamina, max_mana, level, exp, max_exp, inventory, equipped
    global skills, base_attack, weapon_attack

    username = input('Please enter your username: ')
    print('************************************')
    for cls, desc in class_descriptions.items():
        print(f"{cls.capitalize()}: {desc}")
        print("-" * 20)
    print('************************************')

    class_input = input('Please select your class: ').lower()

    inventory = []
    equipped = {"weapon": None, "amulet": None, "armor": None}

    if class_input == 'mage':
        health, stamina, mana, base_attack = 100, 100, 120, 10
    elif class_input == 'knight':
        health, stamina, mana, base_attack = 150, 100, 50, 7
    elif class_input == 'assassin':
        health, stamina, mana, base_attack = 100, 100, 50, 13
    else:
        print('Invalid class. Please try again.')
        return

    weapon_attack = equipped["weapon"].get("attack_boost", 0) if equipped["weapon"] else 0
    attack_power = base_attack + weapon_attack  


    level, exp, max_exp, money = 1, 0, 100, 50
    max_health, max_stamina, max_mana = health, stamina, mana
    get_current_attack()
    skills = {
        "mage": {
            "Fireball": {"mana_cost": 50, "damage": lambda: int(get_current_attack() * 5)},
            "Ice Spike": {"mana_cost": 30, "damage": lambda: int(get_current_attack() * 2)}
        },
        "knight": {
            "Shield Bash": {"mana_cost": 15, "damage": lambda: int(get_current_attack() * 1.2 + max_health * 0.03)},
            "Power Strike": {"mana_cost": 25, "damage": lambda: int(get_current_attack() * 2 +  5/health*50)}
        },
        "assassin": {
            "Backstab": {"mana_cost": 20, "damage": lambda: int(get_current_attack() * 1.5)},
            "Evasion": {"mana_cost": 10, "effect": "evasion"}
        }
    }


   
    if class_input in starting_equipment:
        for item_id in starting_equipment[class_input]:
            item_to_add = next((item for item in item_shop_list if item['id'] == item_id), None)
            if item_to_add:
                inventory.append(item_to_add.copy())
                if item_to_add.get('slot') == 'weapon':
                    equipped["weapon"] = inventory[-1]

    print(f"Character '{username}' the {class_input.capitalize()} created successfully!")
    menu()

def get_current_attack():
    """Recalculate attack power using base_attack + weapon_attack."""
    global attack_power, base_attack, weapon_attack
    weapon_attack = equipped["weapon"].get("attack_boost", 0) if equipped["weapon"] else 0
    attack_power = base_attack + weapon_attack
    return attack_power


def drop_item(item_id):
    """Adds an item to the inventory and shows stars based on rarity."""
    item = next((i for i in item_shop_list if i['id'] == item_id), None)
    if item:
        inventory.append(item)
        rarity = item.get('rarity', 'common').lower()
        stars = "★" * RARITY_STARS.get(rarity, 1)
        print(f"\nYou obtained: {item['name']} [{stars}]!")
    else:
        print("Error: Item not found.")

def battle_loot():
    """Handles loot drops after a battle, showing rarity."""
    drop_chance = random.randint(1, 100)
    
    if drop_chance <= 50:
        # Common drop
        possible_items = [i for i in item_shop_list if i['rarity'] == 'Common']
    elif drop_chance <= 75:
        # Uncommon drop
        possible_items = [i for i in item_shop_list if i['rarity'] == 'Uncommon']
    elif drop_chance <= 90:
        # Rare drop
        possible_items = [i for i in item_shop_list if i['rarity'] == 'Rare']
    elif drop_chance <= 98:
        # Epic drop
        possible_items = [i for i in item_shop_list if i['rarity'] == 'Epic']
    else:
        # Legendary drop
        possible_items = [i for i in item_shop_list if i['rarity'] == 'Legendary']

    if possible_items:
        item = random.choice(possible_items)
        drop_item(item['id'])
    else:
        print("No loot dropped this time.")

# Updated fight function with side-by-side display
def fight(enemy):
    
    import random, time
    global health, mana, money, exp, evasion_active, level 
    enemy['max_health'] = enemy.get('health', 1)
    scaling_factor_health = 1 + (0.10 * (level - 1))  
    scaling_factor_attack = 1 + (0.05 * (level - 1))  
    enemy['health'] = int(enemy['health'] * scaling_factor_health)
    enemy['max_health'] = enemy['health']
    enemy['attack'] = int(enemy['attack'] * scaling_factor_attack)
    print(f"\nA wild {enemy['name']} appears! Prepare to fight!")
    pet_on_battle_start()

    player_art = {
        "mage": ["  /^\\  ", " (o_o) ", "  |=|  ", "  / \\  "],
        "knight": ["  /|\\  ", " (o_o) ", "  |=|  ", "  / \\  "],
        "assassin": ["  /_\\  ", " (•_•) ", "  |=|  ", "  / \\  "]
    }
    monster_art = {
        "Goblin": ["  , ,  ", " /(.-\"-.)\\", " \\  o o / ", "  \\_ v _/ "],
        "Wolf": ["  .--.  ", " /@  \\_ ", "|     __)", " \\__/   "],
        "Bandit": ["  .--.  ", " (o_o)  ", " <)   )╯", "  || || "],
        "Skeleton": ["  .--.  ", " (x_x)  ", " /|_|\\  ", "  / \\  "],
        "Orc": ["  .--.  ", " (ò_ó)  ", "  |=|  ", "  / \\  "],
        "Giant Spider": ["  \\_/  ", " (o.o) ", " /|_|\\ ", "  / \\  "],
        "Dark Knight": ["  /|\\  ", " (⚈_⚈) ", "  |=|  ", "  / \\  "],
        "Fire Elemental": ["  ~~~  ", " (🔥)  ", "  ~~~  ", "  ~~~  "],
        "Troll": ["  .--.  ", " (ಠ_ಠ) ", "  |=|  ", "  / \\  "],
        
        # === Bosses ===
        "Ancient Dragon": [
            "                              ______________                               ",
            "                        ,===:'.,            `-._                           ",
            "                                  `:.`---.__         `-._                 ",
            "                                        `:.     `--.         `.           ",
            "                                 \\.        `.         `.                  ",
            "                         (,,(,    \\.         `.   ____,-`.,               ",
            "                      (,'     `/   \\.   ,--.___`.'                        ",
            "                  ,  ,'  ,--.  `,   \\.;'         `                        ",
            "                   `{D, {    \\  :    \\;                                   ",
            "                     V,,'    /  /    //                                   ",
            "                     j;;    /  ,' ,-//.    ,---.      ,                   ",
            "                     \\;'   /  ,' /  _  \\  /  _  \\   ,'/                   ",
            "                           \\   `'  / \\  `'  / \\  `.' /                    ",
            "                            `.___,'   `.__,'   `.__,'                     "
        ],
        "Demon Lord": [
            "   , ,, ,                              ",
            "   | || |    ,/  _____  \\.             ",
            "   \\_||_/    ||_/     \\_||             ",
            "     ||       \\_| . . |_/              ",
            "     ||         |  L  |                ",
            "    ,||         |`==='|                ",
            "    |>|      ___`>  -<'___             ",
            "    |>|\    /             \\            ",
            "    \\>| \\  /  ,    .    .  |           ",
            "     ||  \\/  /| .  |  . |  |           ",
            "     ||\\  ` / | ___|___ |  |     (     ",
            "  (( || `--'  | _______ |  |     ))  ( ",
            "(  )\\|| (  )\\ | - --- - | -| (  ( \\  ))",
            "(\\/  || ))/ ( | -- - -- |  | )) )  \\(( ",
            " ( ()||((( ())|         |  |( (( () )   "
        ],
        "Lich King": [
            "             ___          ",
            "            /   \\\\        ",
            "       /\\\\ | . . \\\\       ",
            "     ////\\\\|     ||       ",
            "   ////   \\\\ ___//\\       ",
            "  ///      \\\\      \\      ",
            " ///       |\\\\      |     ",
            "//         | \\\\  \\   \\    ",
            "/          |  \\\\  \\   \\   ",
            "           |   \\\\ /   /   ",
            "           |    \\/   /    ",
            "           |     \\\\/|     ",
            "           |      \\\\|     ",
            "           |       \\\\     ",
            "           |        |     ",
            "           |_________\\    "
        ],
        "Titan Golem": [
            "           _......._              ",
            "       .-'.'.'.'.'.'.`-.          ",
            "     .'.'.'.'.'.'.'.'.'.`.        ",
            "    /.'.'               '.\\       ",
            "    |.'    _.--...--._     |      ",
            "    \\    `._.-.....-._.'   /      ",
            "    |     _..- .-. -.._   |       ",
            " .-.'    `.   ((@))  .'   '.-.    ",
            "( ^ \\      `--.   .-'     / ^ )   ",
            " \\  /         .   .       \\  /    ",
            " /          .'     '.  .-    \\    ",
            "( _.\    \\ (_`-._.-'_)    /._\\)   ",
            " `-' \\   ' .--.          / `-'    ",
            "     |  / /|_| `-._.'\\   |        ",
            "     |   |       |_| |   /-.._    ",
            " _..-\\   `.--.______.'  |         ",
            "      \\       .....     |         ",
            "       `.  .'      `.  /          ",
            "         \\           .'           ",
            "          `-..___..-'             "
        ]
    }

    
    def health_bar(current, maximum, length=12):
        current = max(0, current)
        filled = int(round((current / maximum) * length))
        empty = length - filled
        ratio = current / maximum
        if ratio > 0.6:
            color = '\033[92m'  # Green
        elif ratio > 0.3:
            color = '\033[93m'  # Yellow
        else:
            color = '\033[91m'  # Red
        reset = '\033[0m'
        return f"{color}[{'#'*filled}{' '*empty}]{reset} {current}/{maximum} HP"


    def mana_bar(current, maximum, length=12):
        current = max(0, current)
        filled = int(round((current / maximum) * length))
        empty = length - filled
        ratio = current / maximum
        if ratio > 0.6:
            color = '\033[96m'  # Cyan
        elif ratio > 0.3:
            color = '\033[94m'  # Blue
        else:
            color = '\033[91m'  # Red
        reset = '\033[0m'
        return f"{color}[{'¤'*filled}{' '*empty}]{reset} {current}/{maximum} MP"


    def display_frame(player_x=0, enemy_x=0, highlight=None):
        clear_screen()
        p_lines = player_art[class_input]
        e_lines = monster_art[enemy['name']]
        if highlight == 'player':
            p_lines = [f"\033[91m{l}\033[0m" for l in p_lines]
        elif highlight == 'enemy':
            e_lines = [f"\033[91m{l}\033[0m" for l in e_lines]

        for pl, ml in zip(p_lines, e_lines):
            print(" " * player_x + pl + " " * (10 - player_x + enemy_x) + ml)

        # Color the bars
        print(f"HP: {health_bar(health, max_health)}     {enemy['name']} HP: {health_bar(enemy['health'], enemy['max_health'])}")
        print(f"MP: {mana_bar(mana, max_mana)}")
        time.sleep(0.1)


    def animate_attack(attacker, target):
        
        frames = [0,2,4,2,0]
        for f in frames:
            if attacker == 'player':
                display_frame(player_x=f, enemy_x=0, highlight='enemy')
            else:
                display_frame(player_x=0, enemy_x=f, highlight='player')

    while enemy['health'] > 0 and health > 0:
        display_frame()
        print("\nActions: [attack] / [skill] / [use] / [run]")
        action = input("Choose your action: ").lower().strip()

                        # Holy Mage unlock: Heal yourself to full HP in combat 3 times
        if class_input == "mage" and health == max_health:
            quest_progress["mage_holy_mission"] = quest_progress.get("mage_holy_mission", 0) + 1


        if action == "attack":
            damage = get_current_attack()
            damage = pet_on_player_attack(damage)
            battle_sound()
            animate_attack('player', 'enemy')
            enemy['health'] -= damage
            print(f"You attack {enemy['name']} for {damage} damage!")
            extra = pet_extra_damage()
            if extra:
                enemy['health'] -= extra
                print(f"Your pet strikes for {extra} bonus damage!")
            input('press enter to continue.')

        elif action == "skill":
            get_current_attack()
            class_skills = skills.get(class_input, {})
            print("\nSkills:")
            for i, sk_name in enumerate(class_skills.keys()):
                sk_data = class_skills[sk_name]
                print(f"[{i+1}] {sk_name} (Mana Cost: {sk_data['mana_cost']})")
            try:
                choice = int(input("Choose skill number: ")) - 1
                sk_name = list(class_skills.keys())[choice]
                sk_data = class_skills[sk_name]
                if mana < sk_data['mana_cost']:
                    print("Not enough mana!")
                    continue
                mana -= sk_data['mana_cost']
                if sk_name == "Backstab":
                    quest_progress["assassin_shadowblade_mission"] += 1
                    if quest_progress["assassin_shadowblade_mission"] >= 5 and "Shadowblade" not in unlocked_paths:
                        unlocked_paths.append("Shadowblade")
                        print("🌑 You have mastered the shadows! Shadowblade path unlocked!")
                if 'damage' in sk_data:
                    battle_sound()
                    animate_attack('player', 'enemy')
                    damage = sk_data['damage']() if callable(sk_data['damage']) else sk_data['damage']
                    enemy['health'] -= damage
                    print(f"\nYou used {sk_name} and dealt {damage} damage!")
                    input('press enter to continue.')

                if 'effect' in sk_data and sk_data['effect'] == "evasion":
                    evasion_active = True
                    print("Evasion activated!")
                    input('press enter to continue.')
            except:
                print("Invalid choice.")
                input('press enter to continue.')
                continue

        elif action == "use":
            consumables = [item for item in inventory if item.get('type')=='consumable']
            if not consumables:
                print("No consumables!")
                input('press enter to continue.')
                continue
            print("\nConsumables:")
            for i,item in enumerate(consumables):
                print(f"[{i+1}] {item['name']} - Restores {item['effect_value']} {item['effect_stat'].capitalize()}")
            try:
                choice=int(input("Choose item number: ")) -1
                item=consumables[choice]
                use_item(inventory.index(item))
            except:
                print("Invalid choice.")
                continue

        elif action == "run":
            if random.random()<0.5:
                print("You fled successfully!")
                input('press enter to continue.')
                return
            else:
                print("Failed to run!")
                input('press enter to continue.')

        else:
            print("Invalid action.")
            input('press enter to continue.')
            continue

        
        if enemy['health']>0:
            damage=enemy['attack']
            damaged_sound()
            animate_attack('enemy','player')
            take_damage(damage)
            print(f"\n{enemy['name']} attacks you for {damage} damage!")
            heal = pet_on_enemy_attack(damage)
            if heal:
                health = min(max_health, health + heal)
                print(f"{get_active_pet()['name']} sustains you for +{heal} HP!")
            input()
            

            

    
    if health>0:
        pet_on_victory()
        increment_hatch_progress_on_win()
        roll_pet_egg_loot()
        # Material drop system
        # Rare dungeon key drop
        key_drop_chance = min(5 + level, 20)  # scales with level up to 20%
        if random.randint(1, 100) <= key_drop_chance:
            materials["Dungeon Key"] = materials.get("Dungeon Key", 0) + 1
            print("🔑 You found a Dungeon Key!")
            
        if quest_progress["mage_holy_mission"] >= 3 and "Holy Mage" not in unlocked_paths:
            unlocked_paths.append("Holy Mage")
            print("✨ You have purified your soul through healing! Holy Mage path unlocked!")

        if class_input == "assassin" and not equipped["weapon"]:
            quest_progress["brawler_kills"] += 1
            if quest_progress["brawler_kills"] >= 10 and "Brawler" not in unlocked_paths:
                unlocked_paths.append("Brawler")
                print("🔥 You have unlocked the Brawler path! Use !path to switch.")

                # Shadow Caster unlock: Find a rare "Forbidden Tome"
        if class_input == 'mage' and enemy['name'] == "Dark Knight":
            # Drop chance for tome increases with level
            if random.randint(1, 100) <= min(25 + level * 2, 90):
                if not quest_progress["mage_dark_mission"]:
                    quest_progress["mage_dark_mission"] = True
                    unlocked_paths.append("Shadow Caster")
                    print("🌑 You discovered the Forbidden Tome! Shadow Caster path unlocked!")

                # Crusader unlock: Kill 5 Skeletons
        if class_input == 'knight' and enemy['name'] == "Skeleton":
            quest_progress["knight_crusader_mission"] += 1
            if quest_progress["knight_crusader_mission"] >= 5 and "Crusader" not in unlocked_paths:
                unlocked_paths.append("Crusader")
                print("🛡 The church recognizes your holy deeds! Crusader path unlocked!")

        # Berserker unlock: Win 3 battles under 30% HP
        if class_input == 'knight' and health <= max_health * 0.3:
            quest_progress["knight_berserker_mission"] += 1
            if quest_progress["knight_berserker_mission"] >= 3 and "Berserker" not in unlocked_paths:
                unlocked_paths.append("Berserker")
                print("💢 Rage consumes you! Berserker path unlocked!")

        material = enemy.get("material")
        if material:
            # Drop chance scales with level (e.g. 30% + 2% per level)
            drop_chance = min(90, 30 + level * 2)
            if random.randint(1, 100) <= drop_chance:
                amount = 1 + level // 5  # +1 extra every 5 levels
                materials[material] = materials.get(material, 0) + amount
                print(f"You obtained {amount}x {material}!")

        reward_money = random.randint(enemy['money_min'], enemy['money_max'])
        money += reward_money
        gain_exp(enemy['exp'])
        print(f"\nYou defeated {enemy['name']}! Earned {reward_money} gold and {enemy['exp']} exp.")
        get_equipment_drop()
        generate_shop_items()
        auto_save()
    

def path_menu():
    global current_path, unlocked_paths, skills

    clear_screen()
    print("=== PATH MENU ===")
    print(f"Current Path: {current_path if current_path else 'Base ' + class_input.capitalize()}")
    print("\nAvailable Paths:")

    # Helper for progress bar
    def progress_bar(current, total, length=20):
        filled = int((current / total) * length)
        return f"[{'#' * filled}{'.' * (length - filled)}] {current}/{total}"

    # Show all paths for current class
    for path_name, path_data in paths[class_input].items():
        unlocked = path_name in unlocked_paths
        status = "Unlocked ✅" if unlocked else "Locked ❌"
        print(f"\n{path_name}: {status}")

        # Show quest progress if not unlocked
        if not unlocked:
            if class_input == "mage":
                if path_name == "Shadow Caster":
                    done = 1 if quest_progress["mage_dark_mission"] else 0
                    print(f" Quest: Find the Forbidden Tome ({done}/1)")
                elif path_name == "Holy Mage":
                    current = quest_progress.get("mage_holy_mission", 0)
                    print(f" Quest: Heal to full HP 3 times {progress_bar(current, 3)}")

            elif class_input == "knight":
                if path_name == "Crusader":
                    current = quest_progress["knight_crusader_mission"]
                    print(f" Quest: Slay 5 Skeletons {progress_bar(current, 5)}")
                elif path_name == "Berserker":
                    current = quest_progress["knight_berserker_mission"]
                    print(f" Quest: Win 3 fights under 30% HP {progress_bar(current, 3)}")

            elif class_input == "assassin":
                if path_name == "Shadowblade":
                    current = quest_progress["assassin_shadowblade_mission"]
                    print(f" Quest: Land 5 Backstabs {progress_bar(current, 5)}")
                elif path_name == "Brawler":
                    current = quest_progress["brawler_kills"]
                    print(f" Quest: Defeat 10 enemies unarmed {progress_bar(current, 10)}")

    # Allow path switching if any unlocked
    if unlocked_paths:
        print("\nType the path name to switch to it, or type 'back' to exit.")
        choice = input("Your choice: ").title().strip()
        if choice in unlocked_paths:
            current_path = choice
            # Apply new skills dynamically
            new_skills = {}
            for sk, data in paths[class_input][choice]["skills"].items():
                if "damage" in data:
                    # Keep lambda reference, so damage scales dynamically
                    new_skills[sk] = {"mana_cost": data["mana_cost"], "damage": data["damage"]}
                elif "heal" in data:
                    # Healing can stay as lambda (call at use time)
                    new_skills[sk] = {"mana_cost": data["mana_cost"], "heal": data["heal"]}
                else:
                    new_skills[sk] = data

            skills[class_input] = new_skills
            print(f"You have switched to the {choice} path!")
    input("Press Enter...")


def generate_shop_items():
    item_shop_list = [
        {"id": 101, "name": "Health Potion", "type": "consumable", "effect_stat": "health", "effect_value": 20, "price": 25, "rarity": "common"},
        {"id": 102, "name": "Mana Potion", "type": "consumable", "effect_stat": "mana", "effect_value": 20, "price": 30, "rarity": "common"},
        # Mage weapons
        {"id": 4, "name": "Mystic Staff", "slot": "weapon", "weapon_type": "staff", "attack_boost": 5, "price": 120, "rarity": "uncommon"},
        {"id": 5, "name": "Enchanted Wand", "slot": "weapon", "weapon_type": "staff", "attack_boost": 7, "price": 180, "rarity": "uncommon"},
        {"id": 6, "name": "Arcane Staff", "slot": "weapon", "weapon_type": "staff", "attack_boost": 10, "price": 250, "rarity": "rare"},
        {"id": 7, "name": "Elder's Staff", "slot": "weapon", "weapon_type": "staff", "attack_boost": 15, "price": 400, "rarity": "epic"},
        # Knight weapons
        {"id": 1, "name": "Basic Sword", "slot": "weapon", "weapon_type": "sword", "attack_boost": 2, "price": 50, "rarity": "common"},
        {"id": 8, "name": "Iron Longsword", "slot": "weapon", "weapon_type": "sword", "attack_boost": 7, "price": 150, "rarity": "uncommon"},
        {"id": 9, "name": "Knight's Claymore", "slot": "weapon", "weapon_type": "sword", "attack_boost": 12, "price": 280, "rarity": "rare"},
        {"id": 10, "name": "King's Blade", "slot": "weapon", "weapon_type": "sword", "attack_boost": 20, "price": 500, "rarity": "epic"},
        # Assassin weapons
        {"id": 2, "name": "Rusty Dagger", "slot": "weapon", "weapon_type": "dagger", "attack_boost": 1, "price": 30, "rarity": "common"},
        {"id": 11, "name": "Shadow Dagger", "slot": "weapon", "weapon_type": "dagger", "attack_boost": 8, "price": 170, "rarity": "uncommon"},
        {"id": 12, "name": "Poisoned Blade", "slot": "weapon", "weapon_type": "dagger", "attack_boost": 13, "price": 310, "rarity": "rare"},
        {"id": 13, "name": "Executioner's Dagger", "slot": "weapon", "weapon_type": "dagger", "attack_boost": 22, "price": 550, "rarity": "epic"},
        # Ancient artifact
        {"id": 201, "name": "Ancient Amulet", "slot": "amulet", "health_boost": 10, "mana_boost": 10, "price": 200, "rarity": "rare"},
        {"id": 301, "name": "Leather Armor", "slot": "armor", "defense": 5, "price": 100, "rarity": "common"},
        {"id": 302, "name": "Chainmail Armor", "slot": "armor", "defense": 12, "price": 250, "rarity": "uncommon"},
        {"id": 303, "name": "Dragon Scale Armor", "slot": "armor", "defense": 25, "price": 500, "rarity": "epic"},
    ]
    random.shuffle(item_shop_list)
    return item_shop_list[:5]  

def check_level_up():
    global exp, max_exp, level, health, stamina, mana, max_health, max_stamina, max_mana, base_attack
    while exp >= max_exp:
        level += 1
        exp -= max_exp
        max_exp = int(max_exp * 1.5)
        health += 2
        stamina += 2
        mana += 2
        max_health += 2
        max_stamina += 2
        max_mana += 2
        base_attack += 2
        get_current_attack()
        print(f"\nCongratulations! You have leveled up to Level {level}!")
        print(f"Health increased to {health}, Stamina increased to {stamina}, and Mana increased to {mana}.")
        print(f"💡 Hint: {random.choice(tips)}")
        auto_save()  

def gain_exp(amount):
    """Gives the player experience points."""
    global exp
    exp += amount
    print(f"You gained {amount} experience.")
    check_level_up()

def get_equipment_drop():
    """Randomly determines if a new equipment item is found, showing stars."""
    if random.randint(1, 100) <= 20:
        new_item = random.choice(equipment_drop_list)
        inventory.append(new_item.copy())
        rarity = new_item.get('rarity', 'common').lower()
        stars = "★" * RARITY_STARS.get(rarity, 1)
        print(f"You found a new item: {new_item['name']} [{stars}]!")

def get_money_drop():
    """Randomly determines if money is found."""
    global money
    if random.randint(1, 100) <= 80:
        money_found = random.randint(10, 30)
        money += money_found
        print(f"You found {money_found} gold!")

def handle_expedition_event(event_data):
    clear_screen()
    """Handles a random expedition event and triggers fights with visual display."""
    global money

    print(f"\n{event_data['text']}")
    choices = event_data['choices']
    for choice, action in choices.items():
        print(f"[{choice}] -> {action.replace('_', ' ').capitalize()}")

    choice_input = input("Your choice: ").lower()
    if choice_input not in choices:
        print("Invalid choice. You hesitate and miss your opportunity.")
        choice_input = 'no' if 'no' in choices else list(choices.keys())[0]

    
    if event_data.get('fightable', False):
        enemy = random.choice(enemies).copy()
        enemy['max_health'] = enemy['health']
        print(f"\nAn enemy appears due to the event!")
        input("Press Enter to continue...")
        battle_theme()
        fight(enemy) 

    
    if event_data['event'] == "approach_cave":
        if choices.get(choice_input) == "enter":
            if random.random() < 0.5:
                damage_taken = random.randint(10, 20)
                print("You were ambushed inside the cave!")
                take_damage(damage_taken)
                gain_exp(40)
            else:
                print("You explore the cave and find nothing of interest.")
                gain_exp(50)
            get_money_drop()
        else:
            print("You avoid the cave and continue on your way.")
            gain_exp(50)
            get_money_drop()

    elif event_data['event'] == "find_chest":
        if choices.get(choice_input) == "open":
            if random.random() < 0.3:
                damage_taken = random.randint(5, 15)
                print("The chest was trapped! It explodes!")
                take_damage(damage_taken)
                gain_exp(40)
            else:
                print("You open the chest and find some trinkets.")
                gain_exp(50)
                get_equipment_drop()
            get_money_drop()
        else:
            print("You leave the chest alone.")
            gain_exp(50)
            get_money_drop()

    elif event_data['event'] == "encounter_wildlife":
        if choices.get(choice_input) == "investigate":
            if random.random() < 0.6:
                print("It was a friendly animal! You find some berries.")
                gain_exp(50)
            else:
                damage_taken = random.randint(5, 10)
                print("The wildlife attacks! You take damage.")
                take_damage(damage_taken)
                gain_exp(40)
            get_money_drop()
        else:
            print("You leave the wildlife alone.")
            gain_exp(50)
            get_money_drop()

    elif event_data['event'] == "mysterious_traveler":
        if choices.get(choice_input) == "offer help":
            if random.random() < 0.7:
                if random.random() < 0.5:
                    money_found = random.randint(30, 70)
                    print(f"The traveler is grateful and gives you {money_found} gold.")
                    money += money_found
                    gain_exp(70)
                else:
                    print("The traveler grants you ancient wisdom! You feel stronger.")
                    gain_exp(60)
            else:
                damage_taken = random.randint(15, 30)
                money_lost = random.randint(20, 50)
                print(f"The traveler ambushes you! You take {damage_taken} damage and lose {money_lost} gold.")
                take_damage(damage_taken)
                money = max(0, money - money_lost)
                gain_exp(40)
        else:
            print("You ignore the traveler.")
            gain_exp(50)

    elif event_data['event'] == "ancient_ruin":
        if choices.get(choice_input) == "investigate":
            if random.random() < 0.5:
                if random.random() < 0.5:
                    new_artifact = next((item for item in item_shop_list if item['id'] == 201), None)
                    if new_artifact:
                        inventory.append(new_artifact.copy())
                        print(f"You found an ancient artifact: {new_artifact['name']}!")
                    gain_exp(75)
                else:
                    money_found = random.randint(50, 100)
                    print(f"You find hidden treasure! {money_found} gold added.")
                    money += money_found
                    gain_exp(75)
            else:
                damage_taken = random.randint(20, 40)
                print(f"You trigger an ancient trap! Take {damage_taken} damage.")
                take_damage(damage_taken)
                gain_exp(40)
        elif choices.get(choice_input) == "investigate cautiously":
            if random.random() < 0.7:
                money_found = random.randint(20, 60)
                print(f"You carefully investigate and find {money_found} gold.")
                money += money_found
                gain_exp(60)
            else:
                damage_taken = random.randint(10, 25)
                print(f"A minor trap activates! Take {damage_taken} damage.")
                take_damage(damage_taken)
                gain_exp(45)
        else:
            print("You avoid the ruins.")
            gain_exp(50)

    auto_save()
    input("Press Enter to continue...")

def expedition():
    """Starts an expedition, costing stamina and triggering events repeatedly until the player stops."""
    global stamina, item_shop_list
    if not username:
        print("Create a character first!")
        return

    while True:
        if stamina >= 10:
            stamina -= 10
            print("\nYou set out on an expedition...")
            expedition_theme()
            music.play(-1)
            input('\r Press enter to continue.')
            # Reset shop
            item_shop_list = generate_shop_items()
            event_data = random.choice(expedition_events)
            handle_expedition_event(event_data)

            # Ask if player wants to go again
            choice = input("\nDo you want to go on another expedition? (yes/no): ").lower().strip()
            if choice not in ["yes", "y"]:
                print("Returning from expedition.")
                menu_theme()
                break
        else:
            print("You don't have enough stamina to go on another expedition! Try resting.")
            break

def blacksmith_menu():
    """Allows the player to upgrade weapon, armor, or amulet using materials."""
    global equipped, materials

    while True:
        clear_screen()
        print("=== BLACKSMITH ===")
        print("Your materials:")
        if materials:
            for mat, qty in materials.items():
                print(f" - {mat}: {qty}")
        else:
            print("You have no materials yet.")

        print("\nChoose what to upgrade:")
        print("[1] Weapon")
        print("[2] Armor")
        print("[3] Amulet")
        print("[back] Exit")

        choice = input("Your choice: ").lower().strip()
        if choice == "back":
            break

        slot = None
        if choice == "1": slot = "weapon"
        elif choice == "2": slot = "armor"
        elif choice == "3": slot = "amulet"
        else:
            print("Invalid choice.")
            input("Press Enter...")
            continue

        if not equipped.get(slot):
            print("You have nothing equipped in this slot!")
            input("Press Enter...")
            continue

        item = equipped[slot]
        upgrade_item(item)
        input("Press Enter...")

def upgrade_item(item):
    """Handles upgrading of an item with success/fail chance and materials."""
    global materials

    # Determine current upgrade level
    upgrade_level = 0
    if "+" in item["name"]:
        try:
            upgrade_level = int(item["name"].split("+")[-1])
        except:
            upgrade_level = 0

    # Material requirement increases each level
    required_materials = upgrade_level + 1
    material_name = find_enemy_material(item)
    if not material_name:
        print("This item has no upgrade material associated.")
        return

    if materials.get(material_name, 0) < required_materials:
        print(f"Not enough {material_name}! Need {required_materials}, you have {materials.get(material_name, 0)}.")
        return

    # Success chance decreases with each upgrade
    success_chance = max(20, 100 - upgrade_level * 15)

    print(f"Upgrading {item['name']} (Success chance: {success_chance}%)...")
    if random.randint(1, 100) <= success_chance:
        # Success!
        materials[material_name] -= required_materials
        item["name"] = f"{item['name'].split('+')[0].strip()} +{upgrade_level+1}"
        # Buff stats
        if "attack_boost" in item:
            item["attack_boost"] += 2
        if "defense" in item:
            item["defense"] += 2
        if "health_boost" in item:
            item["health_boost"] += 5
        if "mana_boost" in item:
            item["mana_boost"] += 5
        print(f"✅ Upgrade successful! Your item is now {item['name']}.")
    else:
        # Failure
        print("❌ Upgrade failed!")
        materials[material_name] -= required_materials

def find_enemy_material(item):
    """Finds which material corresponds to the item based on its type."""
    if item.get("slot") == "weapon":
        return "Goblin Fang"  # Or you could make weapon-specific materials
    elif item.get("slot") == "armor":
        return "Troll Hide"
    elif item.get("slot") == "amulet":
        return "Cursed Steel"
    return None

def rarity_stars(rarity):
    """Returns a string of stars based on item rarity."""
    rarity_map = {
        "common": "★",
        "uncommon": "★★",
        "rare": "★★★",
        "epic": "★★★★",
        "legendary": "★★★★★"
    }
    return rarity_map.get(rarity.lower(), "★")
 
def rest():
    global stamina, health
    if username:
        stamina_recovered = max_stamina // 2
        health_recovered = max_health // 10
        stamina = min(max_stamina, stamina + stamina_recovered)
        health = min(max_health, health + health_recovered)
        print(f"\nYou rest for a while, recovering {stamina_recovered} stamina and {health_recovered} health.")
        print(f"Current stamina: {stamina}, Current health: {health}")
        auto_save()  
        input('enter to continue')
        clear_screen()

def menu():
    clear_screen()
    if username and class_input:
        health_bar_str = create_bar(health, max_health, bar_length=20, fill_char='♥')
        stamina_bar_str = create_bar(stamina, max_stamina, bar_length=20, fill_char='♦')
        mana_bar_str = create_bar(mana, max_mana, bar_length=20, fill_char='¤')
        exp_bar_str = create_bar(exp, max_exp, bar_length=20, fill_char='▬')

        equipped_weapon_name = equipped["weapon"]["name"] if equipped["weapon"] else "None"
        equipped_amulet_name = equipped["amulet"]["name"] if equipped["amulet"] else "None"
        equipped_armor_name = equipped["armor"]["name"] if equipped["armor"] else "None"
        
        get_current_attack()

        print(" __________________________________________________________")
        print("|                                                          |")
        print(f"|  Player: {username:<48}|")
        print(f"|   Class: {class_input.capitalize():<48}|")
        print(f"|   Level: {level:<48}|")
        print(f"|      XP: {exp_bar_str:<48}|")
        print(f"|  Health: {health_bar_str:<48}|")
        print(f"| Stamina: {stamina_bar_str:<48}|")
        print(f"|    Mana: {mana_bar_str:<48}|")
        print(f"|  Attack: {attack_power:<48}|")
        print(f"|   Money: {money:<48}|")
        print(f"|  Weapon: {equipped_weapon_name:<48}|")
        print(f"|  Amulet: {equipped_amulet_name:<48}|")
        print(f"|   Armor: {equipped_armor_name:<48}|")
        print("|__________________________________________________________|\n")
    else:
        print("Character not created yet. Use '!create' to begin.")

    input("Press Enter to continue...")


def take_damage(damage):
    global health, evasion_active, equipped

    
    armor_def = equipped["armor"]["defense"] if equipped.get("armor") else 0
    damage_after_armor = max(0, damage - armor_def)

    
    if class_input == "assassin" and evasion_active:
        if random.random() < 0.5:
            print("You dodged the attack thanks to Evasion!")
            evasion_active = False
            return
        else:
            evasion_active = False

    health -= damage_after_armor
    if health <= 0:
        health = 0
        print("You have been defeated! Game over.")
        sys.exit()

    if armor_def > 0:
        print(f"You took {damage} damage but your armor blocked {armor_def}! Health reduced by {damage_after_armor}. Current health: {health}.")
    else:
        print(f"You took {damage} damage. Current health: {health}.")

def get_item_price_from_id(item_id):
    """Helper function to find the original shop price of an item."""
    for item in item_shop_list:
        if item['id'] == item_id:
            return item.get('price', 0)
    return 0

def inventory_menu():
    """Displays the player's inventory with interaction and colored rarity."""
    if not inventory:
        print("\nYour inventory is empty.")
        return

    while True:
        print("\n--- Inventory ---")
        for i, item in enumerate(inventory):
            original_price = get_item_price_from_id(item['id'])
            
            
            equipped_status = ""
            for slot in equipped:
                if equipped[slot] and equipped[slot]['id'] == item['id']:
                    equipped_status = " (Equipped)"
                    break
            
            
            rarity = item.get('rarity', 'common').lower()
            stars = "★" * RARITY_STARS.get(rarity, 1)
            display_text = f"[{i+1}] {item['name']} [{stars}]{equipped_status} (ID: {item['id']})"
            if item.get('type') == 'consumable':
                display_text += f" - Restores {item['effect_value']} {item['effect_stat'].capitalize()}"
            elif item.get('slot') == 'weapon':
                display_text += f" - +{item.get('attack_boost', 0)} Attack Power"
            elif item.get('slot') == 'amulet':
                display_text += f" - +{item.get('health_boost', 0)} Health, +{item.get('mana_boost', 0)} Mana"
            elif item.get('slot') == 'armor':
                display_text += f" - +{item.get('defense', 0)} Defense"
            
            
            sell_price = int(original_price * 0.5)
            display_text += f" (Sell for {sell_price} gold)"
            print(display_text)
        
        print("-----------------")
        choice = input("Choose an item number, or type 'back': ").lower().strip()
        if choice == "back":
            break
        
        try:
            item_index = int(choice) - 1
            if 0 <= item_index < len(inventory):
                item = inventory[item_index]
                original_price = get_item_price_from_id(item['id'])
                
                print(f"\nSelected: {item['name']}.")
                actions = ["Back"]
                if item.get('type') == 'consumable':
                    actions.insert(0, "Use")
                if item.get('slot') and (equipped[item['slot']] is None or equipped[item['slot']]['id'] != item['id']):
                    actions.insert(0, "Equip")
                if original_price > 0:
                    actions.append("Sell")

                print(f"Available actions: {'/'.join(actions)}")
                action_choice = input("Your action: ").lower()

                if action_choice == 'use' and 'Use' in actions:
                    use_item(item_index)
                    clear_screen()
                    continue
                elif action_choice == 'equip' and 'Equip' in actions:
                    equip_item(item['id'])
                    clear_screen()
                    continue
                elif action_choice == 'sell' and 'Sell' in actions:
                    sell_item(item_index)
                    clear_screen()
                    continue
                else:
                    print("Invalid action.")
            else:
                print("Invalid item number.")
        except ValueError:
            print("Invalid input. Please enter a number or 'back'.")
        


def sell_item(item_index):
    global money, equipped, inventory
    if item_index < 0 or item_index >= len(inventory):
        print("Invalid item selection.")
        input('press enter to continue.')
        return
    item_to_sell = inventory[item_index]
    original_price = get_item_price_from_id(item_to_sell['id'])
    if original_price > 0:
        sell_price = int(original_price * 0.5)
        money += sell_price
        for slot in equipped:
            if equipped[slot] and equipped[slot]['id'] == item_to_sell['id']:
                equipped[slot] = None
                print(f"You unequipped {item_to_sell['name']} before selling.")
        inventory.pop(item_index)
        print(f"You sold {item_to_sell['name']} for {sell_price} gold.")
        input('press enter to continue.')
        auto_save()  

def use_item(item_index):
    global health, mana
    if item_index < 0 or item_index >= len(inventory):
        print("Invalid item selection.")
        return
    item = inventory[item_index]
    if item.get('type') == 'consumable':
        if item['effect_stat'] == 'health':
            health = min(max_health, health + item['effect_value'])
            print(f"You used a {item['name']} and restored {item['effect_value']} Health.")
        elif item['effect_stat'] == 'mana':
            mana = min(max_mana, mana + item['effect_value'])
            print(f"You used a {item['name']} and restored {item['effect_value']} Mana.")
        inventory.pop(item_index)
        auto_save() 
    else:
        print(f"You cannot use {item['name']} this way. Try equipping it if it's gear.")



def equip_item(item_id):
    global equipped, inventory, class_input
    item_to_equip = next((item for item in inventory if item['id'] == item_id), None)
    if not item_to_equip:
        print("Invalid item ID or item not in inventory.")
        input('press enter to continue.')
        return
    if item_to_equip.get('type') == 'consumable':
        print("You cannot equip a consumable item. Try using it.")
        input('press enter to continue.')
        return
    
    if item_to_equip.get('slot') == 'weapon' and WEAPON_TYPES.get(item_to_equip['weapon_type']) != class_input:
        print(f"You are a {class_input.capitalize()} and cannot equip a {item_to_equip['weapon_type']}.")
        input('press enter to continue.')
        return
    
    slot = item_to_equip.get('slot')
    if slot:
        if equipped.get(slot):
            inventory.append(equipped[slot])
            print(f"You unequipped {equipped[slot]['name']}.")
        equipped[slot] = item_to_equip
        inventory.remove(item_to_equip)
        print(f"You equipped {item_to_equip['name']}.")
        auto_save()
        input('press enter to continue.')

def blackjack():
    """Simple blackjack mini-game with betting."""
    global money
    import random

    if money <= 0:
        print("You have no gold to bet!")
        input("Press Enter...")
        return

    print(f"\nWelcome to Blackjack! You have {money} gold.")
    try:
        bet = int(input("Enter your bet amount: "))
        if bet <= 0:
            print("Bet must be positive.")
            return
        if bet > money:
            print("You don't have enough gold for that bet.")
            return
    except ValueError:
        print("Invalid input.")
        return

    # Initialize deck and hands
    deck = [2,3,4,5,6,7,8,9,10,10,10,10,11] * 4
    random.shuffle(deck)

    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]

    def hand_value(hand):
        value = sum(hand)
        # Handle Ace as 1 if bust
        while value > 21 and 11 in hand:
            hand[hand.index(11)] = 1
            value = sum(hand)
        return value

    def display_hands(show_dealer=False):
        print(f"\nDealer's hand: {dealer_hand[0]} + [?]" if not show_dealer else f"Dealer's hand: {dealer_hand} (Total: {hand_value(dealer_hand)})")
        print(f"Your hand: {player_hand} (Total: {hand_value(player_hand)})")

    # Player turn
    while True:
        display_hands()
        if hand_value(player_hand) == 21:
            print("Blackjack! Let's see if dealer ties...")
            break
        choice = input("Hit or Stand? (h/s): ").lower().strip()
        if choice == "h":
            player_hand.append(deck.pop())
            if hand_value(player_hand) > 21:
                display_hands()
                print("You bust! You lose your bet.")
                money -= bet
                input("Press Enter...")
                return
        elif choice == "s":
            break
        else:
            print("Invalid choice.")

    # Dealer turn
    while hand_value(dealer_hand) < 17:
        dealer_hand.append(deck.pop())

    display_hands(show_dealer=True)
    player_total = hand_value(player_hand)
    dealer_total = hand_value(dealer_hand)

    if dealer_total > 21 or player_total > dealer_total:
        payout = int(bet * (2.5 if player_total == 21 and len(player_hand) == 2 else 2))
        print(f"You win! You gain {payout - bet} gold.")
        money += payout - bet
    elif dealer_total > player_total:
        print("Dealer wins! You lose your bet.")
        money -= bet
    else:
        print("It's a tie! Your bet is returned.")

    input("Press Enter to continue...")

def shop_menu():
    global money, inventory, class_input, item_shop_list

    if not username:
        print("Create a character first!")
        return

    item_shop_list = generate_shop_items()

    while True:
        clear_screen()
        print("\n--- Shop ---")
        print(f"Your money: {money} gold")
        print("Available items:")

        display_items = []
        for item in item_shop_list:
            if item.get('weapon_type') and WEAPON_TYPES.get(item['weapon_type']) != class_input:
                continue
            display_items.append(item)

        for i, item in enumerate(display_items):
            rarity = item.get('rarity', 'common').lower()
            stars = "★" * RARITY_STARS.get(rarity, 1)
            display_text = f"[{i+1}] {item['name']} [{stars}]"
            if item.get('type') == 'consumable':
                display_text += f" (Restores {item['effect_value']} {item['effect_stat'].capitalize()})"
            elif item.get('slot') == 'weapon':
                display_text += f" (+{item.get('attack_boost', 0)} Attack)"
            elif item.get('slot') == 'amulet':
                display_text += f" (+{item.get('health_boost', 0)} Health, +{item.get('mana_boost', 0)} Mana)"
            elif item.get('slot') == 'armor':
                display_text += f" (+{item.get('defense', 0)} Defense)"
            display_text += f" - Price: {item['price']} gold (ID: {item['id']})"
            print(display_text)

        print("-----------------")
        choice = input("Enter item number to buy, 'back' to exit: ").lower()
        if choice == 'back':
            return

        try:
            item_index = int(choice) - 1
            if 0 <= item_index < len(display_items):
                item_to_buy = display_items[item_index]
                buy_item(item_to_buy['id'])
            else:
                print("Invalid item number.")
        except ValueError:
            print("Invalid input. Please enter a number or 'back'.")
        input("Press Enter to continue...")

def daily_reward():
    global last_daily_claim, money, materials

    today = datetime.date.today().isoformat()
    if last_daily_claim == today:
        print("❌ You already claimed your daily reward today! Come back tomorrow.")
        input("Press Enter...")
        return

    # Generate a random reward
    gold_reward = random.randint(100, 300)
    material_reward = random.choice(list(materials.keys())) if materials else None

    money += gold_reward
    print(f"🎁 Daily Reward Claimed! You received {gold_reward} gold.")

    if material_reward:
        materials[material_reward] += 1
        print(f"Bonus: +1 {material_reward}!")

    last_daily_claim = today
    auto_save()
    input("Press Enter...")

def buy_item(item_id):
    global money, inventory
    item_to_buy = next((item for item in item_shop_list if item['id'] == item_id), None)
    if not item_to_buy:
        print("Invalid item ID.")
        return
    if item_to_buy.get('weapon_type') and WEAPON_TYPES.get(item_to_buy['weapon_type']) != class_input:
        print(f"You are a {class_input.capitalize()} and cannot buy a {item_to_buy['weapon_type']}.")
        return
    if money >= item_to_buy['price']:
        money -= item_to_buy['price']
        inventory.append(item_to_buy.copy())
        print(f"You bought {item_to_buy['name']} for {item_to_buy['price']} gold.")
        auto_save()  
    else:
        print("You don't have enough money to buy that item.")

def save_game():
    if not username:
        print("No character to save!")
        return
    
    save_data = {
        "save_version": 2,
        "username": username,
        "class_input": class_input,
        "health": health,
        "stamina": stamina,
        "mana": mana,
        "attack_power": attack_power,
        "base_attack": base_attack,
        "money": money,
        "max_health": max_health,
        "max_stamina": max_stamina,
        "max_mana": max_mana,
        "level": level,
        "exp": exp,
        "max_exp": max_exp,
        "inventory": inventory,
        "equipped": {
            "weapon": equipped.get("weapon"),
            "amulet": equipped.get("amulet"),
            "armor": equipped.get("armor")
        },
        "pets": serialize_pets(),
        "pets": serialize_pets(),
        "current_path": current_path,
        "unlocked_paths": unlocked_paths,
        "quest_progress": quest_progress,
        "materials": materials,
        "last_daily_claim": last_daily_claim,

        

    }



    
    with open(f"{username}_save.json", "w") as f:
        json.dump(save_data, f, indent=4)
    
    print(f"Game saved for {username}!")

def auto_save():
    if not username:
        return
    
    save_data = {
        "save_version": 2,
        "username": username,
        "class_input": class_input,
        "health": health,
        "stamina": stamina,
        "mana": mana,
        "attack_power": attack_power,
        "base_attack": base_attack,
        "money": money,
        "max_health": max_health,
        "max_stamina": max_stamina,
        "max_mana": max_mana,
        "level": level,
        "exp": exp,
        "max_exp": max_exp,
        "inventory": inventory,
        "equipped": {
            "weapon": equipped.get("weapon"),
            "amulet": equipped.get("amulet"),
            "armor": equipped.get("armor")
        },
        "pets": serialize_pets(),
        "pets": serialize_pets(),
        "current_path": current_path,
        "unlocked_paths": unlocked_paths,
        "quest_progress": quest_progress,
        "materials": materials,
        "last_daily_claim": last_daily_claim,

    }



    
    with open(f"{username}_save.json", "w") as f:
        json.dump(save_data, f, indent=4)
    
    print("(Game auto-saved)")

def load_game():
    global username, class_input, health, stamina, mana, attack_power, base_attack
    global money, max_health, max_stamina, max_mana, level, exp, max_exp
    global inventory, equipped
    global current_path, unlocked_paths, quest_progress
    global materials
    global last_daily_claim
    username_input = input("Enter your username to load: ")
    try:
        with open(f"{username_input}_save.json", "r") as f:
            save_data = json.load(f)
        save_version = save_data.get("save_version", 0)  # Default to 0 if not present

        # Version migration
        if save_version < 1:
            # Ensure equipped has all slots (fix for older saves)
            for slot in ["weapon", "amulet", "armor"]:
                if slot not in save_data.get("equipped", {}):
                    save_data["equipped"][slot] = None
            print("Your save file was updated to the latest version!")

        username = save_data.get("username")
        class_input = save_data.get("class_input")
        skills[class_input] = {}
        if class_input == "mage":
            skills[class_input] = {
                "Fireball": {"mana_cost": 50, "damage": lambda: int(get_current_attack() * 5)},
                "Ice Spike": {"mana_cost": 30, "damage": lambda: int(get_current_attack() * 2)}
            }
        elif class_input == "knight":
            skills[class_input] = {
                "Shield Bash": {"mana_cost": 15, "damage": lambda: int(get_current_attack() * 1.2 + max_health * 0.03)},
                "Power Strike": {"mana_cost": 25, "damage": lambda: int(get_current_attack() * 2 + 5 / max_health * 50)}
            }
        elif class_input == "assassin":
            skills[class_input] = {
                "Backstab": {"mana_cost": 20, "damage": lambda: int(get_current_attack() * 1.5)},
                "Evasion": {"mana_cost": 10, "effect": "evasion"}
            }
        health = save_data.get("health")
        stamina = save_data.get("stamina")
        mana = save_data.get("mana")
        attack_power = save_data.get("attack_power")
        base_attack = save_data.get("base_attack")
        money = save_data.get("money")
        max_health = save_data.get("max_health")
        max_stamina = save_data.get("max_stamina")
        max_mana = save_data.get("max_mana")
        level = save_data.get("level")
        exp = save_data.get("exp")
        max_exp = save_data.get("max_exp")
        inventory = save_data.get("inventory", [])
        equipped = save_data.get("equipped", {})

        # PETS
        deserialize_pets(save_data.get("pets", {}))


        current_path = save_data.get("current_path", None)
        if current_path:
            class_paths = paths.get(class_input, {})
            if current_path in class_paths:
                path_data = class_paths[current_path]
                skills[class_input] = {}
                for sk, data in path_data["skills"].items():
                    new_skill = {}
                    if "damage" in data:
                        new_skill["mana_cost"] = data["mana_cost"]
                        new_skill["damage"] = data["damage"]  
                    elif "heal" in data:
                        new_skill["mana_cost"] = data["mana_cost"]
                        new_skill["heal"] = data["heal"]
                    else:
                        new_skill = data
                    skills[class_input][sk] = new_skill
        unlocked_paths = save_data.get("unlocked_paths", [])
        quest_progress = save_data.get("quest_progress", {
            "brawler_kills": 0,
            "mage_dark_mission": False,
            "mage_holy_mission": 0,
            "knight_crusader_mission": 0,
            "knight_berserker_mission": 0,
            "assassin_shadowblade_mission": 0
        })
        materials = save_data.get("materials", {})
        last_daily_claim = save_data.get("last_daily_claim", None)


        # Ensure all equipped slots exist
        for slot in ["weapon", "amulet", "armor"]:
            if slot not in equipped:
                equipped[slot] = None
        


        print(f"Game loaded for {username}!")
        menu()
    except FileNotFoundError:
        print("No saved game found with that username.")



def show_help():
    clear_screen()
    print("=== COMMANDS ===")
    print("!create       - Make a new character")
    print("!expedition/!exp  - Go on an expedition to encounter events or fights")
    print("!shop        - Visit the shop to buy items")
    print("!inventory/!inv   - View your inventory")
    print("!menu       - View your character stats (HP, Mana, Attack, Defense)")
    print("!upgrade     - Open blacksmith menu")
    print("!blackjack   - Gambling <3")
    print("!save        - Manually save your progress")
    print("!load        - Load previously saved game progress")
    print("!help        - Show this help menu")
    print("!quit        - Quit the game")
    print("\nPress Enter to return to the game...")
    input()
    clear_screen()

#dungeon
def roll_dungeon_loot():
    """
    Rolls a reward from the dungeon loot pool with weighted rarity chances,
    favoring class-specific legendary items.
    
    Parameters:
        class_input (str): Player class ("mage", "knight", "assassin")
    
    Returns:
        tuple: (loot_item_dict, rarity_str)
    """
    # Determine rarity based on weighted chance
    roll = random.randint(1, 100)
    if roll <= 40:
        rarity = "common"
    elif roll <= 70:
        rarity = "rare"
    elif roll <= 90:
        rarity = "epic"
    else:
        rarity = "legendary"

    pool = dungeon_loot_pool[rarity]

    # Bias toward class-specific legendaries
    if rarity == "legendary":
        class_items = []
        for item in pool:
            if class_input.lower() == "mage" and any(x in item["name"] for x in ["Staff", "Tome", "Archmage"]):
                class_items.append(item)
            elif class_input.lower() == "knight" and any(x in item["name"] for x in ["Hammer", "Sword", "Paladin"]):
                class_items.append(item)
            elif class_input.lower() == "assassin" and any(x in item["name"] for x in ["Dagger", "Gauntlets"]):
                class_items.append(item)
        # 60% chance to favor class-specific item
        if class_items and random.random() < 0.6:
            loot = random.choice(class_items)
        else:
            loot = random.choice(pool)
    else:
        loot = random.choice(pool)

    return loot, rarity



def dungeon():
    global materials, inventory, money
    
    if materials.get("Dungeon Key", 0) < 1:
        print("❌ You don't have a Dungeon Key! Buy one in the shop or find one in expedition.")
        input("Press Enter...")
        return
    print("🔑 You used 1 Dungeon Key and entered the dungeon!")
    materials["Dungeon Key"] -= 1
    input('Press Enter...')
    dungeon_theme()
    # 4 normal fights
    for stage in range(1, 5):
        print(f"\n--- Dungeon Stage {stage}/5 ---")
        enemy = random.choice(enemies).copy()
        enemy["health"] = int(enemy["health"] * 1.5)  # 50% stronger
        enemy["attack"] = int(enemy["attack"] * 1.3)  # 30% stronger
        fight(enemy)
        if health <= 0:
            print("☠ You were defeated in the dungeon!")
            input()
            menu_theme()
            return

    # Boss fight
    boss_theme()
    boss = random.choice(dungeon_bosses).copy()
    print(f"\n🔥 FINAL STAGE: {boss['name']} Appears!")
    input()
    fight(boss)
    if health <= 0:
        print("☠ You were slain by the dungeon boss...")
        input()
        menu_theme()
        return

    # Reward roll
    loot, rarity = roll_dungeon_loot()
    inventory.append(loot)
    print(f"🎁 Dungeon cleared! You found a {rarity.upper()} item: {loot['name']}!")
    input()
    menu_theme()
    if rarity == "legendary":
        print(f"🔥 LEGENDARY LOOT! {loot['description']}")
        input()
        menu_theme()
    return

# =========================
# PET SYSTEM v1 (Jarvis)
# =========================

# Data
pet_list = [
    {"name": "Dragon",    "type": "air",   "role": "damage_dealer", "rarity": "mythical"},
    {"name": "Alicorn",   "type": "air",   "role": "sustain",        "rarity": "mythical"},
    {"name": "Griffin",   "type": "air",   "role": "amplifier",      "rarity": "mythical"},
    {"name": "Megalodon", "type": "water", "role": "damage_dealer",  "rarity": "mythical"},
    {"name": "Cheetah", "type": "ground", "role": "damage_dealer", "rarity": "rare"},
    {"name": "Lion",    "type": "ground", "role": "amplifier",     "rarity": "rare"},
    {"name": "Shark",   "type": "water",  "role": "damage_dealer", "rarity": "rare"},
    {"name": "Eagle",   "type": "air",    "role": "amplifier",     "rarity": "rare"},
    {"name": "Squid",   "type": "water",  "role": "damage_dealer", "rarity": "rare"},
    {"name": "Panda",   "type": "ground", "role": "sustain",       "rarity": "rare"},
    {"name": "Cat",     "type": "ground", "role": "sustain",       "rarity": "common"},
    {"name": "Dog",     "type": "ground", "role": "amplifier",     "rarity": "common"},
    {"name": "Chicken", "type": "air",    "role": "amplifier",     "rarity": "common"},
    {"name": "Fish",    "type": "water",  "role": "damage_dealer", "rarity": "common"},
    {"name": "Bird",    "type": "air",    "role": "sustain",       "rarity": "common"},
    {"name": "Spider",  "type": "ground", "role": "damage_dealer", "rarity": "common"},
]

egg_shop_list = [
    {"id": 21, "name": "Common Egg",   "rarity": "common",   "price": 200,  "wins_required": 3},
    {"id": 22, "name": "Rare Egg",     "rarity": "rare",     "price": 500,  "wins_required": 6},
    {"id": 23, "name": "Mythic Egg",   "rarity": "mythical", "price": 1500, "wins_required": 10},
]

pet_food_shop_list = [
    {"id": 31, "name": "Common Water Food",   "rarity": "common",   "price":  50, "exp_value":  20, "type": "water"},
    {"id": 32, "name": "Rare Water Food",     "rarity": "rare",     "price": 100, "exp_value":  50, "type": "water"},
    {"id": 33, "name": "Mythic Water Food",   "rarity": "mythical", "price": 200, "exp_value": 140, "type": "water"},
    {"id": 34, "name": "Common Air Food",     "rarity": "common",   "price":  50, "exp_value":  20, "type": "air"},
    {"id": 35, "name": "Rare Air Food",       "rarity": "rare",     "price": 100, "exp_value":  50, "type": "air"},
    {"id": 36, "name": "Mythic Air Food",     "rarity": "mythical", "price": 200, "exp_value": 140, "type": "air"},
    {"id": 37, "name": "Common Ground Food",  "rarity": "common",   "price":  50, "exp_value":  20, "type": "ground"},
    {"id": 38, "name": "Rare Ground Food",    "rarity": "rare",     "price": 100, "exp_value":  50, "type": "ground"},
    {"id": 39, "name": "Mythic Ground Food",  "rarity": "mythical", "price": 200, "exp_value": 140, "type": "ground"},
]

# State
pets_owned = []
active_pet_index = None
egg_inventory = []
pet_food_inventory = []

def rarity_stars(r):
    return {"common":"★", "rare":"★★", "mythical":"★★★"}.get(r, "")

def choose_pet_by_rarity(rarity):
    cands = [p for p in pet_list if p["rarity"] == rarity]
    return random.choice(cands) if cands else None

def add_egg(rarity, source="loot"):
    egg = next((e for e in egg_shop_list if e["rarity"] == rarity), None)
    if not egg: 
        return False
    egg_inventory.append({
        "id": egg["id"], "name": egg["name"], "rarity": egg["rarity"],
        "wins_required": egg["wins_required"], "wins_progress": 0, "source": source
    })
    print(f"You obtained a {egg['name']} ({egg['rarity']}).")
    return True

def add_pet(pet_def):
    pet = {**pet_def, "level":1, "xp":0, "relationship":0}
    pets_owned.append(pet)
    print(f"A new pet hatched: {pet['name']} [{pet['role']}, {pet['type']}, {pet['rarity']}].")
    input()
    return pet

def find_pet_by_name(name):
    for i,p in enumerate(pets_owned):
        if p["name"].lower() == name.lower():
            return i,p
    return None, None

def roll_pet_egg_loot():
    roll = random.randint(1,100)
    if roll <= 10: rarity = "common"
    elif roll <= 14: rarity = "rare"
    elif roll == 15: rarity = "mythical"
    else: return
    add_egg(rarity, source="battle")

def increment_hatch_progress_on_win():
    ch=False
    for egg in egg_inventory:
        if egg["wins_progress"] < egg["wins_required"]:
            egg["wins_progress"] += 1; ch=True
    if ch: print("Your eggs rustle... (+1 win progress)")

def hatch_ready_eggs():
    ready=[e for e in egg_inventory if e["wins_progress"]>=e["wins_required"]]
    if not ready:
        print("No eggs are ready to hatch.")
        input()
        return
    for egg in ready:
        pet_def = choose_pet_by_rarity(egg["rarity"])
        if pet_def: add_pet(pet_def)
        egg_inventory.remove(egg)

def pet_gain_xp(pet, amount):
    pet["xp"] += amount
    while pet["xp"] >= 100:
        pet["xp"] -= 100
        pet["level"] += 1
        pet["relationship"] = min(100, pet["relationship"] + 5)
        print(f"{pet['name']} leveled up! Lv.{pet['level']} (Rel {pet['relationship']}/100)")
        input()

def pet_add_relationship(pet, amount):
    pet["relationship"] = max(0, min(100, pet["relationship"] + amount))

def get_active_pet():
    if active_pet_index is None: return None
    if 0 <= active_pet_index < len(pets_owned):
        return pets_owned[active_pet_index]
    return None

def pet_effect_strength(pet):
    lvl = pet["level"]; rel = pet["relationship"]
    return 1 + (lvl * 0.1) + (rel // 25) * 0.05

def pet_on_battle_start():
    pet = get_active_pet()
    if pet:
        print(f"{pet['name']} is by your side. ({pet['role']})")
        input()

def pet_on_player_attack(base_damage):
    pet = get_active_pet()
    if not pet or pet["role"] != "amplifier":
        return base_damage
    mult = pet_effect_strength(pet)
    boost = 0.10
    return max(1, int(round(base_damage * (1 + boost*(mult-0.9)))))

def pet_extra_damage():
    pet = get_active_pet()
    if not pet or pet["role"] != "damage_dealer":
        return 0
    mult = pet_effect_strength(pet)
    return int(2 * mult)

def pet_on_enemy_attack(enemy_dealt_damage_to_player):
    pet = get_active_pet()
    if not pet or pet["role"] != "sustain":
        return 0
    mult = pet_effect_strength(pet)
    return int(3 * mult)

def pet_on_victory():
    pet = get_active_pet()
    if pet:
        pet_gain_xp(pet, 10)
        pet_add_relationship(pet, 2)
        print("Your pet got 10 exp after the fight!")
        print("Your pet relationship increased by 2!")

def open_pet_shop():
    global money
    while True:
        print("\n--- PET SHOP ---")
        print(f"Gold: {money}")
        print("[1] Buy Eggs")
        print("[2] Buy Pet Food")
        print("[3] Exit")
        c = input("Enter the command number: ").strip()
        if c == "1":
            for e in egg_shop_list:
                print(f"  [{e['id']}] {e['name']} ({e['rarity']}, needs {e['wins_required']} wins) - {e['price']} gold")
            sel = input("Enter egg id to buy or 'b' to back: ").strip().lower()
            if sel == "b": continue
            try:
                eid = int(sel)
                egg = next((x for x in egg_shop_list if x["id"]==eid), None)
                if egg and money >= egg["price"]:
                    money -= egg["price"]; add_egg(egg["rarity"], source="shop")
                else:
                    print("Invalid choice or not enough gold.")
                    input()
            except:
                print("Invalid input.")
                input()
        elif c == "2":
            for f in pet_food_shop_list:
                print(f"  [{f['id']}] {f['name']} ({f['type']}, {f['rarity']}) - {f['price']} gold | XP+{f['exp_value']}")
            sel = input("Enter food id to buy or 'b' to back: ").strip().lower()
            if sel == "b": continue
            try:
                fid = int(sel)
                food = next((x for x in pet_food_shop_list if x['id']==fid), None)
                if food and money >= food["price"]:
                    money -= food["price"]; pet_food_inventory.append(dict(food))
                    print(f"Purchased {food['name']}.")
                    input()
                else:
                    print("Invalid choice or not enough gold.")
                    input()
            except:
                print("Invalid input.")
                input()
        elif c == "3":
            break
        else:
            print("Invalid input.")
            input()

def feed_pet(pet_name):
    idx, pet = find_pet_by_name(pet_name)
    if pet is None:
        print("You don't have that pet."); input();return
    compatible = [f for f in pet_food_inventory if f["type"] == pet["type"]]
    if not compatible:
        print(f"No {pet['type']} food. Buy some at !petshop."); input();return
    print(f"Feeding {pet['name']} (Lv.{pet['level']}, Rel {pet['relationship']}/100)");input()
    for i,f in enumerate(compatible,1):
        print(f"  {i}) {f['name']} ({f['rarity']}) XP+{f['exp_value']}")
    sel = input("Choose number or 'b': ").strip().lower()
    if sel == "b": return
    try:
        k = int(sel)-1; food = compatible[k]
    except:
        print("Invalid choice.");input(); return
    pet_food_inventory.remove(food)
    pet_gain_xp(pet, food["exp_value"]); pet_add_relationship(pet, 3)
    print(f"{pet['name']} enjoyed the meal! (+{food['exp_value']} XP, +3 Relationship)")
    input()

def pet_petting(pet_name):
    idx, pet = find_pet_by_name(pet_name)
    if pet is None:
        print("You don't have that pet.");input(); return
    pet_add_relationship(pet, 2)
    print(f"You pet {pet['name']}. Relationship {pet['relationship']}/100.");input()

def cmd_pets():
    if not pets_owned:
        print("You have no pets yet. Buy eggs at !petshop or win battles for drops."); 
        input()
        return
    print("\\n--- YOUR PETS ---")
    for i,p in enumerate(pets_owned,1):
        tag = "(active)" if active_pet_index == i-1 else ""
        print(f"{i}) {p['name']} {rarity_stars(p['rarity'])} [{p['role']}, {p['type']}] Lv.{p['level']} XP:{p['xp']}/100 Rel:{p['relationship']}/100 {tag}")
    input("Press enter to continue")
def cmd_pet_equip():
    global active_pet_index
    if not pets_owned:
        print("No pets to equip."); 
        input()
        return
    cmd_pets()
    sel = input("Choose pet number to set active: ").strip()
    try:
        k = int(sel)-1; pets_owned[k]
        active_pet_index = k
        print(f"{pets_owned[k]['name']} is now your active pet.")
        input()
    except:
        print("Invalid choice.")
        input()
def cmd_pet_feed():
    if not pets_owned: 
        print("No pets to feed."); 
        input()
        return
    name = input("Enter pet name to feed: ").strip()
    feed_pet(name)
def cmd_pet_pet():
    if not pets_owned: 
        print("No pets yet."); 
        input()
        return
    name = input("Enter pet name to pet: ").strip()
    pet_petting(name)

def cmd_eggs():
    if not egg_inventory:
        print("You have no eggs. Buy from !petshop or win battles."); 
        input()
        return
    print("\\n--- EGGS ---")
    for i,e in enumerate(egg_inventory,1):
        print(f"{i}) {e['name']} {rarity_stars(e['rarity'])} Progress {e['wins_progress']}/{e['wins_required']}  Source:{e.get('source','?')}")
    input()
def cmd_hatch():
    hatch_ready_eggs()

def cmd_petshop():
    open_pet_shop()

def serialize_pets():
    return {
        "pets_owned": pets_owned,
        "active_pet_index": active_pet_index,
        "egg_inventory": egg_inventory,
        "pet_food_inventory": pet_food_inventory
    }

def deserialize_pets(data):
    global pets_owned, active_pet_index, egg_inventory, pet_food_inventory
    pets_owned = data.get("pets_owned", [])
    active_pet_index = data.get("active_pet_index", None)
    egg_inventory = data.get("egg_inventory", [])
    pet_food_inventory = data.get("pet_food_inventory", [])

def listen():
    menu_theme()
    """Main game loop for listening to commands with shortcuts."""
    while True:
        clear_screen()
        if random.randint(1, 3) == 1:
            print(f"💡 {random.choice(tips)}\n")
        command = input("Enter a command (!help for more infomation): ").lower().strip()

        if command == '!create':
            character_creation()
        elif command == '!help':
            show_help()
        elif command == "!daily":
            daily_reward()
        elif command == '!menu':
            menu()
        elif command == '!exp':
            expedition()
        elif command == '!inv':
            inventory_menu()
        elif command == '!shop':
            shop_menu()
        elif command == '!rest':
            rest()
        elif command.startswith('!buy'):
            try:
                parts = command.split()
                if len(parts) > 1:
                    item_id = int(parts[1])
                    buy_item(item_id)
                else:
                    print("Invalid buy command. Use '!buy [item id]'.")
            except (ValueError, IndexError):
                print("Invalid buy command. Use '!buy [item id]'.")
        elif command.startswith('!use'):
            try:
                parts = command.split()
                if len(parts) > 1:
                    item_index = int(parts[1]) - 1
                    use_item(item_index)
                else:
                    print("Invalid use command. Use '!use [inventory index]'.")
            except (ValueError, IndexError):
                print("Invalid use command. Use '!use [inventory index]'.")
        elif command.startswith('!equip'):
            try:
                parts = command.split()
                if len(parts) > 1:
                    item_id = int(parts[1])
                    equip_item(item_id)
                else:
                    print("Invalid equip command. Use '!equip [item id]'.")
            except (ValueError, IndexError):
                print("Invalid equip command. Use '!equip [item id]'.")
        elif command.startswith('!sell'):
            try:
                parts = command.split()
                if len(parts) > 1:
                    item_index = int(parts[1]) - 1
                    sell_item(item_index)
                else:
                    print("Invalid sell command. Use '!sell [inventory index]'.")
            except (ValueError, IndexError):
                print("Invalid sell command. Use '!sell [inventory index]'.")
        elif command == '!quit':
            print("Exiting game. Goodbye!")
            sys.exit()
        elif command == '!save':
            save_game()
        elif command == '!load':
            load_game()
        elif command == '!upgrade':
            blacksmith_menu()
        elif command == '!blackjack':
            blackjack()
        elif command == '!path':
            path_menu()
        elif command == '!dungeon':
            dungeon()
        elif command == '!petshop':
            cmd_petshop()
        elif command == '!pets':
            cmd_pets()
        elif command.startswith('!pet equip'):
            cmd_pet_equip()
        elif command.startswith('!pet feed'):
            cmd_pet_feed()
        elif command.startswith('!pet pet'):
            cmd_pet_pet()
        elif command == '!eggs':
            cmd_eggs()
        elif command == '!hatch':
            cmd_hatch()
        else:
            print("Unknown command.")
            input('enter to continue')


# Start the game loop
if __name__ == "__main__":
    clear_screen()
    welcome_screen()
    listen()





