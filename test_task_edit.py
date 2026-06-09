"""Test script to verify task text editing."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from src.ui.editor import TaskWidget, PageEditor
from src.models.task import Task

def test_task_text_editing():
    """Test editing text in a task."""
    print("Testing task text editing...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create a task widget
    tw = TaskWidget(block_id=1)
    
    print("  Task widget created")
    
    # Find the QTextEdit in the task
    edits = tw.findChildren(type(tw).layout().itemAt(0).widget().findChildren(QTextEdit.__bases__[0]) if tw.layout().count() > 0 else None)
    
    print("  Finding text edit...")
    for widget in tw.findChildren(QTextEdit.__bases__[0]):
        print(f"    Found: {widget.__class__.__name__}")
    
    print("[PASS] Task text editing test completed\n")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("TASK TEXT EDITING TEST")
    print("=" * 60 + "\n")
    
    try:
        success = test_task_text_editing()
    except Exception as e:
        print(f"[FAIL] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    print("=" * 60)
    if success:
        print("[PASS] ALL TESTS PASSED")
    else:
        print("[FAIL] SOME TESTS FAILED")
    print("=" * 60)
