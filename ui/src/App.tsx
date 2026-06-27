import { Link, Outlet } from "react-router-dom";

export default function App() {
  return (
    <div className="min-h-full flex flex-col">
      <header className="border-b border-edge bg-panel/60 backdrop-blur sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-5 py-3 flex items-center gap-3">
          <Link to="/" className="flex items-center gap-2 group">
            <span className="text-lg">🔁</span>
            <span className="font-semibold tracking-tight text-slate-100 group-hover:text-white">
              LoopLens
            </span>
          </Link>
          <span className="text-xs text-slate-500">Chrome DevTools for AI agent loops</span>
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto px-5 py-6">
        <Outlet />
      </main>
    </div>
  );
}
