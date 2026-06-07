## Plan: Fix +List crash in text boxes and table cells

TL;DR - The crash likely occurs in `PageEditor._on_add_list` inside `src/ui/editor.py` because it checks only the direct parent of the focused widget for `TableCell` instead of walking the ancestor chain. Fixing this and making the handler more robust should stop the app from closing.

**Steps**
1. In `src/ui/editor.py`, add a helper method on `PageEditor` to find the nearest `TableCell` ancestor from a focused widget. This should mirror `_find_block_widget` but target `TableCell`.
2. Update `PageEditor._on_add_list`:
   - Replace the direct `focus_widget.parent()` check with the new table-cell ancestor helper.
   - Keep the MarkdownBlock branch unchanged, but make the table-cell lookup robust for nested widgets.
   - Add a small `try/except` around the table-cell and block-body branches to prevent unhandled exceptions from closing the app.
3. If no active text body or table cell is found, preserve the existing fallback behavior of creating a new `checkbox` block.
4. Verify manually after the change by:
   - Clicking inside a regular text block and pressing `+ List`.
   - Clicking inside a table cell and pressing `+ List`.
   - Confirming the app stays open and the task list is inserted.
5. Ensure the fix handles nested focus widgets in table cells and avoids any direct parent-only assumptions.

**Relevant file**
- `src/ui/editor.py` — modify `PageEditor._on_add_list` and add the new table-cell lookup helper.

**Verification**
1. Run the app and test `+ List` while focus is inside a text box.
2. Run the app and test `+ List` while focus is inside a table cell.
3. Confirm no crash and that the task list behavior remains correct.

**Decision**
- The fix is scoped to the toolbar `+ List` handler only. No broader UI or table serialization changes are planned.
