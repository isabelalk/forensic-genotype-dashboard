import { QueryClient, QueryClientProvider, useMutation } from '@tanstack/react-query';
import { useEffect, useState, type ReactNode } from 'react';
import {
  HiOutlineChartBar,
  HiOutlineCheckCircle,
  HiOutlineCloudUpload,
  HiOutlineColorSwatch,
  HiOutlineDatabase,
  HiOutlineExclamationCircle,
  HiOutlineLightningBolt,
} from 'react-icons/hi';
import { vcfApi } from './api/client';
import { ConversionSection } from './components/ConversionSection';
import { FileUploadZone } from './components/FileUploadZone';
import { ResultsUploadSection } from './components/ResultsUploadSection';
import { ValidationPanel } from './components/ValidationPanel';
import { useVCFStore } from './store/vcfStore';

const queryClient = new QueryClient();
const THEME_STORAGE_KEY = 'hirisplex-theme';

type Theme = 'neon-light' | 'dark';

interface AnalysisSectionProps {
  readonly title: string;
  readonly description?: string;
  readonly icon: ReactNode;
  readonly delayClass: string;
  readonly children: ReactNode;
}

const getInitialTheme = (): Theme => {
  if (typeof window === 'undefined') {
    return 'neon-light';
  }

  return window.localStorage.getItem(THEME_STORAGE_KEY) === 'dark' ? 'dark' : 'neon-light';
};

const AnalysisSection = ({ title, description, icon, delayClass, children }: AnalysisSectionProps) => (
  <section className={`analysis-shell animate-slide-up ${delayClass}`}>
    <div className="analysis-core p-5 md:p-6">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-xl border border-[var(--color-border)] bg-[color-mix(in_srgb,var(--color-primary)_14%,var(--color-card))] p-2.5 text-[var(--color-primary)] shadow-[var(--shadow-glow)]">
            {icon}
          </div>
          <div className="space-y-1">
            <h2 className="text-xl font-extrabold tracking-[-0.03em] text-[var(--color-text)] md:text-2xl">{title}</h2>
            {description ? <p className="max-w-2xl text-sm leading-6 text-[var(--color-text-muted)]">{description}</p> : null}
          </div>
        </div>
      </div>
      {children}
    </div>
  </section>
);

