from _collections_abc import Sequence
from re import sub
from helpers.flags import DEBUG, MONEY_FROM_WIN
from sqlite3 import connect
from os import name as os_name
from random import randint, choice
from main import round_int

effectivenessChart: dict[str, dict[str, float]] = {
    "Melee": {"Melee": 0, "Ranged": .25, "Magic": -.25, "Support": 0, "Tank": -.25},
    "Ranged": {"Melee": -.25, "Ranged": 0, "Magic": .25, "Support": 0, "Tank": -.25},
    "Magic": {"Melee": .25, "Ranged": -.25, "Magic": 0, "Support": .25, "Tank": -.25},
    "Support": {"Melee": 0, "Ranged": 0, "Magic": -.25, "Support": 0, "Tank": -.25},
    "Tank": {"Melee": -.25, "Ranged": -.25, "Magic": -.25, "Support": -.25, "Tank": 0}
}

foodChart: dict[str, list[list[int]]] = {
    "Crit Snack" : [[2], [10]],
    "Turtle Potion" : [[1,4], [5,7]],
    "King Puff's Shield" : [[2,4,6], [-5, 15, 10]],
    "Stelle's Bat" : [[0,3], [10, 7]],
}

def unpack_info(rollInfo: str) -> dict[str, int]:
    """
    The function `unpack_info` takes a string input containing key-value pairs separated by
    semicolons, splits the string into individual pairs, extracts the keys and values, and returns a
    dictionary sorted by keys.

    :param rollInfo: The `unpack_info` function takes a string `rollInfo` as input, which
    contains information about rolled items separated by semicolons. Each item is in the format
    "item_frequency", where "item" is the name of the item and "frequency" is the number of times it
    :type rollInfo: str
    :return: The function `unpack_info` is returning a dictionary containing the frequency of
    each item in the input `rollInfo` string. The items in the dictionary are sorted alphabetically by
    key.
    """
    if rollInfo is None:
        return

    frequency = {}
    split_by_puffs = rollInfo.split(";")
    for split in split_by_puffs:
        try:
            frequency[split.split("_")[0]] = int(split.split("_")[1])
        except:
            continue

    return dict(sorted(frequency.items()))

class DamageType():
    def __init__(self, type: str) -> None:
        self.type = type

    def damageType(self) -> str:
        return self.type

class MagicDamage(DamageType):
    def __init__(self):
        super().__init__("Magic")

class RangedDamage(DamageType):
    def __init__(self):
        super().__init__("Ranged")

class MeleeDamage(DamageType):
    def __init__(self):
        super().__init__("Melee")

class SupportDamage(DamageType):
    def __init__(self):
        super().__init__("Support")

class TankDamage(DamageType):
    def __init__(self):
        super().__init__("Tank")

class BlankDamage(DamageType):
    def __init__(self):
        super().__init__("Blank")

def heal(self, puff_list, current_puff):
    if self.health <= 0: return ""
    heal_amt = self.health * 0.75
    for puff in puff_list:
        puff.health += heal_amt
    return f"{self.name} heals the team for {round(heal_amt,1)} health!"

def laziness(self, puff_list, current_puff):
    buff_amt = self.attack * 0.25 + self.trueDefense
    current_puff.trueDefense += buff_amt
    current_puff.attack -= buff_amt * 0.5
    return f"{self.name} makes {current_puff.name} lazy, increasing their true defense by {round(buff_amt,1)} but reducing their attack by {round(buff_amt*0.5,1)}!"

def its_just_a_feature(self, puff_list, current_puff):
    buff_amt = self.attack * 0.5 + self.defensePenetration * 0.5
    current_puff.defensePenetration += buff_amt
    current_puff.health -= buff_amt * 0.5
    return f"Programmer Puff found bugs in the code, increasing {current_puff.name}'s defense penetration by {round(buff_amt,1)}% reducing their health by {round(buff_amt*0.5,1)}!"

def special_support(self, puff_list, current_puff):
    count = 0
    check_list = ["Strawberry Puff", "Luna Puff", "`Progammer Puff`", "Painter Puff"]
    for puff in puff_list:
        if puff.name in check_list: count += 1
    if count >= 3: 
        self.defense += self.defense
        return f"Skater Puff has a special bond with the team, doubling her defense!"
    else: return ""

