import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import Upload from './pages/Upload';
import CriteriaReview from './pages/CriteriaReview';
import BidderUpload from './pages/BidderUpload';
import Dashboard from './pages/Dashboard';
import BidderDetail from './pages/BidderDetail';
import ReviewQueue from './pages/ReviewQueue';
import AuditTrail from './pages/AuditTrail';
import ComparativeMatrix from './pages/ComparativeMatrix';
import BidderProcessing from './pages/BidderProcessing';
import Header from './components/Header';

function App() {
  return (
    <Router>
      <div className="font-sans text-gray-900">
        <Header />
        <div className="pt-24">
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/criteria-review/:tenderId" element={<CriteriaReview />} />
            <Route path="/bidder-upload/:tenderId" element={<BidderUpload />} />
            <Route path="/bidder-processing/:tenderId/:bidderId" element={<BidderProcessing />} />
            <Route path="/dashboard/:tenderId" element={<Dashboard />} />
            <Route path="/bidder/:tenderId/:bidderId" element={<BidderDetail />} />
            <Route path="/review-queue/:tenderId" element={<ReviewQueue />} />
            <Route path="/audit-trail" element={<AuditTrail />} />
            <Route path="/comparative-matrix/:tenderId" element={<ComparativeMatrix />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
