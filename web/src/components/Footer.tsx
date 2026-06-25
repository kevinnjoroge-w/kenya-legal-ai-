import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer className="border-t border-brand-800 bg-brand-900 text-brand-100">
      <div className="mx-auto grid max-w-7xl gap-10 px-5 py-14 sm:px-8 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
        <div>
          <div className="flex items-center gap-2 font-serif text-lg font-bold text-white">
            ⚖️ Kenya Legal AI
          </div>
          <p className="mt-3 max-w-xs text-sm text-brand-200">
            AI-powered legal research grounded in the Constitution, Acts of
            Parliament, and Kenyan case law — every answer backed by citations.
          </p>
        </div>

        <div>
          <h4 className="font-sans text-sm font-semibold text-white">Product</h4>
          <ul className="mt-3 space-y-2 text-sm">
            <li>
              <Link to="/features" className="hover:text-white">
                Features
              </Link>
            </li>
            <li>
              <Link to="/pricing" className="hover:text-white">
                Pricing
              </Link>
            </li>
            <li>
              <Link to="/chat" className="hover:text-white">
                Workspace
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <h4 className="font-sans text-sm font-semibold text-white">
            Data Sources
          </h4>
          <ul className="mt-3 space-y-2 text-sm">
            <li>
              <a
                href="http://kenyalaw.org"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-white"
              >
                Kenya Law
              </a>
            </li>
            <li>
              <a
                href="https://laws.africa"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-white"
              >
                Laws.Africa
              </a>
            </li>
            <li>
              <a
                href="https://judiciary.go.ke"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-white"
              >
                Judiciary of Kenya
              </a>
            </li>
          </ul>
        </div>

        <div>
          <h4 className="font-sans text-sm font-semibold text-white">Company</h4>
          <ul className="mt-3 space-y-2 text-sm">
            <li>
              <Link to="/about" className="hover:text-white">
                About
              </Link>
            </li>
            <li>
              <Link to="/login" className="hover:text-white">
                Sign in
              </Link>
            </li>
            <li>
              <Link to="/signup" className="hover:text-white">
                Create account
              </Link>
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-brand-800/70 px-5 py-6 text-center text-xs text-brand-300 sm:px-8">
        © 2026 Kenya Legal AI. A legal research tool — not a substitute for
        professional legal advice.
      </div>
    </footer>
  );
}
