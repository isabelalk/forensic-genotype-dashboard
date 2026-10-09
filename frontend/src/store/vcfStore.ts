import { create } from 'zustand';
import type { ValidationResult } from '../types';

interface VCFState {
  file: File | null;
  fileId: string | null;
  validationResult: ValidationResult | null;
  isProcessing: boolean;
  currentStep: number;
  continueWithMissingMarkers: boolean;
  continueWithMissingGenotypes: boolean;
  
  setFile: (file: File | null) => void;
  setFileId: (fileId: string | null) => void;
  setValidationResult: (result: ValidationResult | null) => void;
  setIsProcessing: (isProcessing: boolean) => void;
  setCurrentStep: (step: number) => void;
  setContinueWithMissingMarkers: (value: boolean) => void;
  setContinueWithMissingGenotypes: (value: boolean) => void;
  reset: () => void;
}

const initialState = {
  file: null,
  fileId: null,
  validationResult: null,
  isProcessing: false,
  currentStep: 0,
  continueWithMissingMarkers: false,
  continueWithMissingGenotypes: false,
};

export const useVCFStore = create<VCFState>((set) => ({
  ...initialState,
  
  setFile: (file) => set({ file }),
  setFileId: (fileId) => set({ fileId }),
  setValidationResult: (validationResult) => set({ validationResult }),
  setIsProcessing: (isProcessing) => set({ isProcessing }),
  setCurrentStep: (currentStep) => set({ currentStep }),
  setContinueWithMissingMarkers: (continueWithMissingMarkers) => 
    set({ continueWithMissingMarkers }),
  setContinueWithMissingGenotypes: (continueWithMissingGenotypes) => 
    set({ continueWithMissingGenotypes }),
  reset: () => set(initialState),
}));
