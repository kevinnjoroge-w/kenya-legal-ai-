import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Scale, Mail, Lock, Eye, EyeOff, ArrowRight, 
  CheckCircle, AlertCircle, Loader2, User, Briefcase,
  Building2, GraduationCap, Gavel
} from 'lucide-react';

const SignupPage = ({ onLogin }) => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: '',
    firm: '',
    phone: '',
    terms: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const roles = [
    { value: 'advocate', label: 'Practicing Advocate', icon: Gavel },
    { value: 'student', label: 'Law Student', icon: GraduationCap },
    { value: 'academic', label: 'Academic / Researcher', icon: Briefcase },
    { value: 'corporate', label: 'Corporate Counsel', icon: Building2 },
    { value: 'other', label: 'Other Legal Professional', icon: User },
  ];

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (step === 1) {
      if (!formData.firstName || !formData.lastName || !formData.email) {
        setError('Please fill in all required fields');
        return;
      }
      setStep(2);
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (!formData.terms) {
      setError('Please accept the terms and conditions');
      return;
    }

    setIsLoading(true);

    try {
      const res = await fetch('/api/v1/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: `${formData.firstName} ${formData.lastName}`, email: formData.email, password: formData.password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || data.message || 'Signup failed');
      } else {
        if (data.access_token) localStorage.setItem('token', data.access_token);
        onLogin(data.user || { name: `${formData.firstName} ${formData.lastName}`, email: formData.email });
        navigate('/dashboard');
      }
    } catch (e) {
      setError('Network error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center pt-20 pb-16 px-4">
      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#2d5a47] to-[#4a7c59] flex items-center justify-center shadow-lg">
              <Scale className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="font-serif text-2xl font-bold text-[#1e3a2e]">Kenya Legal AI</span>
            </div>
          </Link>
        </div>

        {/* Progress */}
        <div className="flex items-center gap-2 mb-8">
          <div className={`flex-1 h-2 rounded-full ${step >= 1 ? 'bg-[#2d5a47]' : 'bg-gray-200'}`} />
          <div className={`flex-1 h-2 rounded-full ${step >= 2 ? 'bg-[#2d5a47]' : 'bg-gray-200'}`} />
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-xl p-8">
          <h1 className="font-serif text-2xl font-bold text-[#1e3a2e] mb-2">
            {step === 1 ? 'Create your account' : 'Set up your profile'}
          </h1>
          <p className="text-gray-600 mb-6">
            {step === 1 ? 'Start your free legal research journey' : 'Just a few more details to get you started'}
          </p>

          {error && (
            <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm mb-6">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {step === 1 ? (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">First name *</label>
                    <input
                      type="text"
                      name="firstName"
                      value={formData.firstName}
                      onChange={handleChange}
                      placeholder="John"
                      className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-[#2d5a47] focus:ring-2 focus:ring-[#2d5a47]/20 outline-none transition-all text-gray-800"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Last name *</label>
                    <input
                      type="text"
                      name="lastName"
                      value={formData.lastName}
                      onChange={handleChange}
                      placeholder="Doe"
                      className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-[#2d5a47] focus:ring-2 focus:ring-[#2d5a47]/20 outline-none transition-all text-gray-800"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Email address *</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder="you@example.com"
                      className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:border-[#2d5a47] focus:ring-2 focus:ring-[#2d5a47]/20 outline-none transition-all text-gray-800"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Phone number</label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    placeholder="+254 700 000 000"
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-[#2d5a47] focus:ring-2 focus:ring-[#2d5a47]/20 outline-none transition-all text-gray-800"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">I am a... *</label>
                  <div className="grid grid-cols-2 gap-3">
                    {roles.map((role) => (
                      <button
                        key={role.value}
                        type="button"
                        onClick={() => setFormData(prev => ({ ...prev, role: role.value }))}
                        className={`flex items-center gap-2 p-3 rounded-xl border-2 transition-all text-left ${
                          formData.role === role.value
                            ? 'border-[#2d5a47] bg-[#f0f8f4] text-[#2d5a47]'
                            : 'border-gray-200 hover:border-gray-300 text-gray-600'
                        }`}
                      >
                        <role.icon className="w-4 h-4 shrink-0" />
                        <span className="text-sm font-medium">{role.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Law firm / Organization</label>
                  <div className="relative">
                    <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="text"
                      name="firm"
                      value={formData.firm}
                      onChange={handleChange}
                      placeholder="e.g., Oraro & Company Advocates"
                      className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:border-[#2d5a47] focus:ring-2 focus:ring-[#2d5a47]/20 outline-none transition-all text-gray-800"
                    />
                  </div>
                </div>
              </>
            ) : (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Password *</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      placeholder="Min. 8 characters"
                      className="w-full pl-10 pr-12 py-3 rounded-xl border border-gray-200 focus:border-[#2d5a47] focus:ring-2 focus:ring-[#2d5a47]/20 outline-none transition-all text-gray-800"
                      required
                      minLength={8}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Confirm password *</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      name="confirmPassword"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      placeholder="Repeat your password"
                      className="w-full pl-10 pr-12 py-3 rounded-xl border border-gray-200 focus:border-[#2d5a47] focus:ring-2 focus:ring-[#2d5a47]/20 outline-none transition-all text-gray-800"
                      required
                    />
                  </div>
                </div>

                <div className="bg-[#f0f8f4] rounded-xl p-4 space-y-2">
                  <p className="text-sm font-medium text-[#2d5a47]">Password requirements:</p>
                  {[
                    'At least 8 characters',
                    'One uppercase letter',
                    'One number',
                    'One special character',
                  ].map((req, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm text-gray-600">
                      <CheckCircle className="w-4 h-4 text-[#4a7c59]" />
                      {req}
                    </div>
                  ))}
                </div>

                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    name="terms"
                    checked={formData.terms}
                    onChange={handleChange}
                    className="w-5 h-5 rounded border-gray-300 text-[#2d5a47] focus:ring-[#2d5a47] mt-0.5"
                  />
                  <span className="text-sm text-gray-600">
                    I agree to the{' '}
                    <Link to="/terms" className="text-[#2d5a47] font-medium hover:underline">Terms of Service</Link>
                    {' '}and{' '}
                    <Link to="/privacy" className="text-[#2d5a47] font-medium hover:underline">Privacy Policy</Link>
                    . I understand this is a legal research tool and not a substitute for professional legal advice.
                  </span>
                </label>
              </>
            )}

            <div className="flex gap-3">
              {step === 2 && (
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="flex-1 py-3.5 border-2 border-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 transition-all"
                >
                  Back
                </button>
              )}
              <button
                type="submit"
                disabled={isLoading}
                className="flex-1 py-3.5 bg-gradient-to-r from-[#2d5a47] to-[#4a7c59] text-white font-semibold rounded-xl shadow-lg shadow-green-900/20 hover:shadow-green-900/30 transition-all disabled:opacity-70 flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  <>
                    {step === 1 ? 'Continue' : 'Create Account'} <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </div>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-100 text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <Link to="/login" className="text-[#2d5a47] font-semibold hover:text-[#1e3a2e]">
                Sign in
              </Link>
            </p>
          </div>
        </div>

        {/* Trust badges */}
        <div className="mt-8 flex items-center justify-center gap-6 text-sm text-gray-500">
          <span className="flex items-center gap-1.5">
            <CheckCircle className="w-4 h-4 text-[#2d5a47]" /> Free forever plan
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle className="w-4 h-4 text-[#2d5a47]" /> No credit card required
          </span>
        </div>
      </div>
    </div>
  );
};

export default SignupPage;
