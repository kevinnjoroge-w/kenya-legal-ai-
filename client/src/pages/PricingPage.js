import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Check, X, Crown, Diamond, Gem, ChevronDown, ChevronUp,
  ArrowRight, Sparkles, Shield, Zap, HelpCircle
} from 'lucide-react';

const PricingPage = () => {
  const [billing, setBilling] = useState('monthly');
  const [openFaq, setOpenFaq] = useState(null);

  const plans = [
    {
      name: 'Free',
      icon: Gem,
      monthlyPrice: 0,
      yearlyPrice: 0,
      description: 'Perfect for students and personal research',
      features: [
        '5 AI queries per day',
        'Constitution full access',
        'Basic case law search',
        'Community support',
        'Web access only',
      ],
      notIncluded: [
        'PDF document analysis',
        'Citation export',
        'API access',
        'Priority support',
      ],
      cta: 'Start Free',
      popular: false,
      color: 'gray'
    },
    {
      name: 'Professional',
      icon: Crown,
      monthlyPrice: 2999,
      yearlyPrice: 29990,
      description: 'For practicing advocates and small firms',
      features: [
        'Unlimited AI queries',
        'Full case law database',
        'PDF & Word analysis',
        'Citation export (Bluebook, OSCOLA)',
        'Priority email support',
        'Research history & bookmarks',
        'Mobile app access',
        '2 team members',
      ],
      notIncluded: [
        'API access',
        'Custom AI training',
        'SSO & audit logs',
      ],
      cta: 'Start 14-Day Trial',
      popular: true,
      color: 'gold'
    },
    {
      name: 'Enterprise',
      icon: Diamond,
      monthlyPrice: null,
      yearlyPrice: null,
      description: 'For law firms, government & corporations',
      features: [
        'Everything in Professional',
        'Unlimited team members',
        'REST API access',
        'Custom AI model training',
        'SSO & SAML integration',
        'Audit logs & compliance',
        'Dedicated account manager',
        'SLA with 99.9% uptime',
        'On-premise deployment option',
      ],
      notIncluded: [],
      cta: 'Contact Sales',
      popular: false,
      color: 'green'
    },
  ];

  const faqs = [
    { q: 'Can I switch plans anytime?', a: 'Yes, you can upgrade, downgrade, or cancel your subscription at any time. Changes take effect immediately.' },
    { q: 'Is there a free trial for paid plans?', a: 'Professional plans come with a 14-day free trial. No credit card required to start.' },
    { q: 'What payment methods do you accept?', a: 'We accept M-Pesa, bank transfer, Visa, Mastercard, and American Express.' },
    { q: 'Do you offer discounts for law students?', a: 'Yes! Students with a valid .ac.ke email get 50% off Professional plans.' },
    { q: 'Is my data secure?', a: 'Absolutely. We use 256-bit encryption, are SOC 2 compliant, and never train our AI on your private queries.' },
  ];

  return (
    <div className="min-h-screen pt-24 pb-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <span className="inline-block px-4 py-1.5 rounded-full bg-[#d4af37]/10 text-[#b8860b] text-sm font-semibold mb-4">Pricing</span>
          <h1 className="font-serif text-5xl lg:text-6xl font-bold text-[#1e3a2e] mb-6 text-balance">
            Simple, Transparent <span className="text-[#d4af37]">Pricing</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
            Choose the plan that fits your practice. All plans include our core AI research engine.
          </p>

          {/* Billing Toggle */}
          <div className="inline-flex items-center gap-4 bg-gray-100 rounded-full p-1.5">
            <button 
              onClick={() => setBilling('monthly')}
              className={`px-6 py-2.5 rounded-full text-sm font-semibold transition-all ${
                billing === 'monthly' ? 'bg-white text-[#2d5a47] shadow-sm' : 'text-gray-500'
              }`}
            >
              Monthly
            </button>
            <button 
              onClick={() => setBilling('yearly')}
              className={`px-6 py-2.5 rounded-full text-sm font-semibold transition-all flex items-center gap-2 ${
                billing === 'yearly' ? 'bg-white text-[#2d5a47] shadow-sm' : 'text-gray-500'
              }`}
            >
              Yearly
              <span className="px-2 py-0.5 bg-[#d4af37]/10 text-[#b8860b] text-xs rounded-full">Save 17%</span>
            </button>
          </div>
        </div>

        {/* Plans */}
        <div className="grid md:grid-cols-3 gap-6 max-w-6xl mx-auto mb-20">
          {plans.map((plan, i) => (
            <div key={i} className={`relative rounded-2xl p-8 ${
              plan.popular 
                ? 'bg-gradient-to-br from-[#1e3a2e] to-[#2d5a47] text-white shadow-xl shadow-green-900/20 scale-105 z-10' 
                : 'bg-white border border-gray-200 hover:border-[#2d5a47]/30 transition-colors'
            }`}>
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-[#d4af37] text-white text-xs font-bold rounded-full flex items-center gap-1">
                  <Sparkles className="w-3 h-3" /> MOST POPULAR
                </div>
              )}

              <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  plan.popular ? 'bg-white/10' : 'bg-[#f0f8f4]'
                }`}>
                  <plan.icon className={`w-5 h-5 ${plan.popular ? 'text-[#d4af37]' : 'text-[#2d5a47]'}`} />
                </div>
                <h3 className={`font-semibold text-xl ${plan.popular ? 'text-white' : 'text-gray-900'}`}>{plan.name}</h3>
              </div>

              <div className="mb-2">
                {plan.monthlyPrice !== null ? (
                  <>
                    <span className="font-serif text-4xl font-bold">
                      KSh {billing === 'monthly' ? plan.monthlyPrice.toLocaleString() : plan.yearlyPrice.toLocaleString()}
                    </span>
                    <span className={`text-sm ${plan.popular ? 'text-gray-300' : 'text-gray-500'}`}>
                      /{billing === 'monthly' ? 'month' : 'year'}
                    </span>
                  </>
                ) : (
                  <span className="font-serif text-4xl font-bold">Custom</span>
                )}
              </div>
              <p className={`text-sm mb-8 ${plan.popular ? 'text-gray-300' : 'text-gray-500'}`}>{plan.description}</p>

              <ul className="space-y-3 mb-8">
                {plan.features.map((feat, j) => (
                  <li key={j} className="flex items-center gap-3 text-sm">
                    <Check className={`w-4 h-4 ${plan.popular ? 'text-[#d4af37]' : 'text-[#2d5a47]'}`} />
                    <span className={plan.popular ? 'text-gray-200' : 'text-gray-700'}>{feat}</span>
                  </li>
                ))}
                {plan.notIncluded.map((feat, j) => (
                  <li key={j} className="flex items-center gap-3 text-sm opacity-50">
                    <X className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-500">{feat}</span>
                  </li>
                ))}
              </ul>

              <Link 
                to={plan.name === 'Enterprise' ? '/contact' : '/signup'}
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

        {/* FAQ */}
        <div className="max-w-3xl mx-auto">
          <h2 className="font-serif text-3xl font-bold text-[#1e3a2e] text-center mb-8">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {faqs.map((faq, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <button 
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full flex items-center justify-between p-6 text-left"
                >
                  <span className="font-semibold text-gray-900">{faq.q}</span>
                  {openFaq === i ? <ChevronUp className="w-5 h-5 text-gray-500" /> : <ChevronDown className="w-5 h-5 text-gray-500" />}
                </button>
                {openFaq === i && (
                  <div className="px-6 pb-6 text-gray-600 leading-relaxed">
                    {faq.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="mt-20 text-center">
          <p className="text-gray-600 mb-4">Still have questions?</p>
          <Link to="/contact" className="inline-flex items-center gap-2 text-[#2d5a47] font-semibold hover:gap-3 transition-all">
            Contact our sales team <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
};

export default PricingPage;
