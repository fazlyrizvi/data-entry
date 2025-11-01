import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  FileText, Plus, Edit, Trash2, Eye, Save, X, Search, 
  CheckCircle, AlertCircle, Clock, Upload, Download 
} from 'lucide-react';

interface DataTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  fields: TemplateField[];
  createdAt: string;
  createdBy: string;
  lastModified: string;
  status: 'active' | 'draft' | 'archived';
  usageCount: number;
}

interface TemplateField {
  id: string;
  name: string;
  type: 'text' | 'number' | 'date' | 'email' | 'select' | 'textarea';
  required: boolean;
  validation?: string;
  options?: string[];
  placeholder?: string;
}

export const DataEntryTemplateInterface: React.FC = () => {
  const { user } = useAuth();
  const [templates, setTemplates] = useState<DataTemplate[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<DataTemplate | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [newTemplate, setNewTemplate] = useState({
    name: '',
    description: '',
    category: '',
    fields: [] as TemplateField[]
  });

  const categories = [
    'Customer Data', 'Product Information', 'Financial Records', 
    'Employee Records', 'Inventory', 'Sales', 'Marketing', 'Operations'
  ];

  const fieldTypes = [
    { value: 'text', label: 'Text', icon: '📝' },
    { value: 'number', label: 'Number', icon: '🔢' },
    { value: 'date', label: 'Date', icon: '📅' },
    { value: 'email', label: 'Email', icon: '📧' },
    { value: 'select', label: 'Dropdown', icon: '📋' },
    { value: 'textarea', label: 'Long Text', icon: '📄' }
  ];

  // Mock data for demonstration
  React.useEffect(() => {
    const mockTemplates: DataTemplate[] = [
      {
        id: '1',
        name: 'Customer Registration Form',
        description: 'Standard customer onboarding template with required fields',
        category: 'Customer Data',
        fields: [
          { id: '1', name: 'First Name', type: 'text', required: true, placeholder: 'Enter first name' },
          { id: '2', name: 'Last Name', type: 'text', required: true, placeholder: 'Enter last name' },
          { id: '3', name: 'Email', type: 'email', required: true, placeholder: 'Enter email address' },
          { id: '4', name: 'Phone Number', type: 'text', required: false, placeholder: 'Enter phone number' },
          { id: '5', name: 'Customer Type', type: 'select', required: true, options: ['Individual', 'Business', 'Enterprise'] }
        ],
        createdAt: '2024-01-15T10:00:00Z',
        createdBy: 'Admin User',
        lastModified: '2024-01-20T14:30:00Z',
        status: 'active',
        usageCount: 234
      },
      {
        id: '2',
        name: 'Product Information Entry',
        description: 'Template for entering new product details and specifications',
        category: 'Product Information',
        fields: [
          { id: '1', name: 'Product Name', type: 'text', required: true, placeholder: 'Enter product name' },
          { id: '2', name: 'SKU', type: 'text', required: true, placeholder: 'Enter SKU' },
          { id: '3', name: 'Category', type: 'select', required: true, options: ['Electronics', 'Clothing', 'Books', 'Home'] },
          { id: '4', name: 'Price', type: 'number', required: true, placeholder: 'Enter price' },
          { id: '5', name: 'Description', type: 'textarea', required: false, placeholder: 'Enter product description' }
        ],
        createdAt: '2024-01-10T09:15:00Z',
        createdBy: 'Data Manager',
        lastModified: '2024-01-18T16:45:00Z',
        status: 'active',
        usageCount: 156
      },
      {
        id: '3',
        name: 'Employee Onboarding',
        description: 'HR template for new employee information collection',
        category: 'Employee Records',
        fields: [
          { id: '1', name: 'Employee ID', type: 'text', required: true, placeholder: 'Enter employee ID' },
          { id: '2', name: 'Full Name', type: 'text', required: true, placeholder: 'Enter full name' },
          { id: '3', name: 'Department', type: 'select', required: true, options: ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance'] },
          { id: '4', name: 'Start Date', type: 'date', required: true },
          { id: '5', name: 'Emergency Contact', type: 'text', required: true, placeholder: 'Enter emergency contact' }
        ],
        createdAt: '2024-01-05T11:20:00Z',
        createdBy: 'HR Manager',
        lastModified: '2024-01-12T13:10:00Z',
        status: 'draft',
        usageCount: 45
      }
    ];
    setTemplates(mockTemplates);
  }, []);

  const filteredTemplates = templates.filter(template =>
    template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    template.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    template.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const createTemplate = () => {
    if (!newTemplate.name || !newTemplate.category) return;

    const template: DataTemplate = {
      id: Date.now().toString(),
      name: newTemplate.name,
      description: newTemplate.description,
      category: newTemplate.category,
      fields: newTemplate.fields,
      createdAt: new Date().toISOString(),
      createdBy: user?.full_name || 'Current User',
      lastModified: new Date().toISOString(),
      status: 'draft',
      usageCount: 0
    };

    setTemplates(prev => [template, ...prev]);
    setNewTemplate({ name: '', description: '', category: '', fields: [] });
    setShowCreateForm(false);
  };

  const addField = () => {
    const newField: TemplateField = {
      id: Date.now().toString(),
      name: '',
      type: 'text',
      required: false,
      placeholder: ''
    };
    setNewTemplate(prev => ({
      ...prev,
      fields: [...prev.fields, newField]
    }));
  };

  const updateField = (fieldId: string, updates: Partial<TemplateField>) => {
    setNewTemplate(prev => ({
      ...prev,
      fields: prev.fields.map(field => 
        field.id === fieldId ? { ...field, ...updates } : field
      )
    }));
  };

  const removeField = (fieldId: string) => {
    setNewTemplate(prev => ({
      ...prev,
      fields: prev.fields.filter(field => field.id !== fieldId)
    }));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-50';
      case 'draft': return 'text-yellow-600 bg-yellow-50';
      case 'archived': return 'text-neutral-600 bg-neutral-50';
      default: return 'text-neutral-600 bg-neutral-50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-4 h-4" />;
      case 'draft': return <Edit className="w-4 h-4" />;
      case 'archived': return <Clock className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const GlassCard: React.FC<{ children: React.ReactNode; className?: string }> = ({ 
    children, 
    className = '' 
  }) => (
    <div className={`bg-glass-light backdrop-blur-glass border border-glass-border rounded-xl p-6 ${className}`}>
      {children}
    </div>
  );

  const GlassButton: React.FC<{ 
    children: React.ReactNode; 
    onClick?: () => void; 
    variant?: 'primary' | 'secondary' | 'danger';
    disabled?: boolean;
    className?: string;
  }> = ({ children, onClick, variant = 'primary', disabled = false, className = '' }) => {
    const baseClasses = 'px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2';
    const variantClasses = {
      primary: 'bg-primary-500 text-white hover:bg-primary-600 disabled:bg-neutral-300',
      secondary: 'bg-white text-neutral-700 border border-neutral-300 hover:bg-neutral-50 disabled:bg-neutral-100',
      danger: 'bg-red-500 text-white hover:bg-red-600 disabled:bg-neutral-300'
    };

    return (
      <button
        onClick={onClick}
        disabled={disabled}
        className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      >
        {children}
      </button>
    );
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Data Entry Templates</h1>
          <p className="text-neutral-600 mt-1">Create and manage reusable data entry forms</p>
        </div>
        <GlassButton onClick={() => setShowCreateForm(true)}>
          <Plus className="w-4 h-4" />
          <span>Create Template</span>
        </GlassButton>
      </div>

      {/* Search and Filters */}
      <GlassCard>
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search templates..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <select className="px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
            <option value="">All Categories</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>
      </GlassCard>

      {/* Create Template Form */}
      {showCreateForm && (
        <GlassCard>
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold text-neutral-900">Create New Template</h3>
            <button
              onClick={() => setShowCreateForm(false)}
              className="text-neutral-500 hover:text-neutral-700"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">Template Name</label>
                <input
                  type="text"
                  value={newTemplate.name}
                  onChange={(e) => setNewTemplate(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter template name..."
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">Category</label>
                <select
                  value={newTemplate.category}
                  onChange={(e) => setNewTemplate(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="">Select category...</option>
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">Description</label>
              <textarea
                value={newTemplate.description}
                onChange={(e) => setNewTemplate(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Enter template description..."
                rows={3}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-md font-medium text-neutral-900">Form Fields</h4>
                <GlassButton onClick={addField} variant="secondary">
                  <Plus className="w-4 h-4" />
                  <span>Add Field</span>
                </GlassButton>
              </div>
              
              <div className="space-y-3">
                {newTemplate.fields.map(field => (
                  <div key={field.id} className="border border-neutral-200 rounded-lg p-4">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                      <input
                        type="text"
                        value={field.name}
                        onChange={(e) => updateField(field.id, { name: e.target.value })}
                        placeholder="Field name"
                        className="px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                      <select
                        value={field.type}
                        onChange={(e) => updateField(field.id, { type: e.target.value as any })}
                        className="px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      >
                        {fieldTypes.map(type => (
                          <option key={type.value} value={type.value}>
                            {type.icon} {type.label}
                          </option>
                        ))}
                      </select>
                      <input
                        type="text"
                        value={field.placeholder || ''}
                        onChange={(e) => updateField(field.id, { placeholder: e.target.value })}
                        placeholder="Placeholder"
                        className="px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                      <div className="flex items-center space-x-2">
                        <label className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={field.required}
                            onChange={(e) => updateField(field.id, { required: e.target.checked })}
                            className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                          />
                          <span className="text-sm text-neutral-700">Required</span>
                        </label>
                        <button
                          onClick={() => removeField(field.id)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex space-x-3">
              <GlassButton onClick={createTemplate} disabled={!newTemplate.name || !newTemplate.category}>
                <Save className="w-4 h-4" />
                <span>Create Template</span>
              </GlassButton>
              <GlassButton onClick={() => setShowCreateForm(false)} variant="secondary">
                Cancel
              </GlassButton>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Templates Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredTemplates.map(template => (
          <GlassCard key={template.id} className="hover:shadow-lg transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-neutral-900 mb-1">{template.name}</h3>
                <p className="text-sm text-neutral-600 mb-2">{template.description}</p>
                <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                  {template.category}
                </span>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${getStatusColor(template.status)}`}>
                {getStatusIcon(template.status)}
                <span>{template.status}</span>
              </span>
            </div>

            <div className="space-y-3 mb-4">
              <div className="flex justify-between text-sm">
                <span className="text-neutral-500">Fields</span>
                <span className="font-medium">{template.fields.length}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-neutral-500">Usage Count</span>
                <span className="font-medium">{template.usageCount}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-neutral-500">Last Modified</span>
                <span className="font-medium">
                  {new Date(template.lastModified).toLocaleDateString()}
                </span>
              </div>
            </div>

            <div className="flex space-x-2">
              <GlassButton onClick={() => { setSelectedTemplate(template); setShowPreview(true); }} variant="secondary" className="flex-1">
                <Eye className="w-4 h-4" />
                <span>Preview</span>
              </GlassButton>
              <GlassButton onClick={() => {/* Handle edit */}} variant="secondary">
                <Edit className="w-4 h-4" />
              </GlassButton>
              <GlassButton onClick={() => {/* Handle delete */}} variant="danger">
                <Trash2 className="w-4 h-4" />
              </GlassButton>
            </div>
          </GlassCard>
        ))}
      </div>

      {filteredTemplates.length === 0 && (
        <GlassCard className="text-center py-12">
          <FileText className="w-12 h-12 text-neutral-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-neutral-900 mb-2">No templates found</h3>
          <p className="text-neutral-600 mb-4">
            {searchTerm ? 'Try adjusting your search terms' : 'Get started by creating your first template'}
          </p>
          {!searchTerm && (
            <GlassButton onClick={() => setShowCreateForm(true)}>
              <Plus className="w-4 h-4" />
              <span>Create Template</span>
            </GlassButton>
          )}
        </GlassCard>
      )}

      {/* Preview Modal */}
      {showPreview && selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-neutral-900">Template Preview</h3>
              <button
                onClick={() => setShowPreview(false)}
                className="text-neutral-500 hover:text-neutral-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-neutral-900 mb-2">{selectedTemplate.name}</h4>
                <p className="text-neutral-600 text-sm mb-4">{selectedTemplate.description}</p>
              </div>

              <div className="border-t pt-4">
                <h5 className="font-medium text-neutral-900 mb-3">Form Fields</h5>
                <div className="space-y-3">
                  {selectedTemplate.fields.map(field => (
                    <div key={field.id}>
                      <label className="block text-sm font-medium text-neutral-700 mb-1">
                        {field.name}
                        {field.required && <span className="text-red-500 ml-1">*</span>}
                      </label>
                      <input
                        type={field.type === 'text' ? 'text' : field.type}
                        placeholder={field.placeholder || ''}
                        disabled
                        className="w-full px-3 py-2 border border-neutral-300 rounded-lg bg-neutral-50 text-neutral-500"
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};