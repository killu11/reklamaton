import cv2
import numpy as np
from deepface import DeepFace
from PIL import Image
import imagehash
# анализ одной фотографии

# предлагаю все ошибки ловить на уровне выше, при реализации функции, и просто выводить "К сожалению, возникла ошибка при анализе фото. Попробуйте снова"

def analyze_single_photo(image_path):
    """
    Оценивает фото и возвращает словарь с результатами и рекомендациями.
    :param image_path: путь к изображению
    :return: dict с результатами или None в случае ошибки
    """
    import cv2
    import numpy as np
    from deepface import DeepFace

    # Детекция лица
    try:
        face_objs = DeepFace.extract_faces(img_path=image_path, detector_backend="retinaface")
        if len(face_objs) == 0:
            return {"error": "❌ На фото не найдено лицо. Пожалуйста, загрузите фото с одним лицом."}
        if len(face_objs) > 1:
            return {"error": "❌ На фото больше одного лица. Пожалуйста, загрузите фото с одним лицом."}
    except Exception as e:
        print(e)
        return {"error": "❌ На фото не найдено лицо. Пожалуйста, загрузите фото с одним лицом."}

    result = {
        "has_face": True,
        "recommendations": []
    }

    # Анализ эмоции (важно: работаем с массивом лица)
    try:
        emotion_results = DeepFace.analyze(img_path=image_path, actions=['emotion'])
        emotion_result = emotion_results[0]  # <-- тут исправление
        dominant_emotion = emotion_result["dominant_emotion"]
        result["emotion"] = dominant_emotion

        if dominant_emotion == "happy":
            result["recommendations"].append("😄 Отличный выбор! Улыбка делает фото привлекательным и располагающим к общению.")
        elif dominant_emotion == "neutral":
            result["recommendations"].append("😐 Нейтральное выражение подходит, но добавьте чуть больше эмоций — так фото будет запоминающимся.")
        elif dominant_emotion == "sad":
            result["recommendations"].append("😢 Эмоция грусти может отпугнуть потенциальных собеседников. Рекомендуем использовать фото с более позитивным выражением лица.")
        elif dominant_emotion == "angry":
            result["recommendations"].append("😠 Выражение раздражения или злости может вызывать негативные ассоциации. Подберите фото с более дружелюбным лицом.")
        elif dominant_emotion == "fear":
            result["recommendations"].append("😰 Тревожное или напряжённое выражение может вызвать беспокойство у пользователей. Лучше выберите фото с уверенным и спокойным взглядом.")
        elif dominant_emotion == "disgust":
            result["recommendations"].append("😖 Выражение отвращения или недовольства не подходит для дейтинг-профиля. Попробуйте выбрать фото с более приятным и доброжелательным выражением лица.")
        elif dominant_emotion == "surprise":
            result["recommendations"].append("😲 Удивление — не самая подходящая эмоция для профиля. Оно может выглядеть неестественно. Выберите более спокойное и уверенное выражение.")
        else:
            result["recommendations"].append("🙂 Эмоциональное выражение на фото выглядит подходящим для дейтинг-профиля.")
    except Exception as e:
        print(e)
        return {'error': 'К сожалению, при анализе фотографии возникла ошибка. Попробуйте загрузить фотографию снова.'}

    # Анализ резкости и освещения
    try:
        image = cv2.imread(image_path)
        if image is None:
            return {'error': 'Не удалось загрузить изображение. Проверьте путь к файлу.'}
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        brightness = np.mean(gray)
        sharpness_ok = sharpness > 100
        brightness_ok = 40 < brightness < 220
        result["sharpness_ok"] = sharpness_ok
        result["brightness_ok"] = brightness_ok

        if not sharpness_ok:
            result["recommendations"].append("⚠️ Фото слишком размытое. Попробуйте сделать снимок в более стабильной обстановке.")
        else:
            result["recommendations"].append("📷 Резкость в порядке — отличное качество изображения.")
        if not brightness_ok:
            if brightness < 40:
                result["recommendations"].append("⚠️ Слишком тёмное фото. Используйте дополнительное освещение.")
            else:
                result["recommendations"].append("⚠️ Слишком яркое фото. Избегайте прямых бликов.")
        else:
            result["recommendations"].append("💡 Освещение в порядке — фото хорошо выдержано по яркости.")
    except Exception as e:
        print(e)
        return {'error': 'К сожалению, при анализе фотографии возникла ошибка. Попробуйте загрузить фотографию снова.'}

    # Анализ насыщенности цвета
    try:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype("float32")
        saturation = cv2.mean(hsv[:, :, 1])[0]
        saturation_ok = saturation > 40
        result["saturation_ok"] = saturation_ok
        if saturation_ok:
            result["recommendations"].append("🌈 Фото насыщенное, цвета яркие — это привлекает внимание!")
    except Exception as e:
        print(e)
        return {'error': 'К сожалению, при анализе фотографии возникла ошибка. Попробуйте загрузить фотографию снова.'}

    return result

