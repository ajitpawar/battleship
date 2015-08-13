import os
import sys
import select
import random
import Dialog
import tkSimpleDialog
import tkMessageBox
from collections import Counter
from Tkinter import *


# ################################
#        Functions
# ################################

def showDialogBox(mssg, icon="info", type="ok", default="ok"):
    """Return a pop-up dialog box containing message mssg"""

    return tkMessageBox._show("Battleship", mssg, icon, type, default=default)


def clickOverride():
    """Prevent user from closing window"""

    pass


def exitConfirm():
    """Display pop-up dialog box to confirm game exit"""

    confirm = showDialogBox('Exit the game now?', 'question', 'yesno', 'no')
    if confirm == 'yes':
        raise SystemExit


def askOpponentType():
    """Return user's choice of playing against human or computer"""

    opponentType = Dialog.Dialog(None, {'title': 'Battleship',
        'text': 'Choose your opponent',
        'bitmap': 'question',
        'default': 0,
        'strings': ('Human', 'Computer',)}).num
    return opponentType


def askWinCondition():
    """Return user's choice of style of scoring"""

    winCondition = Dialog.Dialog(None, {'title': 'Battleship',
        'text': 'Choose your win condition',
        'bitmap': 'question',
        'default': 0,
        'strings': ('Win by points', 'Win by moves',)}).num
    return winCondition


# ################################
#        Classes
# ################################

class inputForm(object):
    """Class for user-input form"""

    def __init__(self, root):
        """(inputForm, widget) -> NoneType
        Populate widget with input fields, labels and submit button"""

        self.root = root
        self.usernames = []
        self.shipList = {}     # ships present board
        self.boardsize = 10
        self.opponentType = 0  # default opponent human
        self.winCondition = 0  # default condition "win by points"

        # Generate Part 1 - User details
        self.userValues = []
        Part1 = LabelFrame(root, text=" 1. Player Details: ")
        Part1.grid(row=0, columnspan=7, padx=5, pady=5, ipadx=5, ipady=5)
        Label(Part1, text="Name for P1:").grid(row=0, column=0, padx=5, pady=2)
        tag1 = Entry(Part1)
        tag1.grid(row=0, column=1, columnspan=7, sticky="WE", pady=3)
        Label(Part1, text="Name for P2:").grid(row=1, column=0, padx=5, pady=2)
        tag2 = Entry(Part1)
        tag2.grid(row=1, column=1, columnspan=7, sticky="WE", pady=3)
        self.userValues.extend([tag1, tag2])

        # Generate Part 2 - Ship details
        Part2 = LabelFrame(root, text=" 2. Board Details: ")
        Part2.grid(row=2, columnspan=7, padx=5, pady=5, ipadx=5, ipady=5)
        Label(Part2, text="Size:").grid(row=2, column=0, padx=5, pady=2)
        Label(Part2, text="Number of ships:").grid(row=2, column=1)

        self.shipValues = []
        for i in range(3, 7):
            for j in range(2):
                x = Entry(Part2)
                x.grid(row=i, column=j, columnspan=7, sticky="WE", pady=3)
                self.shipValues.append(x)

        # Generate Part 3 - Board size
        Part3 = LabelFrame(root, text=" 3. Board size: ")
        Part3.grid(row=7, columnspan=7, padx=5, pady=5, ipadx=5, ipady=5)
        Label(Part3, text="Size of board:").grid(row=7, column=0)
        self.tag3 = Entry(Part3)
        self.tag3.grid(row=7, column=1, columnspan=7, sticky="WE", pady=3)

        # Generate Help section
        Help = LabelFrame(root, text=" Help ")
        Help.grid(row=0, column=9, columnspan=2, rowspan=8, padx=5, pady=5)
        mssg1 = "Default values:\n\nName: Player 1\nName: " \
                "Player 2\nShips: 2,3,4,5\nBoard Size: 10x10\n"
        mssg2 = "\n\nWin by points:\n Each hit earns 1 point. " \
                "Each ship\nsunk wins points equal to ship size"
        mssg3 = "\n\nWin by moves:\nWinner is declared by " \
                "calculating\naverage hits per move. The more\n" \
                "your hits, the higher your average"
        Label(Help, text=mssg1 + mssg2 + mssg3).grid(row=0)

        # Submit button
        btn = Button(Part3, text="Submit", command=self.validateForm)
        btn.grid(row=8, column=0, sticky='W', padx=5, pady=2)

    def validateForm(self):
        """(inputForm) -> NoneType
        Validate user input to ensure correct input:
        Size of the board must be greater than 1
        Size of a ship must be atleast 1
        Number of ships must be atleast 1"""

        # Get the two usernames
        for i in range(2):
            if not self.userValues[i].get():
                self.usernames.append('Player %s' % int(i + 1))
            else:
                self.usernames.append(self.userValues[i].get())
        try:
            # Validate board size
            if self.tag3.get():
                if int(self.tag3.get()) < 2:
                    raise ValueError('Error: Size of board \
                    must be greater than 1')
                else:
                    self.boardsize = int(self.tag3.get())

            # Validate size and number of ships
            for m, n in zip(self.shipValues[0::2], self.shipValues[1::2]):
                size = m.get()
                number = n.get()
                if size and int(size) < 1:
                    raise ValueError('Error: Size of ship must \
                    be atleast 1')
                if number and int(number) < 1:
                    raise ValueError('Error: Number of ships must \
                    be atleast 1')
                if size and number:
                    self.shipList[int(size)] = int(number)

            # Default values if user left input blank
            if not self.shipList:
                self.shipList = {2: 1, 3: 1, 4: 1, 5: 1}

        except ValueError as ve:
            showDialogBox(ve.message)
        else:
            self.root.quit()


