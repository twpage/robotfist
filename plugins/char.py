from objects import IntegerStat, StringStat, ListStat, Combatant, Schema, Mode, InvalidStatError
from errors import CharacterBuildError

CATALOG_ATTACK_TYPE = {
    "MELEE": {"cost": 0},
    "RANGED": {"cost": 0},
    "VELOCITY": {"cost": 0},
    "AREA-MELEE": {"cost": 2},
    "AREA-RANGED": {"cost": 2}
}

CATALOG_DAMAGE_TYPE = {
    "ENERGY": {"cost": 1},
    "IMPACT": {"cost": 1},
    "BALLISTIC": {"cost": 1},
    "FIRE": {"cost": 1},
    "EXPLOSIVE": {"cost": 1},
    "AIR": {"cost": 1},
    "SONIC": {"cost": 1},
    "WATER": {"cost": 1},
    "ACID": {"cost": 1},
    "MAGNETIC": {"cost": 1},
    "PLASMA": {"cost": 1},
    "ELECTRIC": {"cost": 1},
    "MISC": {"cost": 1},
}

CATALOG_DEFENSE_LEVEL = {
    "PROTECTED": {},
    "GUARDED": {},
    "NEUTRAL": {},
    "AGGRESSIVE": {},
    "FEARLESS": {},
    "HIDDEN": {},
    "OFF-GUARD": {},
    "EVADE": {}
}
    
CATALOG_CORE_STAT = {
    "SPECIES": {},
    "ENERGON": {},
    "COU": {"fullname": "Courage"},
    "LDR": {"fullname": "Leadership"},
    "TECH": {"fullname": "Technical"},
    "INT": {"fullname": "Intelligence"},
    "END": {"fullname": "Endurance"},
    "DEFENSE-LEVEL": {},
    "COMBAT-FLAGS": {}
}

CATALOG_MODE_STAT = {
    "NAME": {},
    "STR": {"fullname": "Strength"},
    "FRP": {"fullname": "Firepower"},
    "ACC": {"fullname": "Accuracy"},
    "AGL": {"fullname": "Agility"},
    "VEL": {"fullname": "Velocity"},
    "SIZE": {},
    "ARMOR": {},
    "ABILITIES": {}
}

CATALOG_ATTACK_STAT = {
    "ATTACK_TYPE": {},
    "DAMAGE_LEVEL": {},
    "DAMAGE_TYPE": {},
    "EFFECT": {}
}

CATALOG_ABILITIES = {
    "FLIGHT": {"cost": 2},
    "SWIM": {"cost": 2},
    "DIVE": {"cost": 2},
    "SPACE-FLIGHT": {"cost": 2},
    "CRACKSHOT": {"cost": 4},
    "INSPIRE": {"cost": 3},
    "EVADE": {"cost": 9},
    "REPAIR": {"cost": 5}
}

CATALOG_SPECIES = {
    "ROBOT": {"modes": 2},
    "HUMAN": {},
    "ALIEN": {},
    "VEHICLE": {},
    "WEAPON": {},
    "BASE": {}
}

CATALOG_COMBAT_FLAG = {
    "COMBAT": {},
    "SCARED": {},
    "CRIPPLED": {},
    "BLINDED": {},
    "UNCON": {},
    "STUNNED": {}
}

CATALOG_ATTACK_EFFECT = {
    "BLIND": {"cost": 2},
    "CRIPPLE": {"cost": 2},
    "STUN": {"cost": 5},
    "ACCURATE": {"cost": 2},
    "INACCURATE": {"cost": -2},
    "EFFICIENT": {"cost": 2},
    "OVERPOWERED": {"cost": -1},
    "NO-ARMOR": {"cost": 3},
    "NO-SIZE": {"cost": 2}
}

## validation functions
def isValidDefenseLevel(x): return x in CATALOG_DEFENSE_LEVEL.keys()
def isValidAbility(x): return x in CATALOG_ABILITIES.keys()
def isValidSpecies(x): return x in CATALOG_SPECIES.keys()
def isValidCombatFlag(x): return x in CATALOG_COMBAT_FLAG.keys()
def isValidDamageType(x): return x in CATALOG_DAMAGE_TYPE.keys()
def isValidAttackType(x): return x in CATALOG_ATTACK_TYPE.keys()
def isValidAttackEffect(x): return x in CATALOG_ATTACK_EFFECT.keys()
def isAlwaysValid(x): return True

## character generation
class mod_combatant(object):
    def __init__(self, fn):
        self.fn = fn
        
    def __call__(self, *args):
        pybot = args[0]
        dbref = args[3] # DBref being editted is always the 4th argument
        char = pybot.loadCombatant(dbref)
        largs = list(args)
        largs[3] = char
        args = tuple(largs)
        self.fn(*args)
        pybot.saveCombatant(char)

