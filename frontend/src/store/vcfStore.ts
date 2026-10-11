import { create } from 'zustand';
import { vcfApi } from '../api/client';
import type { ValidationResult } from '../types';

export const UPLOAD_EXPIRED_MESSAGE = 'Your uploaded file expired on the server. Please upload it again.';

interface VCFState {
  file: File | null;
  fileId: string | null;
  validationResult: ValidationResult | null;
  isProcessing: boolean;
  currentStep: number;
  continueWithMissingMarkers: boolean;
  continueWithMissingGenotypes: boolean;
  uploadExpiredMessage: string | null;
  
  setFile: (file: File | null) => void;
  setFileId: (fileId: string | null) => void;
  setValidationResult: (result: ValidationResult | null) => void;
  setIsProcessing: (isProcessing: boolean) => void;
  setCurrentStep: (step: number) => void;
  setContinueWithMissingMarkers: (value: boolean) => void;
  setContinueWithMissingGenotypes: (value: boolean) => void;
  expireUpload: () => void;
  clearUploadExpiredMessage: () => void;
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
  uploadExpiredMessage: null,
};

const releaseUpload = (fileId: string | null) => {
  if (!fileId) return;

  vcfApi.deleteUpload(fileId).catch((error: unknown) => {
    console.warn('Could not release the upload on the server:', error);
  });
};

export const useVCFStore = create<VCFState>((set, get) => ({
  ...initialState,
  
  setFile: (file) => {
    if (file) {
      set({ file });
      return;
    }

    releaseUpload(get().fileId);
    set(initialState);
  },
  setFileId: (fileId) => set({ fileId }),
  setValidationResult: (validationResult) => set({ validationResult }),
  setIsProcessing: (isProcessing) => set({ isProcessing }),
  setCurrentStep: (currentStep) => set({ currentStep }),
  setContinueWithMissingMarkers: (continueWithMissingMarkers) => 
    set({ continueWithMissingMarkers }),
  setContinueWithMissingGenotypes: (continueWithMissingGenotypes) => 
    set({ continueWithMissingGenotypes }),
  expireUpload: () => set({ ...initialState, uploadExpiredMessage: UPLOAD_EXPIRED_MESSAGE }),
  clearUploadExpiredMessage: () => set({ uploadExpiredMessage: null }),
  reset: () => {
    releaseUpload(get().fileId);
    set(initialState);
  },
}));
