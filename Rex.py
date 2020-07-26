import asyncio
import inspect
import traceback
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.completion import Completer
from prompt_toolkit.completion import Completion
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from fuzzywuzzy import fuzz
from shlex import split
import pprint

#                @@@@
#      &@((((((((@@&(@@@
#   &(((((@(((((((@(((((((((((((((
#   ,(((((((%(((((((((@((((((@
#    (((((@(@(((((((((
#       @((((((((((@@
#            @(
#            @(
#            @(                                   @@@@@@@@@@
#            @(                                   @ &
#            @(                                   @
#            @(                           @@      @                &@
#            @(                      /            @ (                    @
#            @(                  %                @ &                        (
#            @(                                   @ @                          (
#            @(                                   @                              @
#            @(           @                                             #          @
#            @(          *          #                                  #*           (
#            @(         @           ###                              ####
#            @(        @            #####                          ##  ##             ,
#            @(                    ##    ##                      ##    ##              @
#            @(       @    ,, , ,, ##       #,##.           ####       ##   ,,,, ,.    @
#            @(        (@  ,, , ,, ###        ## #        # ##        ###   ,,,, ,.  @(@
#            @(   @    ((@ ,, , ,,  ###          #                  (###    ,,,, ,  @((*  @@
#            @( @      (((                                                          (((*
#            @( @   @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#           %(((@   @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#           %(((@    @###################################################################
#           %(((@    @####@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#####
#           %(((@    @ #########@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@########
#                    @         ##########&@@@@@@@@@@@@@@@@@@@@@@@@@@@###########
#                    @                ########%@@@@@@@@@@@@@@@@@#########
#                      @                    ####@@@@@@@@@@@@@@#####
#                *         %                  ###@@@@@@@@@@@@@###                  @
#                /         %  @                ###@@@@@@@@@@@###                @ (
#                @         @                    ###@@@@@@@@@###.             @    ,          @
#                @         @       @            ###@@@@@@@@@###                   @
#                          @         @           ###@@@@@@@###          @         @          @
#                          &           @          #@@,,,,@@##         @           @          @
#                @         @            .        @,@@@@,@@@,,        @            @          @
#                @      @                @     (@@@@#######@@@,@     @                 %     @
#                @   #                   @   @@,@ ###########  @@@                        @  @
#                 @                      @ ,,@    ###########    &,, @                    @@@
#                @@@                     ,,       ###########      *,,                     @@@@
#                                     (,@         ###########         @,,
#                                   *,            ###########           ,,@                  @@
#                (.  @            %,              ###########              @&          #@   @
#                   @     @     #@                ###########                 ,  #@      @
#                       @        @                #@@@@@@@@@#             @@         @
#                           .@          (@/       #@@@@@@@@@#     @@            @@
#                                   (@             @@@@@@@@@           @@      ,
#                                @           #@*   @@@@@@@@@#               @
#                                     @                                @
#                                                @@@@,     @@@


# These are the example functions, that we are going to map to

async def test():
    print("pokemon go")
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
async def question():
    await rex.ask("What is your question? ")


class stdCmds:
    async def close():
      exit()

    async def debug():
      from ptpdb import set_trace
      set_trace()

# This is an example (the default) cmd-dict

defaultCmds = {
    "exit": stdCmds.close,
    "debug": stdCmds.debug,
    "test": test,
    "arg": arg,
    "arg2": arg2,
    "arg4": arg4,
    "question": question,
    "nested": {
        "a": nA,
        "b": nB,
        "sub": {
            "c": nC
        }
    }
}

