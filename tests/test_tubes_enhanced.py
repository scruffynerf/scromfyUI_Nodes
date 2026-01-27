import os
import sys
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from py.tubes import merge_tube_with_strategy

def test_merge_strategies():
    print("Testing Merge Strategies...")
    
    base = {"prompt": "original", "seed": 123, "tags": ["A", "B"]}
    
    # 1. Override
    res = merge_tube_with_strategy(base, {"prompt": "new"}, "override")
    assert res["prompt"] == "new"
    assert res["seed"] == 123
    print("✓ override ok")
    
    # 2. Only if empty/none
    res = merge_tube_with_strategy(base, {"prompt": "new", "cfg": 7.0}, "only if empty/none")
    assert res["prompt"] == "original"  # No override
    assert res["cfg"] == 7.0           # New key set
    print("✓ only if empty/none ok")
    
    # 3. Combine
    res = merge_tube_with_strategy(base, {"tags": ["C", "A"], "seed": 456}, "combine")
    assert "A" in res["tags"] and "B" in res["tags"] and "C" in res["tags"]
    assert len(res["tags"]) == 3
    assert res["seed"] == [123, 456]
    print("✓ combine ok")

def test_json_logic():
    print("\nTesting JSON logic simulation...")
    # This just tests the underlying helper since the nodes are classes
    base = {"a": 1, "b": 2}
    data_json = '{"b": 3, "c": 4}'
    data = json.loads(data_json)
    
    res = merge_tube_with_strategy(base, data, "override")
    assert res["b"] == 3
    assert res["c"] == 4
    print("✓ JSON merge simulation ok")

if __name__ == "__main__":
    try:
        test_merge_strategies()
        test_json_logic()
        print("\nAll Tube enhancement sanity checks passed!")
    except Exception as e:
        print(f"\nTests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
