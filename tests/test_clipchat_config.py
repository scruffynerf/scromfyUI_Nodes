import os
import sys
import shutil

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock transformers to avoid heavy loading
from unittest.mock import MagicMock
sys.modules['transformers'] = MagicMock()
sys.modules['torch'] = MagicMock()

from py.clipchat import ClipChat

def test_config_logic():
    print("Testing ClipChat Configuration Logic...")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    user_config_path = os.path.join(base_dir, "userconfig", "user_clipchat_settings.json")
    
    # 1. Clean up existing user config
    if os.path.exists(user_config_path):
        os.remove(user_config_path)
    if os.path.exists(os.path.dirname(user_config_path)):
        os.rmdir(os.path.dirname(user_config_path))
    print("- Cleaned up previous user config.")

    # 2. Trigger INPUT_TYPES (should create config)
    inputs = ClipChat.INPUT_TYPES()
    models = inputs["required"]["model_name"][0]
    
    # 3. Verify creation and default loading
    assert os.path.exists(user_config_path), "User config file should be created"
    assert "Qwen/Qwen3-4B-Instruct-2507" in models, "Default model should be present"
    print("✓ Config creation and default load successful")
    
    # 4. Modify config manually
    with open(user_config_path, "w") as f:
        f.write('{"models": ["My/Custom/Model"]}')
        
    # 5. Trigger again (should load custom)
    inputs_modified = ClipChat.INPUT_TYPES()
    custom_models = inputs_modified["required"]["model_name"][0]
    
    assert "My/Custom/Model" in custom_models, "Custom model should be loaded"
    assert len(custom_models) == 1
    print("✓ Custom config load successful")
    
    # Cleanup (optional - leave it so user can see it works)
    # os.remove(user_config_path)
    # os.rmdir(os.path.dirname(user_config_path))

if __name__ == "__main__":
    try:
        test_config_logic()
        print("\nAll config tests passed!")
    except Exception as e:
        print(f"\nTests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
