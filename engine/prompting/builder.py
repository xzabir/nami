import os

def load_template(filename):
    path = os.path.join(os.path.dirname(__file__), "templates", filename)
    with open(path, "r") as f:
        return f.read().strip()

GROUNDING_TEMPLATE = load_template("grounding.txt")
STYLES_TEMPLATE = load_template("styles.txt")

def build_vision_prompt():
    return GROUNDING_TEMPLATE

def build_text_prompt(facts, styles):
    lines = STYLES_TEMPLATE.split("\n")
    style_instructions = {}
    for line in lines:
        if ":" in line:
            parts = line.split(":", 1)
            style_instructions[parts[0].strip()] = line.strip()

    active_instructions = [style_instructions[s] for s in styles if s in style_instructions]
    instructions_text = "\n".join(active_instructions)
    format_example = "{" + ", ".join([f'"{s}": "..."' for s in styles]) + "}"
    
    user_prompt = f"JSON Factual Ledger:\n{facts}\n\nInstructions per style:\n{instructions_text}\n\nRequired output format: exactly {format_example}"
    
    system_prompt = "You are an expert linguistic adapter. You receive a JSON Factual Ledger from a vision model. You must extract the nouns, verbs, and dynamics from 'subjects', 'actions', 'scene_setting', and 'chronological_flow' and map them directly to the stylistic persona. Do not include unconfirmed details. CRITICAL ANTI-HALLUCINATION RULES: 1. Exaggerate the *significance* of an action, never invent the *intent* behind it. 2. Never declare an action happened for 'no reason'. 3. Forbid subjective adverbs/adjectives for physical actions (e.g. 'gracefully', 'dramatic'). Do not introduce any entities, actions, or outcomes that are not explicitly listed in the confirmed sections. Use the 'environment_context' to adapt your humor and metaphors to the specific context of the clip. Rewrite these facts into distinctly-toned captions based on the requested styles. Return ONLY a valid JSON object, no other text. Keep all generated captions between 2-4 sentences."
    
    return system_prompt, user_prompt
