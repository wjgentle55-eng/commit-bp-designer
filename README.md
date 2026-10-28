# BP Workflow Studio

Commit Consulting's drag-and-drop, Scratch-style builder for proposed Workday business process definitions. It starts with the **Supplier Invoice Event**: open the populated Default Definition example, reshape it with the client, then export it in the same layout as a Workday definition export.

## How it works

- **Build**: Initiation is always step `a`. Drag Action, Approval, Approval Chain, Consolidated Approval Chain, Review, To Do, Checklist, Integration and Service blocks into order. Letters update on their own. Mark a step as a sub-step to number it like `a1`, or wrap steps in "Run in parallel" so they share a letter.
- **Conditions**: each step's conditions sit at the front of the block, before the step type. A condition on a single step means that step gets skipped when the condition is false.
- **Paths**: the main line is the default path, with no conditions. Drop a **Split into paths** block to lay cases out side by side (for example Company A vs Company B, or Non-PO invoices). Every path has its own condition rule, and any step you drop into a path carries that rule. All the paths start at the split and rejoin below it.
- **Completion**: mark a step as Complete and the BP completes there. Steps after it still run, and they show below a "completes here" marker.
- **Copying**: use the Copy button on a block, Alt/Option-drag, Ctrl/Cmd+D, or Ctrl/Cmd+C then Ctrl/Cmd+V.
- **Security groups**: groups with "admin" in the name are user-based. Everything else is role-based (constrained).
- **Specify**: To Do steps need text here, since it's what the person sees. Action and Service steps pick from a task list (`TASK_CATALOG` in `index.html`), which has room for descriptions.
- **Definition**: the step grid as you'd configure it in the tenant, plus design checks.

## Import and export

- **Import** a Workday BP definition export (.xlsx with Step, Order, If, Type, Specify, Group... columns) or a design `.json` file from New or Open. When consecutive steps share a condition, they're grouped into a path automatically.
- **Excel** export uses the same 16 columns as the definition export. It also includes Paths, Design Checks and Design Notes sheets.
- **PDF** (Commit-branded flow diagram with paths, plus the definition table), **PNG**, and design **.json**.

`designs/` holds the original Supplier Invoice Event Default Definition export and the matching design file.

## Saving

Designs and templates save in your browser. To share one, export it as a design file and import it on the other side, or commit it to `designs/`.

## Running it

It's a single static file with no build step. Download `index.html` and open it in a browser, or turn on GitHub Pages (Settings > Pages > `main` / root). Excel import and export, plus PDF export, load SheetJS and jsPDF from cdnjs on first use, so they need an internet connection.
