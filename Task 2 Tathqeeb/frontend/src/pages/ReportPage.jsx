import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import ComplianceReport from '../components/ComplianceReport';
import { submitToScholar, getStoredReport } from '../api/client';

const ReportPage = () => {
  const { contractId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [report, setReport] = useState(location.state?.report || null);
  const [loading, setLoading] = useState(!location.state?.report);
  const [error, setError] = useState(null);

  useEffect(() => {
    // If no report in state, fetch it
    if (!report && contractId) {
      fetchReport();
    }
  }, [contractId, report]);

  const fetchReport = async () => {
    try {
      const fetchedReport = await getStoredReport(contractId);
      setReport(fetchedReport);
    } catch (err) {
      console.error(err);
      setError('Failed to load report. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/');
  };

  const handleSubmitToScholar = async (contractId, notes) => {
    try {
      await submitToScholar(contractId, notes);
      setError(null);
      // Show success message
      const successMsg = document.createElement('div');
      successMsg.className = 'fixed top-4 right-4 z-50 bg-green-50 text-green-600 px-4 py-3 rounded-lg shadow-sm border border-green-100 flex items-center gap-2 animate-in slide-in-from-top-2';
      successMsg.innerHTML = '<span>✓</span> Successfully submitted to scholar for review!';
      document.body.appendChild(successMsg);
      setTimeout(() => successMsg.remove(), 3000);
    } catch (err) {
      console.error(err);
      setError('Failed to submit to scholar.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-teal-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <p className="text-red-600 mb-4">{error || 'Report not found'}</p>
        <button 
          onClick={handleBack}
          className="px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700"
        >
          Go Back
        </button>
      </div>
    );
  }

  return (
    <ComplianceReport 
      report={report} 
      onBack={handleBack}
      onSubmitToScholar={handleSubmitToScholar}
    />
  );
};

export default ReportPage;