def tank_outer_shell(self, puff_list, current_puff):
    if self.health >= 0 or self.revivelikeactionscount >= 1: return ""
    self.health = self.healthorg * 0.25
    self.defense = 17
    self.critChance = 40
    self.critDmg = 70
    self.trueDefense = 5
    self.revivelikeactionscount += 1
    self.types[0] = MeleeDamage()
    return f"Tank Puff's outer shell has been blown off revealing their true form!"

def united_kingdom(self, puff_list, current_puff):
    if self.health > self.healthorg * 0.5 or self.revivelikeactionscount >= 1: return ""
    health_sum = 0
    def_sum = 0
    for puff in puff_list:
        if puff.name == "King Puff": continue
        if puff.health > 0: 
            health_sum += puff.health
            def_sum += puff.defense
    self.health += health_sum * 0.5
    self.defense += def_sum * 0.5
    return f"King Puff unites his kingdom, increasing the centripetal forces within the state; increasing his health by {round(health_sum*0.5,1)} and defense by {round(def_sum*0.5,1)}!"

# List and dict here so it doesn't have to be reinitialized every time puff attacks
stat_names: list[str] = ["attack", "health", "critChance", "critDmg", "defense", "defensePenetration", "trueDefense"]
stat_boosts = {
        "attack": 10,
        "health": 10,
        "critChance": 30,
        "critDmg": 100,
        "defense": 30,
        "defensePenetration": 30,
        "trueDefense": 10
    }

def heavenly_boon(self, puff_list, current_puff):
    # Check and initialize attributes if they don't exist
    if not hasattr(self, "puffboost"):
        self.puffboost = None
    if not hasattr(self, "stattypeboost"):
        self.stattypeboost = None
    if not hasattr(self, "prev_boost_value"):
        self.prev_boost_value = None

    # If a previous boost exists, revert it
    if self.puffboost is not None and self.stattypeboost is not None and self.prev_boost_value is not None:
        setattr(self.puffboost, self.stattypeboost, self.prev_boost_value)

    # Choose a random puff and stat to boost
    choosen_puff = choice(puff_list)
    choosen_stat_name = choice(stat_names)
    

    # Save previous value for reverting later
    self.prev_boost_value = getattr(choosen_puff, choosen_stat_name)
    # Apply boost
    setattr(choosen_puff, choosen_stat_name, self.prev_boost_value + stat_boosts[choosen_stat_name])

    # Save which puff and stat were boosted
    self.puffboost = choosen_puff
    self.stattypeboost = choosen_stat_name

    # Format stat name: insert space before capital letters if camel case
    formatted_stat_name = sub(r'(?<!^)(?=[A-Z])', ' ', choosen_stat_name).capitalize()
    return f"{self.name} grants a heavenly boon! {choosen_puff.name}'s {formatted_stat_name} increased by {stat_boosts[choosen_stat_name]}!"

def terrors_from_the_shadow(self, puff_list, current_puff, otarget, ocurrent_puff):
    chance = randint(1, 100)
    isActive = False
    if chance <= 30: isActive = True
    elif chance <= 50 and self.name == "... ... ... .........": isActive = True
    if isActive:
        otarget.effects.append({"name":"stunned", "lifetime" : 2 if self.name == "... ... ... ........." else 1, "scenario": ["crit"]})
        return f"{self.name} brings terrors from the shadow, stunning {self.name}"
    else: return ""

SPECIAL_ABILITIES = {
    "Fairy Puff": {
        "buff": heal,
    },
    "Sleepy Puff": {
        "buff" : laziness,
    },
    "`Progammer Puff`": {
        "buff" : its_just_a_feature,
    },
    "Skater Puff": {
        "lineup_based_buff" : special_support,
    },
    "Tank Puff": {
        "revive": tank_outer_shell, 
    },
    "King Puff": {
        "revive": united_kingdom,
    },
    "Angel Puff": {
        "buff": heavenly_boon,
    },
}