def get_image_hash(image_path):
    """Возвращает perceptual hash изображения"""
    return str(imagehash.phash(Image.open(image_path)))

def compare_two_photos(photo1_path, photo2_path, analysis_cache):
    """
    Сравнивает два фото и возвращает рекомендацию, какое лучше.
    Использует кэш для ускорения анализа.

    :param photo1_path: путь к первому фото
    :param photo2_path: путь ко второму фото
    :param analysis_cache: словарь {image_hash: analysis_result}
    :return: dict с результатами сравнения
    """

    # Получаем хэши фото
    hash1 = get_image_hash(photo1_path)
    hash2 = get_image_hash(photo2_path)

    # Проверяем кэш или анализируем фото
    if hash1 in analysis_cache:
        analysis1 = analysis_cache[hash1]
    else:
        analysis1 = analyze_single_photo(photo1_path)
        analysis_cache[hash1] = analysis1

    if hash2 in analysis_cache:
        analysis2 = analysis_cache[hash2]
    else:
        analysis2 = analyze_single_photo(photo2_path)
        analysis_cache[hash2] = analysis2

    # Проверяем на ошибки
    if "error" in analysis1:
        return {"error": f"Ошибка в первом фото: {analysis1['error']}"}
    if "error" in analysis2:
        return {"error": f"Ошибка во втором фото: {analysis2['error']}"}

    # Счётчики преимуществ
    score1 = 0
    score2 = 0

    reasons = []

    # --- 1. Эмоция ---
    good_emotions = ["happy", "neutral", "surprise"]
    bad_emotions = ["sad", "angry", "fear", "disgust"]

    emotion1 = analysis1.get("emotion")
    emotion2 = analysis2.get("emotion")

    if emotion1 in good_emotions and emotion2 in bad_emotions:
        score1 += 1
        reasons.append("😄 Первое фото с лучшей эмоцией.")
    elif emotion2 in good_emotions and emotion1 in bad_emotions:
        score2 += 1
        reasons.append("😄 Второе фото с лучшей эмоцией.")
    elif emotion1 in good_emotions and emotion2 in good_emotions:
        reasons.append("😄 Оба фото с позитивной эмоцией.")
    elif emotion1 in bad_emotions and emotion2 in bad_emotions:
        reasons.append("😭 Оба фото с негативной эмоцией.")

    # --- 2. Резкость ---
    sharpness1 = analysis1.get("sharpness_ok", False)
    sharpness2 = analysis2.get("sharpness_ok", False)

    if sharpness1 and not sharpness2:
        score1 += 1
        reasons.append("📷 Первое фото более резкое.")
    elif not sharpness1 and sharpness2:
        score2 += 1
        reasons.append("📷 Второе фото более резкое.")
    elif sharpness1 and sharpness2:
        reasons.append("📷 Оба фото резкие.")

    # --- 3. Освещение ---
    brightness1 = analysis1.get("brightness_ok", False)
    brightness2 = analysis2.get("brightness_ok", False)

    if brightness1 and not brightness2:
        score1 += 1
        reasons.append("💡 Первое фото с лучшим освещением.")
    elif not brightness1 and brightness2:
        score2 += 1
        reasons.append("💡 Второе фото с лучшим освещением.")
    elif brightness1 and brightness2:
        reasons.append("💡 Оба фото с хорошим освещением.")

    # --- 4. Насыщенность цвета ---
    saturation1 = analysis1.get("saturation_ok", False)
    saturation2 = analysis2.get("saturation_ok", False)

    if saturation1 and not saturation2:
        score1 += 1
        reasons.append("🌈 Первое фото более насыщенное.")
    elif not saturation1 and saturation2:
        score2 += 1
        reasons.append("🌈 Второе фото более насыщенное.")
    elif saturation1 and saturation2:
        reasons.append("🌈 Оба фото яркие и насыщенные.")

    # --- Определяем победителя ---
    winner = None
    if score1 > score2:
        winner = "Первое фото лучше"
    elif score2 > score1:
        winner = "Второе фото лучше"
    else:
        winner = "Оба фото примерно одинаковые по качеству"

    return {
        "winner": winner,
        "reasons": reasons,
        "score1": score1,
        "score2": score2,
        "is_same_photo": hash1 == hash2
    }