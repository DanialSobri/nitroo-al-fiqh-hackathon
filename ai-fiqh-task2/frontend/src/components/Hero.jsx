import React, { useState, useRef } from 'react';
import { Paperclip, ArrowRight, Focus, Globe, FileText, Upload } from 'lucide-react';

const Hero = ({ onFileUpload, isProcessing }) => {
  const [file, setFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (file) {
      onFileUpload(file);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current.click();
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] w-full px-6">
      <div className="w-full max-w-2xl mx-auto">
        <div className="flex flex-col items-center mb-8 space-y-3 text-center">
          <h1 className="text-3xl font-semibold text-gray-900 tracking-tight">
            AI Fiqh Compliance Agent
          </h1>
          <p className="text-base text-gray-500 font-normal max-w-lg">
            Where knowledge begins. Check your contracts against Shariah regulations.
          </p>
        </div>

        <div className="w-full relative group">
          <div className="absolute inset-0 bg-gray-200/50 rounded-2xl blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <form onSubmit={handleSubmit} className="relative w-full bg-white rounded-2xl border border-gray-200 shadow-sm hover:border-gray-300 hover:shadow-md transition-all duration-200 overflow-hidden">
            <div className="p-4">
              <textarea
                placeholder={file ? `Selected: ${file.name}` : "Upload a contract PDF or ask a question..."}
                className="w-full resize-none outline-none text-base text-gray-700 placeholder-gray-400 min-h-[60px] max-h-[200px] bg-transparent"
                rows={2}
                readOnly={!!file}
              />
            
            <input 
              type="file" 
              ref={fileInputRef}
              onChange={handleFileChange} 
              className="hidden" 
              accept=".pdf"
            />
            
            {file && (
              <div className="flex items-center gap-2 mb-2 p-2 bg-teal-50 rounded-lg w-fit text-teal-700 text-sm">
                <FileText size={16} />
                <span className="truncate max-w-[250px]">{file.name}</span>
                <button 
                  type="button" 
                  onClick={(e) => { e.stopPropagation(); setFile(null); }}
                  className="ml-2 hover:bg-teal-100 rounded-full p-0.5 text-base"
                >
                  &times;
                </button>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between px-4 pb-3 pt-1">
            <div className="flex items-center gap-2">
              <button 
                type="button"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium text-gray-600 bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <Focus size={15} className="text-gray-500" />
                <span>Focus</span>
              </button>
              <button 
                type="button"
                onClick={triggerFileInput}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${file ? 'bg-teal-50 text-teal-700' : 'text-gray-600 bg-gray-50 hover:bg-gray-100'}`}
              >
                <Paperclip size={15} className={file ? "text-teal-600" : "text-gray-500"} />
                <span>Attach</span>
              </button>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 text-xs text-gray-400 font-medium">
                <div className="w-4 h-4 rounded-full border border-gray-200 flex items-center justify-center text-[10px]">?</div>
                Pro
              </div>
              <button 
                type="submit"
                disabled={!file || isProcessing}
                className={`p-2 rounded-full transition-all duration-200 ${file ? 'bg-teal-600 text-white shadow-md hover:bg-teal-700 hover:scale-105' : 'bg-gray-100 text-gray-300 cursor-not-allowed'}`}
              >
                {isProcessing ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                ) : (
                  <ArrowRight size={18} />
                )}
              </button>
            </div>
          </div>
        </form>
      </div>

      <div className="mt-6 flex flex-wrap justify-center gap-2">
        <SuggestionPill icon={<Upload size={13} />} text="Upload Islamic Loan Agreement" />
        <SuggestionPill icon={<FileText size={13} />} text="Check Murabaha Contract" />
        <SuggestionPill icon={<Globe size={13} />} text="Latest BNM Regulations" />
      </div>
    </div>
  </div>
  );
};

const SuggestionPill = ({ icon, text }) => (
  <button className="flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-200 rounded-full text-sm text-gray-600 hover:bg-gray-50 hover:border-gray-300 transition-all shadow-sm">
    <span className="text-gray-400">{icon}</span>
    {text}
  </button>
);

export default Hero;
