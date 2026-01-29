import React, { useState } from 'react';
import { CheckCircle, AlertTriangle, XCircle, ChevronDown, ChevronUp, FileText, ArrowLeft, Download, Share2, Library, Lightbulb, ArrowRight, UserCheck, Send, ExternalLink } from 'lucide-react';
import PDFViewer from './PDFViewer';

const ComplianceReport = ({ report, onBack, onSubmitToScholar }) => {
  const [expandedViolations, setExpandedViolations] = useState({});
  const [showScholarModal, setShowScholarModal] = useState(false);
  const [scholarNotes, setScholarNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showPDFViewer, setShowPDFViewer] = useState({ show: false, clause: '' });
  const [pdfHighlightPages, setPdfHighlightPages] = useState([]);

  if (!report) return null;

  const handleScholarSubmit = async () => {
    setSubmitting(true);
    try {
      await onSubmitToScholar(report.contract_id, scholarNotes);
      setShowScholarModal(false);
      setScholarNotes('');
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleViewInPDF = (pages, clause = '') => {
    setPdfHighlightPages(pages || []);
    setShowPDFViewer({ show: true, clause });
  };

  const toggleViolation = (index) => {
    setExpandedViolations(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score) => {
    if (score >= 90) return 'bg-green-50 border-green-200';
    if (score >= 70) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  return (
    <div className="w-full max-w-4xl mx-auto pb-20 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Header Navigation */}
      <div className="flex items-center justify-between mb-8 sticky top-0 bg-white/80 backdrop-blur-md py-4 z-10 border-b border-gray-100">
        <button 
          onClick={onBack}
          className="flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft size={18} />
          <span className="font-medium">Back to search</span>
        </button>
        <div className="flex gap-2">
           <button 
             onClick={() => setShowScholarModal(true)}
             className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
           >
             <UserCheck size={18} />
             <span>Submit to Scholar</span>
           </button>
           <button className="p-2 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors">
             <Share2 size={18} />
           </button>
           <button className="p-2 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors">
             <Download size={18} />
           </button>
        </div>
      </div>

      {/* Scholar Submission Modal */}
      {showScholarModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 animate-in zoom-in-95 duration-200">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                <UserCheck className="text-purple-600" size={24} />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Submit to Scholar</h3>
                <p className="text-sm text-gray-500">Request expert review of this contract</p>
              </div>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Additional Notes (Optional)
              </label>
              <textarea
                value={scholarNotes}
                onChange={(e) => setScholarNotes(e.target.value)}
                placeholder="Add any specific concerns or questions for the scholar..."
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                rows={4}
              />
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-blue-800 leading-relaxed">
                📋 Your contract will be reviewed by a qualified Shariah scholar. You'll be notified once the review is complete.
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowScholarModal(false);
                  setScholarNotes('');
                }}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                onClick={handleScholarSubmit}
                disabled={submitting}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    Submitting...
                  </>
                ) : (
                  <>
                    <Send size={16} />
                    Submit
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Score Card */}
      <div className="mb-10">
        <h1 className="text-3xl font-semibold text-gray-900 mb-6">Contract Analysis Report</h1>
        
        <div className={`p-8 rounded-2xl border ${getScoreBg(report.overall_score)} flex flex-col md:flex-row items-center justify-between gap-8 shadow-sm overflow-visible`}>
          <div className="flex items-center gap-6">
            <div className="relative w-32 h-32 flex items-center justify-center flex-shrink-0">
              <svg className="w-full h-full transform -rotate-90" style={{ overflow: 'visible' }}>
                <circle cx="64" cy="64" r="60" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-white/50" />
                <circle 
                  cx="64" 
                  cy="64" 
                  r="60" 
                  stroke="currentColor" 
                  strokeWidth="8" 
                  fill="transparent" 
                  strokeDasharray={2 * Math.PI * 60}
                  strokeDashoffset={2 * Math.PI * 60 * (1 - report.overall_score / 100)}
                  className={getScoreColor(report.overall_score)}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-3xl font-bold ${getScoreColor(report.overall_score)}`}>{report.overall_score}%</span>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Score</span>
              </div>
            </div>
            
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h2 className="text-2xl font-bold text-gray-900">
                  {report.category === 'compliant' && 'Shariah Compliant'}
                  {report.category === 'partially_compliant' && 'Partially Compliant'}
                  {report.category === 'non_compliant' && 'Non-Compliant'}
                </h2>
                {report.category === 'compliant' && <CheckCircle className="text-green-600" size={24} />}
                {report.category === 'partially_compliant' && <AlertTriangle className="text-yellow-600" size={24} />}
                {report.category === 'non_compliant' && <XCircle className="text-red-600" size={24} />}
              </div>
              <p className="text-gray-600 text-lg leading-relaxed max-w-xl">
               {report.category === 'compliant' 
                 ? "This contract adheres to the checked Shariah regulations." 
                 : "Several issues were detected that may violate Shariah principles. Review the details below."}
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-4 min-w-[200px]">
            <StatRow label="Regulations Checked" value={report.total_regulations_checked} />
            <StatRow label="Issues Found" value={report.violations_count} color="text-red-600" />
            <StatRow label="Passed Checks" value={report.compliant_count} color="text-green-600" />
          </div>
        </div>
      </div>

      {/* AI Summary */}
      <div className="mb-10">
        <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <FileText size={20} className="text-teal-600" />
          Executive Summary
        </h3>
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm text-gray-700 leading-relaxed space-y-4">
          {report.summary.split('\n').map((para, i) => (
             para.trim() && <p key={i}>{para}</p>
          ))}
        </div>
      </div>

      {/* Recommendations / Next Actions */}
      {report.recommendations && report.recommendations.length > 0 && (
        <div className="mb-10">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Lightbulb size={20} className="text-amber-500" />
            Recommended Next Actions
          </h3>
          <p className="text-sm text-gray-600 mb-4">These are AI-generated suggestions to improve Shariah compliance based on the analysis.</p>
          <div className="bg-gradient-to-br from-amber-50 to-orange-50 p-6 rounded-xl border border-amber-200 shadow-sm">
            <div className="space-y-3">
              {report.recommendations.map((recommendation, index) => (
                <div key={index} className="flex items-start gap-3 bg-white/70 backdrop-blur-sm p-4 rounded-lg border border-amber-100 hover:border-amber-300 transition-colors">
                  <div className="mt-0.5">
                    <ArrowRight size={18} className="text-amber-600 shrink-0" />
                  </div>
                  <p className="text-gray-800 leading-relaxed font-medium">{recommendation}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Violations Detail */}
      {report.violations && report.violations.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle size={20} className="text-red-500" />
            Compliance Issues
          </h3>
          
          <div className="space-y-4">
            {report.violations.map((violation, index) => (
              <div key={index} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden transition-all hover:shadow-md">
                <div 
                  className="p-5 flex items-start justify-between cursor-pointer bg-gray-50/50 hover:bg-gray-50"
                  onClick={() => toggleViolation(index)}
                >
                  <div className="flex gap-4">
                    <div className="mt-1 min-w-[24px]">
                      <XCircle size={24} className="text-red-500" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 text-lg mb-1">{violation.regulation_title}</h4>
                      <p className="text-sm text-gray-500 mb-2 font-medium">Severity: <span className="uppercase text-red-600">{violation.severity}</span></p>
                      {!expandedViolations[index] && (
                        <p className="text-gray-600 line-clamp-2">{violation.description}</p>
                      )}
                    </div>
                  </div>
                  <button className="text-gray-400 hover:text-gray-600">
                    {expandedViolations[index] ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </button>
                </div>
                
                {expandedViolations[index] && (
                  <div className="p-5 pt-3 border-t border-gray-100 bg-white animate-in slide-in-from-top-2 duration-200">
                    <div className="mt-2 space-y-4">
                      <div className="bg-red-50 p-4 rounded-lg border border-red-100">
                        <span className="text-xs font-bold text-red-800 uppercase tracking-wider block mb-2">Issue Description</span>
                        <p className="text-gray-800 leading-relaxed">{violation.description}</p>
                      </div>
                      
                      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <span className="text-xs font-bold text-gray-500 uppercase tracking-wider block mb-2">Violated Contract Section</span>
                        <p className="text-gray-700 italic leading-relaxed">"{violation.violated_clause}"</p>
                      </div>
                      
                      {violation.reasoning && (
                        <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
                          <span className="text-xs font-bold text-blue-800 uppercase tracking-wider block mb-2">AI Reasoning</span>
                          <p className="text-blue-900 leading-relaxed whitespace-pre-line">{violation.reasoning}</p>
                        </div>
                      )}
                      
                      <div className="flex gap-3">
                        {violation.regulation_reference && (
                          <div className="flex-1 flex items-start gap-2 text-sm text-gray-600 bg-blue-50 p-3 rounded-lg border border-blue-100">
                            <Library size={16} className="mt-0.5 text-blue-600 shrink-0" />
                            <div>
                              <span className="font-semibold text-blue-900 block mb-1">Reference:</span>
                              <span>{violation.regulation_reference}</span>
                            </div>
                          </div>
                        )}
                        
                        {violation.violated_clause && (
                          <button
                            onClick={() => handleViewInPDF(violation.pages, violation.violated_clause)}
                            className="flex items-center gap-2 px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium text-sm"
                          >
                            <FileText size={16} />
                            {violation.pages && violation.pages.length > 0 
                              ? `View on Page ${violation.pages.map(p => p + 1).join(', ')}`
                              : 'View in PDF'
                            }
                            <ExternalLink size={14} />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* PDF Viewer Modal */}
      {showPDFViewer.show && (
        <PDFViewer
          contractId={report.contract_id}
          highlightPages={pdfHighlightPages}
          violatedClause={showPDFViewer.clause}
          onClose={() => setShowPDFViewer({ show: false, clause: '' })}
        />
      )}
    </div>
  );
};

const StatRow = ({ label, value, color = "text-gray-900" }) => (
  <div className="flex items-center justify-between border-b border-gray-100 pb-2 last:border-0 last:pb-0">
    <span className="text-sm text-gray-500 font-medium">{label}</span>
    <span className={`font-bold text-lg ${color}`}>{value}</span>
  </div>
);

export default ComplianceReport;
