import React, { useState } from 'react';
import { 
  UserCheck, 
  Save, 
  X, 
  Calendar, 
  MapPin, 
  Phone, 
  Mail,
  AlertTriangle,
  CheckCircle,
  Loader2,
  FileText,
  Heart,
  Pill,
  Activity,
  Thermometer
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';

interface MedicalRecord {
  patientName: string;
  dateOfBirth: string;
  medicalRecordNumber: string;
  primaryDiagnosis: string;
  icd10Code: string;
  bloodPressure: string;
  heartRate: string;
  temperature: string;
  currentMedications: string;
  knownAllergies: string;
  attendingPhysician: string;
  admissionDate: string;
}

interface FormErrors {
  [key: string]: string;
}

export const MedicalRecordsForm: React.FC = () => {
  const [formData, setFormData] = useState<MedicalRecord>({
    patientName: '',
    dateOfBirth: '',
    medicalRecordNumber: '',
    primaryDiagnosis: '',
    icd10Code: '',
    bloodPressure: '',
    heartRate: '',
    temperature: '',
    currentMedications: '',
    knownAllergies: '',
    attendingPhysician: '',
    admissionDate: ''
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);

  const steps = [
    { id: 1, name: 'Patient Info', icon: UserCheck },
    { id: 2, name: 'Vitals', icon: Heart },
    { id: 3, name: 'Medications', icon: Pill },
    { id: 4, name: 'Review', icon: FileText }
  ];

  const handleInputChange = (field: keyof MedicalRecord, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validateStep = (step: number): boolean => {
    const newErrors: FormErrors = {};

    switch (step) {
      case 1:
        if (!formData.patientName.trim()) newErrors.patientName = 'Patient name is required';
        if (!formData.dateOfBirth) newErrors.dateOfBirth = 'Date of birth is required';
        if (!formData.medicalRecordNumber.trim()) newErrors.medicalRecordNumber = 'Medical record number is required';
        if (!formData.primaryDiagnosis.trim()) newErrors.primaryDiagnosis = 'Primary diagnosis is required';
        if (!formData.attendingPhysician.trim()) newErrors.attendingPhysician = 'Attending physician is required';
        if (!formData.admissionDate) newErrors.admissionDate = 'Admission date is required';
        break;
      
      case 2:
        if (formData.bloodPressure && !/^\d{2,3}\/\d{2,3}$/.test(formData.bloodPressure)) {
          newErrors.bloodPressure = 'Blood pressure must be in format 120/80';
        }
        if (formData.heartRate && (isNaN(Number(formData.heartRate)) || Number(formData.heartRate) < 0)) {
          newErrors.heartRate = 'Heart rate must be a valid number';
        }
        if (formData.temperature && (isNaN(Number(formData.temperature)) || Number(formData.temperature) < 90 || Number(formData.temperature) > 110)) {
          newErrors.temperature = 'Temperature must be between 90-110°F';
        }
        break;
      
      case 3:
        // No specific validation for medications and allergies
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const nextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, steps.length));
    }
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return;

    setIsSubmitting(true);

    // Simulate API call
    try {
      await new Promise(resolve => setTimeout(resolve, 2000));
      setIsSubmitted(true);
    } catch (error) {
      console.error('Submission failed:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      patientName: '',
      dateOfBirth: '',
      medicalRecordNumber: '',
      primaryDiagnosis: '',
      icd10Code: '',
      bloodPressure: '',
      heartRate: '',
      temperature: '',
      currentMedications: '',
      knownAllergies: '',
      attendingPhysician: '',
      admissionDate: ''
    });
    setErrors({});
    setIsSubmitted(false);
    setCurrentStep(1);
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">
                  Patient Name *
                </label>
                <input
                  type="text"
                  value={formData.patientName}
                  onChange={(e) => handleInputChange('patientName', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 ${
                    errors.patientName ? 'border-red-500' : 'border-neutral-200'
                  }`}
                  placeholder="Enter full name"
                />
                {errors.patientName && (
                  <p className="text-red-600 text-xs mt-1">{errors.patientName}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">
                  Date of Birth *
                </label>
                <input
                  type="date"
                  value={formData.dateOfBirth}
                  onChange={(e) => handleInputChange('dateOfBirth', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 ${
                    errors.dateOfBirth ? 'border-red-500' : 'border-neutral-200'
                  }`}
                />
                {errors.dateOfBirth && (
                  <p className="text-red-600 text-xs mt-1">{errors.dateOfBirth}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">
                  Medical Record Number *
                </label>
                <input
                  type="text"
                  value={formData.medicalRecordNumber}
                  onChange={(e) => handleInputChange('medicalRecordNumber', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 ${
                    errors.medicalRecordNumber ? 'border-red-500' : 'border-neutral-200'
                  }`}
                  placeholder="MRN-123456"
                />
                {errors.medicalRecordNumber && (
                  <p className="text-red-600 text-xs mt-1">{errors.medicalRecordNumber}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">
                  ICD-10 Code
                </label>
                <input
                  type="text"
                  value={formData.icd10Code}
                  onChange={(e) => handleInputChange('icd10Code', e.target.value.toUpperCase())}
                  className="w-full px-3 py-2 border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                  placeholder="e.g., I10"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">
                  Attending Physician *
                </label>
                <input
                  type="text"
                  value={formData.attendingPhysician}
                  onChange={(e) => handleInputChange('attendingPhysician', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 ${
                    errors.attendingPhysician ? 'border-red-500' : 'border-neutral-200'
                  }`}
                  placeholder="Dr. Smith"
                />
                {errors.attendingPhysician && (
                  <p className="text-red-600 text-xs mt-1">{errors.attendingPhysician}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">
                  Admission Date *
                </label>
                <input
                  type="date"
                  value={formData.admissionDate}
                  onChange={(e) => handleInputChange('admissionDate', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 ${
                    errors.admissionDate ? 'border-red-500' : 'border-neutral-200'
                  }`}
                />
                {errors.admissionDate && (
                  <p className="text-red-600 text-xs mt-1">{errors.admissionDate}</p>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Primary Diagnosis *
              </label>
              <textarea
                value={formData.primaryDiagnosis}
                onChange={(e) => handleInputChange('primaryDiagnosis', e.target.value)}
                rows={3}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 ${
                  errors.primaryDiagnosis ? 'border-red-500' : 'border-neutral-200'
                }`}
                placeholder="Enter primary diagnosis and clinical notes"
              />
              {errors.primaryDiagnosis && (
                <p className="text-red-600 text-xs mt-1">{errors.primaryDiagnosis}</p>
              )}
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">
                  Blood Pressure
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={formData.bloodPressure}
                    onChange={(e) => handleInputChange('bloodPressure', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 ${
                      errors.bloodPressure ? 'border-red-500' : 'border-neutral-200'
                    }`}
                    placeholder="120/80"
                  />
                  <Activity className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-neutral-400" />
                </div>
                {errors.bloodPressure && (
                  <p className="text-red-600 text-xs mt-1">{errors.bloodPressure}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">
                  Heart Rate (BPM)
                </label>
                <div className="relative">
                  <input
                    type="number"
                    value={formData.heartRate}
                    onChange={(e) => handleInputChange('heartRate', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 ${
                      errors.heartRate ? 'border-red-500' : 'border-neutral-200'
                    }`}
                    placeholder="72"
                    min="0"
                    max="200"
                  />
                  <Heart className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-neutral-400" />
                </div>
                {errors.heartRate && (
                  <p className="text-red-600 text-xs mt-1">{errors.heartRate}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">
                  Temperature (°F)
                </label>
                <div className="relative">
                  <input
                    type="number"
                    step="0.1"
                    value={formData.temperature}
                    onChange={(e) => handleInputChange('temperature', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 ${
                      errors.temperature ? 'border-red-500' : 'border-neutral-200'
                    }`}
                    placeholder="98.6"
                    min="90"
                    max="110"
                  />
                  <Thermometer className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-neutral-400" />
                </div>
                {errors.temperature && (
                  <p className="text-red-600 text-xs mt-1">{errors.temperature}</p>
                )}
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start space-x-2">
                <AlertTriangle className="w-5 h-5 text-blue-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-blue-900">Vital Signs Guidelines</h4>
                  <p className="text-sm text-blue-700 mt-1">
                    Record vital signs using standard units. Blood pressure in mmHg, heart rate in BPM, 
                    temperature in Fahrenheit. Contact physician if values are outside normal ranges.
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Current Medications
              </label>
              <textarea
                value={formData.currentMedications}
                onChange={(e) => handleInputChange('currentMedications', e.target.value)}
                rows={4}
                className="w-full px-3 py-2 border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                placeholder="List all current medications, dosages, and frequency"
              />
              <p className="text-xs text-neutral-500 mt-1">
                Include prescription medications, over-the-counter drugs, and supplements
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Known Allergies
              </label>
              <textarea
                value={formData.knownAllergies}
                onChange={(e) => handleInputChange('knownAllergies', e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                placeholder="List all known allergies including medications, foods, and environmental triggers"
              />
              <p className="text-xs text-neutral-500 mt-1">
                Include reaction severity and type of allergic response
              </p>
            </div>

            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start space-x-2">
                <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-red-900">Allergy Alert</h4>
                  <p className="text-sm text-red-700 mt-1">
                    Allergies are critical for patient safety. Double-check all allergy information 
                    before proceeding with treatment.
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <h4 className="font-medium text-green-900">Review Your Information</h4>
              </div>
              <p className="text-sm text-green-700 mt-1">
                Please review all information before submitting the medical record.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <h4 className="font-medium text-neutral-900">Patient Information</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-neutral-600">Patient Name:</span>
                    <span className="font-medium">{formData.patientName || 'Not specified'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-600">Date of Birth:</span>
                    <span className="font-medium">{formData.dateOfBirth || 'Not specified'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-600">Medical Record #:</span>
                    <span className="font-medium">{formData.medicalRecordNumber || 'Not specified'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-600">ICD-10 Code:</span>
                    <span className="font-medium">{formData.icd10Code || 'Not specified'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-600">Attending Physician:</span>
                    <span className="font-medium">{formData.attendingPhysician || 'Not specified'}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="font-medium text-neutral-900">Vitals & Medication</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-neutral-600">Blood Pressure:</span>
                    <span className="font-medium">{formData.bloodPressure || 'Not recorded'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-600">Heart Rate:</span>
                    <span className="font-medium">{formData.heartRate ? `${formData.heartRate} BPM` : 'Not recorded'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-600">Temperature:</span>
                    <span className="font-medium">{formData.temperature ? `${formData.temperature}°F` : 'Not recorded'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-600">Allergies:</span>
                    <span className="font-medium">{formData.knownAllergies ? 'Documented' : 'None listed'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-600">Medications:</span>
                    <span className="font-medium">{formData.currentMedications ? 'Documented' : 'None listed'}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  if (isSubmitted) {
    return (
      <div className="max-w-2xl mx-auto">
        <GlassCard>
          <div className="text-center py-8">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-neutral-900 mb-2">Record Submitted Successfully</h3>
            <p className="text-neutral-600 mb-6">
              Medical record for {formData.patientName} has been saved and is now available for review.
            </p>
            <div className="flex space-x-4 justify-center">
              <button
                onClick={resetForm}
                className="px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
              >
                Create New Record
              </button>
              <button className="px-6 py-2 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 transition-colors">
                View Records
              </button>
            </div>
          </div>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-neutral-900 flex items-center justify-center space-x-2">
          <UserCheck className="w-8 h-8 text-blue-600" />
          <span>Medical Records Form</span>
        </h1>
        <p className="text-neutral-600 mt-2">HIPAA-compliant medical record entry system</p>
      </div>

      {/* Progress Steps */}
      <GlassCard>
        <div className="flex items-center justify-between">
          {steps.map((step, index) => {
            const StepIcon = step.icon;
            const isActive = step.id === currentStep;
            const isCompleted = step.id < currentStep;
            
            return (
              <div key={step.id} className="flex items-center">
                <div className={`
                  flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors
                  ${isActive ? 'border-primary-500 bg-primary-50' : 
                    isCompleted ? 'border-green-500 bg-green-50' : 'border-neutral-300 bg-neutral-50'}
                `}>
                  {isCompleted ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <StepIcon className={`w-5 h-5 ${isActive ? 'text-primary-600' : 'text-neutral-500'}`} />
                  )}
                </div>
                <div className="ml-3">
                  <p className={`text-sm font-medium ${isActive ? 'text-primary-600' : 'text-neutral-900'}`}>
                    {step.name}
                  </p>
                </div>
                {index < steps.length - 1 && (
                  <div className={`w-16 h-px mx-4 ${isCompleted ? 'bg-green-300' : 'bg-neutral-300'}`} />
                )}
              </div>
            );
          })}
        </div>
      </GlassCard>

      {/* Form Content */}
      <GlassCard>
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-neutral-900 mb-2">
            Step {currentStep}: {steps.find(s => s.id === currentStep)?.name}
          </h2>
          <p className="text-neutral-600">
            {currentStep === 1 && 'Enter basic patient information and medical details'}
            {currentStep === 2 && 'Record vital signs and measurements'}
            {currentStep === 3 && 'Document current medications and allergies'}
            {currentStep === 4 && 'Review all information before submission'}
          </p>
        </div>

        {renderStepContent()}

        {/* Navigation */}
        <div className="flex justify-between pt-6 border-t border-neutral-200">
          <button
            onClick={prevStep}
            disabled={currentStep === 1}
            className="px-6 py-2 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Previous
          </button>

          <div className="flex space-x-3">
            <button
              onClick={resetForm}
              className="px-6 py-2 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 transition-colors"
            >
              Reset
            </button>

            {currentStep === steps.length ? (
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="flex items-center space-x-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Submitting...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    <span>Submit Record</span>
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={nextStep}
                className="px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
              >
                Next
              </button>
            )}
          </div>
        </div>
      </GlassCard>
    </div>
  );
};

export default MedicalRecordsForm;