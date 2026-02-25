import os
import time
import re
import requests
import shutil
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langchain_tavily import TavilySearch

# Load all API Keys from .env
load_dotenv()
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# --- PATH & SECURITY CONFIG ---
BASE_DIR = Path(__file__).parent.parent.resolve()
BLOG_DIR = BASE_DIR / "content" / "blog"

# --- HELPER FUNCTIONS ---
def create_slug(text):
    """Fallback sanitization: Converts text into a URL-friendly slug."""
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def get_seo_slug(prompt_text):
    """Uses Qwen to convert a long prompt into a short 3-5 word SEO slug."""
    print("🔤 Extracting a short, SEO-friendly URL slug...")
    slug_generator = OllamaLLM(model="qwen2.5-coder:7b", base_url="[http://127.0.0.1:11434](http://127.0.0.1:11434)")
    raw_slug = slug_generator.invoke(
        f"Extract the core topic from this text and turn it into a 3 to 5 word URL slug.\n"
        f"Text: {prompt_text}\n"
        f"Output ONLY the words separated by hyphens. No quotes, no intro text."
    ).strip()
    return create_slug(raw_slug)

def get_visual_keyword(topic):
    """Forces Qwen to pick from a list of highly visual, Unsplash-friendly keywords."""
    print("👁️ Translating topic into a visual search keyword...")
    vision_generator = OllamaLLM(model="qwen2.5-coder:7b", base_url="http://127.0.0.1:11434")
    
    prompt = (
        f"You are an art director finding a background photo for a blog post about: '{topic}'.\n"
        f"Choose EXACTLY ONE word from this specific list that best matches the topic:\n"
        f"linux, server, code, programming, cloud, database, hardware, network, security, software, developer, keyboard.\n"
        f"Output ONLY the single word. No punctuation, no explanation."
    )
    
    raw_keyword = vision_generator.invoke(prompt).strip()
    clean_keyword = re.sub(r'[^a-zA-Z]', '', raw_keyword).lower()
    
    # Failsafe: if the AI still disobeys and picks a weird word, default to 'code'
    allowed_words = ["linux", "server", "code", "programming", "cloud", "database", "hardware", "network", "security", "software", "developer", "keyboard"]
    if clean_keyword not in allowed_words:
        return "code"
        
    return clean_keyword

def clean_llm_output(text, fallback_yaml):
    """Bulletproof sanitizer: Ensures YAML is present and removes markdown wrappers."""
    # 1. Look for the start of the YAML frontmatter
    start_idx = text.find("---")
    
    if start_idx != -1:
        # Slice off any conversational junk before the YAML
        text = text[start_idx:]
    else:
        # FAILSAFE: The AI completely forgot the YAML. We inject it manually.
        print("⚠️ AI missed the YAML frontmatter! Force-injecting the template...")
        # Strip leading markdown wrappers just in case
        text = re.sub(r"^```[a-z]*\n", "", text.strip(), flags=re.IGNORECASE)
        text = fallback_yaml + "\n\n" + text

    # 2. Clean up trailing markdown code block ticks at the bottom of the file
    text = text.strip()
    if text.endswith("```"):
        text = text[:-3].strip()
        
    return text + "\n"

def get_bundle_dir(slug):
    """Calculates and validates the secure path for the page bundle."""
    bundle_path = (BLOG_DIR / slug).resolve()
    if not bundle_path.is_relative_to(BLOG_DIR):
        raise PermissionError("Access Denied: Path traversal attempt blocked!")
    return bundle_path

def save_secure_draft(bundle_path, content):
    """Saves Markdown content as index.md inside the bundle directory."""
    os.makedirs(bundle_path, exist_ok=True)
    target_path = bundle_path / "index.md"
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
    return target_path

def get_stock_photo_url(visual_keyword):
    """Searches Unsplash using a broad visual keyword."""
    if not UNSPLASH_ACCESS_KEY:
        print("⚠️ Unsplash API Key missing in .env. Skipping image.")
        return None
        
    def fetch_image(query_string):
        url = "https://api.unsplash.com/search/photos"
        params = {"query": query_string, "orientation": "landscape", "per_page": 1, "client_id": UNSPLASH_ACCESS_KEY}
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("results"):
                return data["results"][0]["urls"]["regular"]
        except Exception as e:
            pass
        return None

    # Try 1: Our curated keyword (e.g., "linux" or "server")
    print(f"🖼️ Searching Unsplash for visual: '{visual_keyword}'...")
    img = fetch_image(visual_keyword)
    if img: return img
    
    # Try 2: Ultimate Fallback
    print("⚠️ Specific image not found. Falling back to generic tech image...")
    return fetch_image("software development code")

