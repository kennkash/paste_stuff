import React from ‘react’;
import { DollarSign, TrendingDown } from ‘lucide-react’;

const SpotfireSavingsSlide = () => {
return (
<div className="w-full h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-12 flex flex-col">
{/* Header */}
<div className="mb-8">
<h1 className="text-5xl font-bold text-slate-800 mb-2">
Spotfire License Optimization
</h1>
<p className="text-2xl text-slate-600">Right-sizing our license mix for maximum efficiency</p>
</div>

```
  {/* Main Content */}
  <div className="flex-1 flex gap-6">
    {/* Current State */}
    <div className="flex-1 bg-white rounded-2xl shadow-lg p-8 border-2 border-red-200">
      <div className="flex items-center gap-2 mb-6">
        <div className="w-3 h-3 bg-red-500 rounded-full"></div>
        <h2 className="text-2xl font-bold text-slate-700">Current State</h2>
      </div>
      
      <div className="space-y-4 mb-8">
        <div className="bg-slate-50 rounded-lg p-5">
          <div className="text-lg font-semibold text-slate-800 mb-3">Analyst Licenses</div>
          <div className="grid grid-cols-3 gap-4 text-center mb-2">
            <div>
              <div className="text-sm text-slate-500 mb-1">Quantity</div>
              <div className="text-2xl font-bold text-slate-700">3,500</div>
            </div>
            <div className="flex items-center justify-center">
              <span className="text-2xl text-slate-400">×</span>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">Unit Cost</div>
              <div className="text-2xl font-bold text-slate-700">$950</div>
            </div>
          </div>
          <div className="pt-3 border-t border-slate-300 text-right">
            <div className="text-sm text-slate-500">Subtotal</div>
            <div className="text-2xl font-bold text-slate-800">$3,325,000</div>
          </div>
        </div>
        <div className="bg-slate-50 rounded-lg p-5">
          <div className="text-lg font-semibold text-slate-800 mb-3">Consumer Licenses</div>
          <div className="grid grid-cols-3 gap-4 text-center mb-2">
            <div>
              <div className="text-sm text-slate-500 mb-1">Quantity</div>
              <div className="text-2xl font-bold text-slate-700">0</div>
            </div>
            <div className="flex items-center justify-center">
              <span className="text-2xl text-slate-400">×</span>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">Unit Cost</div>
              <div className="text-2xl font-bold text-slate-700">$333</div>
            </div>
          </div>
          <div className="pt-3 border-t border-slate-300 text-right">
            <div className="text-sm text-slate-500">Subtotal</div>
            <div className="text-2xl font-bold text-slate-800">$0</div>
          </div>
        </div>
      </div>

      <div className="pt-6 border-t-2 border-slate-200">
        <div className="flex justify-between items-center">
          <span className="text-lg font-semibold text-slate-600">Annual Cost</span>
          <span className="text-3xl font-bold text-red-600">$3,325,000</span>
        </div>
      </div>
    </div>

    {/* Arrow */}
    <div className="flex items-center justify-center">
      <div className="text-emerald-600">
        <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </div>

    {/* Proposed State */}
    <div className="flex-1 bg-white rounded-2xl shadow-lg p-8 border-2 border-emerald-200">
      <div className="flex items-center gap-2 mb-6">
        <div className="w-3 h-3 bg-emerald-500 rounded-full"></div>
        <h2 className="text-2xl font-bold text-slate-700">Proposed State</h2>
      </div>
      
      <div className="space-y-4 mb-8">
        <div className="bg-slate-50 rounded-lg p-5">
          <div className="text-lg font-semibold text-slate-800 mb-3">Analyst Licenses</div>
          <div className="grid grid-cols-3 gap-4 text-center mb-2">
            <div>
              <div className="text-sm text-slate-500 mb-1">Quantity</div>
              <div className="text-2xl font-bold text-slate-700">350</div>
            </div>
            <div className="flex items-center justify-center">
              <span className="text-2xl text-slate-400">×</span>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">Unit Cost</div>
              <div className="text-2xl font-bold text-slate-700">$950</div>
            </div>
          </div>
          <div className="pt-3 border-t border-slate-300 text-right">
            <div className="text-sm text-slate-500">Subtotal</div>
            <div className="text-2xl font-bold text-slate-800">$332,500</div>
          </div>
        </div>
        <div className="bg-slate-50 rounded-lg p-5">
          <div className="text-lg font-semibold text-slate-800 mb-3">Consumer Licenses</div>
          <div className="grid grid-cols-3 gap-4 text-center mb-2">
            <div>
              <div className="text-sm text-slate-500 mb-1">Quantity</div>
              <div className="text-2xl font-bold text-slate-700">2,100</div>
            </div>
            <div className="flex items-center justify-center">
              <span className="text-2xl text-slate-400">×</span>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">Unit Cost</div>
              <div className="text-2xl font-bold text-slate-700">$333</div>
            </div>
          </div>
          <div className="pt-3 border-t border-slate-300 text-right">
            <div className="text-sm text-slate-500">Subtotal</div>
            <div className="text-2xl font-bold text-slate-800">$699,300</div>
          </div>
        </div>
      </div>

      <div className="pt-6 border-t-2 border-slate-200">
        <div className="flex justify-between items-center">
          <span className="text-lg font-semibold text-slate-600">Annual Cost</span>
          <span className="text-3xl font-bold text-emerald-600">$1,031,800</span>
        </div>
      </div>
    </div>
  </div>

  {/* Savings Banner */}
  <div className="mt-8 bg-gradient-to-r from-emerald-600 to-emerald-500 rounded-2xl shadow-xl p-8">
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="bg-white rounded-full p-3">
          <TrendingDown className="w-8 h-8 text-emerald-600" />
        </div>
        <div>
          <div className="text-emerald-100 text-lg font-medium">Annual Savings</div>
          <div className="text-white text-5xl font-bold">$2,293,200</div>
        </div>
      </div>
      <div className="text-right">
        <div className="text-emerald-100 text-lg mb-2">Cost Reduction</div>
        <div className="text-white text-6xl font-bold">69%</div>
      </div>
    </div>
  </div>
</div>
```

);
};

export default SpotfireSavingsSlide;