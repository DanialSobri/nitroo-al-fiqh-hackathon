import React, { useEffect, useState } from 'react';
import { BarChart3, TrendingUp, ThumbsUp, ThumbsDown, AlertTriangle, CheckCircle, FileText, Activity } from 'lucide-react';
import { getAnalytics } from '../api/client';

const AnalyticsView = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const data = await getAnalytics();
      setAnalytics(data);
    } catch (err) {
      setError("Failed to load analytics.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-teal-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-4 text-gray-500">Loading analytics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <AlertTriangle size={48} className="text-red-500 mb-4" />
        <p className="text-red-600 font-medium">{error}</p>
      </div>
    );
  }

  if (!analytics) return null;

  return (
    <div className="w-full max-w-6xl mx-auto px-6 py-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight mb-2">Analytics Dashboard</h1>
        <p className="text-gray-500">Comprehensive insights into contract compliance and user feedback</p>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        <MetricCard
          icon={<FileText className="text-teal-600" size={24} />}
          label="Total Contracts"
          value={analytics.total_contracts}
          bgColor="bg-teal-50"
        />
        <MetricCard
          icon={<Activity className="text-blue-600" size={24} />}
          label="Avg Compliance Score"
          value={`${analytics.avg_compliance_score}%`}
          bgColor="bg-blue-50"
        />
        <MetricCard
          icon={<ThumbsUp className="text-green-600" size={24} />}
          label="Thumbs Up"
          value={analytics.total_thumbs_up}
          bgColor="bg-green-50"
        />
        <MetricCard
          icon={<ThumbsDown className="text-red-600" size={24} />}
          label="Thumbs Down"
          value={analytics.total_thumbs_down}
          bgColor="bg-red-50"
        />
      </div>

      {/* User Satisfaction */}
      <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <TrendingUp size={20} className="text-teal-600" />
          User Satisfaction Rate
        </h3>
        <div className="flex items-center gap-6">
          <div className="relative w-32 h-32">
            <svg className="w-full h-full transform -rotate-90">
              <circle cx="64" cy="64" r="56" stroke="currentColor" strokeWidth="10" fill="transparent" className="text-gray-200" />
              <circle 
                cx="64" 
                cy="64" 
                r="56" 
                stroke="currentColor" 
                strokeWidth="10" 
                fill="transparent" 
                strokeDasharray={2 * Math.PI * 56}
                strokeDashoffset={2 * Math.PI * 56 * (1 - analytics.rating_satisfaction / 100)}
                className="text-green-500"
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-bold text-gray-900">{analytics.rating_satisfaction}%</span>
              <span className="text-xs text-gray-500">Satisfied</span>
            </div>
          </div>
          <div className="flex-1">
            <p className="text-gray-700 leading-relaxed">
              Based on {analytics.total_thumbs_up + analytics.total_thumbs_down} user ratings, 
              {analytics.rating_satisfaction >= 70 
                ? " the system demonstrates strong user satisfaction with contract analysis accuracy." 
                : " there's room for improvement in analysis accuracy and user experience."}
            </p>
          </div>
        </div>
      </div>

      {/* Compliance Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BarChart3 size={20} className="text-teal-600" />
            Compliance Distribution
          </h3>
          <div className="space-y-4">
            <ComplianceBar
              label="Compliant"
              count={analytics.total_compliant}
              total={analytics.total_contracts}
              color="bg-green-500"
              icon={<CheckCircle size={16} />}
            />
            <ComplianceBar
              label="Partially Compliant"
              count={analytics.total_partially_compliant}
              total={analytics.total_contracts}
              color="bg-amber-500"
              icon={<AlertTriangle size={16} />}
            />
            <ComplianceBar
              label="Non-Compliant"
              count={analytics.total_non_compliant}
              total={analytics.total_contracts}
              color="bg-red-500"
              icon={<AlertTriangle size={16} />}
            />
          </div>
        </div>

        {/* Top Violations */}
        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle size={20} className="text-red-600" />
            Top Violations
          </h3>
          {analytics.top_violations && analytics.top_violations.length > 0 ? (
            <div className="space-y-3">
              {analytics.top_violations.map((violation, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center text-red-600 font-bold text-sm">
                      {index + 1}
                    </div>
                    <span className="text-sm font-medium text-gray-800 line-clamp-1">{violation.regulation}</span>
                  </div>
                  <span className="text-sm font-bold text-red-600">{violation.count}x</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No violations recorded yet.</p>
          )}
        </div>
      </div>

      {/* Insights */}
      <div className="bg-gradient-to-br from-teal-50 to-blue-50 p-6 rounded-2xl border border-teal-200 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Activity size={20} className="text-teal-600" />
          Key Insights
        </h3>
        <div className="space-y-3">
          {analytics.total_contracts === 0 ? (
            <InsightItem text="No contracts analyzed yet. Upload your first contract to get started." />
          ) : (
            <>
              <InsightItem 
                text={`${((analytics.total_compliant / analytics.total_contracts) * 100).toFixed(1)}% of contracts are fully Shariah compliant.`}
              />
              {analytics.avg_compliance_score < 70 && (
                <InsightItem 
                  text="Average compliance score is below 70%. Consider reviewing contract templates and regulations."
                  type="warning"
                />
              )}
              {analytics.rating_satisfaction < 60 && (
                <InsightItem 
                  text="User satisfaction is below 60%. Analysis accuracy may need improvement."
                  type="warning"
                />
              )}
              {analytics.top_violations.length > 0 && (
                <InsightItem 
                  text={`Most common violation: "${analytics.top_violations[0].regulation}" (${analytics.top_violations[0].count} occurrences)`}
                />
              )}
              {analytics.total_thumbs_up > analytics.total_thumbs_down * 2 && (
                <InsightItem 
                  text="Users are highly satisfied with the compliance analysis results!"
                  type="success"
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const MetricCard = ({ icon, label, value, bgColor }) => (
  <div className={`${bgColor} p-6 rounded-2xl border border-gray-200 shadow-sm`}>
    <div className="flex items-center justify-between mb-3">
      {icon}
    </div>
    <div className="text-3xl font-bold text-gray-900 mb-1">{value}</div>
    <div className="text-sm text-gray-600 font-medium">{label}</div>
  </div>
);

const ComplianceBar = ({ label, count, total, color, icon }) => {
  const percentage = total > 0 ? (count / total) * 100 : 0;
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
          {icon}
          <span>{label}</span>
        </div>
        <span className="text-sm font-bold text-gray-900">{count}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div 
          className={`${color} h-full rounded-full transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-xs text-gray-500 mt-1 block">{percentage.toFixed(1)}%</span>
    </div>
  );
};

const InsightItem = ({ text, type = "info" }) => {
  const colors = {
    info: "bg-blue-100 text-blue-800 border-blue-200",
    warning: "bg-amber-100 text-amber-800 border-amber-200",
    success: "bg-green-100 text-green-800 border-green-200"
  };
  
  return (
    <div className={`p-3 rounded-lg border ${colors[type]}`}>
      <p className="text-sm font-medium leading-relaxed">{text}</p>
    </div>
  );
};

export default AnalyticsView;