@mod_combatant
def init(pybot, enactor, from_loc, char, species, *args):
    base = char.addSchema("BASE")
    
    ## core stats
    base.addStat("SPECIES", StringStat(isValidSpecies, species))
    base.addStat("DEFENSE-LEVEL", StringStat(isValidDefenseLevel, "NEUTRAL"))
    base.addStat("COMBAT-FLAGS", ListStat(isValidCombatFlag))
    base.addStat("ENERGON", IntegerStat(50, 50, False, True))
    for st in ["COU", "LDR", "TECH", "INT", "END"]:
        base.addStat(st, IntegerStat(1))
    
    ## add modes
    num_modes = CATALOG_SPECIES[species].get("modes", 1)
    if num_modes > 1 and len(args) != (num_modes - 1):
        raise CharacterBuildError(str.format("alternate mode names not provided for species with more than 1 mode"))
        
    for m in range(num_modes):
        mode_name = species if m == 0 else args[m-1]
        mode = base.addMode(mode_name)
        _initMode(mode, mode_name)
            
    char.copySchema("BASE", "CURRENT")
    pybot.pemit(enactor, str.format("Initialized combatant {0} - [name({0})] ", char.dbref))
    return True

@mod_combatant
def addmode(pybot, enactor, from_loc, char, mode_name):
    mode = char.base().addMode(mode_name)
    _initMode(mode, mode_name)
    pybot.pemit(enactor, str.format("Added mode #{0} '{1}' to [name({2})]", mode.getNumber(), mode.name, char.dbref))
    return mode

def _initMode(mode, mode_name):
    mode.addStat("NAME", StringStat(isAlwaysValid, mode_name.title()))
    mode.addStat("ABILITIES", ListStat(isValidAbility))
    for st in ["STR", "FRP", "AGL", "ACC", "VEL", "SIZE", "ARMOR"]:
        mode.addStat(st, IntegerStat(1))

@mod_combatant
def core(pybot, enactor, from_loc, char, stat_name, new_value):
    stat_name = stat_name.upper()
    char.base().getStat(stat_name).set_str(new_value)
    pybot.pemit(enactor, str.format("Core stat {1} for [name({0})] ({0}) set to {2}", char.dbref, stat_name, new_value))
    return True

@mod_combatant
def mode(pybot, enactor, from_loc, char, str_mode_no, stat_name, new_value):
    stat_name = stat_name.upper()
    mode_no = int(str_mode_no)
    char.base().getMode(mode_no).getStat(stat_name).set_str(new_value)
    pybot.pemit(enactor, str.format("Mode {3} stat {1} for [name({0})] ({0}) set to {2}", char.dbref, stat_name, new_value, mode_no))
    return True

@mod_combatant
def attack(pybot, enactor, from_loc, char, str_mode_no, str_attack_no, stat_name, new_value):
    stat_name = stat_name.upper()
    mode_no = int(str_mode_no)
    attack_no = int(str_attack_no)
    char.base().getMode(mode_no).getAttack(attack_no).getStat(stat_name).set_str(new_value)
    pybot.pemit(enactor, str.format("Attack {4} on mode {3} stat {1} for [name({0})] ({0}) set to {2}", char.dbref, stat_name, new_value, mode_no, attack_no))
    return True

@mod_combatant
def diff(pybot, enactor, from_loc, char):
    """
    Return differences between BASE and CURRENT schema
    """
    R = []
    ## core
    core_diff_lst = [st for st in CATALOG_CORE_STAT if char.base().get(st) != char.current().get(st)]
    R.append(str.format("Core Stats: {0}", "(No differences)" if not core_diff_lst else " ".join(core_diff_lst)))
    
    ## num modes
    base_modes = len(char.base().getModes())
    current_modes = len(char.current().getModes())
    if base_modes != current_modes:
        R.append(str.format("Number of modes is different: {0} (BASE) vs {1} (CURRENT)", base_modes, current_modes))
        
    else:
        for mode_no in range(base_modes):
            base_mode = char.base().getMode(mode_no)
            current_mode = char.current().getMode(mode_no)
            mode_diff_lst = [st for st in CATALOG_MODE_STAT if base_mode.get(st) != current_mode.get(st)]
            R.append(str.format("Mode {1} Stats: {0}", "(No differences)" if not mode_diff_lst else " ".join(mode_diff_lst), mode_no))
    
    pybot.pemit(enactor, R)
    
@mod_combatant
def stamp(pybot, enactor, from_loc, char, to_schema="CURRENT"):
    char.copySchema("BASE", to_schema)
    pybot.pemit(enactor, str.format("Copied BASE Schema to {1} for [name({0})] ({0})", char.dbref, to_schema))
    return True