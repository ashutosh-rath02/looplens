import { Link, Outlet } from "react-router-dom";

export default function App() {
  return (
    <div className="min-h-full flex flex-col">
      <header className="border-b border-edge bg-panel/60 backdrop-blur sticky top-0 z-10">
        <div className="w-full px-6 py-3 flex items-center gap-3">
          <Link to="/" className="flex items-center gap-2 group">
            <span className="text-lg">🔁</span>
            <span className="font-semibold tracking-tight text-slate-100 group-hover:text-white">
              LoopLens
            </span>
          </Link>
          <span className="text-xs text-slate-500">Chrome DevTools for AI agent loops</span>
          <nav className="ml-auto flex items-center gap-4 text-sm">
            <Link to="/" className="text-slate-400 hover:text-slate-100">
              Runs
            </Link>
            <Link to="/compare" className="text-slate-400 hover:text-slate-100">
              Compare
            </Link>
          </nav>
        </div>
      </header>
      <main className="flex-1 w-full px-6 py-6">
        <Outlet />
      </main>
    </div>
  );
}
