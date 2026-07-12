import os

dirs = [
    "engine",
    "engine/core",
    "engine/preprocessing",
    "engine/prompting/templates",
    "engine/providers",
    "engine/utils",
    "docker",
    "tests/unit",
    "tests/integration",
    "tests/fixtures"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    init_file = os.path.join(d, "__init__.py")
    if d.startswith("engine") and not os.path.exists(init_file):
        with open(init_file, "w") as f:
            pass

print("Directories created.")
