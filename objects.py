"""
Todd Page
4/6/2013
"""

from collections import OrderedDict
import copy, re


from errors import InvalidStatError

class Stat:
    """
    Base class for a Stat
    """
    def get(self):
        raise NotImplementedError("Stat does not have get() defined")
    
    def set(self):
        raise NotImplementedError("Stat does not have set() defined")
    
class IntegerStat:
    """
    Individual combat stat (health, power, etc)
    Keeps track of a single number with bounds
    """
    def __init__(self, max_value, init_value=None, AllowBelowZero=False, AllowAboveMax=False):
        self.max_value = max_value
        self.value = init_value if init_value else max_value
        self.AllowBelowZero = AllowBelowZero
        self.AllowAboveMax = AllowAboveMax
        
    def get(self):
        return self.value
    
    def getPercent(self):
        return round((self.value / (1.0 * self.max_value)) * 100, 2)

    def reset(self):
        self.value = self.max_value
        return True
    
    def set(self, new_value):
        self.value = new_value
        self.max_value = new_value
        
    def set_str(self, str_new_value):
        new_value = int(str_new_value)
        self.set(new_value)
        
    def __add__(self, number):
        self.value += number
        return self.checkBounds()
    
    def __sub__(self, number):
        self.value -= number
        return self.checkBounds()

    def checkBounds(self):
        if self.value < 0 and not self.AllowBelowZero:
            self.value = 0
            return True
        
        elif self.value > self.max_value and not self.AllowAboveMax:
            self.value = self.max_value
            return True
        
        else:
            return False
        
    def isZero(self):
        return self.value == 0
    
    def isMax(self):
        return self.value == self.max_value
    
class StringStat:
    def __init__(self, validate_fn, value):
        self.validate_fn = validate_fn
        if not validate_fn(value):
            raise InvalidStatError(str.format("initial value {0} does not match validation function", value))
        self.value = value
        
    def get(self):
        return self.value
    
    def set(self, new_value):
        if not self.validate_fn(new_value):
            return False
        else:
            self.value = new_value
            return True

    def set_str(self, str_new_value):
        self.set(str_new_value.upper())

class ListStat:
    def __init__(self, validate_fn):
        self.validate_fn = validate_fn
        self.value = set([])
        
    def add(self, new_value):
        if self.validate_fn(new_value):
            self.value.add(new_value)
            return True
        else:
            raise InvalidStatError(str.format("value {0} does not match validation function", new_value))
        
    def remove(self, existing_value):
        if self.validate_fn(existing_value):
            self.value.remove(existing_value)
            return True
        else:
            raise InvalidStatError(str.format("value {0} does not match validation function", new_value))
        
    def reset(self):
        self.value = set([])
        
    def get(self):
        return self.value
    
    def set(self, new_value_lst):
        result_lst = [self.add(v) for v in new_value_lst]
        if not all(result_lst):
            raise InvalidStatError(str.format("At least one value in {0} does not match validation function", new_value_lst))
        else:
            return True
        
    def set_str(self, str_new_value):
        new_value_lst = [s.upper() for s in str_new_value.split(" ")]
        self.set(new_value_lst)


class ThingWithStats:
    """
    Schemas, modes, and attacks all have stats
    """
    def __init__(self):
        self.stats_dct = {}
        
    def addStat(self, stat_name, stat):
        if stat_name in self.stats_dct:
            return False
        else:
            self.stats_dct[stat_name] = stat
            stat.name = stat_name ## do this so we dont have to pass in the name twice
            return True
    
    def getStats(self):
        return self.stats_dct.values()
    
    def getStat(self, stat_name):
        return self.stats_dct.get(stat_name, None)
    
    def get(self, stat_name):
        return self.getStat(stat_name).get()
        
    def has(self, stat_name):
        return stat_name in self.stats_dct
    
