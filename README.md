# BP Workflow Studio

Commit Consulting's drag-and-drop, Scratch-style builder for proposed Workday business process definitions. It starts with the **Supplier Invoice Event**: open the populated Default Definition example, reshape it with the client, then export it in the same layout as a Workday definition export.

## How it works

- **Home**: opening the app lands on a home page with **New definition**, a **Build from a Workday definition** drop zone, and your saved definitions (Open). Drop the definition export (.xlsx), choose the file, or paste the step grid, and it's built into blocks for you: shared conditions become paths, Complete = Yes becomes the Document approved block, same-letter steps become parallel, and Workday owned conditions are locked. The side panel then lists what was built. New asks which business process first, then lets you start from the delivered default (Supplier Invoice), start blank, use a template, or import.
- **Palette**: Approval, Action, Service and To Do are up top. **Path manipulation** (Split into paths, Run in parallel, Document approved) and **Other types** (Approval Chain, Consolidated Approval Chain, Review, Checklist, Integration) are dropdowns.
- **Build**: Initiation is always step `a`. Letters update on their own. Mark a step as a sub-step to number it like `a1`.
- **Business process**: the header dropdown decides which Action and Service tasks, security groups, condition rules and recommendations are offered (`BP_CATALOG` in `index.html`). Supplier Invoice Event is fully loaded; the others have groups only for now.
- **Conditions**: a step's conditions sit at the front of the block. Workday owned conditions show in grey, stay with their delivered step, and can't be added to another step or used as a path rule.
- **Split into paths** and **Run in parallel** share the same C-block shape, with their contents side by side. Each path has a condition rule in the same format as a step condition, and every step dropped into a path carries it. Steps in a parallel block share one order letter.
- **Document approved**: place it under the step that completes the business process. That step gets Complete = Yes. There can only be one.
- **Help text**: click into any step and add your own notes in the Help text field in Step details.
- **Step details**: clicking a block shows a plain-English description of what the step does, then its fields.
- **All**: on Approval and Action steps, every member of the security group has to approve or act.
- **Checklist**: add items and assign each one to a group. Drag a To Do block onto a checklist to turn it into an item.
- **Integration and Service**: named in Specify, no security group.
- **Copy and delete**: hover any block for Copy and Delete. Alt/Option-drag copies, Ctrl/Cmd+D duplicates, Ctrl/Cmd+C then V copies and pastes, Delete removes.
- **Recommended**: with nothing selected, the right panel recommends blocks for the chosen process that aren't on the canvas yet.
- **Security groups**: groups with "admin" in the name are user-based. Everything else is role-based (constrained).

## Import and export

- **Import** a Workday BP definition export (.xlsx with Step, Order, If, Type, Specify, Group... columns) or a design `.json` file from New or Open. When consecutive steps share a condition, they're grouped into a path automatically.
- **Excel** export uses the same 16 columns as the definition export. It also includes Paths, Checklist Items, Design Checks, and Help and Notes sheets.
- **PDF** (Commit-branded flow diagram with paths, plus the definition table), **PNG**, and design **.json**.

`designs/` holds the original Supplier Invoice Event Default Definition export and the matching design file.

## Saving

Designs and templates save in your browser. To share one, export it as a design file and import it on the other side, or commit it to `designs/`.

## Running it

It's a single static file with no build step. Download `index.html` and open it in a browser, or turn on GitHub Pages (Settings > Pages > `main` / root). Excel import and export, plus PDF export, load SheetJS and jsPDF from cdnjs on first use, so they need an internet connection.
