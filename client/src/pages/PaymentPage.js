import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Scale, CreditCard, Lock, Check, ChevronLeft, Shield,
  Star, Zap, Crown, Diamond, AlertCircle, Loader2
} from 'lucide-react';

const PaymentPage = () => {
  const [selectedPlan, setSelectedPlan] = useState('professional');
  const [billingCycle, setBillingCycle] = useState('monthly');
  const [step, setStep] = useState(1);
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('card');
  const [formData, setFormData] = useState({
    cardNumber: '',
    cardName: '',
    expiry: '',
    cvv: '',
    phone: '',
  });
  const navigate = useNavigate();

  const plans = {
    free: {
      name: 'Free',
      icon: Star,
      price: 0,
      description: 'For students and personal research',
      features: ['5 queries/day', 'Constitution access', 'Basic case search'],
      color: 'gray'
    },
    professional: {
      name: 'Professional',
      icon: Crown,
      monthlyPrice: 2999,
      yearlyPrice: 29990,
      description: 'For practicing advocates',
      features: ['Unlimited queries', 'Full case law DB', 'Citation export', 'PDF analysis', 'Priority support'],
      color: 'gold',
      popular: true
    },
    enterprise: {
      name: 'Enterprise',
      icon: Diamond,
      price: 'Custom',
      description: 'For law firms & government',
      features: ['Everything in Pro', 'API access', 'Custom training', 'SSO & audit logs', 'Dedicated support'],
      color: 'green'
    },
  };

  const paymentMethods = [
    { id: 'card', label: 'Credit/Debit Card', icon: CreditCard },
    { id: 'mpesa', label: 'M-Pesa', icon: Phone },
    { id: 'bank', label: 'Bank Transfer', icon: Building },
  ];

  const handlePayment = async (e) => {
    e.preventDefault();
    setIsProcessing(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/v1/billing/create-checkout-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ plan: selectedPlan, billing_cycle: billingCycle }),
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.detail || 'Payment initiation failed');
      } else {
        // Redirect to Stripe Checkout
        window.location.href = data.url;
      }
    } catch (err) {
      alert('Network error');
    } finally {
      setIsProcessing(false);
    }
  };

  const currentPlan = plans[selectedPlan];
  const price = billingCycle === 'monthly' ? currentPlan.monthlyPrice : currentPlan.yearlyPrice;

  return (
    <div className="min-h-screen pt-24 pb-16">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Back Button */}
        <Link to="/pricing" className="inline-flex items-center gap-2 text-gray-600 hover:text-[#2d5a47] mb-8 transition-colors">
          <ChevronLeft className="w-4 h-4" />
          Back to Pricing
        </Link>

        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="font-serif text-4xl font-bold text-[#1e3a2e] mb-4">Complete Your Subscription</h1>
          <p className="text-gray-600">Choose your plan and payment method to get started</p>
        </div>

        {step === 1 && (
          <div className="space-y-8">
            {/* Plan Selection */}
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
              <h2 className="font-semibold text-[#1e3a2e] mb-6">1. Select Your Plan</h2>

              <div className="grid md:grid-cols-3 gap-4 mb-6">
                {Object.entries(plans).map(([key, plan]) => (
                  <button
                    key={key}
                    onClick={() => setSelectedPlan(key)}
                    className={`relative p-6 rounded-xl border-2 transition-all text-left ${
                      selectedPlan === key
                        ? 'border-[#2d5a47] bg-[#f0f8f4]'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {plan.popular && (
                      <span className="absolute -top-3 left-4 px-3 py-1 bg-[#d4af37] text-white text-xs font-bold rounded-full">
                        POPULAR
                      </span>
                    )}
                    <plan.icon className={`w-8 h-8 mb-3 ${selectedPlan === key ? 'text-[#2d5a47]' : 'text-gray-400'}`} />
                    <h3 className="font-semibold text-[#1e3a2e] mb-1">{plan.name}</h3>
                    <p className="text-sm text-gray-500 mb-3">{plan.description}</p>
                    <div className="font-serif text-2xl font-bold text-[#1e3a2e]">
                      {plan.price === 'Custom' ? 'Custom' : `KSh ${plan.monthlyPrice?.toLocaleString() || 0}`}
                      {plan.monthlyPrice && <span className="text-sm font-normal text-gray-500">/mo</span>}
                    </div>
                  </button>
                ))}
              </div>

              {/* Billing Cycle */}
              {selectedPlan !== 'enterprise' && selectedPlan !== 'free' && (
                <div className="flex items-center gap-4">
                  <span className="text-sm font-medium text-gray-700">Billing cycle:</span>
                  <div className="inline-flex bg-gray-100 rounded-full p-1">
                    <button
                      onClick={() => setBillingCycle('monthly')}
                      className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                        billingCycle === 'monthly' ? 'bg-white text-[#2d5a47] shadow-sm' : 'text-gray-500'
                      }`}
                    >
                      Monthly
                    </button>
                    <button
                      onClick={() => setBillingCycle('yearly')}
                      className={`px-4 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2 ${
                        billingCycle === 'yearly' ? 'bg-white text-[#2d5a47] shadow-sm' : 'text-gray-500'
                      }`}
                    >
                      Yearly
                      <span className="text-xs px-2 py-0.5 bg-[#d4af37]/10 text-[#b8860b] rounded-full">Save 17%</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Summary */}
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
              <h2 className="font-semibold text-[#1e3a2e] mb-4">Order Summary</h2>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">{currentPlan.name} Plan ({billingCycle})</span>
                  <span className="font-medium">{price === 'Custom' ? 'Contact us' : `KSh ${price?.toLocaleString()}`}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">VAT (16%)</span>
                  <span className="font-medium">
                    {price === 'Custom' ? '-' : `KSh ${Math.round(price * 0.16).toLocaleString()}`}
                  </span>
                </div>
                <div className="border-t border-gray-100 pt-3 flex justify-between">
                  <span className="font-semibold text-[#1e3a2e]">Total</span>
                  <span className="font-serif text-xl font-bold text-[#2d5a47]">
                    {price === 'Custom' ? 'Custom' : `KSh ${Math.round(price * 1.16).toLocaleString()}`}
                  </span>
                </div>
              </div>

              <button
                onClick={() => setStep(2)}
                className="w-full mt-6 py-3.5 bg-gradient-to-r from-[#2d5a47] to-[#4a7c59] text-white font-semibold rounded-xl shadow-lg shadow-green-900/20 hover:shadow-green-900/30 transition-all"
              >
                Continue to Payment
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-8">
            {/* Payment Method */}
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
              <h2 className="font-semibold text-[#1e3a2e] mb-6">2. Payment Method</h2>

              <div className="grid sm:grid-cols-3 gap-4 mb-8">
                {paymentMethods.map((method) => (
                  <button
                    key={method.id}
                    onClick={() => setPaymentMethod(method.id)}
                    className={`p-4 rounded-xl border-2 transition-all flex flex-col items-center gap-2 ${
                      paymentMethod === method.id
                        ? 'border-[#2d5a47] bg-[#f0f8f4]'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <method.icon className={`w-6 h-6 ${paymentMethod === method.id ? 'text-[#2d5a47]' : 'text-gray-400'}`} />
                    <span className="text-sm font-medium">{method.label}</span>
                  </button>
                ))}
              </div>

              {paymentMethod === 'card' && (
                <form onSubmit={handlePayment} className="space-y-5">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Card Number</label>
                    <div className="relative">
                      <CreditCard className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        type="text"
                        placeholder="1234 5678 9012 3456"
                        className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:border-[#2d5a47] focus:ring-2 focus:ring-[#2d5a47]/20 outline-none transition-all"
                        value={formData.cardNumber}
                        onChange={(e) => setFormData({...formData, cardNumber: e.target.value})}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Cardholder Name</label>
                    <input
                      type="text"
                      placeholder="Name on card"
                      className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-[#2d5a47] focus:ring-2 focus:ring-[#2d5a47]/20 outline-none transition-all"
                      value={formData.cardName}
                      onChange={(e) => setFormData({...formData, cardName: e.target.value})}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Expiry Date</label>
                      <input
                        type="text"
                        placeholder="MM/YY"
                        className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-[#2d5a47] focus:ring-2 focus:ring-[#2d5a47]/20 outline-none transition-all"
                        value={formData.expiry}
                        onChange={(e) => setFormData({...formData, expiry: e.target.value})}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">CVV</label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                          type="text"
                          placeholder="123"
                          className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:border-[#2d5a47] focus:ring-2 focus:ring-[#2d5a47]/20 outline-none transition-all"
                          value={formData.cvv}
                          onChange={(e) => setFormData({...formData, cvv: e.target.value})}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 p-4 bg-[#f0f8f4] rounded-xl">
                    <Shield className="w-5 h-5 text-[#2d5a47]" />
                    <span className="text-sm text-[#2d5a47]">Your payment is secured with 256-bit SSL encryption</span>
                  </div>

                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => setStep(1)}
                      className="flex-1 py-3.5 border-2 border-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 transition-all"
                    >
                      Back
                    </button>
                    <button
                      type="submit"
                      disabled={isProcessing}
                      className="flex-1 py-3.5 bg-gradient-to-r from-[#2d5a47] to-[#4a7c59] text-white font-semibold rounded-xl shadow-lg shadow-green-900/20 hover:shadow-green-900/30 transition-all disabled:opacity-70 flex items-center justify-center gap-2"
                    >
                      {isProcessing ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        <>
                          <Lock className="w-5 h-5" />
                          Pay KSh {Math.round(price * 1.16).toLocaleString()}
                        </>
                      )}
                    </button>
                  </div>
                </form>
              )}

              {paymentMethod === 'mpesa' && (
                <form onSubmit={handlePayment} className="space-y-5">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">M-Pesa Phone Number</label>
                    <input
                      type="tel"
                      placeholder="254700000000"
                      className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-[#2d5a47] focus:ring-2 focus:ring-[#2d5a47]/20 outline-none transition-all"
                      value={formData.phone}
                      onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    />
                  </div>

                  <div className="p-4 bg-[#f0f8f4] rounded-xl">
                    <p className="text-sm text-[#2d5a47]">
                      You will receive an M-Pesa prompt on your phone. Enter your PIN to complete the payment.
                    </p>
                  </div>

                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => setStep(1)}
                      className="flex-1 py-3.5 border-2 border-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 transition-all"
                    >
                      Back
                    </button>
                    <button
                      type="submit"
                      disabled={isProcessing}
                      className="flex-1 py-3.5 bg-gradient-to-r from-[#2d5a47] to-[#4a7c59] text-white font-semibold rounded-xl shadow-lg shadow-green-900/20 hover:shadow-green-900/30 transition-all disabled:opacity-70 flex items-center justify-center gap-2"
                    >
                      {isProcessing ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        <>
                          <Phone className="w-5 h-5" />
                          Pay with M-Pesa
                        </>
                      )}
                    </button>
                  </div>
                </form>
              )}

              {paymentMethod === 'bank' && (
                <div className="space-y-5">
                  <div className="p-6 bg-[#f0f8f4] rounded-xl">
                    <h3 className="font-semibold text-[#1e3a2e] mb-4">Bank Transfer Details</h3>
                    <div className="space-y-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Bank Name:</span>
                        <span className="font-medium">Kenya Commercial Bank</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Account Name:</span>
                        <span className="font-medium">Kenya Legal AI Ltd</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Account Number:</span>
                        <span className="font-medium">1234567890</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Branch Code:</span>
                        <span className="font-medium">001</span>
                      </div>
                    </div>
                  </div>

                  <p className="text-sm text-gray-600">
                    Please include your email address as the reference. Your account will be activated within 24 hours of payment confirmation.
                  </p>

                  <button
                    onClick={() => setStep(1)}
                    className="w-full py-3.5 border-2 border-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 transition-all"
                  >
                    Back
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="text-center py-16">
            <div className="w-20 h-20 rounded-full bg-[#f0f8f4] flex items-center justify-center mx-auto mb-6">
              <Check className="w-10 h-10 text-[#2d5a47]" />
            </div>
            <h2 className="font-serif text-3xl font-bold text-[#1e3a2e] mb-4">Payment Successful!</h2>
            <p className="text-gray-600 mb-8 max-w-md mx-auto">
              Thank you for subscribing to Kenya Legal AI. Your account has been upgraded to the {currentPlan.name} plan.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link 
                to="/dashboard" 
                className="px-8 py-3.5 bg-gradient-to-r from-[#2d5a47] to-[#4a7c59] text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all"
              >
                Go to Dashboard
              </Link>
              <Link 
                to="/research" 
                className="px-8 py-3.5 border-2 border-[#2d5a47] text-[#2d5a47] font-semibold rounded-xl hover:bg-[#f0f8f4] transition-all"
              >
                Start Researching
              </Link>
            </div>
          </div>
        )}

        {/* Security Badges */}
        <div className="mt-12 flex items-center justify-center gap-8 text-sm text-gray-500">
          <span className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-[#2d5a47]" /> 256-bit SSL Encrypted
          </span>
          <span className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-[#2d5a47]" /> PCI DSS Compliant
          </span>
          <span className="flex items-center gap-2">
            <Check className="w-4 h-4 text-[#2d5a47]" /> Money-back Guarantee
          </span>
        </div>
      </div>
    </div>
  );
};

// Helper components
const Phone = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/>
  </svg>
);

const Building = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="2" width="16" height="20" rx="2" ry="2"/>
    <path d="M9 22v-4h6v4"/>
    <path d="M8 6h.01"/>
    <path d="M16 6h.01"/>
    <path d="M8 10h.01"/>
    <path d="M16 10h.01"/>
    <path d="M8 14h.01"/>
    <path d="M16 14h.01"/>
  </svg>
);

export default PaymentPage;
