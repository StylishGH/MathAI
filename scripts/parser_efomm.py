import os
import re
import json
import pymupdf
from pathlib import Path

def extract_text_and_images(pdf_path, output_img_dir):
    os.makedirs(output_img_dir, exist_ok=True)
    doc = pymupdf.open(pdf_path)
    
    pages_data = []
    for page_idx, page in enumerate(doc):
        text = page.get_text("text")
        
        images = []
        for img_idx, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            img_filename = f"page_{page_idx+1}_img_{img_idx+1}.{image_ext}"
            img_filepath = os.path.join(output_img_dir, img_filename)
            
            with open(img_filepath, "wb") as f:
                f.write(image_bytes)
            images.append(img_filename)
            
        pages_data.append({
            "page_num": page_idx + 1,
            "text": text,
            "images": images
        })
        
    return pages_data

def clean_footer(text):
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        if "Prova:" in line or "MATEM" in line or "FÍSICA" in line or "PS-EFOMM" in line or "Exame de Conhecimentos" in line or "[PAGE_" in line:
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()

def split_into_questions(pages_data):
    full_text = ""
    math_started = False
    
    for p in pages_data:
        # Só começa a juntar o texto depois de encontrar algo parecido com "PROVA DE MATEMÁTICA" ou se já começou
        # Em arquivos divididos, pode já ser matemática na pág 1.
        if not math_started:
            if "MATEM" in p['text'].upper():
                math_started = True
            elif len(pages_data) < 15: 
                # Se for um PDF pequeno (ex: só matemática), começa do início
                math_started = True
                
        if math_started:
            full_text += f"\n[PAGE_START {p['page_num']}]\n"
            full_text += p['text']
            full_text += f"\n[PAGE_END {p['page_num']}]\n"
        
    # Se nunca encontrou MATEM (anomalia), processa tudo
    if not math_started:
        for p in pages_data:
            full_text += f"\n[PAGE_START {p['page_num']}]\n"
            full_text += p['text']
            full_text += f"\n[PAGE_END {p['page_num']}]\n"
            
    pattern = re.compile(r'(?:^|\n)\s*([0-9lI]{1,2})\s*(?:ª|º|\"|\'|”|“|11|\-|\.|\)|a|\s)*Quest(?:ã|a|)(?:o|)\b', re.IGNORECASE)
    splits = pattern.split(full_text)
    
    if len(splits) <= 1:
        pattern = re.compile(r'(?:^|\n)\s*(\d{1,2})\s*\)', re.IGNORECASE)
        splits = pattern.split(full_text)
        
    questions = []
    expected_q = 1
    
    for i in range(1, len(splits), 2):
        q_num_str = splits[i].upper().replace('I', '1').replace('L', '1')
        try:
            q_num = int(q_num_str)
        except:
            continue
        
        if q_num != expected_q and (q_num < expected_q or q_num > expected_q + 2):
            q_num = expected_q
            
        # EFOMM Matemática é de 1 a 20.
        if q_num > 20:
            continue
            
        q_text = splits[i+1].strip()
        q_text = clean_footer(q_text)
        
        questions.append({
            "numero": q_num,
            "texto_bruto": q_text
        })
        
        expected_q = q_num + 1
        
    return questions

def parse_alternatives(questions):
    alt_pattern = re.compile(r'(?:\n\s*|\b)\(([A-E])\)\s*')
    
    parsed_questions = []
    for q in questions:
        raw = q["texto_bruto"]
        splits = alt_pattern.split(raw)
        
        enunciado = splits[0].strip()
        alternativas = {}
        
        if len(splits) >= 11:
            for i in range(1, len(splits), 2):
                letter = splits[i].upper()
                text = splits[i+1].strip()
                alternativas[f"alternativa_{letter.lower()}"] = text
                
        parsed_questions.append({
            "numero": q["numero"],
            "enunciado": enunciado,
            "alternativas": alternativas,
            "texto_bruto": raw
        })
        
    return parsed_questions
