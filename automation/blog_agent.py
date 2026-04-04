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
# Define the script's home (e.g., automation/)
SCRIPT_DIR = Path(__file__).parent.resolve()

# Define the root project directory (one level up from automation)
BASE_DIR = SCRIPT_DIR.parent

# Define where the final drafts go
BLOG_DIR = SCRIPT_DIR / "ai_drafts"

# Ensure the draft folder exists
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
    
    # Truncate outline to prevent VRAM overflow during metadata generation
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
    
    # Filter out empty lines in case the AI double-spaced its response
    raw_lines = [line for line in raw if line.strip()]
    
    # --- NEW: Aggressive Label & Quote Stripper ---
    def clean_meta_line(line, default_text):
        if not line: return default_text
        
        # 1. Remove markdown bold/italics just in case (e.g., **Title:**)
        cleaned = line.replace('**', '').replace('*', '').strip()
        
        # 2. Aggressively strip prefixes (handles "1. Title:", "Meta Description:", etc.)
        # This safely ignores colons inside the actual title (e.g., "Hugo: A Guide")
        cleaned = re.sub(
            r'^\s*(?:\d+\.\s*)?(?:Title|Meta Description|Description|Summary|Line \d+)\s*:\s*', 
            '', 
            cleaned, 
            flags=re.IGNORECASE
        )
        
        # 3. Strip surrounding quotes (both single and double) and whitespace
        cleaned = cleaned.strip(" \"'")
        
        # 4. Convert any remaining internal double quotes to single quotes for YAML safety
        return cleaned.replace('"', "'").strip()
    
    # Extract and aggressively clean the AI output
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
    # 1. Remove DeepSeek's thinking tags if any leaked through
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    
    # 2. Remove accidental YAML frontmatter if Qwen disobeys
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2].strip()
            
    # 3. Remove markdown code wrappers (e.g., ```markdown ... ```)
    text = re.sub(r"^```[a-z]*\n", "", text, flags=re.IGNORECASE)
    if text.endswith("```"):
        text = text[:-3].strip()
        
    return text + "\n"


def get_bundle_dir(slug):
    """Calculates and validates the secure path for the page bundle."""
    bundle_path = (BLOG_DIR / slug).resolve()
    if not bundle_path.is_relative_to(BLOG_DIR):
        raise PermissionError("Access Denied: Path traversal attempt blocked!")
    return bundle_path


def generate_and_inject_frontmatter(slug, ai_title, description, summary):
    """Uses Hugo to generate perfect frontmatter, injects AI data, and cleans up."""
    print(f"\n🔧 [Step 1.5] Generating Blowfish archetype for: {ai_title}")
    
    # Generate into a temporary ghost directory inside content
    temp_dir_name = f"ghost_draft_{slug}"
    post_rel_path = f"{temp_dir_name}/index.md"
    
    try:
        # Reverted to standard hugo new without the unsupported flag
        subprocess.run(
            ["hugo", "new", post_rel_path], 
            cwd=BASE_DIR, 
            check=True, 
            capture_output=True
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Hugo new failed. Error: {e.stderr.decode()}")
        raise

    # Read the generated file
    temp_full_dir = BASE_DIR / "content" / temp_dir_name
    temp_full_file = temp_full_dir / "index.md"
    
    with open(temp_full_file, "r", encoding="utf-8") as f:
        frontmatter = f.read().strip()

    # INSTANT CLEANUP: Delete the ghost directory from the Hugo content folder
    shutil.rmtree(temp_full_dir)

    # 💉 THE FIX: Inject ALL the AI-generated metadata, overwriting whatever Hugo guessed
    frontmatter = re.sub(r'^title:.*', f'title: "{ai_title}"', frontmatter, flags=re.MULTILINE)
    frontmatter = re.sub(r'^description:.*', f'description: "{description}"', frontmatter, flags=re.MULTILINE)
    frontmatter = re.sub(r'^summary:.*', f'summary: "{summary}"', frontmatter, flags=re.MULTILINE)
    
    return frontmatter


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
                return data["results"][0]["urls"]["regular"]
        except Exception as e:
            pass
        return None

    print(f"🖼️ Searching Unsplash for visual: '{visual_keyword}'...")
    img = fetch_image(visual_keyword)
    if img:
        return img

    print("⚠️ Specific image not found. Falling back to generic tech image...")
    return fetch_image("software development code")


def save_post_thumbnail(image_url, bundle_path):
    """Downloads and saves the image directly into the page bundle."""
    if not image_url:
        return
        
    # Standardized image name for Blowfish
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

    # 1. Pre-calculate metadata
    slug = get_seo_slug(topic)
    print(f"   -> Calculated SEO Slug: {slug}")
    draft_bundle_dir = get_bundle_dir(slug)

    # Clean up the draft target directory if it exists from a previous failed run
    if draft_bundle_dir.exists():
        shutil.rmtree(draft_bundle_dir)

    # 2. Parallel Tasks: Web Research & Image Sourcing
    print("\n🔍 [Step 1/4] Searching web for facts & finding a thumbnail...")
    search_tool = TavilySearch(max_results=3)
    search_data = search_tool.invoke(topic)

    visual_keyword = get_visual_keyword(topic)
    print(f"   -> Visual Keyword chosen: {visual_keyword}")
    image_url = get_stock_photo_url(visual_keyword)

    # 3. Architect / Outliner (DeepSeek-R1)
    print("\n🧠 [Step 2/4] DeepSeek is structuring the technical outline...")
    thinker = OllamaLLM(
        model="deepseek-r1:14b",
        base_url="http://127.0.0.1:11434",
        keep_alive="0",
    )
    raw_outline = thinker.invoke(
        f"Analyze these search results: {search_data}. "
        f"Create a deep technical outline for a blog post about '{topic}' "
        f"for codeflamingo.eu. Focus on advanced concepts for developers."
    )
    
    # Strip out the massive DeepSeek thinking blocks to save memory!
    outline = re.sub(r'<think>.*?</think>', '', raw_outline, flags=re.DOTALL).strip()

    # 4. Generate Metadata & Inject into Frontmatter
    ai_title, description, summary = get_seo_metadata(topic, outline)
    injected_frontmatter = generate_and_inject_frontmatter(slug, ai_title, description, summary)

    # 5. Writer / Coder (Qwen)
    print("\n✍️  [Step 3/4] Qwen is drafting the Markdown content...")
    writer = OllamaLLM(
        model="qwen2.5-coder:14b",
        base_url="http://127.0.0.1:11434",
        keep_alive="0",
    )

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
    
    # Merge Hugo's Frontmatter with Qwen's Body
    final_post = injected_frontmatter + "\n\n" + clean_body

    # 6. Finalize: Write directly to ai_drafts & Save Image
    print("\n💾 [Step 4/4] Writing directly to ai_drafts for human review...")
    
    # Write the index.md directly into the automation/ai_drafts folder
    save_secure_draft(draft_bundle_dir, final_post)
    
    # Download the thumbnail as feature.png
    save_post_thumbnail(image_url, draft_bundle_dir)

    print(f"\n✨ AUTOMATION COMPLETE! (Time taken: {time.time() - start_time:.1f}s)")
    print(f"📦 Bundle ready for review at: {draft_bundle_dir.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    print("--- CodeFlamingo Blog Agent Initialized ---")
    target_topic = input("Enter topic: ")
    generate_blog(target_topic)