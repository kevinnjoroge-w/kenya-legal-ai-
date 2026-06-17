import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, Loader2, Scale, Filter, BookOpen, Gavel, FileText,
  ChevronRight, Download, Share2, Bookmark, Copy, ThumbsUp,
  ThumbsDown, RefreshCw, Sparkles, AlertTriangle, X
} from 'lucide-react';

const ResearchPage = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [filters, setFilters] = useState({ docType: '', court: '' });
  const [showFilters, setShowFilters] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const exampleQueries = [
    "What does Article 27 of the Constitution say about equality?",
    "Explain the rights of an accused person under Kenyan law",
    "What is the process for impeaching a governor in Kenya?",
    "Summarize the Employment Act 2007 provisions on termination",
    "Recent Supreme Court decisions on land rights",
  ];

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const token = localStorage.getItem('token');
      const body = {
        query: input,
        mode: 'research',
        document_type: filters.docType || null,
        court: filters.court || null,
        history: messages.map(m => ({ role: m.role, content: m.content })),
      };

      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        const msg = err?.detail || err?.message || 'AI service error';
        setMessages(prev => [...prev, { role: 'assistant', content: msg }]);
      } else {
        const data = await res.json();
        const aiMessage = { role: 'assistant', content: data.response, sources: data.sources, followUp: data.follow_up_questions };
        setMessages(prev => [...prev, aiMessage]);
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Network error while calling AI service.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExampleClick = (query) => {
    setInput(query);
  };

  return (
    <div className="min-h-screen pt-20 pb-4 flex flex-col">
      <div className="flex-1 max-w-5xl mx-auto w-full px-4 flex flex-col">
        {/* Header */}
        <div className="text-center py-8">
          <h1 className="font-serif text-3xl font-bold text-[#1e3a2e] mb-2">Legal Research Chat</h1>
          <p className="text-gray-600">Ask any question about Kenyan law and get citation-backed answers</p>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-6 mb-4 min-h-[400px]">
          {messages.length === 0 ? (
            <div className="text-center py-16">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-[#f0f8f4] to-[#e8f5e9] flex items-center justify-center mx-auto mb-6">
                <Scale className="w-10 h-10 text-[#2d5a47]" />
              </div>
              <h3 className="font-serif text-2xl font-bold text-[#1e3a2e] mb-3">Welcome to Kenya Legal AI</h3>
              <p className="text-gray-600 max-w-lg mx-auto mb-8">
                Ask me about the Constitution of Kenya, Acts of Parliament, court judgments, or any aspect of Kenya's legal framework.
              </p>

              <div className="max-w-2xl mx-auto">
                <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">Try asking:</p>
                <div className="space-y-2">
                  {exampleQueries.map((query, i) => (
                    <button
                      key={i}
                      onClick={() => handleExampleClick(query)}
                      className="w-full text-left px-5 py-4 bg-white rounded-xl border border-gray-200 hover:border-[#2d5a47]/30 hover:bg-[#f0f8f4] transition-all text-sm text-gray-700 flex items-center gap-3 group"
                    >
                      <Sparkles className="w-4 h-4 text-[#d4af37]" />
                      {query}
                      <ChevronRight className="w-4 h-4 text-gray-400 ml-auto group-hover:text-[#2d5a47] group-hover:translate-x-1 transition-all" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div key={i} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#2d5a47] to-[#4a7c59] flex items-center justify-center shrink-0">
                    <Scale className="w-4 h-4 text-white" />
                  </div>
                )}
                <div className={`max-w-[80%] rounded-2xl px-6 py-4 ${
                  msg.role === 'user' 
                    ? 'bg-gradient-to-r from-[#2d5a47] to-[#4a7c59] text-white' 
                    : 'bg-white border border-gray-200 shadow-sm'
                }`}>
                  {msg.role === 'assistant' ? (
                    <div className="prose prose-sm max-w-none">
                      <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                        {msg.content}
                      </div>

                      {/* Sources */}
                      {msg.sources && (
                        <div className="mt-4 pt-4 border-t border-gray-100">
                          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Sources Cited</p>
                          <div className="flex flex-wrap gap-2">
                            {msg.sources.map((source, j) => (
                              <span key={j} className="px-3 py-1 bg-[#f0f8f4] text-[#2d5a47] text-xs rounded-full font-medium">
                                {source.type === 'constitution' && <BookOpen className="w-3 h-3 inline mr-1" />}
                                {source.type === 'judgment' && <Gavel className="w-3 h-3 inline mr-1" />}
                                {source.type === 'act' && <FileText className="w-3 h-3 inline mr-1" />}
                                {source.title}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Follow-up */}
                      {msg.followUp && (
                        <div className="mt-4 pt-4 border-t border-gray-100">
                          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Explore Further</p>
                          <div className="flex flex-wrap gap-2">
                            {msg.followUp.map((q, j) => (
                              <button
                                key={j}
                                onClick={() => handleExampleClick(q)}
                                className="px-3 py-1.5 bg-[#f0f8f4] hover:bg-[#2d5a47] hover:text-white text-[#2d5a47] text-xs rounded-full transition-colors"
                              >
                                → {q}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Actions */}
                      <div className="mt-4 pt-4 border-t border-gray-100 flex items-center gap-3">
                        <button className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors" title="Copy">
                          <Copy className="w-4 h-4 text-gray-400" />
                        </button>
                        <button className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors" title="Like">
                          <ThumbsUp className="w-4 h-4 text-gray-400" />
                        </button>
                        <button className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors" title="Dislike">
                          <ThumbsDown className="w-4 h-4 text-gray-400" />
                        </button>
                        <button className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors" title="Regenerate">
                          <RefreshCw className="w-4 h-4 text-gray-400" />
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm">{msg.content}</p>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center shrink-0">
                    <span className="text-xs font-bold text-gray-600">You</span>
                  </div>
                )}
              </div>
            ))
          )}

          {isLoading && (
            <div className="flex gap-4">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#2d5a47] to-[#4a7c59] flex items-center justify-center shrink-0">
                <Scale className="w-4 h-4 text-white" />
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl px-6 py-4 shadow-sm">
                <div className="flex gap-2">
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-lg p-4">
          {/* Filters */}
          <div className="flex items-center gap-2 mb-3">
            <button 
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors text-sm text-gray-600"
            >
              <Filter className="w-4 h-4" />
              Filters
            </button>
            {filters.docType && (
              <span className="px-3 py-1 rounded-full bg-[#f0f8f4] text-[#2d5a47] text-xs font-medium flex items-center gap-1">
                {filters.docType}
                <X className="w-3 h-3 cursor-pointer" onClick={() => setFilters({...filters, docType: ''})} />
              </span>
            )}
            {filters.court && (
              <span className="px-3 py-1 rounded-full bg-[#f0f8f4] text-[#2d5a47] text-xs font-medium flex items-center gap-1">
                {filters.court}
                <X className="w-3 h-3 cursor-pointer" onClick={() => setFilters({...filters, court: ''})} />
              </span>
            )}
          </div>

          {showFilters && (
            <div className="flex gap-4 mb-3 pb-3 border-b border-gray-100">
              <select 
                value={filters.docType}
                onChange={(e) => setFilters({...filters, docType: e.target.value})}
                className="px-3 py-2 rounded-lg bg-gray-50 border border-gray-200 text-sm text-gray-700 focus:outline-none focus:border-[#2d5a47]"
              >
                <option value="">All Sources</option>
                <option value="constitution">Constitution</option>
                <option value="act">Acts of Parliament</option>
                <option value="judgment">Court Judgments</option>
                <option value="legal_notice">Legal Notices</option>
              </select>
              <select 
                value={filters.court}
                onChange={(e) => setFilters({...filters, court: e.target.value})}
                className="px-3 py-2 rounded-lg bg-gray-50 border border-gray-200 text-sm text-gray-700 focus:outline-none focus:border-[#2d5a47]"
              >
                <option value="">All Courts</option>
                <option value="Supreme Court">Supreme Court</option>
                <option value="Court of Appeal">Court of Appeal</option>
                <option value="High Court">High Court</option>
                <option value="Employment and Labour Relations Court">Employment & Labour Court</option>
                <option value="Environment and Land Court">Environment & Land Court</option>
              </select>
            </div>
          )}

          <div className="flex items-end gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask a legal question..."
              rows={1}
              className="flex-1 resize-none bg-transparent border-none focus:outline-none text-gray-800 placeholder-gray-400 min-h-[24px] max-h-[120px]"
              style={{ height: 'auto' }}
            />
            <button 
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="w-10 h-10 rounded-xl bg-gradient-to-r from-[#2d5a47] to-[#4a7c59] text-white flex items-center justify-center hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
            <span>{input.length} / 2000</span>
            <span className="flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              AI-generated content — not legal advice
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResearchPage;