def save_post_thumbnail(image_url, bundle_path):
    """Downloads and saves the image directly into the page bundle."""
    if not image_url: return
    target_path = bundle_path / "logo.jpg"
    print(f"⬇️ Downloading thumbnail to bundle: {target_path.relative_to(BASE_DIR)}...")
    try:
        os.makedirs(bundle_path, exist_ok=True)
        response = requests.get(image_url, stream=True, timeout=20)
        response.raise_for_status()
        with open(target_path, "wb") as out_file:
            shutil.copyfileobj(response.raw, out_file)
        print("✅ Thumbnail saved successfully.")
    except Exception as e:
        print(f"⚠️ Failed to download/save image: {e}")

# --- MAIN AGENT PIPELINE ---
def generate_blog(topic):
    print(f"\n🚀 Starting Page Bundle Pipeline for: '{topic}'")
    start_time = time.time()
    
    # 1. Pre-calculate metadata
    slug = get_seo_slug(topic)
    print(f"   -> Calculated SEO Slug: {slug}")
    bundle_path = get_bundle_dir(slug)
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    # 2. Define the strict YAML Template
    yaml_template = f"""---
title: "[Write a catchy, SEO-friendly title for the topic]"
date: {current_time}
draft: true

# post thumb
image: "/blog/{slug}/logo.jpg"

# meta description
description: "[Write a compelling 1-2 sentence meta description for search engines]"

# taxonomies
categories:
  - Tech
tags:
  - [tag1]
  - [tag2]

# post type
type: "post"
---"""

    # 3. Parallel Tasks: Web Research & Image Sourcing
    print("🔍 [Step 1/4] Searching web for facts & finding a thumbnail...")
    search_tool = TavilySearch(max_results=3)
    search_data = search_tool.invoke(topic)
    
    # Translate the topic into a photography-friendly keyword
    visual_keyword = get_visual_keyword(topic)
    print(f"   -> Visual Keyword chosen: {visual_keyword}")
    image_url = get_stock_photo_url(visual_keyword) 

    # 4. Architect / Outliner (DeepSeek-R1)
    print("\n🧠 [Step 2/4] DeepSeek is structuring the technical outline...")
    thinker = OllamaLLM(
        model="deepseek-r1:7b", base_url="[http://127.0.0.1:11434](http://127.0.0.1:11434)", keep_alive="1h"
    )
    outline = thinker.invoke(
        f"Analyze these search results: {search_data}. "
        f"Create a deep technical outline for a blog post about '{topic}' "
        f"for codeflaming.eu. Focus on advanced concepts for developers."
    )

    # 5. Writer / Coder (Qwen)
    print("\n✍️  [Step 3/4] Qwen is drafting the final Markdown content...")
    writer = OllamaLLM(
        model="qwen2.5-coder:7b", base_url="[http://127.0.0.1:11434](http://127.0.0.1:11434)", keep_alive="10m"
    )
    
    # Notice the CRITICAL INSTRUCTIONS block added to force compliance
    final_prompt = f"""You are the expert technical writer for codeflaming.eu.
Draft a full Hugo blog post based on this outline: {outline}

CRITICAL INSTRUCTIONS:
1. You MUST start your response EXACTLY with this YAML frontmatter. Fill in the [brackets]:
{yaml_template}
2. DO NOT wrap your response in ```markdown tags. Start the very first line with ---
3. Follow the YAML immediately with the Markdown body.
"""
    raw_post = writer.invoke(final_prompt)
    
    # Clean the LLM output and pass the template as a failsafe
    final_post = clean_llm_output(raw_post, yaml_template)

    # 6. Finalize: Save Draft & Download Image
    print("\n💾 [Step 4/4] Generating Page Bundle...")
    save_secure_draft(bundle_path, final_post)
    save_post_thumbnail(image_url, bundle_path)

    print(f"\n✨ AUTOMATION COMPLETE! (Time taken: {time.time() - start_time:.1f}s)")
    print(f"📦 Bundle created at: {bundle_path.relative_to(BASE_DIR)}")

if __name__ == "__main__":
    print("--- CodeFlaming Blog Agent Initialized ---")
    target_topic = input("Enter topic: ")
    generate_blog(target_topic)