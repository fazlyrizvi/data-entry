import React, { useState } from 'react';
import { 
  FileText, 
  Users, 
  Package, 
  ClipboardList, 
  UserCheck,
  Building,
  FileStack,
  ArrowRight,
  Star,
  Clock,
  TrendingUp,
  CheckCircle
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';

interface Template {
  id: string;
  name: string;
  description: string;
  category: 'business' | 'healthcare' | 'inventory' | 'survey' | 'hr';
  icon: React.ComponentType<any>;
  estimatedTime: string;
  difficulty: 'Easy' | 'Medium' | 'Advanced';
  usageCount: number;
  rating: number;
  features: string[];
  fields: TemplateField[];
}

interface TemplateField {
  name: string;
  type: 'text' | 'email' | 'phone' | 'number' | 'date' | 'select' | 'textarea' | 'boolean';
  required: boolean;
  validation?: string;
  options?: string[];
}

const templates: Template[] = [
  {
    id: 'medical-records',
    name: 'Medical Records',
    description: 'Standard medical record form with patient information, vitals, and diagnosis codes',
    category: 'healthcare',
    icon: UserCheck,
    estimatedTime: '8-12 min',
    difficulty: 'Advanced',
    usageCount: 2450,
    rating: 4.8,
    features: [
      'HIPAA compliant fields',
      'ICD-10 code support',
      'Vital signs tracking',
      'Medication management',
      'Allergy tracking'
    ],
    fields: [
      { name: 'Patient Name', type: 'text', required: true },
      { name: 'Date of Birth', type: 'date', required: true },
      { name: 'Medical Record Number', type: 'text', required: true },
      { name: 'Primary Diagnosis', type: 'text', required: true },
      { name: 'ICD-10 Code', type: 'text', required: false },
      { name: 'Blood Pressure', type: 'text', required: false },
      { name: 'Heart Rate', type: 'number', required: false },
      { name: 'Temperature', type: 'number', required: false },
      { name: 'Current Medications', type: 'textarea', required: false },
      { name: 'Known Allergies', type: 'textarea', required: false },
      { name: 'Attending Physician', type: 'text', required: true },
      { name: 'Admission Date', type: 'date', required: true }
    ]
  },
  {
    id: 'customer-database',
    name: 'Customer Database',
    description: 'Complete customer information management with contact details and preferences',
    category: 'business',
    icon: Building,
    estimatedTime: '5-8 min',
    difficulty: 'Medium',
    usageCount: 1890,
    rating: 4.6,
    features: [
      'Contact validation',
      'Lead scoring',
      'Customer segmentation',
      'Social media integration',
      'Communication preferences'
    ],
    fields: [
      { name: 'Company Name', type: 'text', required: true },
      { name: 'Contact Person', type: 'text', required: true },
      { name: 'Email Address', type: 'email', required: true },
      { name: 'Phone Number', type: 'phone', required: true },
      { name: 'Street Address', type: 'text', required: true },
      { name: 'City', type: 'text', required: true },
      { name: 'State/Province', type: 'text', required: true },
      { name: 'Postal Code', type: 'text', required: true },
      { name: 'Country', type: 'text', required: true },
      { name: 'Industry', type: 'select', options: ['Technology', 'Healthcare', 'Finance', 'Retail', 'Manufacturing', 'Other'], required: true },
      { name: 'Company Size', type: 'select', options: ['1-10', '11-50', '51-200', '201-1000', '1000+'], required: true },
      { name: 'Lead Source', type: 'select', options: ['Website', 'Referral', 'Social Media', 'Email Campaign', 'Trade Show', 'Cold Call'], required: false },
      { name: 'Preferred Contact Method', type: 'select', options: ['Email', 'Phone', 'Text Message'], required: false },
      { name: 'Notes', type: 'textarea', required: false }
    ]
  },
  {
    id: 'inventory-management',
    name: 'Inventory Management',
    description: 'Product inventory tracking with SKU, pricing, and stock management',
    category: 'inventory',
    icon: Package,
    estimatedTime: '3-5 min',
    difficulty: 'Easy',
    usageCount: 3200,
    rating: 4.7,
    features: [
      'SKU generation',
      'Barcode support',
      'Stock level alerts',
      'Supplier management',
      'Cost tracking'
    ],
    fields: [
      { name: 'Product Name', type: 'text', required: true },
      { name: 'SKU', type: 'text', required: true },
      { name: 'Category', type: 'select', options: ['Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports', 'Automotive', 'Other'], required: true },
      { name: 'Description', type: 'textarea', required: false },
      { name: 'Unit Price', type: 'number', required: true },
      { name: 'Cost Price', type: 'number', required: false },
      { name: 'Current Stock', type: 'number', required: true },
      { name: 'Minimum Stock', type: 'number', required: true },
      { name: 'Maximum Stock', type: 'number', required: false },
      { name: 'Supplier', type: 'text', required: false },
      { name: 'Location', type: 'text', required: false },
      { name: 'Last Updated', type: 'date', required: false },
      { name: 'Discontinued', type: 'boolean', required: false }
    ]
  },
  {
    id: 'survey-data',
    name: 'Survey Data Collection',
    description: 'Flexible survey form with various question types and conditional logic',
    category: 'survey',
    icon: ClipboardList,
    estimatedTime: '4-7 min',
    difficulty: 'Medium',
    usageCount: 1650,
    rating: 4.5,
    features: [
      'Conditional logic',
      'Multi-choice questions',
      'Rating scales',
      'File upload support',
      'Progress tracking'
    ],
    fields: [
      { name: 'Survey Title', type: 'text', required: true },
      { name: 'Respondent Email', type: 'email', required: false },
      { name: 'Age Range', type: 'select', options: ['18-24', '25-34', '35-44', '45-54', '55-64', '65+'], required: false },
      { name: 'Location', type: 'text', required: false },
      { name: 'Satisfaction Rating', type: 'select', options: ['1 - Very Dissatisfied', '2 - Dissatisfied', '3 - Neutral', '4 - Satisfied', '5 - Very Satisfied'], required: true },
      { name: 'Features Used', type: 'select', options: ['Feature A', 'Feature B', 'Feature C', 'Feature D', 'None'], required: false },
      { name: 'Likelihood to Recommend', type: 'select', options: ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'], required: true },
      { name: 'Additional Comments', type: 'textarea', required: false },
      { name: 'Follow-up Required', type: 'boolean', required: false },
      { name: 'Contact Permission', type: 'boolean', required: false }
    ]
  },
  {
    id: 'employee-records',
    name: 'Employee Records',
    description: 'HR employee information with personal details, position, and compensation',
    category: 'hr',
    icon: Users,
    estimatedTime: '6-10 min',
    difficulty: 'Medium',
    usageCount: 2100,
    rating: 4.9,
    features: [
      'Employee onboarding',
      'Compensation tracking',
      'Benefits management',
      'Performance reviews',
      'Document storage'
    ],
    fields: [
      { name: 'Employee ID', type: 'text', required: true },
      { name: 'First Name', type: 'text', required: true },
      { name: 'Last Name', type: 'text', required: true },
      { name: 'Email Address', type: 'email', required: true },
      { name: 'Phone Number', type: 'phone', required: true },
      { name: 'Date of Birth', type: 'date', required: true },
      { name: 'Address', type: 'text', required: true },
      { name: 'Position/Title', type: 'text', required: true },
      { name: 'Department', type: 'select', options: ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance', 'Operations', 'Other'], required: true },
      { name: 'Hire Date', type: 'date', required: true },
      { name: 'Employment Type', type: 'select', options: ['Full-time', 'Part-time', 'Contract', 'Intern'], required: true },
      { name: 'Annual Salary', type: 'number', required: false },
      { name: 'Manager', type: 'text', required: false },
      { name: 'Emergency Contact', type: 'text', required: true },
      { name: 'Benefits Enrolled', type: 'select', options: ['Health Insurance', 'Dental', 'Vision', '401k', 'Life Insurance', 'None'], required: false }
    ]
  }
];

export const TemplateSelector: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);

  const categories = [
    { id: 'all', name: 'All Templates', count: templates.length },
    { id: 'business', name: 'Business', count: templates.filter(t => t.category === 'business').length },
    { id: 'healthcare', name: 'Healthcare', count: templates.filter(t => t.category === 'healthcare').length },
    { id: 'inventory', name: 'Inventory', count: templates.filter(t => t.category === 'inventory').length },
    { id: 'survey', name: 'Survey', count: templates.filter(t => t.category === 'survey').length },
    { id: 'hr', name: 'Human Resources', count: templates.filter(t => t.category === 'hr').length }
  ];

  const filteredTemplates = selectedCategory === 'all' 
    ? templates 
    : templates.filter(t => t.category === selectedCategory);

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Easy': return 'text-green-600 bg-green-50';
      case 'Medium': return 'text-yellow-600 bg-yellow-50';
      case 'Advanced': return 'text-red-600 bg-red-50';
      default: return 'text-neutral-600 bg-neutral-50';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'business': return Building;
      case 'healthcare': return UserCheck;
      case 'inventory': return Package;
      case 'survey': return ClipboardList;
      case 'hr': return Users;
      default: return FileText;
    }
  };

  if (selectedTemplate) {
    return (
      <div className="space-y-6">
        {/* Template Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className={`p-3 rounded-lg ${getDifficultyColor(selectedTemplate.difficulty)} bg-opacity-20`}>
              <selectedTemplate.icon className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-neutral-900">{selectedTemplate.name}</h2>
              <p className="text-neutral-600">{selectedTemplate.description}</p>
            </div>
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={() => setSelectedTemplate(null)}
              className="px-4 py-2 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 transition-colors"
            >
              Back to Templates
            </button>
            <button className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors flex items-center space-x-2">
              <span>Use This Template</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Template Details */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Features */}
            <GlassCard>
              <h3 className="text-lg font-semibold text-neutral-900 mb-4">Features</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {selectedTemplate.features.map((feature, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span className="text-sm text-neutral-700">{feature}</span>
                  </div>
                ))}
              </div>
            </GlassCard>

            {/* Form Fields */}
            <GlassCard>
              <h3 className="text-lg font-semibold text-neutral-900 mb-4">Form Fields</h3>
              <div className="space-y-3">
                {selectedTemplate.fields.map((field, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg">
                    <div>
                      <span className="font-medium text-neutral-900">{field.name}</span>
                      <span className="text-sm text-neutral-500 ml-2">({field.type})</span>
                      {field.required && (
                        <span className="text-red-500 ml-2">*</span>
                      )}
                    </div>
                    {field.options && (
                      <span className="text-xs text-neutral-500">
                        {field.options.length} options
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>

          {/* Stats Sidebar */}
          <div className="space-y-6">
            <GlassCard>
              <h3 className="text-lg font-semibold text-neutral-900 mb-4">Template Stats</h3>
              
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <Clock className="w-5 h-5 text-neutral-500" />
                  <div>
                    <p className="text-sm text-neutral-600">Estimated Time</p>
                    <p className="font-medium text-neutral-900">{selectedTemplate.estimatedTime}</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <TrendingUp className="w-5 h-5 text-neutral-500" />
                  <div>
                    <p className="text-sm text-neutral-600">Usage Count</p>
                    <p className="font-medium text-neutral-900">{selectedTemplate.usageCount.toLocaleString()}</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <Star className="w-5 h-5 text-yellow-500" />
                  <div>
                    <p className="text-sm text-neutral-600">Rating</p>
                    <p className="font-medium text-neutral-900">{selectedTemplate.rating}/5.0</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <FileStack className="w-5 h-5 text-neutral-500" />
                  <div>
                    <p className="text-sm text-neutral-600">Total Fields</p>
                    <p className="font-medium text-neutral-900">{selectedTemplate.fields.length}</p>
                  </div>
                </div>
              </div>
            </GlassCard>

            <GlassCard>
              <h3 className="text-lg font-semibold text-neutral-900 mb-4">Quick Actions</h3>
              
              <div className="space-y-3">
                <button className="w-full text-left p-3 bg-primary-50 border border-primary-200 rounded-lg hover:bg-primary-100 transition-colors">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-primary-600" />
                    <span className="font-medium text-primary-900">Preview Form</span>
                  </div>
                </button>
                
                <button className="w-full text-left p-3 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors">
                  <div className="flex items-center space-x-2">
                    <FileStack className="w-4 h-4 text-blue-600" />
                    <span className="font-medium text-blue-900">Download Template</span>
                  </div>
                </button>
                
                <button className="w-full text-left p-3 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition-colors">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    <span className="font-medium text-green-900">Use Template</span>
                  </div>
                </button>
              </div>
            </GlassCard>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Data Entry Templates</h1>
          <p className="text-neutral-600 mt-1">Choose from pre-built templates or create custom forms</p>
        </div>
        
        <div className="flex space-x-3">
          <button className="px-4 py-2 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 transition-colors">
            Import Template
          </button>
          <button className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors">
            Create Custom
          </button>
        </div>
      </div>

      {/* Category Filter */}
      <GlassCard>
        <div className="flex items-center space-x-3 overflow-x-auto">
          {categories.map((category) => {
            const CategoryIcon = getCategoryIcon(category.id);
            return (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`
                  flex items-center space-x-2 px-4 py-2 rounded-lg whitespace-nowrap font-medium text-sm transition-colors
                  ${selectedCategory === category.id 
                    ? 'bg-primary-500 text-white' 
                    : 'text-neutral-600 hover:bg-neutral-100'
                  }
                `}
              >
                <CategoryIcon className="w-4 h-4" />
                <span>{category.name}</span>
                <span className={`
                  text-xs px-2 py-1 rounded-full
                  ${selectedCategory === category.id 
                    ? 'bg-white/20 text-white' 
                    : 'bg-neutral-200 text-neutral-600'
                  }
                `}>
                  {category.count}
                </span>
              </button>
            );
          })}
        </div>
      </GlassCard>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTemplates.map((template) => {
          const TemplateIcon = template.icon;
          
          return (
            <GlassCard key={template.id} className="hover:shadow-lg transition-shadow cursor-pointer">
              <div 
                className="p-6"
                onClick={() => setSelectedTemplate(template)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 rounded-lg ${getDifficultyColor(template.difficulty)} bg-opacity-20`}>
                    <TemplateIcon className="w-6 h-6" />
                  </div>
                  <div className="flex items-center space-x-1">
                    <Star className="w-4 h-4 text-yellow-500" />
                    <span className="text-sm font-medium text-neutral-900">{template.rating}</span>
                  </div>
                </div>
                
                <h3 className="text-lg font-semibold text-neutral-900 mb-2">{template.name}</h3>
                <p className="text-sm text-neutral-600 mb-4">{template.description}</p>
                
                <div className="flex items-center justify-between text-sm text-neutral-500 mb-4">
                  <span>{template.estimatedTime}</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(template.difficulty)}`}>
                    {template.difficulty}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="text-xs text-neutral-500">
                    {template.usageCount.toLocaleString()} uses
                  </div>
                  <button className="flex items-center space-x-1 text-primary-600 hover:text-primary-700 text-sm font-medium">
                    <span>Use Template</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </GlassCard>
          );
        })}
      </div>

      {filteredTemplates.length === 0 && (
        <GlassCard>
          <div className="text-center py-12">
            <FileText className="w-16 h-16 text-neutral-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-neutral-900 mb-2">
              No Templates Found
            </h3>
            <p className="text-neutral-600">
              No templates found in the {categories.find(c => c.id === selectedCategory)?.name} category.
            </p>
          </div>
        </GlassCard>
      )}
    </div>
  );
};

export default TemplateSelector;