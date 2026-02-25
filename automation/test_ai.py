import time
from langchain_ollama import OllamaLLM

def run_diagnostic():
    print("--- 🛠️ Starting Ollama Diagnostic ---")
    
    # 1. Initialize with explicit IPv4 address
    # We use 127.0.0.1 instead of 'localhost' to avoid IPv6 issues
    print("1. Connecting to Ollama at http://127.0.0.1:11434...")
    llm = OllamaLLM(
        model="qwen2.5-coder:7b", 
        base_url="http://127.0.0.1:11434",
        timeout=60 # Give your 3070 Ti a full minute to load the model
    )

    try:
        start_time = time.time()
        print("2. Sending prompt... (This may take 10-30 seconds if it's the first run)")
        
        # Simple probe
        response = llm.invoke("Say the word 'Flaming'")
        
        end_time = time.time()
        print(f"3. ✅ Success! (Time taken: {end_time - start_time:.2f}s)")
        print(f"   Response: {response}")

    except Exception as e:
        print(f"   ❌ Failed!")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Details: {e}")
        print("\n💡 Tip: Check if you pulled the model exactly: 'ollama pull qwen2.5-coder:7b'")

if __name__ == "__main__":
    run_diagnostic()