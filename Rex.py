import asyncio
import aiojobs
import inspect
import traceback
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.completion import Completer
from prompt_toolkit.completion import Completion
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from fuzzywuzzy import fuzz

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


# This is an example (the default) cmd-dict

defaultCmds = {
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

class _CompletionLookup(Completer):
    def __init__(self, cmds):
        super()
        self.cmds = cmds

    # Dont touch it; it works...
    def get_completions(self, document, complete_event):
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
                 printExceptions = True, raiseExceptions = False, pipeReturn = False):
        self.cmds = cmds
        self.prompt = prompt
        self.hasToolbar = hasToolbar
        self.session = PromptSession()
        self.toolbar = [("", "")]
        self.printExceptions = printExceptions
        self.raiseExceptions = raiseExceptions
        self.pipeReturn = pipeReturn

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
            words = inp.split(" ")
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
                    ret = await pos(*words[index+1:])
                    if self.pipeReturn:
                        return ret
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
        if self.pipeReturn:
            raise Exception("Cannot 'run', if pipeReturn is set to true")
        while await self.once():
            pass

    def runFromSync(self):
        asyncio.run(self.run())

    def _bottom_toolbar(self):
        return self.toolbar

    async def setToolbarMsg(self, msg: str, col: str = "bg:black"):
        self.toolbar = [(col, " "+msg)]
