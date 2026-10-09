import axios from 'axios';
import type {
  HirisPlexSResultsResponse,
  FileUploadResponse,
  ValidationResult,
  ConversionRequest,
  ConversionResponse,
  MarkersResponse,
  Plex34StructureOutputResponse,
  Plex34StructureResponse,
} from '../types';

const API_BASE_URL = '/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const vcfApi = {
  uploadFile: async (file: File): Promise<FileUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post<FileUploadResponse>(
      '/vcf/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    
    return response.data;
  },

  validateFile: async (fileId: string): Promise<ValidationResult> => {
    const response = await api.post<ValidationResult>(
      '/vcf/validate',
      null,
      {
        params: { file_id: fileId },
      }
    );
    
    return response.data;
  },

  convertFile: async (request: ConversionRequest): Promise<ConversionResponse> => {
    const response = await api.post<ConversionResponse>(
      '/vcf/convert',
      request
    );
    
    return response.data;
  },

  downloadFile: (fileId: string, markerType: 'hirisplex' | 'plex34') => {
    const url = `${API_BASE_URL}/vcf/download/${fileId}/${markerType}`;
    window.open(url, '_blank');
  },

  generatePlex34StructureInput: async (fileId: string): Promise<Plex34StructureResponse> => {
    const response = await api.post<Plex34StructureResponse>(
      '/vcf/plex34/structure-input',
      null,
      {
        params: { file_id: fileId },
      }
    );

    return response.data;
  },

  downloadPlex34StructureInput: (artifactId: string) => {
    const url = `${API_BASE_URL}/vcf/plex34/structure-input/${artifactId}/download`;
    window.open(url, '_blank');
  },

  parsePlex34StructureOutput: async (file: File): Promise<Plex34StructureOutputResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<Plex34StructureOutputResponse>(
      '/vcf/plex34/structure-output',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  },

  parseHirisplexSResults: async (file: File): Promise<HirisPlexSResultsResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<HirisPlexSResultsResponse>(
      '/results/hirisplex-s',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  },

  downloadFullVCF: (fileId: string) => {
    const url = `${API_BASE_URL}/vcf/download-full/${fileId}`;
    window.open(url, '_blank');
  },

  getMarkers: async (markerType: 'hirisplex' | 'plex34'): Promise<MarkersResponse> => {
    const response = await api.get<MarkersResponse>(
      `/vcf/markers/${markerType}`
    );

    return response.data;
  },

};
