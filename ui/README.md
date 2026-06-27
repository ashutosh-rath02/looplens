# LoopLens UI

React + Vite + TypeScript + Tailwind dashboard. **Scaffolded in Phase 4.**

Planned structure:

```
ui/
  package.json
  src/
    main.tsx
    App.tsx
    pages/
      RunsPage.tsx
      RunDetailPage.tsx
    components/
      MetricsBar.tsx
      Timeline.tsx
      WarningCard.tsx
      EventDrawer.tsx
```

In dev, Vite runs the UI and proxies `/api` to the backend on `:8765`. For
`looplens dev` / production, the UI is built to `ui/dist/` and served by the
FastAPI backend so everything lives on a single URL (`http://localhost:8765`).
