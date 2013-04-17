"""
Todd Page
4/16/2013

large-form display commands
"""

## standard libraries
## custom libraries
from char import CATALOG_MODE_STAT

def profile(pybot, enactor_dbref, from_loc_dbref, target_dbref=None):
    R = []
    
    if not target_dbref:
        target_dbref = enactor_dbref
        
    target = pybot.loadCombatant(target_dbref)
    
    R.append(str.format("[header(PROFILE: [name({0})] \[{1}\])]", target.dbref, target.base().get("SPECIES")))
    
    ## base / mode 1
    top_dct = {st: target.base().get(st) for st in ["END", "INT", "LDR", "COU", "TECH", "ENERGON"]}
    top_dct.update({st: target.base().getMode(0).get(st) for st in ["STR", "FRP", "ACC", "AGL"]})
    #123456789012345678901234567890123456789012345678901234567890123456789012345678
    R.append(str.format("""
BASE STATS / MODE 1
Strength     {STR:3}                    Intelligence    {INT:3}
Firepower    {FRP:3}                    Leadership      {LDR:3}
Accuracy     {ACC:3}                    Courage         {COU:3}
Agility      {AGL:3}                    Technical       {TECH:3}
Endurance    {END:3}                    Energon         {ENERGON:3}
""".strip("\n"), **top_dct))
    
    ## other modes
    for mode_no, mode in enumerate(target.base().getModes()):
        R.append(str.format("[fileheader(MODE {0} - {1})]", mode_no, mode.name))
        R.append(str.format("Size: {0}  -  Velocity: {1}  -  Armor: {2}", 
                            mode.get("SIZE"), mode.get("VEL"), mode.get("ARMOR")))
        
        ## only show differences for alternate modes
        if mode_no > 0:
            io = 0
            altstats_text = ""
            
            for st in ["STR", "FRP", "ACC", "AGL"]:
                alt_stat = mode.get(st)
                if alt_stat != target.base().getMode(0).get(st):
                    text = str.format("[ljust(Mode {0}: {1}, 39)]", CATALOG_MODE_STAT[st]["fullname"], alt_stat)
                    if (io % 2) == 1:
                        altstats_text += text
                    else:
                        altstats_text += "\n" + text
                    
                    io += 1
            
            if altstats_text: R.append(altstats_text.strip("\n"))
        
        R.append(str.format("Abilities: {0}", " ".join(mode.get("ABILITIES"))))
    R.append("[header()]")
    
    pybot.pemit(enactor_dbref, R)
    return True
    
