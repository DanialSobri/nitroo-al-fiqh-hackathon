import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Shield, CheckCircle, ArrowRight, Sparkles, BookOpen, Zap, Upload } from 'lucide-react';

const HomePage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-6 py-12">

        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-emerald-600 to-green-700 rounded-2xl mb-8 shadow-lg">
            <Shield className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-5xl md:text-7xl font-bold text-gray-900 mb-6 leading-tight">
            Tathqeeb AI
            <span className="block text-emerald-600">(تثقيب)</span>
          </h1>
          <p className="text-lg text-emerald-700 font-medium mb-4">
            تثقيب (Tathqeeb) - Arabic for "Verification" & "Authentication"
          </p>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed mb-8">
            Ensure your contracts comply with Islamic Shariah principles using advanced AI technology.
            Our verification system provides authentic Shariah compliance analysis for Islamic finance.
          </p>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6 mb-16">

          {/* Large Hero Card */}
          <div className="md:col-span-2 lg:col-span-2 bg-gradient-to-br from-emerald-600 to-green-700 rounded-3xl p-8 text-white shadow-lg hover:shadow-xl transition-all duration-300">
            <div className="h-full flex flex-col justify-between">
              <div>
                <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm mb-6">
                  <Upload className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-3xl font-bold mb-4">Start Your Verification</h3>
                <p className="text-white/90 text-lg leading-relaxed mb-6">
                  Upload your PDF contract and receive authentic Shariah compliance analysis with detailed recommendations through our Tathqeeb verification system.
                </p>
              </div>
              <button
                onClick={() => navigate('/check')}
                className="inline-flex items-center px-6 py-3 bg-white text-emerald-600 font-semibold rounded-xl hover:bg-gray-50 transition-all duration-200 shadow-md hover:shadow-lg transform hover:-translate-y-0.5 w-fit"
              >
                Verify Contract
                <ArrowRight className="ml-2 w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Smart Analysis Card */}
          <div className="md:col-span-1 lg:col-span-1 bg-white rounded-3xl p-6 shadow-sm border border-emerald-100 hover:shadow-md transition-shadow duration-300">
            <div className="flex flex-col h-full">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-400 to-green-500 rounded-xl flex items-center justify-center shadow-lg mb-4">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <h4 className="text-xl font-bold text-gray-900 mb-3">Smart Analysis</h4>
              <p className="text-gray-600 text-sm leading-relaxed flex-1">
                Advanced AI analyzes contract terms against comprehensive Shariah regulations.
              </p>
            </div>
          </div>

          {/* Compliance Reports Card */}
          <div className="md:col-span-1 lg:col-span-1 bg-white rounded-3xl p-6 shadow-sm border border-emerald-100 hover:shadow-md transition-shadow duration-300">
            <div className="flex flex-col h-full">
              <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-yellow-500 rounded-xl flex items-center justify-center shadow-lg mb-4">
                <CheckCircle className="w-6 h-6 text-white" />
              </div>
              <h4 className="text-xl font-bold text-gray-900 mb-3">Compliance Reports</h4>
              <p className="text-gray-600 text-sm leading-relaxed flex-1">
                Detailed reports with specific recommendations for non-compliant terms.
              </p>
            </div>
          </div>

          {/* Islamic Finance Focus Card - Wide */}
          <div className="md:col-span-2 lg:col-span-2 bg-white rounded-3xl p-8 shadow-sm border border-emerald-100 hover:shadow-md transition-shadow duration-300">
            <div className="flex items-center gap-6 h-full">
              <div className="flex-shrink-0">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg">
                  <BookOpen className="w-8 h-8 text-white" />
                </div>
              </div>
              <div className="flex-1">
                <h4 className="text-2xl font-bold text-gray-900 mb-3">Islamic Finance Focus</h4>
                <p className="text-gray-600 text-lg leading-relaxed">
                  Specialized for Islamic finance contracts including Murabaha, Ijara, Musharaka, and other Islamic financial instruments.
                </p>
              </div>
            </div>
          </div>

          {/* Instant Results Card */}
          <div className="md:col-span-1 lg:col-span-2 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-3xl p-6 text-white shadow-lg hover:shadow-xl transition-all duration-300">
            <div className="flex items-center gap-4 h-full">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                  <Zap className="w-6 h-6 text-white" />
                </div>
              </div>
              <div className="flex-1">
                <h4 className="text-xl font-bold mb-2">Instant Results</h4>
                <p className="text-white/90 text-sm leading-relaxed">
                  Get immediate compliance analysis with actionable insights.
                </p>
              </div>
            </div>
          </div>

        </div>

        {/* Bottom CTA */}
        <div className="text-center">
          <p className="text-gray-500 text-lg mb-6">
            Ready to verify your contracts are Shariah compliant with Tathqeeb AI?
          </p>
          <button
            onClick={() => navigate('/check')}
            className="inline-flex items-center px-10 py-5 bg-emerald-600 text-white font-semibold rounded-xl hover:bg-emerald-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
          >
            Verify Your Contract Now
            <ArrowRight className="ml-2 w-5 h-5" />
          </button>
        </div>

      </div>
    </div>
  );
};

export default HomePage;
