import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  LayoutDashboard, MessageSquare, Search, FileText, Bookmark,
  Settings, CreditCard, Bell, LogOut, Scale, TrendingUp,
  Clock, Zap, ArrowRight, ChevronRight, Star, Download,
  Share2, MoreHorizontal, BarChart3, Target, Activity
} from 'lucide-react';

const DashboardPage = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('overview');

  const stats = [
    { label: 'Queries This Month', value: '247', change: '+12%', icon: MessageSquare },
    { label: 'Documents Analyzed', value: '18', change: '+5%', icon: FileText },
    { label: 'Saved Cases', value: '34', change: '+8%', icon: Bookmark },
    { label: 'Research Hours Saved', value: '42h', change: '+23%', icon: Clock },
  ];

  const recentQueries = [
    { query: 'Article 27 equality provisions in employment', date: '2 hours ago', type: 'Constitution' },
    { query: 'Supreme Court land rights decisions 2023', date: 'Yesterday', type: 'Case Law' },
    { query: 'Employment Act termination procedures', date: '3 days ago', type: 'Statute' },
    { query: 'Judicial review process High Court', date: '1 week ago', type: 'Procedure' },
  ];

  const savedCases = [
    { title: 'Mumo v. KRA [2023] KESC', court: 'Supreme Court', date: '2023', relevance: '98%' },
    { title: 'Katiba Institute v. AG [2022] KESC', court: 'Supreme Court', date: '2022', relevance: '94%' },
    { title: 'Nairobi Women\'s Hospital v. MOH', court: 'High Court', date: '2021', relevance: '91%' },
  ];

  const sidebarItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'queries', label: 'My Queries', icon: MessageSquare },
    { id: 'saved', label: 'Saved Cases', icon: Bookmark },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'billing', label: 'Billing', icon: CreditCard },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen pt-20 pb-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar */}
          <div className="lg:w-64 shrink-0">
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-4 sticky top-24">
              <div className="flex items-center gap-3 p-4 mb-4 border-b border-gray-100">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#2d5a47] to-[#d4af37] flex items-center justify-center">
                  <span className="text-white font-bold text-sm">{user?.name?.split(' ').map(n => n[0]).join('') || 'U'}</span>
                </div>
                <div>
                  <p className="font-semibold text-[#1e3a2e] text-sm">{user?.name || 'User'}</p>
                  <p className="text-xs text-gray-500">{user?.email || 'user@example.com'}</p>
                </div>
              </div>

              <nav className="space-y-1">
                {sidebarItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                      activeTab === item.id
                        ? 'bg-[#2d5a47]/10 text-[#2d5a47]'
                        : 'text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </button>
                ))}
              </nav>

              <div className="mt-4 pt-4 border-t border-gray-100">
                <button
                  onClick={onLogout}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-red-600 hover:bg-red-50 transition-all"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            {/* Header */}
            <div className="mb-8">
              <h1 className="font-serif text-3xl font-bold text-[#1e3a2e] mb-2">
                {activeTab === 'overview' && 'Dashboard Overview'}
                {activeTab === 'queries' && 'My Queries'}
                {activeTab === 'saved' && 'Saved Cases'}
                {activeTab === 'analytics' && 'Research Analytics'}
                {activeTab === 'billing' && 'Billing & Subscription'}
                {activeTab === 'settings' && 'Account Settings'}
              </h1>
              <p className="text-gray-600">
                {activeTab === 'overview' && 'Track your research activity and insights'}
                {activeTab === 'queries' && 'View and manage your research queries'}
                {activeTab === 'saved' && 'Access your bookmarked cases and documents'}
                {activeTab === 'analytics' && 'Analyze your research patterns and productivity'}
                {activeTab === 'billing' && 'Manage your subscription and payments'}
                {activeTab === 'settings' && 'Update your profile and preferences'}
              </p>
            </div>

            {activeTab === 'overview' && (
              <div className="space-y-8">
                {/* Stats Grid */}
                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  {stats.map((stat, i) => (
                    <div key={i} className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between mb-4">
                        <div className="w-10 h-10 rounded-xl bg-[#f0f8f4] flex items-center justify-center">
                          <stat.icon className="w-5 h-5 text-[#2d5a47]" />
                        </div>
                        <span className="text-xs font-semibold text-green-600 bg-green-50 px-2 py-1 rounded-full">
                          {stat.change}
                        </span>
                      </div>
                      <div className="font-serif text-3xl font-bold text-[#1e3a2e] mb-1">{stat.value}</div>
                      <div className="text-sm text-gray-500">{stat.label}</div>
                    </div>
                  ))}
                </div>

                {/* Recent Activity */}
                <div className="grid lg:grid-cols-2 gap-6">
                  <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
                    <div className="flex items-center justify-between mb-6">
                      <h3 className="font-semibold text-[#1e3a2e]">Recent Queries</h3>
                      <Link to="/research" className="text-sm text-[#2d5a47] font-medium hover:underline flex items-center gap-1">
                        New Query <ArrowRight className="w-4 h-4" />
                      </Link>
                    </div>
                    <div className="space-y-4">
                      {recentQueries.map((query, i) => (
                        <div key={i} className="flex items-start gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors cursor-pointer">
                          <div className="w-8 h-8 rounded-lg bg-[#f0f8f4] flex items-center justify-center shrink-0">
                            <MessageSquare className="w-4 h-4 text-[#2d5a47]" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-[#1e3a2e] truncate">{query.query}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-xs text-gray-500">{query.date}</span>
                              <span className="text-xs px-2 py-0.5 rounded-full bg-[#f0f8f4] text-[#2d5a47] font-medium">
                                {query.type}
                              </span>
                            </div>
                          </div>
                          <ChevronRight className="w-4 h-4 text-gray-400" />
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
                    <div className="flex items-center justify-between mb-6">
                      <h3 className="font-semibold text-[#1e3a2e]">Saved Cases</h3>
                      <button className="text-sm text-[#2d5a47] font-medium hover:underline">
                        View All
                      </button>
                    </div>
                    <div className="space-y-4">
                      {savedCases.map((case_, i) => (
                        <div key={i} className="flex items-start gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors cursor-pointer">
                          <div className="w-8 h-8 rounded-lg bg-[#f9f6e8] flex items-center justify-center shrink-0">
                            <Bookmark className="w-4 h-4 text-[#d4af37]" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-[#1e3a2e] truncate">{case_.title}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-xs text-gray-500">{case_.court}</span>
                              <span className="text-xs text-gray-400">{case_.date}</span>
                            </div>
                          </div>
                          <span className="text-xs font-semibold text-[#4a7c59]">{case_.relevance}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="bg-gradient-to-br from-[#1e3a2e] to-[#2d5a47] rounded-2xl p-8 text-white">
                  <h3 className="font-serif text-2xl font-bold mb-4">Ready to Research?</h3>
                  <p className="text-gray-300 mb-6 max-w-lg">
                    Access the full power of Kenya Legal AI. Search across 100,000+ court judgments, 
                    700+ Acts of Parliament, and the complete Constitution of Kenya 2010.
                  </p>
                  <Link 
                    to="/research" 
                    className="inline-flex items-center gap-2 px-6 py-3 bg-white text-[#2d5a47] font-semibold rounded-xl hover:bg-gray-100 transition-colors"
                  >
                    <Zap className="w-5 h-5" />
                    Start Researching
                  </Link>
                </div>
              </div>
            )}

            {activeTab === 'queries' && (
              <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
                <p className="text-gray-500 text-center py-12">Query history feature coming soon...</p>
              </div>
            )}

            {activeTab === 'saved' && (
              <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
                <p className="text-gray-500 text-center py-12">Saved cases feature coming soon...</p>
              </div>
            )}

            {activeTab === 'analytics' && (
              <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
                <p className="text-gray-500 text-center py-12">Analytics feature coming soon...</p>
              </div>
            )}

            {activeTab === 'billing' && (
              <div className="space-y-6">
                <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h3 className="font-semibold text-[#1e3a2e] text-lg">Current Plan</h3>
                      <p className="text-gray-500">Manage your subscription</p>
                    </div>
                    <span className="px-4 py-2 bg-[#d4af37]/10 text-[#b8860b] font-semibold rounded-full text-sm">
                      {user?.plan || 'Free'} Plan
                    </span>
                  </div>

                  <div className="border-t border-gray-100 pt-6">
                    <div className="grid sm:grid-cols-3 gap-4">
                      <div className="p-4 bg-[#f0f8f4] rounded-xl">
                        <p className="text-sm text-gray-600 mb-1">Queries Used</p>
                        <p className="font-serif text-2xl font-bold text-[#2d5a47]">5 / 5</p>
                        <p className="text-xs text-gray-500 mt-1">Daily limit</p>
                      </div>
                      <div className="p-4 bg-[#f0f8f4] rounded-xl">
                        <p className="text-sm text-gray-600 mb-1">Documents</p>
                        <p className="font-serif text-2xl font-bold text-[#2d5a47]">0 / 0</p>
                        <p className="text-xs text-gray-500 mt-1">PDF analysis</p>
                      </div>
                      <div className="p-4 bg-[#f0f8f4] rounded-xl">
                        <p className="text-sm text-gray-600 mb-1">Next Billing</p>
                        <p className="font-serif text-2xl font-bold text-[#2d5a47]">Free</p>
                        <p className="text-xs text-gray-500 mt-1">No charges</p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 pt-6 border-t border-gray-100">
                    <Link 
                      to="/pricing" 
                      className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[#2d5a47] to-[#4a7c59] text-white font-semibold rounded-xl hover:shadow-lg transition-all"
                    >
                      <CreditCard className="w-5 h-5" />
                      Upgrade Plan
                    </Link>
                  </div>
                </div>

                <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
                  <h3 className="font-semibold text-[#1e3a2e] text-lg mb-4">Payment Methods</h3>
                  <p className="text-gray-500 text-center py-8">No payment methods on file. Upgrade to add one.</p>
                </div>
              </div>
            )}

            {activeTab === 'settings' && (
              <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
                <p className="text-gray-500 text-center py-12">Settings feature coming soon...</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