typeChart = {
    "melee": MeleeDamage,
    "ranged": RangedDamage,
    "magic": MagicDamage,
    "support": SupportDamage,
    "tank": TankDamage
}

class Puff:
    def __init__(self, name: str, data: Sequence[int|float], owner: int, types: list[DamageType], level=0):
        self.name = name
        self.level = level
        self.owner = owner
        self.types = types
        self.attack = data[0]
        self.health = data[1]
        self.healthorg = self.health
        self.critChance = data[2]
        self.critDmg = data[3]
        self.defense = data[4]
        self.defensePenetration = data[5]
        self.trueDefense = data[6]
        self.special_abilities = SPECIAL_ABILITIES.get(name, {})
        self.revivelikeactionscount = 0
        self.effects: list[dict] = []  # Changed to list of dicts for effect tracking
        self.can_attack = True

    def use_special_ability(self, attack_name: str, target: Sequence, current_puff, otarget: Sequence=[], ocurrent_puff=None) -> str:
        if self.special_abilities:
            ability = self.special_abilities.get(attack_name, None)
            if ability and attack_name == "special_attack":
                return ability(self, target, current_puff, otarget, ocurrent_puff) # type: ignore
            elif ability:
                return ability(self, target, current_puff)
        return ""

    def eval_attack(self, scenario):
        """
        Checks all effects in self.effects. If an effect matches the scenario,
        applies its inline function and manages its lifetime.
        """
        # Define effect handlers inline
        effect_handlers = {
            "stunned": lambda puff: setattr(puff, "can_attack", False),
            "poisoned": lambda puff: setattr(puff, "health", puff.health - 5)
        }

        # Track effects to remove after processing
        effects_to_remove = []

        for effect in self.effects:
            effect_name = effect.get("name", "blank")
            lifetime = effect.get("lifetime", 0)

            if scenario not in effect.get("scenario", []): continue
            # Apply effect if handler exists
            handler = effect_handlers.get(effect_name)
            if handler: handler(self)

            # Decrement lifetime
            effect["lifetime"] = lifetime - 1

            # Remove effect if lifetime is up
            if effect["lifetime"] <= 0: effects_to_remove.append(effect)

        # Remove expired effects
        for effect in effects_to_remove: self.effects.remove(effect)
        if not any(effect.get("name") == "stunned" for effect in self.effects): self.can_attack = True

class LineupPuff(Puff):
    def __init__(self, name: str, data: Sequence[int|float], databuff: list[int], owner: int, types: list[DamageType], level=0):
        super().__init__(name, data, owner, types, level)
        self.attackbuff = f"{databuff[0]:+}"
        self.healthbuff = f"{databuff[1]:+}"
        self.critChancebuff = f"{databuff[2]:+}"
        self.critDmgbuff = f"{databuff[3]:+}"
        self.defensebuff = f"{databuff[4]:+}"
        self.defensePenetrationbuff = f"{databuff[5]:+}"
        self.trueDefensebuff = f"{databuff[6]:+}"


