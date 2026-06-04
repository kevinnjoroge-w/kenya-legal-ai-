import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Scale, Brain, Shield, Globe, Zap, BookOpen, Users,
  Award, TrendingUp, Target, Check, ArrowRight, Quote
} from 'lucide-react';

const AboutPage = () => {
  const values = [
    {
      icon: Brain,
      title: 'Accuracy First',
      description: 'We believe legal research demands absolute precision. Every citation is verified, every source is real, and every answer is grounded in actual Kenyan law.'
    },
    {
      icon: Shield,
      title: 'Ethical AI',
      description: 'Legal ethics are not an afterthought. Our AI framework includes automatic disclaimers, court hierarchy awareness, and clear delineation between settled and debated law.'
    },
    {
      icon: Globe,
      title: 'Kenya First',
      description: 'We are not a generic AI with a Kenyan flag. Our models are trained exclusively on Kenyan jurisprudence, from the 2010 Constitution to the latest Court of Appeal decisions.'
    },
    {
      icon: Users,
      title: 'Built by Lawyers',
      description: 'Our team includes practicing advocates, constitutional scholars, and legal technologists who understand the real challenges of Kenyan legal practice.'
    },
  ];

  const team = [
    {
      name: 'Kevin Njoroge W.',
      role: 'Founder & CEO',
      bio: 'Advocate of the High Court of Kenya with a passion for legal technology and access to justice.',
      initials: 'KN'
    },
    {
      name: 'Dr. Sarah Wanjiku',
      role: 'Chief Legal Officer',
      bio: 'Former Associate at Oraro & Company. Specializes in constitutional and commercial law.',
      initials: 'SW'
    },
    {
      name: 'James Mwangi',
      role: 'Head of Engineering',
      bio: 'Ex-Google engineer with expertise in AI/ML systems and large language models.',
      initials: 'JM'
    },
    {
      name: 'Prof. Ben Sihanya',
      role: 'Academic Advisor',
      bio: 'Professor of Intellectual Property Law at the University of Nairobi.',
      initials: 'BS'
    },
  ];

  const stats = [
    { value: '2,000+', label: 'Active Users' },
    { value: '100K+', label: 'Documents Indexed' },
    { value: '99.7%', label: 'Citation Accuracy' },
    { value: '< 3 sec', label: 'Avg. Response Time' },
  ];

  return (
    <div className="min-h-screen pt-24 pb-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Hero */}
        <div className="text-center mb-20">
          <span className="inline-block px-4 py-1.5 rounded-full bg-[#2d5a47]/10 text-[#2d5a47] text-sm font-semibold mb-4">About Us</span>
          <h1 className="font-serif text-5xl lg:text-6xl font-bold text-[#1e3a2e] mb-6 text-balance">
            Building the Future of <span className="text-[#d4af37]">Legal Research</span> in Kenya
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Kenya Legal AI was born from a simple observation: Kenyan lawyers spend too much time searching for information 
            and too little time applying it. We're here to change that.
          </p>
        </div>

        {/* Mission */}
        <div className="bg-gradient-to-br from-[#1e3a2e] to-[#2d5a47] rounded-3xl p-12 lg:p-16 text-white mb-20">
          <div className="max-w-3xl mx-auto text-center">
            <Quote className="w-12 h-12 text-[#d4af37] mx-auto mb-6" />
            <p className="font-serif text-2xl lg:text-3xl leading-relaxed mb-6">
              "Our mission is to democratize access to legal information in Kenya. Every advocate, 
              every law student, every citizen deserves access to accurate, timely legal research — 
              not just those who can afford expensive databases."
            </p>
            <p className="text-gray-300">— Kevin Njoroge W., Founder</p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-20">
          {stats.map((stat, i) => (
            <div key={i} className="text-center p-6 bg-white rounded-2xl border border-gray-100 shadow-sm hover-lift">
              <div className="font-serif text-4xl font-bold text-[#2d5a47] mb-2">{stat.value}</div>
              <div className="text-sm text-gray-500">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Values */}
        <div className="mb-20">
          <h2 className="font-serif text-3xl font-bold text-[#1e3a2e] text-center mb-12">Our Values</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {values.map((value, i) => (
              <div key={i} className="bg-white rounded-2xl p-8 border border-gray-100 shadow-sm hover:shadow-lg transition-all hover-lift">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#f0f8f4] to-[#e8f5e9] flex items-center justify-center mb-4">
                  <value.icon className="w-6 h-6 text-[#2d5a47]" />
                </div>
                <h3 className="font-semibold text-xl text-[#1e3a2e] mb-3">{value.title}</h3>
                <p className="text-gray-600 leading-relaxed">{value.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Team */}
        <div className="mb-20">
          <h2 className="font-serif text-3xl font-bold text-[#1e3a2e] text-center mb-12">Our Team</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {team.map((member, i) => (
              <div key={i} className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm hover:shadow-lg transition-all text-center hover-lift">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#2d5a47] to-[#d4af37] flex items-center justify-center mx-auto mb-4 text-white font-bold text-xl">
                  {member.initials}
                </div>
                <h3 className="font-semibold text-lg text-[#1e3a2e]">{member.name}</h3>
                <p className="text-sm text-[#d4af37] font-medium mb-2">{member.role}</p>
                <p className="text-sm text-gray-600">{member.bio}</p>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="text-center">
          <h2 className="font-serif text-3xl font-bold text-[#1e3a2e] mb-4">Join the Movement</h2>
          <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
            Be part of the transformation of legal research in Kenya. Start your free trial today.
          </p>
          <Link to="/signup" className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-[#2d5a47] to-[#4a7c59] text-white font-semibold rounded-2xl shadow-xl shadow-green-900/20 hover:shadow-green-900/30 hover:-translate-y-1 transition-all btn-shine">
            Get Started Free <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;