class Players(object):
    """Class for players of the game"""

    def __init__(self, frame1, frame2, usernames, winCondition):
        """(Players, widget, widget, list of str, int) -> NoneType """

        self.frame1 = frame1
        self.frame2 = frame2
        self.usernames = usernames
        self.winCondition = winCondition
        self.tracker = None
        self.message = {0: None, 1: None}
        self.score = [0, 0]
        self.moves = [[0], [0]]

    def updateWidget(self):
        """(Players) -> NoneType
        Update title of the widget to display current player's turn"""

        if self.frame1.state() == 'normal':
            self.frame2.deiconify()
            self.frame1.withdraw()
        else:
            self.frame2.withdraw()
            self.frame2.update()
            self.frame2.deiconify()
            self.frame1.title("%s's turn" % self.usernames[1])
            self.frame2.title("%s's turn" % self.usernames[0])
            showDialogBox("%s's turn first!" % self.usernames[0])
        self.frame1.update()
        self.frame2.update()

    def switchTurn(self):
        """(Players) -> NoneType
        Switch turns between the two players
        Switch between widgets belonging to the respective players"""

        # Widget for player 1
        if self.frame1.state() == 'normal':
            self.frame2.deiconify()
            self.frame1.withdraw()
            self.frame1.update()
            self.frame2.update()
            if self.message[0]:
                showDialogBox(self.message[0])  # announce
                self.message[0] = None
            game2.canvas.tag_bind('square', '<Button-1>', game2.fire)

        # Widget for player 2
        else:
            self.frame1.deiconify()
            self.frame2.withdraw()
            self.frame1.update()
            self.frame2.update()
            if game2.isComputer == 1:
                self.frame1.after(500)
                game1.computer_fire()
            else:
                if self.message[1]:
                    showDialogBox(self.message[1])  # announce
                    self.message[1] = None
                game1.canvas.tag_bind('square', '<Button-1>', game1.fire)

    def endOfTurn(self, tracker):
        """(Players, dict) -> NoneType
        Check for a winner after each turn and declare him if available
        Calculate player scores and winning margin"""

        # Get status on whether all ships have been sunk
        win = self.checkForWin(tracker)

        if not win:
            if self.frame1.state() == 'normal':
                battleships = game1
            else:
                battleships = game2
            self.frame1.after(500)
            self.switchTurn()
        else:

            # Calculate scores
            if self.winCondition:
                text = 'hits per move'
                for i in range(2):
                    if len(self.moves[i]) == 1:
                        continue
                    total = self.moves[i][0]
                    for n in self.moves[i][1:]:
                        total += n
                    avg = float(len(self.moves[i]) - 1) / total
                    self.score[i] = float('%.2f' % avg)
            else:
                text = 'points'

            # Player with the highest score is the winner
            index = self.score.index(max(self.score))
            winner = self.usernames[index]
            margin = max(self.score) - min(self.score)

            # Prepare scorecard
            mssg0 = "Congratulations, %s wins!" % self.usernames[index]
            mssg1 = "Scorecard:\n\n%s's score: %s  %s\n" \
               "%s's score: %s  %s\n\n" % (self.usernames[0], self.score[0],\
                text, self.usernames[1], self.score[1], text)
            mssg2 = "%s wins by a margin of  %s %s" % (winner, margin, text)

            if self.score[0] == self.score[1]:
                mssg0 = "It's a draw!"
                mssg2 = ""

            # Reveal ship positions for both players
            game1.canvas.tag_raise('ship', 'square')
            game2.canvas.tag_raise('ship', 'square')
            game1.canvas.tag_raise('text')
            game2.canvas.tag_raise('text')

            # Display scorecard
            showDialogBox(mssg0)
            self.frame1.deiconify()
            self.frame2.deiconify()
            showDialogBox(mssg1 + mssg2)
            showDialogBox("End of game!\n\n" \
            "Here are the board setups for both players")

    def checkForWin(self, tracker):
        """(Players, dict) -> int
        Return True if all ships have been sunk, False otherwise"""

        # Check damage levels for all ships in the tracker
        # 0 = Fully damaged (sunk), Non-zero otherwise
        for i in tracker.values():
            if i != 0:
                break
        else:
            return True
        return False


