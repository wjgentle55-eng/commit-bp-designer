# BP Workflow Studio

Commit Consulting's drag-and-drop, Scratch-style builder for proposed Workday business process definitions. It starts with the **Supplier Invoice Event**: open the populated Default Definition example, reshape it with the client, then export it in the same layout as a Workday definition export.

## How it works

- **Build**: Initiation is always step `a`. Drag Action, Approval, Approval Chain, Consolidated Approval Chain, Review, To Do, Checklist, Integration and Service blocks into order. Letters update on their own. Mark a step as a sub-step to number it like `a1`, or wrap steps in "Run in parallel" so they share a letter.
- **Groups and conditions**: drop security group pills and condition rules onto steps. Each step also takes Specify, Due Date, All, Optional, Do Not Advance, Complete, Routing Modifier, Run As User and the Initiator/Approvers routing restrictions.
- **Paths**: a condition on one step means that step gets skipped when the condition is false, and the app flags it. When the same condition sits on two or more steps (but not all of them), it becomes its own **path split** automatically. You can also add splits by hand, like Company A vs Company B. The Paths tab lays each case out in its own lane. Every lane starts at Initiation and ends at Complete, and you can walk through the lanes one at a time with Previous and Next.
- **Definition**: the step grid as you'd configure it in the tenant, plus design checks. For example, it warns when a path has no Workday condition rule behind it, which would make the step run for every case.

## Import and export

- **Import** a Workday BP definition export (.xlsx with Step, Order, If, Type, Specify, Group... columns) or a design `.json` file from New or Open. Shared conditions are split into paths automatically.
- **Excel** export uses the same 16 columns as the definition export. It also includes Paths, Path Splits, Design Checks and Design Notes sheets.
- **PDF** (Commit-branded paths diagram plus definition table), **PNG**, and design **.json**.

`designs/` holds the original Supplier Invoice Event Default Definition export and the matching design file.

## Saving

Designs and templates save in your browser. To share one, export it as a design file and import it on the other side, or commit it to `designs/`.

## Running it

It's a single static file with no build step. Download `index.html` and open it in a browser, or turn on GitHub Pages (Settings > Pages > `main` / root). Excel import and export, plus PDF export, load SheetJS and jsPDF from cdnjs on first use, so they need an internet connection.