def get_puffs_for_battle(puff_names: list[str], user_id: int, buffs: dict[str, str]={}, forlineupfunc: bool=False) -> tuple[Sequence[Puff|LineupPuff], dict[str, str]]:
    """
    The function `get_puffs_for_battle` retrieves puff data from a database, adjusts stats based on user
    level, and returns a list of Puff objects.

    :param puff_names: The `get_puffs_for_battle` function takes a list of `puff_names` as input. It
    then retrieves the stats for each puff from a database, calculates the attack and health stats based
    on the user's level (if provided), and creates a list of `Puff` objects
    :param user_id: The `user_id` parameter in the `get_puffs_for_battle` function is used to specify
    the user for whom you want to retrieve the puffs data. It is used to fetch the user's rolled golds
    and normals stats from the database and then scale the attack and health stats of
    :return: The function `get_puffs_for_battle` returns a list of `Puff` objects with updated attack
    and health stats based on the level of the user associated with each puff. The `Puff` objects are
    created using the puff names, attack, health, user_id, and level information obtained from the
    database queries and calculations within the function.
    """
    puff_data = []
    final_data = []
    conn = connect("assets\\database\\puffs.db") if os_name == "nt" else connect("assets/database/puffs.db")
    cursor = conn.cursor()

    for puff in puff_names:
        cursor.execute("SELECT stats, types FROM puffs WHERE name = ?", (puff,))
        puff_data.append(cursor.fetchone())

    cursor.close()
    conn.close()

    conn = connect("assets\\database\\users.db") if os_name == "nt" else connect("assets/database/users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT rolledGolds, rolledNormals FROM stats WHERE username = ?", (user_id,))
    data = cursor.fetchone()
    cursor.close()
    conn.close()

    goldRolls = data[0] if data and data[0] else ""
    normalRolls = data[1] if data and data[1] else ""
    packedStats = goldRolls + ";" + normalRolls if goldRolls or normalRolls else ""
    if packedStats == "": packedStats = None
    unpackedStats = unpack_info(packedStats) # type: ignore

    for puff in range(len(puff_data)):
        data = list(map(int,puff_data[puff][0].split(";")))
        # 0: Attack, 1: Health, 2: Crit Chance, 3: Crit Dmg, 4: Defense, 5: Defense Penetration, 6: True Defense
        if DEBUG:
            print(f"Unpacked stats: {data}")
        # If user_id is provided, get the user's level for the puff
        level = 0
        level = unpackedStats.get(puff_names[puff],-1)
        if level == -1:
            print(f"Error: {puff_names[puff]} not found in unpackedStats")
            continue
        databuff = [0] * 7

        # Scale stats based on level
        data[0] += level # Attack
        data[1] += level * 2 # health
        data[4] += round_int(.25*level**1.75) # Defense

        buffs_to_be_applied = buffs.get(puff_names[puff], "").split("|")
        for buff in buffs_to_be_applied:
            if DEBUG: print(f"Buff: {buff}"); print(foodChart.get(buff, []))
            if buff == "": continue
            for stat in range(len(foodChart.get(buff, [])[0])):
                if forlineupfunc: databuff[foodChart[buff][0][stat]] += foodChart[buff][1][stat]
                else: data[foodChart[buff][0][stat]] += foodChart[buff][1][stat]
        types = puff_data[puff][1].split(";")
        if not forlineupfunc and puff_names[puff] in buffs: del buffs[puff_names[puff]]
        typeList = []
        if DEBUG: print(f"Original Types: {types}")
        for type in types:
            try: typeList.append(typeChart[type]())
            except: continue
        if len(typeList) == 1: typeList.append(BlankDamage())
        if DEBUG: print(f"Final Types: {typeList}")
        if forlineupfunc:
            final_data.append(
                LineupPuff(puff_names[puff],data,databuff,user_id, typeList, level)
            )
        else:
            final_data.append(
                Puff(puff_names[puff],data,user_id, typeList, level)
            )
    for puff in final_data:
        puff.use_special_ability("lineup_based_buff", final_data, puff)
    return final_data, buffs

def roguelite_get_info(puff_name: str) -> tuple[list, list]:
    """
    The function `roguelite_get_info` retrieves information about a specific puff from a database and
    returns its stats and types.

    :param puff_name: The `puff_name` parameter is a string that represents the name of the puff for
    which you want to retrieve information from the database. It is used to query the database and
    fetch the corresponding stats and types for that specific puff
    :return: The function `roguelite_get_info` returns a tuple containing two tuples. The first tuple
    contains the stats of the specified puff, while the second tuple contains the types associated with
    that puff.
    """
    conn = connect("assets\\database\\puffs.db") if os_name == "nt" else connect("assets/database/puffs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT stats, types FROM puffs WHERE name = ?", (puff_name,))
    data: tuple = cursor.fetchone()
    cursor.close()
    conn.close()
    data[0].split(";"); data[1].split(";")
    for type in data[1]: type = typeChart[type]()
    if len(data[1]) == 1: data[1].append(BlankDamage())
    return data