class Board(object):
    """Class representing board used in the game"""

    def __init__(self, frame, players, shipList, boardsize, opponent, number):
        """(Board, widget, Players, dict, int, int, int) -> NoneType """

        self.myframe = frame
        self.players = players
        self.shipList = shipList
        self.boardsize = boardsize
        self.isComputer = opponent  # 0 human, 1 computer
        self.playerNumber = number
        self.shipID = 101  # Every ship is identified by an id
        self.exitstatus = 0

        # List representing every attacked location on the board
        # 0 = not attacked yet, 1 = attacked
        self.hit = [0 for i in range(pow(self.boardsize, 2))]

        # Keeps track of ships alongwith their original sizes
        # As ships are hit, their size in tracker will be decremented
        # Size of zero represents sunk ship
        # Example: {101:5, 102:0, 103:7, 104:1, 105:0}
        # So, ships with id "102" and "105" have been sunk
        self.tracker = {}

        # Create canvas
        self.canvas = Canvas(\
            self.myframe, background='white', highlightthickness=0,\
            width=pow(self.boardsize, 2) + 140,\
            height=pow(self.boardsize, 2) + 160)
        self.canvas.pack(fill=BOTH, expand=TRUE)

        # Draw board on canvas
        self.squares = []
        for y in xrange(self.boardsize):
            for x in xrange(self.boardsize):
                self.squares.append(self.canvas.create_rectangle(\
                x * 20 + 20, y * 20 + 40, x * 20 + 40, y * 20 + 60, \
                fill='#0055ff', width=2))
                self.canvas.addtag_withtag('square', self.squares[-1])

        self.placeShips()

    def placeShips(self):
        """(Board) -> NoneType
        Randomly place each ship on the board in 20 attempts
        Announce failures in placing ships to the user"""

        self.ships = []  # Canvas co-ordinates for the ships
        self.shipText = []  # Text to be displayed besides each ship
        self.failedAttempts = []
        self.names = {2: 'BOAT', 3: 'SUB', 4: 'CRUISER', 5: 'CARRIER'}

        items = self.shipList.items()
        for k, v in items:
            for i in range(v):   # for every ship v of size k
                attempts = 20
                success = False
                while not success and attempts > 0:
                    success = True
                    n = random.randrange(0, len(self.hit))
                    shipRotation = random.randrange(0, 2)
                    attempts -= 1

                    # Check if ship fits horizontally
                    if shipRotation != 0:
                        for j in range(n, n + k):
                            if (j >= len(self.hit)) or (j % self.boardsize \
                                < n % self.boardsize) or (self.hit[j] != 0):
                                success = False
                                break
                    # Check if ship fits vertically
                    else:
                        for j in range(n, n + k * self.boardsize, \
                                       self.boardsize):
                            if (j >= len(self.hit)) or (self.hit[j] != 0):
                                success = False
                                break

                # Keep track of ships that failed to be placed
                if attempts == 0:
                    self.failedAttempts.append(k)
                    continue

                # Ships of custom sizes above 5 are named "BATTLESHIP"
                name = 'BATTLESHIP'
                if k in self.names:
                    name = self.names[k]

                x = n % self.boardsize * 20 + 20
                y = (n / self.boardsize) * 20 + 40

                # Place ship horizontally
                if shipRotation != 0:
                    for i in range(n, n + k):
                        self.hit[i] = self.shipID
                    self.ships.append(self.canvas.create_rectangle(\
                    x, y + 5, x + k * 20, y + 15, fill='orange', width=1))
                    self.shipText.append(self.canvas.create_text(\
                    x + 20, y, text=name, font='Courier 6', fill='yellow'))

                # Place ship vertically
                else:
                    for i in range(n, n + k * self.boardsize, self.boardsize):
                        self.hit[i] = self.shipID
                    self.ships.append(self.canvas.create_rectangle(\
                    x + 5, y, x + 15, y + k * 20, fill='orange', width=1))
                    cname = ""
                    for ch in name:
                        cname += ch + '\n'
                    self.shipText.append(self.canvas.create_text(\
                    x, y + 20, text=cname, font='Courier 6', fill='yellow'))

                # Tag every placed ship with "tagXXX" where XXX is shipID
                # Will be used to identify which ship was bombed
                self.canvas.addtag_withtag('tag%s' % \
                                      self.shipID, self.ships[-1])
                self.canvas.addtag_withtag('ship', self.ships[-1])
                self.tracker[self.shipID] = k
                self.shipID += 1

        # Announce any failures in placing ships
        # Game will exit after user is notified of this failure
        if self.failedAttempts:
            mssg = "Oops, we failed to fit the " \
                    "following ships on this board:\n\n"
            failCount = Counter(self.failedAttempts)
            for m, n in failCount.items():
                mssg += '%s  ships of size %s\n' % (n, m)
            showDialogBox(mssg + "\nUnfortunately, we " \
                    "cannot proceed with the game!")
            showDialogBox("Goodbye!")
            self.exitstatus = 1
            return

        # 'tracker' will be modified throughout the game, so keep a copy
        self.counter_copy = self.tracker.copy()
        self.players.tracker = self.tracker

        for i in self.ships:
            self.canvas.addtag_withtag('ship', i)
        for i in self.shipText:
            self.canvas.addtag_withtag('text', i)
        for i in range(self.shipID - 100):
            self.ships.append(None)
            self.shipText.append(None)

        if self.isComputer == 1:
            self.canvas.tag_lower('ship')
            self.canvas.tag_lower('text')
            self.canvas.tag_bind('square', '<Button-1>', self.fire)
        else:
            self.clickDone = Button(self.myframe, text='Done',\
                                    command=self.clickDone)
            self.clickDone.place(x=1, y=1)

    def clickDone(self):
        """(Board) -> NoneType
        Proceed with the game once user is done placing ships"""

        # Hide done button
        self.clickDone.place_forget()

        # Hide all ships and their names
        self.canvas.tag_lower('ship')
        self.canvas.tag_lower('text')
        self.canvas.tag_bind('square', '<Button-1>', self.fire)
        self.players.updateWidget()

        # If opponent is computer, unbind left-click trigger
        # This prevents user from left-clicking
        if game2.isComputer == 1:
            self.canvas.tag_unbind('square', '<Button-1>')
            self.players.frame1.title("%s's turn" % self.players.usernames[1])
            self.players.frame2.title("%s's turn" % self.players.usernames[0])
            showDialogBox("%s's turn first" % self.players.usernames[0])

    def fire(self, event):
        """(Board, event) -> NoneType
        Bomb the location that user clicked on"""

        # Unbind left-click to prevent user from bombing
        # multiple locations at once
        self.canvas.tag_unbind('square', '<Button-1>')
        self.canvas.update()

        # Get co-ordinates of the square that was clicked
        n = self.canvas.find_closest(event.x, event.y)
        n = int(n[0]) - 1
        try:
            coords = self.canvas.coords(self.squares[n])
            coords[0], coords[1], coords[2], coords[3]
            if self.hit[n] == 5:  # Location already bombed
                raise IndexError
        except IndexError:
            self.canvas.tag_bind('square', '<Button-1>', self.fire)
        else:
            self.bomb(n)

    def computer_fire(self):
        """(Board, mouse event) -> NoneType
        Randomly fire on a new location"""

        # Check tracker to see if previous attempt was a hit
        # If yes, continue to bomb rest of the ship first
        for shipID, size in self.tracker.items():
            if (size != 0) and (self.counter_copy[shipID] != size):
                for n in range(len(self.hit)):
                    if self.hit[n] == shipID:
                        self.bomb(n)
                        return

        # Else, randomly fire on a new location
        n = random.randrange(0, len(self.hit))
        while self.hit[n] == 5:
            n = random.randrange(0, len(self.hit))
        self.bomb(n)

    def bomb(self, index):
        """(Board, int) -> NoneType
        Bomb the square on the board at location index
        Display visually if the location is a hit, sink or a miss"""

        coords = self.canvas.coords(self.squares[index])
        x, y = coords[0] + 10, coords[1] + 10
        tag = self.hit[index]

        # Count moves for player (used for scoring)
        if self.players.winCondition == 1:
            self.players.moves[self.playerNumber][0] += 1

        # Hit
        if tag != 0:
            self.tracker[tag] -= 1

            # Count moves for player (used in scoring)
            if self.players.winCondition == 1:
                self.players.moves[self.playerNumber].append(\
                    self.players.moves[self.playerNumber][0])
                self.players.moves[self.playerNumber][0] = 0

            # Ship was sunk
            if self.tracker[tag] == 0:
                text = []
                tagname = 'tag%s' % tag

                # Bonus points equal to the size of ship
                # awarded for sinking entire ship
                if self.players.winCondition == 0:
                    self.players.score[self.playerNumber] += \
                        self.counter_copy[tag]

                # Show bombed location with black & orange flashing bar
                for i in range(5):
                    text.append(self.canvas.create_text(\
                                      x, y, text='O', fill='red'))
                    self.canvas.addtag_withtag('text', text[-1])
                self.canvas.tag_raise(tagname, 'square')
                for i in range(3):  # Flashing bar
                    self.canvas.itemconfig(tagname, {'fill': 'black'})
                    self.canvas.update()
                    self.myframe.after(100)
                    self.canvas.itemconfig(tagname, {'fill': 'orange'})
                    self.canvas.update()
                    self.myframe.after(100)

                self.hit[index] = 5
                self.players.message[not self.playerNumber] = \
                    '%s,\nYour ship of size %s was sunk by enemy' % \
                    (self.players.usernames[not self.playerNumber], \
                     self.counter_copy[tag])
                self.players.endOfTurn(self.tracker)
                return

            # Hit, but not sunk. Player gets only 1 point
            if self.players.winCondition == 0:
                self.players.score[self.playerNumber] += 1

            # Show hit location with flashing black & red circle
            text = []
            for i in range(3):
                del text[:]
                for i in range(5):  # flash black circle
                    text.append(self.canvas.create_text(\
                        x, y, text='O', fill='black'))
                    self.canvas.addtag_withtag('text', text[-1])
                self.canvas.update()
                self.myframe.after(100)
                del text[:]
                for i in range(5):  # flash red circle
                    text.append(self.canvas.create_text(\
                        x, y, text='O', fill='red'))
                    self.canvas.addtag_withtag('text', text[-1])
                self.canvas.update()
                self.myframe.after(100)

        # Complete miss. Draw 'X'
        else:
            for i in range(5):
                text = self.canvas.create_text(x, y, text='X', fill='yellow')
                self.canvas.addtag_withtag('text', text)
            self.canvas.update()
            self.myframe.after(250)
        self.hit[index] = 5
        self.players.endOfTurn(self.tracker)


