import { useCallback, useState } from 'react';
import { ErrorCode, useDropzone, type FileError, type FileRejection } from 'react-dropzone';
import {
  HiOutlineCheckCircle,
  HiOutlineCloudUpload,
  HiOutlineDocument,
  HiOutlineFolderOpen,
  HiOutlineX,
} from 'react-icons/hi';
import {
  ACCEPTED_VCF_EXTENSIONS,
  MAX_VCF_UPLOAD_BYTES,
  MAX_VCF_UPLOAD_LABEL,
  hasAcceptedVcfExtension,
} from '../config/limits';
import { useVCFStore } from '../store/vcfStore';
import { Alert } from './Alert';

const ACCEPTED_EXTENSIONS_TEXT = ACCEPTED_VCF_EXTENSIONS.join(', ');

const validateVcfName = (file: File): FileError | null =>
  hasAcceptedVcfExtension(file.name)
    ? null
    : { code: ErrorCode.FileInvalidType, message: 'Unsupported file extension.' };

const describeRejection = (rejection: FileRejection): string => {
  const { name } = rejection.file;
  const codes = rejection.errors.map((error) => error.code);

  if (codes.includes(ErrorCode.FileInvalidType)) {
    return `"${name}" is not a supported file type. Accepted extensions: ${ACCEPTED_EXTENSIONS_TEXT}.`;
  }
  if (codes.includes(ErrorCode.FileTooLarge)) {
    return `"${name}" exceeds ${MAX_VCF_UPLOAD_LABEL}. Choose a smaller file.`;
  }
  if (codes.includes(ErrorCode.TooManyFiles)) {
    return 'Select a single VCF file.';
  }
  return `"${name}" could not be selected.`;
};

export const FileUploadZone = () => {
  const { file, setFile } = useVCFStore();
  const [rejectionMessage, setRejectionMessage] = useState<string | null>(null);

  const onDropAccepted = useCallback((acceptedFiles: File[]) => {
    const selectedFile = acceptedFiles[0];
    if (selectedFile) {
      setRejectionMessage(null);
      setFile(selectedFile);
    }
  }, [setFile]);

  const onDropRejected = useCallback((rejections: FileRejection[]) => {
    const firstRejection = rejections[0];
    setRejectionMessage(firstRejection ? describeRejection(firstRejection) : null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDropAccepted,
    onDropRejected,
    validator: validateVcfName,
    accept: {
      'text/plain': ['.vcf'],
      'application/gzip': ['.vcf.gz'],
    },
    maxSize: MAX_VCF_UPLOAD_BYTES,
    multiple: false,
  });

  if (file) {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <div className="rounded-xl border border-[color-mix(in_srgb,var(--color-primary)_28%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-primary)_10%,var(--color-card))] p-2 text-[var(--color-primary)]">
            <HiOutlineFolderOpen className="h-5 w-5" />
          </div>
          <span className="font-bold tracking-wide text-[var(--color-text)]">Selected VCF file</span>
        </div>

        <div className="glass-hover relative overflow-hidden rounded-2xl border border-[color-mix(in_srgb,var(--color-success)_35%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-success)_10%,var(--color-card))] p-4">
          <div className="relative z-10 flex items-center justify-between gap-4">
            <div className="flex min-w-0 flex-1 items-center gap-3">
              <div className="relative rounded-xl bg-[var(--color-card)] p-2.5 shadow-[var(--shadow-success)]">
                <HiOutlineDocument className="h-8 w-8 text-[var(--color-success)]" />
                <HiOutlineCheckCircle className="absolute -bottom-1 -right-1 h-5 w-5 rounded-full bg-[var(--color-card)] text-[var(--color-success)]" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate font-bold text-[var(--color-text)]">{file.name}</p>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-sm">
                  <span className="font-mono font-bold text-[var(--color-success)]">{(file.size / 1024).toFixed(2)} KB</span>
                  <span className="text-[var(--color-text-muted)]">Ready to process</span>
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setFile(null)}
              className="rounded-xl p-2.5 text-[var(--color-text-muted)] transition-all duration-200 hover:bg-[color-mix(in_srgb,var(--color-error)_10%,var(--color-card))] hover:text-[var(--color-error)]"
              title="Remove file"
            >
              <HiOutlineX className="h-6 w-6" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className="rounded-xl border border-[color-mix(in_srgb,var(--color-primary)_28%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-primary)_10%,var(--color-card))] p-2 text-[var(--color-primary)]">
          <HiOutlineFolderOpen className="h-5 w-5" />
        </div>
        <span className="font-bold tracking-wide text-[var(--color-text)]">Upload VCF file</span>
      </div>

      <div
        {...getRootProps()}
        className={`dropzone-surface glass-hover group relative cursor-pointer overflow-hidden rounded-2xl border-2 border-dashed p-5 transition-all duration-500 md:p-5 ${
          isDragActive
            ? 'dropzone-surface--active-brand scale-[1.01]'
            : 'dropzone-surface--brand'
        }`}
      >
        <input {...getInputProps()} />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,color-mix(in_srgb,var(--color-primary)_18%,transparent),transparent_45%)] opacity-0 transition-opacity duration-500 group-hover:opacity-100" />

        <div className="relative flex flex-col items-center justify-center text-center">
          <div className={`relative mb-3 rounded-xl border border-[color-mix(in_srgb,var(--color-primary)_25%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-primary)_10%,var(--color-card))] p-3 shadow-[var(--shadow-glow)] transition-transform duration-500 ${isDragActive ? 'scale-105 rotate-2' : 'group-hover:scale-105'}`}>
            <HiOutlineCloudUpload className="h-8 w-8 text-[var(--color-primary)]" />
          </div>

          <div className="mb-3 space-y-1">
            <p className="text-base font-extrabold text-[var(--color-text)]">
              {isDragActive ? 'Drop the file here' : 'Drag and drop your file here'}
            </p>
            <p className="text-sm text-[var(--color-text-muted)]">or click to select a local VCF</p>
          </div>

          <div className="mb-3 flex flex-wrap items-center justify-center gap-2 text-xs text-[var(--color-text-muted)]">
            <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-card-strong)] px-3 py-1 font-mono">VCF</span>
            <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-card-strong)] px-3 py-1 font-mono">VCF.GZ</span>
            <span>Max. {MAX_VCF_UPLOAD_LABEL}</span>
          </div>

          <button type="button" className="btn-primary rounded-full px-5 py-2.5 text-sm">
            Browse file
          </button>
        </div>
      </div>

      {rejectionMessage ? (
        <div role="alert">
          <Alert variant="error">
            <p className="font-bold">File not accepted</p>
            <p className="mt-1 text-sm text-[var(--color-text-muted)]">{rejectionMessage}</p>
          </Alert>
        </div>
      ) : null}
    </div>
  );
};