class Combatant:
    """
    Singleton combat entity, tied to a single DBref# on the MUSH
    """
    def __init__(self, dbref):
        self.dbref = dbref
        self.schema_dct = {}
        #self.addSchema("BASE")
        
    def getSchemas(self):
        return self.schema_dct.values()
    
    def getSchema(self, schema_name):
        return self.schema_dct.get(schema_name, None)
    
    def addSchema(self, schema_name):
        schema = Schema(self, schema_name)
        self.schema_dct[schema_name] = schema
        return schema
    
    def copySchema(self, from_schema_name, to_schema_name):
        if from_schema_name not in self.schema_dct:
            return False
        else:
            copy_schema = copy.deepcopy(self.getSchema(from_schema_name))
            copy_schema.name = to_schema_name
            self.schema_dct[to_schema_name] = copy_schema
            return True
        
    def toMUSH(self):
        """
        re-create this object in MUSHcode
        """
        #mush_lst = [str.format("&XSTATS {0}", self.dbref)]
        mush_lst = [str.format("@wipe {0}/XSTATS", self.dbref)]
        
        for schema in self.getSchemas():
            mush_lst += schema.toMUSH()
            
        return mush_lst
    
    def display(self):
        text = str.format("{0}\n", self.dbref)
        for schema in self.getSchemas():
            text += schema.display()
        
        return text
    
    def base(self):
        return self.getSchema("BASE")
    
    def current(self):
        return self.getSchema("CURRENT")

class Schema(ThingWithStats):
    """
    Container for a combatant's state, typically current, or original/base
    """
    def __init__(self, parent, name):
        ThingWithStats.__init__(self)
        self.parent = parent
        self.name = name
        self.mode = 0
        
        self.flags_lst = []
        self.modes_lst = []
        
    def addMode(self, mode_name):
        mode = Mode(self, mode_name)
        self.modes_lst.append(mode)
        return mode
        
    def getModes(self):
        return self.modes_lst
    
    def getMode(self, mode_num):
        if mode_num < 0 or mode_num >= len(self.modes_lst):
            return None
        else:
            return self.modes_lst[mode_num]
        
    def getCurrentMode(self):
        return self.modes_lst[self.mode]
    
    def setMode(self, new_mode_no):
        self.mode = new_mode_no
        return True
    
    def toMUSH(self):
        """
        re-create this object in MUSHcode
        """
        mush_lst = []
        ## core stats
        for stat in self.getStats():
            mush_lst.append(str.format("&XSTATS`{1}`{2} {0}={3}", self.parent.dbref, self.name, stat.name, stat.get()))
            
        ## modes
        for mode in self.getModes():
            mush_lst += mode.toMUSH()
            
        return mush_lst
    
    def display(self):
        text = str.format("\t{0}\n", self.name)
        for stat in self.getStats():
            text += str.format("\t{0}: {1}\n", stat.name, stat.get())
            
        for mode in self.getModes():
            text += mode.display()
                
        return text
            
class Mode(ThingWithStats):
    """
    (some) combatants have multiple modes, with stats specific to that mode
    ALL combatants have at least 1 primary 'mode'
    """
    def __init__(self, parent, name):
        ThingWithStats.__init__(self)
        self.parent = parent
        self.name = name
        
        self.attacks_lst = []
        
    def getNumber(self):
        """Returns the # in the ordered list of modes for the parent schema"""
        return self.parent.modes_lst.index(self)
    
    def addAttack(self, attack_name):
        attack = Attack(self, attack_name)
        self.attacks_lst.append(attack)
        return attack
    
    def getAttacks(self):
        return self.attacks_lst
    
    def getAttack(self, attack_num):
        if attack_num < 0 or attack_num >= len(self.attacks_lst):
            return None
        else:
            return self.attacks_lst[attack_num]
    
    def toMUSH(self):
        """
        re-create this object in MUSHcode
        """
        mush_lst = []
        
        mush_lst.append(str.format("&XSTATS`{1}`MODE_{2}`{3} {0}={4}", self.parent.parent.dbref, self.parent.name, self.getNumber(), "NAME", self.name))
        
        ## mode stats
        for stat in self.getStats():
            mush_lst.append(str.format("&XSTATS`{1}`MODE_{2}`{3} {0}={4}", self.parent.parent.dbref, self.parent.name, self.getNumber(), stat.name, stat.get()))
            
        ## attacks
        for attack in self.getAttacks():
            mush_lst += attack.toMUSH()
            
        return mush_lst
    
    def display(self):
        text = str.format("\t\tMode {0} - {1}\n", self.getNumber(), self.name)
        
        for stat in self.getStats():
            text += str.format("\t\t{0}: {1}\n", stat.name, stat.get())
            
        for attack in self.getAttacks():
            text += attack.display()
            
        return text
        