# ################################
#       Main
# ################################

if __name__ == '__main__':

    global game1, game2

    # Main display frame
    root = Tk()
    root.title('Battleship')
    root.withdraw()
    root.protocol('WM_DELETE_WINDOW', clickOverride)

    showDialogBox("Battleship Game!\n\nCreated by:\nAjit Pawar\n(c) 2012")

    # Display user-input Form
    root1 = Tk()
    form = inputForm(root1)
    root1.protocol('WM_DELETE_WINDOW', clickOverride)
    root1.mainloop()
    root1.withdraw()

    # Retrieve user-supplied values from Form
    boardsize = form.boardsize
    usernames = form.usernames
    shipList = form.shipList
    opponent = askOpponentType()
    winCondition = askWinCondition()
    if opponent == 1:
        usernames[0] = 'Player'
        usernames[1] = 'Computer'

    showDialogBox("Let's Play Battleship!\n\n%s\n   " \
    "vs\n%s\n\nGood Luck!" % (usernames[0], usernames[1]))

    # Create two widgets, one for each player
    top = Menu(root)
    frame1 = Toplevel(root, menu=top)
    frame2 = Toplevel(root, menu=top)
    frame2.withdraw()

    frame1.title("%s's setup" % usernames[0])
    frame2.title("%s's setup" % usernames[1])
    frame1.protocol('WM_DELETE_WINDOW', exitConfirm)
    frame2.protocol('WM_DELETE_WINDOW', exitConfirm)
    frame1.resizable(width=0, height=0)
    frame2.resizable(width=0, height=0)

    # Create objects
    players = Players(frame1, frame2, usernames, winCondition)
    game1 = Board(frame1, players, shipList, boardsize, 0, 1)
    game2 = Board(frame2, players, shipList, boardsize, opponent, 0)

    root.mainloop()
    root.quit()
    raise SystemExit
