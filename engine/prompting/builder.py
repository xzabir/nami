import os

def load_template(filename):
    path = os.path.join(os.path.dirname(__file__), "templates", filename)
    with open(path, "r") as f:
        return f.read().strip()

GROUNDING_TEMPLATE = load_template("grounding.txt")
STYLES_TEMPLATE = load_template("styles.txt")

def build_vision_prompt():
    return GROUNDING_TEMPLATE

def build_verifier_prompt(primary_facts):
    system_prompt = (
        "You are an elite QA vision model. Your job is to rigorously audit the object classification and spatial "
        "anchoring of the provided JSON Temporal Scene Graph based on the visual evidence in the frames.\n"
        "Look for common perception errors (e.g., misclassifying a street lamp as a traffic light, or attaching "
        "a camera to a pole instead of a building wall). Verify every entity's exact placement.\n"
        "You MUST return the corrected JSON object using the exact same schema. Do NOT wrap in markdown code fences."
    )
    user_prompt = f"Please verify and correct the following JSON Temporal Scene Graph:\n{primary_facts}"
    return system_prompt, user_prompt

def build_text_prompt(facts, styles, domain="General"):
    lines = STYLES_TEMPLATE.split("\n")
    style_instructions = {}
    for line in lines:
        if ":" in line:
            parts = line.split(":", 1)
            style_instructions[parts[0].strip()] = line.strip()

    active_instructions = [style_instructions[s] for s in styles if s in style_instructions]
    instructions_text = "\n".join(active_instructions)
    format_example = "{" + ", ".join([f'"{s}": "..."' for s in styles]) + "}"
    
    user_prompt = f"Markdown Scene Description:\n{facts}\n\nIdentified Domain: {domain}\n\nInstructions per style:\n{instructions_text}\n\nRequired output format: exactly {format_example}"
    
    system_prompt = (
        "You are an expert linguistic adapter. You receive a Markdown Scene Description from a vision model. "
        "You must extract the entities and events from the description and map them directly to the stylistic persona. "
        "CRITICAL HALLUCINATION PREVENTION RULES:\n"
        "1. You MUST ONLY reference entities, events, and texts that exist in the scene description.\n"
        "2. CONFIDENCE GATING: If the vision model mentions text or details as uncertain or unclear, exclude them entirely from your caption. Do not mention them. For main subjects and events, include them even if confidence is low, but adjust your certainty in the description.\n"
        "3. Exaggerate the *significance* of an action, never invent the *intent* behind it.\n"
        "4. Do not introduce any entities, actions, or outcomes that are not explicitly listed in the description.\n"
        "5. SEAMLESS CAPTIONING: DO NOT expose internal reasoning, the inference process, or image quality issues. DO NOT mention 'frames', 'sequence', 'documents', 'confidence', 'stylized filtering', 'artifacts', 'OCR', or 'unclear text'. Describe the scene naturally. If text/signs are unclear, ignore them entirely rather than stating they are unclear.\n"
        f"Use the identified domain ('{domain}') to inject domain-specific terminology, metaphors, and pacing into your writing. "
        "Rewrite these facts into distinctly-toned captions based on the requested styles. "
        "Return ONLY a valid JSON object, no other text. Do NOT wrap the JSON in markdown code fences. Keep all generated captions between 2-4 sentences."
    )
    
    return system_prompt, user_prompt