def get_lineup(user_id: int):
    """
    The function `get_lineup` retrieves a user's PvP lineup from a database and returns it as a list of
    lineup items.

    :param user_id: The `get_lineup` function retrieves the lineup data for a specific user from a
    database table named `pvp_lineup`. The function takes a `user_id` as an optional parameter, which is
    used to identify the user whose lineup data needs to be retrieved
    :return: The function `get_lineup` returns a list of lineup data for a specific user, retrieved from
    a database table named `pvp_lineup`. If the user does not have any lineup data stored in the
    database, an empty list is returned.
    """
    conn = connect("assets\\database\\users.db") if os_name == "nt" else connect("assets/database/users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO pvp_lineup (username) VALUES (?)", (user_id,))
    cursor.execute("SELECT lineup FROM pvp_lineup WHERE username = ?", (user_id,))
    data = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return data.split(";") if data else []

def save_lineup(lineup: list[str], user_id: int) -> None:
    """
    The `save_lineup` function saves a lineup for a user in a database, formatting the lineup and
    updating the database with the user's ID.

    :param lineup: The `save_lineup` function takes a lineup list and an optional user_id as parameters.
    The lineup list contains the elements that make up the lineup that needs to be saved. The user_id is
    an optional parameter that specifies the user for whom the lineup is being saved
    :param user_id: The `user_id` parameter in the `save_lineup` function is used to specify the user
    for whom the lineup is being saved. It is an optional parameter, meaning it has a default value of
    `None`. If a `user_id` is provided when calling the function, the lineup will
    """
    conn = connect("assets\\database\\users.db") if os_name == "nt" else connect("assets/database/users.db")
    cursor = conn.cursor()

    formattedLineup = ";".join(lineup)
    cursor.execute("INSERT OR IGNORE INTO pvp_lineup (username) VALUES (?)", (user_id,))
    cursor.execute("UPDATE pvp_lineup SET lineup = ? WHERE username = ?", (formattedLineup, user_id,))

    conn.commit()
    cursor.close()
    conn.close()

def get_owned(user_id: int) -> dict[str, int]:
    """
    This Python function retrieves owned stats for a specific user from a database and returns the
    unpacked rolled information.

    :param user_id: The get_owned function retrieves the rolled golds and normals stats for a specific
    user from a database. The user_id parameter is used to specify the username for which the stats are being retrieved
    :return: The function get_owned is returning a dictionary with the result of calling the
    function unpack_info with the argument packedStats
    """
    conn = connect("assets\\database\\users.db") if os_name == "nt" else connect("assets/database/users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT rolledGolds, rolledNormals FROM stats WHERE username = ?", (user_id,))
    data = cursor.fetchone()
    goldRolls = data[0] if data and data[0] else ""
    normalRolls = data[1] if data and data[1] else ""
    packedStats = goldRolls + ";" + normalRolls if goldRolls or normalRolls else ""
    if packedStats == "": packedStats = None
    cursor.close()
    conn.close()
    return unpack_info(packedStats) # type: ignore

