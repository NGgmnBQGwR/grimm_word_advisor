# encoding: utf-8

from xml.dom import minidom

import cv2
import numpy


COMPARISON_MATRIX_SIZE = 5


class CropType(object):
    ALL = [[1]]
    LOWER_HALF = [[0],
                  [1]]
    MIDDLE_HALF = [[0,1,0],
                   [0,1,0]]
    RIGHT_HALF = [[0,1],
                  [0,1],
                  [0,1],]
    LOWER_RIGHT_CORNER = [[0,0],
                          [0,1]]
    LETTERS_FROM_1080P = [
        [0,0,0],
        [0,0,0],
        [0,0,0],
        [0,1,0],
        [0,1,0]
    ]


def crop(image, crop_matrix):
    height, width, shape = image.shape

    rows = len(crop_matrix)
    if rows == 0:
        return image
    
    cols = len(crop_matrix[0])
    if cols == 0:
        return image

    row_start = None
    row_end = None
    prev_row = None
    for row_index, row in enumerate(crop_matrix):
        if any(row):
            prev_row = True
            if row_start is None:
                row_start = row_index
        elif prev_row:
            if row_end is None:
                row_end = row_index

    if row_start is None:
        return image

    if row_end is None:
        row_end = rows

    col_start = None
    col_end = None
    for row in crop_matrix:
        prev_elem = None
        for col_index, elem in enumerate(row):
            if elem == 1:
                prev_elem = 1
                if col_start is None:
                    col_start = col_index
            elif elem == 0 and prev_elem == 1:
                if col_end is None:
                    col_end = col_index

    if col_start is None:
        return image

    if col_end is None:
        col_end = cols

    row_increment = int(round(height / float(rows)))
    col_increment = int(round(width / float(cols)))
    
    height_from = (row_increment * row_start)
    height_to = (row_increment * row_end)
    
    width_from = (col_increment * col_start)
    width_to = (col_increment * col_end)
    return image[height_from : height_to, width_from : width_to]


def overlap(rect1, rect2):
    l1, r1 = rect1
    l2, r2 = rect2
    left1 = min(l1[0], r1[0])
    left2 = min(l2[0], r2[0])
    right1 = max(l1[0], r1[0])
    right2 = max(l2[0], r2[0])
    bottom1 = min(l1[1], r1[1])
    bottom2 = min(l2[1], r2[1])
    top1 = max(l1[1], r1[1])
    top2 = max(l2[1], r2[1])
    
    if left1 > right2 or right1 < left2:
        return False
    if top1 < bottom2 or bottom1 > top2:
        return False
    return True


def find_bounding_boxes(img):
    bounding_boxes = []
    # ищем все контуры на изображении
    temp_image, contours, hierarchy = cv2.findContours(img.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for x in xrange(len(contours)):
        area = cv2.contourArea(contours[x])
        # буквы находятся в контурах с такой площадью
        # более правильного способа отфильтровывать мусор не нашёл
        if area > 5000 or area < 300:
            continue
        # находим минимальный прямоугольник, содержащий контур
        bx,by,bw,bh = cv2.boundingRect(contours[x])
        bounding_boxes.append( ((bx,by), (bx+bw,by+bh)) )

    return bounding_boxes


def resize_letter(letter, size=COMPARISON_MATRIX_SIZE):
    resized_letter = cv2.resize(letter, (size, size))
    resized_letter = cv2.threshold(resized_letter, 128, 255, cv2.THRESH_BINARY)[1]
    return resized_letter


def load_spritesheet_data(xml_filepath, png_filepath):
    sheet_xml_data = minidom.parse(xml_filepath)
    sheet_image = cv2.imread(png_filepath)

    sheet_letters = {}

    for subtexture in sheet_xml_data.getElementsByTagName('SubTexture'):
        if subtexture.attributes['name'].value.startswith('letter_00'):
            letter = chr(int(subtexture.attributes['name'].value.split('_')[-1])+64)  # ord('A')-1 (index starts from 1)
            if letter in sheet_letters:
                raise AssertionError('Letter {} is already in the dict.'.format(letter))
            x = int(subtexture.attributes['x'].value)
            y = int(subtexture.attributes['y'].value)
            w = int(subtexture.attributes['width'].value)
            h = int(subtexture.attributes['height'].value)
            letter_image = cv2.threshold(cv2.split(sheet_image[y:y+h, x:x+w])[0], 20, 255, cv2.THRESH_BINARY)[1]
            sheet_letters[letter] = resize_letter(letter_image)

    if len(sheet_letters.keys()) != 26:
        raise AssertionError('Failed to load all 26 letters from "{}"/"{}" datasheet'.format(xml_filepath, png_filepath))
    
    return sheet_letters


def filter_bounding_boxes(boxes):
    # сортируем все найденные прямоугольники по размеру
    boxes.sort(key = lambda x: (x[1][0] - x[0][0]) + (x[1][1] - x[0][1]), reverse=True)
    # так как они отсортированы по размеру, то проходим по списку и не добавляем пересекающиеся прямоугольники
    # таким образом у нас получается список непересекающихся прямугольников, содержащих контуры
    filtered_bounding_boxes = []
    for box in boxes:
        if any([overlap(box, x) for x in filtered_bounding_boxes]):
            continue
        filtered_bounding_boxes.append(box)
    # сортируем прямоугольники, чтобы они соответствовали рядам и колонкам на оригинальном изображении
    filtered_bounding_boxes.sort(key = lambda x: (x[0][1]/60, x[0][0]))
    return filtered_bounding_boxes

def get_letters_from_boxes(cropped_bw, boxes):
    letters = []
    for box in filtered_bounding_boxes:
        letter = cropped_bw[box[0][1]:box[1][1], box[0][0]:box[1][0]]
        letters.append(letter)
    return letters


def get_resized_letters_from_boxes(cropped_bw, boxes):
    letters = []
    for box in boxes:
        letter = cropped_bw[box[0][1]:box[1][1], box[0][0]:box[1][0]]
        letter = resize_letter(letter)
        letters.append(letter)
    return letters

def compare_images(img1, img2):
    return numpy.sum(img1 == img2)

def find_best_match(letter, spritesheet_data):
    results = []
    for letter_name, sprite in spritesheet_data.items():
        result = compare_images(letter, sprite)
        results.append((result, letter_name))
    results.sort(key=lambda x: x[0], reverse=True)
    return results[0][1]

def get_screenshot():
    time.sleep(2)
    pil_image = ImageGrab.grab()
    return numpy.array((pil_image), dtype='uint8')[:, :, ::-1].copy()
