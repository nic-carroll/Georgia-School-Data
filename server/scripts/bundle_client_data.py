#!/usr/bin/env python3
"""
Bundle all 235 Georgia School Districts and 2,301 Individual Schools directly into client/georgia_master_data.js
Ensures zero-dependency, 100% offline availability of all Georgia districts and schools in the client dropdowns!
"""

import os
import json

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "gosa"))
COMPREHENSIVE_JSON = os.path.join(DATA_DIR, "georgia_comprehensive_db.json")
JS_OUTPUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "client", "georgia_master_data.js"))

def bundle():
    if not os.path.exists(COMPREHENSIVE_JSON):
        print(f"Error: {COMPREHENSIVE_JSON} missing.")
        return

    with open(COMPREHENSIVE_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    districts = data.get("districts", [])
    all_schools = data.get("allSchools", [])

    js_content = f"// Comprehensive Dataset of all 235 Georgia School Districts and {len(all_schools)} Individual Schools\n"
    js_content += f"window.GEORGIA_GOSA_MASTER = {json.dumps(data, indent=2)};\n"

    with open(JS_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(js_content)

    print(f"Bundled {len(districts)} Georgia Districts and {len(all_schools)} Individual Schools into {JS_OUTPUT}")

if __name__ == "__main__":
    bundle()
