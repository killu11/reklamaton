import re
import easyocr
from bs4 import BeautifulSoup
import easyocr
import re
from PIL import Image
import numpy as np

def parse_profile_screenshot(image_path):
    reader = easyocr.Reader(['ru'], gpu=False)
    result_text = reader.readtext(image_path, detail=0, paragraph=True)
    text = "\n".join(result_text)

    sections = {}
    current_section = None
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith('био'):
            current_section = 'bio'
            sections[current_section] = []
            continue
        if line.lower().startswith('основное'):
            current_section = 'main'
            sections[current_section] = []
            continue
        if line.lower().startswith('язык'):
            current_section = 'languages'
            sections[current_section] = []
            continue
        if current_section:
            sections[current_section].append(line)

    # Структурируем результат
    profile = {
        "raw": dict(sections),
        "main": {},
        "languages": [],
        "bio": "",
    }

    if 'bio' in sections:
        profile['bio'] = " ".join(sections['bio']).strip()
    if 'languages' in sections:
        profile['languages'] = [line for line in sections['languages'] 
                                if line and not re.search(r'[🇷🇺🇬🇧]', line)]
    if 'main' in sections:
        zodiac = height = education = children = attitude = smoking = None
        other = []
        for item in sections['main']:
            if re.search(r'(Овен|Телец|Близнецы|Рак|Лев|Дева|Весы|Скорпион|Стрелец|Козерог|Водолей|Рыбы)', item, re.I):
                zodiac = item; continue
            if re.match(r'^\d{3}\s*см?$', item):
                height = item.replace(" ", ""); continue
            if re.search(r'(Высшее|Среднее|Техникум|Колледж|Бакалавр|Магистр|Студент)', item, re.I):
                education = item; continue
            if re.search(r'нет, но хотел', item, re.I):
                children = 'Нет, но хотелось бы'; continue
            if re.search(r'(есть|нет)', item, re.I) and ('хочется' not in item):
                children = item; continue
            if re.search(r'(нейтр|без разницы)', item, re.I):
                attitude = item; continue
            if re.search(r'(не курю|курю|иногда курю|нейтр)', item, re.I):
                smoking = item; continue
            other.append(item)
        
        profile["main"] = {k: v for k, v in {
            "zodiac": zodiac, "height": height, "education": education, 
            "children": children, "attitude_children": attitude, "smoking": smoking,
            "other": other or None
        }.items() if v}

    # Строка для общения с model (LLM)
    def fieldru(key):
        return {
            "zodiac": "Знак зодиака",
            "height": "Рост",
            "education": "Образование",
            "children": "Дети",
            "attitude_children": "Отношение к детям",
            "smoking": "Курение",
            "other": "Другое"
        }.get(key, key)

    parts = []
    if profile["bio"]: parts.append(f"О себе: {profile['bio']}")
    for k, v in profile["main"].items():
        if v:
            if isinstance(v, list):
                v = ", ".join(v)
            if k != "other":
                parts.append(f"{fieldru(k)}: {v}")
    if profile["languages"]:
        parts.append(f"Языки: {', '.join(profile['languages'])}")
    if profile["main"].get("other"):
        parts.append(f"Другое: {', '.join(profile['main']['other'])}")
    profile["full_text"] = "\n".join(parts)

    return profile

def get_bbox_center(bbox):
    x = [point[0] for point in bbox]
    y = [point[1] for point in bbox]
    return sum(x) / 4, sum(y) / 4

def get_avg_color(img, bbox):
    x_coords = [int(point[0]) for point in bbox]
    y_coords = [int(point[1]) for point in bbox]
    min_x, max_x = max(min(x_coords), 0), min(max(x_coords), img.width)
    min_y, max_y = max(min(y_coords), 0), min(max(y_coords), img.height)
    if min_x >= max_x or min_y >= max_y:
        return (255,255,255)
    crop = img.crop((min_x, min_y, max_x, max_y))
    arr = np.array(crop)
    avg = arr.mean(axis=(0, 1))
    return tuple(avg.astype(int))

def is_blue(rgb):
    return rgb[2] > 200 and rgb[0] < 180 and rgb[1] > 150

def is_gray(rgb):
    r, g, b = rgb
    return abs(r-g) < 15 and abs(g-b) < 15 and 180 < r < 250

# Регулярка для времени — одно/два числа : два числа
RE_TIME = re.compile(r"\b\d{1,2}:\d{2}\b")

def parse_twinby_chat(image_path, crop_percent=0.1):  # crop_percent = по 13% сверху и снизу (≈ 1/8)
    reader = easyocr.Reader(['ru'], gpu=False)
    img = Image.open(image_path)
    width, height = img.size
    # Обрезаем верх и низ (crop)
    y1 = int(height * crop_percent)
    y2 = int(height * (1 - crop_percent))
    img_cropped = img.crop((0, y1, width, y2))
    # OCR  ТОЛЬКО по обрезанному фрагменту
    results = reader.readtext(np.array(img_cropped), detail=1, paragraph=False)
    messages = []
    for entry in results:
        bbox, text, conf = entry
        text = text.strip()
        # Смещаем bbox к изначальному img по оси y
        bbox = [[x, y + y1] for x, y in bbox]
        # -- Фильтрация "шапок"/футеров/времени/пустых
        if not text:
            continue
        if re.search(r"Сегодня|Вчера", text, re.I):
            continue
        if RE_TIME.search(text):
            continue
        cx, cy = get_bbox_center(bbox)
        avg_rgb = get_avg_color(img, bbox)
        # Определи роль (выставить свои пороги)
        if cx > width * 0.55:
            role = "You"
        elif cx < width * 0.45:
            role = "Partner"
        else:
            if is_blue(avg_rgb):
                role = "You"
            else:
                role = "Partner"
        messages.append({"role": role, "text": text})
    return messages

def parse_telegram_html_chat(html_path):
    """
    Парсит Telegram-диалог из HTML-выгрузки (messages.html)
    Использует информацию из class="joined", чтобы определить,
    что сообщение принадлежит предыдущей цепочке от того же пользователя.
    Сообщения без from_name приписываются к последнему отправителю.
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    messages = []
    current_group = None

    for msg in soup.find_all('div', class_='message'):
        classes = msg.get('class', [])
        is_joined = 'joined' in classes

        user_div = msg.find('div', class_='from_name')
        text_div = msg.find('div', class_='text')

        if not text_div:
            continue

        text = text_div.get_text(separator='\n', strip=True)
        if not text:
            continue

        # Определяем отправителя
        if not is_joined or not user_div:
            if user_div:
                sender = user_div.get_text(strip=True)
            elif current_group:
                sender = current_group['role']
            else:
                sender = "Неизвестный автор"
        else:
            sender = user_div.get_text(strip=True)

        # Объединяем или создаём новое сообщение
        if not is_joined or (current_group and current_group['role'] != sender):
            messages.append({"role": sender, "text": text})
            current_group = messages[-1]
        else:
            if current_group:
                current_group['text'] += '\n' + text

    return messages