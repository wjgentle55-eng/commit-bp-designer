# BP Workflow Studio

Commit Consulting's drag-and-drop, Scratch-style builder for proposed Workday business process definitions. It starts with the **Supplier Invoice Event**: open the populated Default Definition example, reshape it with the client, then export it in the same layout as a Workday definition export.

## How it works

- **Home**: opening the app lands on a home page with **New definition**, a **Build from a Workday definition** drop zone, and your saved definitions (Open). Drop the definition export (.xlsx), choose the file, or paste the step grid, and it's built into blocks for you: shared conditions become paths, Complete = Yes becomes the Document approved block, same-letter steps become parallel, and Workday owned conditions are locked. The side panel then lists what was built. New asks which business process first, then lets you start from the delivered default (Supplier Invoice), start blank, use a template, or import.
- **Palette**: Approval, Action, Service and To Do are up top. **Path manipulation** (Split into paths, Run in parallel, Document approved) and **Other types** (Approval Chain, Consolidated Approval Chain, Review, Checklist, Integration) are dropdowns.
- **Build**: Initiation is always step `a`. Letters update on their own. Mark a step as a sub-step to number it like `a1`.
- **Business process**: chosen when the definition is created (New, or read from an import) and fixed after that; to design another process, start a New definition. It decides which Action and Service tasks, security groups, condition rules and recommendations are offered (`BP_CATALOG` in `index.html`). Supplier Invoice Event is fully loaded; the others have groups only for now.
- **Conditions**: a step's conditions sit at the front of the block. Workday owned conditions show in grey, stay with their delivered step, and can't be added to another step or used as a path rule.
- **Build paths**: groups steps into paths automatically (it also runs on every import). A path is a condition rule, or a group of rules that always appear together, that two or more steps contain; a path whose steps all sit inside a bigger path stays as step conditions instead. A step that belongs to several paths sits in one and shows as a dashed **linked copy** in the others (edited and exported once). A step that falls between a path's steps but doesn't need its rule is **shared**: it runs whatever the path condition is. Steps outside any path stay on the main line and apply to all. Lanes are ordered to keep the original Workday order wherever possible; Undo reverts it. A path can need more than one rule: dropping another rule on a path header adds it.
- **Split into paths** and **Run in parallel** share the same C-block shape, with their contents side by side. Each path has a condition rule in the same format as a step condition, and every step dropped into a path carries it. Steps in a parallel block share one order letter.
- **Document approved**: place it under the step that completes the business process. That step gets Complete = Yes. There can only be one.
- **Help text**: click into any step and add your own notes in the Help text field in Step details.
- **Flow tab**: the client-facing view, and exactly what the PDF flow page prints. Steps read left to right and wrap to the next row, numbered Step 1, Step 2... (parallel steps share a number, like 3A and 3B). Each card puts the approver or reviewer at the top, then the due date, then the entry conditions. A dashed **gate** card shows a path condition and which steps it applies to. Two or more paths sit in a dashed **Conditional paths** frame, and parallel steps sit in a dashed **Run in parallel** frame. Steps after Document approved are greyed and tagged After approval. **Auto** picks the cards per row that fit one page; if a design is too long to stay readable on one page, the PDF splits it across landscape pages. The Definition tab and PDF table show the Step number next to the Workday order letter. Click a card to jump to that step in Build.
- **Step details**: clicking a block shows a plain-English description of what the step does, then its fields.
- **All**: on Approval and Action steps, every member of the security group has to approve or act.
- **Checklist**: add items and assign each one to a group. Drag a To Do block onto a checklist to turn it into an item.
- **Integration and Service**: named in Specify, no security group.
- **Copy and delete**: hover any block for Copy and Delete. Alt/Option-drag copies, Ctrl/Cmd+D duplicates, Ctrl/Cmd+C then V copies and pastes, Delete removes.
- **Select several blocks**: click a block, then Shift-click another in the same column to select the run between them. Selections have to be next to each other. Copy, paste, duplicate, delete and drag work on the whole run.
- **Custom chains**: save a selected run with **Save as custom chain**. It shows up in the Custom chains tab on the left, ready to drag in. A chain saved in one business process can be used in another only if every task, security group and condition rule in it exists there; otherwise it's greyed out with what's missing. Chains save in your browser for now.
- **Initial vs proposed**: what comes in from Workday (an import or a delivered default) is the **Initial** version. Every edit is part of the **Proposed** version. Build, Definition and Flow (and the PDF) put a thick yellow border on every pending change, labelled New or Changed with what changed. All three list removed steps (with Restore on Build). The toggle above the canvas shows the Initial version read-only.
- **Publish**: makes the proposed version the new approved version in Studio (Published v1, v2...), which later changes are compared against. Earlier versions are kept. Nothing is sent to Workday.
- **Revert**: replaces the proposed version with an earlier one: the last published version (discarding every proposed change), an older published version, or Initial. Each choice shows how much it differs from Proposed. Published versions stay in the history and Undo brings the proposed changes back. To make a reverted version official again, press Publish. Nothing is sent to Workday.
- **Migrate to tenant**: will send a published version to the Workday tenant. Not available yet.
- **Recommended**: with nothing selected, the right panel recommends blocks for the chosen process that aren't on the canvas yet.
- **Security groups**: groups with "admin" in the name are user-based. Everything else is role-based (constrained).

## Clients and folders

Home is organized as **Clients › Business processes › Definitions**. Add a client, add business process folders inside it, and start or import definitions from inside a folder so they're filed there. The header shows where a definition is filed (**Client › Business process**); neither can be edited there. To file a definition under another client, use **Move to client** on its card on Home. Definitions without a client sit under **No client**. Definitions saved before folders existed are filed automatically by their Client field. Renaming a client updates its definitions; only an empty client or folder can be deleted (move its definitions first). Like everything else, folders save in this browser until the hosted version (logins and edit history come later).

## Pulling from Workday

`tools/wd_pull` is a read-only command-line tool that pulls business process definitions from a tenant (`Get_Business_Process_Definitions` on `Core_Implementation_Service`) and writes one `.csv` per definition in the definition export's columns. Drop the files on Home inside a client folder: several at once are each saved as a definition there, and the importer builds paths, conditions and the Document approved point as for an export. Setup, options and what to confirm on the first live run are in [tools/wd_pull/README.md](tools/wd_pull/README.md). Credentials stay in a local `.env`, which is gitignored.

## Import and export

- **Import** a Workday BP definition export (.xlsx with Step, Order, If, Type, Specify, Group... columns) or a design `.json` file from New or Open. When consecutive steps share a condition, they're grouped into a path automatically.
- **Excel** export uses the same 16 columns as the definition export. It also includes Paths, Checklist Items, Design Checks, and Help and Notes sheets.
- **PDF** (Commit-branded flow that reads left to right and wraps to rows to fit one page, plus the definition table with a Step column), **PNG**, and design **.json**.

`designs/` holds the original Supplier Invoice Event Default Definition export and the matching design file.

## Saving

Designs and templates save in your browser. To share one, export it as a design file and import it on the other side, or commit it to `designs/`.

## Running it

It's a single static file with no build step. Download `index.html` and open it in a browser, or turn on GitHub Pages (Settings > Pages > `main` / root). Excel import and export, plus PDF export, load SheetJS and jsPDF from cdnjs on first use, so they need an internet connection.
