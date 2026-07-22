import cv2
import mediapipe as mp
from time import sleep
from PIL import ImageFont, ImageDraw, Image
import numpy as np
from jamo import j2h
import webbrowser

# 폰트 설정
FONT_PATH = "malgun.ttf"
FONT_SIZE = 40
font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

# Mediapipe 손 인식 세팅
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# 카메라 초기화
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

# 쌍자음 매핑
double_consonants = {'ㄱ': 'ㄲ', 'ㄷ': 'ㄸ', 'ㅂ': 'ㅃ', 'ㅅ': 'ㅆ', 'ㅈ': 'ㅉ'}

# 이중모음 매핑
compound_vowels = {
    ('ㅗ', 'ㅏ'): 'ㅘ', ('ㅗ', 'ㅐ'): 'ㅙ', ('ㅗ', 'ㅣ'): 'ㅚ',
    ('ㅜ', 'ㅓ'): 'ㅝ', ('ㅜ', 'ㅔ'): 'ㅞ', ('ㅜ', 'ㅣ'): 'ㅟ',
    ('ㅡ', 'ㅣ'): 'ㅢ'
}

# 겹받침 매핑 (곁받침 처리용)
compound_jongsung = {
    ('ㄱ', 'ㅅ'): 'ㄳ',
    ('ㄴ', 'ㅈ'): 'ㄵ',
    ('ㄴ', 'ㅎ'): 'ㄶ',
    ('ㄹ', 'ㄱ'): 'ㄺ',
    ('ㄹ', 'ㅁ'): 'ㄻ',
    ('ㄹ', 'ㅂ'): 'ㄼ',
    ('ㄹ', 'ㅅ'): 'ㄽ',
    ('ㄹ', 'ㅌ'): 'ㄾ',
    ('ㄹ', 'ㅍ'): 'ㄿ',
    ('ㄹ', 'ㅎ'): 'ㅀ',
    ('ㅂ', 'ㅅ'): 'ㅄ',
}

# 키보드 레이아웃 (한글/영어)
keys_kor_normal = [
    ["1","2","3","4","5","6","7","8","9","0", "Del"],
    ["ㅂ","ㅈ","ㄷ","ㄱ","ㅅ","ㅛ","ㅕ","ㅑ","ㅐ","ㅔ"],
    ["ㅁ","ㄴ","ㅇ","ㄹ","ㅎ","ㅗ","ㅓ","ㅏ","ㅣ","Shift"],
    ["ㅋ","ㅌ","ㅊ","ㅍ","ㅠ","ㅜ","ㅡ", ",",".", "Enter","한/영"],
    [" "]
]

keys_kor_shift = [
    ["!","@","#","$","%","^","&","*","(", ")", "Del"],
    ["ㅃ","ㅉ","ㄸ","ㄲ","ㅆ","ㅛ","ㅕ","ㅑ","ㅒ","ㅖ"],
    ["ㅁ","ㄴ","ㅇ","ㄹ","ㅎ","ㅗ","ㅓ","ㅏ","ㅣ","Shift"],
    ["ㅋ","ㅌ","ㅊ","ㅍ","ㅠ","ㅜ","ㅡ","<",">", "Enter","한/영"],
    [" "]
]

keys_eng_normal = [
    ["1","2","3","4","5","6","7","8","9","0", "Del"],
    ["q","w","e","r","t","y","u","i","o","p"],
    ["a","s","d","f","g","h","j","k","l",";","Shift"],
    ["z","x","c","v","b","n","m",",",".","Enter","한/영"],
    [" "]
]

keys_eng_shift = [
    ["!","@","#","$","%","^","&","*","(", ")", "Del"],
    ["Q","W","E","R","T","Y","U","I","O","P"],
    ["A","S","D","F","G","H","J","K","L",":","Shift"],
    ["Z","X","C","V","B","N","M","<",">","Enter","한/영"],
    [" "]
]

# 버튼 클래스 및 생성 함수
class Button:
    def __init__(self, pos, text, size=[85,85]):
        self.pos = pos
        self.size = size
        self.text = text

def create_buttons(keys):
    buttonList = []
    screen_width = 1280
    button_w, button_h = 75, 75
    top_margin = 100
    vertical_gap = 90

    # 특별 키의 크기 비율 정의
    special_widths = {
        "Enter": 1.5,
        "Shift": 1.5,
        "한/영": 1.5,
        "Del": 1.5,
        " ": 5  # Spacebar는 여전히 5배로 유지
    }

    for i, row in enumerate(keys):
        # 키마다 가로폭 결정
        widths = [
            int(button_w * special_widths.get(k, 1))  # 특별 키는 배율 적용, 아니면 기본 크기
            for k in row
        ]
        total_row_width = sum(widths)
        margin = (screen_width - total_row_width) // (len(row) + 1)

        x = margin
        y = top_margin + i * vertical_gap
        for key, w in zip(row, widths):
            buttonList.append(Button([x, y], key, size=[w, button_h]))
            x += w + margin

    return buttonList