function AppContent() {
  const { file, fileId, validationResult, setFileId, setValidationResult } = useVCFStore();
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  const validateMutation = useMutation({
    mutationFn: vcfApi.validateFile,
    onSuccess: (data) => {
      setValidationResult(data);
    },
    onError: (error) => {
      setUploadError(error instanceof Error ? error.message : 'Error validating the file.');
    },
  });

  const uploadMutation = useMutation({
    mutationFn: vcfApi.uploadFile,
    onSuccess: (data) => {
      setUploadError(null);
      setFileId(data.file_id);
      validateMutation.mutate(data.file_id);
    },
    onError: (error) => {
      setUploadError(error instanceof Error ? error.message : 'Error uploading the file.');
    },
  });

  const handleUpload = () => {
    if (!file) return;
    uploadMutation.mutate(file);
  };

  const handleThemeToggle = () => {
    setTheme((currentTheme) => (currentTheme === 'neon-light' ? 'dark' : 'neon-light'));
  };

  const themeLabel = theme === 'neon-light' ? 'Neon Light' : 'Dark Mode';
  const alternateThemeLabel = theme === 'neon-light' ? 'Dark Mode' : 'Neon Light';

  return (
    <div data-theme={theme} className="relative min-h-[100dvh] w-full overflow-hidden text-[var(--color-text)]">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute left-[8%] top-[18%] h-80 w-80 rounded-full bg-[color-mix(in_srgb,var(--color-primary)_20%,transparent)] blur-3xl" />
        <div className="absolute right-[6%] top-[28%] h-96 w-96 rounded-full bg-[color-mix(in_srgb,var(--color-secondary)_18%,transparent)] blur-3xl" />
        <div className="absolute bottom-[8%] left-[36%] h-72 w-72 rounded-full bg-[color-mix(in_srgb,var(--color-success)_16%,transparent)] blur-3xl" />
      </div>

      <div className="relative z-10 mx-auto w-full max-w-[min(100%,112rem)] px-4 py-6 sm:px-6 md:py-8 lg:px-8 2xl:px-10">
        <header className="mb-6 animate-slide-up md:mb-8">
          <div className="flex flex-col gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--surface-glass)] p-4 shadow-[var(--shadow-card)] md:flex-row md:items-center md:justify-between md:p-5">
            <div className="flex min-w-0 items-start gap-3">
              <div className="rounded-xl bg-[var(--gradient-info)] p-2.5 text-white shadow-[var(--shadow-glow)]">
                <HiOutlineDatabase className="h-5 w-5" />
              </div>
              <div className="min-w-0 space-y-2">
                <div>
                  <h1 className="text-2xl font-black leading-tight tracking-[-0.04em] text-[var(--color-text)] sm:text-[1.75rem]">
                    Virtual Phenotypic Modeling
                  </h1>
                  <p className="mt-1 text-sm leading-5 text-[var(--color-text-muted)] sm:text-base">
                    Genomic processing and forensic phenotype/ancestry analysis
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full border border-[color-mix(in_srgb,var(--color-primary)_36%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-primary)_10%,var(--color-card))] px-3 py-1 text-xs font-bold uppercase tracking-[0.16em] text-[var(--color-primary)]">
                    Genomics Workbench
                  </span>
                  <span className="rounded-full border border-[color-mix(in_srgb,var(--color-info)_34%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-info)_10%,var(--color-card))] px-3 py-1 font-mono text-xs font-bold text-[var(--color-info)]">
                    HIrisPlex-S + PLEX-34
                  </span>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={handleThemeToggle}
              aria-pressed={theme === 'dark'}
              className="btn-secondary group w-full rounded-full px-4 py-2 text-sm md:w-auto"
            >
              <HiOutlineColorSwatch className="h-5 w-5 text-[var(--color-primary)] transition-transform duration-300 group-hover:rotate-12" />
              <span>{themeLabel}</span>
              <span className="rounded-full bg-[color-mix(in_srgb,var(--color-primary)_12%,var(--color-card))] px-3 py-1 text-xs text-[var(--color-text-muted)]">
                switch to {alternateThemeLabel}
              </span>
            </button>
          </div>
        </header>

        <main className="space-y-5 md:space-y-6">
          <AnalysisSection title="Upload VCF" description="Drag in the file, confirm upload, and keep validation in the backend's original order." icon={<HiOutlineCloudUpload className="h-6 w-6" />} delayClass="delay-100">
            <FileUploadZone />

            {file && !fileId && !uploadMutation.isPending ? (
              <button onClick={handleUpload} className="btn-primary mt-5 w-full text-base">
                <HiOutlineLightningBolt className="h-5 w-5" />
                Upload and validate file
              </button>
            ) : null}

            {uploadMutation.isPending ? (
              <div className="mt-5 flex justify-center py-6">
                <div className="data-surface rounded-2xl p-4 shadow-[var(--shadow-card)]">
                  <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-full border-4 border-[color-mix(in_srgb,var(--color-primary)_20%,transparent)] border-t-[var(--color-primary)] motion-safe:animate-spin" />
                    <div>
                      <p className="font-bold text-[var(--color-text)]">Processing file</p>
                      <p className="text-sm text-[var(--color-text-muted)]">Validating markers before conversion.</p>
                    </div>
                  </div>
                </div>
              </div>
            ) : null}

            {fileId ? (
              <div className="mt-5 rounded-2xl border border-[color-mix(in_srgb,var(--color-success)_38%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-success)_10%,var(--color-card))] p-4 text-[var(--color-text)] animate-slide-up">
                <div className="flex items-start gap-3">
                  <HiOutlineCheckCircle className="mt-0.5 h-6 w-6 flex-shrink-0 text-[var(--color-success)]" />
                  <div>
                    <p className="font-bold">File uploaded successfully</p>
                    {uploadMutation.data?.message ? <p className="mt-1 text-sm text-[var(--color-text-muted)]">{uploadMutation.data.message}</p> : null}
                  </div>
                </div>
              </div>
            ) : null}

            {uploadError ? (
              <div className="mt-5 rounded-2xl border border-[color-mix(in_srgb,var(--color-error)_42%,var(--color-border))] bg-[color-mix(in_srgb,var(--color-error)_10%,var(--color-card))] p-4 animate-slide-up">
                <div className="flex items-start gap-3">
                  <HiOutlineExclamationCircle className="mt-0.5 h-6 w-6 flex-shrink-0 text-[var(--color-error)]" />
                  <div>
                    <p className="font-bold text-[var(--color-text)]">Unable to upload or validate the file.</p>
                    <p className="mt-1 text-sm text-[var(--color-text-muted)]">{uploadError}</p>
                  </div>
                </div>
              </div>
            ) : null}
          </AnalysisSection>

          {validationResult ? (
            <AnalysisSection title="Quality Control / Processing Status" description="Checks IDs, markers, missing genotypes, and REF/ALT before file generation." icon={<HiOutlineCheckCircle className="h-6 w-6" />} delayClass="delay-200">
              <ValidationPanel validation={validationResult} />
            </AnalysisSection>
          ) : null}

          {validationResult ? (
            <AnalysisSection title="Conversion / Processing" description="Generate HIrisPlex-S CSV, PLEX-34 CSV, and the STRUCTURE package without changing processing order." icon={<HiOutlineCloudUpload className="h-6 w-6" />} delayClass="delay-300">
              <ConversionSection />
            </AnalysisSection>
          ) : null}

          <AnalysisSection title="Result Reader" description="Independent uploads for HIrisPlex-S CSV and PLEX-34 STRUCTURE output, with themed visualizations and the audit table preserved." icon={<HiOutlineChartBar className="h-6 w-6" />} delayClass="delay-400">
            <ResultsUploadSection />
          </AnalysisSection>
        </main>

        {validationResult ? (
          <footer className="mt-8 text-center animate-fade-in">
            <div className="inline-flex rounded-full border border-[var(--color-border)] bg-[var(--surface-glass)] px-4 py-2 text-sm font-medium text-[var(--color-text-muted)] shadow-[var(--shadow-card)]">
              HIrisPlex-S & PLEX-34 phenotypic modeling platform
            </div>
          </footer>
        ) : null}
      </div>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}

export default App;
