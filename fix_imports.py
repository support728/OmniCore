#!/usr/bin/env python
"""Fix relative imports in fastapi_rag_backend/app to absolute package paths."""

import os
import re
from pathlib import Path

# Target directory
target_dir = Path(r"c:\Users\smoni\OneDrive\New folder\New folder\OmniCore\fastapi_rag_backend\app")

# Pattern to match relative imports
pattern = re.compile(r'^(\s*)(from|import)\s+app\.', re.MULTILINE)

fixed_files = []
for py_file in target_dir.rglob('*.py'):
    with open(py_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if file has relative imports
    if pattern.search(content):
        # Replace "from app." with "from fastapi_rag_backend.app."
        # Replace "import app." with "import fastapi_rag_backend.app."
        new_content = pattern.sub(r'\1\2 fastapi_rag_backend.app.', content)
        
        with open(py_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        fixed_files.append(str(py_file.relative_to(target_dir.parent.parent)))
        print(f"Fixed: {py_file.relative_to(target_dir.parent.parent)}")

print(f"\nTotal files fixed: {len(fixed_files)}")