class Attack(ThingWithStats):
    """
    Attacks are possessed by combant's modes and have the same basic components that determine damage and effect
    """
    def __init__(self, parent, name):
        ThingWithStats.__init__(self)
        self.parent = parent
        self.name = name
        
    def getNumber(self):
        """Returns the # in the ordered list of attacks for the parent mode"""
        return self.parent.attacks_lst.index(self)
        
    def toMUSH(self):
        mush_lst = []
        mush_lst.append(str.format("&XSTATS`{1}`MODE_{2}`ATTACK_{3}`{4} {0}={5}", self.parent.parent.parent.dbref, self.parent.parent.name, self.parent.getNumber(), self.getNumber(), "NAME", self.name))
        
        ## mode stats
        for stat in self.getStats():
            mush_lst.append(str.format("&XSTATS`{1}`MODE_{2}`ATTACK_{3}`{4} {0}={5}", self.parent.parent.parent.dbref, self.parent.parent.name, self.parent.getNumber(), self.getNumber(), stat.name, stat.get()))
            
        return mush_lst
    
    def display(self):
        text = str.format("\t\t\tAttack {0} - {1}\n", self.getNumber(), self.name)
        
        for stat in self.getStats():
            text += str.format("\t\t\t{0}: {1}\n", stat.name, stat.get())
    
        return text
        
#def loadCombatantFromMUSH(pybot, dbref):
    #combatant = Combatant(dbref)
    #attrib_lst = pybot.getFromMUSH(str.format("th [lattr({0}/XSTATS`**)]", dbref)).split(" ")
    #value_lst = pybot.getFromMUSH(str.format("th [map(#lambda/get({0}/\%0), lattr({0}/XSTATS`**),,|)]", dbref)).split("|")

    #mushdata_dct = dict(zip(attrib_lst, value_lst))
    
    ### set up schemas
    #for attrib, value in mushdata_dct.items():
        #component_lst = attrib.split("`")
        #if len(component_lst) == 2:
            #schema_name = component_lst[1]
            #combatant.addSchema(schema_name)
            #del mushdata_dct[attrib]
            
    ### setup modes
    #modes_rx = re.compile("XSTATS`(.*)`MODE_(\d+)`NAME")
    #for attrib, value in mushdata_dct.items():
        #match = modes_rx.search(attrib)
        #if match:
            #schema_name, mode_num = match.groups()
            #mode_name = value
            #mode = combatant.getSchema(schema_name).addMode(mode_name)
            #mode._number = int(mode_num)
            #del mushdata_dct[attrib]
                
    ### order modes
    #for schema in combatant.getSchemas():
        #schema.modes_lst.sort(key=lambda m: m._number)
    
    ### setup attacks
    #attacks_rx = re.compile("XSTATS`(.*)`MODE_(\d+)`ATTACK_(\d+)`NAME")
    #for attrib, value in mushdata_dct.items():
        #match = modes_rx.search(attrib)
        #if match:
            #schema_name, mode_num, attack_num = match.groups()
            #attack_name = value
            #attack = combatant.getSchema(schema_name).getMode(int(mode_num)).addAttack(attack_name)
            #attack._number = int(attack_num)
            #del mushdata_dct[attrib]
                    
    ### order attacks
    #for schema in combatant.getSchemas():
        #for mode in schema.getModes():
            #mode.attacks_lst.sort(key=lambda a: a._number)
        
    ### setup stats
    #for attrib, value in mushdata_dct.items():
        #component_lst = attrib.split("`")
        #if len(component_lst) == 3:
            #if component_lst[2].startswith("MODE"):
                #continue
            #else:
                #xstats, schema_name, stat_name = component_lst
                #combatant.getSchema(schema_name).addStat(stat_name, int(value))
                #del mushdata_dct[attrib]
                
        #elif len(component_lst) == 4:
            #if component_lst[3].startswith("ATTACK"):
                #continue
            #else:
                #xstats, schema_name, mode_str, stat_name = component_lst
                #mode_num = int(mode_str.split("_")[1])
                #combatant.getSchema(schema_name).getMode(mode_num).addStat(stat_name, int(value))
                #del mushdata_dct[attrib]
                
        #elif len(component_lst) == 5:
            #xstats, schema_name, mode_str, attack_str, stat_name = component_lst
            #mode_num = int(mode_str.split("_")[1])
            #attack_num = int(attack_str.split("_")[1])
            #combatant.getSchema(schema_name).getMode(mode_num).getAttack(attack_num).addStat(stat_name, int(value))
            #del mushdata_dct[attrib]
                
    #return combatant
        