class _CompletionLookup(Completer):
    def __init__(self, cmds):
        super()
        self.cmds = cmds

    # Dont touch it; it works...
    def get_completions(self, document, complete_event):
        try:
            words = split(document.text)
        except ValueError:
            # Will happen, if the user opened a " or ' and hasn't closed it yet...
            # Were just gonna pretend he did already close it and try again...
            try:
                if document.text.find('"')!=-1:
                    words = split(document.text+'"')
                elif document.text.find("'")!=-1:
                    words = split(document.text+"'")
                else:
                    raise ValueError("Unable to auto-close quotation")
            except ValueError:
                words = document.text.split(" ")
        pos = self.cmds
        index = -1
        # For evere entered 'word'
        for i,word in enumerate(words):
            index = i
            # We traverse one step further down the tree, until we hit a function
            if not str(type(pos))=="<class 'function'>" and word in pos:
                pos = pos[word]
            else:
                break
        # If we are not at a function yet, we are going to generate autocomplete hints
        if not str(type(pos))=="<class 'function'>" :
            comps = []
            for word in pos:
                score = fuzz.partial_ratio(word,words[-1]) + fuzz.ratio(word, words[-1])
                if score > 90 or (len(words)==index+1 and str(document.text).endswith(" ")):
                    comps.append([word, score])
            # Which are sorted by relevance
            comps.sort(key = lambda x: x[1], reverse = True)
            for i in range(min(5, len(comps))):
                yield Completion(comps[i][0], start_position=0)
        else:
            # When we are already at a function, we give hints about expected arguments
            args = inspect.getfullargspec(pos)[0]
            if len(args)>len(words)-index-1:
                arg = args[len(words)-index-1]
                yield Completion("<"+str(arg)+">", start_position=0)

class Rex():
    def __init__(self, cmds=defaultCmds, prompt="[~> ", hasToolbar = True,
                 printExceptions = True, raiseExceptions = False):
        self.cmds = cmds
        self.prompt = prompt
        self.askPrompt = "[?> "
        self.hasToolbar = hasToolbar
        self.session = PromptSession()
        self.toolbar = [("", "")]
        self.printExceptions = printExceptions
        self.raiseExceptions = raiseExceptions

    async def once(self):
        with patch_stdout():
            try:
                inp = await self.session.prompt_async(self.prompt,
                                                 completer = _CompletionLookup(self.cmds),
                                                 auto_suggest = AutoSuggestFromHistory(),
                                                 bottom_toolbar = [None,self._bottom_toolbar][self.hasToolbar])
            except KeyboardInterrupt:
                return False
        try:
            words = split(inp)
            pos = self.cmds
            index = 0
            for i,word in enumerate(words):
                if not str(type(pos))=="<class 'function'>" and word in pos:
                    pos = pos[word]
                else:
                    break
                index = i
            if str(type(pos))=="<class 'function'>":
                if len(inspect.getfullargspec(pos)[0])!=len(words[index+1:]):
                    print("[!] The given commands expects "+str(len(inspect.getfullargspec(pos)[0]))+" arguments, "+
                          "but "+str(len(words[index+1:]))+" were given")
                else:
                    # run the function
                    if inspect.iscoroutinefunction(pos):
                        # function is async
                        ret = await pos(*words[index+1:])
                    else:
                        ret = pos(*words[index+1:])
                    await self.print(ret)
            else:
                print("[!] No such command")
        except Exception as e:
            if self.printExceptions:
                print("[!] An Exception Occured: "+str(e))
                for line in traceback.format_exc().split("\n"):
                    print("[ ] "+line)
            if self.raiseExceptions:
                raise e
        return True

    async def run(self):
        while await self.once():
            pass

    async def print(self, txt):
        if txt==None:
            return
        nice = pprint.pformat(txt)
        for line in nice.split("\n"):
            print("[<] "+line)

    async def ask(self, question):
        print("[?] "+question)
        with patch_stdout():
            try:
                # new prompt instance, so the history / completer dont get mixed up
                inp = await PromptSession().prompt_async(self.askPrompt,
                                                        bottom_toolbar = [None,self._bottom_toolbar][self.hasToolbar])
            except KeyboardInterrupt:
                return False
        return inp

    def runFromSync(self):
        asyncio.run(self.run())

    def _bottom_toolbar(self):
        return self.toolbar

    async def setToolbarMsg(self, msg: str, col: str = "bg:black"):
        self.toolbar = [(col, " "+msg)]

if __name__=="__main__":
    rex = Rex()
    rex.runFromSync()
