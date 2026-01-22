import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Shield, CheckCircle, ArrowRight } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-6 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-full mb-6">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            AI Contract Checker
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Ensure your contracts comply with Islamic Shariah principles using advanced AI technology.
            Upload your documents and receive instant compliance analysis powered by Islamic jurisprudence.
          </p>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <FileText className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Smart Analysis</h3>
            <p className="text-gray-600">
              Advanced AI analyzes contract terms against comprehensive Shariah regulations and Islamic finance principles.
            </p>
          </div>

          <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <CheckCircle className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Compliance Reports</h3>
            <p className="text-gray-600">
              Get detailed compliance reports with specific recommendations and alternative clauses for non-compliant terms.
            </p>
          </div>

          <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <Shield className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Islamic Finance Focus</h3>
            <p className="text-gray-600">
              Specialized for Islamic finance contracts including Murabaha, Ijara, and Musharaka agreements.
            </p>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center">
          <button
            onClick={() => navigate('/check')}
            className="inline-flex items-center px-8 py-4 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors duration-200 shadow-lg hover:shadow-xl"
          >
            Start Checking Contracts
            <ArrowRight className="ml-2 w-5 h-5" />
          </button>
          <p className="text-gray-500 mt-4">
            Upload your PDF contract and get instant Shariah compliance analysis
          </p>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;