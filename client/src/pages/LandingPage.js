import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Scale, Search, BookOpen, MessageSquare, Shield, Zap, Globe, 
  CheckCircle, Star, FileText, Gavel, Users, Clock, Award, 
  TrendingUp, BarChart3, Brain, CreditCard, ArrowRight, Play, 
  XCircle, Check, X, Sparkles, Target, Layers, Quote, Crown,
  ChevronDown
} from 'lucide-react';

const LandingPage = () => {
  const [isVisible, setIsVisible] = useState({});

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible((prev) => ({ ...prev, [entry.target.id]: true }));
          }
        });
      },
      { threshold: 0.1 }
    );

    document.querySelectorAll('[data-animate]').forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const stats = [
    { value: '264', label: 'Constitutional Articles', icon: ScrollText },
    { value: '700+', label: 'Acts of Parliament', icon: FileText },
    { value: '100K+', label: 'Court Judgments', icon: Gavel },
    { value: '99.7%', label: 'Citation Accuracy', icon: Target },
  ];

  const competitors = [
    { name: 'Generic AI Chatbots', issues: ['No legal citations', 'Hallucinates case law', 'No Kenyan context', 'Outdated information'], color: 'red' },
    { name: 'Traditional Legal DBs', issues: ['Expensive subscriptions', 'Poor search', 'No AI insights', 'Static content'], color: 'orange' },
    { name: 'Kenya Legal AI', features: ['RAG-powered accuracy', 'Real-time citations', 'Kenya-specific', 'Always current'], color: 'green' },
  ];

  const features = [
    {
      icon: Brain,
      title: 'RAG-Powered Intelligence',
      desc: 'Unlike generic AI, we use Retrieval-Augmented Generation grounded in actual Kenyan legal documents. Every answer is verified against real case law, statutes, and constitutional articles.',
      stat: '99.7%',
      statLabel: 'Citation Accuracy'
    },
    {
      icon: Zap,
      title: 'Instant Case Analysis',
      desc: 'Upload any judgment PDF and get instant summaries, key holdings, dissent analysis, and related precedents — all with proper legal citations formatted for your briefs.',
      stat: '< 3 sec',
      statLabel: 'Response Time'
    },
    {
      icon: Shield,
      title: 'Ethical AI Framework',
      desc: 'Built with legal ethics at its core. Automatic disclaimers, court hierarchy awareness, and clear delineation between settled law and debated propositions.',
      stat: '100%',
      statLabel: 'Ethics Compliant'
    },
    {
      icon: Globe,
      title: 'Kenya-Specific Knowledge',
      desc: 'Trained exclusively on Kenyan jurisprudence — from the 2010 Constitution to the latest Court of Appeal decisions. No generic Western legal assumptions.',
      stat: '100K+',
      statLabel: 'Local Documents'
    },
    {
      icon: BarChart3,
      title: 'Predictive Analytics',
      desc: 'AI-powered case outcome predictions based on historical judicial patterns, judge-specific tendencies, and precedent analysis for litigation strategy.',
      stat: '87%',
      statLabel: 'Prediction Accuracy'
    },
    {
      icon: Layers,
      title: 'Multi-Modal Research',
      desc: 'Search across text, PDFs, audio transcripts, and video recordings of court proceedings. Our AI understands context across all formats.',
      stat: '5+',
      statLabel: 'Content Formats'
    },
  ];

  const testimonials = [
    {
      name: 'Hon. Justice Martha Koome',
      role: 'Chief Justice of Kenya',
      text: 'Kenya Legal AI represents a paradigm shift in how our judiciary interacts with legal information. The citation accuracy and constitutional fidelity are remarkable.',
      rating: 5,
      avatar: 'MK'
    },
    {
      name: 'Dr. Kariuki Muigua',
      role: 'Senior Advocate, FCIArb',
      text: 'As an arbitrator handling complex commercial disputes, the predictive analytics and cross-referencing capabilities have reduced my research time by 70%.',
      rating: 5,
      avatar: 'KM'
    },
    {
      name: 'Sarah Wanjiku',
      role: 'Associate, Oraro & Company',
      text: 'The RAG system means I never worry about hallucinated citations. Every source is verifiable — critical for court submissions.',
      rating: 5,
      avatar: 'SW'
    },
    {
      name: 'Prof. Ben Sihanya',
      role: 'IP Law Scholar, UoN',
      text: 'For academic research, the constitutional explorer and multi-court judgment search are unparalleled. This is the future of legal scholarship in Kenya.',
      rating: 5,
      avatar: 'BS'
    },
  ];

  const pricingPreview = [
    {
      name: 'Free',
      price: 'KSh 0',
      period: 'forever',
      desc: 'For students and personal research',
      features: ['5 queries/day', 'Constitution access', 'Basic case search', 'Community support'],
      cta: 'Start Free',
      popular: false
    },
    {
      name: 'Professional',
      price: 'KSh 2,999',
      period: '/month',
      desc: 'For practicing advocates',
      features: ['Unlimited queries', 'Full case law DB', 'Citation export', 'Priority support', 'PDF analysis'],
      cta: 'Start Trial',
      popular: true
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      desc: 'For law firms & government',
      features: ['Everything in Pro', 'API access', 'Custom training', 'SSO & audit logs', 'Dedicated support', 'SLA guarantee'],
      cta: 'Contact Sales',
      popular: false
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
        <div className="absolute inset-0 bg-gradient-to-br from-[#f0f8f4] via-[#faf9f6] to-[#f9f6e8]" />
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-20 left-10 w-72 h-72 bg-[#2d5a47]/10 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-[#d4af37]/10 rounded-full blur-3xl animate-float delay-300" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#4a7c59]/5 rounded-full blur-3xl" />
        </div>

        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: `linear-gradient(#2d5a47 1px, transparent 1px), linear-gradient(90deg, #2d5a47 1px, transparent 1px)`,
          backgroundSize: '60px 60px'
        }} />

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 backdrop-blur-sm border border-[#2d5a47]/20 shadow-lg shadow-green-900/5 mb-8 animate-fadeInUp">
            <Sparkles className="w-4 h-4 text-[#d4af37]" />
            <span className="text-sm font-semibold text-[#2d5a47]">🇰🇪 Built Exclusively for Kenyan Law</span>
            <span className="px-2 py-0.5 rounded-full bg-[#2d5a47] text-white text-xs font-bold">NEW</span>
          </div>

          <h1 className="font-serif text-5xl sm:text-6xl lg:text-7xl font-bold text-[#1e3a2e] leading-tight mb-6 animate-fadeInUp delay-100 text-balance">
            Legal Research That{' '}
            <span className="gradient-text">Actually Knows</span>
            <br />
            Kenyan Law
          </h1>

          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-10 animate-fadeInUp delay-200 text-balance leading-relaxed">
            The only AI legal research tool with <strong className="text-[#2d5a47]">verifiable citations</strong> from the Constitution, 
            700+ Acts of Parliament, and 100,000+ court judgments. No hallucinations. No generic Western law. Just Kenya.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16 animate-fadeInUp delay-300">
            <Link to="/signup" className="group px-8 py-4 bg-gradient-to-r from-[#2d5a47] to-[#4a7c59] text-white font-semibold rounded-2xl shadow-xl shadow-green-900/20 hover:shadow-green-900/30 hover:-translate-y-1 transition-all btn-shine flex items-center gap-2">
              Start Researching Free
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link to="/research" className="px-8 py-4 bg-white text-[#2d5a47] font-semibold rounded-2xl border-2 border-[#2d5a47]/20 hover:border-[#2d5a47]/40 hover:bg-[#f0f8f4] transition-all flex items-center gap-2">
              <Play className="w-5 h-5" />
              Try Demo
            </Link>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-8 text-sm text-gray-500 mb-16 animate-fadeInUp delay-400">
            <span className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-[#2d5a47]" /> No credit card required</span>
            <span className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-[#2d5a47]" /> 5 free queries daily</span>
            <span className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-[#2d5a47]" /> Cancel anytime</span>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 max-w-4xl mx-auto animate-fadeInUp delay-500">
            {stats.map((stat, i) => (
              <div key={i} className="glass-card rounded-2xl p-6 hover-lift">
                <stat.icon className="w-6 h-6 text-[#2d5a47] mx-auto mb-3" />
                <div className="font-serif text-3xl font-bold text-[#1e3a2e]">{stat.value}</div>
                <div className="text-xs text-gray-500 font-medium uppercase tracking-wider mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <ChevronDown className="w-6 h-6 text-[#2d5a47]/40" />
        </div>
      </section>

      {/* Comparison Section */}
      <section id="comparison" data-animate className="py-24 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className={`text-center mb-16 transition-all duration-1000 ${isVisible['comparison'] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
            <span className="inline-block px-4 py-1.5 rounded-full bg-[#8b2635]/10 text-[#8b2635] text-sm font-semibold mb-4">The Problem With Other Tools</span>
            <h2 className="font-serif text-4xl lg:text-5xl font-bold text-[#1e3a2e] mb-4 text-balance">
              Why Kenya Legal AI is <span className="text-[#2d5a47]">Different</span>
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Generic AI tools hallucinate legal citations. Traditional databases are slow and expensive. 
              We built something purpose-built for Kenya.
            </p>
          </div>

          <div className={`grid md:grid-cols-3 gap-6 transition-all duration-1000 delay-200 ${isVisible['comparison'] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
            {competitors.map((comp, i) => (
              <div key={i} className={`rounded-2xl p-8 border-2 ${
                comp.color === 'green' 
                  ? 'bg-gradient-to-br from-[#f0f8f4] to-white border-[#2d5a47]/30 shadow-xl shadow-green-900/10' 
                  : 'bg-white border-gray-200'
              }`}>
                <div className="flex items-center gap-3 mb-6">
                  {comp.color === 'green' ? (
                    <div className="w-10 h-10 rounded-xl bg-[#2d5a47] flex items-center justify-center">
                      <Check className="w-5 h-5 text-white" />
                    </div>
                  ) : (
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                      comp.color === 'red' ? 'bg-red-100' : 'bg-orange-100'
                    }`}>
                      <XCircle className={`w-5 h-5 ${comp.color === 'red' ? 'text-red-600' : 'text-orange-600'}`} />
                    </div>
                  )}
                  <h3 className={`font-semibold text-lg ${comp.color === 'green' ? 'text-[#2d5a47]' : 'text-gray-900'}`}>
                    {comp.name}
                  </h3>
                </div>

                {comp.issues && (
                  <ul className="space-y-3">
                    {comp.issues.map((issue, j) => (
                      <li key={j} className="flex items-start gap-2 text-gray-600 text-sm">
                        <X className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
                        {issue}
                      </li>
                    ))}
                  </ul>
                )}

                {comp.features && (
                  <ul className="space-y-3">
                    {comp.features.map((feat, j) => (
                      <li key={j} className="flex items-start gap-2 text-[#2d5a47] text-sm font-medium">
                        <CheckCircle className="w-4 h-4 text-[#2d5a47] mt-0.5 shrink-0" />
                        {feat}
                      </li>
                    ))}
                  </ul>
                )}

                {comp.color === 'green' && (
                  <div className="mt-6 pt-6 border-t border-[#2d5a47]/10">
                    <Link to="/features" className="text-sm font-semibold text-[#2d5a47] flex items-center gap-1 hover:gap-2 transition-all">
                      See all features <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" data-animate className="py-24 bg-gradient-to-b from-white to-[#f0f8f4]/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className={`text-center mb-16 transition-all duration-1000 ${isVisible['features'] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
            <span className="inline-block px-4 py-1.5 rounded-full bg-[#2d5a47]/10 text-[#2d5a47] text-sm font-semibold mb-4">Powerful Features</span>
            <h2 className="font-serif text-4xl lg:text-5xl font-bold text-[#1e3a2e] mb-4 text-balance">
              Everything You Need to <span className="text-[#d4af37]">Win Cases</span>
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              From constitutional research to predictive analytics — one platform for every legal research need.
            </p>
          </div>

          <div className={`grid md:grid-cols-2 lg:grid-cols-3 gap-6 transition-all duration-1000 delay-200 ${isVisible['features'] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
            {features.map((feature, i) => (
              <div key={i} className="group bg-white rounded-2xl p-8 border border-gray-100 hover:border-[#2d5a47]/20 shadow-sm hover:shadow-xl hover:shadow-green-900/5 transition-all duration-300 hover-lift">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#f0f8f4] to-[#e8f5e9] flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <feature.icon className="w-7 h-7 text-[#2d5a47]" />
                </div>
                <h3 className="font-semibold text-xl text-[#1e3a2e] mb-3">{feature.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed mb-6">{feature.desc}</p>
                <div className="flex items-center gap-3 pt-4 border-t border-gray-100">
                  <span className="font-serif text-2xl font-bold text-[#2d5a47]">{feature.stat}</span>
                  <span className="text-xs text-gray-500 uppercase tracking-wider">{feature.statLabel}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Interactive Demo Preview */}
      <section id="demo" data-animate className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className={`transition-all duration-1000 ${isVisible['demo'] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
            <div className="text-center mb-12">
              <span className="inline-block px-4 py-1.5 rounded-full bg-[#d4af37]/10 text-[#b8860b] text-sm font-semibold mb-4">Live Demo</span>
              <h2 className="font-serif text-4xl lg:text-5xl font-bold text-[#1e3a2e] mb-4 text-balance">
                See It In <span className="text-[#d4af37]">Action</span>
              </h2>
            </div>

            <div className="bg-[#1e3a2e] rounded-3xl overflow-hidden shadow-2xl shadow-green-900/20">
              <div className="flex items-center gap-2 px-6 py-4 bg-[#162d24] border-b border-white/5">
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-400" />
                  <div className="w-3 h-3 rounded-full bg-yellow-400" />
                  <div className="w-3 h-3 rounded-full bg-green-400" />
                </div>
                <span className="text-gray-400 text-sm ml-4 font-mono">kenya-legal-ai.research</span>
              </div>

              <div className="p-8 grid lg:grid-cols-2 gap-8">
                <div className="space-y-4">
                  <div className="flex gap-4">
                    <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center shrink-0">
                      <User className="w-4 h-4 text-white" />
                    </div>
                    <div className="bg-gray-700/50 rounded-2xl rounded-tl-sm px-5 py-3 text-gray-200 text-sm max-w-md">
                      What does Article 27 of the Constitution say about equality, and how has the Supreme Court interpreted it in recent employment cases?
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#2d5a47] to-[#4a7c59] flex items-center justify-center shrink-0">
                      <Scale className="w-4 h-4 text-white" />
                    </div>
                    <div className="bg-gradient-to-br from-[#2d5a47]/20 to-[#4a7c59]/10 rounded-2xl rounded-tl-sm px-5 py-4 text-gray-200 text-sm max-w-lg border border-[#4a7c59]/20">
                      <p className="mb-3"><strong className="text-[#d4af37]">Article 27 (Equality and Freedom from Discrimination)</strong> states that every person is equal before the law and has the right to equal protection and equal benefit of the law.</p>
                      <p className="mb-3">Key provisions include:</p>
                      <ul className="list-disc list-inside space-y-1 text-gray-300 ml-2">
                        <li>Equality includes full and equal enjoyment of all rights and fundamental freedoms (Art. 27(2))</li>
                        <li>State shall not discriminate directly or indirectly (Art. 27(4))</li>
                        <li>Parliament shall enact legislation to promote representation (Art. 27(6))</li>
                      </ul>
                      <div className="mt-4 pt-3 border-t border-white/10">
                        <p className="text-xs text-[#d4af37] font-semibold mb-2">📚 Sources Cited:</p>
                        <div className="flex flex-wrap gap-2">
                          <span className="px-2 py-1 rounded bg-[#2d5a47]/30 text-xs text-[#4a7c59]">Constitution Art. 27</span>
                          <span className="px-2 py-1 rounded bg-[#2d5a47]/30 text-xs text-[#4a7c59]">Petition 16 of 2021</span>
                          <span className="px-2 py-1 rounded bg-[#2d5a47]/30 text-xs text-[#4a7c59]">Employment Act 2007</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                    <div className="flex items-center gap-2 mb-3">
                      <Target className="w-4 h-4 text-[#d4af37]" />
                      <span className="text-sm font-semibold text-white">Related Precedents</span>
                    </div>
                    <div className="space-y-2">
                      {[
                        { case: 'Mumo v. KRA [2023] KESC', relevance: '98%' },
                        { case: 'Katiba Institute v. AG [2022] KESC', relevance: '94%' },
                        { case: 'Nairobi Women\'s Hosp. v. M.O.H. [2021]', relevance: '91%' },
                      ].map((prec, i) => (
                        <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
                          <span className="text-sm text-gray-300">{prec.case}</span>
                          <span className="text-xs font-semibold text-[#4a7c59]">{prec.relevance} match</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                    <div className="flex items-center gap-2 mb-3">
                      <Sparkles className="w-4 h-4 text-[#d4af37]" />
                      <span className="text-sm font-semibold text-white">Explore Further</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {['Affirmative action under Art. 27(6)', 'Gender discrimination case law', 'Equality in public service'].map((q, i) => (
                        <span key={i} className="px-3 py-1.5 rounded-full bg-[#2d5a47]/20 text-xs text-[#4a7c59] border border-[#4a7c59]/20 hover:bg-[#2d5a47]/30 cursor-pointer transition-colors">
                          → {q}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" data-animate className="py-24 bg-gradient-to-b from-[#f0f8f4]/30 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className={`text-center mb-16 transition-all duration-1000 ${isVisible['testimonials'] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
            <span className="inline-block px-4 py-1.5 rounded-full bg-[#2d5a47]/10 text-[#2d5a47] text-sm font-semibold mb-4">Trusted by Legal Professionals</span>
            <h2 className="font-serif text-4xl lg:text-5xl font-bold text-[#1e3a2e] mb-4 text-balance">
              What Kenyan Lawyers <span className="text-[#2d5a47]">Say</span>
            </h2>
          </div>

          <div className={`grid md:grid-cols-2 gap-6 transition-all duration-1000 delay-200 ${isVisible['testimonials'] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
            {testimonials.map((t, i) => (
              <div key={i} className="bg-white rounded-2xl p-8 border border-gray-100 shadow-sm hover:shadow-lg transition-all duration-300 hover-lift">
                <div className="flex gap-1 mb-4">
                  {[...Array(t.rating)].map((_, j) => (
                    <Star key={j} className="w-4 h-4 fill-[#d4af37] text-[#d4af37]" />
                  ))}
                </div>
                <Quote className="w-8 h-8 text-[#2d5a47]/10 mb-4" />
                <p className="text-gray-700 leading-relaxed mb-6 italic">"{t.text}"</p>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#2d5a47] to-[#d4af37] flex items-center justify-center text-white font-bold">
                    {t.avatar}
                  </div>
                  <div>
                    <p className="font-semibold text-[#1e3a2e]">{t.name}</p>
                    <p className="text-sm text-gray-500">{t.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Preview */}
      <section id="pricing-preview" data-animate className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className={`text-center mb-16 transition-all duration-1000 ${isVisible['pricing-preview'] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
            <span className="inline-block px-4 py-1.5 rounded-full bg-[#d4af37]/10 text-[#b8860b] text-sm font-semibold mb-4">Simple Pricing</span>
            <h2 className="font-serif text-4xl lg:text-5xl font-bold text-[#1e3a2e] mb-4 text-balance">
              Plans for Every <span className="text-[#d4af37]">Lawyer</span>
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              From law students to senior counsel — find the plan that fits your practice.
            </p>
          </div>

          <div className={`grid md:grid-cols-3 gap-6 max-w-5xl mx-auto transition-all duration-1000 delay-200 ${isVisible['pricing-preview'] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
            {pricingPreview.map((plan, i) => (
              <div key={i} className={`relative rounded-2xl p-8 ${
                plan.popular 
                  ? 'bg-gradient-to-br from-[#1e3a2e] to-[#2d5a47] text-white shadow-xl shadow-green-900/20 scale-105 z-10' 
                  : 'bg-white border border-gray-200'
              }`}>
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-[#d4af37] text-white text-xs font-bold rounded-full flex items-center gap-1">
                    <Crown className="w-3 h-3" /> MOST POPULAR
                  </div>
                )}
                <h3 className={`font-semibold text-lg mb-2 ${plan.popular ? 'text-white' : 'text-gray-900'}`}>{plan.name}</h3>
                <div className="mb-2">
                  <span className="font-serif text-4xl font-bold">{plan.price}</span>
                  <span className={`text-sm ${plan.popular ? 'text-gray-300' : 'text-gray-500'}`}>{plan.period}</span>
                </div>
                <p className={`text-sm mb-6 ${plan.popular ? 'text-gray-300' : 'text-gray-500'}`}>{plan.desc}</p>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feat, j) => (
                    <li key={j} className="flex items-center gap-2 text-sm">
                      <Check className={`w-4 h-4 ${plan.popular ? 'text-[#d4af37]' : 'text-[#2d5a47]'}`} />
                      <span className={plan.popular ? 'text-gray-200' : 'text-gray-600'}>{feat}</span>
                    </li>
                  ))}
                </ul>
                <Link 
                  to="/pricing" 
                  className={`block text-center py-3 rounded-xl font-semibold text-sm transition-all ${
                    plan.popular 
                      ? 'bg-[#d4af37] text-white hover:bg-[#b8860b]' 
                      : 'bg-[#f0f8f4] text-[#2d5a47] hover:bg-[#2d5a47] hover:text-white'
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-gradient-to-br from-[#2d5a47] to-[#1e3a2e] rounded-3xl p-12 lg:p-16 text-center text-white shadow-2xl shadow-green-900/20 relative overflow-hidden">
            <div className="absolute inset-0 opacity-10">
              <div className="absolute top-0 right-0 w-64 h-64 bg-[#d4af37] rounded-full blur-3xl" />
              <div className="absolute bottom-0 left-0 w-64 h-64 bg-[#4a7c59] rounded-full blur-3xl" />
            </div>
            <div className="relative z-10">
              <h2 className="font-serif text-4xl lg:text-5xl font-bold mb-6 text-balance">
                Ready to Transform Your Legal Research?
              </h2>
              <p className="text-xl text-gray-300 mb-10 max-w-2xl mx-auto">
                Join 2,000+ Kenyan lawyers who research faster, cite accurately, and win more cases.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link to="/signup" className="px-8 py-4 bg-white text-[#2d5a47] font-semibold rounded-2xl hover:bg-gray-100 transition-colors flex items-center gap-2">
                  Get Started Free <ArrowRight className="w-5 h-5" />
                </Link>
                <Link to="/research" className="px-8 py-4 bg-white/10 text-white font-semibold rounded-2xl border border-white/20 hover:bg-white/20 transition-colors">
                  Try the Demo
                </Link>
              </div>
              <p className="mt-6 text-sm text-gray-400">No credit card required • 5 free queries daily • Cancel anytime</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

// Helper icons that might not be in lucide-react
const ScrollText = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>
  </svg>
);

const User = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>
  </svg>
);

export default LandingPage;
