# BP Workflow Studio

A drag-and-drop, Scratch-style builder for proposing Workday business process approval chains. Use it live in client design workshops, then export a config-ready table for the build.

## What it does

- **Starter BPs**: load a typical default chain for Supplier Invoice, Expense Report, Requisition, Purchase Order, Journal Entry, Spend Authorization, Supplier Request, Ad Hoc Bank Transaction and Asset Disposal, or start from a blank canvas. Confirm starters against the client's delivered definition before building.
- **Step blocks**: Approval, Approval Chain, Consolidated Approval Chain, Review, To Do, Action, Checklist and Integration. Order letters (a, b, c...) update automatically as you drag.
- **Parallel steps**: wrap steps in a "Run in parallel" block so they share the same order letter.
- **Security groups**: role-based, user-based, self-service and integration groups, plus client-specific custom groups. Drag a group pill onto a step to attach it.
- **Condition rules**: drag a condition (e.g. `Amount > 10,000`) onto a step to make it the entry condition, or write your own.
- **Routing restrictions**: Company, Cost Center, hierarchies, Region, Supervisory Org and more.
- **Design checks**: flags missing groups, chains without role-based groups, single-step parallel blocks and back-to-back duplicate approvals.
- **Views**: Build (blocks), Flow (clean diagram for sign-off) and Config (the step grid you'd configure in the tenant).
- **Exports**: Excel config table, PDF (flow diagram plus definition table), PNG, and a `.json` design file.

## Saving and sharing

Designs and templates save in your browser (localStorage). To share a design with a teammate, use **Export > Design file (.json)** and have them use **Open > Import design file**. You can also commit design files to the `designs/` folder in this repo so the team has one place to find them.

## Running it

It's a single static file, no build step.

- **GitHub Pages**: Settings > Pages > Deploy from branch > `main` / root.
- **Locally**: open `index.html` in a browser.

The Excel and PDF exports load SheetJS and jsPDF from cdnjs on first use, so they need an internet connection.

## Tips

- Click a palette block to append it to the end, or click a pill to attach it to the selected step.
- `Delete` removes the selected step, `Ctrl/Cmd + Z` undoes, `Ctrl/Cmd + S` saves.
- Drag a step back onto the palette to remove it.
