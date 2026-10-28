# BP Workflow Studio

Commit Consulting's drag-and-drop, Scratch-style builder for proposed Workday business process definitions. It starts with the **Supplier Invoice Event**: open the populated Default Definition example, reshape it with the client, then export it in the same layout as a Workday definition export.

## How it works

- **Build**: Initiation is always step `a`. Drag Action, Approval, Approval Chain, Consolidated Approval Chain, Review, To Do, Checklist, Integration and Service blocks into order. Letters update on their own. Mark a step as a sub-step to number it like `a1`, or wrap steps in "Run in parallel" so they share a letter.
- **Conditions**: each step's conditions sit at the front of the block, before the step type. A condition on a single step means that step gets skipped when the condition is false.
- **Business process**: pick the process in the header. It decides which Action and Service tasks, security groups, condition rules and recommendations are offered (`BP_CATALOG` in `index.html`). Supplier Invoice Event is fully loaded; the others have groups only for now.
- **Paths**: the main line is the default path, with no conditions, and it runs straight down the middle of a **Split into paths** block. The condition paths branch left and right of it (for example Company A vs Company B, or Non-PO invoices). Every path has its own condition rule, and any step you drop into a path carries that rule. All the paths start at the split and rejoin below it.
- **Completion**: drag in the **Business process complete** block where the document gets approved. There can only be one. Steps below it still run after completion, and on export the step right above it gets Complete = Yes.
- **Copy and delete**: hover any block for Copy and Delete buttons. You can also Alt/Option-drag to copy, press Ctrl/Cmd+D to duplicate, Ctrl/Cmd+C then V to copy and paste, Delete to remove, or drag a block back to the palette.
- **Recommended**: with nothing selected, the right panel recommends blocks for the chosen process that aren't on the canvas yet. Click one or drag it in. Click a block and the panel switches to that block's details.
- **Security groups**: groups with "admin" in the name are user-based. Everything else is role-based (constrained).
- **Specify**: To Do steps need text here, since it's what the person sees. Action and Service steps pick from a dropdown of the selected process's tasks, which has room for descriptions, or take a custom task.
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
