import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, File, AlertCircle } from 'lucide-react';

const UploadView = ({ onFileSelect }) => {
  const [error, setError] = useState(null);

  const onDrop = useCallback((acceptedFiles, fileRejections) => {
    setError(null);
    
    if (fileRejections.length > 0) {
      setError("Please upload a valid PDF file.");
      return;
    }

    if (acceptedFiles?.length > 0) {
      const file = acceptedFiles[0];
      if (file.type !== 'application/pdf') {
        setError("Only PDF files are allowed.");
        return;
      }
      onFileSelect(file);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    multiple: false
  });

  return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-[70vh] w-full max-w-4xl mx-auto px-6 fade-in duration-500">
      <div className="text-center mb-10 space-y-3">
        <h1 className="text-4xl font-bold text-gray-900 tracking-tight">
          Tathqeeb AI Compliance Checker
        </h1>
        <p className="text-lg text-gray-500 max-w-2xl mx-auto">
          Upload your Islamic finance contracts to automatically analyze Shariah compliance, detect violations, and generate detailed reports.
        </p>
      </div>

      <div 
        {...getRootProps()} 
        className={`w-full max-w-2xl text-center p-12 rounded-3xl border-2 border-dashed transition-all duration-300 cursor-pointer relative overflow-hidden group
          ${isDragActive 
            ? 'border-teal-500 bg-teal-50 shadow-lg scale-[1.01]' 
            : 'border-gray-200 hover:border-teal-400 hover:bg-gray-50/50 hover:shadow-md'
          }
          ${error ? 'border-red-300 bg-red-50/30' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center gap-6 relative z-10">
          <div className={`w-20 h-20 rounded-2xl flex items-center justify-center transition-colors duration-300 ${isDragActive ? 'bg-teal-100 text-teal-600' : 'bg-gray-100 text-gray-400 group-hover:bg-teal-50 group-hover:text-teal-500'}`}>
            <Upload size={36} strokeWidth={1.5} />
          </div>

          <div className="space-y-2">
            <h3 className="text-xl font-semibold text-gray-900">
              {isDragActive ? "Drop your contract here" : "Upload Contract"}
            </h3>
            <p className="text-gray-500">
              Drag & drop your PDF file here, or click to browse
            </p>
          </div>
          
          <div className="flex items-center gap-4 text-xs text-gray-400 uppercase tracking-widest font-medium mt-4">
            <span className="flex items-center gap-1.5"><File size={14} /> PDF Support</span>
            <span className="w-1 h-1 rounded-full bg-gray-300"></span>
            <span className="flex items-center gap-1.5"><FileText size={14} /> Max 10MB</span>
          </div>
        </div>

        {/* Decorative background gradients */}
        <div className="absolute top-0 left-1/4 w-1/2 h-1/2 bg-teal-500/5 rounded-full blur-3xl -z-0 transform -translate-y-1/2 pointer-events-none"></div>
      </div>

      {error && (
        <div className="mt-6 flex items-center gap-2 text-red-600 bg-red-50 px-4 py-2 rounded-lg border border-red-100 animate-in slide-in-from-top-2">
          <AlertCircle size={16} />
          <span className="text-sm font-medium">{error}</span>
        </div>
      )}
    </div>
  );
};

export default UploadView;
