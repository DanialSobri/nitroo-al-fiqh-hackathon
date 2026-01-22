import React, { useState } from 'react';
import HistoryView from '../components/HistoryView';
import ProcessingView from '../components/ProcessingView';
import { useNavigate } from 'react-router-dom';
import { checkCompliance, rateContract, getStoredReport } from '../api/client';

const HistoryPage = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleViewReport = async (contractId) => {
    try {
      setIsProcessing(true);
      
      // Fetch cached report (no re-analysis)
      const report = await getStoredReport(contractId);
      
      // Navigate to report page
      navigate(`/report/${contractId}`, { state: { report } });
    } catch (err) {
      console.error(err);
      setError('Failed to load report. The contract may not have been analyzed yet.');
      setIsProcessing(false);
    }
  };

  const handleRerunCheck = async (contractId) => {
    try {
      setIsProcessing(true);
      
      // Re-run compliance check (full re-analysis)
      await new Promise(resolve => setTimeout(resolve, 1000));
      const checkRes = await checkCompliance(contractId);
      
      // Navigate to report page
      navigate(`/report/${contractId}`, { state: { report: checkRes } });
    } catch (err) {
      console.error(err);
      setError('Failed to re-run compliance check.');
      setIsProcessing(false);
    }
  };

  const handleRateContract = async (contractId, rating) => {
    try {
      await rateContract(contractId, rating);
    } catch (err) {
      console.error(err);
      setError('Failed to submit rating.');
    }
  };

  return (
    <>
      {error && (
        <div className="absolute top-4 right-4 z-50 bg-red-50 text-red-600 px-4 py-3 rounded-lg shadow-sm border border-red-100 flex items-center gap-2 animate-in slide-in-from-top-2">
          <span>!</span>
          {error}
          <button onClick={() => setError(null)} className="ml-2 font-bold">&times;</button>
        </div>
      )}

      {isProcessing ? (
        <ProcessingView />
      ) : (
        <HistoryView 
          onViewReport={handleViewReport} 
          onRerunCheck={handleRerunCheck}
          onRateContract={handleRateContract}
        />
      )}
    </>
  );
};

export default HistoryPage;
