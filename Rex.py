import asyncio
import aiojobs
import inspect
import traceback
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.completion import Completer
from prompt_toolkit.completion import Completion
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from fuzzywuzzy import fuzz

def bottom_toolbar():
    return [('bg:green', " All systems nominal")]

async def test():
    print("pokemon go")

async def close():
    exit()

async def nA():
    print("this is a test")
async def nB():
    print("this is b test")
async def nC():
    print("this is c test")
async def arg(arg):
    print("got " + arg)
async def arg2(arg1, arg2):
    print("got " + arg1 + " and " + arg2)
async def arg4(arg1, arg2, arg3, arg4):
    print("got " + arg1 + " and " + arg2 + " and " + arg3 + " and " + arg4)

cmds = {
    "test": test,
    "exit": close,
    "arg": arg,
    "arg2": arg2,
    "arg4": arg4,
    "nested": {
        "a": nA,
        "b": nB,
        "sub": {
            "c": nC
        }
    }
}

class AutoCompleterPlus(Completer):
    def get_completions(self, document, complete_event):
        words = document.text.split(" ")
        pos = cmds
        index = -1
        for i,word in enumerate(words):
            index = i
            if not str(type(pos))=="<class 'function'>" and word in pos:
                pos = pos[word]
            else:
                break
        if not str(type(pos))=="<class 'function'>" :
            comps = []
            for word in pos:
                score = fuzz.partial_ratio(word,words[-1]) + fuzz.ratio(word, words[-1])
                if score > 90 or (len(words)==index+1 and str(document.text).endswith(" ")):
                    comps.append([word, score])
            comps.sort(key = lambda x: x[1], reverse = True)
            for i in range(min(5, len(comps))):
                yield Completion(comps[i][0], start_position=0)
        else:
            args = inspect.getfullargspec(pos)[0]
            if len(args)>len(words)-index-1:
                arg = args[len(words)-index-1]
                yield Completion("<"+str(arg)+">", start_position=0)

async def Rex(cmds=cmds):
    session = PromptSession()
    while True:
        with patch_stdout():
            try:
                inp = await session.prompt_async("[~> ",
                                                 completer = AutoCompleterPlus(),
                                                 auto_suggest = AutoSuggestFromHistory(),
                                                 bottom_toolbar = bottom_toolbar)
            except KeyboardInterrupt:
                return True
        try:
            words = inp.split(" ")
            pos = cmds
            index = 0
            for i,word in enumerate(words):
                if not str(type(pos))=="<class 'function'>" and word in pos:
                    pos = pos[word]
                else:
                    break
                index = i
            if str(type(pos))=="<class 'function'>":
                await pos(*words[index+1:])
            else:
                print("[!] No such command")
        except Exception as e:
            print("[!] An Exception Occured: "+str(e))
            for line in traceback.format_exc().split("\n"):
                print("[ ] "+line)
