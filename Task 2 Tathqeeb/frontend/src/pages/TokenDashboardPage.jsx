import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, Database, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { getTokenStatistics } from '../api/client';

const TokenDashboardPage = () => {
  const [tokenData, setTokenData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedRow, setExpandedRow] = useState(null);

  useEffect(() => {
    loadTokenStatistics();
  }, []);

  const loadTokenStatistics = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getTokenStatistics();
      setTokenData(data);
    } catch (err) {
      console.error('Failed to load token statistics:', err);
      setError('Failed to load token statistics. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('en-US').format(num || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    try {
      return new Date(dateStr).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };

  const getCategoryColor = (category) => {
    switch (category) {
      case 'compliant':
        return 'text-green-600 bg-green-100';
      case 'partially_compliant':
        return 'text-yellow-600 bg-yellow-100';
      case 'non_compliant':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getCategoryLabel = (category) => {
    switch (category) {
      case 'compliant':
        return 'Compliant';
      case 'partially_compliant':
        return 'Partially Compliant';
      case 'non_compliant':
        return 'Non-Compliant';
      default:
        return 'Not Analyzed';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading token statistics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <p className="text-red-600">{error}</p>
          <button
            onClick={loadTokenStatistics}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Token Management Dashboard</h1>
        <p className="text-gray-600">Monitor LLM token usage across all contract analyses</p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Total Contracts Analyzed</h3>
            <FileText className="text-blue-500" size={24} />
          </div>
          <p className="text-3xl font-bold text-gray-900">{tokenData?.total_contracts_analyzed || 0}</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-emerald-500">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Total Input Tokens</h3>
            <TrendingUp className="text-emerald-500" size={24} />
          </div>
          <p className="text-3xl font-bold text-gray-900">{formatNumber(tokenData?.total_prompt_tokens)}</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-purple-500">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Total Output Tokens</h3>
            <Activity className="text-purple-500" size={24} />
          </div>
          <p className="text-3xl font-bold text-gray-900">{formatNumber(tokenData?.total_completion_tokens)}</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-orange-500">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Avg Tokens/Contract</h3>
            <Database className="text-orange-500" size={24} />
          </div>
          <p className="text-3xl font-bold text-gray-900">{formatNumber(Math.round(tokenData?.avg_tokens_per_contract || 0))}</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-red-500">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Total Process Time</h3>
            <Activity className="text-red-500" size={24} />
          </div>
          <p className="text-3xl font-bold text-gray-900">{tokenData?.total_process_time ? `${tokenData.total_process_time}s` : '0s'}</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-indigo-500">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Avg Process Time/Contract</h3>
            <TrendingUp className="text-indigo-500" size={24} />
          </div>
          <p className="text-3xl font-bold text-gray-900">{tokenData?.avg_process_time_per_contract ? `${tokenData.avg_process_time_per_contract}s` : '0s'}</p>
        </div>
      </div>

      {/* Total Tokens Summary */}
      <div className="bg-gradient-to-r from-emerald-50 to-blue-50 rounded-lg shadow-md p-6 mb-8 border border-emerald-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Tokens Used</h3>
            <p className="text-gray-600">Combined input and output tokens across all analyses</p>
          </div>
          <div className="text-right">
            <p className="text-5xl font-bold text-emerald-600">{formatNumber(tokenData?.total_tokens)}</p>
            <p className="text-sm text-gray-500 mt-2">
              {formatNumber(tokenData?.total_prompt_tokens)} in + {formatNumber(tokenData?.total_completion_tokens)} out
            </p>
          </div>
        </div>
      </div>

      {/* Contracts Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <h2 className="text-xl font-semibold text-gray-900">Token Usage Per Contract</h2>
        </div>
        
        {tokenData?.contracts && tokenData.contracts.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contract
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Analyzed At
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Input Tokens
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Output Tokens
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Tokens
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Process Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {tokenData.contracts.map((contract, index) => (
                  <React.Fragment key={contract.contract_id}>
                    <tr className="hover:bg-gray-50 transition">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <FileText className="text-gray-400 mr-2" size={18} />
                          <div>
                            <p className="text-sm font-medium text-gray-900 truncate max-w-xs" title={contract.filename}>
                              {contract.filename}
                            </p>
                            <p className="text-xs text-gray-500 font-mono">{contract.contract_id.substring(0, 8)}...</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(contract.checked_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-emerald-600">
                        {formatNumber(contract.prompt_tokens)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-purple-600">
                        {formatNumber(contract.completion_tokens)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-bold text-gray-900">
                        {formatNumber(contract.total_tokens)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-indigo-600">
                        {contract.process_time ? `${contract.process_time.toFixed(2)}s` : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {contract.category ? (
                          <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getCategoryColor(contract.category)}`}>
                            {getCategoryLabel(contract.category)}
                          </span>
                        ) : (
                          <span className="text-xs text-gray-400">N/A</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <button
                          onClick={() => setExpandedRow(expandedRow === index ? null : index)}
                          className="text-emerald-600 hover:text-emerald-800 transition"
                        >
                          {expandedRow === index ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                        </button>
                      </td>
                    </tr>
                    
                    {expandedRow === index && (
                      <tr>
                        <td colSpan="8" className="px-6 py-4 bg-gray-50">
                          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div className="bg-white rounded p-4 border border-gray-200">
                              <p className="text-xs text-gray-500 mb-1">Compliance Score</p>
                              <p className="text-2xl font-bold text-gray-900">
                                {contract.compliance_score !== null && contract.compliance_score !== undefined
                                  ? `${contract.compliance_score}%`
                                  : 'N/A'}
                              </p>
                            </div>
                            <div className="bg-white rounded p-4 border border-gray-200">
                              <p className="text-xs text-gray-500 mb-1">Input/Output Ratio</p>
                              <p className="text-2xl font-bold text-gray-900">
                                {contract.prompt_tokens > 0
                                  ? (contract.completion_tokens / contract.prompt_tokens).toFixed(2)
                                  : 'N/A'}
                              </p>
                            </div>
                            <div className="bg-white rounded p-4 border border-gray-200">
                              <p className="text-xs text-gray-500 mb-1">Process Time</p>
                              <p className="text-2xl font-bold text-gray-900">
                                {contract.process_time ? `${contract.process_time.toFixed(2)}s` : 'N/A'}
                              </p>
                            </div>
                            <div className="bg-white rounded p-4 border border-gray-200">
                              <p className="text-xs text-gray-500 mb-1">Contract ID</p>
                              <p className="text-sm font-mono text-gray-900 break-all">{contract.contract_id}</p>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="px-6 py-12 text-center">
            <Database className="mx-auto text-gray-300 mb-4" size={48} />
            <p className="text-gray-500">No token usage data available yet.</p>
            <p className="text-sm text-gray-400 mt-2">Token usage will be tracked once contracts are analyzed.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TokenDashboardPage;
