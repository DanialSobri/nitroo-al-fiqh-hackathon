import React, { useEffect, useState } from 'react';
import { CheckCircle2, Loader2, FileText, Search, Scale, FileCheck } from 'lucide-react';

const ProcessingView = () => {
  const [currentStage, setCurrentStage] = useState(0);

  const stages = [
    { label: "Uploading Contract", icon: FileText, delay: 1000 },
    { label: "Extracting Text & Embedding", icon: Search, delay: 3000 },
    { label: "Retrieving Shariah Regulations", icon: Scale, delay: 2000 },
    { label: "Analyzing Compliance Violations", icon: FileCheck, delay: 4000 }
  ];

  useEffect(() => {
    let timeout;
    if (currentStage < stages.length) {
      timeout = setTimeout(() => {
        if (currentStage < stages.length - 1) { // Don't auto-complete the last stage, wait for app logic
           setCurrentStage(prev => prev + 1);
        }
      }, stages[currentStage].delay);
    }
    return () => clearTimeout(timeout);
  }, [currentStage]);

  return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-[60vh] w-full max-w-2xl mx-auto px-6">
      <div className="text-center mb-12">
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">Analyzing Contract</h2>
        <p className="text-gray-500">Please wait while our agent reviews your document against Shariah standards.</p>
      </div>

      <div className="w-full space-y-6">
        {stages.map((stage, index) => {
          const isActive = index === currentStage;
          const isCompleted = index < currentStage;
          const isPending = index > currentStage;
          const Icon = stage.icon;

          return (
            <div 
              key={index}
              className={`flex items-center gap-4 p-4 rounded-xl border transition-all duration-500
                ${isPending ? 'border-transparent opacity-40' : ''}
                ${isActive ? 'border-green-100 bg-green-50/50 scale-[1.02] shadow-sm' : ''}
                ${isCompleted ? 'border-gray-100 bg-white' : ''}
              `}
            >
              <div className={`
                w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-colors duration-500
                ${isActive ? 'bg-green-600 text-white' : ''}
                ${isCompleted ? 'bg-green-100 text-green-600' : ''}
                ${isPending ? 'bg-gray-100 text-gray-400' : ''}
              `}>
                {isCompleted ? (
                   <CheckCircle2 size={20} />
                ) : isActive ? (
                   <Loader2 size={20} className="animate-spin" />
                ) : (
                  <Icon size={18} />
                )}
              </div>

              <div className="flex-1">
                 <h4 className={`font-medium transition-colors duration-300 ${isActive ? 'text-green-900' : 'text-gray-700'}`}>
                   {stage.label}
                 </h4>
                 {isActive && (
                   <p className="text-xs text-green-600 mt-0.5 animate-pulse">Processing...</p>
                 )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ProcessingView;
