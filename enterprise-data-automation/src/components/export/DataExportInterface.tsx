import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Shield, BarChart3, CheckCircle, AlertCircle, Clock } from 'lucide-react';

export const DataExportInterface: React.FC = () => {
  const { user } = useAuth();
  
  const componentName = window.location.pathname.replace('/', '').replace('-', ' ');
  const iconComponent = componentName.includes('quality') ? Shield : BarChart3;
  const Icon = iconComponent;
  
  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-neutral-900 capitalize">{componentName}</h1>
        <p className="text-neutral-600 mt-1">Advanced {componentName} capabilities</p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-glass-light backdrop-blur-glass border border-glass-border rounded-xl p-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-neutral-900">Passed</h3>
              <p className="text-2xl font-bold text-green-600">1,247</p>
            </div>
          </div>
        </div>

        <div className="bg-glass-light backdrop-blur-glass border border-glass-border rounded-xl p-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
              <Clock className="w-5 h-5 text-yellow-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-neutral-900">Pending</h3>
              <p className="text-2xl font-bold text-yellow-600">23</p>
            </div>
          </div>
        </div>

        <div className="bg-glass-light backdrop-blur-glass border border-glass-border rounded-xl p-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <AlertCircle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-neutral-900">Failed</h3>
              <p className="text-2xl font-bold text-red-600">5</p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-glass-light backdrop-blur-glass border border-glass-border rounded-xl p-8 text-center">
        <Icon className="w-16 h-16 text-primary-500 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-neutral-900 mb-2 capitalize">{componentName} Module</h3>
        <p className="text-neutral-600">This module provides comprehensive {componentName} capabilities with real-time monitoring and automated workflows.</p>
      </div>
    </div>
  );
};
