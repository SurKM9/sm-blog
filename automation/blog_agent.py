import os
import time
import re
import requests
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langchain_tavily import TavilySearch

# Load all API Keys from .env
load_dotenv()
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# --- PATH & SECURITY CONFIG ---
SCRIPT_DIR = Path(__file__).parent.resolve()
BASE_DIR = SCRIPT_DIR.parent
BLOG_DIR = SCRIPT_DIR / "ai_drafts"
BLOG_DIR.mkdir(exist_ok=True)

# --- HELPER FUNCTIONS ---
def create_slug(text):
    """Fallback sanitization: Converts text into a URL-friendly slug."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def get_seo_slug(prompt_text):
    """Uses Qwen to convert a long prompt into a short 3-5 word SEO slug."""
    print("🔤 Extracting a short, SEO-friendly URL slug...")
    slug_generator = OllamaLLM(
        model="qwen2.5-coder:14b",
        base_url="http://127.0.0.1:11434",
        keep_alive="0"
    )
    raw_slug = slug_generator.invoke(
        f"Extract the core topic from this text and turn it into a 3 to 5 word URL slug.\n"
        f"Text: {prompt_text}\n"
        f"Output ONLY the words separated by hyphens. No quotes, no intro text."
    ).strip()
    return create_slug(raw_slug)


def get_seo_metadata(topic, outline):
    """Generates the title, description, and summary for the Hugo frontmatter."""
    print("🔤 Generating SEO Title, Description, and Summary...")
    meta_generator = OllamaLLM(
        model="qwen2.5-coder:14b",
        base_url="http://127.0.0.1:11434",
        keep_alive="0"
    )
    
    safe_outline = outline[:1500] 
    prompt = (
        f"Based on this topic: '{topic}' and this technical outline: {safe_outline}\n"
        f"Provide exactly three lines of output.\n"
        f"Line 1: A catchy, professional technical blog post title.\n"
        f"Line 2: A 1-2 sentence SEO meta description.\n"
        f"Line 3: A short summary for a blog post list view.\n"
        f"Do not include any labels, quotes, or markdown. Just the raw text."
    )
    
    raw = meta_generator.invoke(prompt).strip().split('\n')
    raw_lines = [line for line in raw if line.strip()]
    
    def clean_meta_line(line, default_text):
        if not line: return default_text
        cleaned = line.replace('**', '').replace('*', '').strip()
        cleaned = re.sub(
            r'^\s*(?:\d+\.\s*)?(?:Title|Meta Description|Description|Summary|Line \d+)\s*:\s*', 
            '', 
            cleaned, 
            flags=re.IGNORECASE
        )
        cleaned = cleaned.strip(" \"'")
        return cleaned.replace('"', "'").strip()
    
    ai_title = clean_meta_line(raw_lines[0] if len(raw_lines) > 0 else "", topic.title())
    description = clean_meta_line(raw_lines[1] if len(raw_lines) > 1 else "", f"Technical deep dive into {topic}.")
    summary = clean_meta_line(raw_lines[-1] if len(raw_lines) > 2 else "", f"An advanced guide on {topic} for developers.")
    
    return ai_title, description, summary


def get_visual_keyword(topic):
    """Forces Qwen to pick from a list of highly visual, Unsplash-friendly keywords."""
    print("👁️ Translating topic into a visual search keyword...")
    vision_generator = OllamaLLM(
        model="qwen2.5-coder:14b", 
        base_url="http://127.0.0.1:11434",
        keep_alive="0"
    )

    prompt = (
        f"You are an art director finding a background photo for a blog post about: '{topic}'.\n"
        f"Choose EXACTLY ONE word from this specific list that best matches the topic:\n"
        f"linux, server, code, programming, cloud, database, hardware, network, security, software, developer, keyboard.\n"
        f"Output ONLY the single word. No punctuation, no explanation."
    )

    raw_keyword = vision_generator.invoke(prompt).strip()
    clean_keyword = re.sub(r"[^a-zA-Z]", "", raw_keyword).lower()

    allowed_words = [
        "linux", "server", "code", "programming", "cloud", "database",
        "hardware", "network", "security", "software", "developer", "keyboard"
    ]
    
    if clean_keyword not in allowed_words:
        return "code"
    return clean_keyword


def clean_markdown_body(text):
    """Bulletproof sanitizer: Strips markdown wrappers and accidental frontmatter."""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2].strip()
    text = re.sub(r"^```[a-z]*\n", "", text, flags=re.IGNORECASE)
    if text.endswith("```"):
        text = text[:-3].strip()
    return text + "\n"


def get_bundle_dir(slug):
    bundle_path = (BLOG_DIR / slug).resolve()
    if not bundle_path.is_relative_to(BLOG_DIR):
        raise PermissionError("Access Denied: Path traversal attempt blocked!")
    return bundle_path


def generate_and_inject_frontmatter(slug, ai_title, description, summary):
    """Uses Hugo to generate perfect frontmatter, injects AI data, and cleans up."""
    print(f"\n🔧 [Step 1.5] Generating Blowfish archetype for: {ai_title}")
    
    temp_dir_name = f"ghost_draft_{slug}"
    post_rel_path = f"{temp_dir_name}/index.md"
    
    try:
        subprocess.run(["hugo", "new", post_rel_path], cwd=BASE_DIR, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Hugo new failed. Error: {e.stderr.decode()}")
        raise

    temp_full_dir = BASE_DIR / "content" / temp_dir_name
    temp_full_file = temp_full_dir / "index.md"
    
    with open(temp_full_file, "r", encoding="utf-8") as f:
        frontmatter = f.read().strip()

    shutil.rmtree(temp_full_dir)

    frontmatter = re.sub(r'^title:.*', f'title: "{ai_title}"', frontmatter, flags=re.MULTILINE)
    frontmatter = re.sub(r'^description:.*', f'description: "{description}"', frontmatter, flags=re.MULTILINE)
    frontmatter = re.sub(r'^summary:.*', f'summary: "{summary}"', frontmatter, flags=re.MULTILINE)
    
    return frontmatter


def save_secure_draft(bundle_path, content):
    os.makedirs(bundle_path, exist_ok=True)
    target_path = bundle_path / "index.md"
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
    return target_path


def get_stock_photo_url(visual_keyword):
    """Searches Unsplash and extracts image URL, author name, and profile link."""
    if not UNSPLASH_ACCESS_KEY:
        print("⚠️ Unsplash API Key missing in .env. Skipping image.")
        return None, None, None

    def fetch_image(query_string):
        url = "https://api.unsplash.com/search/photos"
        params = {
            "query": query_string,
            "orientation": "landscape",
            "per_page": 1,
            "client_id": UNSPLASH_ACCESS_KEY,
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("results"):
                result = data["results"][0]
                img_url = result["urls"]["regular"]
                author_name = result["user"]["name"]
                # Append required UTM tags per Unsplash API guidelines
                author_link = f"{result['user']['links']['html']}?utm_source=CodeFlamingo&utm_medium=referral"
                return img_url, author_name, author_link
        except Exception as e:
            pass
        return None, None, None

    print(f"🖼️ Searching Unsplash for visual: '{visual_keyword}'...")
    img_url, author_name, author_link = fetch_image(visual_keyword)
    
    if img_url:
        return img_url, author_name, author_link

    print("⚠️ Specific image not found. Falling back to generic tech image...")
    return fetch_image("software development code")


def save_post_thumbnail(image_url, bundle_path):
    if not image_url:
        return
    target_path = bundle_path / "feature.png" 
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

    slug = get_seo_slug(topic)
    print(f"   -> Calculated SEO Slug: {slug}")
    draft_bundle_dir = get_bundle_dir(slug)

    if draft_bundle_dir.exists():
        shutil.rmtree(draft_bundle_dir)

    print("\n🔍 [Step 1/4] Searching web for facts & finding a thumbnail...")
    search_tool = TavilySearch(max_results=3)
    search_data = search_tool.invoke(topic)

    visual_keyword = get_visual_keyword(topic)
    print(f"   -> Visual Keyword chosen: {visual_keyword}")
    
    # UNPACK ALL THREE VARIABLES
    image_url, author_name, author_link = get_stock_photo_url(visual_keyword)

    print("\n🧠 [Step 2/4] DeepSeek is structuring the technical outline...")
    thinker = OllamaLLM(model="deepseek-r1:14b", base_url="http://127.0.0.1:11434", keep_alive="0")
    raw_outline = thinker.invoke(
        f"Analyze these search results: {search_data}. "
        f"Create a deep technical outline for a blog post about '{topic}' "
        f"for codeflamingo.eu. Focus on advanced concepts for developers."
    )
    outline = re.sub(r'<think>.*?</think>', '', raw_outline, flags=re.DOTALL).strip()

    ai_title, description, summary = get_seo_metadata(topic, outline)
    injected_frontmatter = generate_and_inject_frontmatter(slug, ai_title, description, summary)

    print("\n✍️  [Step 3/4] Qwen is drafting the Markdown content...")
    writer = OllamaLLM(model="qwen2.5-coder:14b", base_url="http://127.0.0.1:11434", keep_alive="0")
    final_prompt = f"""You are the expert technical writer for codeflamingo.eu.
                    Draft a full Hugo blog post based on this outline: {outline}

                    CRITICAL INSTRUCTIONS:
                    1. Write ONLY the Markdown body of the post.
                    2. DO NOT output any YAML frontmatter (no --- blocks).
                    3. DO NOT wrap your response in ```markdown tags.
                    4. Start directly with the introduction or the first heading.
                    """
    raw_post = writer.invoke(final_prompt)
    clean_body = clean_markdown_body(raw_post)
    
    # NEW: Build the compliant Unsplash attribution string
    if image_url and author_name:
        attribution = (
            f"\n\n---\n"
            f"*Photo by [{author_name}]({author_link}) on "
            f"[Unsplash](https://unsplash.com/?utm_source=CodeFlamingo&utm_medium=referral)*\n"
        )
        final_post = injected_frontmatter + "\n\n" + clean_body + attribution
    else:
        final_post = injected_frontmatter + "\n\n" + clean_body

    print("\n💾 [Step 4/4] Writing directly to ai_drafts for human review...")
    save_secure_draft(draft_bundle_dir, final_post)
    save_post_thumbnail(image_url, draft_bundle_dir)

    print(f"\n✨ AUTOMATION COMPLETE! (Time taken: {time.time() - start_time:.1f}s)")
    print(f"📦 Bundle ready for review at: {draft_bundle_dir.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    print("--- CodeFlamingo Blog Agent Initialized ---")
    target_topic = input("Enter topic: ")
    generate_blog(target_topic)