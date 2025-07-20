import zipfile
import json
import os
from PIL import Image
import cv2
import numpy as np
import re
from werkzeug.utils import secure_filename
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
import requests
from io import BytesIO

model_dir = "/home/groupe/.cache/modelscope/qwen/Qwen-VL-Chat"

tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_dir, device_map="cuda", trust_remote_code=True, bf16=True).eval()

def get_damage_position(x1, y1, x2, y2, img_width=1920, img_height=1440):
    x_center = (x1 + x2) / 2
    y_center = (y1 + y2) / 2

    if x_center < img_width / 3:
        h_pos = "à gauche"
    elif x_center < 2 * img_width / 3:
        h_pos = "au centre"
    else:
        h_pos = "à droite"

    if y_center < img_height / 3:
        v_pos = "en haut"
    elif y_center < 2 * img_height / 3:
        v_pos = "au milieu"
    else:
        v_pos = "en bas"

    return f"{v_pos} {h_pos}"

def process_image_text(image_path, detection_type):
    if detection_type == 'damage':
        prompt = 'Identify and name the type of damage visible in the image. Respond only with the damage type.'
    elif detection_type == 'equipment':
        prompt = 'Identify and name the visible equipment in the image. Respond only with the equipment name.'

    query = tokenizer.from_list_format([
        {'image': image_path},
        {'text': prompt},
    ])
    response, history = model.chat(tokenizer, query=query, history=None)
    print(f"text: {response}")

    # Nettoyage du texte pour ne retourner que le nom pertinent
    if detection_type == 'equipment':
        
        match = re.search(r"(?:is\s*:?\s*)?([\w\s-]+)\.?", response, re.IGNORECASE)
        if match:
            response = match.group(1).strip()

    elif detection_type == 'damage':
        
        match = re.search(r"is\s+(?:a|an)?\s*([\w\s-]+)[\.\n]?", response, re.IGNORECASE)
        if match:
            response = match.group(1).strip()

    return response


def process_image(image_path, prompt):
    print("image path")
    print(image_path)

    query = tokenizer.from_list_format([
        {'image': image_path},
        {'text': prompt},
    ])
    response, history = model.chat(tokenizer, query=query, history=None)
    print(response)

    image_with_bbox = tokenizer.draw_bbox_on_latest_picture(response, history)
    output_image_path = os.path.join("output", os.path.basename(image_path))
    image_with_bbox.save(output_image_path)

    return response, os.path.basename(output_image_path)

def extract_bbox_dimensions(response):
    bbox_pattern = re.compile(r'<box>\((\d+),(\d+)\),\((\d+),(\d+)\)</box>')
    match = bbox_pattern.search(response)
    width, height = 1920, 1440

    if match:
        x1, y1, x2, y2 = map(int, match.groups())
        x1_actual = int((x1 * width) / 1000)
        y1_actual = int((y1 * height) / 1000)
        x2_actual = int((x2 * width) / 1000)
        y2_actual = int((y2 * height) / 1000)
        return x1_actual, y1_actual, x2_actual, y2_actual
    return None

def process_and_resize_images(image_path, x1, y1, x2, y2, fx, fy, cx, cy):
    desired_resolution = (1440, 1920)
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        print(f"Failed to read image {image_path} with OpenCV.")
        return

    resized_image = cv2.resize(image, desired_resolution, interpolation=cv2.INTER_NEAREST)
    print(f"Min depth value: {np.min(resized_image)}")
    print(f"Max depth value: {np.max(resized_image)}")

    output_path = "resized_image.png"
    cv2.imwrite(output_path, resized_image)
    print(f"Resized image saved to {output_path}")

    depth_map = np.array(resized_image).astype(np.float32)

    # Limiter les coordonnées à l'image
    x1 = min(x1, depth_map.shape[1] - 1)
    x2 = min(x2, depth_map.shape[1] - 1)
    y1 = min(y1, depth_map.shape[0] - 1)
    y2 = min(y2, depth_map.shape[0] - 1)

    # Réduction de la boîte de 10% sur chaque bord
    margin_x = int((x2 - x1) * 0.1)
    margin_y = int((y2 - y1) * 0.1)

    x1 += margin_x
    x2 -= margin_x
    y1 += margin_y
    y2 -= margin_y

    # Vérification que les coordonnées restent valides
    x1 = max(0, min(x1, depth_map.shape[1] - 1))
    x2 = max(0, min(x2, depth_map.shape[1] - 1))
    y1 = max(0, min(y1, depth_map.shape[0] - 1))
    y2 = max(0, min(y2, depth_map.shape[0] - 1))

    Z1 = depth_map[y1, x1]
    Z2 = depth_map[y2, x2]

    X1 = (x1 - cx) * Z1 / fx
    Y1 = (y1 - cy) * Z1 / fy
    X2 = (x2 - cx) * Z2 / fx
    Y2 = (y2 - cy) * Z2 / fy

    try:
        width = np.sqrt((X2 - X1) ** 2 + (Z2 - Z1) ** 2)
        height = np.sqrt((Y2 - Y1) ** 2 + (Z2 - Z1) ** 2)
        print(f"Width: {width}, Height: {height}")
    except OverflowError:
        print("Overflow error encountered in W AND H calculation.")
        return None, None

    return int(width), int(height)


def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)


def analyze_zip(zip_path, detection_type):
    extract_to = os.path.join(os.getcwd(), 'uploads')
    os.makedirs(extract_to, exist_ok=True)
    extract_zip(zip_path, extract_to)

    zip_filename = secure_filename(zip_path.filename)
    zip_file_name = os.path.splitext(zip_filename)[0]
    extract_to = os.path.join(os.getcwd(), 'uploads', zip_file_name)

    image_sizes = {}
    json_content = None

    for root, dirs, files in os.walk(extract_to):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if file_name.endswith('.json'):
                with open(file_path, 'r') as file:
                    json_content = json.load(file)
            elif file_name.endswith(('.png', '.jpg', '.jpeg')):
                with Image.open(file_path) as img:
                    image_sizes[file_path] = img.size

    if not image_sizes:
        print("No images found in the zip file.")
        return

    sorted_images = sorted(image_sizes.items(), key=lambda x: x[1][0] * x[1][1])
    smallest_image = sorted_images[0][0]
    largest_image = sorted_images[-1][0]
    print(f"Smallest image: {smallest_image}")
    print(f"Largest image: {largest_image}")

    if json_content:
        fx = json_content.get("focalLengthX")
        fy = json_content.get("focalLengthY")
        cx = json_content.get("principalPointX")
        cy = json_content.get("principalPointY")
    else:
        print("No JSON file found in the zip.")
        return

    if detection_type == 'damage':
        prompt = 'Draw a bounding box around each visible damage in the image and label it with the name of the damage only.'
    elif detection_type == 'equipment':
        prompt = 'Draw a bounding box around each visible equipment in the image and label it with the name of the equipment only.'
    
    response, output_image_path = process_image(largest_image, prompt)
    bbox_dimensions = extract_bbox_dimensions(response)

    if bbox_dimensions:
        x1, y1, x2, y2 = bbox_dimensions
        print(f"Processing smallest image: {smallest_image}")
        Width, Height = process_and_resize_images(smallest_image, x1, y1, x2, y2, fx, fy, cx, cy)
        Position = get_damage_position(x1, y1, x2, y2)
    else:
        print("No bounding box dimensions found.")
        Width, Height, Position = None, None, None

    # Seulement pour les dommages
    response_text = process_image_text(largest_image, detection_type)


    return response_text, output_image_path, Width, Height, Position