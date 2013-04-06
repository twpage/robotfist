import random, pickle, zlib
import objects

def main(pybot):
    
    #hazard = objects.Combatant("#6")
    #core = hazard.addSchema("BASE")
    
    #for stat_name in ["END", "COU", "LDR", "INT", "TECH", "ENERGON"]:
        #core.addStat(stat_name, random.randint(3, 9))
        
    #for mode_name in ["ROBOT", "JEEP"]:
        #mode = hazard.getSchema("BASE").addMode(mode_name)
        #for stat_name in ["STR", "ACC", "AGL", "FRP", "VEL", "ARMOR"]:
            #mode.addStat(stat_name, random.randint(3, 9))

    #hazard.getSchema("BASE").getMode(0).addAttack("Fisticuffs")
    #hazard.getSchema("BASE").getMode(0).addAttack("Laser Rifle")
    #hazard.getSchema("BASE").getMode(1).addAttack("Turret")
    
    #hazard.copySchema("BASE", "CURRENT")
    
    #bonesaw = objects.Combatant("#7")
    hazard = pybot.loadCombatantFromDB("#6")
    #pybot.dumpCombatantToMUSH(hazard)
    #pybot.dumpCombatantToDB(hazard)
    #hazard = objects.loadCombatantFromMUSH(pybot, "#6")
    pass
