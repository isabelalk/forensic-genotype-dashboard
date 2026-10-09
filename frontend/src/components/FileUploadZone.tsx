import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  HiOutlineCheckCircle,
  HiOutlineCloudUpload,
  HiOutlineDocument,
  HiOutlineFolderOpen,
  HiOutlineX,
} from 'react-icons/hi';
import { useVCFStore } from '../store/vcfStore';

export const FileUploadZone = () => {
  const { file, setFile } = useVCFStore();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const selectedFile = acceptedFiles[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  }, [setFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.vcf'],
      'application/gzip': ['.vcf.gz', '.gz'],
    },
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
            <span>Max. 200MB</span>
          </div>

          <button type="button" className="btn-primary rounded-full px-5 py-2.5 text-sm">
            Browse file
          </button>
        </div>
      </div>
    </div>
  );
};
