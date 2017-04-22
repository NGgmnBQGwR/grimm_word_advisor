#encoding: utf-8

import time
import string
import itertools
import base64
import Tkinter
from xml.dom import minidom

import cv2
import numpy
from PIL import ImageGrab, ImageTk, Image

import word_finder
import utils
import keyboard


WORD_LIST_FILENAME = 'words.txt'
SPRITESHEET_DATA_XML = 'data/data2.xml'
SPRITESHEET_DATA_IMAGE = 'data/sheet2.png'
SCREENSHOT_HOTKEY_BUTTON = 'home'


class LetterQuestSolver(object):
    def __init__(self):
        self.word_finder = word_finder.BruteForceWordFinder(words=WORD_LIST_FILENAME)
        self.spritesheet_data = utils.load_spritesheet_data(SPRITESHEET_DATA_XML, SPRITESHEET_DATA_IMAGE)
        self.hotkey_handler = None
        self.pil_screenshot = None
        self.cv2_cropped_bw_letters = None
        self.resized_pil_screenshot = None

        # Tkinter-related objects
        self.tk_root = None
        self.tk_screenshot = None
        self.tk_screenshot_label = None
        self.tk_letters_image = None
        self.tk_letters_label = None
        self.hotkey_button = None
        self.letters_box = None
        self.words_box_left = None
        self.words_box_right = None

    def get_letters_from_grimmscreenshot(self, image, spritesheet_data):
        pil_cv2_image = numpy.array((image), dtype='uint8')[:, :, ::-1].copy()
        cv2_image_cropped = utils.crop(pil_cv2_image, utils.CropType.LETTERS_FROM_1080P)

        cropped_grey = cv2.cvtColor(cv2_image_cropped, cv2.COLOR_BGR2GRAY)
        cropped_bw = cv2.threshold(cropped_grey, 80, 255, cv2.THRESH_BINARY_INV)[1]

        self.cv2_cropped_bw_letters = cropped_bw
        self.refresh_letters_label()

        bounding_boxes = utils.find_bounding_boxes(cropped_bw)
        filtered_bounding_boxes = utils.filter_bounding_boxes(bounding_boxes)
        if len(filtered_bounding_boxes) != 15:
            # raise AssertionError('Unable to find 15 letters in screenshot. Found {}.'.format(len(filtered_bounding_boxes)))
            print 'WARNING: Unable to find 15 letters in screenshot. Found {}.'.format(len(filtered_bounding_boxes))
        screenshot_image_letters = utils.get_resized_letters_from_boxes(cropped_bw, filtered_bounding_boxes)

        recognized_letters = []
        for i in screenshot_image_letters:
            best_match = utils.find_best_match(i, spritesheet_data)
            recognized_letters.append(best_match)

        return recognized_letters

    def recognize_screenshot(self):
        letters = self.get_letters_from_grimmscreenshot(self.pil_screenshot, self.spritesheet_data)
        self.update_letters_box(letters)
        result = self.word_finder.find_words(letters, 5, 5)
        self.update_words_box(result)

    def take_screenshot(self, timeout=0.0):
        if timeout:
            time.sleep(timeout)
        self.pil_screenshot = ImageGrab.grab()
        self.refresh_screenshot_label()
        self.recognize_screenshot()

    def refresh_screenshot_label(self):
        self.resized_pil_screenshot = self.pil_screenshot.resize((640, 360))
        self.tk_screenshot = ImageTk.PhotoImage(self.resized_pil_screenshot)
        self.tk_screenshot_label.configure(image = self.tk_screenshot)

    def refresh_letters_label(self):
        self.tk_letters_image = Image.fromarray(self.cv2_cropped_bw_letters).resize((320, 180))
        self.tk_letters_image = ImageTk.PhotoImage(self.tk_letters_image)
        self.tk_letters_label.configure(image = self.tk_letters_image)

    def toggle_screenshot_hotkey(self):
        if self.hotkey_handler is None:
            self.hotkey_handler = keyboard.register_hotkey(SCREENSHOT_HOTKEY_BUTTON, self.take_screenshot)
            self.hotkey_button.config(relief="sunken")
        else:
            keyboard.unhook(self.hotkey_handler)
            self.hotkey_handler = None
            self.hotkey_button.config(relief="raised")

    def update_words_box(self, words):
        self.words_box_left.config(state=Tkinter.NORMAL)
        self.words_box_left.delete(1.0, Tkinter.END)
        self.words_box_left.insert(Tkinter.INSERT, '\n'.join(words[0]))
        self.words_box_left.config(state=Tkinter.DISABLED)

        self.words_box_right.config(state=Tkinter.NORMAL)
        self.words_box_right.delete(1.0, Tkinter.END)
        self.words_box_right.insert(Tkinter.INSERT, '\n'.join(words[1]))
        self.words_box_right.config(state=Tkinter.DISABLED)

    def update_letters_box(self, new_letters):
        if isinstance(new_letters, str):
            pass
        elif isinstance(new_letters, list):
            st = []
            for index, nl in enumerate(new_letters):
                if index % 5 == 0 and index > 0:
                    st.append('\n')
                st.append(nl+' ')
            new_letters = ''.join(st)
        else:
            raise ValueError("Wrong 'new_letters' argument '{}'".format(new_letters))
        self.letters_box.config(state=Tkinter.NORMAL)
        self.letters_box.delete(1.0, Tkinter.END)
        self.letters_box.insert(Tkinter.INSERT, new_letters)
        self.letters_box.config(state=Tkinter.DISABLED)

    def stop(self):
        self.tk_root.destroy()

    def start(self):
        self.tk_root = Tkinter.Tk()
        # row with screenshot
        self.tk_root.grid_rowconfigure(0, weight=3)
        # row with captured letters in image and text form
        self.tk_root.grid_rowconfigure(1, weight=1)
        # row with words suggestions and buttons
        self.tk_root.grid_rowconfigure(2, weight=1)

        self.tk_root.wm_title("Letter Quest Helper")

        self.tk_screenshot_label = Tkinter.Label(self.tk_root)
        self.tk_screenshot_label.grid(row=0, columnspan=3)

        self.tk_letters_label = Tkinter.Label(self.tk_root)
        self.tk_letters_label.grid(row=1, column=0, columnspan=2)

        self.letters_box = Tkinter.Text(self.tk_root, height=3,width=10, font=('Source Code Pro Medium', 12))
        self.letters_box.grid(row=1, column=2)
        self.letters_box.insert(Tkinter.INSERT, 'a b c d e\n1 2 3 4 5\nq w e r t')
        self.letters_box.config(state=Tkinter.DISABLED)

        self.words_box_left = Tkinter.Text(self.tk_root, height=5,width=40, font=('Source Code Pro Medium', 18))
        self.words_box_left.grid(row=2, column=0)
        self.words_box_left.config(state=Tkinter.DISABLED)

        self.words_box_right = Tkinter.Text(self.tk_root, height=5,width=40, font=('Source Code Pro Medium', 18))
        self.words_box_right.grid(row=2, column=1)
        self.words_box_right.config(state=Tkinter.DISABLED)

        self.hotkey_button = Tkinter.Button(text="Enable hotkey", width=12, relief="raised", command=self.toggle_screenshot_hotkey)
        self.hotkey_button.grid(row=2, column=2)

        self.tk_root.protocol("WM_DELETE_WINDOW", self.stop)
        self.tk_root.mainloop()

def main():
    LetterQuestSolver().start()

if __name__ == '__main__':
    main()