# 한글 자모 리스트
CHOSUNG = ['ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ','ㅅ','ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']
JUNGSUNG = ['ㅏ','ㅐ','ㅑ','ㅒ','ㅓ','ㅔ','ㅕ','ㅖ','ㅗ','ㅘ','ㅙ','ㅚ','ㅛ','ㅜ','ㅝ','ㅞ','ㅟ','ㅠ','ㅡ','ㅢ','ㅣ']
JONGSUNG = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ',
            'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ',
            'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

def is_choseong(c): return c in CHOSUNG
def is_jungseong(c): return c in JUNGSUNG
def is_jongseong(c): return c in JONGSUNG and c != ''

jamo_buffer = ['', '', '']  # [초성, 중성, 종성]
finalText = ""

def compose_jamo_buffer():
    if jamo_buffer[0] and jamo_buffer[1]:
        try:
            return j2h(*jamo_buffer)
        except:
            return ''.join(jamo_buffer)
    elif jamo_buffer[1]:
        return jamo_buffer[1]  # 중성만 있을 때 출력
    elif jamo_buffer[0]:
        return jamo_buffer[0]
    else:
        return ''

def flush_buffer():
    global jamo_buffer, finalText
    if jamo_buffer[0] != '':
        finalText += compose_jamo_buffer()
    jamo_buffer[:] = ['', '', '']
    
def add_jamo(j):
    global jamo_buffer, finalText

    # 이중모음 처리
    if jamo_buffer[1] and jamo_buffer[2] == '' and is_jungseong(j):
        combined = compound_vowels.get((jamo_buffer[1], j))
        if combined:
            jamo_buffer[1] = combined
            return

    # 이중받침 가능한 조합
    double_jongsung = {
        ('ㄱ', 'ㅅ'): 'ㄳ',
        ('ㄴ', 'ㅈ'): 'ㄵ',
        ('ㄴ', 'ㅎ'): 'ㄶ',
        ('ㄹ', 'ㄱ'): 'ㄺ',
        ('ㄹ', 'ㅁ'): 'ㄻ',
        ('ㄹ', 'ㅂ'): 'ㄼ',
        ('ㄹ', 'ㅅ'): 'ㄽ',
        ('ㄹ', 'ㅌ'): 'ㄾ',
        ('ㄹ', 'ㅍ'): 'ㄿ',
        ('ㄹ', 'ㅎ'): 'ㅀ',
        ('ㅂ', 'ㅅ'): 'ㅄ'
    }

    if jamo_buffer == ['', '', '']:
        if is_choseong(j):
            jamo_buffer[0] = j
        elif is_jungseong(j):
            jamo_buffer[1] = j
        else:
            jamo_buffer[0] = j

    elif jamo_buffer[1] == '':
        if is_jungseong(j):
            jamo_buffer[1] = j
        else:
            flush_buffer()
            add_jamo(j)

    elif jamo_buffer[2] == '':
        if is_jongseong(j):
            jamo_buffer[2] = j
        elif is_jungseong(j):
            # 중성 변경하지 말고 그대로 출력만 하도록 처리
            flush_buffer()
            finalText += j  # 중성만 바로 출력
        elif is_choseong(j):
            flush_buffer()
            jamo_buffer[0] = j
        else:
            flush_buffer()
            jamo_buffer[0] = j

    else:
        if is_jongseong(j):
            combo = double_jongsung.get((jamo_buffer[2], j))
            if combo:
                jamo_buffer[2] = combo
            else:
                flush_buffer()
                jamo_buffer[0] = j

        elif is_jungseong(j):
            jong = jamo_buffer[2]
            if jong in double_jongsung.values():
                # 겹받침 분리 처리
                # 예: 'ㄻ' -> 'ㄹ' (종성), 'ㅁ' (초성)
                for k, v in double_jongsung.items():
                    if v == jong:
                        first_part, second_part = k
                        break
                else:
                    first_part, second_part = jong, ''
        
                # 1) 기존 글자: 초성 + 중성 + 첫번째 받침(분리한 겹받침 첫 부분)
                temp_buffer = [jamo_buffer[0], jamo_buffer[1], first_part]
                finalText += j2h(*temp_buffer)  # 완성 글자 추가
        
                # 2) 버퍼 초기화 후, 새 초성 = 분리한 겹받침 두번째 받침, 중성 = j, 종성 비움
                jamo_buffer[:] = ['', '', '']
                jamo_buffer[0] = second_part
                jamo_buffer[1] = j
                jamo_buffer[2] = ''

            else:
                # 단일 받침 → 초성으로 이동
                prev_jong = jamo_buffer[2]
                jamo_buffer[2] = ''
                finalText += compose_jamo_buffer()
                jamo_buffer[:] = ['', '', '']
                jamo_buffer[0] = prev_jong
                jamo_buffer[1] = j
                jamo_buffer[2] = ''

        elif is_choseong(j):
            flush_buffer()
            jamo_buffer[0] = j

        else:
            flush_buffer()
            jamo_buffer[0] = j


