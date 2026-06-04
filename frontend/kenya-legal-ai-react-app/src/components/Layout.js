import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Scale, X, Menu, ChevronDown, Crown, User, LogOut, 
  LayoutDashboard, Settings, Home, Zap, CreditCard, 
  Search, Users, Rocket, LogIn
} from 'lucide-react';

export const GlobalStyles = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:wght@600;700;800&display=swap');

    :root {
      --green-primary: #2d5a47;
      --green-light: #f0f8f4;
      --green-dark: #1e3a2e;
      --green-muted: #4a7c59;
      --gold-primary: #d4af37;
      --gold-light: #f9f6e8;
      --gold-dark: #b8860b;
      --red-primary: #8b2635;
      --cream: #faf9f6;
      --parchment: #f5f3ef;
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }
    html { scroll-behavior: smooth; }

    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: linear-gradient(180deg, #faf9f6 0%, #f5f3ef 100%);
      color: #18181b;
      -webkit-font-smoothing: antialiased;
      overflow-x: hidden;
    }

    .font-serif { font-family: 'Playfair Display', Georgia, serif; }

    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #f4f4f5; }
    ::-webkit-scrollbar-thumb { background: #d4d4d8; border-radius: 999px; }
    ::-webkit-scrollbar-thumb:hover { background: #a1a1aa; }

    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(30px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    @keyframes scaleIn {
      from { opacity: 0; transform: scale(0.95); }
      to { opacity: 1; transform: scale(1); }
    }
    @keyframes float {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-10px); }
    }
    @keyframes gradientShift {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }

    .animate-fadeInUp { animation: fadeInUp 0.8s ease-out forwards; }
    .animate-fadeIn { animation: fadeIn 0.5s ease forwards; }
    .animate-scaleIn { animation: scaleIn 0.4s ease forwards; }
    .animate-float { animation: float 6s ease-in-out infinite; }

    .delay-100 { animation-delay: 0.1s; }
    .delay-200 { animation-delay: 0.2s; }
    .delay-300 { animation-delay: 0.3s; }
    .delay-400 { animation-delay: 0.4s; }
    .delay-500 { animation-delay: 0.5s; }

    .gradient-text {
      background: linear-gradient(135deg, #2d5a47, #d4af37, #2d5a47);
      background-size: 200% auto;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      animation: gradientShift 4s ease infinite;
    }

    .glass-card {
      background: rgba(255, 255, 255, 0.7);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.3);
    }

    .hover-lift {
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .hover-lift:hover {
      transform: translateY(-4px);
      box-shadow: 0 20px 40px rgba(45, 90, 71, 0.12);
    }

    .btn-shine {
      position: relative;
      overflow: hidden;
    }
    .btn-shine::after {
      content: '';
      position: absolute;
      top: 0; left: -100%;
      width: 100%; height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
      transition: left 0.5s;
    }
    .btn-shine:hover::after {
      left: 100%;
    }

    .text-balance { text-wrap: balance; }
  `}</style>
);

export const Navbar = ({ isAuthenticated, user, onLogout }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { path: '/', label: 'Home', icon: Home },
    { path: '/features', label: 'Features', icon: Zap },
    { path: '/pricing', label: 'Pricing', icon: CreditCard },
    { path: '/research', label: 'Research', icon: Search },
    { path: '/about', label: 'About', icon: Users },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      scrolled 
        ? 'bg-white/95 backdrop-blur-xl shadow-lg shadow-green-900/5 border-b border-green-100/50' 
        : 'bg-transparent'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-18 py-3">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#2d5a47] to-[#4a7c59] flex items-center justify-center shadow-lg shadow-green-900/20 group-hover:shadow-green-900/30 transition-shadow">
              <Scale className="w-5 h-5 text-white" />
            </div>
            <div className="hidden sm:block">
              <span className="font-serif text-xl font-bold text-[#1e3a2e] tracking-tight">Kenya Legal AI</span>
              <span className="block text-[10px] font-semibold text-[#4a7c59] tracking-widest uppercase -mt-0.5">Powered by AI</span>
            </div>
          </Link>

          <div className="hidden lg:flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive(link.path)
                    ? 'bg-[#2d5a47]/10 text-[#2d5a47] shadow-sm'
                    : 'text-gray-600 hover:text-[#2d5a47] hover:bg-gray-100/50'
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          <div className="hidden lg:flex items-center gap-3">
            {isAuthenticated ? (
              <div className="relative">
                <button 
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-100 hover:bg-gray-200 transition-colors"
                >
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#2d5a47] to-[#d4af37] flex items-center justify-center">
                    <User className="w-4 h-4 text-white" />
                  </div>
                  <span className="text-sm font-medium text-gray-700">{user?.name || 'Account'}</span>
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                </button>
                {showUserMenu && (
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl shadow-green-900/10 border border-gray-100 overflow-hidden animate-scaleIn">
                    <div className="p-4 border-b border-gray-100">
                      <p className="font-semibold text-gray-900">{user?.name}</p>
                      <p className="text-xs text-gray-500">{user?.email}</p>
                      <span className="inline-flex items-center gap-1 mt-2 px-2 py-0.5 rounded-full bg-[#d4af37]/10 text-[#b8860b] text-xs font-semibold">
                        <Crown className="w-3 h-3" /> {user?.plan || 'Free'}
                      </span>
                    </div>
                    <Link to="/dashboard" className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 text-sm text-gray-700" onClick={() => setShowUserMenu(false)}>
                      <LayoutDashboard className="w-4 h-4" /> Dashboard
                    </Link>
                    <Link to="/settings" className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 text-sm text-gray-700" onClick={() => setShowUserMenu(false)}>
                      <Settings className="w-4 h-4" /> Settings
                    </Link>
                    <button 
                      onClick={() => { onLogout(); setShowUserMenu(false); }}
                      className="flex items-center gap-3 px-4 py-3 hover:bg-red-50 text-sm text-red-600 w-full"
                    >
                      <LogOut className="w-4 h-4" /> Sign Out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <>
                <Link to="/login" className="px-5 py-2.5 text-sm font-semibold text-[#2d5a47] hover:text-[#1e3a2e] transition-colors">
                  Sign In
                </Link>
                <Link to="/signup" className="px-5 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-[#2d5a47] to-[#4a7c59] rounded-xl shadow-lg shadow-green-900/20 hover:shadow-green-900/30 hover:-translate-y-0.5 transition-all btn-shine">
                  Get Started Free
                </Link>
              </>
            )}
          </div>

          <button 
            onClick={() => setIsOpen(!isOpen)}
            className="lg:hidden p-2 rounded-xl hover:bg-gray-100 transition-colors"
          >
            {isOpen ? <X className="w-6 h-6 text-gray-700" /> : <Menu className="w-6 h-6 text-gray-700" />}
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="lg:hidden bg-white/95 backdrop-blur-xl border-t border-gray-100 animate-fadeIn">
          <div className="px-4 py-6 space-y-2">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => setIsOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium ${
                  isActive(link.path) ? 'bg-[#2d5a47]/10 text-[#2d5a47]' : 'text-gray-600'
                }`}
              >
                <link.icon className="w-5 h-5" />
                {link.label}
              </Link>
            ))}
            <div className="pt-4 border-t border-gray-100 space-y-2">
              {isAuthenticated ? (
                <>
                  <Link to="/dashboard" onClick={() => setIsOpen(false)} className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-gray-700">
                    <LayoutDashboard className="w-5 h-5" /> Dashboard
                  </Link>
                  <button onClick={() => { onLogout(); setIsOpen(false); }} className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-red-600 w-full">
                    <LogOut className="w-5 h-5" /> Sign Out
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" onClick={() => setIsOpen(false)} className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-[#2d5a47]">
                    <LogIn className="w-5 h-5" /> Sign In
                  </Link>
                  <Link to="/signup" onClick={() => setIsOpen(false)} className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-white bg-gradient-to-r from-[#2d5a47] to-[#4a7c59]">
                    <Rocket className="w-5 h-5" /> Get Started Free
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

export const Footer = () => (
  <footer className="bg-[#1e3a2e] text-white">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="py-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#4a7c59] to-[#2d5a47] flex items-center justify-center">
              <Scale className="w-5 h-5 text-white" />
            </div>
            <span className="font-serif text-xl font-bold">Kenya Legal AI</span>
          </div>
          <p className="text-gray-400 text-sm leading-relaxed">
            AI-powered legal research for the Kenyan legal framework. Built by lawyers, for lawyers.
          </p>
          <div className="flex gap-3">
            {[Facebook, Twitter, Linkedin, Instagram].map((Icon, i) => (
              <a key={i} href="#" className="w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center hover:bg-[#d4af37]/20 hover:text-[#d4af37] transition-all">
                <Icon className="w-4 h-4" />
              </a>
            ))}
          </div>
        </div>

        <div>
          <h4 className="font-semibold text-sm uppercase tracking-wider text-[#d4af37] mb-4">Product</h4>
          <ul className="space-y-3">
            {['Features', 'Pricing', 'Research', 'API Access', 'Security'].map((item) => (
              <li key={item}>
                <Link to={`/${item.toLowerCase().replace(' ', '-')}`} className="text-gray-400 hover:text-white text-sm transition-colors">
                  {item}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h4 className="font-semibold text-sm uppercase tracking-wider text-[#d4af37] mb-4">Resources</h4>
          <ul className="space-y-3">
            {['Documentation', 'Blog', 'Case Studies', 'Webinars', 'Support'].map((item) => (
              <li key={item}>
                <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors">{item}</a>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h4 className="font-semibold text-sm uppercase tracking-wider text-[#d4af37] mb-4">Legal</h4>
          <ul className="space-y-3">
            {['Privacy Policy', 'Terms of Service', 'Cookie Policy', 'Disclaimer', 'Contact'].map((item) => (
              <li key={item}>
                <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors">{item}</a>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="py-6 border-t border-white/10 flex flex-col md:flex-row items-center justify-between gap-4">
        <p className="text-gray-500 text-sm">
          © 2026 Kenya Legal AI. All rights reserved. Not a substitute for professional legal advice.
        </p>
        <div className="flex items-center gap-6 text-gray-500 text-sm">
          <span className="flex items-center gap-2"><Shield className="w-4 h-4" /> SOC 2 Compliant</span>
          <span className="flex items-center gap-2"><Lock className="w-4 h-4" /> 256-bit Encryption</span>
        </div>
      </div>
    </div>
  </footer>
);

const Facebook = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
  </svg>
);

const Twitter = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
  </svg>
);

const Linkedin = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
  </svg>
);

const Instagram = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/>
  </svg>
);

const Shield = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
  </svg>
);

const Lock = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
    <path d="M7 11V7a5 5 0 0110 0v4"/>
  </svg>
);
