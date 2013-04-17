"""
Todd Page
4/16/2013

Handle MUSH interface to combat/char system
"""

## standard libraries
import re

from plugins import display
    
patterns = [
    (re.compile(pattern), fn) for pattern, fn in [
        ("profile$", display.profile),
        ("profile (#\d+)$", display.profile)
        ]
    ]

def processInput(pybot, enactor, from_loc, input_text):
    pybot.echo("dispatcher: " + input_text)
    for rx, fn in patterns:
        match = rx.search(input_text)
        if match:
            args = match.groups()
            return {
                "function": fn, 
                "args": args
            }
        
    pybot.pemit(enactor, "Hrm... nope.")
    return {}