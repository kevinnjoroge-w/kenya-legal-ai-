import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Brain, Search, FileText, Zap, BarChart3, Shield, 
  Check, Layers, ArrowRight, MessageSquare, BookOpen,
  Gavel, Landmark, ScrollText, Target, Clock, Database
} from 'lucide-react';

const FeaturesPage = () => {
  const features = [
    {
      icon: Brain,
      title: 'RAG-Powered Legal AI',
      description: 'Our Retrieval-Augmented Generation system grounds every response in actual Kenyan legal documents. Unlike generic AI that hallucinates citations, we verify every claim against real case law, statutes, and constitutional articles.',
      benefits: ['99.7% citation accuracy', 'Zero hallucinations', 'Real-time source verification', 'Constitutional fidelity'],
      color: 'from-[#f0f8f4] to-[#e8f5e9]'
    },
    {
      icon: Search,
      title: 'Advanced Case Law Search',
      description: 'Search across 100,000+ court judgments from the Supreme Court, Court of Appeal, High Court, and specialized tribunals. Filter by court, date, judge, subject matter, and legal principles.',
      benefits: ['Multi-court coverage', 'Semantic search', 'Citation network analysis', 'Judge-specific insights'],
      color: 'from-[#f9f6e8] to-[#fefce8]'
    },
    {
      icon: FileText,
      title: 'Constitution Explorer',
      description: 'Interactive exploration of the Constitution of Kenya 2010. Navigate by chapter, article, or clause. Cross-reference with related statutes and judicial interpretations.',
      benefits: ['Chapter navigation', 'Cross-referencing', 'Judicial interpretations', 'Amendment history'],
      color: 'from-[#fef2f2] to-[#fef9f3]'
    },
    {
      icon: Zap,
      title: 'Document Analysis',
      description: 'Upload any legal document — judgments, contracts, pleadings — and get instant AI-powered analysis. Extract key holdings, identify risks, generate summaries, and find related precedents.',
      benefits: ['PDF & Word support', 'Key holding extraction', 'Risk identification', 'Precedent matching'],
      color: 'from-[#f0f8f4] to-[#e0f2fe]'
    },
    {
      icon: BarChart3,
      title: 'Predictive Analytics',
      description: 'AI-powered case outcome predictions based on historical judicial patterns. Analyze judge-specific tendencies, court trends, and precedent strength for litigation strategy.',
      benefits: ['Outcome predictions', 'Judge analytics', 'Court trend analysis', 'Settlement recommendations'],
      color: 'from-[#faf5ff] to-[#f3e8ff]'
    },
    {
      icon: Shield,
      title: 'Ethical AI Framework',
      description: 'Built with legal ethics at its core. Automatic disclaimers distinguish between settled law and debated propositions. Court hierarchy awareness ensures proper precedent weighting.',
      benefits: ['Auto-disclaimers', 'Court hierarchy awareness', 'Ethics compliance', 'Bias detection'],
      color: 'from-[#f0fdf4] to-[#dcfce7]'
    },
  ];

  const integrations = [
    'Microsoft Word', 'Google Docs', 'Clio', 'PracticePanther', 'Dropbox', 'OneDrive',
    'Slack', 'Teams', 'Notion', 'Zapier'
  ];

  return (
    <div className="min-h-screen pt-24 pb-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-20">
          <span className="inline-block px-4 py-1.5 rounded-full bg-[#2d5a47]/10 text-[#2d5a47] text-sm font-semibold mb-4">Features</span>
          <h1 className="font-serif text-5xl lg:text-6xl font-bold text-[#1e3a2e] mb-6 text-balance">
            Everything You Need to <span className="text-[#d4af37]">Win</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            From constitutional research to predictive litigation analytics — one platform that understands Kenyan law like no other.
          </p>
        </div>

        {/* Features Grid */}
        <div className="space-y-24">
          {features.map((feature, i) => (
            <div key={i} className={`grid lg:grid-cols-2 gap-12 items-center ${i % 2 === 1 ? '' : ''}`}>
              <div className={i % 2 === 1 ? 'lg:order-2' : ''}>
                <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-6`}>
                  <feature.icon className="w-8 h-8 text-[#2d5a47]" />
                </div>
                <h2 className="font-serif text-3xl font-bold text-[#1e3a2e] mb-4">{feature.title}</h2>
                <p className="text-gray-600 leading-relaxed mb-6">{feature.description}</p>
                <ul className="space-y-3">
                  {feature.benefits.map((benefit, j) => (
                    <li key={j} className="flex items-center gap-3">
                      <div className="w-6 h-6 rounded-full bg-[#2d5a47]/10 flex items-center justify-center">
                        <Check className="w-4 h-4 text-[#2d5a47]" />
                      </div>
                      <span className="text-gray-700">{benefit}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className={`bg-gradient-to-br from-[#f0f8f4] to-white rounded-3xl p-8 border border-gray-100 shadow-lg ${i % 2 === 1 ? 'lg:order-1' : ''}`}>
                <div className="aspect-video bg-gradient-to-br from-[#1e3a2e] to-[#2d5a47] rounded-2xl flex items-center justify-center">
                  <feature.icon className="w-20 h-20 text-white/20" />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Integration Section */}
        <div className="mt-24 text-center">
          <h2 className="font-serif text-3xl font-bold text-[#1e3a2e] mb-4">Works With Your Workflow</h2>
          <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
            Seamlessly integrate Kenya Legal AI into your existing tools and processes.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            {integrations.map((tool, i) => (
              <div key={i} className="px-6 py-3 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center">
                  <Layers className="w-4 h-4 text-gray-600" />
                </div>
                <span className="font-medium text-gray-700">{tool}</span>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="mt-20 text-center">
          <Link to="/signup" className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-[#2d5a47] to-[#4a7c59] text-white font-semibold rounded-2xl shadow-xl shadow-green-900/20 hover:shadow-green-900/30 hover:-translate-y-1 transition-all btn-shine">
            Start Your Free Trial <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </div>
    </div>
  );
};

export default FeaturesPage;
