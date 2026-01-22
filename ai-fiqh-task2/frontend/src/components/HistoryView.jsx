import React, { useEffect, useState } from 'react';
import { FileText, Calendar, CheckCircle2, AlertTriangle, XCircle, MinusCircle, ChevronRight, RefreshCcw, Eye, ThumbsUp, ThumbsDown, UserCheck } from 'lucide-react';
import { getContractHistory } from '../api/client';

const HistoryView = ({ onViewReport, onRerunCheck, onRateContract }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const data = await getContractHistory();
      // Sort by date desc
      const sorted = data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      setHistory(sorted);
    } catch (err) {
      setError("Failed to load history.");
    } finally {
      setLoading(false);
    }
  };

  const handleRating = async (contractId, rating) => {
    try {
      // Optimistically update UI
      setHistory(prevHistory => 
        prevHistory.map(item => 
          item.contract_id === contractId 
            ? { ...item, user_rating: rating } 
            : item
        )
      );
      
      // Call the parent handler
      await onRateContract(contractId, rating);
    } catch (err) {
      // Revert on error
      fetchHistory();
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    }).format(date);
  };
  
  const getStatusConfig = (contract) => {
    const score = contract.compliance_score;
    const category = contract.compliance_category;
    
    if (score === null || score === undefined) {
      return {
        color: 'text-gray-500',
        bg: 'bg-gray-100',
        border: 'border-gray-200',
        icon: MinusCircle,
        label: 'Not Checked'
      };
    }

    if (category === 'compliant' || score >= 90) {
      return {
        color: 'text-emerald-700',
        bg: 'bg-emerald-50',
        border: 'border-emerald-200',
        icon: CheckCircle2,
        label: `Compliant • ${score}%`
      };
    }
    
    if (category === 'partially_compliant' || score >= 70) {
      return {
        color: 'text-amber-700',
        bg: 'bg-amber-50',
        border: 'border-amber-200',
        icon: AlertTriangle,
        label: `Partial • ${score}%`
      };
    }

    return {
      color: 'text-rose-700',
      bg: 'bg-rose-50',
      border: 'border-rose-200',
      icon: XCircle,
      label: `Non-Compliant • ${score}%`
    };
  };

  return (
    <div className="flex flex-col items-center w-full max-w-5xl mx-auto px-6 py-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      <div className="text-center mb-12 space-y-2">
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Contract History</h1>
        <p className="text-gray-500 max-w-md mx-auto">
          View your past contract analysis reports and track compliance status over time.
        </p>
      </div>

      {loading ? (
        <div className="w-full max-w-3xl space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-28 bg-gray-50 rounded-2xl animate-pulse border border-gray-100"></div>
          ))}
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center p-12 bg-red-50 rounded-3xl border border-red-100 text-red-600 max-w-lg">
          <AlertTriangle size={32} className="mb-3 opacity-80" />
          <p className="font-medium">{error}</p>
        </div>
      ) : history.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-16 text-center bg-gray-50 rounded-3xl border-2 border-dashed border-gray-200 max-w-lg w-full">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4 text-gray-400">
                <FileText size={32} />
            </div>
          <h3 className="text-lg font-semibold text-gray-900">No contracts yet</h3>
          <p className="text-gray-500 mt-1">Upload your first contract to see it here.</p>
        </div>
      ) : (
        <div className="w-full max-w-6xl grid gap-4">
          {history.map((item) => {
            const status = getStatusConfig(item);
            const StatusIcon = status.icon;
            // Extract the base color name for the decorative bar (e.g. 'bg-emerald-500')
            const accentColorClass = status.bg.includes('emerald') ? 'bg-emerald-500' : 
                                     status.bg.includes('amber') ? 'bg-amber-500' : 
                                     status.bg.includes('rose') ? 'bg-rose-500' : 'bg-gray-400';
            
            return (
              <div 
                key={item.contract_id}
                className="group relative bg-white p-6 rounded-2xl border border-gray-200 shadow-sm hover:shadow-md hover:border-teal-300 transition-all duration-300 flex items-center gap-8 overflow-hidden"
              >
                {/* Decorative side bar on hover */}
                <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${accentColorClass} opacity-0 group-hover:opacity-100 transition-opacity duration-300`}></div>

                {/* Icon */}
                <div className={`w-14 h-14 rounded-xl flex items-center justify-center shrink-0 transition-colors duration-300 ${status.bg} ${status.color}`}>
                  <FileText size={24} strokeWidth={1.5} />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 pr-4">
                  <h3 className="text-lg font-semibold text-gray-900 truncate">
                    {item.filename || "Untitled Contract"}
                  </h3>
                  
                  <div className="flex items-center gap-3 mt-2 flex-wrap">
                    <div className="flex items-center gap-1.5 text-sm text-gray-500">
                       <Calendar size={14} />
                       {formatDate(item.created_at)}
                    </div>
                    
                    <div className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${status.bg} ${status.color} ${status.border}`}>
                       <StatusIcon size={12} />
                       <span>{status.label}</span>
                    </div>

                    {item.scholar_status === 'pending' && (
                      <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border bg-purple-50 text-purple-700 border-purple-200">
                        <UserCheck size={12} />
                        <span>Scholar Review</span>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Actions */}
                <div className="flex items-center gap-3 shrink-0">
                  {/* Rating buttons */}
                  <div className="flex items-center gap-1.5 border-r border-gray-200 pr-4">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRating(item.contract_id, 1);
                      }}
                      className={`p-2 rounded-lg transition-colors ${
                        item.user_rating === 1 
                          ? 'bg-green-100 text-green-600' 
                          : 'text-gray-400 hover:bg-gray-100 hover:text-green-600'
                      }`}
                      title="Thumbs up"
                    >
                      <ThumbsUp size={16} />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRating(item.contract_id, -1);
                      }}
                      className={`p-2 rounded-lg transition-colors ${
                        item.user_rating === -1 
                          ? 'bg-red-100 text-red-600' 
                          : 'text-gray-400 hover:bg-gray-100 hover:text-red-600'
                      }`}
                      title="Thumbs down"
                    >
                      <ThumbsDown size={16} />
                    </button>
                  </div>
                  
                  {item.has_report && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onViewReport(item.contract_id);
                      }}
                      className="flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors text-sm font-medium whitespace-nowrap"
                    >
                      <Eye size={16} />
                      <span>View Report</span>
                    </button>
                  )}
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onRerunCheck(item.contract_id);
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium whitespace-nowrap"
                  >
                    <RefreshCcw size={16} />
                    <span>Re-run Check</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default HistoryView;
