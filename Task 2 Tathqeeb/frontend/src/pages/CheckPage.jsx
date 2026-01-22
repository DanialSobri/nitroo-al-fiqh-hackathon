import React, { useState } from 'react';
import UploadView from '../components/UploadView';
import ProcessingView from '../components/ProcessingView';
import { useNavigate } from 'react-router-dom';
import { uploadContract, checkCompliance } from '../api/client';

const CheckPage = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleFileUpload = async (file) => {
    try {
      setError(null);
      setIsProcessing(true);

      // Upload
      const uploadRes = await uploadContract(file);

      // Analyze
      await new Promise(resolve => setTimeout(resolve, 2500));

      const checkRes = await checkCompliance(uploadRes.contract_id);

      // Navigate to report page
      navigate(`/report/${uploadRes.contract_id}`, { state: { report: checkRes } });
    } catch (err) {
      console.error(err);
      setError('Failed to process contract. Please try again.');
      setIsProcessing(false);
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
        <UploadView onFileSelect={handleFileUpload} />
      )}
    </>
  );
};

export default CheckPage;