def battle(puff1: Puff | LineupPuff, puff2: Puff | LineupPuff, context1: Sequence[Puff | LineupPuff], context2: Sequence[Puff | LineupPuff]) -> tuple[Sequence[str | int], Sequence[Puff | LineupPuff], Sequence[Puff | LineupPuff]]:
    """
    This Python function simulates a battle between two Puff objects by reducing their health based on
    their attack values until one of them wins or it's a draw.

    :param puff1: Puff object representing the first creature in the battle. It has attributes like
    name, health, attack, level, and owner
    :type puff1: Puff
    :param puff2: Puff 2 is an instance of the Puff class, representing a character or creature in a
    battle. It has attributes such as health, attack power, name, level, and owner. In the battle
    function, puff2's health is reduced by puff1's attack power in each round of
    :type puff2: Puff
    :return: The `battle` function returns a tuple containing a message indicating the outcome of the
    battle and an integer value representing the result. The message can be one of the following:
    - If both `puff1` and `puff2` have health less than or equal to 0, it returns "⚔️ It's a draw!
    (puff1.name vs puff2.name)"
    """
    events = []
    events.extend(["--------------",f"**Battle**: {puff1.name} vs {puff2.name}"])
    if puff2.health <= 0: return [f"🏅 {puff1.name} wins! (Lvl {puff1.level}) - <@{puff1.owner}>", 1], context1, context2
    if puff1.health <= 0: return [f"🏅 {puff2.name} wins! (Lvl {puff2.level}) - <@{puff2.owner}>", -1], context1, context2
    tank1: list[int] = []
    tank2: list[int] = []
    ranged1: list[int] = []
    ranged2: list[int] = []
    support1: list[int] = []
    support2: list[int] = []
    pos1: int = context1.index(puff1)
    pos2: int = context2.index(puff2)
    for _ in range(len(context1)):
        if context1[_].types[0].type == "Tank" or context1[_].types[1].type == "Tank":
            tank1.append(_) # Only adds indexes for references instead of copying
        if context1[_].types[0].type == "Ranged" or context1[_].types[1].type == "Ranged":
            ranged1.append(_)
        if context1[_].types[0].type == "Support" or context1[_].types[1].type == "Support":
            support1.append(_)
    for _ in range(len(context2)):
        if context2[_].types[0].type == "Tank" or context2[_].types[1].type == "Tank":
            tank2.append(_)
        if context2[_].types[0].type == "Ranged" or context2[_].types[1].type == "Ranged":
            ranged2.append(_)
        if context2[_].types[0].type == "Support" or context2[_].types[1].type == "Support":
            support2.append(_)
    def perform_attack(attacker, defender, attacker_context, defender_context, attacker_support, attacker_ranged, defender_tank, attacker_pos, events):
        if attacker.can_attack == False: return
        if DEBUG:
            print(f"{attacker.name} ({attacker.health}) vs {defender.name} ({defender.health})\nOpponent: {attacker.owner} vs {defender.owner}")
        chance = randint(1, 100)
        attack = 0
        typeBuff = 0
        # Support buffs
        for puff in attacker_support:
            result = attacker_context[puff].use_special_ability("buff", attacker_context, attacker)
            if result != "": events.append(result)
        # Crit calculation
        attack += attacker.attack
        result = attack.use_special_ability("special_attack", attacker_context, attacker, defender_context, defender)
        if result != "": events.append(result)
        if chance <= attacker.critChance:
            attack *= (attacker.critDmg * .10 + 1)
            puff2.eval_attack("crit") # Checks for effects to activate
            events.append(f"{attacker.name} crits {defender.name} for {round(attack,1 )} damage!")
        # Ranged support
        for rangedpuff in range(len(attacker_ranged)):
            if attacker == attacker_context[attacker_ranged[rangedpuff]]: continue
            calcattack = attacker_context[attacker_ranged[rangedpuff]].attack * (.8 + (.1 * (attacker_ranged[rangedpuff] - attacker_pos)))# Base attack + 10% for each pos away
            if chance <= (attacker_context[attacker_ranged[rangedpuff]].critChance)-5*(attacker_ranged[rangedpuff] - attacker_pos):# checks crit, reduces by 5 for each pos away
                calcattack = calcattack * (attacker_context[attacker_ranged[rangedpuff]].critDmg * .10 + 1)
                events.append(f"{attacker_context[attacker_ranged[rangedpuff]].name} crits {defender.name} for {round(calcattack,1 )} damage with ranged support!")
            attack += calcattack
        SafeDmg = attack * attacker.defensePenetration
        DefendableDmg = (attack - SafeDmg) * (1 - (defender.defense * .01))
        attack = SafeDmg + DefendableDmg - defender.trueDefense
        # Type effectiveness
        for type in attacker.types:
            try:
                typeBuff += effectivenessChart[type.type][defender.types[0].type]
                typeBuff += effectivenessChart[type.type][defender.types[1].type]
            except: continue
        attack = attack * (1 + typeBuff)
        # Tank mechanics
        # Tank mechanics refactored to reduce repetition
        tanks_to_hit = []
        if len(defender_tank) > 0 and (defender.types[0].type != "Tank" or defender.types[1].type != "Tank"):
            attack_split = attack / (len(defender_tank) + 1)
            tanks_to_hit = defender_tank
        elif len(defender_tank) > 1 and (defender.types[0].type == "Tank" or defender.types[1].type == "Tank"):
            attack_split = attack / len(defender_tank)
            tanks_to_hit = [tank for tank in defender_tank if defender_context[tank].name != defender.name]
        else: attack_split = None  # No tank splitting

        if tanks_to_hit and attack_split is not None:
            for tank_idx in tanks_to_hit:
                defender_context[tank_idx].health -= attack_split
                if defender_context[tank_idx].health <= 0:
                    defender_context[tank_idx].use_special_ability("revive", defender_context, defender_context[tank_idx])
                    if defender_context[tank_idx].health <= 0: events.append(f"{defender_context[tank_idx].name} has fainted!")
        defender.health -= attack

    while puff1.health > 0 and puff2.health > 0:
        perform_attack(
            puff1, puff2, context1, context2, support1, ranged1, tank2, pos1, events
        )
        perform_attack(
            puff2, puff1, context2, context1, support2, ranged2, tank1, pos2, events
        )
        if DEBUG:
            print(f"After a fight: Puff1: {puff1.health}, Puff2: {puff2.health}")
        if puff1.health <= 0 and puff2.health <= 0:
            puff1.use_special_ability("revive", context1, puff1)
            puff2.use_special_ability("revive", context2, puff2)
            events.extend([f"⚔️ It's a draw! ({puff1.name} vs {puff2.name})", 0])
            continue
        if puff2.health <= 0:
            puff2.use_special_ability("revive", context2, puff2)
            events.extend([f"🏅 {puff1.name} wins! (Lvl {puff1.level}) - <@{puff1.owner}>", 1])
            continue
        if puff1.health <= 0:
            puff1.use_special_ability("revive", context1, puff1)
            events.extend([f"🏅 {puff2.name} wins! (Lvl {puff2.level}) - <@{puff2.owner}>", -1])
            continue
    return events, context1, context2 # Catch all
    # Change to return a list of events that has happened with score at the end and the new context lists

