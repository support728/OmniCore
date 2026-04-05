#!/usr/bin/env python3
"""Remove duplicated text from JSON files."""

import json
import os

def clean_memory_json():
    """Remove consecutive duplicate messages from memory.json"""
    memory_path = r"cd 04_Code\memory.json"
    try:
        with open(memory_path, 'r') as f:
            data = json.load(f)
        
        # Remove consecutive duplicates (same role + content)
        cleaned = []
        seen_prev = None
        for item in data:
            current = (item.get("role"), item.get("content"))
            if current != seen_prev:
                cleaned.append(item)
            seen_prev = current
        
        with open(memory_path, 'w') as f:
            json.dump(cleaned, f, indent=2)
        
        removed = len(data) - len(cleaned)
        print(f"✓ memory.json: Removed {removed} duplicate entries ({len(data)} → {len(cleaned)})")
        return removed
    except Exception as e:
        print(f"  memory.json: {e}")
        return 0

def clean_user_memory_json():
    """Remove consecutive duplicate entries from user_memory.json"""
    user_path = r"cd 04_Code\user_memory.json"
    try:
        with open(user_path, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and "memories" in data:
            memories = data["memories"]
            cleaned = []
            seen_prev = None
            for item in memories:
                # Create a hashable key of the item
                current = json.dumps(item, sort_keys=True)
                if current != seen_prev:
                    cleaned.append(item)
                seen_prev = current
            
            data["memories"] = cleaned
            with open(user_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            removed = len(memories) - len(cleaned)
            if removed > 0:
                print(f"✓ user_memory.json: Removed {removed} duplicate entries ({len(memories)} → {len(cleaned)})")
            return removed
        return 0
    except Exception as e:
        print(f"  user_memory.json: {e}")
        return 0

if __name__ == "__main__":
    print("[Cleaning duplicate text from JSON files...]")
    total = 0
    total += clean_memory_json()
    total += clean_user_memory_json()
    print(f"\n✅ Total duplicates removed: {total}")
