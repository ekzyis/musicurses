#!/usr/bin/env python3

import os
import subprocess
import curses
import curses.ascii
from proposals import loadProposals
from filetypes import Filetype
from enum import Enum
#import logging

class Mode(Enum):
    INSERT = "INSERT"
    NORMAL = "NORMAL"
    def __str__(self):
        return str(self.value)

MUSICPATH = '/media/ekzyis/HDD/ekzyis/Musik'
CURSES_ENTER_KEYS = [curses.KEY_ENTER, 10, 13]
CURSES_TYPE_KEYS = [x for x in range(0,256)]
# custom key code definitions
curses.KEY_SDOWN = 336 # SHIFT-DOWN
curses.KEY_SUP = 337 # SHIFT-UP

#logging.basicConfig(filename='/home/ekzyis/musicurses.log', level=logging.DEBUG)

class Musicurses():
    MIN_SELECTION_INDEX = -1
    MAX_SELECTION_INDEX = None
    PROMPT = '> '
    def __init__(self, stdscr):
        self.__stdscr = stdscr
        self.__path = MUSICPATH
        self.__selection = Musicurses.MIN_SELECTION_INDEX
        self.__selectionList = []
        self.__prompt = Musicurses.PROMPT
        self.__cursor = (0,2)
        self.__input = ''
        self.__proposals = []
        self.__mode = Mode.INSERT
        self.__commandInput = ''
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
        self.__style = {
            "SELECTION": curses.color_pair(1),
            Filetype.DIRECTORY: curses.color_pair(2),
            Filetype.AUDIO: curses.color_pair(3),
            Filetype.PLAYLIST: curses.color_pair(3),
            Filetype.OTHER: curses.color_pair(0)
        }
        # need to initialize here since curses needs to be initialized
        # -1 because we want the index
        # additional -1 because we start at -1 (which is pattern input line)
        # additional -1 because last line is reserved for command prompt
        # total: -3
        Musicurses.MAX_SELECTION_INDEX = curses.LINES-3

    def run(self):
        stdscr = self.__stdscr
        stdscr.clear()
        self.__proposals = loadProposals(self.__path, self.__input)
        self.__render()
        while(True):
            self.__handleEvent(stdscr.getch())
            self.__render()

    def __render(self):
        stdscr = self.__stdscr
        stdscr.clear()
        stdscr.addstr(0, 0, self.__prompt + self.__input)
        # Musicurses.MAX_SELECTION_INDEX +1 because we need length
        for (i,p) in enumerate(self.__proposals[0:Musicurses.MAX_SELECTION_INDEX+1]):
            style = curses.A_NORMAL
            if(i == self.__selection or i in self.__selectionList): style = self.__style["SELECTION"]
            else: style = self.__style[p.type()]
            stdscr.addstr(i+1, 0, p.name(), style)
        last = self.__commandInput if self.__commandInput else "-- {} --".format(self.__mode)
        stdscr.addstr(curses.LINES-1, 0, last)
        stdscr.noutrefresh()
        curses.setsyx(self.__cursor[0], self.__cursor[1])
        curses.doupdate()

    def __handleEvent(self, c):
        prev_mode = self.__mode
        self.__handleMode(c)
        # only change input if mode did not change during __handleMode
        if(prev_mode == self.__mode):
            self.__handleInput(c)
        if(c in [curses.KEY_DOWN, curses.KEY_UP, curses.KEY_SDOWN, curses.KEY_SUP]):
            self.__handleArrowNavigation(c)
        elif(c in CURSES_ENTER_KEYS):
            self.__handleEnterPress()
            self.__updateProposals()
        elif(curses.ascii.isprint(c) or c == curses.KEY_BACKSPACE):
            self.__updateProposals()
        self.__updatePrompt()
        self.__updateCursor()

    def __handleMode(self, c):
        if(c == curses.ascii.ESC):
            self.__mode = Mode.NORMAL
        elif(self.__mode == Mode.NORMAL):
            if(c in CURSES_TYPE_KEYS):
                char = chr(c)
                if(self.__commandInput == ''):
                    if(char == 'i'):
                        self.__mode = Mode.INSERT

    def __handleInput(self, c):
        def __inner__handleInput(prev, c):
            if(c in CURSES_ENTER_KEYS):
                return prev
            elif(c == curses.KEY_BACKSPACE):
                return prev[:-1]
            elif(curses.ascii.isprint(c)):
                return prev + chr(c)
            else: return prev
        input = self.__input
        commandInput = self.__commandInput
        if(self.__mode == Mode.INSERT):
            input = __inner__handleInput(input, c)
        elif(self.__mode == Mode.NORMAL):
            if(c in CURSES_TYPE_KEYS or c == curses.KEY_BACKSPACE):
                char = chr(c)
                if(char == ':' and commandInput == ''):
                    commandInput = char
                elif(commandInput):
                    commandInput = __inner__handleInput(commandInput, c)
        self.__input = input
        self.__commandInput = commandInput

    def __handleArrowNavigation(self, c):
        max_proposals_index = len(self.__proposals[0:Musicurses.MAX_SELECTION_INDEX+1])-1
        def __inner__getDownSelection(sel):
            return min([Musicurses.MAX_SELECTION_INDEX, max_proposals_index, sel+1])
        def __inner__getUpSelection(sel):
            return max(Musicurses.MIN_SELECTION_INDEX, sel-1)
        selection = self.__selection
        selectionList = self.__selectionList
        if(c in [curses.KEY_DOWN, curses.KEY_SDOWN]):
            selection = __inner__getDownSelection(selection)
            if(c == curses.KEY_DOWN):
                selectionList = []
            else:
                # User is holding down shift!
                # add previous element if list was empty
                if(not selectionList):
                    selectionList.append(selection-1)
                elif(max(selectionList) >= selection):
                    # always add next element at bottom (don't re-add an already added item when navigating back)
                    selection = max(selectionList)+1
                selectionList.append(selection)
        elif(c in [curses.KEY_UP, curses.KEY_SUP]):
            selection = __inner__getUpSelection(selection)
            if(c == curses.KEY_UP):
                selectionList = []
            else:
                # User is holding down shift!
                # add previous element if list was empty
                if(not selectionList):
                    selectionList.append(selection+1)
                elif(min(selectionList) <= selection):
                    # always add next element at top (don't re-add an already added item when navigating back)
                    selection = min(selectionList)-1
                selectionList.append(selection)
        else:
            raise ValueError("Key code does not belong to an Arrow key!")
        self.__selection = selection
        self.__selectionList = selectionList

    def __resetSelectionList(self):
        self.__selectionList = []

    def __handleEnterPress(self):
        selection = self.__selection
        selectionList = self.__selectionList
        proposals = self.__proposals
        input = self.__input
        commandInput = self.__commandInput
        mode = self.__mode
        if(mode == Mode.NORMAL):
            if(commandInput == ':q'):
                exit(0)
        if(0 <= selection <= Musicurses.MAX_SELECTION_INDEX or len(selectionList) > 1):
            if(len(selectionList) > 1):
                # we selected a list of proposals!
                for s in selectionList:
                    p = proposals[s]
                    if(p.type() in [Filetype.AUDIO,Filetype.PLAYLIST]):
                        self.__play(p.path())
            else:
                selectedItem = proposals[selection]
                if(selectedItem.type() == Filetype.DIRECTORY):
                    self.__changePath(selectedItem.path())
                elif(selectedItem.type() in [Filetype.AUDIO,Filetype.PLAYLIST]):
                    # let's play some music, will we?
                    self.__play(selectedItem.path())
        elif(selection == Musicurses.MIN_SELECTION_INDEX):
            if(mode == Mode.INSERT):
                if(input == '..'):
                    self.__changePath(self.__path + '/..')

    def __changePath(self, path):
        self.__path = os.path.abspath(path)
        self.__input = ''
        self.__selection = Musicurses.MIN_SELECTION_INDEX
        self.__selectionList = []

    def __play(self, path):
        FNULL = open(os.devnull, 'w')
        subprocess.Popen(['xplayer', '--enqueue', path],
            stdout=FNULL, stderr=FNULL,
            preexec_fn=os.setpgrp)

    def __updateProposals(self):
        self.__proposals = loadProposals(self.__path, self.__input)
        if(len(self.__proposals) <= self.__selection):
            self.__selection = len(self.__proposals)-1

    def __updatePrompt(self):
        prompt = self.__prompt
        prompt = "{}{}".format(self.__path.replace(MUSICPATH, ''), Musicurses.PROMPT)
        if(prompt[0] == '/'): prompt = prompt[1:]
        self.__prompt = prompt

    def __updateCursor(self):
        self.__cursor = (0,len(self.__prompt + self.__input))

def main(stdscr):
    inst = Musicurses(stdscr)
    inst.run()

if __name__ == "__main__":
    os.environ.setdefault('ESCDELAY', '25')
    curses.wrapper(main)
