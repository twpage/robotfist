"""
Todd Page
4/4/2013

Telnet Interface between PennMUSH and Python
"""

## standard libraries
import telnetlib, ConfigParser, random, re, sqlite3, pickle, time, os, sys, imp#, inspect

## custom libraries
import objects, startup
from errors import CombatantDoesNotExist

## third-party libraries

CONFIG_FILE = "development.cfg"
DB_FILE = "development.db"

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
        self.command_match_rx = re.compile("(PYBOT\d+):(#\d+):(#\d+):(.*)$")

        ## telnet vars
        self.ShouldQuit = False
        self.telnet = None
        
        ## Modules
        self.modules_dir = os.path.join(os.getcwd(), "plugins")
        self.plugin_scan_dct = {}
        self.plugin_dct = {}
        self.scanModules()        
        
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

    def scanModules(self):
        for filename in os.listdir(self.modules_dir):
            if not filename.endswith(".py"): continue
            #if filename == "base.py": continue
            
            mod_name, ext = os.path.splitext(filename)
            mod_file = os.path.join(self.modules_dir, filename)
            
            modified = os.stat(mod_file).st_mtime
            
            stored_modified = self.plugin_scan_dct.get(filename, 0)
            
            if modified > stored_modified:
                self.echo(str.format("importing module {0}", filename))
                module = imp.load_source(mod_name, mod_file)
                self.plugin_scan_dct[filename] = modified
                self.plugin_dct[mod_name] = module    
    
    def sendToTelnet(self, socket_msg):
        self.telnet.write(socket_msg+"\n")
    
    def listen(self):
        last_command_t = time.time()
        
        while not self.ShouldQuit:
            text = self.telnet.read_until("\n")
            text = text.strip()
            self.echo(text)
            
            if text == "Pybot/PYBOT_CODE - Set.":
                onStartup(self)
                
            if (time.time() - last_command_t) > 5:
                self.scanModules()
            
            match = self.command_match_rx.search(text)
            if match:
                secret_code, enactor, from_loc, input_str = match.groups()
                
                #if input_str.find("/") != -1:
                    ### slash, break out module and command
                    #module_name, cmd_text = input_str.split("/")                    
                #else:
                    ### no slash, assume default 'cmd' module
                    #module_name = "cmd"
                    #cmd_text = input_str
                    
                #input_lst = cmd_text.split(" ")
                #cmd_name = input_lst[0]
                #args_lst = input_lst[1:]
                    
                ## double check code
                if secret_code != self.secret_code:
                    self.echo("Warning -- Received wrong secret code!")
                    return
                
                self.processCommand(enactor, from_loc, input_str)
                last_command_t = time.time()                

    def echo(self, text):
        print str.format("->{0}", text)
        
    def processCommand(self, enactor, from_loc, input_str):
        self.echo(str.format("got input {0}", input_str))
        
        dispatcher = self.plugin_dct["dispatcher"]
        result = dispatcher.processInput(self, enactor, from_loc, input_str)
        
        if not result:
            self.pemit(enactor, "Hrmm... nope.")
        else:
            fn = result["function"]
            args = result["args"]
            
            try:
                fn(self, enactor, from_loc, *args)
            except Exception as ex:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                err_msg = str.format("RF: Code error in {0}.{1}: '{2}'", fn.__module__, fn.func_name, str(ex))
                err_msg += str.format(" {0} {1}:{2}", str(exc_type).split(".")[1][:-2], fname, exc_tb.tb_lineno)
                self.echo(err_msg)
                self.pemit(enactor, err_msg)
            
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
    
    #def dumpCombatantToMUSH(self, combatant):
        #for line in combatant.toMUSH():
            #result = self.getFromMUSH(line)
        #return True
    
    def saveCombatant(self, combatant):
        c = self.db.cursor()
        blob = pickle.dumps(combatant, 0)
        c.execute(str.format("DELETE FROM combatants where dbref = '{0}'", combatant.dbref))
        exec_str = str.format("INSERT INTO combatants values ('{0}', \"{1}\", {2})",
                             combatant.dbref,
                             blob,
                             time.time())
        c.execute(exec_str)
        self.db.commit()
        return True
    
    def loadCombatant(self, dbref):
        c = self.db.cursor()
        c.execute(str.format("SELECT pickledobject from combatants where dbref = '{0}'", dbref))
        data = c.fetchone()
        if data == None:
            raise CombatantDoesNotExist(dbref)
        else:
            blob = data[0]
        
        combatant = pickle.loads(str(blob))
        #self.combatant_dct[dbref] = combatant
        return combatant
    
    def pemit(self, target_dbref, response):
        return self.sendToMUSH("pemit", target_dbref, response)
    
    def remit(self, target_dbref, response):
        return self.sendToMUSH("remit", target_dbref, response)

    def oemit(self, target_dbref, response):
        return self.sendToMUSH("oemit", target_dbref, response)

    def sendToMUSH(self, transmit, target_dbref, response):
        """
        Use @pemit/remit to send a response to a given target
        """
        if type(response) == list:
            response_text = "\n".join(response)
            response_text.strip("\n")
        else:
            response_text = str(response)
            
        response_text = response_text.replace("\n", "%r")
        response_text = response_text.replace(" ", "%b")
        self.sendToTelnet(str.format("@{0} {1}={2}", transmit, target_dbref, response_text))
        return True
    
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
    
