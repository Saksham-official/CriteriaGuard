import React, { useState } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';

import API_BASE_URL from '../api/config';

const BidderUpload = () => {
  const { tenderId } = useParams();
  const navigate = useNavigate();
  const [bidderName, setBidderName] = useState('');
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleUpload = async () => {
    if (!bidderName || files.length === 0) {
      setError('Please provide bidder name and at least one document.');
      return;
    }

    const formData = new FormData();
    formData.append('tender_id', tenderId);
    formData.append('bidder_name', bidderName);
    formData.append('officer_id', localStorage.getItem('officerId') || 'SYSTEM_OR_OFFICER');
    files.forEach(file => {
      formData.append('files', file);
    });

    setLoading(true);
    setError('');
    setMessage('');

    try {
      await axios.post(`${API_BASE_URL}/api/bidders/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setMessage(`Documents for ${bidderName} are now being processed!`);
      setBidderName('');
      setFiles([]);
      // You could navigate to a dashboard here
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred during upload.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-12 px-6">
      <div className="bg-white rounded-2xl shadow-xl p-8 max-w-2xl w-full">
        <h1 className="text-3xl font-bold text-gray-800 mb-6 text-center">Add Bidder Submission</h1>
        <p className="text-gray-600 mb-8 text-center">
          Upload certificates, financial statements, and supporting documents for a bidder.
        </p>

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Bidder Name / Company Name</label>
            <input 
              type="text" 
              value={bidderName}
              onChange={(e) => setBidderName(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
              placeholder="e.g. Sharma Constructions"
            />
          </div>

          <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 flex flex-col items-center justify-center bg-gray-50 hover:bg-gray-100 transition duration-300 cursor-pointer">
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.jpg,.jpeg,.png,.tiff"
              onChange={handleFileChange}
              className="hidden"
              id="file-upload-multiple"
            />
            <label htmlFor="file-upload-multiple" className="cursor-pointer flex flex-col items-center w-full">
              <svg className="w-12 h-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
              <span className="text-blue-600 font-medium hover:text-blue-800 transition">
                {files.length > 0 ? `${files.length} files selected` : 'Click to select multiple files'}
              </span>
              {files.length > 0 && (
                <ul className="mt-4 text-sm text-gray-500 list-disc text-left">
                  {files.map((f, i) => <li key={i}>{f.name}</li>)}
                </ul>
              )}
            </label>
          </div>

          {error && <div className="text-red-500 text-sm text-center bg-red-50 py-2 rounded">{error}</div>}
          {message && <div className="text-green-600 text-sm text-center bg-green-50 py-2 rounded">{message}</div>}

          <div className="flex gap-4 pt-4">
            <button
              onClick={() => navigate(`/dashboard/${tenderId}`)}
              className="w-1/3 py-3 rounded-xl font-bold text-gray-700 bg-gray-200 hover:bg-gray-300 transition duration-300"
            >
              Go to Dashboard
            </button>
            <button
              onClick={handleUpload}
              disabled={loading || !bidderName || files.length === 0}
              className={`w-2/3 py-3 rounded-xl font-bold text-white shadow-md transition duration-300 ${
                loading || !bidderName || files.length === 0 ? 'bg-blue-300 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 hover:shadow-lg'
              }`}
            >
              {loading ? 'Processing Documents...' : 'Start Extraction (DocProbe)'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BidderUpload;
