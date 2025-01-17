import autoit
import keyboard
import os
import pyautogui
import pytesseract
import re
import time
from PIL import Image

#### CONFIGURE THESE BELOW AS INSTRUCTED

# how many life skips are required for the script to rebirth
MIN_SKIPS = 0

# the max amount of time in which a life should take (if it's been longer than this number, it will attempt to rebirth)
MAX_TIME = 120

# whether or not to load each layout
LAYOUTS = [
    # if the value is True, the layout will load when layout cost from below is reached, otherwise it will not load
    True, # layout 1
    False, # layout 2
    False # layout 3
]

# how much each layout costs
COSTS = [
    # the number should be in scientific notation (https://minershaven.fandom.com/wiki/Cash_Suffixes)
    # if the number is incorrect, it may break the script
    0.0, # layout 1
    0.0, # layout 1
    0.0 # layout 1
]

#### CONFIGURE THESE ABOVE AS INSTRUCTED (DONT EDIT BELOW UNLESS U KNOW WHAT UR DOING)

def updateTitle(title: str):
    os.system(f"title {title}")

def output(*msgs):
    print("[DEBUG]", *msgs)

class Haven:
    def __init__(self):
        self.layoutsLoaded = False
        self.lastRebirthTime = time.time()

        # x, y
        self.robloxCoords = [10, 10] # top left of roblox
        self.layoutCoords = [1075, 645] # layout button
        self.settingButtonCoords = [60, 660] # settings buttopn
        self.layoutButtons = [ # each of the individual layout buttons
            [1200, 400], # 1
            [1200, 560], # 2
            [1200, 720] # 3
        ]
        self.rebornConfirmButtons = [ # buttons to confirm you wanna reborn
            [ # 2
                [1060, 510],
                [970, 500, 150, 20]
            ],
            [
                [850, 510],
                [770, 500, 150, 20]
            ]
        ]

        self.confirmPath1 = "images/confirm_1.png"
        self.confirmPath2 = "images/confirm_2.png"

        # x, y, width, height
        self.skipsCoords = [1060, 400, 86, 22] # label of life skips amount
        self.skipsPath = "images/skips.png"

        self.settingsCoords = [710, 235, 190, 35] # title of settings ui
        self.layoutsCoords = [610, 240, 195, 30] # title of layouts ui
        self.settingsPath = "images/settings.png"
        self.layoutsPath = "images/layouts.png"

        self.cashCoords = [640, 15, 175, 30] # amount of cash label
        self.cashPrefix = "@ $"
        self.cashPath = "images/cash.png"

        self.rebornCoords = [940, 490, 220, 35] # reborn price label
        self.rebornPrefix = "[ Reborn $"
        self.rebornPath = "images/reborn.png"
        self.minRebornPrice = 25.0e+18 # 25Qn

        # path to tesseract ocr
        self.tesseractPath = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
        pytesseract.pytesseract.tesseract_cmd = self.tesseractPath
    
    # clicks on a set of coordinates
    def click(self, coords: list):
        x, y = coords
        autoit.mouse_click("left", x, y)

    # gets the center of an area
    def getCenterOf(self, coords: list) -> [int, int]:
        x, y, width, height = coords
        centerX = x + (width / 2)
        centerY = y + (height / 2)
        return [int(centerX), int(centerY)]

    # screenshots a set of coordinates
    def screenshot(self, x: int, y: int, width: int, height: int):
        return pyautogui.screenshot(region=(x, y, width, height))
    
    # opens an image
    def openImage(self, path: str):
        return Image.open(path)

    # uses tesseract to convert an image's text to a string
    def imageToString(self, imageData: str, responseIsNumber: bool, prefix="THE_PREFIX_LOL") -> str:
        string = pytesseract.image_to_string(imageData).replace(prefix, "")

        if responseIsNumber:
            string = string.replace("er", "e+")
            string = string.replace("b", "6")
            string = string.replace("B", "8")
            string = string.replace("z", "2")
            string = string.replace("Z", "2")
            string = string.replace("q", "9")
            string = string.replace("g", "9")
            string = string.replace("o", "0")
            string = string.replace("O", "0")
            string = string.replace("l", "1")
            string = string.replace("i", "1")
            string = string.replace("I", "1")
            string = string.replace("s", "5")
            string = string.replace("S", "5")
            string = string.replace("T", "7")
            string = string.replace("t", "7")

        return string.strip()

    # updates the input screenshot (so we can off read it later)
    def updateScreenshot(self, imagePath: str, coords: list):
        x, y, width, height = coords
        image = self.screenshot(x, y, width, height)
        image.save(imagePath)

    # gets whether or not a certain menu is open
    def isMenuOpen(self, menuPath: str, menuCoords: list, expectedString: str) -> bool:
        self.updateScreenshot(menuPath, menuCoords)
        image = self.openImage(menuPath)
        text = self.imageToString(image, False)
        return expectedString.lower() in text.lower()

    # gets the amount of cash you currently have
    def getCashAmount(self) -> float:
        try:
            self.updateScreenshot(self.cashPath, self.cashCoords)
            image = self.openImage(self.cashPath)
            text = self.imageToString(image, True, self.cashPrefix)
            return float(text)
        except:
            return 0.0
    
    # gets the price to reborn you currently are at
    def getRebornPrice(self) -> float:
        try:
            self.updateScreenshot(self.rebornPath, self.rebornCoords)
            image = self.openImage(self.rebornPath)
            text = self.imageToString(image, True, self.rebornPrefix)
            return float(text)
        except:
            return 0.0
    
    # gets the amount of lifeskips
    def getLifeSkips(self) -> float:
        try:
            self.updateScreenshot(self.skipsPath, self.skipsCoords)
            image = self.openImage(self.skipsPath)
            text = self.imageToString(image, True)
            return float(text[0])
        except:
            return 0.0

    # gets whether or not you're able to rebirth:
    # (if you have atleast 25Qn and if the input rebornPrice is atleast 25Qn)
    # (if the current amount of lives you will skip is less than the minimum amount)
    # (if your input cash amount is atleast the input reborn price)
    def canRebirth(self, cashAmount: float, rebornPrice: float) -> bool:
        lifeSkips = self.getLifeSkips()
        if cashAmount < self.minRebornPrice:
            return False
        elif rebornPrice < self.minRebornPrice:
            return False
        elif lifeSkips < MIN_SKIPS:
            return False
        elif cashAmount < rebornPrice:
            return False
        return True

    # gets the coordinates of the yes confirmation button for rebirthing
    def getYesRebirthButton(self):
        confirm1 = self.rebornConfirmButtons[0]
        confirm2 = self.rebornConfirmButtons[1]
        self.updateScreenshot(self.confirmPath1, confirm1[1])
        self.updateScreenshot(self.confirmPath2, confirm2[1])

        image1 = self.openImage(self.confirmPath1)
        text1 = self.imageToString(image1, False)

        return confirm1[0] if text1.lower() == "yes" else confirm2[0]

    # performs a rebirth
    def doRebirth(self):
        while not self.isMenuOpen(self.settingsPath, self.settingsCoords, "settings"):
            output("REBORN: opening settings menu")
            self.click(self.settingButtonCoords)
            time.sleep(0.25)
        
        while self.isMenuOpen(self.settingsPath, self.settingsCoords, "settings"):
            output("REBORN: clicking reborn button")
            rebornButtonCoords = self.getCenterOf(self.rebornCoords)
            self.click(rebornButtonCoords)
            time.sleep(0.1)

            output("REBORN: clicking yes")
            yesButtonCoords = self.getYesRebirthButton()
            self.click(yesButtonCoords)
            time.sleep(0.1)

            self.lastRebirthTime = time.time()
        
        self.layoutsLoaded = False
        time.sleep(1)

    # loads the layouts
    def loadLayouts(self):        
        while not self.isMenuOpen(self.layoutsPath, self.layoutsCoords, "layouts"):
            if not self.isMenuOpen(self.settingsPath, self.settingsCoords, "settings"):
                output("MAIN: opening settings menu")
                self.click(self.settingButtonCoords)
                time.sleep(0.5) # wait for settings to open

            output("LAYOUTS: opening layouts menu")
            self.click(self.layoutCoords)
            time.sleep(0.25)

        for layout in range(len(LAYOUTS)):
            doLoad = LAYOUTS[layout]
            requiredCash = COSTS[layout]

            while self.getCashAmount() < requiredCash:
                if requiredCash == 0:
                    break
                output(f"LAYOUTS: not enough cash for layout: {layout + 1}")
                time.sleep(0.1)

            if doLoad:
                output(f"LAYOUTS: loading layout: {layout + 1}")

                self.click(self.layoutButtons[layout])
                time.sleep(1)

        self.layoutsLoaded = True

    # initializes the script
    def init(self): 
        while True:
            if keyboard.is_pressed("ctrl") and keyboard.is_pressed("q"):
                output("MAIN: exiting (ctrl + q pressed)")
                exit()
                
            if not self.isMenuOpen(self.settingsPath, self.settingsCoords, "settings"):
                if not self.isMenuOpen(self.layoutsPath, self.layoutsCoords, "layouts") or self.layoutsLoaded:
                    self.click(self.settingButtonCoords)
            
            elapsed = time.time() - self.lastRebirthTime
            cash = self.getCashAmount()
            price = self.getRebornPrice()
            skips = self.getLifeSkips()

            updateTitle(f"MH Bot - CASH: ${cash} - REBORN PRICE: ${price} - SKIPS: {skips} - TIME ELAPSED: {int(elapsed)}")

            if not self.layoutsLoaded:
                self.loadLayouts()

            if (self.canRebirth(cash, price) or (elapsed) >= MAX_TIME) and self.layoutsLoaded:
                self.doRebirth()
            elif not self.canRebirth(cash, price):
                output("REBORN: not enough cash for rebirth")
