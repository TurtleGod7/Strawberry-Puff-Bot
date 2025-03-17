from sqlite3 import connect
from os import name as os_name

def unpack_rolled_info(rollInfo: str):
    """
    The function `unpack_rolled_info` takes a string input containing key-value pairs separated by
    semicolons, splits the string into individual pairs, extracts the keys and values, and returns a
    dictionary sorted by keys.
    
    :param rollInfo: The `unpack_rolled_info` function takes a string `rollInfo` as input, which
    contains information about rolled items separated by semicolons. Each item is in the format
    "item_frequency", where "item" is the name of the item and "frequency" is the number of times it
    :type rollInfo: str
    :return: The function `unpack_rolled_info` is returning a dictionary containing the frequency of
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

# The class `Puff` represents a character with attributes such as name, attack, health, owner, and
# level, with a method to level up the character.
class Puff:
    def __init__(self, name, attack, health, owner, level=0):
        self.name = name
        self.attack = attack
        self.health = health
        self.level = level
        self.owner = owner

    def level_up(self):
        self.level += 1
        self.attack += 1
        self.health += 2

def get_puffs_for_battle(puff_names, user_id) -> list[Puff]:
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
        cursor.execute("SELECT stats FROM puffs WHERE name = ?", (puff,))
        puff_data.append(cursor.fetchone())
        
    cursor.close()
    conn.close()
    
    conn = connect("assets\\database\\users.db") if os_name == "nt" else connect("assets/database/users.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT rolledGolds, rolledNormals FROM stats WHERE username = ?", (user_id,))
    data = cursor.fetchone()
    goldRolls = data[0] if data and data[0] else ""
    normalRolls = data[1] if data and data[1] else ""
    packedStats = goldRolls + ";" + normalRolls if goldRolls or normalRolls else ""
    if packedStats == "": packedStats = None
    unpackedStats = unpack_rolled_info(packedStats) # type: ignore
    
    cursor.close()
    conn.close()
    for puff in range(len(puff_data)):
        attack, health = list(map(int,puff_data[puff][0].split(";")))

        # If user_id is provided, get the user's level for the puff
        level = 0
        level = int(unpackedStats.get(puff_names[puff], 0))
        
        # Scale stats based on level
        attack += level
        health += level * 2
        
        final_data.append(Puff(puff_names[puff], attack, health, user_id, level))
    
    return final_data

def get_lineup(user_id):
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

def save_lineup(lineup, user_id):
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

def get_owned(user_id):
    """
    This Python function retrieves owned stats for a specific user from a database and returns the
    unpacked rolled information.
    
    :param user_id: The get_owned function retrieves the rolled golds and normals stats for a specific
    user from a database. The user_id parameter is used to specify the username for which the stats are being retrieved
    :return: The function get_owned is returning a dictionary with the result of calling the
    function unpack_rolled_info with the argument packedStats
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
    return unpack_rolled_info(packedStats) # type: ignore

def battle(puff1: Puff, puff2: Puff):
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
    while puff1.health > 0 and puff2.health > 0:
        puff2.health -= puff1.attack
        puff1.health -= puff2.attack
        if puff1.health and puff2.health <= 0:
            return f"⚔️ It's a draw! ({puff1.name} vs {puff2.name})", 0
        if puff2.health <= 0:
            return f"🏅 {puff1.name} wins! (Lvl {puff1.level}) - <@{puff1.owner}>", 1
        if puff1.health <= 0:
            return f"🏅 {puff2.name} wins! (Lvl {puff2.level}) - <@{puff2.owner}>", -1
    return f"⚔️ It's a draw! ({puff1.name} vs {puff2.name})", 0 # Catch all