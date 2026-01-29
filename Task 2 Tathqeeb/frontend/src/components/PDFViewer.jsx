import React, { useState, useEffect, useCallback } from 'react';
import { X, ZoomIn, ZoomOut, ChevronLeft, ChevronRight, Download } from 'lucide-react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url
).toString();

const PDFViewer = ({ contractId, highlightPages = [], violatedClause = '', onClose }) => {
  const [pdfUrl, setPdfUrl] = useState(null);
  const [pdfBlob, setPdfBlob] = useState(null);
  const [currentPage, setCurrentPage] = useState(highlightPages[0] || 1);
  const [scale, setScale] = useState(1.2);
  const [loading, setLoading] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);
  const [numPages, setNumPages] = useState(null);

  const customTextRenderer = useCallback((textItem) => {
    if (!violatedClause || violatedClause.length < 10) return textItem.str;
    
    // Extract meaningful keywords, excluding common stop words
    const stopWords = new Set(['the', 'shall', 'be', 'at', 'a', 'of', 'per', 'on', 'and', 'to', 'is', 'in', 'for', 'with', 'by', 'as', 'an', 'are', 'was', 'were', 'has', 'have', 'had', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those']);
    const words = violatedClause.toLowerCase()
      .split(/\s+/)
      .filter(w => w.length > 4 && !stopWords.has(w));
    
    const lowerText = textItem.str.toLowerCase();
    
    // Count how many keywords match
    const matchCount = words.filter(word => lowerText.includes(word)).length;
    
    // Calculate match ratio
    const matchRatio = matchCount / words.length;
    
    // Only highlight if high similarity or multiple matches in substantial text
    if (matchRatio > 0.5 || (matchCount >= 4 && textItem.str.length > 30)) {
      return `<mark style="background-color: yellow;">${textItem.str}</mark>`;
    }
    return textItem.str;
  }, [violatedClause]);

  useEffect(() => {
    if (contractId) {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const url = `${apiUrl}/contracts/pdf/${contractId}`;
      setPdfUrl(url);
      fetch(url)
        .then(response => response.blob())
        .then(blob => {
          setPdfBlob(blob);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [contractId]);

  useEffect(() => {
    if (highlightPages && highlightPages.length > 0) {
      setCurrentPage(highlightPages[0]);
      setReloadKey(prev => prev + 1);
    }
  }, [highlightPages]);

  const handleZoomIn = () => setScale(prev => Math.min(prev + 0.2, 2.5));
  const handleZoomOut = () => setScale(prev => Math.max(prev - 0.2, 0.5));

  const handleDownload = () => {
    if (pdfUrl) {
      window.open(pdfUrl, '_blank');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-6xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center gap-4">
            <h3 className="text-lg font-semibold text-gray-900">Contract PDF</h3>
            {highlightPages && highlightPages.length > 0 && (
              <div className="flex items-center gap-2 px-3 py-1 bg-yellow-100 border border-yellow-300 rounded-lg">
                <span className="text-sm font-medium text-yellow-900">
                  📍 Violation on page{highlightPages.length > 1 ? 's' : ''}: {highlightPages.map(p => p + 1).join(', ')}
                </span>
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            {/* Download Button */}
            <button
              onClick={handleDownload}
              className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-sm font-medium"
              title="Download PDF"
            >
              <Download size={16} />
              Download
            </button>

            {/* Zoom Controls */}
            <div className="flex items-center gap-1 mr-2 bg-gray-100 rounded-lg p-1">
              <button
                onClick={handleZoomOut}
                className="p-2 hover:bg-white rounded transition-colors"
                title="Zoom Out"
              >
                <ZoomOut size={18} />
              </button>
              <span className="px-3 text-sm font-medium text-gray-700 min-w-[60px] text-center">
                {Math.round(scale * 100)}%
              </span>
              <button
                onClick={handleZoomIn}
                className="p-2 hover:bg-white rounded transition-colors"
                title="Zoom In"
              >
                <ZoomIn size={18} />
              </button>
            </div>

            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Highlighted Clause Info */}
        {violatedClause && (
          <div className="px-4 py-3 bg-amber-50 border-b border-amber-200">
            <p className="text-sm text-amber-900">
              <span className="font-semibold">Looking for:</span> "{violatedClause.substring(0, 150)}{violatedClause.length > 150 ? '...' : ''}"
            </p>
          </div>
        )}

        {/* PDF Content */}
        <div className="flex-1 overflow-auto bg-gray-800">
          {loading && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-white">Loading PDF...</p>
              </div>
            </div>
          )}
          
          {pdfUrl && (
            <div className="flex justify-center items-start p-8">
              <Document
                file={pdfBlob}
                onLoadSuccess={({ numPages }) => {
                  setNumPages(numPages);
                  setLoading(false);
                }}
                onLoadError={() => setLoading(false)}
                loading=""
              >
                <Page
                  key={reloadKey}
                  pageNumber={currentPage + 1}
                  scale={scale}
                  renderTextLayer={true}
                  customTextRenderer={customTextRenderer}
                  className="bg-white shadow-2xl"
                >
                  <style>{`
                    .react-pdf__Page__textContent mark {
                      background-color: yellow !important;
                      padding: 2px 0;
                    }
                  `}</style>
                </Page>
              </Document>
            </div>
          )}
        </div>

        {/* Footer with Page Navigation */}
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          <div className="flex items-center justify-center gap-4">
            {/* Page Navigation */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                disabled={currentPage === 0}
                className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                title="Previous Page"
              >
                <ChevronLeft size={16} />
                Prev
              </button>
              
              <span className="text-sm text-gray-600 min-w-[80px] text-center">
                Page {currentPage + 1} of {numPages || '?'}
              </span>
              
              <button
                onClick={() => setCurrentPage(Math.min((numPages || 1) - 1, currentPage + 1))}
                disabled={currentPage >= (numPages || 1) - 1}
                className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                title="Next Page"
              >
                Next
                <ChevronRight size={16} />
              </button>
            </div>

            {highlightPages && highlightPages.length > 1 && (
              <>
                <div className="w-px h-8 bg-gray-300"></div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      const currentIndex = highlightPages.indexOf(currentPage);
                      if (currentIndex > 0) {
                        setCurrentPage(highlightPages[currentIndex - 1]);
                      }
                    }}
                    disabled={highlightPages.indexOf(currentPage) === 0}
                    className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft size={16} />
                    Previous Violation
                  </button>
                  
                  <span className="text-sm text-gray-600">
                    Violation {highlightPages.indexOf(currentPage) + 1} of {highlightPages.length}
                  </span>
                  
                  <button
                    onClick={() => {
                      const currentIndex = highlightPages.indexOf(currentPage);
                      if (currentIndex < highlightPages.length - 1) {
                        setCurrentPage(highlightPages[currentIndex + 1]);
                      }
                    }}
                    disabled={highlightPages.indexOf(currentPage) === highlightPages.length - 1}
                    className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Next Violation
                    <ChevronRight size={16} />
                  </button>
                </div>
              </>
            )}
            
            {(!highlightPages || highlightPages.length <= 1) && (
              <span className="text-sm text-gray-600">
                Showing page {currentPage + 1}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PDFViewer;
