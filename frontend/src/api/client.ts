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

const OBJECT_URL_REVOKE_DELAY_MS = 1000;

/** Endpoints that address a stored upload by `file_id`; a 404 from them means the upload expired. */
const FILE_ID_ENDPOINT_FRAGMENTS = [
  '/vcf/validate',
  '/vcf/convert',
  '/vcf/download',
  '/vcf/plex34/structure-input',
] as const;

const UPLOAD_EXPIRED_DEFAULT_MESSAGE = 'The uploaded file is no longer available on the server.';

export class UploadExpiredError extends Error {
  constructor(message: string = UPLOAD_EXPIRED_DEFAULT_MESSAGE) {
    super(message);
    this.name = 'UploadExpiredError';
  }
}

const isFileIdEndpoint = (url: string | undefined): boolean =>
  url !== undefined && FILE_ID_ENDPOINT_FRAGMENTS.some((fragment) => url.includes(fragment));

const readDetail = (body: unknown): string | null => {
  if (typeof body === 'object' && body !== null && 'detail' in body) {
    const { detail } = body as { detail: unknown };
    if (typeof detail === 'string' && detail.length > 0) {
      return detail;
    }
  }
  return null;
};

export const getApiErrorMessage = (error: unknown, fallback: string): string => {
  if (axios.isAxiosError(error)) {
    return readDetail(error.response?.data) ?? error.message ?? fallback;
  }
  if (error instanceof Error && error.message.length > 0) {
    return error.message;
  }
  return fallback;
};

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (
      axios.isAxiosError(error) &&
      error.response?.status === 404 &&
      isFileIdEndpoint(error.config?.url)
    ) {
      return Promise.reject(new UploadExpiredError());
    }
    return Promise.reject(error);
  },
);

const readResponseDetail = async (response: Response): Promise<string | null> => {
  try {
    return readDetail(await response.json());
  } catch (parseError) {
    console.warn('Download error response was not JSON:', parseError);
    return null;
  }
};

const filenameFromContentDisposition = (header: string | null): string | null => {
  if (!header) {
    return null;
  }

  const encodedMatch = /filename\*\s*=\s*(?:UTF-8|utf-8)''([^;]+)/.exec(header);
  if (encodedMatch?.[1]) {
    try {
      return decodeURIComponent(encodedMatch[1].trim());
    } catch (decodeError) {
      console.warn('Could not decode Content-Disposition filename:', decodeError);
    }
  }

  const plainMatch = /filename\s*=\s*(?:"([^"]+)"|([^;]+))/.exec(header);
  const filename = (plainMatch?.[1] ?? plainMatch?.[2])?.trim();
  return filename && filename.length > 0 ? filename : null;
};

// Saved via a temporary <a download> so file_id URLs never land in a new tab or browser history.
const downloadBlob = async (path: string, fallbackFilename: string): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}${path}`, { credentials: 'same-origin' });

  if (response.status === 404) {
    throw new UploadExpiredError();
  }
  if (!response.ok) {
    const detail = await readResponseDetail(response);
    throw new Error(detail ?? `Download failed (HTTP ${response.status}).`);
  }

  const blob = await response.blob();
  const filename = filenameFromContentDisposition(response.headers.get('Content-Disposition')) ?? fallbackFilename;
  const objectUrl = URL.createObjectURL(blob);

  const anchor = document.createElement('a');
  anchor.href = objectUrl;
  anchor.download = filename;
  anchor.rel = 'noopener';
  anchor.hidden = true;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();

  window.setTimeout(() => URL.revokeObjectURL(objectUrl), OBJECT_URL_REVOKE_DELAY_MS);
};

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

  deleteUpload: async (fileId: string): Promise<void> => {
    await api.delete(`/vcf/upload/${encodeURIComponent(fileId)}`);
  },

  downloadFile: (fileId: string, markerType: 'hirisplex' | 'plex34'): Promise<void> =>
    downloadBlob(
      `/vcf/download/${encodeURIComponent(fileId)}/${markerType}`,
      `${markerType}_input.csv`,
    ),

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

  downloadPlex34StructureInput: (artifactId: string): Promise<void> =>
    downloadBlob(
      `/vcf/plex34/structure-input/${encodeURIComponent(artifactId)}/download`,
      'plex34_structure_input.zip',
    ),

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

  downloadFullVCF: (fileId: string): Promise<void> =>
    downloadBlob(`/vcf/download-full/${encodeURIComponent(fileId)}`, 'converted_vcf.csv'),

  getMarkers: async (markerType: 'hirisplex' | 'plex34'): Promise<MarkersResponse> => {
    const response = await api.get<MarkersResponse>(
      `/vcf/markers/${markerType}`
    );

    return response.data;
  },

};
