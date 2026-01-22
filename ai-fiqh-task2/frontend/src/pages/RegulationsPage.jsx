import React, { useState, useEffect } from 'react';
import { BookOpen, Search, Plus, X, FileText, ChevronLeft, ChevronRight } from 'lucide-react';
import { addRegulations, listRegulations, searchRegulations } from '../api/client';

const RegulationsPage = () => {
  const [regulations, setRegulations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  
  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);
  const [totalItems, setTotalItems] = useState(0);
  
  // Form states
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    category: '',
    reference: ''
  });

  useEffect(() => {
    loadRegulations();
  }, [currentPage]);

  const loadRegulations = async () => {
    try {
      setLoading(true);
      const offset = (currentPage - 1) * itemsPerPage;
      const data = await listRegulations(offset, itemsPerPage);
      
      // Handle both array response and paginated response with metadata
      if (Array.isArray(data)) {
        setRegulations(data);
        setTotalItems(data.length);
      } else if (data.regulations) {
        setRegulations(Array.isArray(data.regulations) ? data.regulations : []);
        setTotalItems(data.total || data.regulations.length);
      } else {
        setRegulations([]);
        setTotalItems(0);
      }
      
      setError(null);
    } catch (err) {
      setError('Failed to load regulations');
      console.error(err);
      setRegulations([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    try {
      setLoading(true);
      const data = await searchRegulations(searchQuery, 20);
      setSearchResults(data.results || []);
      setError(null);
    } catch (err) {
      setError('Failed to search regulations');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddRegulation = async (e) => {
    e.preventDefault();
    
    if (!formData.title || !formData.content || !formData.category) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setLoading(true);
      await addRegulations([formData]);
      
      // Reset form
      setFormData({
        title: '',
        content: '',
        category: '',
        reference: ''
      });
      
      setShowAddForm(false);
      loadRegulations();
      setError(null);
    } catch (err) {
      setError('Failed to add regulation');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  // Ensure displayList is always an array
  const displayList = searchResults.length > 0 ? searchResults : (Array.isArray(regulations) ? regulations : []);

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Shariah Regulations Management</h1>
        <p className="text-gray-600">Add, search, and manage Shariah regulations and rules</p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Action Bar */}
      <div className="mb-6 flex gap-4 items-center">
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors"
        >
          {showAddForm ? <X className="h-5 w-5" /> : <Plus className="h-5 w-5" />}
          {showAddForm ? 'Cancel' : 'Add Regulation'}
        </button>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex-1 flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search regulations..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
            />
          </div>
          <button
            type="submit"
            className="px-6 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
          >
            Search
          </button>
          {searchResults.length > 0 && (
            <button
              type="button"
              onClick={() => {
                setSearchQuery('');
                setSearchResults([]);
              }}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Clear
            </button>
          )}
        </form>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <div className="mb-6 bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Add New Regulation</h2>
          <form onSubmit={handleAddRegulation} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Content <span className="text-red-500">*</span>
              </label>
              <textarea
                name="content"
                value={formData.content}
                onChange={handleInputChange}
                rows={6}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="category"
                  value={formData.category}
                  onChange={handleInputChange}
                  placeholder="e.g., Riba Definition"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Reference
                </label>
                <input
                  type="text"
                  name="reference"
                  value={formData.reference}
                  onChange={handleInputChange}
                  placeholder="e.g., Qur'an 2:275-279"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors disabled:opacity-50"
              >
                {loading ? 'Adding...' : 'Add Regulation'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Regulations List */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              {searchResults.length > 0 ? `Search Results (${searchResults.length})` : `All Regulations (${regulations.length})`}
            </h2>
            {loading && (
              <div className="text-sm text-gray-500">Loading...</div>
            )}
          </div>
        </div>

        <div className="divide-y divide-gray-200">
          {displayList.length === 0 ? (
            <div className="px-6 py-12 text-center text-gray-500">
              <BookOpen className="h-12 w-12 mx-auto mb-3 text-gray-400" />
              <p>No regulations found</p>
            </div>
          ) : (
            displayList.map((reg) => (
              <div key={reg.id || reg.regulation_id} className="px-6 py-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-start gap-4">
                  <FileText className="h-5 w-5 text-teal-600 mt-1 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 mb-2">
                      {reg.title}
                    </h3>
                    
                    <p className="text-gray-700 mb-3 leading-relaxed">
                      {reg.content}
                    </p>

                    <div className="flex flex-wrap gap-4 text-sm">
                      <div className="flex items-center gap-1">
                        <span className="font-medium text-gray-700">Category:</span>
                        <span className="px-2 py-1 bg-teal-100 text-teal-800 rounded">
                          {reg.category}
                        </span>
                      </div>

                      {reg.reference && (
                        <div className="flex items-center gap-1">
                          <span className="font-medium text-gray-700">Reference:</span>
                          <span className="text-gray-600">{reg.reference}</span>
                        </div>
                      )}

                      {reg.score !== undefined && (
                        <div className="flex items-center gap-1">
                          <span className="font-medium text-gray-700">Relevance:</span>
                          <span className="text-gray-600">{(reg.score * 100).toFixed(1)}%</span>
                        </div>
                      )}

                      {reg.created_at && (
                        <div className="text-gray-500">
                          Added: {new Date(reg.created_at).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Pagination Controls */}
        {searchResults.length === 0 && regulations.length > 0 && (
          <div className="px-6 py-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, totalItems)} of {totalItems} regulations
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                  className="flex items-center gap-1 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </button>
                
                <div className="flex items-center gap-1">
                  {[...Array(Math.ceil(totalItems / itemsPerPage))].map((_, idx) => {
                    const pageNum = idx + 1;
                    const totalPages = Math.ceil(totalItems / itemsPerPage);
                    
                    // Show first page, last page, current page, and pages around current
                    if (
                      pageNum === 1 ||
                      pageNum === totalPages ||
                      (pageNum >= currentPage - 1 && pageNum <= currentPage + 1)
                    ) {
                      return (
                        <button
                          key={pageNum}
                          onClick={() => setCurrentPage(pageNum)}
                          className={`px-3 py-2 rounded-lg transition-colors ${
                            currentPage === pageNum
                              ? 'bg-teal-600 text-white'
                              : 'border border-gray-300 hover:bg-gray-50'
                          }`}
                        >
                          {pageNum}
                        </button>
                      );
                    } else if (
                      pageNum === currentPage - 2 ||
                      pageNum === currentPage + 2
                    ) {
                      return <span key={pageNum} className="px-2 text-gray-400">...</span>;
                    }
                    return null;
                  })}
                </div>
                
                <button
                  onClick={() => setCurrentPage(prev => Math.min(Math.ceil(totalItems / itemsPerPage), prev + 1))}
                  disabled={currentPage >= Math.ceil(totalItems / itemsPerPage)}
                  className="flex items-center gap-1 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RegulationsPage;
