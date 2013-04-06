"""
Todd Page
4/4/2013

Telnet Interface between PennMUSH and Python
"""

## standard libraries
import telnetlib, ConfigParser, random, re, sqlite3, pickle, time

## custom libraries
import combat, character, objects, startup

## third-party libraries

CONFIG_FILE = "development.cfg"
DB_FILE = "robofist.db"

def main():
    pybot = initPybotFromConfigFile()
    pybot.start()

def onStartup(pybot):
    startup.main(pybot)

class Pybot:
    def __init__(self, host, port, player, password):
        self.host = host
        self.port = port
        self.player = player
        self.password = password
        self.secret_code = None
        self.command_match_rx = re.compile("(PYBOT\d+):(\w+):(\w+)(:.*|)")

        ## telnet vars
        self.ShouldQuit = False
        self.telnet = None
        
        ## combatants
        self.db = sqlite3.connect(DB_FILE)
        self.combatant_dct = {}
        
    def start(self):
        tn = telnetlib.Telnet(self.host, self.port)
        self.telnet = tn
        
        self.sendToTelnet(str.format("ch \"{0}\" {1}", self.player, self.password))
        self.sendToTelnet("p todd=I connected at [time()]")
        self.echo("pybot has connected")
        
        self.secret_code = "PYBOT" + str(random.randint(1, 9999999))
        self.sendToTelnet(str.format("&PYBOT_CODE me={0}", self.secret_code))

        self.listen()
        self.telnet.close()
        self.db.close()

    def sendToTelnet(self, socket_msg):
        self.telnet.write(socket_msg+"\n")
    
    def listen(self):
        while not self.ShouldQuit:		
            text = self.telnet.read_until("\n")
            text = text.strip()
            self.echo(text)
            
            if text == "Pybot/PYBOT_CODE - Set.":
                onStartup(self)
                
            match = self.command_match_rx.search(text)
            if match:
                secret_code, module, cmd, arg_text = match.groups()
                if arg_text:
                    args_lst = arg_text[1:].split(":")
                else:
                    args_lst = []
                    
                ## double check code
                if secret_code != self.secret_code:
                    self.echo("Warning -- Received wrong secret code!")
                    return
                
                self.processCommand(module, cmd, *args_lst)

    def echo(self, text):
        print str.format("->{0}", text)
        
    def processCommand(self, module, cmd_name, *args):
        self.echo(str.format("got command {0}:{1}", module, cmd_name))

        if module == "combat":
            combat.processCommand(self, cmd_name, *args)
            
        elif module == "character":
            character.processCommand(self, cmd_name, *args)
            
        elif module == "":
            if cmd_name == "quit":
                self.ShouldQuit = True

            elif cmd_name == "look":
                self.sendToTelnet("look")
    
            elif cmd_name == "pose":
                pose_cmd = ":" + args[0] + "\n"
                self.sendToTelnet(pose_cmd)
    
            elif cmd_name == "say":
                pose_cmd = "\"" + args[0] + "\n"
                self.sendToTelnet(pose_cmd)
    
            elif cmd_name == "walk":
                walk_cmd = "go " + args[0] + "\n"
                self.sendToTelnet(walk_cmd)
        else:
            self.echo(str.format("Invalid module {0}", module))
            
    
    def getFromMUSH(self, mush_text):
        """
        Get any generic data from the MUSH
        
        Sends any given text to the MUSH and WAITS on the 
        telnet response
        """
        self.sendToTelnet(mush_text)
        resp_text = self.telnet.read_until("\n")
        resp_text = resp_text.strip() ## clear off weird whitespace
        self.echo(resp_text)
        
        return resp_text
    
    def dumpCombatantToMUSH(self, combatant):
        for line in combatant.toMUSH():
            result = self.getFromMUSH(line)
        return True
    
    def dumpCombatantToDB(self, combatant):
        c = self.db.cursor()
        blob = pickle.dumps(combatant)
        c.execute(str.format("DELETE FROM combatants where dbref = '{0}'", combatant.dbref))
        c.execute(str.format("INSERT INTO combatants values (\"{0}\", \"{1}\", {2})",
                             combatant.dbref,
                             blob,
                             time.time()))
        self.db.commit()
        return True
    
    def loadCombatantFromDB(self, dbref):
        c = self.db.cursor()
        c.execute(str.format("SELECT pickledobject from combatants where dbref = '{0}'", dbref))
        blob = c.fetchone()[0]
        combatant = pickle.loads(blob)
        self.combatant_dct[dbref] = combatant
        return combatant
    
def initPybotFromConfigFile():
    config = ConfigParser.ConfigParser()
    config.optionxform = str
    config.read(CONFIG_FILE)
    
    pybot = Pybot(host=config.get("general", "host"),
                  port=config.get("general", "port"),
                  player=config.get("general", "player"),
                  password=config.get("general", "password"))
    
    return pybot
    
class AttributeStorageError(Exception):
    pass

if __name__ == '__main__':
    main()
    