def finalize_battle(winner: int, loser: int) -> None:
    conn = connect("assets\\database\\users.db") if os_name == "nt" else connect("assets/database/users.db")
    cursor = conn.cursor()

    cursor.executemany("UPDATE stats SET totalBattles = totalBattles + 1 WHERE username = ?", [(winner,), (loser,)])
    cursor.execute("UPDATE stats SET win = win + 1 WHERE username = ?", (winner,))
    cursor.execute("UPDATE stats SET loss = loss + 1 WHERE username = ?", (loser,))
    cursor.execute("UPDATE stats SET money = money + " + str(MONEY_FROM_WIN) + " WHERE username = ?", (winner,))
    conn.commit()
    cursor.close()
    conn.close()

ROGUELITE_MODIFIERS = {
    "Volcanic": {"description": "All puffs take 5% max HP damage per turn", "effect": "health_multiplier 0.95"},
    "Critical Boost": {"description": "+50% crit damage but -30% defense", "effect": "crit_damage 1.5 defense 0.7"},
    "Tank Meta": {"description": "Tank-type puffs gain +40% HP", "effect": "tank_health 1.4"},
    "Glass Cannon": {"description": "Attack doubled but HP halved", "effect": "attack 2.0 health 0.5"},
}

class RogueliteRun:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.floor = 1
        self.health = 100
        self.shards = 0
        self.modifiers: list[str] = []
        self.buffs: dict[str, float] = {}
        self.lineup: list[str] = []
        
    def apply_modifier(self, modifier: str):
        """Parse and apply modifier effects"""
        effects = ROGUELITE_MODIFIERS[modifier]["effect"].split()
        for i in range(0, len(effects), 2):
            stat = effects[i]
            value = float(effects[i+1])
            self.buffs[stat] = value

    def calculate_damage(self, base_damage: float) -> float:
        """Apply all buffs to damage calculation"""
        modified = base_damage
        if 'attack' in self.buffs:
            modified *= self.buffs['attack']
        if 'crit_damage' in self.buffs:
            modified *= self.buffs['crit_damage']
        return modified

    def save_to_db(self):
        """Save current run state to database"""
        conn = connect("assets/database/users.db")
        cursor = conn.cursor()
        cursor.execute("""
            REPLACE INTO roguelite_runs 
            (user_id, floor, health, shards, modifiers, buffs, lineup)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.user_id,
                self.floor,
                self.health,
                self.shards,
                ";".join(self.modifiers),
                ";".join(f"{k}_{v}" for k,v in self.buffs.items()),
                ";".join(self.lineup)
            ))
        conn.commit()
        cursor.close()

def initialize_roguelite_run(user_id: int) -> RogueliteRun:
    """Start a new roguelite run with base lineup"""
    run = RogueliteRun(user_id)
    
    # Get user's regular lineup
    base_lineup = get_lineup(user_id)
    run.lineup = base_lineup[:5]  # First 5 puffs
    
    # Add initial modifier every 5 floors
    if run.floor % 5 == 0:
        modifier = choice(list(ROGUELITE_MODIFIERS.keys()))
        run.modifiers.append(modifier)
        run.apply_modifier(modifier)
    
    run.save_to_db()
    return run

PRESET_LINEUPS = {
    0: [  # Tier 0 (floors 0–4)
        ["Normal Puff", "Normal Puff", "Normal Puff"],
        ["Tarantula Puff", "Normal Puff", "Ice Cream Puff"]
    ],
    1: [  # Tier 1 (floors 5–9)
        ["Infected Puff", "Ice Cream Puff", "Rectangle Puff", "Normal Puff"],
        ["Tarantula Puff", "Infected Puff", "Normal Puff", "Ice Cream Puff"]
    ],
    2: [  # Tier 2 (floors 10–14)
        ["Rectangle Puff", "Tarantula Puff", "Infected Puff", "Ice Cream Puff", "Normal Puff"]
        # Add more good synergies here...
    ],
    # ...
}

def generate_roguelite_opponent(run: RogueliteRun) -> dict:
    tier = run.floor // 5
    lineup_pool = PRESET_LINEUPS.get(tier, PRESET_LINEUPS[max(PRESET_LINEUPS)])  # Fallback to highest tier
    chosen_lineup = choice(lineup_pool)

    scaled_puffs = []
    for name in chosen_lineup:
        base_stats, types = roguelite_get_info(name)
        scaled_stats = [s * (1 + 0.2 * tier) for s in base_stats]
        scaled_puffs.append(
            Puff(
                name=name,
                data=scaled_stats,
                owner=0,
                types=types,
                level=tier
            )
        )
    
    return {
        "lineup": scaled_puffs,
        "description": f"Floor {run.floor} AI Opponent (Tier {tier})",
        "modifiers": run.modifiers
    }


def process_roguelite_battle(player_puffs: Sequence[Puff | LineupPuff], ai_puffs: Sequence[Puff | LineupPuff], run: RogueliteRun) -> dict:
    """Run a battle and return results"""
    battle_log = []
    player_health_start = sum(p.health for p in player_puffs)
    
    # Simulate battle rounds
    for p1, p2 in zip(player_puffs, ai_puffs):
        result, player_puffs, ai_puffs = battle(p1, p2, player_puffs, ai_puffs)
        battle_log.extend(result)
    
    # Calculate damage taken
    player_health_end = sum(p.health for p in player_puffs)
    damage_taken = player_health_start - player_health_end
    
    # Apply floor modifiers
    for modifier in run.modifiers:
        if "Volcanic" in modifier:
            damage_taken += sum(p.health * 0.05 for p in player_puffs)

    return {
        "log": battle_log,
        "damage_taken": int(damage_taken),
        "victory": sum(x for x in battle_log if isinstance(x, int)) >= 0
    }

def calculate_shard_reward(floor: int) -> int:
    """Calculate currency reward based on floor"""
    base = floor * 10
    bonus = floor ** 1.5
    return int(base + bonus)

def get_available_upgrades(user_id: int) -> list[dict]:
    """Get upgrades available for purchase"""
    return [
        {
            "id": 1,
            "name": "Reinforced Armor",
            "cost": 50,
            "effect": "Adds +10% base HP to all puffs",
            "type": "permanent"
        },
        {
            "id": 2,
            "name": "Crit Boost",
            "cost": 75,
            "effect": "+15% critical hit chance",
            "type": "temporary"
        }
    ]