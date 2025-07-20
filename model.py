import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
from PIL import Image
import requests
from io import BytesIO
import os

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen-VL-Chat", trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen-VL-Chat", device_map="auto", trust_remote_code=True, fp16=True).eval()
model.generation_config = GenerationConfig.from_pretrained("Qwen/Qwen-VL-Chat", trust_remote_code=True)

def process_image(image_path):
    print("image path")
    print(image_path)
    
    query = tokenizer.from_list_format([
        {'image': image_path},  # Local path
        {'text': 'draw and detect damage in a box in the picture?'},
    ])
    response, history = model.chat(tokenizer, query=query, history=None)
    print(response)

    image_with_bbox = tokenizer.draw_bbox_on_latest_picture(response, history)
    output_image_path = os.path.join("output", os.path.basename(image_path))
    image_with_bbox.save(output_image_path)
    
    
    return response, os.path.basename(output_image_path)

def process_image_text(image_path):
    query = tokenizer.from_list_format([
        {'image': image_path},  # Local path
        {'text': 'describe the damages detected appears in the image'},
    ])
    response, history = model.chat(tokenizer, query=query, history=None)
    print(f"text: {response}")

    
    return response