def drawAll(img, buttonList, shift_on, pressed_key=None):
    img_pil = Image.fromarray(img)
    draw = ImageDraw.Draw(img_pil)

    for button in buttonList:
        x, y = button.pos
        w, h = button.size
        key = button.text

        # 기본 배경색 설정
        bg_color = (128, 128, 128)
        text_color = (255, 255, 255)

        # 클릭 상태 처리
        if key == pressed_key:
            bg_color = (255, 0, 255) if key != "Shift" else (0, 0, 255)

        draw.rectangle([x, y, x + w, y + h], fill=bg_color)
        draw.text((x + 20, y + 20), key, font=font, fill=text_color)

    return np.array(img_pil)

is_korean = False
is_shift = False
buttonList = create_buttons(keys_eng_normal)

while True:
    success, img = cap.read()
    if not success:
        break
    img = cv2.flip(img, 1)
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    lmList = []
    if results.multi_hand_landmarks:
        handLms = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)
        h, w, _ = img.shape
        for lm in handLms.landmark:
            cx, cy = int(lm.x * w), int(lm.y * h)
            lmList.append((cx, cy))

    img = drawAll(img, buttonList, is_shift)

    if lmList:
        x,y = lmList[8]  # 검지 끝
        for button in buttonList:
            bx, by = button.pos
            bw, bh = button.size
            if bx < x < bx + bw and by < y < by + bh:
                cv2.rectangle(img, (bx, by), (bx + bw, by + bh), (175, 0, 175), cv2.FILLED)
                img_pil = Image.fromarray(img)
                draw = ImageDraw.Draw(img_pil)
                draw.text((bx + 20, by + 20), button.text, font=font, fill=(255,255,255))
                img = np.array(img_pil)

                x2, y2 = lmList[12]  # 중지 끝
                distance = ((x2 - x) ** 2 + (y2 - y) ** 2) ** 0.5

                if distance < 30:  # 클릭 인식
                    key = button.text
                    if is_korean:
                        if key == "Del":
                            if jamo_buffer[2]:
                                jamo_buffer[2] = ''
                            elif jamo_buffer[1]:
                                jamo_buffer[1] = ''
                            elif jamo_buffer[0]:
                                jamo_buffer[0] = ''
                            else:
                                finalText = finalText[:-1]
                        elif key == "한/영":
                            flush_buffer()
                            is_korean = False
                            is_shift = False
                            buttonList = create_buttons(keys_eng_normal)
                        elif key == " ":
                            flush_buffer()
                            finalText += " "
                        elif key == "Shift":
                            is_shift = not is_shift
                            buttonList = create_buttons(keys_kor_shift if is_shift else keys_kor_normal)
                        elif key == "Enter":
                            flush_buffer()
                            query = finalText.strip()
                            if query:
                                webbrowser.open(f"https://www.google.com/search?q={query}")
                                finalText = ""
                        else:
                            if is_shift and key in double_consonants:
                                add_jamo(double_consonants[key])
                            else:
                                add_jamo(key)
                            is_shift = False
                            buttonList = create_buttons(keys_kor_normal)
                    else:
                        # 영어 모드
                        if key == "Del":
                            finalText = finalText[:-1]
                        elif key == "한/영":
                            is_korean = True
                            is_shift = False
                            buttonList = create_buttons(keys_kor_normal)
                        elif key == " ":
                            finalText += " "
                        elif key == "Shift":
                            is_shift = not is_shift
                            buttonList = create_buttons(keys_eng_shift if is_shift else keys_eng_normal)
                        elif key == "Enter":
                            flush_buffer()
                            query = finalText.strip()
                            if query:
                                webbrowser.open(f"https://www.google.com/search?q={query}")
                                finalText = ""
                        else:
                            finalText += key
                            is_shift = False
                            buttonList = create_buttons(keys_eng_normal)

                    sleep(0.3)  # 입력 지연

    # 텍스트 출력
    cv2.rectangle(img, (50, 40), (1100, 100), (0, 0, 0), cv2.FILLED)
    img_pil = Image.fromarray(img)
    draw = ImageDraw.Draw(img_pil)
    draw.text((60, 40), finalText + compose_jamo_buffer(), font=font, fill=(255, 255, 255))
    img = np.array(img_pil)

    cv2.imshow("Hand Keyboard", img)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()